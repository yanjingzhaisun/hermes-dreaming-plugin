"""
SQLite-backed fact store with entity resolution and trust scoring.
Single-user Hermes memory store plugin.
"""

import logging
import hashlib
import os
import re
import sqlite3
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from . import holographic as hrr
except ImportError:
    import holographic as hrr  # type: ignore[no-redef]

try:
    from . import embeddings as emb
except ImportError:
    try:
        import embeddings as emb  # type: ignore[no-redef]
    except ImportError:
        emb = None  # type: ignore[assignment]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS facts (
    fact_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    content         TEXT NOT NULL UNIQUE,
    category        TEXT DEFAULT 'general',
    tags            TEXT DEFAULT '',
    trust_score     REAL DEFAULT 0.5,
    retrieval_count INTEGER DEFAULT 0,
    helpful_count   INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hrr_vector      BLOB
);

CREATE TABLE IF NOT EXISTS entities (
    entity_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    entity_type TEXT DEFAULT 'unknown',
    aliases     TEXT DEFAULT '',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_entities (
    fact_id   INTEGER REFERENCES facts(fact_id),
    entity_id INTEGER REFERENCES entities(entity_id),
    PRIMARY KEY (fact_id, entity_id)
);

CREATE INDEX IF NOT EXISTS idx_facts_trust    ON facts(trust_score DESC);
CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category);
CREATE INDEX IF NOT EXISTS idx_entities_name  ON entities(name);

CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts
    USING fts5(content, tags, content=facts, content_rowid=fact_id);

CREATE TRIGGER IF NOT EXISTS facts_ai AFTER INSERT ON facts BEGIN
    INSERT INTO facts_fts(rowid, content, tags)
        VALUES (new.fact_id, new.content, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS facts_ad AFTER DELETE ON facts BEGIN
    INSERT INTO facts_fts(facts_fts, rowid, content, tags)
        VALUES ('delete', old.fact_id, old.content, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS facts_au AFTER UPDATE ON facts BEGIN
    INSERT INTO facts_fts(facts_fts, rowid, content, tags)
        VALUES ('delete', old.fact_id, old.content, old.tags);
    INSERT INTO facts_fts(rowid, content, tags)
        VALUES (new.fact_id, new.content, new.tags);
END;

CREATE TABLE IF NOT EXISTS memory_banks (
    bank_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_name  TEXT NOT NULL UNIQUE,
    vector     BLOB NOT NULL,
    dim        INTEGER NOT NULL,
    fact_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- holographic-plus: semantic embedding sidecar tables (additive; original
-- tables untouched so the bundled holographic provider keeps working on the
-- same database).
CREATE TABLE IF NOT EXISTS fact_embeddings (
    fact_id    INTEGER PRIMARY KEY REFERENCES facts(fact_id),
    model      TEXT NOT NULL,
    dim        INTEGER NOT NULL,
    vector     BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_hash TEXT
);

CREATE TABLE IF NOT EXISTS entity_embeddings (
    entity_id  INTEGER PRIMARY KEY REFERENCES entities(entity_id),
    model      TEXT NOT NULL,
    dim        INTEGER NOT NULL,
    vector     BLOB NOT NULL,
    content_hash TEXT
);
"""

# Trust adjustment constants
_HELPFUL_DELTA   =  0.05
_UNHELPFUL_DELTA = -0.10
_TRUST_MIN       =  0.0
_TRUST_MAX       =  1.0

# Entity extraction patterns
_RE_CAPITALIZED  = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b')
_RE_DOUBLE_QUOTE = re.compile(r'"([^"]+)"')
_RE_SINGLE_QUOTE = re.compile(r"'([^']+)'")
_RE_AKA          = re.compile(
    r'(\w+(?:\s+\w+)*)\s+(?:aka|also known as)\s+(\w+(?:\s+\w+)*)',
    re.IGNORECASE,
)
# holographic-plus: CJK quoted-term patterns. Chinese text has no
# capitalization and FTS-unfriendly tokenization, so quoted spans are the
# reliable regex-detectable entity signal.
_RE_CJK_CORNER   = re.compile(r'「([^」]{1,30})」')
_RE_CJK_BOOK     = re.compile(r'《([^》]{1,30})》')
_RE_CJK_DQUOTE   = re.compile(r'“([^”]{1,30})”')


def _clamp_trust(value: float) -> float:
    return max(_TRUST_MIN, min(_TRUST_MAX, value))


class MemoryStore:
    """SQLite-backed fact store with entity resolution and trust scoring."""

    # --- Process-wide shared connection registry -------------------------
    # SQLite permits only one writer at a time. Each MemoryStore instance used
    # to open its own connection guarded by its own RLock, so the several
    # providers that coexist in one process (the main agent plus every
    # delegate_task subagent) raced as independent WAL writers. Combined with
    # writes that were not rolled back on error, one connection could leave an
    # open write transaction that pinned the write lock and made every other
    # connection's write fail with "database is locked" for the full busy
    # timeout. All instances for the same database now share ONE connection and
    # ONE re-entrant lock, so access is fully serialized and cross-connection
    # contention is impossible. The shared connection is refcounted, so closing
    # one instance never tears the connection out from under a live sibling.
    _shared: dict = {}
    _shared_guard = threading.Lock()

    def __init__(
        self,
        db_path: "str | Path | None" = None,
        default_trust: float = 0.5,
        hrr_dim: int = 1024,
        embedder=None,
        entity_merge_threshold: float = 0.88,
    ) -> None:
        if db_path is None:
            from hermes_constants import get_hermes_home
            db_path = str(get_hermes_home() / "memory_store.db")
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.default_trust = _clamp_trust(default_trust)
        self.hrr_dim = hrr_dim
        self._hrr_available = hrr._HAS_NUMPY
        # Facts stored while HRR is unavailable get no hrr_vector and become
        # invisible to reason/related retrieval. Used to be a silent skip;
        # count it and warn so the gap is observable (kanban t_f16f154e).
        self._hrr_dropped = 0
        # holographic-plus: optional EmbeddingClient (fail-open semantics live
        # in the client; None here means semantic features fully off).
        self._embedder = embedder if (embedder is not None and getattr(embedder, "enabled", False)) else None
        self._entity_merge_threshold = float(entity_merge_threshold)

        # Acquire (or open) the process-wide shared connection for this DB.
        # resolve() (not just expanduser) so symlinked/relative paths to the
        # same file share ONE connection instead of silently reintroducing
        # the multi-writer contention this registry exists to prevent.
        try:
            self._key = str(self.db_path.resolve())
        except OSError:
            self._key = str(self.db_path)
        with MemoryStore._shared_guard:
            entry = MemoryStore._shared.get(self._key)
            if entry is None:
                conn = sqlite3.connect(
                    self._key,
                    check_same_thread=False,
                    timeout=10.0,
                    # Autocommit: every statement is its own transaction, so a
                    # write that raises mid-method can never leave a dangling
                    # transaction (and its write lock) open. The explicit
                    # commit() calls below become harmless no-ops.
                    isolation_level=None,
                )
                conn.row_factory = sqlite3.Row
                entry = {"conn": conn, "lock": threading.RLock(), "refs": 0, "ready": False}
                MemoryStore._shared[self._key] = entry
            entry["refs"] += 1
            self._entry = entry
            self._conn = entry["conn"]
            self._lock = entry["lock"]

        # Initialise the schema once per shared connection.
        with self._lock:
            if not self._entry["ready"]:
                self._init_db()
                self._entry["ready"] = True
            columns = {row[1] for row in self._conn.execute("PRAGMA table_info(facts)").fetchall()}
            self._has_deprecated_at = "deprecated_at" in columns

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        """Create tables, indexes, and triggers if they do not exist. Enable WAL mode."""
        # Use the shared WAL-fallback helper so memory_store.db degrades
        # gracefully on NFS/SMB/FUSE-mounted HERMES_HOME (same issue as
        # state.db / kanban.db — see hermes_state._WAL_INCOMPAT_MARKERS).
        from hermes_state import apply_wal_with_fallback
        apply_wal_with_fallback(self._conn, db_label="memory_store.db (holographic)")
        self._conn.executescript(_SCHEMA)
        # Additive sidecar-only migration; old writers leave NULL => detectable stale.
        for table in ("fact_embeddings", "entity_embeddings"):
            cols = {r[1] for r in self._conn.execute(f"PRAGMA table_info({table})")}
            if "content_hash" not in cols:
                self._conn.execute(f"ALTER TABLE {table} ADD COLUMN content_hash TEXT")
        # Migrate: add hrr_vector column if missing (safe for existing databases)
        columns = {row[1] for row in self._conn.execute("PRAGMA table_info(facts)").fetchall()}
        if "hrr_vector" not in columns:
            self._conn.execute("ALTER TABLE facts ADD COLUMN hrr_vector BLOB")
        self._conn.commit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_fact(
        self,
        content: str,
        category: str = "general",
        tags: str = "",
        entities: "list[str] | None" = None,
    ) -> int:
        """Insert a fact and return its fact_id.

        Deduplicates by content (UNIQUE constraint). On duplicate, returns
        the existing fact_id without modifying the row. Extracts entities from
        the content and links them to the fact.

        holographic-plus: ``entities`` lets callers (LLM extraction pipeline,
        the fact_store tool) supply explicit entity names; they are unioned
        with regex-extracted candidates. A semantic embedding of the content
        is stored best-effort after insert.
        """
        with self._lock:
            content = content.strip()
            if not content:
                raise ValueError("content must not be empty")

            try:
                cur = self._conn.execute(
                    """
                    INSERT INTO facts (content, category, tags, trust_score)
                    VALUES (?, ?, ?, ?)
                    """,
                    (content, category, tags, self.default_trust),
                )
                self._conn.commit()
                fact_id: int = cur.lastrowid  # type: ignore[assignment]
            except sqlite3.IntegrityError:
                # Duplicate content — return existing id
                row = self._conn.execute(
                    "SELECT fact_id FROM facts WHERE content = ?", (content,)
                ).fetchone()
                return int(row["fact_id"])

            # Entity extraction and linking: explicit caller-supplied
            # entities first (higher quality), then regex candidates.
            names: list[str] = []
            seen_names: set[str] = set()
            for name in (entities or []) + self._extract_entities(content):
                stripped = (name or "").strip()
                if stripped and stripped.lower() not in seen_names:
                    seen_names.add(stripped.lower())
                    names.append(stripped)
            for name in names:
                entity_id = self._resolve_entity(name)
                self._link_fact_entity(fact_id, entity_id)

            # Compute HRR vector after entity linking
            self._compute_hrr_vector(fact_id, content)
            self._rebuild_bank(category)
            # holographic-plus: semantic embedding, best-effort (never raises)
            self._save_fact_embedding(fact_id, content)

            return fact_id

    def search_facts(
        self,
        query: str,
        category: str | None = None,
        min_trust: float = 0.3,
        limit: int = 10,
    ) -> list[dict]:
        """Full-text search over facts using FTS5.

        Returns a list of fact dicts ordered by FTS5 rank, then trust_score
        descending. Also increments retrieval_count for matched facts.
        """
        with self._lock:
            query = query.strip()
            if not query:
                return []

            # FTS5 AND-joins tokens by default, which zeroes out recall on
            # natural-language queries. Reuse the retriever's sanitizer
            # (stopword drop + OR-join content tokens). Imported lazily to
            # avoid a store->retrieval import cycle.
            # holographic-plus: import the fork's retriever, not the bundled one
            try:
                from .retrieval import FactRetriever
            except ImportError:
                from retrieval import FactRetriever  # type: ignore[no-redef]

            match_query = FactRetriever._sanitize_fts_query(query)
            params: list = [match_query, min_trust]
            category_clause = ""
            if category is not None:
                category_clause = "AND f.category = ?"
                params.append(category)
            params.append(limit)

            sql = f"""
                SELECT f.fact_id, f.content, f.category, f.tags,
                       f.trust_score, f.retrieval_count, f.helpful_count,
                       f.created_at, f.updated_at
                FROM facts f
                JOIN facts_fts fts ON fts.rowid = f.fact_id
                WHERE facts_fts MATCH ?
                  AND f.trust_score >= ?
                  {"AND f.deprecated_at IS NULL" if self._has_deprecated_at else ""}
                  {category_clause}
                ORDER BY fts.rank, f.trust_score DESC
                LIMIT ?
            """

            rows = self._conn.execute(sql, params).fetchall()
            results = [self._row_to_dict(r) for r in rows]

            if results:
                ids = [r["fact_id"] for r in results]
                placeholders = ",".join("?" * len(ids))
                self._conn.execute(
                    f"UPDATE facts SET retrieval_count = retrieval_count + 1 WHERE fact_id IN ({placeholders})",
                    ids,
                )
                self._conn.commit()

            return results

    def update_fact(
        self,
        fact_id: int,
        content: str | None = None,
        trust_delta: float | None = None,
        tags: str | None = None,
        category: str | None = None,
    ) -> bool:
        """Partially update a fact. Trust is clamped to [0, 1].

        Returns True if the row existed, False otherwise.
        """
        with self._lock:
            row = self._conn.execute(
                "SELECT fact_id, trust_score, content FROM facts WHERE fact_id = ?", (fact_id,)
            ).fetchone()
            if row is None:
                return False

            content_changed = content is not None and content.strip() != row["content"]
            assignments: list[str] = ["updated_at = CURRENT_TIMESTAMP"]
            params: list = []

            if content is not None:
                assignments.append("content = ?")
                params.append(content.strip())
            if tags is not None:
                assignments.append("tags = ?")
                params.append(tags)
            if category is not None:
                assignments.append("category = ?")
                params.append(category)
            if trust_delta is not None:
                new_trust = _clamp_trust(row["trust_score"] + trust_delta)
                assignments.append("trust_score = ?")
                params.append(new_trust)

            params.append(fact_id)
            self._conn.execute(
                f"UPDATE facts SET {', '.join(assignments)} WHERE fact_id = ?",
                params,
            )
            self._conn.commit()

            # Only actual text changes invalidate semantic/entity indexes.
            if content_changed:
                self._conn.execute(
                    "DELETE FROM fact_entities WHERE fact_id = ?", (fact_id,)
                )
                for name in self._extract_entities(content):
                    entity_id = self._resolve_entity(name)
                    self._link_fact_entity(fact_id, entity_id)
                self._conn.commit()

            # Old semantic hash remains stale if API fails (fail-open).
            if content_changed:
                self._compute_hrr_vector(fact_id, content.strip())
                self._save_fact_embedding(fact_id, content.strip())
            # Rebuild bank for relevant category
            cat = category or self._conn.execute(
                "SELECT category FROM facts WHERE fact_id = ?", (fact_id,)
            ).fetchone()["category"]
            self._rebuild_bank(cat)

            return True

    def remove_fact(self, fact_id: int) -> bool:
        """Delete a fact and its entity links. Returns True if the row existed."""
        with self._lock:
            row = self._conn.execute(
                "SELECT fact_id, category FROM facts WHERE fact_id = ?", (fact_id,)
            ).fetchone()
            if row is None:
                return False

            self._conn.execute("SAVEPOINT hp_remove_fact")
            try:
                self._conn.execute("DELETE FROM fact_embeddings WHERE fact_id = ?", (fact_id,))
                self._conn.execute("DELETE FROM fact_entities WHERE fact_id = ?", (fact_id,))
                self._conn.execute("DELETE FROM facts WHERE fact_id = ?", (fact_id,))
                self._conn.execute("RELEASE hp_remove_fact")
            except Exception:
                self._conn.execute("ROLLBACK TO hp_remove_fact")
                self._conn.execute("RELEASE hp_remove_fact")
                raise
            self._rebuild_bank(row["category"])
            return True

    def list_facts(
        self,
        category: str | None = None,
        min_trust: float = 0.0,
        limit: int = 50,
    ) -> list[dict]:
        """Browse facts ordered by trust_score descending.

        Optionally filter by category and minimum trust score.
        """
        with self._lock:
            params: list = [min_trust]
            category_clause = ""
            if category is not None:
                category_clause = "AND category = ?"
                params.append(category)
            params.append(limit)

            sql = f"""
                SELECT fact_id, content, category, tags, trust_score,
                       retrieval_count, helpful_count, created_at, updated_at
                FROM facts
                WHERE trust_score >= ?
                  {"AND deprecated_at IS NULL" if self._has_deprecated_at else ""}
                  {category_clause}
                ORDER BY trust_score DESC
                LIMIT ?
            """
            rows = self._conn.execute(sql, params).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def record_feedback(self, fact_id: int, helpful: bool) -> dict:
        """Record user feedback and adjust trust asymmetrically.

        helpful=True  -> trust += 0.05, helpful_count += 1
        helpful=False -> trust -= 0.10

        Returns a dict with fact_id, old_trust, new_trust, helpful_count.
        Raises KeyError if fact_id does not exist.
        """
        with self._lock:
            row = self._conn.execute(
                "SELECT fact_id, trust_score, helpful_count FROM facts WHERE fact_id = ?",
                (fact_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"fact_id {fact_id} not found")

            old_trust: float = row["trust_score"]
            delta = _HELPFUL_DELTA if helpful else _UNHELPFUL_DELTA
            new_trust = _clamp_trust(old_trust + delta)

            helpful_increment = 1 if helpful else 0
            self._conn.execute(
                """
                UPDATE facts
                SET trust_score    = ?,
                    helpful_count  = helpful_count + ?,
                    updated_at     = CURRENT_TIMESTAMP
                WHERE fact_id = ?
                """,
                (new_trust, helpful_increment, fact_id),
            )
            self._conn.commit()

            return {
                "fact_id":      fact_id,
                "old_trust":    old_trust,
                "new_trust":    new_trust,
                "helpful_count": row["helpful_count"] + helpful_increment,
            }

    # ------------------------------------------------------------------
    # Entity helpers
    # ------------------------------------------------------------------

    def _extract_entities(self, text: str) -> list[str]:
        """Extract entity candidates from text using simple regex rules.

        Rules applied (in order):
        1. Capitalized multi-word phrases  e.g. "John Doe"
        2. Double-quoted terms             e.g. "Python"
        3. Single-quoted terms             e.g. 'pytest'
        4. AKA patterns                    e.g. "Guido aka BDFL" -> two entities

        Returns a deduplicated list preserving first-seen order.
        """
        seen: set[str] = set()
        candidates: list[str] = []

        def _add(name: str) -> None:
            stripped = name.strip()
            if stripped and stripped.lower() not in seen:
                seen.add(stripped.lower())
                candidates.append(stripped)

        for m in _RE_CAPITALIZED.finditer(text):
            _add(m.group(1))

        for m in _RE_DOUBLE_QUOTE.finditer(text):
            _add(m.group(1))

        for m in _RE_SINGLE_QUOTE.finditer(text):
            _add(m.group(1))

        for m in _RE_AKA.finditer(text):
            _add(m.group(1))
            _add(m.group(2))

        # holographic-plus: CJK quoted spans
        for pattern in (_RE_CJK_CORNER, _RE_CJK_BOOK, _RE_CJK_DQUOTE):
            for m in pattern.finditer(text):
                _add(m.group(1))

        return candidates

    def _resolve_entity(self, name: str) -> int:
        """Find an existing entity by name or alias (case-insensitive) or create one.

        holographic-plus: after exact name/alias misses, falls back to
        semantic resolution — embed the name and merge into the best-matching
        existing entity (cosine >= entity_merge_threshold) by appending the
        new name to its aliases. Merges are logged and reversible (aliases
        are plain CSV, no data is deleted).

        Returns the entity_id.
        """
        # Exact name match
        row = self._conn.execute(
            "SELECT entity_id FROM entities WHERE name LIKE ?", (name,)
        ).fetchone()
        if row is not None:
            return int(row["entity_id"])

        # Search aliases — aliases stored as comma-separated; use LIKE with % boundaries
        alias_row = self._conn.execute(
            """
            SELECT entity_id FROM entities
            WHERE ',' || aliases || ',' LIKE '%,' || ? || ',%'
            """,
            (name,),
        ).fetchone()
        if alias_row is not None:
            return int(alias_row["entity_id"])

        # holographic-plus: semantic merge against existing entities
        merged = self._find_semantic_entity(name)
        if merged is not None:
            return merged

        # Create new entity
        cur = self._conn.execute(
            "INSERT INTO entities (name) VALUES (?)", (name,)
        )
        self._conn.commit()
        entity_id = int(cur.lastrowid)  # type: ignore[return-value]
        # holographic-plus: embed the new canonical name (best-effort)
        self._save_entity_embedding(entity_id, name)
        return entity_id

    # ------------------------------------------------------------------
    # holographic-plus: embedding helpers (all best-effort, never raise)
    # ------------------------------------------------------------------

    def _save_fact_embedding(self, fact_id: int, content: str) -> None:
        self._save_embedding("facts", "fact_embeddings", "fact_id", "content", fact_id, content)

    def _save_entity_embedding(self, entity_id: int, name: str) -> None:
        # Canonical name is the embedding input; aliases do not change it.
        self._save_embedding("entities", "entity_embeddings", "entity_id", "name", entity_id, name)

    def _save_embedding(self, source, sidecar, key, column, ident, text) -> None:
        if self._embedder is None or emb is None:
            return
        try:
            vec = self._embedder.embed(text)
            if vec is None:
                logger.warning("%s embedding unavailable for id=%s; missing/stale", source, ident)
                return
            # CAS in one SQL statement: do not resurrect a deleted fact or attach
            # a vector to content another process changed while HTTP was in flight.
            self._conn.execute(
                f"INSERT INTO {sidecar} ({key}, model, dim, vector, content_hash) "
                f"SELECT {key}, ?, ?, ?, ? FROM {source} WHERE {key}=? AND {column}=? "
                f"ON CONFLICT({key}) DO UPDATE SET model=excluded.model, dim=excluded.dim, "
                "vector=excluded.vector, content_hash=excluded.content_hash" +
                (", created_at=CURRENT_TIMESTAMP" if sidecar == "fact_embeddings" else ""),
                (self._embedder.model, len(vec), emb.vec_to_bytes(vec),
                 hashlib.sha256(text.encode("utf-8")).hexdigest(), ident, text),
            )
        except Exception as e:
            logger.warning("%s embedding save failed for id=%s (%s); missing/stale", source, ident, type(e).__name__)

    def _find_semantic_entity(self, name: str) -> "int | None":
        """Cosine-match *name* against embedded entities; merge on high sim.

        On a match the new name is appended to the entity's aliases and the
        existing entity_id is returned. Returns None when semantic resolution
        is unavailable or nothing clears the threshold.
        """
        if self._embedder is None or emb is None:
            return None
        try:
            vec = self._embedder.embed(name)
            if vec is None:
                return None
            rows = self._conn.execute(
                """
                SELECT ee.entity_id, ee.vector, ee.content_hash, ee.model, ee.dim, e.name, e.aliases
                FROM entity_embeddings ee
                JOIN entities e ON e.entity_id = ee.entity_id
                """
            ).fetchall()
            best_id = None
            best_sim = -1.0
            best_name = ""
            best_aliases = ""
            for row in rows:
                if (row["content_hash"] != hashlib.sha256(row["name"].encode("utf-8")).hexdigest()
                        or row["model"] != self._embedder.model or row["dim"] != self._embedder.dim):
                    continue
                sim = emb.cosine(vec, emb.bytes_to_vec(row["vector"]))
                if sim > best_sim:
                    best_sim = sim
                    best_id = int(row["entity_id"])
                    best_name = row["name"]
                    best_aliases = row["aliases"] or ""
            if best_id is not None and best_sim >= self._entity_merge_threshold:
                new_aliases = (best_aliases + "," + name) if best_aliases else name
                self._conn.execute(
                    "UPDATE entities SET aliases = ? WHERE entity_id = ?",
                    (new_aliases, best_id),
                )
                self._conn.commit()
                logger.info(
                    "holographic-plus: entity '%s' merged into '%s' (id=%d, cosine=%.3f, threshold=%.2f)",
                    name, best_name, best_id, best_sim, self._entity_merge_threshold,
                )
                return best_id
            return None
        except Exception as e:
            logger.debug("semantic entity resolution failed for '%s': %s", name, e)
            return None

    def _link_fact_entity(self, fact_id: int, entity_id: int) -> None:
        """Insert into fact_entities, silently ignore if the link already exists."""
        self._conn.execute(
            """
            INSERT OR IGNORE INTO fact_entities (fact_id, entity_id)
            VALUES (?, ?)
            """,
            (fact_id, entity_id),
        )
        self._conn.commit()

    def _compute_hrr_vector(self, fact_id: int, content: str) -> None:
        """Compute and store HRR vector for a fact. Counted + warned if numpy unavailable."""
        with self._lock:
            if not self._hrr_available:
                self._hrr_dropped += 1
                if self._hrr_dropped == 1 or self._hrr_dropped % 100 == 0:
                    logger.warning(
                        "holographic-plus: HRR unavailable (numpy not importable in this process); "
                        "fact %d stored WITHOUT hrr_vector (dropped this process: %d). "
                        "It will be invisible to HRR retrieval (reason/related) until backfilled.",
                        fact_id, self._hrr_dropped,
                    )
                return

            # Get entities linked to this fact
            rows = self._conn.execute(
                """
                SELECT e.name FROM entities e
                JOIN fact_entities fe ON fe.entity_id = e.entity_id
                WHERE fe.fact_id = ?
                """,
                (fact_id,),
            ).fetchall()
            entities = [row["name"] for row in rows]

            vector = hrr.encode_fact(content, entities, self.hrr_dim)
            self._conn.execute(
                "UPDATE facts SET hrr_vector = ? WHERE fact_id = ?",
                (hrr.phases_to_bytes(vector), fact_id),
            )
            self._conn.commit()

    def _rebuild_bank(self, category: str) -> None:
        """Full rebuild of a category's memory bank from all its fact vectors."""
        with self._lock:
            if not self._hrr_available:
                return

            bank_name = f"cat:{category}"
            rows = self._conn.execute(
                "SELECT hrr_vector FROM facts WHERE category = ? AND hrr_vector IS NOT NULL",
                (category,),
            ).fetchall()

            if not rows:
                self._conn.execute("DELETE FROM memory_banks WHERE bank_name = ?", (bank_name,))
                self._conn.commit()
                return

            vectors = [hrr.bytes_to_phases(row["hrr_vector"], dim=self.hrr_dim) for row in rows]
            bank_vector = hrr.bundle(*vectors)
            fact_count = len(vectors)

            # Check SNR
            hrr.snr_estimate(self.hrr_dim, fact_count)

            self._conn.execute(
                """
                INSERT INTO memory_banks (bank_name, vector, dim, fact_count, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(bank_name) DO UPDATE SET
                    vector = excluded.vector,
                    dim = excluded.dim,
                    fact_count = excluded.fact_count,
                    updated_at = excluded.updated_at
                """,
                (bank_name, hrr.phases_to_bytes(bank_vector), self.hrr_dim, fact_count),
            )
            self._conn.commit()

    def rebuild_all_vectors(self, dim: int | None = None) -> int:
        """Recompute all HRR vectors + banks from text. For recovery/migration.

        Returns the number of facts processed.
        """
        with self._lock:
            if not self._hrr_available:
                return 0

            if dim is not None:
                self.hrr_dim = dim

            rows = self._conn.execute(
                "SELECT fact_id, content, category FROM facts"
            ).fetchall()

            categories: set[str] = set()
            for row in rows:
                self._compute_hrr_vector(row["fact_id"], row["content"])
                categories.add(row["category"])

            for category in categories:
                self._rebuild_bank(category)

            return len(rows)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        """Convert a sqlite3.Row to a plain dict."""
        return dict(row)

    @classmethod
    def release_all_under(cls, directory: "str | Path") -> int:
        """Force-close every shared connection whose database lives under ``directory``.

        ``close()`` is refcount-driven, so a live holder (e.g. an agent's
        memory provider) keeps a profile's SQLite handle open indefinitely.
        That is exactly what a profile delete must break on Windows: the
        desktop's main ``serve`` process opens ``memory_store.db`` for every
        known profile, and ``rmtree`` of the profile directory fails with
        ``WinError 32`` while any of those handles is open (#88347). This
        closes the matching connections unconditionally — the directory is
        going away, so later use by a stale holder is expected to fail — and
        returns how many were closed. In a process that holds none (e.g. the
        CLI deleting from outside serve) this is a harmless no-op returning 0.
        """
        root = os.path.normcase(str(Path(directory).expanduser().resolve())) + os.sep
        with cls._shared_guard:
            # Snapshot the keys first so the registry stays stable while
            # connections are closed inside their per-database locks (closing
            # can run no user code, but this keeps the invariant obvious).
            doomed = [
                key
                for key in cls._shared
                if os.path.normcase(key).startswith(root)
            ]
            for key in doomed:
                entry = cls._shared.pop(key)
                try:
                    with entry["lock"]:
                        entry["conn"].close()
                except Exception:
                    # A connection that is already closed or broken must not
                    # abort releasing its siblings.
                    pass
        return len(doomed)

    def close(self) -> None:
        """Release this instance's reference to the shared connection.

        The underlying connection is closed only when the last MemoryStore
        referencing the same database is closed, so closing one instance can
        never break sibling instances that still hold it. Idempotent.
        """
        if getattr(self, "_entry", None) is None:
            return
        with MemoryStore._shared_guard:
            entry = self._entry
            if entry is None:
                return
            entry["refs"] -= 1
            if entry["refs"] <= 0:
                try:
                    entry["conn"].close()
                finally:
                    # Pop only OUR entry. After release_all_under() force-
                    # closed this entry (profile delete, #88347) a same-path
                    # store may have re-registered a FRESH entry under the
                    # same key; a stale holder's late close() must not evict
                    # it — that would silently reintroduce the multi-writer
                    # contention this registry exists to prevent.
                    if MemoryStore._shared.get(self._key) is entry:
                        MemoryStore._shared.pop(self._key, None)
            self._entry = None

    def __enter__(self) -> "MemoryStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

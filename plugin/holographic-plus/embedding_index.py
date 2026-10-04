"""Sidecar-only schema and read-only consistency inspection (no MemoryStore init)."""
import hashlib
import math

SOURCES = (("facts", "fact_embeddings", "fact_id", "content"),
           ("entities", "entity_embeddings", "entity_id", "name"))


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def inspect(conn, model="text-embedding-v4", dim=1024):
    result = {}
    for source, sidecar, key, column in SOURCES:
        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({sidecar})")}
        originals = dict(conn.execute(f"SELECT {key}, {column} FROM {source}"))
        expression = "content_hash" if "content_hash" in cols else "NULL"
        rows = {r[0]: r[1:] for r in conn.execute(
            f"SELECT {key}, model, dim, vector, {expression} FROM {sidecar}")} if cols else {}
        missing, stale, orphan = [], [], sorted(set(rows) - set(originals))
        for ident, text in originals.items():
            if ident not in rows:
                missing.append(ident)
                continue
            m, d, vector, digest = rows[ident]
            invalid = m != model or d != dim or digest != text_hash(text)
            try:
                import embeddings as emb
                decoded = emb.bytes_to_vec(vector)
                invalid |= len(decoded) != dim or not all(math.isfinite(v) for v in decoded)
            except Exception:
                invalid = True
            if invalid:
                stale.append(ident)
        result[source] = {"source_count": len(originals), "embedding_count": len(rows),
                          "hash_column": "content_hash" in cols,
                          "missing": sorted(missing), "stale": sorted(stale), "orphan": orphan}
    return result


def migrate(conn):
    # Only sidecar tables change. Do not initialize any base schema/FTS/banks.
    for source, sidecar, key, _ in SOURCES:
        conn.execute(f"CREATE TABLE IF NOT EXISTS {sidecar} ("
                     f"{key} INTEGER PRIMARY KEY REFERENCES {source}({key}), "
                     "model TEXT NOT NULL, dim INTEGER NOT NULL, vector BLOB NOT NULL, "
                     "content_hash TEXT" +
                     (", created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if source == "facts" else "") + ")")
        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({sidecar})")}
        if "content_hash" not in cols:
            conn.execute(f"ALTER TABLE {sidecar} ADD COLUMN content_hash TEXT")


def save_if_current(conn, spec, ident, text, vector, model):
    import embeddings as emb
    source, sidecar, key, column = spec
    cur = conn.execute(
        f"INSERT INTO {sidecar} ({key},model,dim,vector,content_hash) "
        f"SELECT {key},?,?,?,? FROM {source} WHERE {key}=? AND {column}=? "
        f"ON CONFLICT({key}) DO UPDATE SET model=excluded.model,dim=excluded.dim,"
        "vector=excluded.vector,content_hash=excluded.content_hash" +
        (",created_at=CURRENT_TIMESTAMP" if source == "facts" else ""),
        (model, len(vector), emb.vec_to_bytes(vector), text_hash(text), ident, text))
    return cur.rowcount == 1

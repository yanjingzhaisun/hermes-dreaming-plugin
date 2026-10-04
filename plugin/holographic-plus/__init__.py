"""holographic-plus — embedding-augmented fork of the bundled holographic memory plugin.

PORTED: paths parameterized; the plugin itself reads only its own config keys.

Built on top of Hermes' bundled `holographic` provider (MIT, original plugin by
dusterbloom). Adds:

- Semantic retrieval: an embedding sidecar table (provider configurable;
  the reference deployment uses DashScope text-embedding-v4), cosine candidate
  pool merged with FTS5, blended scoring
- Semantic entity resolution: high-cosine entity names merge as aliases
- CJK entity extraction (「」《》"" quoted spans) + explicit entities param
  on fact_store(add)

It shares the SAME SQLite database as the bundled provider (memory_store.db);
sidecar tables are additive. Rolling back = set memory.provider: holographic.

Config in $HERMES_HOME/config.yaml (profile-scoped):
  plugins:
    holographic-plus:
      db_path: $HERMES_HOME/memory_store.db
      auto_extract: false
      default_trust: 0.5
      min_trust_threshold: 0.3
      temporal_decay_half_life: 0
      embedding_enabled: true
      embedding_model: text-embedding-v4
      embedding_dim: 1024
      embedding_timeout_s: 3.0
      semantic_weight: 0.45
      fts_weight: 0.25
      jaccard_weight: 0.15
      hrr_weight: 0.15
      entity_merge_threshold: 0.88
"""

from __future__ import annotations

import json
import logging
import os
import hashlib
import fcntl
import uuid
import threading
import sys
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List

from agent.memory_provider import MemoryProvider
from tools.registry import tool_error
from utils import is_truthy_value
from .store import MemoryStore
from .retrieval import FactRetriever
from hermes_cli.config import cfg_get

logger = logging.getLogger(__name__)


_PROVIDER_CODE_HASH=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
_TELEMETRY_INSTANCE=str(uuid.uuid4())
_TELEMETRY_START=None
_TELEMETRY_END=None
_TELEMETRY_THREAD=None
_TELEMETRY_GUARD=threading.RLock()


def _telemetry_path():
    from hermes_constants import get_hermes_home
    return Path(get_hermes_home())/'state/fact-recalls.jsonl'


def _telemetry_base(source):
    start_ticks=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]
    return {'schema':'dream-decay-1','event_id':str(uuid.uuid4()),'occurred_at':datetime.now(timezone.utc).isoformat(),
            'source':source,'provider_code_hash':_PROVIDER_CODE_HASH,'instance_id':_TELEMETRY_INSTANCE,
            'process_id':os.getpid(),'process_start':start_ticks,'session_id':None,'fact_ids':[]}


def _telemetry_append(event):
    path=_telemetry_path();path.parent.mkdir(parents=True,exist_ok=True)
    lock=Path(str(path)+'.lock');lock.touch(mode=0o600,exist_ok=True)
    with lock.open('r+') as guard:
        fcntl.flock(guard,fcntl.LOCK_EX)
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
        with os.fdopen(fd,'ab') as out:out.write(json.dumps(event,sort_keys=True).encode()+b'\n');out.flush();os.fsync(out.fileno())
        fcntl.flock(guard,fcntl.LOCK_UN)
    os.chmod(path,0o600)


def _telemetry_gap(source,exc):
    # Independent sidecar: if the main log cannot be appended, persist a gap.
    # If storage itself is unavailable, leases expire; never renew after failure.
    global _TELEMETRY_END
    _TELEMETRY_END=None
    try:
        path=Path(str(_telemetry_path())+'.gaps.jsonl');path.parent.mkdir(parents=True,exist_ok=True)
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
        with os.fdopen(fd,'ab') as out:
            out.write(json.dumps(dict(_telemetry_base('telemetry-gap'),failed_source=source,error=type(exc).__name__)).encode()+b'\n');out.flush();os.fsync(out.fileno())
    except Exception:pass
    logger.warning('Dreaming telemetry gap source=%s error=%s',source,type(exc).__name__)


def _record_recall_event(facts, source, session_id=None):
    try:
        event=_telemetry_base(source);event['session_id']=session_id
        event['fact_ids']=[{'fact_id':int(x['fact_id']),'content_hash':hashlib.sha256(x.get('content','').encode()).hexdigest()}
                          for x in facts if isinstance(x,dict) and type(x.get('fact_id')) is int]
        if event['fact_ids']:_telemetry_append(event)
    except Exception as exc:_telemetry_gap(source,exc)


def _coverage_heartbeat():
    global _TELEMETRY_END
    with _TELEMETRY_GUARD:
        if _TELEMETRY_END is None:return
        try:
            event=_telemetry_base('telemetry-coverage')
            event.update(coverage_start=event['occurred_at'],coverage_end=(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat())
            _telemetry_append(event);_TELEMETRY_END=event['coverage_end']
        except Exception as exc:_telemetry_gap('telemetry-coverage',exc)


def _record_telemetry_ready():
    global _TELEMETRY_START,_TELEMETRY_END,_TELEMETRY_THREAD
    with _TELEMETRY_GUARD:
        if _TELEMETRY_START is not None:return
        try:
            event=_telemetry_base('telemetry-ready');_TELEMETRY_START=event['occurred_at']
            event.update(coverage_start=_TELEMETRY_START,coverage_end=(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat())
            _telemetry_append(event);_TELEMETRY_END=event['coverage_end']
            def heartbeat():
                while True:
                    threading.Event().wait(30)
                    _coverage_heartbeat()
            _TELEMETRY_THREAD=threading.Thread(target=heartbeat,name='dream-recall-coverage',daemon=True)
            _TELEMETRY_THREAD.start()
        except Exception as exc:_telemetry_gap('telemetry-ready',exc)


# ---------------------------------------------------------------------------
# Tool schemas (unchanged from original PR)
# ---------------------------------------------------------------------------

FACT_STORE_SCHEMA = {
    "name": "fact_store",
    "description": (
        "Deep structured memory with algebraic reasoning. "
        "Use alongside the memory tool — memory for always-on context, "
        "fact_store for deep recall and compositional queries.\n\n"
        "ACTIONS (simple → powerful):\n"
        "• add — Store a fact the user would expect you to remember.\n"
        "• search — Keyword lookup ('editor config', 'deploy process').\n"
        "• probe — Entity recall: ALL facts about a person/thing.\n"
        "• related — What connects to an entity? Structural adjacency.\n"
        "• reason — Compositional: facts connected to MULTIPLE entities simultaneously.\n"
        "• contradict — Memory hygiene: find facts making conflicting claims.\n"
        "• update/remove/list — CRUD operations.\n\n"
        "IMPORTANT: Before answering questions about the user, ALWAYS probe or reason first."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "search", "probe", "related", "reason", "contradict", "update", "remove", "list"],
            },
            "content": {"type": "string", "description": "Fact content (required for 'add')."},
            "query": {"type": "string", "description": "Search query (required for 'search')."},
            "entity": {"type": "string", "description": "Entity name for 'probe'/'related'."},
            "entities": {"type": "array", "items": {"type": "string"}, "description": "Entity names: for 'reason' (required); for 'add' (optional explicit entities, preferred over regex extraction)."},
            "fact_id": {"type": "integer", "description": "Fact ID for 'update'/'remove'."},
            "category": {"type": "string", "enum": ["user_pref", "project", "tool", "general"]},
            "tags": {"type": "string", "description": "Comma-separated tags."},
            "trust_delta": {"type": "number", "description": "Trust adjustment for 'update'."},
            "min_trust": {"type": "number", "description": "Minimum trust filter (default: 0.3)."},
            "limit": {"type": "integer", "description": "Max results (default: 10)."},
        },
        "required": ["action"],
    },
}

FACT_FEEDBACK_SCHEMA = {
    "name": "fact_feedback",
    "description": (
        "Rate a fact after using it. Mark 'helpful' if accurate, 'unhelpful' if outdated. "
        "This trains the memory — good facts rise, bad facts sink."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["helpful", "unhelpful"]},
            "fact_id": {"type": "integer", "description": "The fact ID to rate."},
        },
        "required": ["action", "fact_id"],
    },
}


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _load_plugin_config() -> dict:
    try:
        # Canonical loader: behavioral read now honors the managed-scope
        # overlay + ${VAR} expansion (e.g. an api key template) too.
        from hermes_cli.config import load_config_readonly
        all_config = load_config_readonly()
        return cfg_get(all_config, "plugins", "holographic-plus", default={}) or {}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# MemoryProvider implementation
# ---------------------------------------------------------------------------

class HolographicPlusMemoryProvider(MemoryProvider):
    """Holographic memory + semantic embeddings (fork: holographic-plus)."""

    def __init__(self, config: dict | None = None):
        self._config = config or _load_plugin_config()
        self._store = None
        self._retriever = None
        self._min_trust = float(self._config.get("min_trust_threshold", 0.3))

    @property
    def name(self) -> str:
        return "holographic-plus"

    def is_available(self) -> bool:
        return True  # SQLite is always available, numpy is optional

    def save_config(self, values, hermes_home):
        """Write config to config.yaml under plugins.hermes-memory-store."""
        from pathlib import Path
        config_path = Path(hermes_home) / "config.yaml"
        try:
            import yaml
            # Write-back round-trip: raw read is correct (merged defaults
            # must not be persisted back into the user's file).
            from hermes_cli.config import read_user_config_raw
            existing = read_user_config_raw(config_path)
            existing.setdefault("plugins", {})
            existing["plugins"]["hermes-memory-store"] = values
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(existing, f, default_flow_style=False)
        except Exception:
            pass

    def get_config_schema(self):
        from hermes_constants import display_hermes_home
        _default_db = f"{display_hermes_home()}/memory_store.db"
        return [
            {"key": "db_path", "description": "SQLite database path", "default": _default_db},
            {"key": "auto_extract", "description": "Auto-extract facts at session end", "default": "false", "choices": ["true", "false"]},
            {"key": "default_trust", "description": "Default trust score for new facts", "default": "0.5"},
            {"key": "hrr_dim", "description": "HRR vector dimensions", "default": "1024"},
        ]

    def initialize(self, session_id: str, **kwargs) -> None:
        from hermes_constants import get_hermes_home
        _hermes_home = str(get_hermes_home())
        _default_db = _hermes_home + "/memory_store.db"
        db_path = self._config.get("db_path", _default_db)
        # Expand $HERMES_HOME in user-supplied paths so config values like
        # "$HERMES_HOME/memory_store.db" or "~/.hermes/memory_store.db" both
        # resolve to the active profile's directory.
        if isinstance(db_path, str):
            db_path = db_path.replace("$HERMES_HOME", _hermes_home)
            db_path = db_path.replace("${HERMES_HOME}", _hermes_home)
        default_trust = float(self._config.get("default_trust", 0.5))
        hrr_dim = int(self._config.get("hrr_dim", 1024))
        hrr_weight = float(self._config.get("hrr_weight", 0.15))
        fts_weight = float(self._config.get("fts_weight", 0.25))
        jaccard_weight = float(self._config.get("jaccard_weight", 0.15))
        semantic_weight = float(self._config.get("semantic_weight", 0.45))
        temporal_decay = int(self._config.get("temporal_decay_half_life", 0))
        entity_merge_threshold = float(self._config.get("entity_merge_threshold", 0.88))

        # holographic-plus: embedding client (fail-open; disabled without key)
        embedder = None
        if is_truthy_value(self._config.get("embedding_enabled", True)):
            from .embeddings import EmbeddingClient
            embedder = EmbeddingClient(
                base_url=str(self._config.get("embedding_base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")),
                model=str(self._config.get("embedding_model", "text-embedding-v4")),
                dim=int(self._config.get("embedding_dim", 1024)),
                timeout_s=float(self._config.get("embedding_timeout_s", 3.0)),
                enabled=True,
                api_key=self._config.get("embedding_api_key") or None,
            )

        self._store = MemoryStore(
            db_path=db_path,
            default_trust=default_trust,
            hrr_dim=hrr_dim,
            embedder=embedder,
            entity_merge_threshold=entity_merge_threshold,
        )
        self._retriever = FactRetriever(
            store=self._store,
            temporal_decay_half_life=temporal_decay,
            fts_weight=fts_weight,
            jaccard_weight=jaccard_weight,
            hrr_weight=hrr_weight,
            semantic_weight=semantic_weight,
            hrr_dim=hrr_dim,
        )
        _record_telemetry_ready()
        self._session_id = session_id

    def system_prompt_block(self) -> str:
        if not self._store:
            return ""
        try:
            total = self._store._conn.execute(
                "SELECT COUNT(*) FROM facts"
            ).fetchone()[0]
        except Exception:
            total = 0
        if total == 0:
            return (
                "# Holographic Memory\n"
                "Active. Empty fact store — proactively add facts the user would expect you to remember.\n"
                "Use fact_store(action='add') to store durable structured facts about people, projects, preferences, decisions.\n"
                "Use fact_feedback to rate facts after using them (trains trust scores)."
            )
        return (
            f"# Holographic Memory\n"
            f"Active. {total} facts stored with entity resolution and trust scoring.\n"
            f"Use fact_store to search, probe entities, reason across entities, or add facts.\n"
            f"Use fact_feedback to rate facts after using them (trains trust scores)."
        )

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if not self._retriever or not query:
            return ""
        try:
            results = self._retriever.search(query, min_trust=self._min_trust, limit=5)
            if not results:
                return ""
            lines = []
            for r in results:
                trust = r.get("trust_score", r.get("trust", 0))
                lines.append(f"- [{trust:.1f}] {r.get('content', '')}")
            _record_recall_event(results, "prefetch", session_id or None)
            return "## Holographic Memory\n" + "\n".join(lines)
        except Exception as e:
            logger.debug("Holographic prefetch failed: %s", e)
            return ""

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        # Holographic memory stores explicit facts via tools, not auto-sync.
        # The on_session_end hook handles auto-extraction if configured.
        pass

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [FACT_STORE_SCHEMA, FACT_FEEDBACK_SCHEMA]

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        if tool_name == "fact_store":
            return self._handle_fact_store(args)
        elif tool_name == "fact_feedback":
            return self._handle_fact_feedback(args)
        return tool_error(f"Unknown tool: {tool_name}")

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        # is_truthy_value: the config schema declares auto_extract as a string
        # enum ("false"/"true"), and a plain truthiness check treats the string
        # "false" as enabled (#57682).
        if not is_truthy_value(self._config.get("auto_extract", False)):
            return
        if not self._store or not messages:
            return
        self._auto_extract_facts(messages)

    def on_memory_write(self, action: str, target: str, content: str) -> None:
        """Mirror built-in memory writes as facts."""
        if action == "add" and self._store and content:
            try:
                category = "user_pref" if target == "user" else "general"
                self._store.add_fact(content, category=category)
            except Exception as e:
                logger.debug("Holographic memory_write mirror failed: %s", e)

    def shutdown(self) -> None:
        # Release the shared SQLite connection deterministically on the
        # caller's thread. Dropping the reference alone leaves fd finalization
        # to GC, which keeps the connection (and its write lock) alive on a
        # long-running gateway and prolongs the "database is locked" contention
        # this store's shared-connection refcounting is meant to eliminate.
        # close() is idempotent and refcount-guarded, so siblings stay safe.
        if self._store is not None:
            try:
                self._store.close()
            except Exception as e:
                logger.debug("Holographic shutdown close() failed: %s", e)
        self._store = None
        self._retriever = None

    # -- Tool handlers -------------------------------------------------------

    def _handle_fact_store(self, args: dict) -> str:
        try:
            action = args["action"]
            store = self._store
            retriever = self._retriever

            if action == "add":
                fact_id = store.add_fact(
                    args["content"],
                    category=args.get("category", "general"),
                    tags=args.get("tags", ""),
                    entities=args.get("entities"),
                )
                return json.dumps({"fact_id": fact_id, "status": "added"})

            elif action == "search":
                results = retriever.search(
                    args["query"],
                    category=args.get("category"),
                    min_trust=float(args.get("min_trust", self._min_trust)),
                    limit=int(args.get("limit", 10)),
                )
                _record_recall_event(results, "provider_tool_search")
                return json.dumps({"results": results, "count": len(results)})

            elif action == "probe":
                results = retriever.probe(
                    args["entity"],
                    category=args.get("category"),
                    limit=int(args.get("limit", 10)),
                )
                _record_recall_event(results, "provider_tool_probe")
                return json.dumps({"results": results, "count": len(results)})

            elif action == "related":
                results = retriever.related(
                    args["entity"],
                    category=args.get("category"),
                    limit=int(args.get("limit", 10)),
                )
                _record_recall_event(results, "provider_tool_related")
                return json.dumps({"results": results, "count": len(results)})

            elif action == "reason":
                entities = args.get("entities", [])
                if not entities:
                    return tool_error("reason requires 'entities' list")
                results = retriever.reason(
                    entities,
                    category=args.get("category"),
                    limit=int(args.get("limit", 10)),
                )
                _record_recall_event(results, "provider_tool_reason")
                return json.dumps({"results": results, "count": len(results)})

            elif action == "contradict":
                results = retriever.contradict(
                    category=args.get("category"),
                    limit=int(args.get("limit", 10)),
                )
                return json.dumps({"results": results, "count": len(results)})

            elif action == "update":
                updated = store.update_fact(
                    int(args["fact_id"]),
                    content=args.get("content"),
                    trust_delta=float(args["trust_delta"]) if "trust_delta" in args else None,
                    tags=args.get("tags"),
                    category=args.get("category"),
                )
                return json.dumps({"updated": updated})

            elif action == "remove":
                removed = store.remove_fact(int(args["fact_id"]))
                return json.dumps({"removed": removed})

            elif action == "list":
                facts = store.list_facts(
                    category=args.get("category"),
                    min_trust=float(args.get("min_trust", 0.0)),
                    limit=int(args.get("limit", 10)),
                )
                return json.dumps({"facts": facts, "count": len(facts)})

            else:
                return tool_error(f"Unknown action: {action}")

        except KeyError as exc:
            return tool_error(f"Missing required argument: {exc}")
        except Exception as exc:
            return tool_error(str(exc))

    def _handle_fact_feedback(self, args: dict) -> str:
        try:
            fact_id = int(args["fact_id"])
            helpful = args["action"] == "helpful"
            result = self._store.record_feedback(fact_id, helpful=helpful)
            return json.dumps(result)
        except KeyError as exc:
            return tool_error(f"Missing required argument: {exc}")
        except Exception as exc:
            return tool_error(str(exc))

    # -- Auto-extraction (on_session_end) ------------------------------------

    def _auto_extract_facts(self, messages: list) -> None:
        # Local import (pattern used in initialize()): the compressor module is
        # heavier than this plugin and is only needed when auto_extract is on.
        from agent.context_compressor import (
            _MERGED_PRIOR_CONTEXT_HEADER,
            _MERGED_SUMMARY_DELIMITER,
            is_compaction_summary_message,
        )

        def _pre_delimiter_user_segment(msg: dict):
            """Return the genuine user text preceding a merged-into-tail
            compaction summary, or None when the whole message is a summary.

            Merge-into-tail messages (agent/context_compressor.py ~3163-3190)
            wrap real prior tail content BEFORE ``_MERGED_SUMMARY_DELIMITER``,
            prefixed with ``_MERGED_PRIOR_CONTEXT_HEADER``, then append the
            generated handoff summary AFTER the delimiter. Dropping the whole
            row (as ``is_compaction_summary_message`` alone would suggest)
            discards that genuine pre-delimiter content too (#57690 review).
            Only the summary suffix must be excluded from harvesting.
            """
            content = msg.get("content", "")
            if not isinstance(content, str) or _MERGED_SUMMARY_DELIMITER not in content:
                return None
            pre = content.split(_MERGED_SUMMARY_DELIMITER, 1)[0]
            if pre.startswith(_MERGED_PRIOR_CONTEXT_HEADER):
                pre = pre[len(_MERGED_PRIOR_CONTEXT_HEADER):]
            pre = pre.strip()
            return pre or None

        _PREF_PATTERNS = [
            re.compile(r'\bI\s+(?:prefer|like|love|use|want|need)\s+(.+)', re.IGNORECASE),
            re.compile(r'\bmy\s+(?:favorite|preferred|default)\s+\w+\s+is\s+(.+)', re.IGNORECASE),
            re.compile(r'\bI\s+(?:always|never|usually)\s+(.+)', re.IGNORECASE),
        ]
        _DECISION_PATTERNS = [
            re.compile(r'\bwe\s+(?:decided|agreed|chose)\s+(?:to\s+)?(.+)', re.IGNORECASE),
            re.compile(r'\bthe\s+project\s+(?:uses|needs|requires)\s+(.+)', re.IGNORECASE),
        ]

        extracted = 0
        for msg in messages:
            if msg.get("role") != "user":
                continue
            # Compaction handoff summaries can be inserted as role="user"
            # messages; their prose reliably matches the decision patterns, so
            # without this guard the compactor's own output is stored as a
            # durable "fact" on every rollover (#57682). A merge-into-tail
            # summary also carries genuine pre-delimiter user content in the
            # SAME row; harvest that segment instead of dropping the whole
            # message (#57690 review).
            pre_delimiter_segment = _pre_delimiter_user_segment(msg)
            if pre_delimiter_segment is not None:
                content = pre_delimiter_segment
            elif is_compaction_summary_message(msg):
                continue
            else:
                content = msg.get("content", "")
            if not isinstance(content, str) or len(content) < 10:
                continue

            for pattern in _PREF_PATTERNS:
                if pattern.search(content):
                    try:
                        self._store.add_fact(content[:400], category="user_pref")
                        extracted += 1
                    except Exception:
                        pass
                    break

            for pattern in _DECISION_PATTERNS:
                if pattern.search(content):
                    try:
                        self._store.add_fact(content[:400], category="project")
                        extracted += 1
                    except Exception:
                        pass
                    break

        if extracted:
            logger.info("Auto-extracted %d facts from conversation", extracted)


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    """Register the holographic-plus memory provider with the plugin system."""
    config = _load_plugin_config()
    provider = HolographicPlusMemoryProvider(config=config)
    ctx.register_memory_provider(provider)

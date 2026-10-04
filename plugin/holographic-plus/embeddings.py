"""Semantic embedding client for holographic-plus.

DashScope OpenAI-compatible embeddings (text-embedding-v4, 1024-dim by
default). Design rules:

- Fail-open everywhere: any API/network failure returns None and is logged;
  fact writes and retrieval must NEVER break because embeddings are down.
- Query-side in-memory LRU cache (prefetch fires per user message).
- Batch API for backfill (DashScope accepts up to 10 inputs per call).

API key resolution order:
  1. explicit config embedding_api_key
  2. env DASHSCOPE_API_KEY
  3. disabled (no credential-file fallback)
"""

from __future__ import annotations

import json
import logging
import math
import os
import struct
import threading
import urllib.request
from collections import OrderedDict

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
_DEFAULT_MODEL = "text-embedding-v4"
_DEFAULT_DIM = 1024
_BATCH_SIZE = 10
_LRU_MAX = 256
_F32_PREFIX = b"EMB1"


def _load_api_key() -> str:
    return os.environ.get("DASHSCOPE_API_KEY", "").strip()


class EmbeddingClient:
    """Thread-safe, fail-open embedding client with LRU query cache."""

    def __init__(
        self,
        base_url: str = _DEFAULT_BASE_URL,
        model: str = _DEFAULT_MODEL,
        dim: int = _DEFAULT_DIM,
        timeout_s: float = 3.0,
        enabled: bool = True,
        api_key: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.dim = dim
        self.timeout_s = timeout_s
        self._api_key = (api_key or "").strip() or _load_api_key()
        self.enabled = bool(enabled and self._api_key)
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._lock = threading.Lock()
        if enabled and not self._api_key:
            logger.warning("holographic-plus: embedding enabled but no API key found; semantic features disabled")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed(self, text: str) -> list[float] | None:
        """Embed a single text (cached). Returns None on any failure."""
        if not self.enabled:
            return None
        text = (text or "").strip()
        if not text:
            return None
        with self._lock:
            hit = self._cache.get(text)
            if hit is not None:
                self._cache.move_to_end(text)
                return hit
        vec = self._request([text])
        if vec is None:
            return None
        v = vec[0]
        with self._lock:
            self._cache[text] = v
            if len(self._cache) > _LRU_MAX:
                self._cache.popitem(last=False)
        return v

    def embed_batch(self, texts: list[str]) -> list[list[float] | None]:
        """Embed many texts in batches of 10. Per-item None on failure."""
        results: list[list[float] | None] = [None] * len(texts)
        if not self.enabled or not texts:
            return results
        for start in range(0, len(texts), _BATCH_SIZE):
            chunk_idx = list(range(start, min(start + _BATCH_SIZE, len(texts))))
            chunk = [(texts[i] or "").strip() for i in chunk_idx]
            vecs = self._request(chunk)
            if vecs is None:
                continue
            for i, v in zip(chunk_idx, vecs):
                results[i] = v
        return results

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _request(self, inputs: list[str]) -> list[list[float]] | None:
        payload = {
            "model": self.model,
            "input": inputs,
            "dimensions": self.dim,
            "encoding_format": "float",
        }
        req = urllib.request.Request(
            self.base_url + "/embeddings",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self._api_key,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            data = body.get("data") or []
            # OpenAI-compatible: each item has embedding + index; sort by index
            data.sort(key=lambda d: d.get("index", 0))
            vecs = [d["embedding"] for d in data]
            if len(vecs) != len(inputs):
                logger.warning("embedding count mismatch: got %d want %d", len(vecs), len(inputs))
                return None
            if [d.get("index") for d in data] != list(range(len(inputs))):
                logger.warning("embedding index mismatch")
                return None
            if any(len(v) != self.dim or any(not isinstance(x, (int, float)) or not math.isfinite(x) for x in v) for v in vecs):
                logger.warning("embedding dimension/nonfinite mismatch")
                return None
            return vecs
        except Exception as e:
            logger.warning("embedding request failed (%d inputs): %s", len(inputs), e)
            return None


# ----------------------------------------------------------------------
# Vector (de)serialization + similarity (pure stdlib)
# ----------------------------------------------------------------------

def vec_to_bytes(vec: list[float]) -> bytes:
    return _F32_PREFIX + struct.pack("<%df" % len(vec), *vec)


def bytes_to_vec(data: bytes) -> list[float]:
    if data.startswith(_F32_PREFIX):
        data = data[len(_F32_PREFIX):]
    n = len(data) // 4
    return list(struct.unpack("<%df" % n, data))


def cosine(a: list[float], b: list[float]) -> float:
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))

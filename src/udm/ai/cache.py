"""Simple TTL-based JSON file cache for AI-fetched metadata.

Stored under the per-user config directory so it survives restarts but is not
committed to the repository. All operations are best-effort: any I/O failure is
logged and treated as a cache miss rather than propagated.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from udm.config import config_dir
from udm.logger import logger


class TTLCache:
    """A tiny persistent cache keyed by string, with per-entry expiry."""

    def __init__(self, filename: str, ttl_seconds: int) -> None:
        self._path: Path = config_dir() / filename
        self._ttl = max(0, int(ttl_seconds))

    def get(self, key: str) -> Any | None:
        """Return the cached value for *key* if present and fresh, else None."""
        store = self._read()
        entry = store.get(key)
        if not entry:
            return None
        ts = entry.get("ts", 0)
        if self._ttl and (time.time() - ts) > self._ttl:
            logger.info(f"Cache entry '{key}' expired.")
            return None
        return entry.get("value")

    def set(self, key: str, value: Any) -> None:
        """Persist *value* under *key* with the current timestamp."""
        store = self._read()
        store[key] = {"ts": time.time(), "value": value}
        self._write(store)

    def clear(self) -> None:
        """Remove the cache file entirely."""
        try:
            self._path.unlink(missing_ok=True)
        except OSError as e:
            logger.warning(f"Could not clear cache {self._path}: {e}")

    # ── internals ────────────────────────────────────────────────

    def _read(self) -> dict:
        if not self._path.exists():
            return {}
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Could not read cache {self._path}: {e}")
            return {}

    def _write(self, store: dict) -> None:
        try:
            tmp = self._path.with_suffix(self._path.suffix + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(store, f, indent=2)
            tmp.replace(self._path)
        except OSError as e:
            logger.warning(f"Could not write cache {self._path}: {e}")

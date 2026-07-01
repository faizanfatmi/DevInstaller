"""High-level service that keeps language/compiler versions up to date.

This module orchestrates the Gemini client and the TTL cache to answer a single
question: *what is the latest stable version of each requested language or
compiler?* It is designed to be safe to call from anywhere — it never raises,
never blocks indefinitely, and returns cached data when the API is unavailable.

To avoid blocking the Qt event loop, callers should run :meth:`refresh` on a
background thread (see ``udm.gui`` integration) and apply the result on the UI
thread.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from udm.ai.cache import TTLCache
from udm.ai.gemini import GeminiClient, GeminiError, gemini_available
from udm.logger import logger

_CACHE_FILE = "language_versions.json"
_CACHE_KEY = "latest_versions"
# Refresh at most once per day.
_CACHE_TTL_SECONDS = 24 * 60 * 60

_PROMPT_TEMPLATE = (
    "You are a release-tracking assistant. For each of the following programming "
    "languages or compilers, return the latest stable release version as of "
    "today. Respond with ONLY a compact JSON object mapping the exact input name "
    "to a version string, with no prose and no markdown fences. "
    "If you are unsure of a version, omit that key. Inputs: {names}"
)


@dataclass(frozen=True)
class LanguageVersion:
    """A single language/compiler and its latest known stable version."""

    name: str
    version: str


class VersionUpdater:
    """Fetch and cache the latest stable versions for a set of languages."""

    def __init__(self, client: GeminiClient | None = None) -> None:
        self._client = client
        self._cache = TTLCache(_CACHE_FILE, _CACHE_TTL_SECONDS)

    def cached_versions(self) -> dict[str, str]:
        """Return the last cached mapping (may be empty). Never triggers I/O errors."""
        data = self._cache.get(_CACHE_KEY)
        return dict(data) if isinstance(data, dict) else {}

    def refresh(
        self, names: list[str], *, force: bool = False
    ) -> dict[str, str]:
        """Return latest versions for *names*, using cache when possible.

        This method never raises. On any failure it logs and falls back to the
        cached mapping (possibly empty).

        Parameters
        ----------
        names:
            Language / compiler display names to look up.
        force:
            When True, bypass the cache freshness check and always query the API
            (still falls back to cache on error).
        """
        names = [n for n in dict.fromkeys(n.strip() for n in names) if n]
        if not names:
            return {}

        if not force:
            cached = self.cached_versions()
            if cached and all(n in cached for n in names):
                logger.info("Using cached language versions.")
                return {n: cached[n] for n in names}

        if not gemini_available():
            logger.warning(
                "Gemini not configured; returning cached language versions."
            )
            return self.cached_versions()

        try:
            fresh = self._query(names)
        except GeminiError as e:
            logger.warning(f"Version refresh failed: {e}; using cache.")
            return self.cached_versions()
        except Exception as e:  # noqa: BLE001 - never let this bubble up
            logger.exception(f"Unexpected version refresh error: {e}")
            return self.cached_versions()

        merged = self.cached_versions()
        merged.update(fresh)
        if fresh:
            self._cache.set(_CACHE_KEY, merged)
            logger.info(f"Updated {len(fresh)} language version(s) via Gemini.")
        return merged

    # ── internals ────────────────────────────────────────────────

    def _query(self, names: list[str]) -> dict[str, str]:
        client = self._client or GeminiClient()
        prompt = _PROMPT_TEMPLATE.format(names=", ".join(names))
        raw = client.generate_text(prompt, response_mime_type="application/json")
        parsed = self._parse_json_object(raw)
        # Keep only string->string entries for requested names.
        result: dict[str, str] = {}
        for name in names:
            value = parsed.get(name)
            if isinstance(value, (str, int, float)) and str(value).strip():
                result[name] = str(value).strip()
        return result

    @staticmethod
    def _parse_json_object(raw: str) -> dict:
        """Parse a JSON object, tolerating stray markdown fences."""
        text = raw.strip()
        # Strip ```json ... ``` fences if the model added them.
        fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
        if fence:
            text = fence.group(1).strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Gemini version response was not valid JSON.")
            return {}
        return data if isinstance(data, dict) else {}

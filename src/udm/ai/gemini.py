"""Minimal Gemini REST client.

Uses only the Python standard library (``urllib``) so the application gains no
new hard dependency. The API key is read exclusively from the
``DEVINSTALLER_GEMINI_API_KEY`` environment variable and is never persisted to
disk or logged.

The client is intentionally small: it sends a single-turn text prompt and
returns the model's text response. It implements a bounded retry loop with
exponential backoff for transient failures (HTTP 429/5xx and network errors)
and raises :class:`GeminiError` for non-recoverable problems. Callers that want
fully graceful behaviour should use :mod:`udm.ai.version_updater`, which never
raises.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from udm.config import gemini_api_key, gemini_model, gemini_timeout
from udm.logger import logger

_API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"

# HTTP status codes that are worth retrying.
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class GeminiError(RuntimeError):
    """Raised when a Gemini request cannot be completed."""


def gemini_available() -> bool:
    """Return True if a Gemini API key is configured."""
    return bool(gemini_api_key())


class GeminiClient:
    """Small single-turn Gemini text client.

    Parameters
    ----------
    max_retries:
        Maximum number of *additional* attempts after the first request.
    backoff_base:
        Base seconds for exponential backoff (attempt ``n`` waits
        ``backoff_base * 2**n`` seconds, capped at ``backoff_cap``).
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        max_retries: int = 3,
        backoff_base: float = 1.0,
        backoff_cap: float = 20.0,
    ) -> None:
        self._api_key = api_key or gemini_api_key()
        self._model = model or gemini_model()
        self._timeout = timeout if timeout is not None else gemini_timeout()
        self._max_retries = max(0, int(max_retries))
        self._backoff_base = max(0.0, float(backoff_base))
        self._backoff_cap = max(self._backoff_base, float(backoff_cap))

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def generate_text(self, prompt: str, *, response_mime_type: str | None = None) -> str:
        """Send *prompt* and return the model's plain-text response.

        Raises
        ------
        GeminiError
            If the client is unconfigured or the request fails after all
            retries.
        """
        if not self.configured:
            raise GeminiError("Gemini API key is not configured.")
        if not prompt or not prompt.strip():
            raise GeminiError("Prompt must not be empty.")

        url = f"{_API_ROOT}/{self._model}:generateContent?key={self._api_key}"
        payload: dict = {
            "contents": [{"parts": [{"text": prompt}]}],
        }
        if response_mime_type:
            payload["generationConfig"] = {"response_mime_type": response_mime_type}

        body = json.dumps(payload).encode("utf-8")
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                raw = self._post(url, body)
                return self._extract_text(raw)
            except _RetryableError as exc:
                last_error = exc
                if attempt < self._max_retries:
                    delay = min(
                        self._backoff_base * (2 ** attempt), self._backoff_cap
                    )
                    logger.warning(
                        f"Gemini request failed ({exc}); retrying in {delay:.1f}s "
                        f"(attempt {attempt + 1}/{self._max_retries})."
                    )
                    time.sleep(delay)
                    continue
                break
            except GeminiError:
                raise
            except Exception as exc:  # noqa: BLE001 - normalise to GeminiError
                raise GeminiError(f"Unexpected Gemini error: {exc}") from exc

        raise GeminiError(
            f"Gemini request failed after {self._max_retries + 1} attempts: "
            f"{last_error}"
        )

    # ── internals ────────────────────────────────────────────────────

    def _post(self, url: str, body: bytes) -> dict:
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as resp:
                data = resp.read().decode("utf-8", errors="replace")
            return json.loads(data)
        except urllib.error.HTTPError as exc:
            if exc.code in _RETRYABLE_STATUS:
                raise _RetryableError(f"HTTP {exc.code}") from exc
            detail = self._safe_error_body(exc)
            raise GeminiError(f"HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            # Network-level failures are transient; allow retry.
            raise _RetryableError(str(exc)) from exc
        except json.JSONDecodeError as exc:
            raise GeminiError(f"Malformed JSON response: {exc}") from exc

    @staticmethod
    def _safe_error_body(exc: urllib.error.HTTPError) -> str:
        try:
            raw = exc.read().decode("utf-8", errors="replace")
            parsed = json.loads(raw)
            return parsed.get("error", {}).get("message", raw)[:300]
        except Exception:
            return exc.reason if hasattr(exc, "reason") else "unknown error"

    @staticmethod
    def _extract_text(raw: dict) -> str:
        """Pull the concatenated text out of a generateContent response."""
        candidates = raw.get("candidates") or []
        if not candidates:
            block = raw.get("promptFeedback", {}).get("blockReason")
            if block:
                raise GeminiError(f"Response blocked by safety filter: {block}")
            raise GeminiError("Gemini returned no candidates.")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts).strip()
        if not text:
            raise GeminiError("Gemini returned an empty response.")
        return text


class _RetryableError(Exception):
    """Internal marker for transient, retry-worthy failures."""

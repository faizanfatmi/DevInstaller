"""AI subsystem — Gemini-backed metadata enrichment.

This package is optional at runtime. If the Gemini API key is not configured
or the network is unavailable, all public helpers degrade gracefully by
returning cached or empty results instead of raising.
"""

from udm.ai.gemini import GeminiClient, GeminiError, gemini_available
from udm.ai.version_updater import VersionUpdater, LanguageVersion

__all__ = [
    "GeminiClient",
    "GeminiError",
    "gemini_available",
    "VersionUpdater",
    "LanguageVersion",
]

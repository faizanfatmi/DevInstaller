"""Configuration loader for tools.json and runtime settings."""

import json
import os
import sys
from pathlib import Path

from udm.logger import logger


def _get_base_dir() -> Path:
    """Return the base directory — sys._MEIPASS when frozen by PyInstaller."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent.parent


TOOLS_JSON_PATH = _get_base_dir() / "tools.json"

# ── Environment variable names ──────────────────────────────────────
ENV_GEMINI_API_KEY = "DEVINSTALLER_GEMINI_API_KEY"
ENV_GEMINI_MODEL = "DEVINSTALLER_GEMINI_MODEL"
ENV_GEMINI_TIMEOUT = "DEVINSTALLER_GEMINI_TIMEOUT"

_DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"
_DEFAULT_GEMINI_TIMEOUT = 30.0


def config_dir() -> Path:
    """Return the per-user config directory, creating it if needed."""
    root = os.environ.get("XDG_CONFIG_HOME")
    base = Path(root) if root else Path.home() / ".config"
    path = base / "devinstaller"
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.warning(f"Could not create config dir {path}: {e}")
    return path


def gemini_api_key() -> str:
    """Return the Gemini API key.

    Checks in order:
    1. Environment variable DEVINSTALLER_GEMINI_API_KEY
    2. A local .env file in the project root
    3. config.json in the user config directory
    """
    # 1. Environment variable
    val = os.environ.get(ENV_GEMINI_API_KEY, "").strip()
    if val:
        return val

    # 2. Local .env file in project root
    try:
        env_file = _get_base_dir() / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith(f"{ENV_GEMINI_API_KEY}="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        return val
    except Exception:
        pass

    # 3. config.json in config_dir()
    try:
        conf_file = config_dir() / "config.json"
        if conf_file.exists():
            with open(conf_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            val = data.get("gemini_api_key", "").strip()
            if val:
                return val
    except Exception:
        pass

    return ""


def gemini_model() -> str:
    """Return the configured Gemini model name."""
    return os.environ.get(ENV_GEMINI_MODEL, "").strip() or _DEFAULT_GEMINI_MODEL


def gemini_timeout() -> float:
    """Return the Gemini request timeout in seconds."""
    raw = os.environ.get(ENV_GEMINI_TIMEOUT, "").strip()
    if not raw:
        return _DEFAULT_GEMINI_TIMEOUT
    try:
        value = float(raw)
        return value if value > 0 else _DEFAULT_GEMINI_TIMEOUT
    except ValueError:
        logger.warning(f"Invalid {ENV_GEMINI_TIMEOUT}={raw!r}; using default.")
        return _DEFAULT_GEMINI_TIMEOUT


def resource_path(name: str) -> Path:
    """Return the absolute path to a bundled resource file.

    Works both when running from source and when frozen by PyInstaller
    (resources are unpacked under sys._MEIPASS).
    """
    return _get_base_dir() / name


def load_tools() -> list[dict]:
    """Load and return the tools list from tools.json."""
    try:
        with open(TOOLS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} tools from tools.json")
        return data
    except Exception as e:
        logger.error(f"Failed to load tools.json: {e}")
        return []


def get_categories(tools: list[dict]) -> list[str]:
    """Return a sorted list of unique category names."""
    return sorted({t.get("category", "Other") for t in tools})

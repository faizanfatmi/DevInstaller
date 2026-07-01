"""Configuration loader for tools.json."""

import json
import sys
from pathlib import Path

from udm.logger import logger


def _get_base_dir() -> Path:
    """Return the base directory — sys._MEIPASS when frozen by PyInstaller."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent.parent


TOOLS_JSON_PATH = _get_base_dir() / "tools.json"


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

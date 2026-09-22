"""Tests for icon mapping and asset completeness."""

import json
import sys
from pathlib import Path
from PySide6.QtGui import QGuiApplication

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from udm.gui.icon_provider import TOOL_ICONS_MAP, ICONS_DIR, get_tool_icon_pixmap

_app = None


def _get_qapp():
    global _app
    if _app is None:
        _app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    return _app


def test_icons_directory_exists():
    assert ICONS_DIR.exists()
    assert ICONS_DIR.is_dir()


def test_all_languages_have_mapped_icons():
    with open(ROOT / "tools.json", "r", encoding="utf-8") as f:
        tools = json.load(f)

    langs = [t for t in tools if t.get("category") == "Languages"]
    for lang in langs:
        key = lang["key"].lower()
        assert key in TOOL_ICONS_MAP, f"Language {key} missing from TOOL_ICONS_MAP"
        icon_file = TOOL_ICONS_MAP[key]
        icon_path = ICONS_DIR / icon_file
        assert icon_path.exists(), f"Icon file {icon_file} for language {key} does not exist"


def test_icon_pixmap_generation():
    _get_qapp()
    with open(ROOT / "tools.json", "r", encoding="utf-8") as f:
        tools = json.load(f)

    # Test top tools
    for tool in tools[:20]:
        pix = get_tool_icon_pixmap(tool, size=36)
        assert not pix.isNull(), f"Generated null pixmap for {tool.get('key')}"
        assert pix.width() == 36
        assert pix.height() == 36

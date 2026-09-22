"""Tests for configuration and tool loading."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from udm.config import load_tools, get_categories, resource_path


def test_load_tools():
    tools = load_tools()
    assert len(tools) >= 120
    assert any(t["key"] == "python" for t in tools)


def test_get_categories():
    tools = load_tools()
    cats = get_categories(tools)
    assert "Languages" in cats
    assert "Compilers" in cats
    assert "Package Managers" in cats


def test_resource_path():
    p = resource_path("logo.png")
    assert p.name == "logo.png"

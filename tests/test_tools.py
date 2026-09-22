"""Tests for tools.json data integrity."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_tools_json_exists_and_loads():
    path = ROOT / "tools.json"
    assert path.exists(), "tools.json must exist in repository root"
    with open(path, "r", encoding="utf-8") as f:
        tools = json.load(f)
    assert isinstance(tools, list)
    assert len(tools) >= 120, f"Expected at least 120 tools, found {len(tools)}"


def test_tools_unique_keys_and_required_fields():
    path = ROOT / "tools.json"
    with open(path, "r", encoding="utf-8") as f:
        tools = json.load(f)

    keys = set()
    for tool in tools:
        assert "key" in tool, f"Tool missing key: {tool}"
        key = tool["key"]
        assert key not in keys, f"Duplicate tool key: {key}"
        keys.add(key)

        assert "name" in tool and tool["name"].strip(), f"Tool {key} missing name"
        assert "category" in tool and tool["category"].strip(), f"Tool {key} missing category"
        assert "description" in tool, f"Tool {key} missing description"


def test_windows_commands_present():
    path = ROOT / "tools.json"
    with open(path, "r", encoding="utf-8") as f:
        tools = json.load(f)

    missing_windows = [t["key"] for t in tools if not t.get("install_command_windows")]
    assert len(missing_windows) == 0, f"Tools missing Windows install commands: {missing_windows}"

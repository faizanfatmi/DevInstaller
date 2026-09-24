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

    # Tools with no native Windows build. Rather than ship a misleading command
    # (e.g. `wsl --install`, which sets up WSL but never installs the tool and
    # can never satisfy the detect check), these intentionally have no Windows
    # installer and report honestly in the UI.
    NO_WINDOWS_INSTALLER = {"valgrind"}

    missing_windows = [
        t["key"]
        for t in tools
        if not t.get("install_command_windows") and t["key"] not in NO_WINDOWS_INSTALLER
    ]
    assert len(missing_windows) == 0, f"Tools missing Windows install commands: {missing_windows}"


def test_rstudio_entry():
    path = ROOT / "tools.json"
    with open(path, "r", encoding="utf-8") as f:
        tools = json.load(f)

    rstudio = next((t for t in tools if t.get("key") == "rstudio"), None)
    assert rstudio is not None, "rstudio entry must exist in tools.json"
    assert rstudio["name"] == "RStudio Desktop"
    assert rstudio["category"] == "IDEs & Editors"
    assert "Posit.RStudio" in rstudio.get("install_command_windows", "")
    assert "rstudio" in rstudio.get("install_command_linux", "")
    assert "rstudio" in rstudio.get("install_command_mac", "")

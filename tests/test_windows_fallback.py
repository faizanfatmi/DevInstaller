"""Tests for Windows package manager detection and Chocolatey fallback."""

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from udm.installer.windows_packages import translate_winget_to_choco, WINGET_TO_CHOCO_MAP
import udm.installer.prerequisites as prereq
import udm.installer.engine as eng


def test_winget_to_choco_translation():
    test_cases = [
        ({"key": "python"}, "choco install python3 -y"),
        ({"key": "nodejs"}, "choco install nodejs-lts -y"),
        ({"key": "rust"}, "choco install rustup.install -y"),
        ({"key": "git"}, "choco install git -y"),
        ({"key": "vscode"}, "choco install vscode -y"),
        ({"key": "gcc"}, "choco install mingw -y"),
        ({"key": "cmake"}, "choco install cmake"),
    ]

    for tool, expected_substr in test_cases:
        dummy_cmd = "winget install dummy"
        translated = translate_winget_to_choco(dummy_cmd, tool)
        assert expected_substr in translated, f"Failed for {tool}: got {translated}"


def test_fallback_simulation_when_winget_missing():
    tool = {"key": "python", "install_command_windows": "winget install Python.Python.3.12"}

    with patch("udm.installer.engine.is_winget_available", return_value=False), \
         patch("udm.installer.engine.is_windows", return_value=True):
        cmd = eng._get_install_cmd(tool)
        assert "choco install" in cmd
        assert "winget" not in cmd

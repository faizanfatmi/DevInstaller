"""Unit tests for complete tool uninstallation in engine.py."""

import os
import tempfile
from unittest.mock import patch

from udm.installer.engine import (
    can_uninstall,
    uninstall_tool,
    _clean_tool_shortcuts,
    _clean_tool_residuals,
)


def test_can_uninstall_package_managers():
    # Winget
    tool_winget = {"name": "Git", "key": "git", "install_command_windows": "winget install --id Git.Git"}
    assert can_uninstall(tool_winget) is True

    # Choco
    tool_choco = {"name": "Make", "key": "make", "install_command_windows": "choco install make -y"}
    assert can_uninstall(tool_choco) is True

    # NPM
    tool_npm = {"name": "TypeScript", "key": "typescript", "install_command_windows": "npm install -g typescript"}
    assert can_uninstall(tool_npm) is True

    # Pip
    tool_pip = {"name": "Meson", "key": "meson", "install_command_windows": "pip install meson"}
    assert can_uninstall(tool_pip) is True

    # Cargo
    tool_cargo = {"name": "Ripgrep", "key": "ripgrep", "install_command_windows": "cargo install ripgrep"}
    assert can_uninstall(tool_cargo) is True

    # Dotnet
    tool_dotnet = {"name": "Entity Framework", "key": "ef", "install_command_windows": "dotnet tool install -g dotnet-ef"}
    assert can_uninstall(tool_dotnet) is True

    # Oracle custom
    tool_oracle = {"name": "Oracle SQL Developer", "key": "oracle_sql_developer"}
    assert can_uninstall(tool_oracle) is True


def test_clean_tool_shortcuts():
    with tempfile.TemporaryDirectory() as td:
        desktop_dir = os.path.join(td, "Desktop")
        os.makedirs(desktop_dir, exist_ok=True)

        shortcut_match = os.path.join(desktop_dir, "MyCustomTool.lnk")
        shortcut_other = os.path.join(desktop_dir, "OtherApp.lnk")

        with open(shortcut_match, "w") as f:
            f.write("shortcut data")
        with open(shortcut_other, "w") as f:
            f.write("other data")

        tool = {"name": "MyCustomTool", "key": "mycustomtool", "binary": "mycustomtool.exe"}

        with patch("udm.installer.engine.is_windows", return_value=True), \
             patch.dict(os.environ, {"USERPROFILE": td, "PUBLIC": "", "APPDATA": "", "PROGRAMDATA": ""}):
            _clean_tool_shortcuts(tool)

        assert not os.path.exists(shortcut_match)
        assert os.path.exists(shortcut_other)


def test_clean_tool_residuals():
    with tempfile.TemporaryDirectory() as td:
        appdata_dir = os.path.join(td, "AppData", "Local", "Programs", "mytool")
        bin_dir = os.path.join(appdata_dir, "bin")
        os.makedirs(bin_dir, exist_ok=True)
        with open(os.path.join(bin_dir, "tool.exe"), "w") as f:
            f.write("exe")

        tool = {
            "name": "mytool",
            "key": "mytool",
            "path_dirs_windows": [bin_dir],
        }

        with patch("udm.installer.engine.is_windows", return_value=True), \
             patch.dict(os.environ, {"LOCALAPPDATA": os.path.join(td, "AppData", "Local")}):
            _clean_tool_residuals(tool)

        assert not os.path.exists(appdata_dir)


def test_uninstall_tool_winget_success():
    tool = {
        "name": "Git",
        "key": "git",
        "install_command_windows": "winget install --id Git.Git -e --silent",
        "detect_cmd": "git --version",
    }

    with patch("udm.installer.engine.is_windows", return_value=True), \
         patch("udm.installer.engine.run_command", return_value=(0, "Successfully uninstalled", "")), \
         patch("udm.installer.engine.detect_tool", return_value=False), \
         patch("udm.installer.engine._clean_tool_paths") as mock_paths, \
         patch("udm.installer.engine._clean_tool_shortcuts") as mock_shortcuts, \
         patch("udm.installer.engine._clean_tool_residuals") as mock_residuals:

        success = uninstall_tool(tool)
        assert success is True
        mock_paths.assert_called_once_with(tool)
        mock_shortcuts.assert_called_once_with(tool)
        mock_residuals.assert_called_once_with(tool)

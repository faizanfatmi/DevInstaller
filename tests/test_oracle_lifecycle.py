"""Tests for Oracle tool detection, uninstallation, and lifecycle routing."""

from unittest.mock import patch

from udm.installer.engine import can_uninstall, detect_tool, uninstall_tool
from udm.installer.oracle import is_oracle_tool


def test_is_oracle_tool():
    assert is_oracle_tool({"key": "oracle_db_xe"}) is True
    assert is_oracle_tool({"key": "oracle_sql_developer"}) is True
    assert is_oracle_tool({"key": "python"}) is False
    assert is_oracle_tool({"key": "sqlite"}) is False


def test_can_uninstall_oracle_tools():
    assert can_uninstall({"key": "oracle_db_xe"}) is True
    assert can_uninstall({"key": "oracle_sql_developer"}) is True


def test_can_uninstall_winget_tool():
    tool = {
        "key": "git",
        "install_command_windows": "winget install --id Git.Git -e --source winget",
    }
    assert can_uninstall(tool) is True


def test_detect_tool_delegates_to_oracle_db():
    tool = {"key": "oracle_db_xe", "name": "Oracle Database 21c XE"}
    with patch("udm.installer.oracle.detect_oracle_db", return_value=True) as mock_detect:
        assert detect_tool(tool) is True
        mock_detect.assert_called_once()

    with patch("udm.installer.oracle.detect_oracle_db", return_value=False) as mock_detect:
        assert detect_tool(tool) is False
        mock_detect.assert_called_once()


def test_detect_tool_delegates_to_sql_developer():
    tool = {"key": "oracle_sql_developer", "name": "Oracle SQL Developer"}
    with patch("udm.installer.oracle.detect_sql_developer", return_value=True) as mock_detect:
        assert detect_tool(tool) is True
        mock_detect.assert_called_once()

    with patch("udm.installer.oracle.detect_sql_developer", return_value=False) as mock_detect:
        assert detect_tool(tool) is False
        mock_detect.assert_called_once()


def test_uninstall_tool_delegates_to_oracle():
    db_tool = {"key": "oracle_db_xe", "name": "Oracle Database 21c XE"}
    with patch("udm.installer.oracle.uninstall_oracle_db", return_value=True) as mock_uninst:
        assert uninstall_tool(db_tool) is True
        mock_uninst.assert_called_once()

    sqld_tool = {"key": "oracle_sql_developer", "name": "Oracle SQL Developer"}
    with patch("udm.installer.oracle.uninstall_sql_developer", return_value=True) as mock_uninst:
        assert uninstall_tool(sqld_tool) is True
        mock_uninst.assert_called_once()

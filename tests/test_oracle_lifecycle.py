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


def test_oracle_lifecycle_decoupled_sqld_only():
    """Installing SQL developer alone must NOT uninstall Oracle DB XE."""
    from udm.installer.oracle import oracle_lifecycle

    tools = [{"key": "oracle_sql_developer", "archive_path": "fake_path"}]
    with patch("udm.installer.oracle.detect_oracle_db") as mock_db_detect, \
         patch("udm.installer.oracle.uninstall_oracle_db") as mock_db_uninst, \
         patch("udm.installer.oracle.detect_sql_developer", return_value=False), \
         patch("udm.installer.oracle.install_sql_developer", return_value=True) as mock_sqld_inst:

        results = oracle_lifecycle(tools)
        assert results.get("oracle_sql_developer") == "installed"
        mock_db_detect.assert_not_called()
        mock_db_uninst.assert_not_called()
        mock_sqld_inst.assert_called_once_with(archive_path="fake_path")


def test_install_sql_developer_from_zip(tmp_path):
    """Test extracting SQL developer from a zip file into user directory."""
    import zipfile
    from udm.installer.oracle import install_sql_developer

    # Create dummy zip with sqldeveloper/sqldeveloper.exe
    zip_file = tmp_path / "sqldeveloper-23.1.zip"
    with zipfile.ZipFile(zip_file, "w") as zf:
        zf.writestr("sqldeveloper/sqldeveloper.exe", "fake binary")
        zf.writestr("sqldeveloper/bin/sqldeveloper.conf", "conf")

    dest_dir = tmp_path / "installed_sqld"
    with patch("udm.installer.oracle._get_sqldeveloper_install_dir_windows", return_value=str(dest_dir)), \
         patch("udm.installer.oracle._create_shortcut_windows") as mock_shortcut, \
         patch("udm.platform.path.add_to_path") as mock_add_path:

        ok = install_sql_developer(archive_path=str(zip_file))
        assert ok is True
        assert (dest_dir / "sqldeveloper" / "sqldeveloper.exe").is_file()
        mock_shortcut.assert_called_once()
        mock_add_path.assert_called_once()


def test_install_sql_developer_from_folder(tmp_path):
    """Test installing SQL developer directly from an existing extracted folder."""
    from udm.installer.oracle import install_sql_developer

    src_folder = tmp_path / "extracted_sqld"
    src_folder.mkdir(parents=True)
    (src_folder / "sqldeveloper.exe").write_text("binary")

    dest_dir = tmp_path / "target_sqld"
    with patch("udm.installer.oracle._get_sqldeveloper_install_dir_windows", return_value=str(dest_dir)), \
         patch("udm.installer.oracle._create_shortcut_windows") as mock_shortcut, \
         patch("udm.platform.path.add_to_path") as mock_add_path:

        ok = install_sql_developer(archive_path=str(src_folder))
        assert ok is True
        assert (dest_dir / "sqldeveloper.exe").is_file()
        mock_shortcut.assert_called_once()
        mock_add_path.assert_called_once()


def test_install_sql_developer_missing_path():
    """Test installing with a non-existent path fails gracefully."""
    from udm.installer.oracle import install_sql_developer

    assert install_sql_developer(archive_path="C:\\non_existent_folder_xyz_123.zip") is False


def test_detect_sql_developer_in_localappdata(tmp_path, monkeypatch):
    """detect_sql_developer returns True when sqldeveloper.exe is in LOCALAPPDATA."""
    from udm.installer.oracle import detect_sql_developer

    sqld_dir = tmp_path / "sqldeveloper"
    sqld_dir.mkdir(parents=True)
    (sqld_dir / "sqldeveloper.exe").write_text("dummy")

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    with patch("udm.installer.oracle.run_command", return_value=(1, "", "")):
        assert detect_sql_developer() is True


def test_oracle_path_dialog(tmp_path):
    """Test OraclePathDialog input validation and path getter."""
    import sys
    from PySide6.QtWidgets import QApplication
    from udm.gui.oracle_dialog import OraclePathDialog

    app = QApplication.instance() or QApplication(sys.argv)

    dialog = OraclePathDialog()
    dialog._validate_path("")
    # Empty path enables direct download
    assert dialog.install_btn.isEnabled() is True
    assert dialog.install_btn.text() == "Download & Install"

    dialog._validate_path("C:\\non_existent_xyz.zip")
    assert dialog.install_btn.isEnabled() is False

    valid_file = tmp_path / "valid.zip"
    valid_file.write_text("fake")
    dialog._validate_path(f'"{valid_file}"')
    assert dialog.install_btn.isEnabled() is True
    assert dialog.install_btn.text() == "Install from File"
    dialog.path_input.setText(f'"{valid_file}"')
    assert dialog.get_path() == str(valid_file)


def test_install_sql_developer_download_flow(tmp_path):
    """Test automatic download flow when no local archive is provided."""
    import zipfile
    from udm.installer.oracle import install_sql_developer

    dest_dir = tmp_path / "installed_sqld"

    def fake_download(url, dest_zip):
        with zipfile.ZipFile(dest_zip, "w") as zf:
            zf.writestr("sqldeveloper.exe", "fake binary")
        return True

    with patch("udm.installer.oracle._download_sql_developer", side_effect=fake_download) as mock_dl, \
         patch("udm.gui.oracle_dialog._detect_default_sqldeveloper_path", return_value=""), \
         patch("udm.installer.oracle._get_sqldeveloper_install_dir_windows", return_value=str(dest_dir)), \
         patch("udm.installer.oracle._create_shortcut_windows"), \
         patch("udm.platform.path.add_to_path"):

        ok = install_sql_developer(archive_path="")
        assert ok is True
        mock_dl.assert_called_once()
        assert (dest_dir / "sqldeveloper.exe").is_file()


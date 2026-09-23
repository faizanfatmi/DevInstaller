"""Unit tests for PATH manipulation and removal utilities."""

from unittest.mock import patch
from pathlib import Path
from udm.platform.path import remove_from_path


def test_remove_from_path_windows():
    current_path = r"C:\Windows\System32;C:\Users\test\AppData\Local\tool\bin;C:\Python312"
    target = r"C:\Users\test\AppData\Local\tool\bin"

    with patch("udm.platform.path.is_windows", return_value=True), \
         patch("udm.platform.path._windows_get_user_path", return_value=current_path), \
         patch("udm.platform.path._windows_set_user_path") as mock_set:

        mock_set.return_value = True
        result = remove_from_path(target)

        assert result is True
        mock_set.assert_called_once()
        new_path = mock_set.call_args[0][0]
        assert target not in new_path
        assert r"C:\Windows\System32" in new_path
        assert r"C:\Python312" in new_path


def test_remove_from_path_windows_case_insensitive():
    current_path = r"C:\Windows\System32;C:\Users\Test\AppData\Local\Tool\BIN"
    target = r"c:\users\test\appdata\local\tool\bin"

    with patch("udm.platform.path.is_windows", return_value=True), \
         patch("udm.platform.path._windows_get_user_path", return_value=current_path), \
         patch("udm.platform.path._windows_set_user_path") as mock_set:

        mock_set.return_value = True
        result = remove_from_path(target)

        assert result is True
        mock_set.assert_called_once()
        new_path = mock_set.call_args[0][0]
        assert r"C:\Windows\System32" in new_path
        assert "tool" not in new_path.lower()


def test_remove_from_path_linux(tmp_path):
    rc_file = tmp_path / ".bashrc"
    rc_file.write_text(
        '# User configs\nexport PATH="$PATH:/home/user/.local/bin"\nexport PATH="$PATH:/opt/mytool/bin"\n',
        encoding="utf-8",
    )

    with patch("udm.platform.path.is_windows", return_value=False), \
         patch("udm.platform.path.is_linux", return_value=True), \
         patch.object(Path, "home", return_value=tmp_path):

        result = remove_from_path("/opt/mytool/bin")
        assert result is True

        content = rc_file.read_text(encoding="utf-8")
        assert "/opt/mytool/bin" not in content
        assert "/home/user/.local/bin" in content

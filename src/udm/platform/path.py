"""PATH manipulation utilities — user-scope only (square / isolated).

Square-mode guarantee
---------------------
All PATH changes are restricted to the *current user* scope exclusively:
  Windows  ->  HKCU\\Environment              (never HKLM system PATH)
  Linux    ->  ~/.bashrc                       (never /etc/profile or /etc/environment)
  macOS    ->  ~/.zshrc                        (never /etc/paths or /etc/profile)

No other files or registry keys are ever written by this module.
"""

import glob
import os
from pathlib import Path
from typing import Optional

from udm.logger import logger
from udm.platform.detect import is_linux, is_mac, is_windows


def resolve_env_path(raw: str) -> Optional[str]:
    """Expand environment variables and resolve a glob pattern.

    Returns the resolved path string, or None when the pattern contains a
    wildcard that matches no existing directory (tool installed to a
    non-standard location, or directory not yet present on disk).
    """
    expanded = os.path.expandvars(raw)
    expanded = os.path.expanduser(expanded)

    if "*" in expanded:
        matches = glob.glob(expanded)
        if matches:
            # Pick the lexicographically last match (highest version).
            return os.path.normpath(sorted(matches)[-1])
        # Wildcard matched nothing — directory absent or wrong path.
        logger.warning(
            f"PATH glob matched no directories (tool may have installed to a "
            f"non-standard location or needs a shell restart): {expanded}"
        )
        return None

    return os.path.normpath(expanded)


# ── Windows helpers ──────────────────────────────────────────────────────────

def _windows_get_user_path() -> str:
    """Read the current user PATH from HKCU\\Environment (never HKLM)."""
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ
        ) as key:
            value, _ = winreg.QueryValueEx(key, "Path")
            return value
    except FileNotFoundError:
        return ""


def _windows_set_user_path(new_path: str) -> bool:
    """Write *new_path* to HKCU\\Environment\\Path and broadcast the change.

    Square-mode: intentionally targets HKCU (user scope) only.
    The system-wide HKLM key is NEVER touched.
    """
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)

        # Broadcast WM_SETTINGCHANGE so Explorer and open consoles pick up
        # the new PATH without requiring a full logoff/logon.
        import ctypes

        ctypes.windll.user32.SendMessageTimeoutW(
            0xFFFF,   # HWND_BROADCAST
            0x001A,   # WM_SETTINGCHANGE
            0,
            "Environment",
            0x0002,   # SMTO_ABORTIFHUNG
            5000,
            None,
        )
        logger.info("Windows user PATH updated in HKCU\\Environment and change broadcasted.")
        return True
    except Exception as exc:
        logger.error(f"Failed to write Windows user PATH: {exc}")
        return False


# ── Public API ───────────────────────────────────────────────────────────────

def add_to_path(raw_directory: str) -> bool:
    """Add *raw_directory* to the user PATH if it is not already present.

    *raw_directory* may contain environment-variable references such as
    ``%LOCALAPPDATA%`` or ``$HOME``, and glob wildcards (``*``).  The path
    is resolved before being compared against the current PATH.

    Returns True on success or when the entry is already present.
    Returns False when the directory could not be resolved (wildcard matched
    nothing) or when the registry / rc-file write failed.
    """
    resolved = resolve_env_path(raw_directory)
    if resolved is None:
        # Wildcard matched nothing — skip (warning already logged).
        return False

    if is_windows():
        # Square-mode: ONLY writes to HKCU\Environment, never HKLM.
        current = _windows_get_user_path()
        entries = [e.strip() for e in current.split(";") if e.strip()]
        normalised = [os.path.normpath(e) for e in entries]
        if resolved in normalised:
            logger.info(f"User PATH already contains: {resolved}")
            return True
        if not os.path.isdir(resolved):
            logger.warning(
                f"Directory not yet on disk — PATH entry will be valid after "
                f"reopening a terminal: {resolved}"
            )
        entries.append(resolved)
        return _windows_set_user_path(";".join(entries))

    elif is_linux():
        # Square-mode: ONLY ~/.bashrc, never /etc/profile or /etc/environment.
        rc_file = Path.home() / ".bashrc"
        export_line = f'\nexport PATH="$PATH:{resolved}"\n'
        try:
            content = rc_file.read_text(encoding="utf-8") if rc_file.exists() else ""
            if resolved in content:
                logger.info(f"~/.bashrc already exports: {resolved}")
                return True
            with open(rc_file, "a", encoding="utf-8") as f:
                f.write(export_line)
            logger.info(f"Appended to ~/.bashrc: {resolved}")
            return True
        except Exception as exc:
            logger.error(f"Failed to update ~/.bashrc: {exc}")
            return False

    elif is_mac():
        # Square-mode: ONLY ~/.zshrc, never /etc/paths or /etc/profile.
        rc_file = Path.home() / ".zshrc"
        export_line = f'\nexport PATH="$PATH:{resolved}"\n'
        try:
            content = rc_file.read_text(encoding="utf-8") if rc_file.exists() else ""
            if resolved in content:
                logger.info(f"~/.zshrc already exports: {resolved}")
                return True
            with open(rc_file, "a", encoding="utf-8") as f:
                f.write(export_line)
            logger.info(f"Appended to ~/.zshrc: {resolved}")
            return True
        except Exception as exc:
            logger.error(f"Failed to update ~/.zshrc: {exc}")
            return False

    return False

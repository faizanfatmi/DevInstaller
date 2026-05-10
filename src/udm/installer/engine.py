"""Core installation engine — detect, install, and configure PATH."""

import platform

from udm.installer.callbacks import log
from udm.installer.prerequisites import ensure_apt_updated, ensure_homebrew
from udm.platform import (
    add_to_path,
    is_linux,
    is_mac,
    is_windows,
    resolve_env_path,
    run_command,
)


def _get_install_cmd(tool: dict) -> str:
    """Return the install command for the current platform, or '' if none."""
    cmd = ""
    if is_windows():
        cmd = tool.get("install_command_windows", "")
        if cmd.startswith("winget") and "--disable-interactivity" not in cmd:
            cmd += " --disable-interactivity"
    elif is_linux():
        cmd = tool.get("install_command_linux", "")
    elif is_mac():
        cmd = tool.get("install_command_mac", "")
    return cmd


def detect_tool(tool: dict) -> bool:
    """Return True if the tool is already present on the system."""
    detect_cmd = tool.get("detect_cmd", "")
    if not detect_cmd:
        return False
    rc, out, _ = run_command(detect_cmd, timeout=15)
    if rc == 0:
        return True
    alt = tool.get("detect_cmd_alt", "")
    if alt:
        rc2, _, _ = run_command(alt, timeout=15)
        if rc2 == 0:
            return True
    return False


def install_tool(tool: dict) -> bool:
    """Install a single tool using the platform install command."""
    name = tool.get("name", "Unknown")
    cmd = _get_install_cmd(tool)

    if not cmd:
        log(f"  ⚠ No install command for {name} on {platform.system()}")
        return False

    if is_mac():
        ensure_homebrew()
    if is_linux() and cmd.startswith("sudo apt"):
        ensure_apt_updated()

    log(f"  Running: {cmd}")
    rc, out, err = run_command(cmd, timeout=900)

    combined = (out + err).lower()
    if rc == 0:
        return True
    if (
        "already installed" in combined
        or "no upgrade" in combined
        or "is already the newest" in combined
    ):
        log(f"  {name} appears already installed (package manager says so).")
        return True

    out_clean = "\n".join(line.strip() for line in out.splitlines() if line.strip())
    err_clean = "\n".join(line.strip() for line in err.splitlines() if line.strip())
    
    log(f"  stdout: {out_clean[-1000:]}")
    if err_clean:
        log(f"  stderr: {err_clean[-1000:]}")
    return False


def setup_path(tool: dict) -> bool:
    """Add required directories to PATH for the given tool."""
    if not tool.get("path_required", False):
        return True

    key = (
        "path_dirs_windows"
        if is_windows()
        else "path_dirs_linux"
        if is_linux()
        else "path_dirs_mac"
    )
    dirs = tool.get(key, [])
    if not dirs:
        return True

    ok = True
    for d in dirs:
        resolved = resolve_env_path(d)
        log(f"  PATH → {resolved}")
        if not add_to_path(resolved):
            log(f"  ⚠ Could not add {resolved} to PATH")
            ok = False
    return ok

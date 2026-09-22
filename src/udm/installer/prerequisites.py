"""Platform prerequisites — Homebrew, Chocolatey, and per-distro package-index refresh.

The Linux refresh helpers run once per session and go through pkexec so the
native polkit authentication dialog is shown for the privileged step.
"""

import os
import shutil

from udm.installer.callbacks import log
from udm.platform import (
    command_exists,
    is_linux,
    is_mac,
    is_windows,
    run_command,
    run_privileged_command,
)


def is_winget_available() -> bool:
    """Return True if winget is installed and available on Windows."""
    return is_windows() and command_exists("winget")


def is_choco_available() -> bool:
    """Return True if Chocolatey (choco) is installed and available on Windows."""
    if not is_windows():
        return False
    if command_exists("choco"):
        return True
    return os.path.exists(r"C:\ProgramData\chocolatey\bin\choco.exe")


def ensure_windows_prerequisites() -> bool:
    """On Windows, verify winget is present; if winget is absent, ensure Chocolatey is installed.

    Many Windows machines (LTSC, older Windows 10, or systems without Microsoft Store)
    lack winget. In that case, Chocolatey (choco) is installed as the fallback package manager
    so software installations proceed smoothly without failing.
    """
    if not is_windows():
        return True

    if hasattr(ensure_windows_prerequisites, "_done"):
        return getattr(ensure_windows_prerequisites, "_success", True)

    # 1. Check if winget is available
    if command_exists("winget"):
        log("  ✓ Windows Package Manager (winget) detected.")
        ensure_windows_prerequisites._done = True
        ensure_windows_prerequisites._success = True
        return True

    log("  ⚠ Windows Package Manager (winget) is not installed on this system.")

    # 2. Check if Chocolatey is already installed
    choco_exe = shutil.which("choco")
    choco_default_bin = r"C:\ProgramData\chocolatey\bin"
    choco_default_exe = os.path.join(choco_default_bin, "choco.exe")

    if not choco_exe and os.path.exists(choco_default_exe):
        if choco_default_bin not in os.environ.get("PATH", ""):
            os.environ["PATH"] = f"{choco_default_bin};{os.environ['PATH']}"
        choco_exe = choco_default_exe

    if choco_exe or command_exists("choco"):
        log("  ✓ Chocolatey (choco) detected — using Chocolatey as fallback installer.")
        ensure_windows_prerequisites._done = True
        ensure_windows_prerequisites._success = True
        return True

    # 3. Neither winget nor choco exists — install Chocolatey automatically
    log("  ⏳ Installing Chocolatey package manager as fallback…")
    log("     Downloading and configuring Chocolatey, please wait…")

    ps_cmd = [
        "powershell.exe",
        "-NoProfile",
        "-InputFormat", "None",
        "-ExecutionPolicy", "Bypass",
        "-Command",
        "[System.Net.ServicePointManager]::SecurityProtocol = 3072; "
        "iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    ]
    rc, out, err = run_command(ps_cmd, timeout=300)

    # Re-check default bin directory and update PATH
    if os.path.exists(choco_default_bin):
        if choco_default_bin not in os.environ.get("PATH", ""):
            os.environ["PATH"] = f"{choco_default_bin};{os.environ['PATH']}"

    if rc == 0 or os.path.exists(choco_default_exe) or command_exists("choco"):
        log("  ✓ Chocolatey successfully installed and ready for package installations!")
        ensure_windows_prerequisites._done = True
        ensure_windows_prerequisites._success = True
        return True
    else:
        log(f"  ⚠ Failed to install Chocolatey automatically (exit {rc}).")
        if err:
            log(f"    stderr: {err[:300]}")
        ensure_windows_prerequisites._done = True
        ensure_windows_prerequisites._success = False
        return False


def ensure_homebrew():
    """On macOS, install Homebrew if it is not present."""
    if is_mac() and not command_exists("brew"):
        log("  Homebrew not found — installing…")
        cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        rc, out, err = run_command(cmd, timeout=300)
        if rc != 0:
            log(f"  ⚠ Homebrew install failed: {err[:200]}")
        else:
            log("  ✓ Homebrew installed.")


def ensure_apt_updated():
    """Run `apt-get update` once per session on Debian-family Linux."""
    if not is_linux():
        return
    if not hasattr(ensure_apt_updated, "_done"):
        log("  Updating apt package index…")
        run_privileged_command("apt-get update -y", timeout=120)
        ensure_apt_updated._done = True


def ensure_pacman_synced():
    """Refresh the pacman database once per session on Arch-family Linux."""
    if not is_linux():
        return
    if not hasattr(ensure_pacman_synced, "_done"):
        log("  Synchronising pacman database…")
        run_privileged_command("pacman -Sy --noconfirm", timeout=180)
        ensure_pacman_synced._done = True


def ensure_dnf_ready():
    """Refresh dnf metadata once per session on Fedora-family Linux."""
    if not is_linux():
        return
    if not hasattr(ensure_dnf_ready, "_done"):
        log("  Refreshing dnf metadata…")
        run_privileged_command("dnf makecache -y", timeout=180)
        ensure_dnf_ready._done = True

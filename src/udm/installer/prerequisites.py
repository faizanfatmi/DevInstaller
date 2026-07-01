"""Platform prerequisites — Homebrew and per-distro package-index refresh.

The Linux refresh helpers run once per session and go through pkexec so the
native polkit authentication dialog is shown for the privileged step.
"""

from udm.installer.callbacks import log
from udm.platform import (
    command_exists,
    is_linux,
    is_mac,
    run_command,
    run_privileged_command,
)


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

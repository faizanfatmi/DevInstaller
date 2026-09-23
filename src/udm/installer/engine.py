"""Core installation engine — detect, install, and configure PATH.

On Linux the correct install command is chosen per distribution family
(Arch / Fedora / Debian). Tools may provide distro-specific commands via
``install_command_arch`` / ``install_command_fedora`` / ``install_command_debian``;
when absent, the engine falls back to the generic ``install_command_linux`` so
existing tools.json entries continue to work unchanged.

Privileged package-manager operations are executed through pkexec so the native
polkit password dialog is displayed.
"""

import platform

from udm.installer.callbacks import log
from udm.installer.distro_packages import translate_apt_command
from udm.installer.prerequisites import (
    ensure_apt_updated,
    ensure_dnf_ready,
    ensure_homebrew,
    ensure_pacman_synced,
    ensure_windows_prerequisites,
    is_winget_available,
)
from udm.installer.windows_packages import translate_winget_to_choco
from udm.platform import (
    add_to_path,
    friendly_pkexec_message,
    is_linux,
    is_mac,
    is_supported_linux,
    is_windows,
    linux_distro_family,
    linux_distro_name,
    resolve_env_path,
    run_command,
    run_privileged_command,
)

# Package managers whose invocations require root (routed via pkexec on Linux).
_PRIVILEGED_MANAGERS = ("apt", "apt-get", "pacman", "dnf", "yum", "zypper")


def _linux_install_cmd(tool: dict) -> str:
    """Return the best install command for the current Linux distro family.

    Falls back to the generic ``install_command_linux`` field.
    """
    family = linux_distro_family()
    per_family_key = {
        "arch": "install_command_arch",
        "fedora": "install_command_fedora",
        "debian": "install_command_debian",
        "suse": "install_command_suse",
    }.get(family)

    # 1) An explicit per-distro command in tools.json always wins.
    if per_family_key and tool.get(per_family_key):
        return tool[per_family_key]

    linux_cmd = tool.get("install_command_linux", "")

    # 2) For Arch/Fedora, derive a native command from the apt command when
    #    possible (non-apt commands like npm/pip/curl are cross-distro and are
    #    returned unchanged by the translator).
    if family in ("arch", "fedora"):
        derived = translate_apt_command(linux_cmd, family)
        if derived:
            return derived

    # 3) Fall back to the generic linux command.
    return linux_cmd


def _get_install_cmd(tool: dict) -> str:
    """Return the install command for the current platform, or '' if none."""
    cmd = ""
    if is_windows():
        cmd = tool.get("install_command_windows", "")
        # If winget is not available on this Windows system, translate to Chocolatey
        if cmd and "winget" in cmd and not is_winget_available():
            cmd = translate_winget_to_choco(cmd, tool)
    elif is_linux():
        cmd = _linux_install_cmd(tool)
    elif is_mac():
        cmd = tool.get("install_command_mac", "")
    return cmd


def _strip_sudo(cmd: str) -> str:
    """Remove a leading 'sudo ' so we do not double-elevate under pkexec."""
    stripped = cmd.strip()
    if stripped.startswith("sudo "):
        return stripped[len("sudo "):].strip()
    return stripped


def _needs_privilege(cmd: str) -> bool:
    """Return True if *cmd* invokes a package manager that requires root."""
    first = _strip_sudo(cmd).split()
    if not first:
        return False
    head = first[0]
    return cmd.strip().startswith("sudo ") or head in _PRIVILEGED_MANAGERS


def detect_tool(tool: dict) -> bool:
    """Return True if the tool is already present on the system."""
    key = tool.get("key", "")
    if key == "oracle_db_xe":
        from udm.installer.oracle import detect_oracle_db
        return detect_oracle_db()
    elif key == "oracle_sql_developer":
        from udm.installer.oracle import detect_sql_developer
        return detect_sql_developer()

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


def uninstall_tool(tool: dict) -> bool:
    """Uninstall a tool using platform-specific commands or custom modules."""
    name = tool.get("name", "Unknown")
    key = tool.get("key", "")

    # Oracle custom uninstaller
    if key == "oracle_db_xe":
        from udm.installer.oracle import uninstall_oracle_db
        log(f"Uninstalling {name} (complete wipeout)…")
        return uninstall_oracle_db()
    elif key == "oracle_sql_developer":
        from udm.installer.oracle import uninstall_sql_developer
        log(f"Uninstalling {name}…")
        return uninstall_sql_developer()

    log(f"Uninstalling {name}…")

    if is_windows():
        cmd = tool.get("install_command_windows", "")
        # Check winget command: winget install --id <Id> ...
        if "winget install" in cmd:
            import re
            m = re.search(r"--id\s+([^\s]+)", cmd)
            if m:
                pkg_id = m.group(1)
                uninst_cmd = f"winget uninstall --id {pkg_id} --silent --accept-source-agreements"
                rc, out, err = run_command(uninst_cmd, timeout=300)
                if rc == 0:
                    log(f"  ✓ {name} uninstalled via winget.")
                    return True
                else:
                    log(f"  ⚠ winget uninstall failed: {err}")
        # Check choco command: choco install <pkg> -y
        if "choco install" in cmd:
            parts = cmd.split()
            if len(parts) >= 3:
                pkg = parts[2]
                uninst_cmd = f"choco uninstall {pkg} -y"
                rc, out, err = run_command(uninst_cmd, timeout=300)
                if rc == 0:
                    log(f"  ✓ {name} uninstalled via Chocolatey.")
                    return True
                else:
                    log(f"  ⚠ choco uninstall failed: {err}")
        log(f"  ⚠ No automatic uninstall command found for {name} on Windows.")
        return False

    elif is_linux():
        cmd = tool.get("install_command_linux", "")
        if "apt" in cmd or "apt-get" in cmd:
            parts = cmd.split()
            pkg = parts[-1]
            rc, out, err = run_command(f"sudo apt-get remove -y {pkg}", timeout=300)
            return rc == 0
        elif "pacman" in cmd:
            parts = cmd.split()
            pkg = parts[-1]
            rc, out, err = run_command(f"sudo pacman -R --noconfirm {pkg}", timeout=300)
            return rc == 0
        elif "dnf" in cmd:
            parts = cmd.split()
            pkg = parts[-1]
            rc, out, err = run_command(f"sudo dnf remove -y {pkg}", timeout=300)
            return rc == 0

    elif is_mac():
        cmd = tool.get("install_command_mac", "")
        if "brew install" in cmd:
            parts = cmd.split()
            pkg = parts[-1]
            rc, out, err = run_command(f"brew uninstall {pkg}", timeout=300)
            return rc == 0

    return False


def can_uninstall(tool: dict) -> bool:
    """Return True if DevInstaller knows how to uninstall this tool."""
    key = tool.get("key", "")
    if key in ("oracle_db_xe", "oracle_sql_developer"):
        return True
    if is_windows():
        cmd = tool.get("install_command_windows", "")
        return "winget install" in cmd or "choco install" in cmd
    elif is_linux():
        cmd = tool.get("install_command_linux", "")
        return any(mgr in cmd for mgr in ("apt", "pacman", "dnf"))
    elif is_mac():
        cmd = tool.get("install_command_mac", "")
        return "brew install" in cmd
    return False



def _run_linux_prerequisites(cmd: str) -> None:
    """Run the once-per-session index refresh for the detected package manager."""
    head = _strip_sudo(cmd).split()[0] if _strip_sudo(cmd).split() else ""
    if head in ("apt", "apt-get"):
        ensure_apt_updated()
    elif head == "pacman":
        ensure_pacman_synced()
    elif head in ("dnf", "yum"):
        ensure_dnf_ready()


def install_tool(tool: dict) -> bool:
    """Install a single tool using the platform install command."""
    name = tool.get("name", "Unknown")

    # Guard against unsupported Linux distributions before doing anything.
    if is_linux() and not is_supported_linux():
        log(
            f"  ✗ {linux_distro_name()} is not a supported Linux distribution. "
            "Supported families: Arch, Fedora, Debian/Ubuntu."
        )
        return False

    cmd = _get_install_cmd(tool)

    # ── Oracle custom handler ────────────────────────────────────────
    # Tools with the ``__oracle_custom__`` sentinel are handled by the
    # dedicated oracle module; the batch installer calls oracle_lifecycle
    # instead, but if a single Oracle tool reaches here directly, delegate.
    if cmd == "__oracle_custom__":
        from udm.installer.oracle import install_oracle_db, install_sql_developer

        key = tool.get("key", "")
        if key == "oracle_db_xe":
            return install_oracle_db()
        elif key == "oracle_sql_developer":
            archive_path = tool.get("archive_path")
            return install_sql_developer(archive_path=archive_path)
        log(f"  ⚠ Unknown Oracle tool key: {key}")
        return False

    if not cmd:
        if is_linux():
            log(
                f"  ⚠ No install command for {name} on "
                f"{linux_distro_name()}."
            )
        else:
            log(f"  ⚠ No install command for {name} on {platform.system()}")
        return False

    if is_mac():
        ensure_homebrew()
    elif is_windows():
        ensure_windows_prerequisites()

    if is_linux():
        _run_linux_prerequisites(cmd)
        if _needs_privilege(cmd):
            exec_cmd = _strip_sudo(cmd)
            log(f"  Running (elevated): {exec_cmd}")
            rc, out, err = run_privileged_command(exec_cmd, timeout=900)
        else:
            log(f"  Running: {cmd}")
            rc, out, err = run_command(cmd, timeout=900)
    else:
        log(f"  Running: {cmd}")
        rc, out, err = run_command(cmd, timeout=900)

    combined = (out + err).lower()
    if rc == 0:
        return True

    # Surface a clear elevation message when pkexec was declined/cancelled.
    if is_linux() and rc in (126, 127):
        log(f"  ✗ {friendly_pkexec_message(rc)}")
        return False

    if rc in (-1978335189, 2316632107, 3010):
        log(f"  ✓ {name} is already up to date on system.")
        return True

    if (
        "already installed" in combined
        or "no upgrade" in combined
        or "is already the newest" in combined
        or "nothing to do" in combined
        or "no available upgrade" in combined
        or "package is not available" in combined
        or "no changes made" in combined
        or "install was successful" in combined
        or "installed to" in combined
    ):
        log(f"  ✓ {name} appears already installed or successfully set up.")
        return True

    out_clean = "\n".join(line.strip() for line in out.splitlines() if line.strip())
    err_clean = "\n".join(line.strip() for line in err.splitlines() if line.strip())

    log(f"  ✗ Install failed (exit {rc})")
    if out_clean:
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
        log(f"  PATH <- {d}")
        if not add_to_path(d):
            log(f"  ⚠ Could not add to PATH: {d}")
            ok = False
    return ok

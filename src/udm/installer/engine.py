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
from typing import Callable, Optional

from udm.installer.callbacks import log
from udm.installer.distro_packages import translate_apt_command
from udm.installer.progress import parse_progress
from udm.installer.prerequisites import (
    ensure_apt_updated,
    ensure_dnf_ready,
    ensure_homebrew,
    ensure_pacman_synced,
    ensure_windows_prerequisites,
    is_choco_available,
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
    remove_from_path,
    resolve_env_path,
    run_command,
    run_command_streamed,
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


def _clean_tool_shortcuts(tool: dict) -> None:
    """Remove desktop and Start Menu shortcuts created for this tool."""
    import os
    if not is_windows():
        return

    name = tool.get("name", "")
    key = tool.get("key", "")
    binary = tool.get("binary", "")

    keywords = {name.lower(), key.lower()}
    if binary:
        keywords.add(binary.lower().replace(".exe", ""))

    search_dirs = [
        os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
        os.path.join(os.environ.get("PUBLIC", ""), "Desktop"),
        os.path.join(
            os.environ.get("APPDATA", ""),
            r"Microsoft\Windows\Start Menu\Programs",
        ),
        os.path.join(
            os.environ.get("PROGRAMDATA", ""),
            r"Microsoft\Windows\Start Menu\Programs",
        ),
    ]

    for base in search_dirs:
        if not base or not os.path.isdir(base):
            continue
        try:
            for root, dirs, files in os.walk(base):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        stem = os.path.splitext(f.lower())[0]
                        if any(k in stem for k in keywords if len(k) >= 3):
                            full_path = os.path.join(root, f)
                            try:
                                os.remove(full_path)
                                log(f"    Removed shortcut: {full_path}")
                            except Exception:
                                pass
        except Exception:
            pass


def _clean_tool_paths(tool: dict) -> None:
    """Remove tool path directories from user PATH."""
    dirs = []
    dirs.extend(tool.get("path_dirs", []))
    if is_windows():
        dirs.extend(tool.get("path_dirs_windows", []))
    elif is_linux():
        dirs.extend(tool.get("path_dirs_linux", []))
    elif is_mac():
        dirs.extend(tool.get("path_dirs_mac", []))

    for d in dirs:
        if d:
            remove_from_path(d)


def _clean_tool_residuals(tool: dict) -> None:
    """Remove leftover installation folders in user space if detected."""
    import os
    import shutil

    dirs = []
    if is_windows():
        dirs.extend(tool.get("path_dirs_windows", []))
        dirs.extend(tool.get("path_dirs", []))
    elif is_linux():
        dirs.extend(tool.get("path_dirs_linux", []))
        dirs.extend(tool.get("path_dirs", []))
    elif is_mac():
        dirs.extend(tool.get("path_dirs_mac", []))
        dirs.extend(tool.get("path_dirs", []))

    user_prefix = os.path.expanduser("~").lower()
    local_app_data = os.environ.get("LOCALAPPDATA", "").lower()
    app_data = os.environ.get("APPDATA", "").lower()

    for raw in dirs:
        resolved = resolve_env_path(raw)
        if not resolved or not os.path.isdir(resolved):
            continue
        norm = os.path.normpath(resolved).lower()
        is_user_space = (
            norm.startswith(user_prefix)
            or (local_app_data and norm.startswith(local_app_data))
            or (app_data and norm.startswith(app_data))
        )
        if is_user_space and len(norm) > len(user_prefix) + 3:
            try:
                target_dir = resolved
                if os.path.basename(target_dir).lower() == "bin":
                    parent = os.path.dirname(target_dir)
                    tool_name = tool.get("name", "").lower()
                    tool_key = tool.get("key", "").lower()
                    if tool_key in os.path.basename(parent).lower() or tool_name in os.path.basename(parent).lower():
                        target_dir = parent
                shutil.rmtree(target_dir, ignore_errors=True)
                log(f"    Removed leftover directory: {target_dir}")
            except Exception:
                pass


def uninstall_tool(tool: dict) -> bool:
    """Uninstall a tool completely using package managers, PATH cleaning, and shortcut wipeout."""
    name = tool.get("name", "Unknown")
    key = tool.get("key", "")

    # Oracle custom uninstaller
    if key == "oracle_db_xe":
        from udm.installer.oracle import uninstall_oracle_db
        log(f"Uninstalling {name} (complete wipeout)…")
        res = uninstall_oracle_db()
        _clean_tool_paths(tool)
        _clean_tool_shortcuts(tool)
        return res
    elif key == "oracle_sql_developer":
        from udm.installer.oracle import uninstall_sql_developer
        log(f"Uninstalling {name}…")
        res = uninstall_sql_developer()
        _clean_tool_paths(tool)
        _clean_tool_shortcuts(tool)
        return res

    log(f"Uninstalling {name}…")
    cmd_success = False

    if is_windows():
        cmd = tool.get("install_command_windows", "")
        # 1. Winget
        if "winget install" in cmd:
            import re
            m = re.search(r"--id\s+([^\s]+)", cmd)
            if m:
                pkg_id = m.group(1)
                uninst_cmd = f"winget uninstall --id {pkg_id} --silent --accept-source-agreements --force"
                rc, out, err = run_command(uninst_cmd, timeout=300)
                if rc == 0:
                    log(f"  ✓ {name} uninstalled via winget.")
                    cmd_success = True
                else:
                    log(f"  ℹ winget uninstall output: {out} {err}")

        # 2. Chocolatey (or fallback if winget didn't find package)
        if ("choco install" in cmd or not cmd_success) and is_choco_available():
            pkg = None
            if "choco install" in cmd:
                parts = cmd.split()
                if len(parts) >= 3:
                    pkg = parts[2]
            if pkg:
                uninst_cmd = f"choco uninstall {pkg} -y --remove-dependencies"
                rc, out, err = run_command(uninst_cmd, timeout=300)
                if rc == 0:
                    log(f"  ✓ {name} uninstalled via Chocolatey.")
                    cmd_success = True

        # 3. NPM global package
        if "npm install -g" in cmd:
            parts = cmd.split("npm install -g")
            if len(parts) > 1:
                pkg = parts[1].strip().split()[0]
                uninst_cmd = f"npm uninstall -g {pkg}"
                rc, out, err = run_command(uninst_cmd, timeout=120)
                if rc == 0:
                    log(f"  ✓ {name} uninstalled via npm.")
                    cmd_success = True

        # 4. Pip package
        if "pip install" in cmd:
            parts = cmd.split("pip install")
            if len(parts) > 1:
                pkg = parts[1].strip().split()[0]
                uninst_cmd = f"python -m pip uninstall -y {pkg}"
                rc, out, err = run_command(uninst_cmd, timeout=120)
                if rc == 0:
                    log(f"  ✓ {name} uninstalled via pip.")
                    cmd_success = True

        # 5. Cargo package
        if "cargo install" in cmd:
            parts = cmd.split("cargo install")
            if len(parts) > 1:
                pkg = parts[1].strip().split()[0]
                uninst_cmd = f"cargo uninstall {pkg}"
                rc, out, err = run_command(uninst_cmd, timeout=120)
                if rc == 0:
                    log(f"  ✓ {name} uninstalled via cargo.")
                    cmd_success = True

        # 6. Dotnet tool
        if "dotnet tool install" in cmd:
            parts = cmd.split("dotnet tool install")
            if len(parts) > 1:
                pkg = parts[1].replace("-g", "").strip().split()[0]
                uninst_cmd = f"dotnet tool uninstall -g {pkg}"
                rc, out, err = run_command(uninst_cmd, timeout=120)
                if rc == 0:
                    log(f"  ✓ {name} uninstalled via dotnet.")
                    cmd_success = True

    elif is_linux():
        cmd = tool.get("install_command_linux", "")
        if "apt" in cmd or "apt-get" in cmd:
            parts = cmd.split()
            pkg = parts[-1]
            rc, out, err = run_command(f"sudo apt-get purge -y {pkg}", timeout=300)
            cmd_success = (rc == 0)
        elif "pacman" in cmd:
            parts = cmd.split()
            pkg = parts[-1]
            rc, out, err = run_command(f"sudo pacman -Rns --noconfirm {pkg}", timeout=300)
            cmd_success = (rc == 0)
        elif "dnf" in cmd:
            parts = cmd.split()
            pkg = parts[-1]
            rc, out, err = run_command(f"sudo dnf remove -y {pkg}", timeout=300)
            cmd_success = (rc == 0)
        elif "pip install" in cmd:
            parts = cmd.split("pip install")
            if len(parts) > 1:
                pkg = parts[1].strip().split()[0]
                rc, _, _ = run_command(f"pip uninstall -y {pkg}", timeout=120)
                cmd_success = (rc == 0)
        elif "npm install -g" in cmd:
            parts = cmd.split("npm install -g")
            if len(parts) > 1:
                pkg = parts[1].strip().split()[0]
                rc, _, _ = run_command(f"npm uninstall -g {pkg}", timeout=120)
                cmd_success = (rc == 0)
        elif "cargo install" in cmd:
            parts = cmd.split("cargo install")
            if len(parts) > 1:
                pkg = parts[1].strip().split()[0]
                rc, _, _ = run_command(f"cargo uninstall {pkg}", timeout=120)
                cmd_success = (rc == 0)

    elif is_mac():
        cmd = tool.get("install_command_mac", "")
        if "brew install" in cmd:
            parts = cmd.split()
            pkg = parts[-1]
            rc, out, err = run_command(f"brew uninstall {pkg}", timeout=300)
            cmd_success = (rc == 0)
        elif "pip install" in cmd:
            parts = cmd.split("pip install")
            if len(parts) > 1:
                pkg = parts[1].strip().split()[0]
                rc, _, _ = run_command(f"pip uninstall -y {pkg}", timeout=120)
                cmd_success = (rc == 0)
        elif "npm install -g" in cmd:
            parts = cmd.split("npm install -g")
            if len(parts) > 1:
                pkg = parts[1].strip().split()[0]
                rc, _, _ = run_command(f"npm uninstall -g {pkg}", timeout=120)
                cmd_success = (rc == 0)
        elif "cargo install" in cmd:
            parts = cmd.split("cargo install")
            if len(parts) > 1:
                pkg = parts[1].strip().split()[0]
                rc, _, _ = run_command(f"cargo uninstall {pkg}", timeout=120)
                cmd_success = (rc == 0)

    # Perform deep clean of user PATH entries, shortcuts, and leftover files
    _clean_tool_paths(tool)
    _clean_tool_shortcuts(tool)
    _clean_tool_residuals(tool)

    # Verification: check if tool is still detected
    if not detect_tool(tool):
        log(f"  ✓ {name} completely uninstalled and removed from system.")
        return True
    elif cmd_success:
        log(f"  ✓ {name} uninstalled (command completed).")
        return True
    else:
        log(f"  ⚠ Could not completely remove {name}.")
        return False


def can_uninstall(tool: dict) -> bool:
    """Return True if DevInstaller knows how to uninstall this tool."""
    key = tool.get("key", "")
    if key in ("oracle_db_xe", "oracle_sql_developer"):
        return True
    if is_windows():
        cmd = tool.get("install_command_windows", "")
        return any(mgr in cmd for mgr in (
            "winget install",
            "choco install",
            "npm install -g",
            "pip install",
            "cargo install",
            "dotnet tool install",
        ))
    elif is_linux():
        cmd = tool.get("install_command_linux", "")
        return any(mgr in cmd for mgr in (
            "apt",
            "pacman",
            "dnf",
            "pip install",
            "npm install -g",
            "cargo install",
        ))
    elif is_mac():
        cmd = tool.get("install_command_mac", "")
        return any(mgr in cmd for mgr in (
            "brew install",
            "pip install",
            "npm install -g",
            "cargo install",
        ))
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


def _augment_winget(cmd: str) -> str:
    """Append ``--disable-interactivity`` to a winget command when missing.

    winget renders a live spinner unless interactivity is disabled; turning it
    off gives clean, deterministic output when stdout is a pipe (which is how we
    stream progress) and avoids the occasional hang waiting on a prompt.
    """
    if "winget" not in cmd or "--disable-interactivity" in cmd:
        return cmd
    return cmd + " --disable-interactivity"


# Output signatures that mean "winget could not find/apply this package" — the
# trigger for the automatic Chocolatey fallback.
_WINGET_NOTFOUND_MARKERS = (
    "no package found",
    "no applicable",
    "no installed package found",
    "found in the following sources",  # ambiguous / no exact match
    "0x8a15000f",
    "0x8a150014",
)


def _looks_like_winget_notfound(rc: int, combined: str) -> bool:
    """Return True if a winget run failed because the package wasn't found."""
    return rc != 0 and any(m in combined for m in _WINGET_NOTFOUND_MARKERS)


def _run_install_command(
    cmd: str,
    progress_cb: Optional[Callable[[int], None]],
    timeout: int = 900,
) -> tuple[int, str, str]:
    """Run *cmd*, streaming live progress to *progress_cb* when provided.

    Falls back to the plain (buffered) ``run_command`` when no callback is given
    so existing callers keep identical behaviour.
    """
    if progress_cb is None:
        return run_command(cmd, timeout=timeout)

    last = {"pct": 0}

    def _on_output(segment: str) -> None:
        pct = parse_progress(segment)
        if pct is not None and pct >= last["pct"]:
            last["pct"] = pct
            progress_cb(pct)

    return run_command_streamed(cmd, on_output=_on_output, timeout=timeout)


def install_tool(tool: dict, progress_cb: Optional[Callable[[int], None]] = None) -> bool:
    """Install a single tool using the platform install command.

    *progress_cb*, when supplied, receives a live 0-100 percentage parsed from the
    package manager's streamed output. When omitted, behaviour is unchanged.
    """
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
            return install_oracle_db(progress_cb=progress_cb)
        elif key == "oracle_sql_developer":
            archive_path = tool.get("archive_path")
            return install_sql_developer(archive_path=archive_path, progress_cb=progress_cb)
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
            rc, out, err = _run_install_command(cmd, progress_cb, timeout=900)
    else:
        run_cmd = _augment_winget(cmd) if is_windows() else cmd
        log(f"  Running: {run_cmd}")
        rc, out, err = _run_install_command(run_cmd, progress_cb, timeout=900)

    combined = (out + err).lower()

    # ── Windows: automatic Chocolatey fallback when winget can't find/apply ──
    if is_windows() and "winget" in cmd and _looks_like_winget_notfound(rc, combined):
        choco_cmd = translate_winget_to_choco(cmd, tool)
        if choco_cmd and "winget" not in choco_cmd:
            log(f"  ℹ winget could not install {name}; falling back to Chocolatey…")
            ensure_windows_prerequisites()  # installs choco if absent
            log(f"  Running (fallback): {choco_cmd}")
            rc, out, err = _run_install_command(choco_cmd, progress_cb, timeout=900)
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

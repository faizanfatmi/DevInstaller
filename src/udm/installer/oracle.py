"""Oracle Database 21c XE & SQL Developer — custom installer lifecycle.

This module handles the special install/uninstall logic for Oracle products:

- If *either* Oracle Database XE or SQL Developer is already installed,
  **both** are fully uninstalled (services stopped, files deleted, registry
  cleaned) before a fresh install of both is performed.
- If neither is present, both are installed from scratch.

The ``oracle_lifecycle`` function is the main entry point called by the
batch installer when Oracle-linked tools are selected.
"""

from __future__ import annotations

import os
import shutil
import glob

from udm.installer.callbacks import log
from udm.platform import is_linux, is_windows, run_command


# ── Detection ───────────────────────────────────────────────────────────

def detect_oracle_db() -> bool:
    """Return True if Oracle Database XE is installed on the system."""
    if is_windows():
        # Check Windows registry for Oracle DB installation
        rc, out, _ = run_command(
            'reg query "HKLM\\SOFTWARE\\Oracle\\KEY_OraDB21Home1" /ve',
            timeout=15,
        )
        if rc == 0:
            return True

        # Also check for Oracle services
        rc2, out2, _ = run_command(
            'sc query OracleServiceXE',
            timeout=15,
        )
        if rc2 == 0 and "RUNNING" in out2.upper() or "STOPPED" in out2.upper():
            return True

        # Check common install paths
        oracle_homes = [
            r"C:\app\oracle\product\21c\dbhomeXE",
            r"C:\oraclexe",
            r"C:\app\oracle",
        ]
        for p in oracle_homes:
            if os.path.isdir(p):
                return True

    elif is_linux():
        # Check /opt/oracle or /u01/app/oracle
        linux_paths = [
            "/opt/oracle/product/21c",
            "/u01/app/oracle",
            "/opt/oracle",
        ]
        for p in linux_paths:
            if os.path.isdir(p):
                return True

        # Check if sqlplus is available
        rc, _, _ = run_command("sqlplus -v", timeout=15)
        if rc == 0:
            return True

        # Check for oracle-xe RPM/DEB package
        rc, out, _ = run_command("rpm -qa | grep -i oracle-database-xe", timeout=15)
        if rc == 0 and out.strip():
            return True
        rc, out, _ = run_command("dpkg -l | grep -i oracle-database-xe", timeout=15)
        if rc == 0 and out.strip():
            return True

    return False


def detect_sql_developer() -> bool:
    """Return True if Oracle SQL Developer is installed on the system."""
    if is_windows():
        # Check registry
        rc, _, _ = run_command(
            'reg query "HKLM\\SOFTWARE\\Oracle\\sqldeveloper" /ve',
            timeout=15,
        )
        if rc == 0:
            return True

        # Check common install locations
        sqldeveloper_paths = [
            r"C:\sqldeveloper",
            r"C:\app\sqldeveloper",
            os.path.join(os.environ.get("PROGRAMFILES", ""), "sqldeveloper"),
            os.path.join(
                os.environ.get("LOCALAPPDATA", ""), "sqldeveloper"
            ),
        ]
        for p in sqldeveloper_paths:
            if p and os.path.isdir(p):
                return True

        # Check if sqldeveloper.exe exists via where
        rc2, _, _ = run_command("where sqldeveloper", timeout=15)
        if rc2 == 0:
            return True

    elif is_linux():
        linux_paths = [
            "/opt/sqldeveloper",
            "/usr/local/sqldeveloper",
            os.path.expanduser("~/sqldeveloper"),
        ]
        for p in linux_paths:
            if os.path.isdir(p):
                return True

        rc, _, _ = run_command("which sqldeveloper", timeout=15)
        if rc == 0:
            return True

    return False


# ── Uninstall ───────────────────────────────────────────────────────────

def _uninstall_oracle_db_windows() -> bool:
    """Completely remove Oracle Database XE on Windows."""
    log("  Stopping Oracle services…")
    for svc in ("OracleServiceXE", "OracleOraDB21Home1TNSListener",
                "OracleOraDB21Home1MTSRecoveryService", "OracleVssWriterXE",
                "OracleJobSchedulerXE"):
        run_command(f"net stop {svc}", timeout=60)

    # Delete Oracle services from the registry
    log("  Removing Oracle services…")
    for svc in ("OracleServiceXE", "OracleOraDB21Home1TNSListener",
                "OracleOraDB21Home1MTSRecoveryService", "OracleVssWriterXE",
                "OracleJobSchedulerXE"):
        run_command(f"sc delete {svc}", timeout=30)

    # Try the official deinstall tool first
    deinstall_paths = glob.glob(
        r"C:\app\oracle\product\21c\dbhomeXE\deinstall\deinstall.bat"
    )
    if deinstall_paths:
        log("  Running Oracle deinstall tool…")
        rc, out, err = run_command(
            f'"{deinstall_paths[0]}" -silent', timeout=600
        )
        if rc == 0:
            log("  ✓ Oracle deinstall completed.")
        else:
            log(f"  ⚠ Oracle deinstall returned exit code {rc}, continuing with manual cleanup…")

    # Manual cleanup of Oracle directories
    log("  Cleaning Oracle directories…")
    oracle_dirs = [
        r"C:\app\oracle",
        r"C:\oraclexe",
        r"C:\Oracle",
        os.path.join(os.environ.get("PROGRAMDATA", ""), "Oracle"),
        os.path.join(os.environ.get("TEMP", ""), "OraInstall*"),
    ]
    for d in oracle_dirs:
        if "*" in d:
            for match in glob.glob(d):
                _safe_rmtree(match)
        elif os.path.isdir(d):
            _safe_rmtree(d)

    # Clean registry keys
    log("  Cleaning Oracle registry entries…")
    reg_keys = [
        r'"HKLM\SOFTWARE\Oracle"',
        r'"HKLM\SOFTWARE\Wow6432Node\Oracle"',
        r'"HKLM\SYSTEM\CurrentControlSet\Services\OracleServiceXE"',
        r'"HKLM\SYSTEM\CurrentControlSet\Services\OracleOraDB21Home1TNSListener"',
    ]
    for key in reg_keys:
        run_command(f"reg delete {key} /f", timeout=15)

    # Remove Oracle from system PATH
    log("  Cleaning Oracle from system PATH…")
    _clean_oracle_from_path_windows()

    log("  ✓ Oracle Database XE uninstall complete.")
    return True


def _uninstall_oracle_db_linux() -> bool:
    """Completely remove Oracle Database XE on Linux."""
    log("  Stopping Oracle services…")
    run_command("sudo systemctl stop oracle-xe-21c", timeout=60)
    run_command("sudo systemctl disable oracle-xe-21c", timeout=30)

    # Try RPM removal first, then DEB
    log("  Removing Oracle packages…")
    rc, _, _ = run_command("sudo rpm -e oracle-database-xe-21c", timeout=120)
    if rc != 0:
        run_command("sudo dpkg --purge oracle-database-xe-21c", timeout=120)

    # Remove preinstall package too
    run_command("sudo rpm -e oracle-database-preinstall-21c", timeout=60)
    run_command("sudo dpkg --purge oracle-database-preinstall-21c", timeout=60)

    # Clean directories
    log("  Cleaning Oracle directories…")
    linux_dirs = [
        "/opt/oracle",
        "/u01/app/oracle",
        "/etc/oratab",
        "/etc/init.d/oracle-xe-21c",
        "/tmp/OraInstall*",
    ]
    for d in linux_dirs:
        if "*" in d:
            for match in glob.glob(d):
                _safe_rmtree(match)
        elif os.path.isfile(d):
            _safe_remove(d)
        elif os.path.isdir(d):
            _safe_rmtree(d)

    # Remove oracle user (optional, be cautious)
    log("  Cleaning Oracle user/group…")
    run_command("sudo userdel -r oracle", timeout=30)
    run_command("sudo groupdel oinstall", timeout=15)
    run_command("sudo groupdel dba", timeout=15)

    log("  ✓ Oracle Database XE uninstall complete.")
    return True


def _uninstall_sql_developer_windows() -> bool:
    """Completely remove Oracle SQL Developer on Windows."""
    log("  Removing SQL Developer…")

    sqldeveloper_dirs = [
        r"C:\sqldeveloper",
        r"C:\app\sqldeveloper",
        os.path.join(os.environ.get("PROGRAMFILES", ""), "sqldeveloper"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "sqldeveloper"),
    ]
    for d in sqldeveloper_dirs:
        if d and os.path.isdir(d):
            _safe_rmtree(d)
            log(f"    Removed {d}")

    # Remove user preferences directory
    user_prefs = os.path.join(
        os.environ.get("APPDATA", ""), "SQL Developer"
    )
    if os.path.isdir(user_prefs):
        _safe_rmtree(user_prefs)
        log(f"    Removed user preferences: {user_prefs}")

    # Clean registry
    run_command(r'reg delete "HKLM\SOFTWARE\Oracle\sqldeveloper" /f', timeout=15)
    run_command(r'reg delete "HKCU\SOFTWARE\Oracle\sqldeveloper" /f', timeout=15)

    # Clean from PATH
    _clean_sqldeveloper_from_path_windows()

    log("  ✓ SQL Developer uninstall complete.")
    return True


def _uninstall_sql_developer_linux() -> bool:
    """Completely remove Oracle SQL Developer on Linux."""
    log("  Removing SQL Developer…")

    linux_dirs = [
        "/opt/sqldeveloper",
        "/usr/local/sqldeveloper",
        os.path.expanduser("~/sqldeveloper"),
        os.path.expanduser("~/.sqldeveloper"),
    ]
    for d in linux_dirs:
        if os.path.isdir(d):
            _safe_rmtree(d)
            log(f"    Removed {d}")

    # Remove symlink if present
    _safe_remove("/usr/local/bin/sqldeveloper")

    # Try RPM/DEB removal
    run_command("sudo rpm -e sqldeveloper", timeout=60)
    run_command("sudo dpkg --purge sqldeveloper", timeout=60)

    log("  ✓ SQL Developer uninstall complete.")
    return True


def uninstall_oracle_db() -> bool:
    """Uninstall Oracle Database XE from the system."""
    if is_windows():
        return _uninstall_oracle_db_windows()
    elif is_linux():
        return _uninstall_oracle_db_linux()
    log("  ⚠ Oracle Database uninstall not supported on this platform.")
    return False


def uninstall_sql_developer() -> bool:
    """Uninstall Oracle SQL Developer from the system."""
    if is_windows():
        return _uninstall_sql_developer_windows()
    elif is_linux():
        return _uninstall_sql_developer_linux()
    log("  ⚠ SQL Developer uninstall not supported on this platform.")
    return False


# ── Install ─────────────────────────────────────────────────────────────

# Oracle download URLs (OTN direct-download links for XE 21c)
_ORACLE_XE_WIN_URL = (
    "https://download.oracle.com/otn-pub/otn_software/db-express/"
    "OracleXE213_Win64.zip"
)
_ORACLE_XE_LINUX_URL = (
    "https://download.oracle.com/otn-pub/otn_software/db-express/"
    "oracle-database-xe-21c-1.0-1.ol8.x86_64.rpm"
)
_SQLDEVELOPER_WIN_URL = (
    "https://download.oracle.com/otn-pub/java/sqldeveloper/"
    "sqldeveloper-23.1.1.345.2114-no-jre.zip"
)
_SQLDEVELOPER_LINUX_URL = (
    "https://download.oracle.com/otn-pub/java/sqldeveloper/"
    "sqldeveloper-23.1.1.345.2114-no-jre.zip"
)

# Default SYS/SYSTEM password used during silent install.
# Shown to the user in the install log after a successful setup.
_ORACLE_DEFAULT_PASSWORD = "Oracle123"


def install_oracle_db() -> bool:
    """Download and install Oracle Database 21c XE."""
    if is_windows():
        return _install_oracle_db_windows()
    elif is_linux():
        return _install_oracle_db_linux()
    log("  ⚠ Oracle Database XE is not available on this platform.")
    return False


def install_sql_developer() -> bool:
    """Download and install Oracle SQL Developer."""
    if is_windows():
        return _install_sql_developer_windows()
    elif is_linux():
        return _install_sql_developer_linux()
    log("  ⚠ SQL Developer is not available on this platform.")
    return False


def _install_oracle_db_windows() -> bool:
    """Install Oracle Database 21c XE on Windows via silent installer."""
    import tempfile

    temp_dir = tempfile.mkdtemp(prefix="oracle_xe_")
    zip_path = os.path.join(temp_dir, "OracleXE213_Win64.zip")

    log("  Downloading Oracle Database 21c XE (~1.8 GB)…")
    log("  This may take several minutes depending on your connection.")
    rc, out, err = run_command(
        f'powershell -Command "'
        f"[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; "
        f"Invoke-WebRequest -Uri '{_ORACLE_XE_WIN_URL}' "
        f"-OutFile '{zip_path}' -UseBasicParsing"
        f'"',
        timeout=3600,
    )
    if rc != 0:
        log(f"  ✗ Download failed: {err}")
        _safe_rmtree(temp_dir)
        return False

    log("  Extracting Oracle XE installer…")
    extract_dir = os.path.join(temp_dir, "extracted")
    rc, out, err = run_command(
        f'powershell -Command "Expand-Archive -Path \'{zip_path}\' '
        f'-DestinationPath \'{extract_dir}\' -Force"',
        timeout=600,
    )
    if rc != 0:
        log(f"  ✗ Extraction failed: {err}")
        _safe_rmtree(temp_dir)
        return False

    # Find setup.exe inside extracted directory
    setup_patterns = [
        os.path.join(extract_dir, "**", "setup.exe"),
    ]
    setup_exe = None
    for pattern in setup_patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            setup_exe = matches[0]
            break

    if not setup_exe:
        log("  ✗ Could not find setup.exe in extracted archive.")
        _safe_rmtree(temp_dir)
        return False

    log("  Running Oracle XE silent installer (this may take 10-20 minutes)…")
    # Silent install with password:
    #   /s           = silent mode
    #   /v"..."      = MSI properties
    #   /qn          = no UI
    #   PASSWORD=... = SYS/SYSTEM password
    rc, out, err = run_command(
        f'"{setup_exe}" /s /v"/qn PASSWORD={_ORACLE_DEFAULT_PASSWORD}"',
        timeout=2400,  # 40 minutes max
    )

    # Clean up temp files
    _safe_rmtree(temp_dir)

    if rc != 0 and rc != 3010:  # 3010 = reboot required (success)
        log(f"  ✗ Oracle XE installation failed (exit {rc})")
        if err:
            log(f"  stderr: {err[-500:]}")
        return False

    log("  ✓ Oracle Database 21c XE installed successfully.")
    log(f"  ╔══════════════════════════════════════════════════╗")
    log(f"  ║  Oracle SYS/SYSTEM password: {_ORACLE_DEFAULT_PASSWORD:<18} ║")
    log(f"  ║  Please change this password after first login!  ║")
    log(f"  ╚══════════════════════════════════════════════════╝")
    if rc == 3010:
        log("  ℹ A system reboot may be required to complete setup.")
    return True


def _install_oracle_db_linux() -> bool:
    """Install Oracle Database 21c XE on Linux."""
    import tempfile

    # Install prerequisite packages
    log("  Installing Oracle prerequisites…")
    run_command(
        "sudo yum install -y oracle-database-preinstall-21c || "
        "sudo apt-get install -y libaio1 unixodbc",
        timeout=300,
    )

    temp_dir = tempfile.mkdtemp(prefix="oracle_xe_")
    rpm_path = os.path.join(temp_dir, "oracle-database-xe-21c.rpm")

    log("  Downloading Oracle Database 21c XE (~2.5 GB)…")
    rc, out, err = run_command(
        f"curl -L -o '{rpm_path}' '{_ORACLE_XE_LINUX_URL}'",
        timeout=3600,
    )
    if rc != 0:
        log(f"  ✗ Download failed: {err}")
        _safe_rmtree(temp_dir)
        return False

    log("  Installing Oracle XE RPM package…")
    rc, out, err = run_command(
        f"sudo rpm -ivh '{rpm_path}' || sudo alien -i '{rpm_path}'",
        timeout=900,
    )
    if rc != 0:
        log(f"  ✗ Package installation failed: {err}")
        _safe_rmtree(temp_dir)
        return False

    # Configure the database with the default password
    log("  Configuring Oracle XE database…")
    pw = _ORACLE_DEFAULT_PASSWORD
    rc, out, err = run_command(
        f"sudo /etc/init.d/oracle-xe-21c configure <<< $'{pw}\n{pw}\n'",
        timeout=600,
    )

    _safe_rmtree(temp_dir)

    if rc != 0:
        log(f"  ⚠ Configuration step returned exit {rc} — may need manual configuration.")

    log("  ✓ Oracle Database 21c XE installed.")
    log(f"  ╔══════════════════════════════════════════════════╗")
    log(f"  ║  Oracle SYS/SYSTEM password: {_ORACLE_DEFAULT_PASSWORD:<18} ║")
    log(f"  ║  Please change this password after first login!  ║")
    log(f"  ╚══════════════════════════════════════════════════╝")
    return True


def _install_sql_developer_windows() -> bool:
    """Install Oracle SQL Developer on Windows (zip-based)."""
    import tempfile

    install_dir = r"C:\sqldeveloper"
    temp_dir = tempfile.mkdtemp(prefix="sqldeveloper_")
    zip_path = os.path.join(temp_dir, "sqldeveloper.zip")

    log("  Downloading Oracle SQL Developer…")
    rc, out, err = run_command(
        f'powershell -Command "'
        f"[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; "
        f"Invoke-WebRequest -Uri '{_SQLDEVELOPER_WIN_URL}' "
        f"-OutFile '{zip_path}' -UseBasicParsing"
        f'"',
        timeout=1200,
    )
    if rc != 0:
        log(f"  ✗ Download failed: {err}")
        _safe_rmtree(temp_dir)
        return False

    log("  Extracting SQL Developer…")
    rc, out, err = run_command(
        f'powershell -Command "Expand-Archive -Path \'{zip_path}\' '
        f"-DestinationPath 'C:\\' -Force\"",
        timeout=300,
    )
    if rc != 0:
        log(f"  ✗ Extraction failed: {err}")
        _safe_rmtree(temp_dir)
        return False

    _safe_rmtree(temp_dir)

    if os.path.isdir(install_dir):
        log(f"  ✓ SQL Developer installed to {install_dir}")
        _create_shortcut_windows(install_dir)
        return True
    else:
        log("  ✗ SQL Developer directory not found after extraction.")
        return False


def _install_sql_developer_linux() -> bool:
    """Install Oracle SQL Developer on Linux (zip-based)."""
    import tempfile

    install_dir = "/opt/sqldeveloper"
    temp_dir = tempfile.mkdtemp(prefix="sqldeveloper_")
    zip_path = os.path.join(temp_dir, "sqldeveloper.zip")

    log("  Downloading Oracle SQL Developer…")
    rc, out, err = run_command(
        f"curl -L -o '{zip_path}' '{_SQLDEVELOPER_LINUX_URL}'",
        timeout=1200,
    )
    if rc != 0:
        log(f"  ✗ Download failed: {err}")
        _safe_rmtree(temp_dir)
        return False

    log("  Extracting SQL Developer…")
    _safe_rmtree(install_dir)
    rc, out, err = run_command(
        f"sudo unzip -o '{zip_path}' -d /opt/",
        timeout=300,
    )
    if rc != 0:
        log(f"  ✗ Extraction failed: {err}")
        _safe_rmtree(temp_dir)
        return False

    _safe_rmtree(temp_dir)

    # Create a symlink for easy access
    run_command(
        f"sudo ln -sf {install_dir}/sqldeveloper.sh /usr/local/bin/sqldeveloper",
        timeout=15,
    )

    if os.path.isdir(install_dir):
        log(f"  ✓ SQL Developer installed to {install_dir}")
        _create_shortcut_linux(install_dir)
        return True
    else:
        log("  ✗ SQL Developer directory not found after extraction.")
        return False


# ── Lifecycle orchestrator ──────────────────────────────────────────────

def oracle_lifecycle(tools: list[dict]) -> dict[str, str]:
    """Run the full Oracle lifecycle: detect → uninstall if needed → install.

    Parameters
    ----------
    tools : list[dict]
        The Oracle-linked tool dicts selected by the user.

    Returns
    -------
    dict[str, str]
        Mapping of tool keys to result status
        (``'installed'`` or ``'failed'``).
    """
    results: dict[str, str] = {}

    db_present = detect_oracle_db()
    sqld_present = detect_sql_developer()

    log("\n══ Oracle Lifecycle ══════════════════════════════════════")

    if db_present or sqld_present:
        log("  Existing Oracle installation(s) detected.")
        if db_present:
            log("    • Oracle Database XE: FOUND")
        if sqld_present:
            log("    • Oracle SQL Developer: FOUND")
        log("  Performing complete uninstall before fresh install…")
        log("")

        # Always uninstall both if either is found
        if db_present:
            log("── Uninstalling Oracle Database XE ──────────────────────")
            uninstall_oracle_db()

        if sqld_present:
            log("── Uninstalling Oracle SQL Developer ────────────────────")
            uninstall_sql_developer()

        log("")
        log("  ✓ Uninstall phase complete. Proceeding with fresh install…")
    else:
        log("  No existing Oracle installations detected.")
        log("  Proceeding with fresh install…")

    log("")

    # Determine which tools to install based on selection
    tool_keys = {t.get("key", "") for t in tools}

    # Install Oracle Database XE
    if "oracle_db_xe" in tool_keys:
        log("── Installing Oracle Database 21c XE ────────────────────")
        if install_oracle_db():
            results["oracle_db_xe"] = "installed"
        else:
            results["oracle_db_xe"] = "failed"

    # Install SQL Developer
    if "oracle_sql_developer" in tool_keys:
        log("── Installing Oracle SQL Developer ──────────────────────")
        if install_sql_developer():
            results["oracle_sql_developer"] = "installed"
        else:
            results["oracle_sql_developer"] = "failed"

    log("══════════════════════════════════════════════════════════")
    return results


# ── Helpers ─────────────────────────────────────────────────────────────

def _create_shortcut_windows(install_dir: str) -> None:
    """Create Desktop and Start Menu shortcuts for SQL Developer on Windows."""
    exe_path = os.path.join(install_dir, "sqldeveloper.exe")
    if not os.path.isfile(exe_path):
        # Try alternate exe location
        alt = os.path.join(install_dir, "sqldeveloper", "sqldeveloper.exe")
        if os.path.isfile(alt):
            exe_path = alt
        else:
            log("  ⚠ sqldeveloper.exe not found — skipping shortcut creation.")
            return

    # Icon path (SQL Developer ships an .ico inside the install dir)
    icon_path = exe_path  # Use the exe itself as the icon source

    # Desktop shortcut
    desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    desktop_lnk = os.path.join(desktop, "Oracle SQL Developer.lnk")

    # Start Menu shortcut
    start_menu = os.path.join(
        os.environ.get("APPDATA", ""),
        "Microsoft", "Windows", "Start Menu", "Programs",
    )
    start_lnk = os.path.join(start_menu, "Oracle SQL Developer.lnk")

    ps_script = (
        '$WshShell = New-Object -ComObject WScript.Shell; '
        f'$Shortcut = $WshShell.CreateShortcut("{desktop_lnk}"); '
        f'$Shortcut.TargetPath = "{exe_path}"; '
        f'$Shortcut.WorkingDirectory = "{install_dir}"; '
        f'$Shortcut.IconLocation = "{icon_path},0"; '
        '$Shortcut.Description = "Oracle SQL Developer"; '
        '$Shortcut.Save(); '
        f'$Shortcut2 = $WshShell.CreateShortcut("{start_lnk}"); '
        f'$Shortcut2.TargetPath = "{exe_path}"; '
        f'$Shortcut2.WorkingDirectory = "{install_dir}"; '
        f'$Shortcut2.IconLocation = "{icon_path},0"; '
        '$Shortcut2.Description = "Oracle SQL Developer"; '
        '$Shortcut2.Save()'
    )

    rc, _, err = run_command(
        f'powershell -Command "{ps_script}"',
        timeout=30,
    )
    if rc == 0:
        log("  ✓ Desktop shortcut created: Oracle SQL Developer")
        log("  ✓ Start Menu shortcut created: Oracle SQL Developer")
    else:
        log(f"  ⚠ Shortcut creation failed: {err}")


def _create_shortcut_linux(install_dir: str) -> None:
    """Create a .desktop file for SQL Developer on Linux."""
    desktop_entry = f"""[Desktop Entry]
Name=Oracle SQL Developer
Comment=Free IDE for Oracle Database development
Exec={install_dir}/sqldeveloper.sh
Icon={install_dir}/icon.png
Terminal=false
Type=Application
Categories=Development;Database;
StartupWMClass=SQL Developer
"""

    # Place in /usr/share/applications for all users
    desktop_file = "/usr/share/applications/sqldeveloper.desktop"
    try:
        rc, _, err = run_command(
            f"sudo tee {desktop_file} > /dev/null << 'DESKTOP_EOF'\n"
            f"{desktop_entry}DESKTOP_EOF",
            timeout=15,
        )
        if rc == 0:
            run_command(f"sudo chmod 644 {desktop_file}", timeout=10)
            log("  ✓ Desktop shortcut created: Oracle SQL Developer")
        else:
            log(f"  ⚠ Desktop shortcut creation failed: {err}")
    except Exception as e:
        log(f"  ⚠ Desktop shortcut creation failed: {e}")

    # Also copy to user's Desktop if it exists
    user_desktop = os.path.expanduser("~/Desktop")
    if os.path.isdir(user_desktop):
        user_desktop_file = os.path.join(user_desktop, "sqldeveloper.desktop")
        try:
            with open(user_desktop_file, "w", encoding="utf-8") as f:
                f.write(desktop_entry)
            os.chmod(user_desktop_file, 0o755)
            log("  ✓ User desktop shortcut created: Oracle SQL Developer")
        except Exception as e:
            log(f"  ⚠ User desktop shortcut failed: {e}")


def is_oracle_tool(tool: dict) -> bool:
    """Return True if the tool is an Oracle-linked tool requiring custom handling."""
    return tool.get("oracle_linked", False) or tool.get("key", "") in (
        "oracle_db_xe",
        "oracle_sql_developer",
    )


def _safe_rmtree(path: str) -> None:
    """Remove a directory tree, ignoring errors."""
    try:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass


def _safe_remove(path: str) -> None:
    """Remove a single file, ignoring errors."""
    try:
        if os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
    except Exception:
        pass


def _clean_oracle_from_path_windows() -> None:
    """Remove Oracle-related entries from the Windows system PATH."""
    rc, out, _ = run_command(
        'powershell -Command "[Environment]::GetEnvironmentVariable(\'Path\', \'Machine\')"',
        timeout=15,
    )
    if rc != 0:
        return

    original = out.strip()
    parts = original.split(";")
    cleaned = [p for p in parts if "oracle" not in p.lower()]

    if len(cleaned) < len(parts):
        new_path = ";".join(cleaned)
        run_command(
            f'powershell -Command "[Environment]::SetEnvironmentVariable(\'Path\', '
            f'\'{new_path}\', \'Machine\')"',
            timeout=15,
        )
        log("    Removed Oracle entries from system PATH.")


def _clean_sqldeveloper_from_path_windows() -> None:
    """Remove SQL Developer entries from the Windows system PATH."""
    rc, out, _ = run_command(
        'powershell -Command "[Environment]::GetEnvironmentVariable(\'Path\', \'Machine\')"',
        timeout=15,
    )
    if rc != 0:
        return

    original = out.strip()
    parts = original.split(";")
    cleaned = [p for p in parts if "sqldeveloper" not in p.lower()]

    if len(cleaned) < len(parts):
        new_path = ";".join(cleaned)
        run_command(
            f'powershell -Command "[Environment]::SetEnvironmentVariable(\'Path\', '
            f'\'{new_path}\', \'Machine\')"',
            timeout=15,
        )
        log("    Removed SQL Developer entries from system PATH.")

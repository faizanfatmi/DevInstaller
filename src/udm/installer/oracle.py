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

from udm.installer.callbacks import log, notify
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
        # Check registry (HKCU first, then HKLM)
        rc, _, _ = run_command(
            'reg query "HKCU\\SOFTWARE\\Oracle\\sqldeveloper" /ve',
            timeout=15,
        )
        if rc == 0:
            return True

        rc, _, _ = run_command(
            'reg query "HKLM\\SOFTWARE\\Oracle\\sqldeveloper" /ve',
            timeout=15,
        )
        if rc == 0:
            return True

        # Check common install locations (including user-space paths)
        sqldeveloper_paths = [
            r"C:\sqldeveloper",
            r"C:\app\sqldeveloper",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "sqldeveloper"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "sqldeveloper"),
            os.path.join(os.environ.get("USERPROFILE", ""), "sqldeveloper"),
            os.path.join(os.environ.get("PROGRAMFILES", ""), "sqldeveloper"),
        ]
        for p in sqldeveloper_paths:
            if p and os.path.isdir(p):
                if os.path.isfile(os.path.join(p, "sqldeveloper.exe")) or \
                   os.path.isfile(os.path.join(p, "sqldeveloper", "sqldeveloper.exe")):
                    return True

        # Check if sqldeveloper.exe exists via where
        rc2, _, _ = run_command("where sqldeveloper", timeout=15)
        if rc2 == 0:
            return True

    elif is_linux():
        linux_paths = [
            "/opt/sqldeveloper",
            "/usr/local/sqldeveloper",
            os.path.expanduser("~/.local/share/sqldeveloper"),
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
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "sqldeveloper"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "sqldeveloper"),
        os.path.join(os.environ.get("USERPROFILE", ""), "sqldeveloper"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), "sqldeveloper"),
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

    # Remove user shortcuts
    desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    _safe_remove(os.path.join(desktop, "Oracle SQL Developer.lnk"))
    start_menu = os.path.join(
        os.environ.get("APPDATA", ""),
        "Microsoft", "Windows", "Start Menu", "Programs",
    )
    _safe_remove(os.path.join(start_menu, "Oracle SQL Developer.lnk"))

    # Clean registry (HKCU first, then HKLM without failing if non-admin)
    run_command(r'reg delete "HKCU\SOFTWARE\Oracle\sqldeveloper" /f', timeout=15)
    run_command(r'reg delete "HKLM\SOFTWARE\Oracle\sqldeveloper" /f', timeout=15)

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
    "https://download.oracle.com/otn_software/java/sqldeveloper/"
    "sqldeveloper-26.2.0.186.2220-x64.zip"
)
_SQLDEVELOPER_LINUX_URL = (
    "https://download.oracle.com/otn_software/java/sqldeveloper/"
    "sqldeveloper-26.2.0.186.2220-no-jre.zip"
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


def install_sql_developer(archive_path: str | None = None) -> bool:
    """Install Oracle SQL Developer from an archive or path."""
    if is_windows():
        return _install_sql_developer_windows(archive_path=archive_path)
    elif is_linux():
        return _install_sql_developer_linux(archive_path=archive_path)
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


def _get_sqldeveloper_install_dir_windows() -> str:
    """Return user-writable install path for SQL Developer on Windows."""
    try:
        test_file = r"C:\.test_devinstaller_write"
        with open(test_file, "w") as f:
            f.write("1")
        os.remove(test_file)
        return r"C:\sqldeveloper"
    except Exception:
        pass

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return os.path.join(local_app_data, "sqldeveloper")
    user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    return os.path.join(user_profile, "sqldeveloper")


def _find_sqldeveloper_exe(base_dir: str) -> str | None:
    """Find sqldeveloper.exe in base_dir or its subfolders."""
    direct = os.path.join(base_dir, "sqldeveloper.exe")
    if os.path.isfile(direct):
        return direct
    nested = os.path.join(base_dir, "sqldeveloper", "sqldeveloper.exe")
    if os.path.isfile(nested):
        return nested
    for match in glob.glob(os.path.join(base_dir, "*", "sqldeveloper.exe")):
        if os.path.isfile(match):
            return match
    return None


def _download_sql_developer(url: str, dest_zip: str) -> bool:
    """Download SQL Developer archive with parallel multi-threading and progress logging."""
    from udm.downloader import download_file_parallel
    log("  Downloading Oracle SQL Developer (~500 MB) via parallel chunk downloader…")
    log(f"  Source: {url}")
    log("  Using 4-thread parallel byte-range streams for maximum download speed.")
    
    last_log_pct = [-10]

    def _progress_cb(pct: int, downloaded: int, total: int):
        mb_down = downloaded // (1024 * 1024)
        mb_total = total // (1024 * 1024) if total > 0 else 0
        if pct >= last_log_pct[0] + 10:
            log(f"    Parallel download: {pct}% ({mb_down} MB / {mb_total} MB)…")
            last_log_pct[0] = pct
        notify("Oracle SQL Developer", f"Downloading {pct}% ({mb_down}/{mb_total} MB)", pct)

    try:
        success = download_file_parallel(
            url=url,
            dest_path=dest_zip,
            progress_callback=_progress_cb,
            num_threads=4,
        )
        if not success:
            log("  ✗ Parallel download failed.")
            return False

        if os.path.isfile(dest_zip) and os.path.getsize(dest_zip) > 10 * 1024 * 1024:
            with open(dest_zip, "rb") as f:
                header = f.read(4)
                if header == b"PK\x03\x04":
                    log("  ✓ Download complete and archive verified.")
                    return True
        log("  ✗ Downloaded file is invalid or incomplete.")
        return False
    except Exception as exc:
        log(f"  ✗ Download failed: {exc}")
        return False


def _find_or_download_sqldeveloper_archive(
    archive_path: str | None = None, is_win: bool = True
) -> tuple[str | None, str | None]:
    """Return (source_path, temp_dir_to_clean)."""
    # 1. Custom provided path
    if archive_path and archive_path.strip():
        p = os.path.expanduser(os.path.expandvars(archive_path.strip().strip('"').strip("'")))
        if os.path.exists(p):
            return (p, None)
        log(f"  ✗ Provided path does not exist: {p}")
        return (None, None)

    # 2. Environment variable
    env_path = os.environ.get("SQLDEVELOPER_ARCHIVE", "").strip().strip('"').strip("'")
    if env_path:
        p = os.path.expanduser(os.path.expandvars(env_path))
        if os.path.exists(p):
            return (p, None)

    # 3. Check Downloads folder for already downloaded zip
    from udm.gui.oracle_dialog import _detect_default_sqldeveloper_path
    detected = _detect_default_sqldeveloper_path()
    if detected:
        log(f"  Using local SQL Developer archive found in Downloads: {detected}")
        return (detected, None)

    # 4. Automatic direct download from Oracle's direct link
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix="sqldeveloper_dl_")
    dest_zip = os.path.join(temp_dir, "sqldeveloper.zip")
    url = _SQLDEVELOPER_WIN_URL if is_win else _SQLDEVELOPER_LINUX_URL
    if _download_sql_developer(url, dest_zip):
        return (dest_zip, temp_dir)

    _safe_rmtree(temp_dir)
    return (None, None)


def _install_sql_developer_windows(archive_path: str | None = None) -> bool:
    """Install Oracle SQL Developer on Windows (zip or directory based)."""
    import zipfile

    source_path, temp_dir = _find_or_download_sqldeveloper_archive(archive_path, is_win=True)
    if not source_path:
        return False

    install_dir = _get_sqldeveloper_install_dir_windows()
    log(f"  Target installation directory: {install_dir}")

    try:
        if os.path.isdir(source_path):
            log(f"  Installing from extracted directory: {source_path}")
            exe = _find_sqldeveloper_exe(source_path)
            if not exe:
                log("  ✗ Could not find sqldeveloper.exe inside specified folder.")
                return False
            if os.path.normpath(source_path).lower() != os.path.normpath(install_dir).lower():
                log(f"  Copying files to {install_dir}…")
                _safe_rmtree(install_dir)
                shutil.copytree(source_path, install_dir)
                actual_dir = install_dir
            else:
                actual_dir = source_path
        elif zipfile.is_zipfile(source_path):
            log(f"  Extracting SQL Developer from: {source_path}…")
            _safe_rmtree(install_dir)
            os.makedirs(install_dir, exist_ok=True)
            with zipfile.ZipFile(source_path, "r") as zf:
                zf.extractall(install_dir)
            actual_dir = install_dir
        else:
            log(f"  ✗ Specified file is not a valid zip archive: {source_path}")
            return False

        exe_path = _find_sqldeveloper_exe(actual_dir)
        if not exe_path:
            log("  ✗ Extraction completed but sqldeveloper.exe was not found.")
            return False

        actual_install_dir = os.path.dirname(exe_path)
        log(f"  ✓ Oracle SQL Developer ready at: {actual_install_dir}")

        _create_shortcut_windows(actual_install_dir)

        try:
            from udm.platform.path import add_to_path
            add_to_path(actual_install_dir)
        except Exception as exc:
            log(f"  ⚠ Could not add to PATH: {exc}")

        return True
    finally:
        if temp_dir:
            _safe_rmtree(temp_dir)


def _install_sql_developer_linux(archive_path: str | None = None) -> bool:
    """Install Oracle SQL Developer on Linux (zip or directory based)."""
    import zipfile

    source_path, temp_dir = _find_or_download_sqldeveloper_archive(archive_path, is_win=False)
    if not source_path:
        return False

    is_root = os.geteuid() == 0 if hasattr(os, "geteuid") else False
    install_dir = "/opt/sqldeveloper" if is_root else os.path.expanduser("~/.local/share/sqldeveloper")
    log(f"  Target installation directory: {install_dir}")

    try:
        if os.path.isdir(source_path):
            log(f"  Installing from extracted directory: {source_path}")
            if os.path.normpath(source_path) != os.path.normpath(install_dir):
                _safe_rmtree(install_dir)
                shutil.copytree(source_path, install_dir)
            actual_dir = install_dir
        elif zipfile.is_zipfile(source_path):
            log(f"  Extracting SQL Developer from: {source_path}…")
            _safe_rmtree(install_dir)
            os.makedirs(install_dir, exist_ok=True)
            with zipfile.ZipFile(source_path, "r") as zf:
                zf.extractall(install_dir)
            actual_dir = install_dir
        else:
            log(f"  ✗ Specified file is not a valid zip archive: {source_path}")
            return False

        _create_shortcut_linux(actual_dir)

        try:
            from udm.platform.path import add_to_path
            add_to_path(actual_dir)
        except Exception:
            pass

        log(f"  ✓ SQL Developer installed to {actual_dir}")
        return True
    finally:
        if temp_dir:
            _safe_rmtree(temp_dir)


# ── Lifecycle orchestrator ──────────────────────────────────────────────

def oracle_lifecycle(tools: list[dict]) -> dict[str, str]:
    """Run the Oracle lifecycle: detect → uninstall if needed → install.

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
    tool_keys = {t.get("key", "") for t in tools}

    db_present = detect_oracle_db() if "oracle_db_xe" in tool_keys else False
    sqld_present = detect_sql_developer() if "oracle_sql_developer" in tool_keys else False

    log("\n══ Oracle Lifecycle ══════════════════════════════════════")

    if db_present or sqld_present:
        log("  Existing installation(s) detected for selected tools:")
        if db_present:
            log("    • Oracle Database XE: FOUND -> Performing clean uninstall…")
            uninstall_oracle_db()
        if sqld_present:
            log("    • Oracle SQL Developer: FOUND -> Performing clean uninstall…")
            uninstall_sql_developer()
        log("  ✓ Uninstall phase complete. Proceeding with fresh install…\n")
    else:
        log("  No existing installations detected for selected tools.")
        log("  Proceeding with fresh install…\n")

    # Install Oracle Database XE
    if "oracle_db_xe" in tool_keys:
        log("── Installing Oracle Database 21c XE ────────────────────")
        if install_oracle_db():
            results["oracle_db_xe"] = "installed"
        else:
            results["oracle_db_xe"] = "failed"

    # Install SQL Developer
    if "oracle_sql_developer" in tool_keys:
        sqld_tool = next((t for t in tools if t.get("key") == "oracle_sql_developer"), {})
        archive_path = sqld_tool.get("archive_path")
        log("── Installing Oracle SQL Developer ──────────────────────")
        if install_sql_developer(archive_path=archive_path):
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
    """Remove SQL Developer entries from the Windows user and system PATH."""
    try:
        from udm.platform.path import _windows_get_user_path, _windows_set_user_path
        user_path = _windows_get_user_path()
        parts = [p.strip() for p in user_path.split(";") if p.strip()]
        cleaned = [p for p in parts if "sqldeveloper" not in p.lower()]
        if len(cleaned) < len(parts):
            _windows_set_user_path(";".join(cleaned))
            log("    Removed SQL Developer entries from user PATH.")
    except Exception:
        pass

    try:
        rc, out, _ = run_command(
            'powershell -Command "[Environment]::GetEnvironmentVariable(\'Path\', \'Machine\')"',
            timeout=15,
        )
        if rc == 0:
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
    except Exception:
        pass

"""Shell command execution utilities."""

import os
import subprocess

from udm.logger import logger
from udm.platform.detect import is_linux, is_windows


def run_command(
    cmd: str,
    shell: bool = True,
    timeout: int = 900,
) -> tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    kwargs: dict = dict(
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=shell,
        timeout=timeout,
    )
    if is_windows():
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    try:
        proc = subprocess.run(cmd, **kwargs)
        return (
            proc.returncode,
            proc.stdout.decode(errors="replace"),
            proc.stderr.decode(errors="replace"),
        )
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {cmd}")
        return -1, "", "Command timed out"
    except Exception as e:
        logger.error(f"Command failed: {cmd} — {e}")
        return -1, "", str(e)


def run_privileged_command(
    cmd: str,
    shell: bool = True,
    timeout: int = 900,
) -> tuple[int, str, str]:
    """Run *cmd* with elevated privileges on Linux using pkexec.

    Behaviour:
    - If already running as root, the command runs unchanged.
    - On Linux with pkexec available, the command is wrapped so the native
      polkit password dialog is shown. Because pkexec does not accept a shell
      string directly, the command is executed via ``sh -c``.
    - If pkexec is unavailable, falls back to running the command as-is (which
      may itself prompt via sudo, or fail with a permissions error that the
      caller surfaces to the user).

    Returns the same (returncode, stdout, stderr) tuple as run_command.
    """
    if not is_linux():
        return run_command(cmd, shell=shell, timeout=timeout)

    already_root = False
    try:
        already_root = os.geteuid() == 0
    except AttributeError:
        already_root = False

    if already_root:
        return run_command(cmd, shell=shell, timeout=timeout)

    if command_exists("pkexec"):
        # pkexec runs a single program; use a login-ish shell to interpret the
        # full command string (pipes, &&, etc.).
        try:
            proc = subprocess.run(
                ["pkexec", "sh", "-c", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
            return (
                proc.returncode,
                proc.stdout.decode(errors="replace"),
                proc.stderr.decode(errors="replace"),
            )
        except subprocess.TimeoutExpired:
            logger.error(f"Privileged command timed out: {cmd}")
            return -1, "", "Command timed out"
        except Exception as e:
            logger.error(f"Privileged command failed: {cmd} — {e}")
            return -1, "", str(e)

    logger.warning("pkexec not found; running command without GUI elevation.")
    return run_command(cmd, shell=shell, timeout=timeout)


def command_exists(cmd: str) -> bool:
    """Check whether *cmd* is available on PATH."""
    try:
        if is_windows():
            result = subprocess.run(
                ["where", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            result = subprocess.run(
                ["which", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        return result.returncode == 0
    except Exception:
        return False

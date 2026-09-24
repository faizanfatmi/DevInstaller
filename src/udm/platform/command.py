"""Shell command execution utilities."""

import os
import subprocess
import threading
from typing import Callable, Optional

from udm.logger import logger
from udm.platform.detect import is_linux, is_windows


def run_command(
    cmd: str | list[str],
    shell: bool = True,
    timeout: int = 900,
) -> tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    if isinstance(cmd, list):
        shell = False

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


def run_command_streamed(
    cmd: str | list[str],
    on_output: Optional[Callable[[str], None]] = None,
    shell: bool = True,
    timeout: int = 900,
) -> tuple[int, str, str]:
    """Run a command, streaming its output live to *on_output* segment by segment.

    Package managers (winget, choco, pip) redraw progress in place using carriage
    returns rather than newlines, so the reader splits on both ``\\n`` and ``\\r``.
    stderr is merged into stdout so a single stream carries everything.

    Returns ``(returncode, full_output, "")`` — the third element is always empty
    since stderr is folded into stdout, matching the ``run_command`` tuple shape.
    A timeout kills the process and returns ``(-1, partial_output, "timed out")``.
    """
    if isinstance(cmd, list):
        shell = False

    popen_kwargs: dict = dict(
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=shell,
        bufsize=0,
    )
    if is_windows():
        popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    try:
        proc = subprocess.Popen(cmd, **popen_kwargs)
    except Exception as e:
        logger.error(f"Command failed to start: {cmd} — {e}")
        return -1, "", str(e)

    collected: list[str] = []
    timed_out = threading.Event()

    # subprocess.Popen has no built-in timeout for streaming reads; a timer
    # thread kills the process if it overruns.
    timer = threading.Timer(timeout, _kill, args=(proc, timed_out))
    timer.daemon = True
    timer.start()

    buffer = ""
    try:
        stream = proc.stdout
        while True:
            chunk = stream.read(1024) if stream else b""
            if not chunk:
                break
            text = chunk.decode(errors="replace")
            buffer += text
            # Split on both newline and carriage return so in-place progress
            # redraws are surfaced as they happen.
            parts = buffer.replace("\r", "\n").split("\n")
            buffer = parts.pop()  # keep the trailing partial segment
            for segment in parts:
                collected.append(segment)
                if on_output and segment.strip():
                    try:
                        on_output(segment)
                    except Exception:
                        pass
        if buffer:
            collected.append(buffer)
            if on_output and buffer.strip():
                try:
                    on_output(buffer)
                except Exception:
                    pass
        proc.wait()
    finally:
        timer.cancel()

    output = "\n".join(collected)
    if timed_out.is_set():
        logger.error(f"Command timed out: {cmd}")
        return -1, output, "Command timed out"
    return proc.returncode if proc.returncode is not None else -1, output, ""


def _kill(proc: "subprocess.Popen", flag: threading.Event) -> None:
    """Mark a process as timed-out and terminate it (used by the watchdog timer)."""
    if proc.poll() is None:
        flag.set()
        try:
            proc.kill()
        except Exception:
            pass


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

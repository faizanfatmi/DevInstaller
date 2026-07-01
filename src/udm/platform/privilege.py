"""Privilege elevation on Linux via pkexec.

``pkexec`` presents the native polkit authentication dialog (the desktop's
administrator-password prompt), which is the right UX for a GUI app — unlike
``sudo`` it does not need a controlling terminal.

All helpers here degrade gracefully: a missing pkexec, a cancelled prompt, or a
failed authentication are reported as structured outcomes rather than raising,
so the installer can show clear, user-friendly messages.
"""

from __future__ import annotations

from udm.logger import logger
from udm.platform.command import command_exists
from udm.platform.detect import is_linux

# pkexec exit codes with special meaning (see pkexec(1)):
#   126 → authorization could not be obtained (dismissed / not authorized)
#   127 → the target program could not be executed / not found
PKEXEC_NOT_AUTHORIZED = 126
PKEXEC_EXEC_FAILED = 127


def pkexec_available() -> bool:
    """Return True if pkexec is present on the current Linux system."""
    return is_linux() and command_exists("pkexec")


def classify_pkexec_result(rc: int) -> str:
    """Map a pkexec return code to an outcome.

    Returns one of: 'ok', 'auth_failed', 'exec_failed', 'error'.
    """
    if rc == 0:
        return "ok"
    if rc == PKEXEC_NOT_AUTHORIZED:
        return "auth_failed"
    if rc == PKEXEC_EXEC_FAILED:
        return "exec_failed"
    return "error"


def friendly_pkexec_message(rc: int) -> str:
    """Return a clear, user-facing message for a pkexec return code."""
    outcome = classify_pkexec_result(rc)
    return {
        "ok": "Authorized.",
        "auth_failed": (
            "Administrator authentication was cancelled or denied. "
            "The action needs elevated privileges to continue."
        ),
        "exec_failed": (
            "The privileged command could not be started. "
            "Please ensure the package manager is installed."
        ),
        "error": f"The privileged command failed (exit code {rc}).",
    }[outcome]

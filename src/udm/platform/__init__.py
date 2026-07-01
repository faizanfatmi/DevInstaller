"""Platform-specific utilities."""

from udm.platform.admin import is_admin, request_admin
from udm.platform.command import (
    command_exists,
    run_command,
    run_privileged_command,
)
from udm.platform.detect import (
    detect_linux_distro,
    detect_os,
    is_linux,
    is_mac,
    is_supported_linux,
    is_windows,
    linux_distro_family,
    linux_distro_name,
    os_label,
)
from udm.platform.path import add_to_path, resolve_env_path
from udm.platform.privilege import (
    classify_pkexec_result,
    friendly_pkexec_message,
    pkexec_available,
)

__all__ = [
    "detect_os",
    "is_windows",
    "is_linux",
    "is_mac",
    "os_label",
    "detect_linux_distro",
    "linux_distro_family",
    "linux_distro_name",
    "is_supported_linux",
    "is_admin",
    "request_admin",
    "add_to_path",
    "resolve_env_path",
    "run_command",
    "run_privileged_command",
    "command_exists",
    "pkexec_available",
    "classify_pkexec_result",
    "friendly_pkexec_message",
]

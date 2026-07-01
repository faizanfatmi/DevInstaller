"""OS and Linux-distribution detection utilities."""

import platform
from functools import lru_cache
from pathlib import Path


def detect_os() -> str:
    """Return 'Windows', 'Linux', or 'Darwin' (macOS)."""
    return platform.system()


def is_windows() -> bool:
    return detect_os() == "Windows"


def is_linux() -> bool:
    return detect_os() == "Linux"


def is_mac() -> bool:
    return detect_os() == "Darwin"


def os_label() -> str:
    """Return a human-friendly OS name."""
    mapping = {"Windows": "Windows", "Linux": "Linux", "Darwin": "macOS"}
    return mapping.get(detect_os(), detect_os())


# ── Linux distribution detection ────────────────────────────────────

_OS_RELEASE_PATH = "/etc/os-release"

# Map distro IDs / ID_LIKE tokens to a normalised package-manager family.
_FAMILY_BY_ID = {
    "arch": "arch",
    "archarm": "arch",
    "manjaro": "arch",
    "endeavouros": "arch",
    "garuda": "arch",
    "fedora": "fedora",
    "rhel": "fedora",
    "centos": "fedora",
    "rocky": "fedora",
    "almalinux": "fedora",
    "debian": "debian",
    "ubuntu": "debian",
    "linuxmint": "debian",
    "pop": "debian",
    "raspbian": "debian",
    "opensuse": "suse",
    "opensuse-leap": "suse",
    "opensuse-tumbleweed": "suse",
    "sles": "suse",
}


def _parse_os_release() -> dict[str, str]:
    """Parse /etc/os-release into a dict. Returns {} if unreadable."""
    data: dict[str, str] = {}
    path = Path(_OS_RELEASE_PATH)
    if not path.exists():
        return data
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            data[key.strip()] = value.strip().strip('"').strip("'")
    except OSError:
        return {}
    return data


@lru_cache(maxsize=1)
def detect_linux_distro() -> dict[str, str]:
    """Return distro info: {'id', 'id_like', 'name', 'family'}.

    ``family`` is normalised to one of: 'arch', 'fedora', 'debian', 'suse',
    'unknown'. Non-Linux systems return family 'unknown'.
    """
    if not is_linux():
        return {"id": "", "id_like": "", "name": os_label(), "family": "unknown"}

    info = _parse_os_release()
    distro_id = info.get("ID", "").lower()
    id_like = info.get("ID_LIKE", "").lower()
    pretty = info.get("PRETTY_NAME") or info.get("NAME") or "Linux"

    family = _FAMILY_BY_ID.get(distro_id, "")
    if not family:
        # Fall back to ID_LIKE tokens (e.g. 'ubuntu debian').
        for token in id_like.split():
            if token in _FAMILY_BY_ID:
                family = _FAMILY_BY_ID[token]
                break
    if not family:
        family = "unknown"

    return {"id": distro_id, "id_like": id_like, "name": pretty, "family": family}


def linux_distro_family() -> str:
    """Return just the normalised distro family (see detect_linux_distro)."""
    return detect_linux_distro()["family"]


def linux_distro_name() -> str:
    """Return the human-friendly distro name (e.g. 'Fedora Linux 40')."""
    return detect_linux_distro()["name"]


def is_supported_linux() -> bool:
    """Return True if the current Linux distro family is supported."""
    return linux_distro_family() in {"arch", "fedora", "debian"}

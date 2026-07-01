"""Translate Debian/apt install commands into pacman (Arch) or dnf (Fedora).

DevInstaller's ``tools.json`` expresses Linux installs with apt commands. To
support Arch and Fedora without duplicating ~130 entries, we derive the native
command at runtime: parse the package list out of an
``apt-get install -y <pkgs>`` command and re-emit it for the target package
manager, translating package names that differ across distributions.

Only apt commands are transformed. Commands that are already cross-distro
(``npm install -g``, ``pip install``, ``curl ... | sh``, ``brew ...``, ``snap``)
are returned unchanged. Unknown package names are passed through verbatim so
the package manager can resolve them or fail with a clear message, rather than
us guessing wrongly.
"""

from __future__ import annotations

import re

# Debian package name -> (arch package(s), fedora package(s)).
# A value of None means "no direct equivalent"; the original name is kept.
# Multiple packages are space-separated.
_PKG_MAP: dict[str, tuple[str | None, str | None]] = {
    # Python
    "python3": ("python", "python3"),
    "python3-pip": ("python-pip", "python3-pip"),
    "python3-venv": ("python", "python3"),
    "python3.11": ("python", "python3.11"),
    "python3.11-venv": ("python", "python3.11"),
    # C / C++ / build
    "g++": ("gcc", "gcc-c++"),
    "build-essential": ("base-devel", "@development-tools"),
    "gfortran": ("gcc-fortran", "gcc-gfortran"),
    "ninja-build": ("ninja", "ninja-build"),
    # Java
    "openjdk-21-jdk": ("jdk-openjdk", "java-21-openjdk-devel"),
    "openjdk-17-jdk": ("jdk17-openjdk", "java-17-openjdk-devel"),
    # .NET
    "dotnet-sdk-8.0": ("dotnet-sdk", "dotnet-sdk-8.0"),
    # PHP
    "php-cli": ("php", "php-cli"),
    "php-mbstring": ("php", "php-mbstring"),
    # Ruby
    "ruby-full": ("ruby", "ruby"),
    # Node
    "nodejs": ("nodejs", "nodejs"),
    # Go
    "golang-go": ("go", "golang"),
    # Databases / services commonly named differently
    "postgresql": ("postgresql", "postgresql-server"),
    "default-mysql-server": ("mariadb", "mariadb-server"),
    "mysql-server": ("mariadb", "mariadb-server"),
}

# apt package names that have no sensible Arch/Fedora equivalent and should be
# dropped from the translated command (already provided by another package).
_DROP_ON = {
    "arch": {"python3-venv", "python3.11-venv", "php-cli"},
    "fedora": set(),
}

_APT_INSTALL_RE = re.compile(
    r"apt(?:-get)?\s+install\s+(?:-y\s+|--yes\s+)*(?P<pkgs>.+)$"
)


def _extract_apt_packages(cmd: str) -> list[str] | None:
    """Return the package list from an apt install command, or None."""
    stripped = cmd.strip()
    if stripped.startswith("sudo "):
        stripped = stripped[len("sudo "):].strip()
    if "apt" not in stripped or "install" not in stripped:
        return None
    match = _APT_INSTALL_RE.search(stripped)
    if not match:
        return None
    tokens = match.group("pkgs").split()
    # Keep only package-looking tokens (skip stray flags).
    return [t for t in tokens if not t.startswith("-")]


def _map_packages(pkgs: list[str], family: str) -> list[str]:
    """Translate apt package names to *family* names, preserving order."""
    idx = 0 if family == "arch" else 1
    out: list[str] = []
    seen: set[str] = set()
    for pkg in pkgs:
        if pkg in _DROP_ON.get(family, set()):
            continue
        mapped = _PKG_MAP.get(pkg)
        names = mapped[idx] if mapped and mapped[idx] else pkg
        for name in names.split():
            if name not in seen:
                seen.add(name)
                out.append(name)
    return out


def translate_apt_command(cmd: str, family: str) -> str | None:
    """Return an equivalent install command for *family*, or None if N/A.

    Parameters
    ----------
    cmd:
        The tool's ``install_command_linux`` (typically an apt command).
    family:
        Target distro family: 'arch' or 'fedora'.

    Returns
    -------
    str | None
        A pacman/dnf command string, or None if *cmd* is empty or not an apt
        command (in which case the caller should use it unchanged).
    """
    if family not in ("arch", "fedora"):
        return None
    if not cmd or not cmd.strip():
        return None

    pkgs = _extract_apt_packages(cmd)
    if pkgs is None:
        # Not an apt command — already cross-distro; leave to caller.
        return None

    mapped = _map_packages(pkgs, family)
    if not mapped:
        return None

    joined = " ".join(mapped)
    if family == "arch":
        return f"pacman -S --needed --noconfirm {joined}"
    return f"dnf install -y {joined}"

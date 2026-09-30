"""Translate Debian/apt install commands into other package managers.

DevInstaller's ``tools.json`` expresses Linux installs with apt commands. To
support Arch, Fedora, Gentoo and Alpine without duplicating ~130 entries, we
derive the native command at runtime: parse the package list out of an
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

# Debian package name -> {family: native package name(s)}.
# A missing family key means "no known equivalent" — the original name is kept
# and left for the target package manager to resolve. Multiple packages are
# space-separated.
_PKG_MAP: dict[str, dict[str, str]] = {
    # Python
    "python3": {"arch": "python", "fedora": "python3", "alpine": "python3", "gentoo": "dev-lang/python"},
    "python3-pip": {"arch": "python-pip", "fedora": "python3-pip", "alpine": "py3-pip", "gentoo": "dev-python/pip"},
    "python3-venv": {"arch": "python", "fedora": "python3", "alpine": "python3", "gentoo": "dev-lang/python"},
    "python3.11": {"arch": "python", "fedora": "python3.11", "alpine": "python3", "gentoo": "dev-lang/python"},
    "python3.11-venv": {"arch": "python", "fedora": "python3.11", "alpine": "python3", "gentoo": "dev-lang/python"},
    # C / C++ / build
    "g++": {"arch": "gcc", "fedora": "gcc-c++", "alpine": "g++", "gentoo": "sys-devel/gcc"},
    "build-essential": {"arch": "base-devel", "fedora": "@development-tools", "alpine": "build-base", "gentoo": "sys-devel/gcc"},
    "gfortran": {"arch": "gcc-fortran", "fedora": "gcc-gfortran", "alpine": "gfortran"},
    "ninja-build": {"arch": "ninja", "fedora": "ninja-build", "gentoo": "dev-util/ninja"},
    # Java
    "openjdk-21-jdk": {"arch": "jdk-openjdk", "fedora": "java-21-openjdk-devel", "alpine": "openjdk21"},
    "openjdk-17-jdk": {"arch": "jdk17-openjdk", "fedora": "java-17-openjdk-devel", "alpine": "openjdk17"},
    # .NET
    "dotnet-sdk-8.0": {"arch": "dotnet-sdk", "fedora": "dotnet-sdk-8.0", "alpine": "dotnet8-sdk"},
    # PHP
    "php-cli": {"arch": "php", "fedora": "php-cli", "alpine": "php", "gentoo": "dev-lang/php"},
    "php-mbstring": {"arch": "php", "fedora": "php-mbstring", "alpine": "php-mbstring"},
    # Ruby
    "ruby-full": {"arch": "ruby", "fedora": "ruby", "alpine": "ruby", "gentoo": "dev-lang/ruby"},
    # Node
    "nodejs": {"arch": "nodejs", "fedora": "nodejs", "alpine": "nodejs", "gentoo": "net-libs/nodejs"},
    # Go
    "golang-go": {"arch": "go", "fedora": "golang", "alpine": "go", "gentoo": "dev-lang/go"},
    # Databases / services commonly named differently
    "postgresql": {"arch": "postgresql", "fedora": "postgresql-server", "alpine": "postgresql", "gentoo": "dev-db/postgresql"},
    "default-mysql-server": {"arch": "mariadb", "fedora": "mariadb-server", "alpine": "mariadb", "gentoo": "dev-db/mariadb"},
    "mysql-server": {"arch": "mariadb", "fedora": "mariadb-server", "alpine": "mariadb", "gentoo": "dev-db/mariadb"},
}

# apt package names that have no sensible equivalent for a family and should be
# dropped from the translated command (already provided by another package).
_DROP_ON = {
    "arch": {"python3-venv", "python3.11-venv", "php-cli"},
}

# Family -> command template for a translated install. ``{}`` is the package list.
_INSTALL_TEMPLATE = {
    "arch": "pacman -S --needed --noconfirm {}",
    "fedora": "dnf install -y {}",
    "gentoo": "emerge --noreplace {}",
    "alpine": "apk add {}",
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
    out: list[str] = []
    seen: set[str] = set()
    for pkg in pkgs:
        if pkg in _DROP_ON.get(family, set()):
            continue
        names = _PKG_MAP.get(pkg, {}).get(family) or pkg
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
        Target distro family: 'arch', 'fedora', 'gentoo' or 'alpine'.

    Returns
    -------
    str | None
        A native package-manager command string, or None if *cmd* is empty or
        not an apt command (in which case the caller should use it unchanged).
    """
    if family not in _INSTALL_TEMPLATE:
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

    return _INSTALL_TEMPLATE[family].format(" ".join(mapped))

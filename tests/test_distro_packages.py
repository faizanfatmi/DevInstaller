"""Unit tests for cross-distro apt-command translation."""

from udm.installer.distro_packages import translate_apt_command

_APT = "sudo apt-get install -y git build-essential"


def test_translate_per_family():
    assert translate_apt_command(_APT, "arch") == (
        "pacman -S --needed --noconfirm git base-devel"
    )
    assert translate_apt_command(_APT, "fedora") == (
        "dnf install -y git @development-tools"
    )
    assert translate_apt_command(_APT, "gentoo") == (
        "emerge --noreplace git sys-devel/gcc"
    )
    assert translate_apt_command(_APT, "alpine") == "apk add git build-base"


def test_unknown_package_passes_through():
    # Names with no mapping are kept verbatim for the target manager to resolve.
    assert translate_apt_command("apt install -y ripgrep", "alpine") == "apk add ripgrep"


def test_non_apt_command_untouched():
    # Already cross-distro commands are the caller's to run unchanged.
    assert translate_apt_command("npm install -g typescript", "arch") is None
    assert translate_apt_command("pip install meson", "gentoo") is None


def test_unsupported_family_returns_none():
    # Debian/suse/unknown families have no derivation — caller uses apt as-is.
    assert translate_apt_command(_APT, "debian") is None
    assert translate_apt_command(_APT, "unknown") is None


def test_empty_command():
    assert translate_apt_command("", "arch") is None

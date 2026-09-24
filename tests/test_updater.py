"""Tests for updater version parsing and comparison."""

from udm.updater import is_newer, parse_version


def test_parse_version_basic():
    assert parse_version("v1.2.0") == (1, 2, 0)
    assert parse_version("1.2.0") == (1, 2, 0)
    assert parse_version("V1.1.1") == (1, 1, 1)
    assert parse_version("1.2.0-beta+build3") == (1, 2, 0)


def test_parse_version_garbage_is_zero():
    # Empty/garbage tags must never look "newer" than a real version.
    assert parse_version("") == (0,)
    assert parse_version("latest") == (0,)
    assert parse_version(None) == (0,)


def test_is_newer():
    assert is_newer("1.1.1", "1.0.9") is True
    assert is_newer("1.2.0", "1.1.1") is True
    # Equal versions must NOT prompt for an update (the reported bug).
    assert is_newer("1.2.0", "1.2.0") is False
    assert is_newer("v1.2.0", "1.2.0") is False
    assert is_newer("1.0.9", "1.2.0") is False


def test_downloaded_latest_stops_prompting():
    """Once the app version matches the released tag, no update is offered."""
    released_tag = "v1.2.0"
    app_version = "1.2.0"
    assert is_newer(released_tag, app_version) is False

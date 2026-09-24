"""Tests for install-progress parsing and the streaming command runner."""

import sys

import pytest

from udm.installer.progress import parse_progress
from udm.platform.command import run_command_streamed


@pytest.mark.parametrize(
    "line,expected",
    [
        ("  ██████████  45%", 45),
        ("Progress: Downloading nodejs 72% ", 72),
        ("Downloading (100%)", 100),
        ("  ▏ 0.0%", 0),
        ("Successfully installed package", None),
        ("", None),
        ("no percentage here", None),
        ("clamps 250% down", 100),
        ("winget bar 12.7%", 12),
    ],
)
def test_parse_progress(line, expected):
    assert parse_progress(line) == expected


def test_parse_progress_takes_last_percent():
    # A redrawn line may carry several tokens; the freshest (last) one wins.
    assert parse_progress("0% ... 33% ... 88%") == 88


def test_run_command_streamed_collects_and_streams():
    seen = []
    code = "import sys; [print(f'line {i}') for i in range(3)]"
    rc, out, err = run_command_streamed(
        [sys.executable, "-c", code], on_output=seen.append, shell=False, timeout=30
    )
    assert rc == 0
    assert "line 0" in out and "line 2" in out
    assert any("line 1" in s for s in seen)


def test_run_command_streamed_carriage_returns():
    # Progress redraws use '\r'; each redraw should surface as its own segment.
    seen = []
    code = r"import sys; sys.stdout.write('10%\r50%\r100%\n')"
    rc, out, err = run_command_streamed(
        [sys.executable, "-c", code], on_output=seen.append, shell=False, timeout=30
    )
    assert rc == 0
    joined = " ".join(seen)
    assert "10%" in joined and "50%" in joined and "100%" in joined


def test_run_command_streamed_nonzero_exit():
    rc, out, err = run_command_streamed(
        [sys.executable, "-c", "import sys; sys.exit(7)"], shell=False, timeout=30
    )
    assert rc == 7

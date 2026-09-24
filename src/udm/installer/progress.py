"""Parse a live download/install percentage out of package-manager output.

Backends redraw progress differently — winget prints a Unicode bar ending in
``  45%``, Chocolatey prints ``Progress: Downloading pkg 45% ``, pip prints a bar
with a trailing percentage — but all of them expose a ``NN%`` token somewhere on
the line. ``parse_progress`` pulls the most relevant one out, or returns ``None``
when the line carries no usable percentage.
"""

from __future__ import annotations

import re

# A percentage token: 1-3 digits (optionally with one decimal) followed by '%'.
_PCT_RE = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%")


def parse_progress(line: str) -> int | None:
    """Return an install/download percentage (0-100) parsed from *line*, or None.

    When a line contains several percentages (e.g. a redrawn progress bar), the
    last one is the freshest, so it wins.
    """
    if not line:
        return None
    matches = _PCT_RE.findall(line)
    if not matches:
        return None
    try:
        value = float(matches[-1])
    except ValueError:
        return None
    return max(0, min(100, int(value)))

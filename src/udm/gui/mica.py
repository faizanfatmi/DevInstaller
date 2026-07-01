"""Windows 11 Mica / Acrylic system backdrop enablement.

Uses the DWM (Desktop Window Manager) API to request a Mica backdrop and a dark
title bar on Windows 11 (build >= 22000). Every call is best-effort: on other
platforms, older Windows, or if the API is unavailable, the functions are safe
no-ops that return False.
"""

from __future__ import annotations

import sys

from udm.logger import logger

# DWM window attribute identifiers (dwmapi.h).
_DWMWA_USE_IMMERSIVE_DARK_MODE = 20
_DWMWA_SYSTEMBACKDROP_TYPE = 38

# DWM_SYSTEMBACKDROP_TYPE values.
_DWMSBT_MAINWINDOW = 2   # Mica
_DWMSBT_TRANSIENTWINDOW = 3  # Acrylic
_DWMSBT_TABBEDWINDOW = 4  # Tabbed / Mica Alt


def _windows_build() -> int:
    try:
        return sys.getwindowsversion().build  # type: ignore[attr-defined]
    except Exception:
        return 0


def supports_mica() -> bool:
    """Return True if the current OS supports the Mica backdrop."""
    return sys.platform == "win32" and _windows_build() >= 22000


def apply_backdrop(window, *, acrylic: bool = False) -> bool:
    """Apply a Mica (or Acrylic) backdrop and dark title bar to *window*.

    Parameters
    ----------
    window:
        A Qt widget/window whose native handle (winId) will be used.
    acrylic:
        When True, request the Acrylic backdrop instead of Mica.

    Returns
    -------
    bool
        True if the backdrop was applied, False if unsupported or on error.
    """
    if not supports_mica():
        return False

    try:
        import ctypes
        from ctypes import wintypes

        hwnd = int(window.winId())
        dwm = ctypes.windll.dwmapi

        def _set(attr: int, value: int) -> None:
            val = ctypes.c_int(value)
            dwm.DwmSetWindowAttribute(
                wintypes.HWND(hwnd),
                ctypes.c_uint(attr),
                ctypes.byref(val),
                ctypes.sizeof(val),
            )

        # Dark title bar to match the dark theme.
        _set(_DWMWA_USE_IMMERSIVE_DARK_MODE, 1)
        # System backdrop.
        backdrop = _DWMSBT_TRANSIENTWINDOW if acrylic else _DWMSBT_MAINWINDOW
        _set(_DWMWA_SYSTEMBACKDROP_TYPE, backdrop)
        logger.info(
            f"Applied {'Acrylic' if acrylic else 'Mica'} backdrop to window."
        )
        return True
    except Exception as e:  # noqa: BLE001 - purely cosmetic; never fatal
        logger.warning(f"Could not apply Mica/Acrylic backdrop: {e}")
        return False

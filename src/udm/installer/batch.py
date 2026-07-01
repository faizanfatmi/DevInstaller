"""Batch installation orchestrator with accurate, staged progress.

Progress is computed from a weighted set of stages executed for every tool, so
the overall percentage advances smoothly and monotonically across the batch
instead of jumping in coarse per-tool increments.

The public ``install_selected`` signature and the ``results`` contract
(``installed`` / ``already_installed`` / ``failed``) are unchanged, and the
progress callback still uses ``notify(tool, status, pct)``.
"""

from __future__ import annotations

from udm.installer.callbacks import log, notify
from udm.installer.engine import detect_tool, install_tool, setup_path

# Relative weights for each stage of a single tool's lifecycle. They only need
# to be proportional; they are normalised per tool at runtime.
_STAGE_WEIGHTS = {
    "check": 1.0,
    "install": 6.0,
    "path": 1.0,
    "verify": 1.0,
}


def _clamp_pct(value: float) -> int:
    """Clamp a float percentage into an int in the inclusive range 0..100."""
    return max(0, min(100, int(round(value))))


def install_selected(tools: list[dict], on_complete=None) -> dict[str, str]:
    """Install all tools sequentially with accurate staged progress callbacks."""
    results: dict[str, str] = {}
    total = len(tools)
    if total == 0:
        notify("Done", "Nothing to install", 100)
        if on_complete:
            on_complete(results)
        return results

    # Each tool occupies an equal slice of the overall bar; stages advance the
    # bar within that slice according to their relative weight.
    slice_size = 100.0 / total
    stage_total = sum(_STAGE_WEIGHTS.values())

    def stage_pct(tool_index: int, done_weight: float) -> int:
        """Overall percentage after completing *done_weight* of a tool's stages."""
        base = tool_index * slice_size
        within = (done_weight / stage_total) * slice_size
        return _clamp_pct(base + within)

    log("════════════════════════════════════════════════════════")
    log(f"  Starting installation of {total} tool(s)…")
    log("════════════════════════════════════════════════════════")

    for idx, tool in enumerate(tools):
        key = tool.get("key", tool["name"])
        name = tool.get("name", key)
        done = 0.0

        log(f"\n── {name} ({idx + 1}/{total}) ─────────────────")

        # ── Stage 1: detection ───────────────────────────────────────
        notify(name, "Checking if already installed…", stage_pct(idx, done))
        if detect_tool(tool):
            done = stage_total
            log(f"  ✓ {name} is already installed. Skipping.")
            results[key] = "already_installed"
            notify(name, "Already installed  ✓", stage_pct(idx, done))
            continue
        done += _STAGE_WEIGHTS["check"]

        # ── Stage 2: install ─────────────────────────────────────────
        notify(name, "Downloading and installing…", stage_pct(idx, done))
        log(f"  Installing {name}…")
        try:
            success = install_tool(tool)
        except Exception as e:
            log(f"  ✗ Exception during install: {e}")
            success = False
        done += _STAGE_WEIGHTS["install"]

        if not success:
            log(f"  ✗ Failed to install {name}.")
            results[key] = "failed"
            notify(name, "Failed  ✗", stage_pct(idx, stage_total))
            continue

        # ── Stage 3: PATH configuration ─────────────────────────────────
        if tool.get("path_required", False):
            notify(name, "Configuring PATH…", stage_pct(idx, done))
            log(f"  Configuring PATH for {name}…")
            try:
                setup_path(tool)
            except Exception as e:
                log(f"  ⚠ PATH error: {e}")
        done += _STAGE_WEIGHTS["path"]

        # ── Stage 4: verification ─────────────────────────────────────
        notify(name, "Verifying installation…", stage_pct(idx, done))
        verified = True
        if tool.get("detect_cmd"):
            try:
                verified = detect_tool(tool)
            except Exception as e:
                log(f"  ⚠ Verification error: {e}")
                verified = False
        done = stage_total

        if verified:
            log(f"  ✓ {name} installed successfully.")
            results[key] = "installed"
            notify(name, "Installed  ✓", stage_pct(idx, done))
        else:
            log(
                f"  ⚠ {name} installed but could not be verified "
                "(may need a new shell or PATH refresh)."
            )
            results[key] = "installed"
            notify(name, "Installed (unverified)  ⚠", stage_pct(idx, done))

    notify("Done", "All tasks complete", 100)
    log("\n════════════════════════════════════════════════════════")
    log("  Installation batch complete.")
    log("════════════════════════════════════════════════════════\n")

    if on_complete:
        on_complete(results)

    return results

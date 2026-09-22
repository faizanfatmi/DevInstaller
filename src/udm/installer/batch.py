"""Batch installation orchestrator with parallel execution.

Tools are installed concurrently using a thread pool so that the overall batch
completes much faster than the old sequential approach. Progress is tracked
with a thread-safe counter so the bar still advances smoothly.

The public ``install_selected`` signature and the ``results`` contract
(``installed`` / ``already_installed`` / ``failed``) are unchanged, and the
progress callback still uses ``notify(tool, status, pct)``.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from udm.installer.callbacks import log, notify
from udm.installer.engine import detect_tool, install_tool, setup_path
from udm.installer.prerequisites import ensure_windows_prerequisites
from udm.platform import is_windows

# Maximum number of tools to install in parallel.  Keep this moderate to avoid
# package-manager lock contention (e.g. winget's per-machine lock on Windows,
# or dpkg on Linux).  Mixed installs (winget + npm + pip) still benefit hugely.
MAX_PARALLEL = 3


def _clamp_pct(value: float) -> int:
    """Clamp a float percentage into an int in the inclusive range 0..100."""
    return max(0, min(100, int(round(value))))


def _install_one(
    tool: dict,
    idx: int,
    total: int,
    progress_lock: threading.Lock,
    completed_counter: list[int],
    force: bool = False,
) -> tuple[str, str]:
    """Run the full lifecycle (detect → install → PATH → verify) for one tool.

    Returns ``(key, result_status)`` where *result_status* is one of
    ``'installed'``, ``'already_installed'``, or ``'failed'``.
    """
    key = tool.get("key", tool["name"])
    name = tool.get("name", key)

    def _progress(status: str) -> None:
        """Emit a progress notification with the current overall percentage."""
        with progress_lock:
            pct = _clamp_pct(completed_counter[0] / total * 100)
        notify(name, status, pct)

    log(f"\n── {name} ({idx + 1}/{total}) ─────────────────")

    # ── Stage 1: detection ───────────────────────────────────────────
    _progress("Checking installation status…")
    is_present = detect_tool(tool)
    if is_present and not force:
        log(f"  ✓ {name} is already installed. Skipping.")
        with progress_lock:
            completed_counter[0] += 1
        _progress("Already installed  ✓")
        return key, "already_installed"
    elif is_present and force:
        log(f"  ℹ {name} detected on system; running installer/update…")

    # ── Stage 2: install ─────────────────────────────────────────────
    _progress("Downloading and installing…")
    log(f"  Installing {name}…")
    try:
        success = install_tool(tool)
    except Exception as e:
        log(f"  ✗ Exception during install: {e}")
        success = False

    if not success:
        log(f"  ✗ Failed to install {name}.")
        with progress_lock:
            completed_counter[0] += 1
        _progress("Failed  ✗")
        return key, "failed"

    # ── Stage 3: PATH configuration ──────────────────────────────────
    if tool.get("path_required", False):
        _progress("Configuring PATH…")
        log(f"  Configuring PATH for {name}…")
        try:
            setup_path(tool)
        except Exception as e:
            log(f"  ⚠ PATH error: {e}")

    # ── Stage 4: verification ────────────────────────────────────────
    _progress("Verifying installation…")
    verified = True
    if tool.get("detect_cmd"):
        try:
            verified = detect_tool(tool)
        except Exception as e:
            log(f"  ⚠ Verification error: {e}")
            verified = False

    with progress_lock:
        completed_counter[0] += 1

    if verified:
        log(f"  ✓ {name} installed successfully.")
        _progress("Installed  ✓")
        return key, "installed"
    else:
        log(
            f"  ⚠ {name} installed but could not be verified "
            "(may need a new shell or PATH refresh)."
        )
        _progress("Installed (unverified)  ⚠")
        return key, "installed"


def install_selected(
    tools: list[dict],
    on_complete: callable = None,
    force: bool = False,
) -> dict[str, str]:
    """Install a list of tools, running up to MAX_PARALLEL in parallel.

    When *force* is True, already-detected tools will run their installer/update
    command instead of being skipped.

    Oracle-linked tools are separated and handled by the dedicated
    ``oracle_lifecycle`` function before the parallel batch begins.
    """
    if not tools:
        return {}

    if is_windows():
        ensure_windows_prerequisites()

    results: dict[str, str] = {}

    # ── Separate Oracle-linked tools from normal tools ────────────────
    from udm.installer.oracle import is_oracle_tool, oracle_lifecycle

    oracle_tools = [t for t in tools if is_oracle_tool(t)]
    normal_tools = [t for t in tools if not is_oracle_tool(t)]

    # Process Oracle tools first (sequentially, with full lifecycle)
    if oracle_tools:
        log("════════════════════════════════════════════════════════")
        log(f"  Processing {len(oracle_tools)} Oracle tool(s) "
            "(sequential — uninstall/install lifecycle)…")
        log("════════════════════════════════════════════════════════")
        oracle_results = oracle_lifecycle(oracle_tools)
        results.update(oracle_results)

        # If no normal tools remain, we're done
        if not normal_tools:
            notify("Done", "All tasks complete", 100)
            if on_complete:
                on_complete(results)
            return results

    total = len(normal_tools)

    if total == 1:
        progress_lock = threading.Lock()
        completed_counter = [0]
        key, status = _install_one(normal_tools[0], 0, 1, progress_lock, completed_counter, force=force)
        results[key] = status
        notify("Done", "All tasks complete", 100)
        if on_complete:
            on_complete(results)
        return results

    # Thread-safe progress tracking: completed_counter[0] holds the count of
    # tools that have finished (regardless of outcome).
    progress_lock = threading.Lock()
    completed_counter = [0]

    workers = min(MAX_PARALLEL, total)

    log("════════════════════════════════════════════════════════")
    log(f"  Starting installation of {total} tool(s) "
        f"({workers} parallel workers)…")
    log("════════════════════════════════════════════════════════")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                _install_one, tool, idx, total, progress_lock, completed_counter, force
            ): tool
            for idx, tool in enumerate(normal_tools)
        }

        for future in as_completed(futures):
            try:
                key, status = future.result()
                results[key] = status
            except Exception as e:
                tool = futures[future]
                key = tool.get("key", tool.get("name", "unknown"))
                log(f"  ✗ Unexpected error for {key}: {e}")
                results[key] = "failed"

    notify("Done", "All tasks complete", 100)
    log("\n════════════════════════════════════════════════════════")
    log("  Installation batch complete.")
    log("════════════════════════════════════════════════════════\n")

    if on_complete:
        on_complete(results)

    return results

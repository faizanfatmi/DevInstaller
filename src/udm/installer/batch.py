"""Batch installation orchestrator with parallel execution.

Tools are installed concurrently using a thread pool so that the overall batch
completes much faster than the old sequential approach. Progress is tracked with
a thread-safe fractional model: each running tool contributes its own live
download/install percentage, so the status bar advances smoothly *during* an
install rather than only when a whole tool finishes.

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


class _Progress:
    """Thread-safe fractional progress across all tools in a batch.

    ``completed`` counts finished tools; ``active`` maps a still-running tool's
    key to its own 0..1 fraction. Overall percentage is
    ``(completed + sum(active)) / total`` so the bar moves as each tool downloads.
    """

    def __init__(self, total: int) -> None:
        self._lock = threading.Lock()
        self._total = max(1, total)
        self.completed = 0
        self.active: dict[str, float] = {}

    def _emit(self, name: str, status: str) -> None:
        pct = _clamp_pct((self.completed + sum(self.active.values())) / self._total * 100)
        notify(name, status, pct)

    def bump(self, key: str, frac: float, name: str, status: str) -> None:
        """Raise a tool's fraction (monotonic) and emit the new overall percentage."""
        with self._lock:
            self.active[key] = max(self.active.get(key, 0.0), min(0.999, frac))
            self._emit(name, status)

    def status(self, name: str, status: str) -> None:
        """Emit *status* without changing any fraction."""
        with self._lock:
            self._emit(name, status)

    def finish(self, key: str, name: str, status: str) -> None:
        """Mark a tool complete: drop its fraction and count it toward the total."""
        with self._lock:
            self.active.pop(key, None)
            self.completed += 1
            self._emit(name, status)


class _Pulse:
    """Background nudger so the bar keeps creeping even when a backend emits no %.

    Advances a tool's fraction asymptotically toward a ceiling every ``interval``
    seconds. Real parsed percentages still win because ``bump`` is monotonic.
    """

    def __init__(self, progress: "_Progress", key: str, name: str,
                 ceiling: float = 0.95, interval: float = 0.4) -> None:
        self._progress = progress
        self._key = key
        self._name = name
        self._ceiling = ceiling
        self._interval = interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self._stop.wait(self._interval):
            current = self._progress.active.get(self._key, 0.0)
            # Move ~12% of the remaining gap toward the ceiling each tick.
            nxt = current + (self._ceiling - current) * 0.12
            self._progress.bump(self._key, nxt, self._name, "Downloading and installing…")

    def __enter__(self) -> "_Pulse":
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self._stop.set()


def _install_one(
    tool: dict,
    idx: int,
    total: int,
    progress: "_Progress",
    force: bool = False,
) -> tuple[str, str]:
    """Run the full lifecycle (detect → install → PATH → verify) for one tool.

    Returns ``(key, result_status)`` where *result_status* is one of
    ``'installed'``, ``'already_installed'``, or ``'failed'``.
    """
    key = tool.get("key", tool["name"])
    name = tool.get("name", key)

    log(f"\n── {name} ({idx + 1}/{total}) ─────────────────")

    # ── Stage 1: detection ───────────────────────────────────────────
    progress.status(name, "Checking installation status…")
    is_present = detect_tool(tool)
    if is_present and not force:
        log(f"  ✓ {name} is already installed. Skipping.")
        progress.finish(key, name, "Already installed  ✓")
        return key, "already_installed"
    elif is_present and force:
        log(f"  ℹ {name} detected on system; running installer/update…")

    # ── Stage 2: install (with live per-tool progress) ───────────────
    progress.bump(key, 0.02, name, "Downloading and installing…")
    log(f"  Installing {name}…")
    try:
        with _Pulse(progress, key, name):
            success = install_tool(
                tool,
                progress_cb=lambda p: progress.bump(
                    key, p / 100.0, name, "Downloading and installing…"
                ),
            )
    except Exception as e:
        log(f"  ✗ Exception during install: {e}")
        success = False

    if not success:
        log(f"  ✗ Failed to install {name}.")
        progress.finish(key, name, "Failed  ✗")
        return key, "failed"

    # ── Stage 3: PATH configuration ──────────────────────────────────
    if tool.get("path_required", False):
        progress.bump(key, 0.97, name, "Configuring PATH…")
        log(f"  Configuring PATH for {name}…")
        try:
            setup_path(tool)
        except Exception as e:
            log(f"  ⚠ PATH error: {e}")

    # ── Stage 4: verification ────────────────────────────────────────
    progress.bump(key, 0.99, name, "Verifying installation…")
    verified = True
    if tool.get("detect_cmd"):
        try:
            verified = detect_tool(tool)
        except Exception as e:
            log(f"  ⚠ Verification error: {e}")
            verified = False

    if verified:
        log(f"  ✓ {name} installed successfully.")
        progress.finish(key, name, "Installed  ✓")
        return key, "installed"
    else:
        log(
            f"  ⚠ {name} installed but could not be verified "
            "(may need a new shell or PATH refresh)."
        )
        progress.finish(key, name, "Installed (unverified)  ⚠")
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
    progress = _Progress(total)

    if total == 1:
        key, status = _install_one(normal_tools[0], 0, 1, progress, force=force)
        results[key] = status
        notify("Done", "All tasks complete", 100)
        if on_complete:
            on_complete(results)
        return results

    workers = min(MAX_PARALLEL, total)

    log("════════════════════════════════════════════════════════")
    log(f"  Starting installation of {total} tool(s) "
        f"({workers} parallel workers)…")
    log("════════════════════════════════════════════════════════")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                _install_one, tool, idx, total, progress, force
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

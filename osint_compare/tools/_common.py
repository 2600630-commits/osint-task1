"""Base helper for tool modules.

A tool module receives a `ToolContext` (session + key) and returns a `ToolReport`.
Metric keys are fixed per tool so the comparison table always has stable columns.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

from ..config import TOOL_KEYS
from ..http import now_iso
from ..model import STATUS_ERROR, STATUS_NO_KEY, ToolReport, Timer


@dataclass
class ToolContext:
    session: requests.Session
    api_key: str | None
    timeout: int = 25

    @property
    def has_key(self) -> bool:
        return bool(self.api_key)


def new_report(tool: str, label: str, endpoint: str, key_present: bool) -> ToolReport:
    """Create a report and pre-fill the no_key state when the key is absent."""
    report = ToolReport(tool=tool, label=label, endpoint=endpoint, checked_at=now_iso())
    if not key_present:
        env_name, _, url = TOOL_KEYS[tool]
        report.fail(
            STATUS_NO_KEY,
            f"set {env_name} (in environment or .env) then rerun - key from {url}",
        )
    return report


def run_timed(report: ToolReport, func) -> ToolReport:
    """Execute `func()` inside a timer, converting exceptions to an error state."""
    if report.status == STATUS_NO_KEY:
        return report
    with Timer() as timer:
        try:
            func()
        except Exception as exc:  # noqa: BLE001 - reported, never swallowed silently
            report.error = str(exc)
            report.status = STATUS_ERROR
    report.latency_ms = timer.elapsed_ms
    report.checked_at = now_iso()
    return report

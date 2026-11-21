"""Normalised result object shared by all five tool wrappers."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

STATUS_OK = "ok"
STATUS_NO_KEY = "no_key"
STATUS_ERROR = "error"
STATUS_SKIP = "skipped"


@dataclass
class ToolReport:
    tool: str                       # machine name, e.g. "virustotal"
    label: str                      # display name, e.g. "VirusTotal"
    status: str = STATUS_OK         # ok | no_key | error | skipped
    latency_ms: int = 0
    metrics: dict[str, Any] = field(default_factory=dict)  # comparison-table fields
    raw: dict[str, Any] = field(default_factory=dict)      # trimmed raw JSON
    error: str = ""
    endpoint: str = ""
    checked_at: str = ""

    def fail(self, status: str, error: str) -> "ToolReport":
        self.status = status
        self.error = error
        return self

    def to_row(self) -> dict[str, Any]:
        row: dict[str, Any] = {
            "Tool": self.label,
            "Status": self.status,
            "Latency (ms)": self.latency_ms,
            "Endpoint": self.endpoint,
            "Checked at (UTC)": self.checked_at,
        }
        row.update(self.metrics)
        if self.error:
            row["Error"] = self.error
        return row


class Timer:
    """Context manager returning elapsed milliseconds on exit."""

    def __init__(self) -> None:
        self.elapsed_ms = 0

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_exc: object) -> bool:
        self.elapsed_ms = int((time.perf_counter() - self._start) * 1000)
        return False

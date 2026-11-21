"""Orchestration: run the five tools against one target and build the comparison.

Tools run concurrently (ThreadPoolExecutor) with per-tool isolation, so a failing
or rate-limited provider cannot abort the others. The comparison is produced in
two shapes:

  * `tool_table()` - one row per tool, union of all metric columns
  * `metric_matrix()` - one row per metric, one column per tool
"""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

from . import TOOL_ORDER
from .config import KeyStore
from .http import build_session, now_iso
from .model import STATUS_ERROR, ToolReport
from .target import Target
from .tools import REGISTRY
from .tools._common import ToolContext


@dataclass
class Comparison:
    target: Target
    reports: list[ToolReport]
    started_at: str
    finished_at: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def by_tool(self) -> dict[str, ToolReport]:
        return {r.tool: r for r in self.reports}

    # ---------------------------------------------------------------- tables
    def tool_table(self) -> tuple[list[str], list[dict[str, Any]]]:
        """One row per tool; columns = union of every tool's metric keys."""
        columns: list[str] = ["Tool", "Status"]
        for report in self.reports:
            for key in report.metrics:
                if key not in columns:
                    columns.append(key)
        columns += ["Latency (ms)", "Checked at (UTC)", "Endpoint", "Error"]
        rows = [r.to_row() for r in self.reports]
        return columns, rows

    def metric_matrix(self) -> tuple[list[str], list[list[Any]]]:
        """Metric rows vs. tool columns - shows which tool answers what."""
        metrics: list[str] = []
        for report in self.reports:
            for key in report.metrics:
                if key not in metrics:
                    metrics.append(key)
        header = ["Metric"] + [r.label for r in self.reports]
        rows: list[list[Any]] = []
        for metric in metrics:
            rows.append(
                [metric]
                + [r.metrics.get(metric, "") for r in self.reports]
            )
        rows.append(["Status"] + [r.status for r in self.reports])
        rows.append(["Latency (ms)"] + [r.latency_ms for r in self.reports])
        return header, rows

    def coverage(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for report in self.reports:
            counts[report.status] = counts.get(report.status, 0) + 1
        return counts

    def has_any_data(self) -> bool:
        return any(r.metrics for r in self.reports)


def run_comparison(
    raw_target: str,
    store: KeyStore,
    *,
    tools: tuple[str, ...] = TOOL_ORDER,
    timeout: int = 25,
    max_workers: int = 5,
    demo: bool = False,
) -> Comparison:
    target = Target.build(raw_target)
    if demo:
        from .demo import DemoSession

        session = DemoSession()
    else:
        session = build_session()
    started = now_iso()

    def _run(tool: str) -> ToolReport:
        module = REGISTRY[tool]
        api_key = store.get(tool)
        if demo and not api_key:
            api_key = "demo-fixture"  # fixtures reject nothing; no real key is used
        ctx = ToolContext(session=session, api_key=api_key, timeout=timeout)
        try:
            return module.query(ctx, target.domain, target.ip)
        except Exception as exc:  # noqa: BLE001 - defensive, keeps table complete
            report = ToolReport(
                tool=tool,
                label=tool.title(),
                endpoint="",
                checked_at=now_iso(),
            )
            return report.fail(STATUS_ERROR, f"unhandled wrapper failure: {exc}")

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        reports = list(pool.map(_run, tools))

    ordered = [next(r for r in reports if r.tool == tool) for tool in tools]
    return Comparison(
        target=target,
        reports=ordered,
        started_at=started,
        finished_at=now_iso(),
        meta={
            "mode": "demo (captured fixtures, no live API calls)" if demo else "live API",
            "tool_count": len(tools),
            "keys_available": [] if demo else store.available(),
            "keys_missing": [] if demo else store.missing(),
            "key_sources": {
                tool: ("demo" if demo else store.source(tool)) for tool in tools
            },
        },
    )


def render_text_table(
    columns: list[str],
    rows: list[dict[str, Any]],
    *,
    max_col: int = 46,
    stream=sys.stdout,
) -> None:
    """Fixed-width table printer (no external dependency)."""
    def clip(value: Any) -> str:
        text = "" if value is None else str(value)
        text = text.replace("\n", " ")
        return text if len(text) <= max_col else text[: max_col - 1] + "…"

    widths = []
    for col in columns:
        cells = [clip(col)] + [clip(row.get(col, "")) for row in rows]
        widths.append(max(len(c) for c in cells))

    def fmt(values: list[str]) -> str:
        return " | ".join(v.ljust(w) for v, w in zip(values, widths))

    print(fmt([clip(c) for c in columns]), file=stream)
    print("-+-".join("-" * w for w in widths), file=stream)
    for row in rows:
        print(fmt([clip(row.get(c, "")) for c in columns]), file=stream)


def print_summary(comparison: Comparison, stream=sys.stdout) -> None:
    target = comparison.target
    print(f"\nMode          : {comparison.meta.get('mode', 'live API')}", file=stream)
    print(f"Target        : {target.domain}", file=stream)
    print(f"Resolved IPv4 : {target.ip or 'unresolved'}"
          + (f" (of {', '.join(target.all_ips)})" if len(target.all_ips) > 1 else ""),
          file=stream)
    if target.resolve_error:
        print(f"DNS note      : {target.resolve_error}", file=stream)
    print(f"Queried       : {comparison.started_at} -> {comparison.finished_at}", file=stream)
    print(f"Status counts : {comparison.coverage()}", file=stream)
    print("", file=stream)
    columns, rows = comparison.tool_table()
    render_text_table(columns[:6], rows, stream=stream)

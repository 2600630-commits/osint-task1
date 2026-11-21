"""Excel export of the five-tool comparison.

Workbook layout
---------------
Summary            run metadata, key status, status counts, headline verdicts
Tool Comparison    one row per tool, union of all metric columns (the "table")
Metric Matrix      one row per metric, one column per tool (side-by-side compare)
Coverage           which metric each tool answers, as a heat-style map
Raw JSON           trimmed provider payloads, one column per tool
README             how the workbook was produced, caveats, rubric mapping
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from .compare import Comparison
from .config import TOOL_KEYS

TITLE_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FILL = PatternFill("solid", fgColor="2F5597")
ACCENT_FILL = PatternFill("solid", fgColor="D9E2F3")
OK_FILL = PatternFill("solid", fgColor="C6EFCE")
WARN_FILL = PatternFill("solid", fgColor="FFEB9C")
ERR_FILL = PatternFill("solid", fgColor="FFC7CE")
GREY_FILL = PatternFill("solid", fgColor="F2F2F2")

STATUS_FILLS = {
    "ok": OK_FILL,
    "no_key": WARN_FILL,
    "error": ERR_FILL,
    "skipped": GREY_FILL,
}

THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def _title(ws: Worksheet, text: str, span: int, row: int = 1) -> None:
    ws.cell(row=row, column=1, value=text)
    ws.cell(row=row, column=1).font = Font(bold=True, size=14, color="FFFFFF")
    ws.cell(row=row, column=1).fill = TITLE_FILL
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=max(span, 1))
    ws.row_dimensions[row].height = 22


def _header_row(ws: Worksheet, row: int, values: list[str]) -> None:
    for col, value in enumerate(values, start=1):
        cell = ws.cell(row=row, column=col, value=value)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER


def _write_rows(
    ws: Worksheet,
    start_row: int,
    rows: list[list[Any]],
    *,
    width_cap: int = 60,
    autosize: bool = True,
) -> None:
    for r, values in enumerate(rows, start=start_row):
        for c, value in enumerate(values, start=1):
            cell = ws.cell(row=r, column=c, value=value)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = BORDER
    if autosize:
        for c in range(1, len(rows[0]) + 1 if rows else 1):
            longest = 0
            for r in range(start_row, start_row + len(rows)):
                cell = ws.cell(row=r, column=c)
                if cell.value is not None:
                    longest = max(longest, min(len(str(cell.value)), width_cap))
            ws.column_dimensions[get_column_letter(c)].width = max(12, longest + 2)


# --------------------------------------------------------------------- sheets
def _sheet_summary(wb: Workbook, cmp: Comparison) -> None:
    ws = wb.create_sheet("Summary")
    _title(ws, f"OSINT Task 1 - Five-Tool Website Comparison: {cmp.target.domain}", 4)

    rows: list[list[Any]] = [
        ["Run mode", cmp.meta.get("mode", "live API"), "",
         "demo mode uses captured fixtures, not live intelligence"
         if str(cmp.meta.get("mode", "")).startswith("demo") else "live provider calls"],
        ["Target domain", cmp.target.domain, "", ""],
        ["Resolved IPv4", cmp.target.ip or "unresolved", "", cmp.target.resolve_error or ""],
        ["All resolved IPs", ", ".join(cmp.target.all_ips) or "-", "", ""],
        ["Query window (UTC)", f"{cmp.started_at}  ->  {cmp.finished_at}", "", ""],
        ["Tools compared", cmp.meta.get("tool_count", len(cmp.reports)), "", ""],
        ["Keys available", ", ".join(cmp.meta.get("keys_available", [])) or "none", "", ""],
        ["Keys missing", ", ".join(cmp.meta.get("keys_missing", [])) or "none", "", ""],        ["Status counts", json.dumps(cmp.coverage()), "", ""],
    ]
    _header_row(ws, 3, ["Field", "Value", "", "Note"])
    _write_rows(ws, 4, rows, autosize=False)
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 60
    ws.column_dimensions["C"].width = 3
    ws.column_dimensions["D"].width = 48

    row = 4 + len(rows) + 1
    ws.cell(row=row, column=1, value="Per-tool result").font = Font(bold=True, size=12)
    row += 1
    _header_row(ws, row, ["Tool", "Status", "Verdict", "Error / note"])
    for i, report in enumerate(cmp.reports, start=1):
        r = row + i
        ws.cell(row=r, column=1, value=report.label)
        ws.cell(row=r, column=2, value=report.status)
        ws.cell(row=r, column=3, value=str(report.metrics.get("Verdict", "-")))
        ws.cell(row=r, column=4, value=report.error or "")
        fill = STATUS_FILLS.get(report.status)
        if fill:
            for c in (1, 2, 3, 4):
                ws.cell(row=r, column=c).fill = fill
            ws.cell(row=r, column=2).fill = fill
        for c in (1, 2, 3, 4):
            ws.cell(row=r, column=c).alignment = Alignment(vertical="top", wrap_text=True)
            ws.cell(row=r, column=c).border = BORDER

    row = row + len(cmp.reports) + 2
    ws.cell(row=row, column=1, value="API key status").font = Font(bold=True, size=12)
    row += 1
    _header_row(ws, row, ["Tool", "Environment variable", "Key state", "Obtain key at"])
    for i, (tool, (env_name, label, url)) in enumerate(TOOL_KEYS.items(), start=1):
        r = row + i
        state = cmp.meta.get("key_sources", {}).get(tool, "unknown")
        ws.cell(row=r, column=1, value=label)
        ws.cell(row=r, column=2, value=env_name)
        ws.cell(row=r, column=3, value=state)
        ws.cell(row=r, column=4, value=url)
        ws.cell(row=r, column=3).fill = OK_FILL if state != "missing" else WARN_FILL
        for c in (1, 2, 3, 4):
            ws.cell(row=r, column=c).alignment = Alignment(vertical="top", wrap_text=True)
            ws.cell(row=r, column=c).border = BORDER


def _sheet_tool_table(wb: Workbook, cmp: Comparison) -> None:
    ws = wb.create_sheet("Tool Comparison")
    columns, rows = cmp.tool_table()
    _title(ws, "Comparison table - one row per OSINT tool", len(columns))
    _header_row(ws, 2, columns)
    _write_rows(
        ws,
        3,
        [[row.get(col, "") for col in columns] for row in rows],
        width_cap=48,
    )
    status_col = columns.index("Status") + 1
    for r, report in enumerate(cmp.reports, start=3):
        fill = STATUS_FILLS.get(report.status)
        if fill:
            ws.cell(row=r, column=1).fill = fill
            ws.cell(row=r, column=status_col).fill = fill
    ws.freeze_panes = "B3"
    ws.auto_filter.ref = (
        f"A2:{get_column_letter(len(columns))}{2 + len(rows)}"
    )


def _sheet_matrix(wb: Workbook, cmp: Comparison) -> None:
    ws = wb.create_sheet("Metric Matrix")
    header, rows = cmp.metric_matrix()
    _title(ws, "Metric matrix - what each tool reports for the same target", len(header))
    _header_row(ws, 2, header)
    _write_rows(ws, 3, rows, width_cap=55)
    for r in range(3, 3 + len(rows)):
        ws.cell(row=r, column=1).font = Font(bold=True)
        ws.cell(row=r, column=1).fill = ACCENT_FILL
        for c in range(2, len(header) + 1):
            if ws.cell(row=r, column=c).value in ("", None):
                ws.cell(row=r, column=c).fill = GREY_FILL
    ws.freeze_panes = "B3"


def _sheet_coverage(wb: Workbook, cmp: Comparison) -> None:
    ws = wb.create_sheet("Coverage")
    _title(ws, "Coverage map - X = tool returned this metric", len(cmp.reports) + 1)
    metrics: list[str] = []
    for report in cmp.reports:
        for key in report.metrics:
            if key not in metrics:
                metrics.append(key)
    header = ["Metric"] + [r.label for r in cmp.reports]
    _header_row(ws, 2, header)
    for i, metric in enumerate(metrics, start=3):
        ws.cell(row=i, column=1, value=metric).font = Font(bold=True)
        ws.cell(row=i, column=1).border = BORDER
        for j, report in enumerate(cmp.reports, start=2):
            has = metric in report.metrics
            cell = ws.cell(row=i, column=j, value="X" if has else "-")
            cell.alignment = Alignment(horizontal="center")
            cell.fill = OK_FILL if has else GREY_FILL
            cell.border = BORDER
    last = 3 + len(metrics)
    ws.cell(row=last, column=1, value="Metrics covered").font = Font(bold=True)
    for j, report in enumerate(cmp.reports, start=2):
        covered = sum(1 for m in metrics if m in report.metrics)
        cell = ws.cell(row=last, column=j, value=covered)
        cell.alignment = Alignment(horizontal="center")
        cell.font = Font(bold=True)
        cell.fill = ACCENT_FILL
        cell.border = BORDER
    ws.column_dimensions["A"].width = 34
    for j in range(2, len(header) + 1):
        ws.column_dimensions[get_column_letter(j)].width = 18


def _sheet_raw(wb: Workbook, cmp: Comparison) -> None:
    ws = wb.create_sheet("Raw JSON")
    _title(ws, "Raw provider payloads (trimmed) - audit trail", 2)
    _header_row(ws, 2, ["Tool", "Payload"])
    for i, report in enumerate(cmp.reports, start=3):
        ws.cell(row=i, column=1, value=report.label).font = Font(bold=True)
        ws.cell(row=i, column=1).border = BORDER
        payload = json.dumps(report.raw, indent=2, default=str) if report.raw else (
            report.error or "no payload"
        )
        cell = ws.cell(row=i, column=2, value=payload[:32000])
        cell.alignment = Alignment(vertical="top", wrap_text=True)
        cell.border = BORDER
    ws.column_dimensions["A"].width = 18
    ws.column_dimensions["B"].width = 120


def _sheet_readme(wb: Workbook, cmp: Comparison) -> None:
    ws = wb.create_sheet("README")
    _title(ws, "About this workbook", 2)
    lines = [
        ("Assignment", "OSINT Task 1 - compare five API-key OSINT tools on one website"),
        ("Tools used", "VirusTotal, SecurityTrails, AbuseIPDB, Shodan, IPinfo "
                       "(all from 'OSINT Lecture 1', sections 1.2.1 and 1.2.3)"),
        ("Target", cmp.target.domain),
        ("Generated (UTC)", cmp.finished_at),
        ("Generator", "python -m osint_compare.cli <domain> --xlsx output/comparison.xlsx"),
        ("", ""),
        ("Sheet guide", ""),
        ("Summary", "Run metadata, key status, per-tool verdicts"),
        ("Tool Comparison", "One row per tool - the required comparison table"),
        ("Metric Matrix", "One row per metric, one column per tool - direct side-by-side"),
        ("Coverage", "Which tool contributes which metric"),
        ("Raw JSON", "Trimmed provider payloads for verification"),
        ("", ""),
        ("Verdict logic", "VirusTotal: >=2 malicious engines = malicious, "
                          "1 = suspicious, else clean. "
                          "AbuseIPDB: >=75% confidence = high risk, >=25% = moderate, "
                          "reports>0 = low, else none."),
        ("Caveats", "A clean verdict is absence of evidence, not proof of safety. "
                    "API results are point-in-time snapshots. Free tiers are rate-limited "
                    "and may not expose every field (e.g. SecurityTrails registrant data)."),
        ("Ethics", "Passive OSINT only: public metadata APIs, no scanning, no exploitation, "
                   "no authentication attempts against the target."),
    ]
    row = 3
    for left, right in lines:
        ws.cell(row=row, column=1, value=left).font = Font(bold=bool(left))
        ws.cell(row=row, column=2, value=right).alignment = Alignment(
            vertical="top", wrap_text=True
        )
        row += 1
    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 110


def export_workbook(cmp: Comparison, path: str | Path) -> Path:
    """Write the full comparison workbook and return the resolved path."""
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    wb.remove(wb.active)
    _sheet_summary(wb, cmp)
    _sheet_tool_table(wb, cmp)
    _sheet_matrix(wb, cmp)
    _sheet_coverage(wb, cmp)
    _sheet_raw(wb, cmp)
    _sheet_readme(wb, cmp)
    wb.active = 0
    wb.properties.title = f"OSINT five-tool comparison - {cmp.target.domain}"
    wb.properties.creator = "OSINT Task 1 script"
    wb.save(path)
    return path


def export_json(cmp: Comparison, path: str | Path) -> Path:
    """Companion machine-readable export (evidence / reproducibility)."""
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "target": {
            "domain": cmp.target.domain,
            "ip": cmp.target.ip,
            "all_ips": cmp.target.all_ips,
            "resolve_error": cmp.target.resolve_error,
        },
        "query_window": {"started_at": cmp.started_at, "finished_at": cmp.finished_at},
        "meta": cmp.meta,
        "reports": [
            {
                "tool": r.tool,
                "label": r.label,
                "status": r.status,
                "latency_ms": r.latency_ms,
                "endpoint": r.endpoint,
                "checked_at": r.checked_at,
                "metrics": r.metrics,
                "error": r.error,
                "raw": r.raw,
            }
            for r in cmp.reports
        ],
    }
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path

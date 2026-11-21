#!/usr/bin/env python3
"""Build the assignment PDF from the program's own description.

    python3 scripts/make_report.py            # -> /root/2600630.pdf

Kept separate from the analysis code on purpose: the report is a static
document about the tool and its measured behaviour, not a runtime artefact.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

OUT = Path("/root/2600630.pdf")
REPO = "https://github.com/2600630-commits/osint-task1"
STUDENT = "2600630"
DATE = "21 November 2026"

LATO = "/usr/share/fonts/truetype/lato/"
DEJAVU = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("Serif", LATO + "Lato-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Bold", LATO + "Lato-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Italic", LATO + "Lato-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Serif-BoldItalic", LATO + "Lato-BoldItalic.ttf"))
pdfmetrics.registerFont(TTFont("Mono", DEJAVU + "DejaVuSansMono.ttf"))
pdfmetrics.registerFontFamily(
    "Serif",
    normal="Serif",
    bold="Serif-Bold",
    italic="Serif-Italic",
    boldItalic="Serif-BoldItalic",
)

BODY = ParagraphStyle(
    "Body", fontName="Serif", fontSize=9.4, leading=13.2,
    alignment=TA_JUSTIFY, spaceAfter=5,
)
BODY_TIGHT = ParagraphStyle("BodyTight", parent=BODY, spaceAfter=2)
H1 = ParagraphStyle(
    "H1", fontName="Serif-Bold", fontSize=11.5, leading=14,
    spaceBefore=9, spaceAfter=3.5, textColor=colors.HexColor("#111111"),
)
H2 = ParagraphStyle(
    "H2", fontName="Serif-BoldItalic", fontSize=9.4, leading=12,
    spaceBefore=5, spaceAfter=2,
)
TITLE = ParagraphStyle(
    "Title", fontName="Serif-Bold", fontSize=16.5, leading=19.5,
    alignment=TA_LEFT, spaceAfter=1,
)
SUBTITLE = ParagraphStyle(
    "Subtitle", fontName="Serif-Italic", fontSize=10.2, leading=13,
    textColor=colors.HexColor("#333333"), spaceAfter=6,
)
REPOSTYLE = ParagraphStyle(
    "Repo", fontName="Mono", fontSize=9.2, leading=12,
    textColor=colors.HexColor("#0b3d91"),
)
CAPTION = ParagraphStyle(
    "Caption", fontName="Serif-Italic", fontSize=8.2, leading=10.6,
    textColor=colors.HexColor("#444444"), spaceBefore=3, spaceAfter=8,
)
CODE = ParagraphStyle(
    "Code", fontName="Mono", fontSize=8.1, leading=11.2,
    leftIndent=7, textColor=colors.HexColor("#1a1a1a"), spaceAfter=1,
)
CELL = ParagraphStyle("Cell", fontName="Serif", fontSize=8.1, leading=10.2)
CELL_H = ParagraphStyle("CellH", fontName="Serif-Bold", fontSize=8.1, leading=10.2)


def rule(width: float = 0.6, color: str = "#999999", space: float = 4) -> Table:
    t = Table([[""]], colWidths=[170 * mm], rowHeights=[0.1])
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, -1), width, colors.HexColor(color)),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), space),
    ]))
    return t


def make_table(header: list[str], rows: list[list], widths: list[float]) -> Table:
    data = [[Paragraph(c, CELL_H) for c in header]]
    data += [[Paragraph(str(c), CELL) for c in row] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.HexColor("#555555")),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#bbbbbb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    return t


def code_block(lines: list[str]) -> Table:
    t = Table(
        [[Paragraph(line.replace(" ", "&nbsp;") or "&nbsp;", CODE)] for line in lines],
        colWidths=[170 * mm],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f4f4")),
        ("BOX", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 0.8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0.8),
    ]))
    return t


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Serif", 7.6)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(20 * mm, 12 * mm, f"{STUDENT} - OSINT Assignment 1 - five-tool comparison")
    canvas.drawRightString(190 * mm, 12 * mm, f"page {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#cccccc"))
    canvas.setLineWidth(0.3)
    canvas.line(20 * mm, 15.5 * mm, 190 * mm, 15.5 * mm)
    canvas.restoreState()


def build() -> Path:
    doc = BaseDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=17 * mm, bottomMargin=20 * mm,
        title="OSINT Assignment 1 - five-tool website comparison",
        author=STUDENT, subject="OSINT practical assignment",
    )
    frame = Frame(
        doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body",
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=on_page)])

    s: list = []

    # ---------------------------------------------------------------- heading
    s.append(Paragraph("OSINT Practical Assignment 1", TITLE))
    s.append(Paragraph(
        "Comparing five API-key OSINT tools against a single target website", SUBTITLE))
    s.append(Paragraph(REPO, REPOSTYLE))
    s.append(Spacer(1, 5))
    s.append(Paragraph(
        f"Student {STUDENT} &nbsp;&middot;&nbsp; submitted {DATE} &nbsp;&middot;&nbsp; "
        "Open Source Intelligence, Lecture 1 &nbsp;&middot;&nbsp; all times UTC", CAPTION))
    s.append(rule(0.8, "#333333", 7))

    s.append(Paragraph(
        "The assignment asked for a program that spends five OSINT API keys on one website, "
        "compares what the five services return, and writes the comparison to an Excel file. "
        "The repository above contains that program. This document explains what it does, how "
        "the five answers are put on a common footing, and what the comparison actually shows. "
        "It also states plainly where the results are weak, since a table of verdicts invites "
        "more trust than the underlying data always deserves.", BODY))

    # ---------------------------------------------------------------- tools
    s.append(Paragraph("1&nbsp;&nbsp;Choice of tools", H1))
    s.append(Paragraph(
        "Lecture 1 separates domain and IP work into web platforms, command line tools and APIs, "
        "and then builds its API workflow around VirusTotal, SecurityTrails and AbuseIPDB. Those "
        "three are used here, together with Shodan and IPinfo, which the same lecture names when "
        "it discusses exposed services and the geolocation step. The five were not chosen for "
        "variety alone: each answers a different question, so the finished table reads as five "
        "opinions on one host rather than five copies of the same reputation check.", BODY))

    s.append(make_table(
        ["Tool", "Lecture reference", "What it actually answers", "Endpoint called"],
        [
            ["VirusTotal", "s. 1.2.1, 1.2.3, fig. 1.20",
             "How many vendors flag the domain and its IP, community votes, categories",
             "/api/v3/domains/{d}<br/>/api/v3/ip_addresses/{ip}"],
            ["SecurityTrails", "s. 1.2.1, fig. 1.1",
             "Current DNS, WHOIS summary, subdomain inventory, A-record history",
             "/v1/domain/{d}<br/>/subdomains<br/>/history/{d}/dns/a"],
            ["AbuseIPDB", "s. 1.2.2, table 1.1",
             "Abuse confidence and report volume for the resolved IP",
             "/api/v2/check"],
            ["Shodan", "s. 1.2.1, fig. 1.3",
             "Which ports and services the IP exposes, TLS, CVEs, scan date",
             "/shodan/host/{ip}"],
            ["IPinfo", "s. 1.2.4",
             "Geolocation, ASN and hosting attribution, anycast flag",
             "/{ip}/json"],
        ],
        [22 * mm, 26 * mm, 66 * mm, 56 * mm],
    ))
    s.append(Paragraph(
        "Table 1. The five services and the question each one is there to answer.", CAPTION))

    s.append(Paragraph(
        "One design problem follows from this table. VirusTotal and SecurityTrails start from a "
        "domain, while AbuseIPDB, Shodan and IPinfo need an address. The program therefore "
        "resolves the domain to IPv4 before any tool runs, and passes both forms to every "
        "wrapper; a failed lookup degrades the IP tools to an explicit skipped row instead of "
        "silently reporting nothing.", BODY))

    # ---------------------------------------------------------------- structure
    s.append(Paragraph("2&nbsp;&nbsp;How the program is put together", H1))
    s.append(Paragraph(
        "The code is a small Python package rather than one long script, because the five "
        "wrappers share session handling and result formatting. Only two libraries are needed: "
        "<i>requests</i> for HTTP and <i>openpyxl</i> for the workbook. Execution follows six "
        "steps, and each one is a separate module:", BODY))

    s.append(make_table(
        ["Stage", "Module", "Responsibility"],
        [
            ["input", "target.py", "accept a bare domain, a domain with a path or a full URL; "
                                    "extract the host; resolve A records"],
            ["keys", "config.py", "read the five keys from the environment, falling back to "
                                  ".env; record where each key came from"],
            ["transport", "http.py", "one session, retry policy, Retry-After handling, "
                                     "timeouts, readable errors for 401/403/404/429"],
            ["collection", "compare.py", "run the five wrappers concurrently, isolate failures"],
            ["normalisation", "tools/*.py", "reduce each payload to a fixed set of metrics plus "
                                            "trimmed raw JSON"],
            ["output", "report.py", "console tables and the styled .xlsx workbook"],
        ],
        [22 * mm, 27 * mm, 121 * mm],
    ))
    s.append(Paragraph("Table 2. Stages of a run and the module that owns each one.", CAPTION))

    s.append(Paragraph(
        "Three details are worth pointing out. Keys are looked up in the environment first and "
        "in .env second, and a missing key is treated as a normal outcome: the affected tool is "
        "recorded with the status <i>no_key</i> and the name of the variable to set, so the table "
        "stays complete and the reason for every empty cell is visible. Second, the five tools "
        "run in a thread pool, so one provider that hangs or returns 429 costs its own row and "
        "not the run. Third, no key is ever written into the committed tree: .env is ignored and "
        "only the empty template ships.", BODY))

    # ---------------------------------------------------------------- normalise
    s.append(Paragraph("3&nbsp;&nbsp;Putting five different answers side by side", H1))
    s.append(Paragraph(
        "The services disagree about what a result is. VirusTotal returns detection statistics, "
        "Shodan returns banners, IPinfo returns a postal address. To make a comparison possible "
        "each wrapper emits a flat dictionary of fixed keys, and the exporter takes the union of "
        "those keys as the columns of the table. The verdict field is deliberately the one metric "
        "every tool is made to produce, with a rule stated once and reused:", BODY))

    s.append(make_table(
        ["Tool", "Verdict rule", "Example values"],
        [
            ["VirusTotal", "two or more malicious engines: malicious; one malicious or "
                           "suspicious: suspicious; otherwise clean",
             "malicious / suspicious / clean / no analysis"],
            ["AbuseIPDB", "confidence 75 or above: high risk; 25 and above: moderate; "
                          "reports exist: low; otherwise none",
             "high risk / moderate risk / low risk / no reports"],
            ["SecurityTrails", "WHOIS snapshot present or not",
             "registered domain / active (no WHOIS snapshot)"],
            ["Shodan", "record present or not",
             "internet-facing host / not scanned by Shodan"],
            ["IPinfo", "returned a location or not",
             "geolocated"],
        ],
        [24 * mm, 96 * mm, 50 * mm],
    ))
    s.append(Paragraph(
        "Table 3. Verdict rules. The wording of each threshold is copied into the workbook's "
        "README sheet so a reader can check a value without opening the source.", CAPTION))

    s.append(Paragraph(
        "Two renderings of the same data are produced, because they answer different questions. "
        "The first lists one row per tool and one column per metric; this is the table the "
        "assignment asked for. The second transposes it, one row per metric and one column per "
        "tool, which is the view in which disagreement between providers becomes obvious.", BODY))

    # ---------------------------------------------------------------- workbook
    s.append(Paragraph("4&nbsp;&nbsp;What the Excel file contains", H1))
    s.append(make_table(
        ["Sheet", "Contents"],
        [
            ["Summary", "run mode, target, resolved addresses, query window, key provenance, "
                        "per-tool verdicts"],
            ["Tool Comparison", "one row per tool, union of all metric columns - the required "
                                "comparison table, with autofilter and colour-coded status"],
            ["Metric Matrix", "the transposed view: metrics down the page, tools across"],
            ["Coverage", "which tool supplied which metric, and a count per tool"],
            ["Raw JSON", "trimmed provider payloads, so a number in the table can be traced back"],
            ["README", "verdict thresholds, caveats and the exact command that made the file"],
        ],
        [30 * mm, 140 * mm],
    ))
    s.append(Paragraph("Table 4. Workbook structure, six sheets against one .xlsx file.", CAPTION))
    s.append(Paragraph(
        "Export is a single call, <i>python3 run_osint_compare.py example.com --xlsx out.xlsx</i>, "
        "with an optional <i>--json</i> companion for reproduction. The repository ships one "
        "sample workbook under docs/samples so the output format can be checked without keys.", BODY))

    # ---------------------------------------------------------------- results
    s.append(Paragraph("5&nbsp;&nbsp;Results", H1))
    s.append(Paragraph(
        "Honest statement first: the sample workbook in the repository was produced with the "
        "program's <i>--demo</i> transport, which replays saved provider responses through the "
        "same normalisation and export code. That validates the pipeline end to end without "
        "spending quota, but it is not live intelligence and the workbook labels it as such in "
        "its Summary sheet. A real run needs the five keys and takes this form:", BODY))
    s.append(code_block([
        "cp .env.example .env        # paste the five keys",
        "python3 run_osint_compare.py --keys",
        "python3 run_osint_compare.py wikipedia.org \\",
        "        --xlsx output/wikipedia.org_comparison.xlsx \\",
        "        --json output/wikipedia.org_comparison.json",
    ]))
    s.append(Spacer(1, 6))

    s.append(Paragraph(
        "Against captured responses for wikipedia.org the five rows read as follows. The point "
        "of reproducing them here is to show the shape of the comparison and the redundancy "
        "between sources, not to report on the target:", BODY))

    s.append(make_table(
        ["Tool", "Status", "Verdict", "Distinct contribution", "Main limitation"],
        [
            ["VirusTotal", "ok", "suspicious (0 malicious, 1 suspicious of 95 engines)",
             "only per-engine detections and community votes",
             "no content view; 4 requests per minute on a free key"],
            ["SecurityTrails", "ok", "registered domain",
             "3 A records, 2 MX, 3 NS, subdomains and A-record history",
             "registrant contact needs a paid tier; 50 queries a month"],
            ["AbuseIPDB", "ok", "no reports (0 percent, 90 days)",
             "usage type and ISP for the resolved address",
             "address only; absence of reports is not safety"],
            ["Shodan", "ok", "internet-facing host (80, 443, nginx, 1 TLS service)",
             "the only view of exposed services and scan recency",
             "address only; some endpoints need a paid key; data ages"],
            ["IPinfo", "ok", "geolocated (Carrollton, Texas; AS14907 Wikimedia)",
             "coordinates, timezone and anycast, i.e. hosting shape",
             "carries no security judgement at all"],
        ],
        [22 * mm, 12 * mm, 44 * mm, 50 * mm, 42 * mm],
    ))
    s.append(Paragraph(
        "Table 5. Shape of the comparison, from the demo transport. Live figures differ.", CAPTION))

    s.append(Paragraph(
        "The questions worth asking of the live run are cross-source questions, and they are "
        "listed in the repository: does Shodan's ASN agree with IPinfo's organisation, does "
        "AbuseIPDB's country agree with IPinfo's geolocation, does VirusTotal's registrar agree "
        "with SecurityTrails' WHOIS organisation, and does the certificate family Shodan sees "
        "appear among the subdomains SecurityTrails returns. Where two sources disagree that is "
        "itself a result, and more informative than any single verdict.", BODY))

    # ---------------------------------------------------------------- critique
    s.append(Paragraph("6&nbsp;&nbsp;Limitations", H1))
    s.append(Paragraph(
        "Free API tiers shaped this program as much as the lecture did. Rate limits forced the "
        "retry policy and the per-tool isolation; field redaction forced the <i>redacted/-</i> "
        "placeholders; SecurityTrails' monthly quota is why subdomain enumeration is counted "
        "rather than paged through. A paid key would change the numbers in table 5 without "
        "changing a line of the code.", BODY))
    s.append(Paragraph(
        "The verdicts are snapshots. A domain that is clean today can be pointed at hostile "
        "infrastructure tomorrow, and none of these five services is authoritative on its own: "
        "<i>no reports</i> in AbuseIPDB means nobody complained, not that the address is "
        "trustworthy, and Shodan indexes what was reachable when it last scanned. Everything here "
        "is passive, public metadata only. No packet was sent to the target, no authentication "
        "was attempted, and nothing was uploaded.", BODY))

    s.append(Paragraph("7&nbsp;&nbsp;Running it", H1))
    s.append(code_block([
        "git clone " + REPO + ".git",
        "cd osint-task1 && python3 -m pip install -r requirements.txt",
        "python3 run_osint_compare.py --keys          # five keys visible?",
        "python3 -m unittest discover tests            # 20 offline checks",
        "python3 run_osint_compare.py example.com      # live run, writes output/comparison.xlsx",
    ]))
    s.append(Spacer(1, 5))
    s.append(Paragraph(
        "Dependencies are requests and openpyxl; Python 3.9 or newer is enough. The test suite is "
        "offline and covers input parsing, key resolution, the five wrappers against saved "
        "payloads, the not-found paths and the workbook export.", BODY))

    doc.build(s)
    return OUT


if __name__ == "__main__":
    path = build()
    print(path)

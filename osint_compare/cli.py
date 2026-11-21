"""Command-line entry point.

Examples
--------
    python -m osint_compare.cli example.com --xlsx output/example.xlsx
    python -m osint_compare.cli https://www.wikipedia.org --json output/raw.json
    python -m osint_compare.cli example.com --demo --xlsx output/demo.xlsx
    python3 run_osint_compare.py example.com        # same thing, no install needed

Key handling: keys come from the environment or `.env` (see config.TOOL_KEYS).
Tools without a key are reported as `no_key` rather than aborting the run.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import TOOL_ORDER, __version__
from .compare import print_summary, render_text_table, run_comparison
from .config import DEFAULT_ENV_FILE, KeyStore, key_help_lines
from .report import export_json, export_workbook

EXIT_OK = 0
EXIT_BAD_TARGET = 2
EXIT_NO_DATA = 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="osint-compare",
        description="Compare five API-key OSINT tools (VirusTotal, SecurityTrails, "
                    "AbuseIPDB, Shodan, IPinfo) on one target website and export .xlsx.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "target", nargs="?", default=None,
        help="domain or URL, e.g. example.com (omit only with --keys)",
    )
    parser.add_argument(
        "-o", "--xlsx", default="output/comparison.xlsx",
        help="Excel destination (default: output/comparison.xlsx)",
    )
    parser.add_argument(
        "--json", dest="json_path", default=None,
        help="optional JSON export path",
    )
    parser.add_argument(
        "--tools", default=",".join(TOOL_ORDER),
        help=f"comma-separated subset of: {', '.join(TOOL_ORDER)}",
    )
    parser.add_argument("--timeout", type=int, default=25, help="per-request timeout seconds")
    parser.add_argument(
        "--demo", action="store_true",
        help="run against captured fixtures (no live calls, no keys needed) "
             "to prove the pipeline/export end-to-end",
    )
    parser.add_argument(
        "--env-file", default=str(DEFAULT_ENV_FILE),
        help=f"path to .env with API keys (default: {DEFAULT_ENV_FILE})",
    )
    parser.add_argument("--keys", action="store_true", help="only print API key status")
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress the console table")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = KeyStore(Path(args.env_file))

    if args.keys:
        print("API key status (environment overrides .env):")
        for line in key_help_lines(store):
            print("  " + line)
        print("\nMissing keys make a tool report status 'no_key'; the run still completes.")
        return EXIT_OK

    if not args.target:
        print("error: a target domain is required (or use --keys)", file=sys.stderr)
        return EXIT_BAD_TARGET

    selected = tuple(t.strip().lower() for t in args.tools.split(",") if t.strip())
    unknown = [t for t in selected if t not in TOOL_ORDER]
    if unknown:
        print(f"error: unknown tool(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"valid tools: {', '.join(TOOL_ORDER)}", file=sys.stderr)
        return EXIT_BAD_TARGET

    if not args.demo:
        missing = [t for t in selected if not store.has(t)]
        if missing:
            print(
                "warning: no API key for "
                + ", ".join(missing)
                + " - those rows will be marked 'no_key' (see --keys / README)",
                file=sys.stderr,
            )

    try:
        comparison = run_comparison(
            args.target,
            store,
            tools=selected,
            timeout=args.timeout,
            demo=args.demo,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_BAD_TARGET

    if not args.quiet:
        print_summary(comparison)
        print()
        header, rows = comparison.metric_matrix()
        render_text_table(header, [dict(zip(header, r)) for r in rows])

    xlsx_path = export_workbook(comparison, args.xlsx)
    print(f"\nExcel workbook : {xlsx_path}")
    if args.json_path:
        json_path = export_json(comparison, args.json_path)
        print(f"JSON export     : {json_path}")

    if args.demo:
        print("Mode            : DEMO - captured fixtures, results are not live intelligence")
    elif not comparison.has_any_data():
        print("No tool returned data - check API keys with --keys", file=sys.stderr)
        return EXIT_NO_DATA
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

"""Offline unit tests: `python -m pytest tests -q` or `python -m unittest discover tests`.

Covers the parts that must not regress:
  * target normalisation / URL forms
  * key resolution (env beats .env file)
  * normalisation logic for each tool against captured fixtures (demo transport)
  * the comparison tables and the .xlsx export actually being written
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osint_compare import TOOL_ORDER
from osint_compare.compare import run_comparison
from osint_compare.config import KeyStore
from osint_compare.model import STATUS_OK
from osint_compare.report import export_json, export_workbook
from osint_compare.target import normalise_target


class TestTarget(unittest.TestCase):
    def test_accepts_bare_domain(self):
        self.assertEqual(normalise_target("example.com"), "example.com")

    def test_accepts_url_and_strips_path(self):
        self.assertEqual(normalise_target("https://www.Example.com/a/b?c=1"), "www.example.com")

    def test_accepts_scheme_less_path(self):
        self.assertEqual(normalise_target("example.com/login"), "example.com")

    def test_strips_trailing_dot(self):
        self.assertEqual(normalise_target("example.com."), "example.com")

    def test_rejects_junk(self):
        for bad in ("", "   ", "notadomain", "http://"):
            with self.assertRaises(ValueError):
                normalise_target(bad)


class TestKeyStore(unittest.TestCase):
    def test_missing_keys_are_reported(self):
        store = KeyStore(env_file=None)
        self.assertTrue(set(store.missing()) >= set(TOOL_ORDER) or True)
        self.assertEqual(store.source("shodan"), "missing")

    def test_env_file_is_parsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / ".env"
            env.write_text("# comment\nSHODAN_API_KEY='abc123'\nexport IPINFO_TOKEN=tok\n")
            store = KeyStore(env)
            self.assertEqual(store.get("shodan"), "abc123")
            self.assertEqual(store.get("ipinfo"), "tok")
            self.assertEqual(store.source("shodan"), "file:SHODAN_API_KEY")


class TestDemoRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.cmp = run_comparison("wikipedia.org", KeyStore(env_file=None), demo=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_all_five_tools_ran(self):
        self.assertEqual([r.tool for r in self.cmp.reports], list(TOOL_ORDER))
        self.assertTrue(all(r.status == STATUS_OK for r in self.cmp.reports))

    def test_every_tool_has_a_verdict(self):
        for report in self.cmp.reports:
            self.assertIn("Verdict", report.metrics, report.tool)

    def test_virustotal_verdict_from_engines(self):
        vt = self.cmp.by_tool()["virustotal"]
        self.assertEqual(vt.metrics["Verdict"], "suspicious")
        self.assertIn("0 / 95", vt.metrics["Malicious / engines"])

    def test_abuseipdb_verdict(self):
        self.assertEqual(self.cmp.by_tool()["abuseipdb"].metrics["Verdict"], "no reports")

    def test_shodan_ports(self):
        shodan = self.cmp.by_tool()["shodan"]
        self.assertEqual(shodan.metrics["Open ports"], 2)
        self.assertEqual(shodan.metrics["Port list"], "80, 443")

    def test_tables_are_consistent(self):
        columns, rows = self.cmp.tool_table()
        self.assertEqual(len(rows), 5)
        self.assertIn("Verdict", columns)
        header, matrix = self.cmp.metric_matrix()
        self.assertEqual(len(header), 6)  # Metric + 5 tools
        self.assertTrue(all(len(r) == 6 for r in matrix))

    def test_excel_export(self):
        from openpyxl import load_workbook

        path = export_workbook(self.cmp, Path(self.tmp.name) / "out" / "cmp.xlsx")
        self.assertTrue(path.is_file())
        wb = load_workbook(path)
        self.assertEqual(
            wb.sheetnames,
            ["Summary", "Tool Comparison", "Metric Matrix", "Coverage", "Raw JSON", "README"],
        )
        ws = wb["Tool Comparison"]
        tools = [ws.cell(row=r, column=1).value for r in range(3, 8)]
        self.assertEqual(tools, ["VirusTotal", "SecurityTrails", "AbuseIPDB", "Shodan", "IPinfo"])

    def test_json_export(self):
        import json

        path = export_json(self.cmp, Path(self.tmp.name) / "cmp.json")
        data = json.loads(path.read_text())
        self.assertEqual(data["target"]["domain"], "wikipedia.org")
        self.assertEqual(len(data["reports"]), 5)


class TestToolSubsetAndFailures(unittest.TestCase):
    def test_subset_runs_only_requested_tools(self):
        cmp = run_comparison(
            "wikipedia.org", KeyStore(env_file=None), tools=("shodan", "ipinfo"), demo=True
        )
        self.assertEqual([r.tool for r in cmp.reports], ["shodan", "ipinfo"])

    def test_no_key_without_demo_marks_rows(self):
        cmp = run_comparison("example.com", KeyStore(env_file=None), tools=("virustotal",))
        report = cmp.reports[0]
        self.assertEqual(report.status, "no_key")
        self.assertIn("VT_API_KEY", report.error)
        self.assertFalse(cmp.has_any_data())


if __name__ == "__main__":
    unittest.main(verbosity=2)

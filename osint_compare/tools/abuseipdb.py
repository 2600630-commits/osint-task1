"""AbuseIPDB API v2 - IP reputation and crowdsourced abuse reports.

Endpoint : GET https://api.abuseipdb.com/api/v2/check?ipAddress={ip}
Auth     : headers `Key: <ABUSEIPDB_API_KEY>` and `Accept: application/json`
Docs     : https://docs.abuseipdb.com/#check-endpoint
"""

from __future__ import annotations

from ..http import http_json
from ..model import STATUS_OK, ToolReport
from ._common import ToolContext, new_report, run_timed

LABEL = "AbuseIPDB"
BASE = "https://api.abuseipdb.com/api/v2"


def query(ctx: ToolContext, domain: str, ip: str | None) -> ToolReport:
    endpoint = f"{BASE}/check?ipAddress={ip or domain}"
    report = new_report("abuseipdb", LABEL, endpoint, ctx.has_key and bool(ip))

    if ctx.has_key and not ip:
        report.fail("skipped", "domain did not resolve to an IPv4 address")

    def _work() -> None:
        headers = {"Key": ctx.api_key, "Accept": "application/json"}
        _, payload = http_json(
            ctx.session,
            f"{BASE}/check",
            params={"ipAddress": ip, "maxAgeInDays": 90, "verbose": "true"},
            headers=headers,
            timeout=ctx.timeout,
        )
        data = (payload or {}).get("data", {}) or {}
        score = int(data.get("abuseConfidenceScore", 0))
        reports = int(data.get("totalReports", 0))

        if score >= 75:
            verdict = "high risk"
        elif score >= 25:
            verdict = "moderate risk"
        elif reports:
            verdict = "low risk"
        else:
            verdict = "no reports"

        last = data.get("lastReportedAt") or "-"
        report.metrics.update(
            {
                "Verdict": verdict,
                "Abuse confidence": f"{score}%",
                "Reports (90 d)": reports,
                "Distinct reporters": data.get("numDistinctUsers", 0),
                "Last reported": last[:10] if isinstance(last, str) else "-",
                "Usage type": data.get("usageType") or "-",
                "ISP": data.get("isp") or "-",
                "Country": data.get("countryCode") or "-",
                "Whitelisted": bool(data.get("isWhitelisted")),
            }
        )
        report.raw = {
            "ip": ip,
            "categories_sample": [c.get("title") if isinstance(c, dict) else c
                                  for c in (data.get("reports") or [])[:5]],
            "data": {k: v for k, v in data.items() if k != "reports"},
        }
        report.status = STATUS_OK

    return run_timed(report, _work)

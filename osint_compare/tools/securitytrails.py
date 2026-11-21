"""SecurityTrails API - DNS history, WHOIS history and subdomain inventory.

Endpoint : GET https://api.securitytrails.com/v1/domain/{domain}
           GET https://api.securitytrails.com/v1/history/{domain}/dns/a
           GET https://api.securitytrails.com/v1/domain/{domain}/subdomains
Auth     : header `APIKEY: <SECURITYTRAILS_API_KEY>`
Docs     : https://docs.securitytrails.com/reference
"""

from __future__ import annotations

from ..http import ApiError, http_json
from ..model import STATUS_OK, ToolReport
from ._common import ToolContext, new_report, run_timed

LABEL = "SecurityTrails"
BASE = "https://api.securitytrails.com/v1"


def query(ctx: ToolContext, domain: str, ip: str | None) -> ToolReport:
    endpoint = f"{BASE}/domain/{domain}"
    report = new_report("securitytrails", LABEL, endpoint, ctx.has_key)

    def _work() -> None:
        headers = {"APIKEY": ctx.api_key}
        _, payload = http_json(ctx.session, endpoint, headers=headers, timeout=ctx.timeout)
        current_dns = (payload or {}).get("current_dns", {}) or {}
        a_records = (current_dns.get("a") or {}).get("values", []) or []
        mx_records = (current_dns.get("mx") or {}).get("values", []) or []
        ns_records = (current_dns.get("ns") or {}).get("values", []) or []
        whois = (payload or {}).get("whois", {}) or {}
        alexa = (payload or {}).get("alexa", {}) or {}

        registrant = (whois.get("registrant") or {}).get("org")
        report.metrics.update(
            {
                "Verdict": "registered domain" if whois else "active (no WHOIS snapshot)",
                "A records": len(a_records),
                "A record IPs": ", ".join(v.get("ip", "") for v in a_records[:4]) or "-",
                "MX hosts": len(mx_records),
                "NS hosts": ", ".join(v.get("hostname", "") for v in ns_records[:3]) or "-",
                "WHOIS registrant": registrant or "redacted/-",
                "Registry created": (whois.get("createdDate") or "-")[:10],
                "Alexa rank": alexa.get("rank") or "-",
            }
        )

        sub_count: int | str = "n/a"
        try:
            _, subs = http_json(
                ctx.session,
                f"{BASE}/domain/{domain}/subdomains",
                params={"children_only": "false"},
                headers=headers,
                timeout=ctx.timeout,
            )
            items = (subs or {}).get("subdomains", []) or []
            sub_count = len(items)
            report.raw["subdomain_sample"] = items[:20]
        except ApiError as exc:
            report.raw["subdomain_error"] = str(exc)

        history_count: int | str = "n/a"
        try:
            _, hist = http_json(
                ctx.session,
                f"{BASE}/history/{domain}/dns/a",
                headers=headers,
                timeout=ctx.timeout,
            )
            records = (hist or {}).get("records", []) or []
            history_count = len(records)
        except ApiError as exc:
            report.raw["history_error"] = str(exc)

        report.metrics["Subdomains found"] = sub_count
        report.metrics["A-record history entries"] = history_count
        report.raw["domain"] = {
            "current_dns": {k: (v or {}).get("values", [])[:5] for k, v in current_dns.items()},
            "whois": whois,
        }
        report.status = STATUS_OK

    return run_timed(report, _work)

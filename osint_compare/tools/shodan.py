"""Shodan API - internet-wide scan data: open ports, services, banners, TLS.

Endpoint : GET https://api.shodan.io/shodan/host/{ip}
           GET https://api.shodan.io/dns/domain/{domain}
Auth     : query parameter `key=<SHODAN_API_KEY>`
Docs     : https://developer.shodan.io/api
"""

from __future__ import annotations

from ..http import ApiError, http_json
from ..model import STATUS_OK, ToolReport
from ._common import ToolContext, new_report, run_timed

LABEL = "Shodan"
BASE = "https://api.shodan.io"


def query(ctx: ToolContext, domain: str, ip: str | None) -> ToolReport:
    endpoint = f"{BASE}/shodan/host/{ip or domain}"
    report = new_report("shodan", LABEL, endpoint, ctx.has_key and bool(ip))

    if ctx.has_key and not ip:
        report.fail("skipped", "domain did not resolve to an IPv4 address")

    def _work() -> None:
        params = {"key": ctx.api_key}
        try:
            _, payload = http_json(
                ctx.session, endpoint, params=params, timeout=ctx.timeout
            )
        except ApiError as exc:
            if exc.status == 404:
                report.metrics["Verdict"] = "not scanned by Shodan"
                report.metrics["Open ports"] = "0"
                report.status = STATUS_OK
                report.error = "Shodan holds no scan record for this IP"
                return
            raise

        payload = payload or {}
        services = payload.get("data", []) or []
        ports = payload.get("ports", []) or sorted(
            {s.get("port") for s in services if isinstance(s.get("port"), int)}
        )
        products = sorted(
            {
                f"{s.get('product')} {s.get('version') or ''}".strip()
                for s in services
                if s.get("product")
            }
        )
        vulns = payload.get("vulns", {}) or {}
        ssl_services = [s for s in services if s.get("ssl")]

        report.metrics.update(
            {
                "Verdict": "internet-facing host",
                "Open ports": len(ports),
                "Port list": ", ".join(str(p) for p in ports[:15]) or "-",
                "Organisation": payload.get("org") or payload.get("isp") or "-",
                "ASN": payload.get("asn") or "-",
                "Hostnames": ", ".join((payload.get("hostnames") or [])[:3]) or "-",
                "Products": ", ".join(products[:5]) or "-",
                "CVEs": len(vulns),
                "TLS services": len(ssl_services),
                "Last scan": (payload.get("last_update") or "-")[:19],
            }
        )
        report.raw = {
            "ip": payload.get("ip_str"),
            "ports": ports,
            "products": products[:10],
            "vulns": list(vulns)[:10],
            "services": [
                {
                    "port": s.get("port"),
                    "transport": s.get("transport"),
                    "product": s.get("product"),
                    "version": s.get("version"),
                    "banner": (s.get("data") or "")[:300],
                }
                for s in services[:8]
            ],
        }
        report.status = STATUS_OK

    return run_timed(report, _work)

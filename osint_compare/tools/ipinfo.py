"""IPinfo API - geolocation, ASN/hosting attribution and hostname context.

Endpoint : GET https://ipinfo.io/{ip}/json?token=<IPINFO_TOKEN>
Auth     : query parameter `token` (free tier: 50k lookups/month)
Docs     : https://ipinfo.io/developers
"""

from __future__ import annotations

from ..http import http_json
from ..model import STATUS_OK, ToolReport
from ._common import ToolContext, new_report, run_timed

LABEL = "IPinfo"
BASE = "https://ipinfo.io"


def query(ctx: ToolContext, domain: str, ip: str | None) -> ToolReport:
    endpoint = f"{BASE}/{ip or domain}/json"
    report = new_report("ipinfo", LABEL, endpoint, ctx.has_key)

    def _work() -> None:
        _, payload = http_json(
            ctx.session,
            endpoint,
            params={"token": ctx.api_key},
            timeout=ctx.timeout,
        )
        payload = payload or {}
        loc = payload.get("loc", "") or ""
        lat, _, lon = loc.partition(",")
        org = payload.get("org", "")

        report.metrics.update(
            {
                "Verdict": "geolocated",
                "Hostname": payload.get("hostname") or "-",
                "City / region": f"{payload.get('city') or '-'} / {payload.get('region') or '-'}",
                "Country": payload.get("country") or "-",
                "Coordinates": loc or "-",
                "ASN / org": org or "-",
                "Timezone": payload.get("timezone") or "-",
                "Postal": payload.get("postal") or "-",
                "Anycast": bool(payload.get("anycast")),
            }
        )
        report.raw = {
            "ip": payload.get("ip"),
            "location": {"lat": lat, "lon": lon},
            "org": org,
            "hostname": payload.get("hostname"),
            "raw_keys": sorted(payload),
        }
        report.status = STATUS_OK

    return run_timed(report, _work)

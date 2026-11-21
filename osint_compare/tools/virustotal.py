"""VirusTotal API v3 - multi-vendor detections for a domain and its IP.

Endpoint : GET https://www.virustotal.com/api/v3/domains/{domain}
           GET https://www.virustotal.com/api/v3/ip_addresses/{ip}
Auth     : header `x-apikey: <VT_API_KEY>` (free community key is enough)
Docs     : https://docs.virustotal.com/reference/domain-info
"""

from __future__ import annotations

from ..http import ApiError, http_json
from ..model import STATUS_OK, ToolReport
from ._common import ToolContext, new_report, run_timed

LABEL = "VirusTotal"
BASE = "https://www.virustotal.com/api/v3"


def _trim(vt_object: dict) -> dict:
    attrs = vt_object.get("attributes", {}) if isinstance(vt_object, dict) else {}
    keep = (
        "last_analysis_stats",
        "last_analysis_date",
        "reputation",
        "total_votes",
        "categories",
        "registrar",
        "creation_date",
        "last_modification_date",
        "whois",
        "popularity_ranks",
    )
    trimmed = {k: attrs[k] for k in keep if k in attrs}
    trimmed["id"] = vt_object.get("id")
    trimmed["type"] = vt_object.get("type")
    return trimmed


def query(ctx: ToolContext, domain: str, ip: str | None) -> ToolReport:
    endpoint = f"{BASE}/domains/{domain}"
    report = new_report("virustotal", LABEL, endpoint, ctx.has_key)

    def _work() -> None:
        headers = {"x-apikey": ctx.api_key}
        try:
            _, payload = http_json(ctx.session, endpoint, headers=headers, timeout=ctx.timeout)
        except ApiError as exc:
            if exc.status == 404:
                report.metrics["Verdict"] = "not in dataset"
                report.metrics["Malicious / engines"] = "0 / 0"
                report.status = STATUS_OK
                report.error = "VirusTotal has never seen this domain (not necessarily safe)"
                return
            raise

        data = payload.get("data", {}) if isinstance(payload, dict) else {}
        stats = (data.get("attributes") or {}).get("last_analysis_stats", {}) or {}
        malicious = int(stats.get("malicious", 0))
        suspicious = int(stats.get("suspicious", 0))
        harmless = int(stats.get("harmless", 0))
        undetected = int(stats.get("undetected", 0))
        engines = malicious + suspicious + harmless + undetected

        if malicious >= 2:
            verdict = "malicious"
        elif malicious or suspicious:
            verdict = "suspicious"
        elif engines:
            verdict = "clean"
        else:
            verdict = "no analysis"

        votes = (data.get("attributes") or {}).get("total_votes", {}) or {}
        categories = (data.get("attributes") or {}).get("categories", {}) or {}

        report.metrics.update(
            {
                "Verdict": verdict,
                "Malicious / engines": f"{malicious} / {engines}",
                "Suspicious engines": suspicious,
                "Community votes": f"+{votes.get('harmless', 0)} / -{votes.get('malicious', 0)}",
                "Categories": ", ".join(sorted(set(categories.values())))[:120] or "-",
                "Registrar": ((data.get("attributes") or {}).get("registrar") or "-"),
            }
        )
        report.raw = {"domain": _trim(data), "ip": None}

        if ip:
            try:
                _, ip_payload = http_json(
                    ctx.session, f"{BASE}/ip_addresses/{ip}", headers=headers, timeout=ctx.timeout
                )
                ip_data = ip_payload.get("data", {}) if isinstance(ip_payload, dict) else {}
                ip_stats = (ip_data.get("attributes") or {}).get("last_analysis_stats", {}) or {}
                report.metrics["IP malicious / engines"] = (
                    f"{ip_stats.get('malicious', 0)} / "
                    f"{sum(int(v) for v in ip_stats.values() if isinstance(v, int))}"
                )
                report.raw["ip"] = _trim(ip_data)
            except ApiError as exc:
                report.metrics["IP malicious / engines"] = f"n/a ({exc.status})"

        report.status = STATUS_OK

    return run_timed(report, _work)

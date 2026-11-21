"""Captured provider payloads used by `--demo` mode.

Demo mode exists so the full pipeline (query -> normalise -> table -> .xlsx) can
be exercised and graded without spending paid API quota or shipping keys. It is
*not* a substitute for real API calls: the transport is faked, and every demo
row is labelled as such in the workbook so results cannot be mistaken for live
intelligence.

Payload shapes mirror the live API responses documented by each vendor.
"""

from __future__ import annotations

import json
from typing import Any

DOMAIN = "wikipedia.org"
IP = "208.80.153.224"

VIRUSTOTAL_DOMAIN = {
    "data": {
        "id": DOMAIN,
        "type": "domain",
        "attributes": {
            "last_analysis_stats": {
                "harmless": 72,
                "malicious": 0,
                "suspicious": 1,
                "undetected": 22,
                "timeout": 0,
            },
            "last_analysis_date": 1763712000,
            "reputation": 412,
            "total_votes": {"harmless": 118, "malicious": 3},
            "categories": {
                "BitDefender": "reference",
                "Comodo Valkeu": "reference",
                "Forcepoint ThreatSeeker": "reference",
            },
            "registrar": "MarkMonitor Inc.",
            "creation_date": 979488000,
            "popularity_ranks": {"Alexa": {"rank": 12, "timestamp": 1763712000}},
        },
    }
}

VIRUSTOTAL_IP = {
    "data": {
        "id": IP,
        "type": "ip_address",
        "attributes": {
            "last_analysis_stats": {
                "harmless": 61,
                "malicious": 0,
                "suspicious": 0,
                "undetected": 14,
            },
            "reputation": 88,
            "total_votes": {"harmless": 40, "malicious": 0},
            "country": "US",
            "as_owner": "WIKIMEDIA",
        },
    }
}

SECURITYTRAILS_DOMAIN = {
    "hostname": DOMAIN,
    "endpoint": "/v1/domain/wikipedia.org",
    "current_dns": {
        "a": {
            "first_seen": "2024-01-10",
            "values": [
                {"ip": "208.80.153.224", "ipv": 4},
                {"ip": "208.80.154.224", "ipv": 4},
                {"ip": "198.35.26.96", "ipv": 4},
            ],
        },
        "mx": {
            "values": [
                {"hostname": "mx1001.wikimedia.org", "priority": 10},
                {"hostname": "mx2001.wikimedia.org", "priority": 50},
            ]
        },
        "ns": {
            "values": [
                {"hostname": "ns0.wikimedia.org"},
                {"hostname": "ns1.wikimedia.org"},
                {"hostname": "ns2.wikimedia.org"},
            ]
        },
        "txt": {"values": [{"value": "v=spf1 include:_spf.wikimedia.org ~all"}]},
    },
    "whois": {
        "createdDate": "2001-01-13",
        "expiresDate": "2027-01-13",
        "updatedDate": "2026-01-12",
        "registrant": {"org": "Wikimedia Foundation, Inc.", "country": "US"},
        "registrarName": "MarkMonitor Inc.",
        "status": ["clientDeleteProhibited", "clientTransferProhibited"],
    },
    "alexa": {"rank": 12},
    "subdomain_count": 61,
}

SECURITYTRAILS_SUBDOMAINS = {
    "endpoint": "/v1/domain/wikipedia.org/subdomains",
    "subdomains": [
        "en", "de", "fr", "es", "ja", "ru", "zh", "www", "commons", "meta",
        "api", "upload", "stats", "donate", "foundation", "shop", "mail",
        "lists", "gerrit", "phabricator",
    ],
}

SECURITYTRAILS_HISTORY = {
    "endpoint": "/v1/history/wikipedia.org/dns/a",
    "records": [
        {"first_seen": "2025-06-01", "last_seen": "2026-11-01",
         "values": [{"ip": "208.80.153.224"}, {"ip": "208.80.154.224"}]},
        {"first_seen": "2024-02-11", "last_seen": "2025-05-30",
         "values": [{"ip": "198.35.26.96"}]},
        {"first_seen": "2022-03-04", "last_seen": "2024-02-10",
         "values": [{"ip": "103.102.166.224"}]},
    ],
}

ABUSEIPDB_CHECK = {
    "data": {
        "ipAddress": IP,
        "isPublic": True,
        "ipVersion": 4,
        "isWhitelisted": True,
        "abuseConfidenceScore": 0,
        "countryCode": "US",
        "usageType": "Data Center/Web Hosting/Transit",
        "isp": "Wikimedia Foundation Inc.",
        "domain": DOMAIN,
        "hostnames": ["text-lb.codfw.wikimedia.org"],
        "totalReports": 0,
        "numDistinctUsers": 0,
        "lastReportedAt": None,
        "reports": [],
    }
}

SHODAN_HOST = {
    "ip_str": IP,
    "ip": 3495129312,
    "ports": [80, 443],
    "hostnames": ["text-lb.codfw.wikimedia.org", DOMAIN],
    "domains": [DOMAIN],
    "org": "Wikimedia Foundation Inc.",
    "isp": "Wikimedia Foundation Inc.",
    "asn": "AS14907",
    "country_name": "United States",
    "city": "Carrollton",
    "os": None,
    "last_update": "2026-11-19T10:34:37.275352",
    "vulns": {},
    "tags": [],
    "data": [
        {
            "port": 80,
            "transport": "tcp",
            "product": "nginx",
            "version": "1.25.3",
            "data": "HTTP/1.1 301 Moved Permanently\r\nServer: nginx\r\nLocation: https://wikipedia.org/\r\n",
        },
        {
            "port": 443,
            "transport": "tcp",
            "product": "nginx",
            "version": "1.25.3",
            "ssl": {
                "cert": {
                    "issuer": {"CN": "Let's Encrypt", "O": "Let's Encrypt"},
                    "subject": {"CN": DOMAIN},
                    "expires": "20270126082932Z",
                },
                "versions": ["TLSv1.2", "TLSv1.3"],
            },
            "data": "HTTP/1.1 200 OK\r\nServer: nginx\r\nContent-Type: text/html\r\n",
        },
    ],
}

IPINFO_IP = {
    "ip": IP,
    "hostname": "text-lb.codfw.wikimedia.org",
    "city": "Carrollton",
    "region": "Texas",
    "country": "US",
    "loc": "32.9537,-96.8903",
    "org": "AS14907 Wikimedia Foundation Inc.",
    "postal": "75006",
    "timezone": "America/Chicago",
    "readme": "https://ipinfo.io/missingauth",
}


def _route(url: str) -> tuple[int, Any]:
    """Map a request URL to the captured fixture payload."""
    url = url.lower()
    if "virustotal.com" in url and "/ip_addresses/" in url:
        return 200, VIRUSTOTAL_IP
    if "virustotal.com" in url and "/domains/" in url:
        return 200, VIRUSTOTAL_DOMAIN
    if "securitytrails.com" in url and "/subdomains" in url:
        return 200, SECURITYTRAILS_SUBDOMAINS
    if "securitytrails.com" in url and "/history/" in url:
        return 200, SECURITYTRAILS_HISTORY
    if "securitytrails.com" in url:
        return 200, SECURITYTRAILS_DOMAIN
    if "abuseipdb.com" in url:
        return 200, ABUSEIPDB_CHECK
    if "shodan.io" in url:
        return 200, SHODAN_HOST
    if "ipinfo.io" in url:
        return 200, IPINFO_IP
    return 404, {"error": f"no demo fixture for {url}"}


class FixtureResponse:
    """Minimal stand-in for `requests.Response` (only what the tools touch)."""

    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload) if not isinstance(payload, str) else payload
        self.reason = "OK" if status_code == 200 else "Fixture miss"

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 400

    def json(self) -> Any:
        if isinstance(self._payload, str):
            return json.loads(self._payload)
        return self._payload


class DemoSession:
    """Duck-typed replacement for requests.Session used by `--demo`."""

    demo = True

    def __init__(self) -> None:
        self.calls: list[str] = []

    def get(self, url: str, **_kwargs: Any) -> FixtureResponse:
        self.calls.append(url)
        status, payload = _route(url)
        return FixtureResponse(status, payload)

    def mount(self, *_args: Any, **_kwargs: Any) -> None:  # parity with requests.Session
        return None

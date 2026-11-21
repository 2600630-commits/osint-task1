"""Target preparation: normalise user input and resolve the target to an IPv4.

Shared groundwork (not one of the five keyed tools): DNS resolution is needed
because Shodan, AbuseIPDB and IPinfo are IP-centric while VirusTotal and
SecurityTrails start from the domain.
"""

from __future__ import annotations

import socket
from dataclasses import dataclass, field
from urllib.parse import urlsplit


def normalise_target(raw: str) -> str:
    """Accept 'example.com', 'www.example.com/path' or a full URL; return the host."""
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("empty target")
    if "://" not in raw:
        raw = "http://" + raw
    host = urlsplit(raw).hostname or ""
    host = host.strip().strip(".").lower()
    if not host or "." not in host:
        raise ValueError(f"'{raw}' does not look like a public domain name")
    return host


@dataclass
class Target:
    domain: str
    url: str
    ip: str | None = None
    all_ips: list[str] = field(default_factory=list)
    resolve_error: str = ""

    @classmethod
    def build(cls, raw: str) -> "Target":
        domain = normalise_target(raw)
        target = cls(domain=domain, url=f"https://{domain}")
        try:
            infos = socket.getaddrinfo(domain, 443, socket.AF_INET, socket.SOCK_STREAM)
            seen: list[str] = []
            for info in infos:
                ip = info[4][0]
                if ip not in seen:
                    seen.append(ip)
            target.all_ips = seen
            target.ip = seen[0] if seen else None
            if not seen:
                target.resolve_error = "no IPv4 address returned"
        except socket.gaierror as exc:
            target.resolve_error = f"DNS resolution failed: {exc}"
        return target

    def __str__(self) -> str:
        return f"{self.domain} -> {self.ip or 'unresolved'}"

"""Tool wrappers. Each module exposes `query(ctx, domain, ip) -> ToolReport`."""

from . import virustotal, securitytrails, abuseipdb, shodan, ipinfo

REGISTRY = {
    "virustotal": virustotal,
    "securitytrails": securitytrails,
    "abuseipdb": abuseipdb,
    "shodan": shodan,
    "ipinfo": ipinfo,
}

__all__ = ["REGISTRY", "virustotal", "securitytrails", "abuseipdb", "shodan", "ipinfo"]

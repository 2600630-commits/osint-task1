"""API key loading.

Keys are read from the process environment first, then from a local `.env`
file (simple KEY=VALUE parser, no external dependency). Each tool is optional:
a missing key produces a `no_key` row in the report instead of aborting the run,
which keeps the comparison table complete and auditable.
"""

from __future__ import annotations

import os
from pathlib import Path

# tool -> (environment variable, human label, where to obtain the key)
TOOL_KEYS = {
    "virustotal": (
        "VT_API_KEY",
        "VirusTotal",
        "https://www.virustotal.com/gui/my-apikey",
    ),
    "securitytrails": (
        "SECURITYTRAILS_API_KEY",
        "SecurityTrails",
        "https://securitytrails.com/app/account/credentials",
    ),
    "abuseipdb": (
        "ABUSEIPDB_API_KEY",
        "AbuseIPDB",
        "https://www.abuseipdb.com/account/api",
    ),
    "shodan": (
        "SHODAN_API_KEY",
        "Shodan",
        "https://account.shodan.io/",
    ),
    "ipinfo": (
        "IPINFO_TOKEN",
        "IPinfo",
        "https://ipinfo.io/account/token",
    ),
}

DEFAULT_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip().removeprefix("export ").strip()
        value = value.strip().strip("'\"")
        if key:
            values[key] = value
    return values


class KeyStore:
    """Resolves API keys for the five tools and remembers where they came from."""

    def __init__(self, env_file: Path | None = DEFAULT_ENV_FILE) -> None:
        self._file_values = _parse_env_file(env_file) if env_file else {}
        self._sources: dict[str, str] = {}

    def get(self, tool: str) -> str | None:
        env_name, _, _ = TOOL_KEYS[tool]
        value = os.environ.get(env_name)
        if value:
            self._sources[tool] = f"env:{env_name}"
            return value.strip()
        value = self._file_values.get(env_name)
        if value:
            self._sources[tool] = f"file:{env_name}"
            return value.strip()
        self._sources[tool] = "missing"
        return None

    def has(self, tool: str) -> bool:
        return bool(self.get(tool))

    def source(self, tool: str) -> str:
        """Where the key came from - 'missing', 'env:VT_API_KEY', 'file:...'."""
        if tool not in self._sources:
            self.get(tool)
        return self._sources[tool]

    def available(self) -> list[str]:
        return [tool for tool in TOOL_KEYS if self.has(tool)]

    def missing(self) -> list[str]:
        return [tool for tool in TOOL_KEYS if not self.has(tool)]


def key_help_lines(store: KeyStore) -> list[str]:
    """Human-readable key status, used in the CLI banner and the workbook."""
    lines = []
    for tool, (env_name, label, url) in TOOL_KEYS.items():
        state = "set" if store.has(tool) else "MISSING"
        lines.append(f"{label:<14} {state:<8} {store.source(tool):<28} {url}")
    return lines

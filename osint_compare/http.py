"""Shared HTTP plumbing: one session, retries, rate-limit back-off, size caps.

Every tool module uses `http_json` / `http_get` so timeouts, retries and error
messages are handled consistently and one slow API cannot hang the whole run.
"""

from __future__ import annotations

import json
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_TIMEOUT = 25
USER_AGENT = "osint-task1-compare/1.0 (educational OSINT lab)"


def build_session(retries: int = 2) -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    retry = Retry(
        total=retries,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_maxsize=8)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class ApiError(RuntimeError):
    """Non-2xx response raised by a tool wrapper."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.message = message


AUTH_MESSAGES = {
    401: "authentication failed - API key missing, wrong or revoked",
    403: "access forbidden - key lacks permission or quota exhausted",
    404: "not found - target unknown to this provider",
    429: "rate limit reached for this API key",
}


def _raise_for_status(response: requests.Response) -> None:
    if response.ok:
        return
    body = (response.text or "").strip().replace("\n", " ")
    snippet = body[:220] if body else response.reason
    hint = AUTH_MESSAGES.get(response.status_code)
    if hint and response.status_code in AUTH_MESSAGES:
        snippet = f"{hint} | {snippet}"
    raise ApiError(response.status_code, snippet)


def http_get(
    session: requests.Session,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    allow_status: tuple[int, ...] = (),
) -> requests.Response:
    response = session.get(url, params=params, headers=headers, timeout=timeout)
    if response.status_code in allow_status:
        return response
    _raise_for_status(response)
    return response


def http_json(
    session: requests.Session,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    allow_status: tuple[int, ...] = (),
) -> tuple[int, Any]:
    """Return (status_code, parsed_json_or_text)."""
    response = http_get(
        session, url, params=params, headers=headers, timeout=timeout, allow_status=allow_status
    )
    try:
        return response.status_code, response.json()
    except (json.JSONDecodeError, ValueError):
        return response.status_code, (response.text or "")[:4000]


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

# OSINT Task 1 — Five-Tool Website Intelligence Comparison

Assignment: *"Develop a script or program that uses the API keys of five OSINT tools
mentioned in OSINT Lecture 1 to analyze any target website. Compare the results
obtained from all five tools in a table and export them to an Excel (.xlsx) file."*

This project queries **five API-key OSINT services introduced in the lecture**
(section 1.2.1 *Online platforms* and 1.2.3 *Use of APIs*), normalises their
answers into one schema, renders a comparison table, and writes a formatted
Excel workbook.

| # | Tool | What it contributes | API used | Key variable |
|---|------|---------------------|----------|--------------|
| 1 | **VirusTotal** | Multi-vendor detections, reputation, categories, votes (domain + IP) | `GET /api/v3/domains/{domain}`, `/api/v3/ip_addresses/{ip}` | `VT_API_KEY` |
| 2 | **SecurityTrails** | Current DNS (A/MX/NS/TXT), WHOIS summary, subdomain inventory, A-record history | `GET /v1/domain/{domain}`, `/subdomains`, `/history/{domain}/dns/a` | `SECURITYTRAILS_API_KEY` |
| 3 | **AbuseIPDB** | IP abuse confidence score, report volume, usage type, whitelist state | `GET /api/v2/check` | `ABUSEIPDB_API_KEY` |
| 4 | **Shodan** | Internet-facing ports, services/products, TLS services, CVEs, last scan | `GET /shodan/host/{ip}` | `SHODAN_API_KEY` |
| 5 | **IPinfo** | Geolocation, ASN/org attribution, hostname, timezone, anycast flag | `GET /{ip}/json` | `IPINFO_TOKEN` |

All five names appear in Lecture 1; the lecture also names the API-key pattern
("with an API key, they can write a Python script to query VirusTotal's API…")
and specifies VirusTotal, SecurityTrails and AbuseIPDB as the API trio.

---

## 1. Quick start

```bash
git clone <this-repo> osint-5tool-compare && cd osint-5tool-compare
python3 -m pip install -r requirements.txt

cp .env.example .env          # then paste your five keys into .env
python3 run_osint_compare.py example.com --xlsx output/example.xlsx
```

Output:

```
output/example.xlsx           # the required five-tool comparison table
```

Useful variants:

```bash
python3 run_osint_compare.py --keys                       # are my keys visible?
python3 run_osint_compare.py https://www.wikipedia.org \  # full URL accepted
        --tools virustotal,shodan --json output/raw.json
python3 run_osint_compare.py example.com --demo \         # no keys needed
        --xlsx output/demo.xlsx
python3 -m unittest discover tests -v                     # offline test suite
```

Package-style invocation also works: `python3 -m osint_compare.cli example.com`.

## 2. Getting the five keys (all have a free tier)

| Tool | Where to generate | Free tier |
|------|-------------------|-----------|
| VirusTotal | https://www.virustotal.com/gui/my-apikey | 4 req/min, 500/day |
| SecurityTrails | https://securitytrails.com/app/account/credentials | 50 queries/month |
| AbuseIPDB | https://www.abuseipdb.com/account/api | 1 000 checks/day |
| Shodan | https://account.shodan.io/ | limited endpoints (host lookup available) |
| IPinfo | https://ipinfo.io/account/token | 50 000 lookups/month |

Keys are read from environment variables first, then from `.env`:

```
VT_API_KEY=...
SECURITYTRAILS_API_KEY=...
ABUSEIPDB_API_KEY=...
SHODAN_API_KEY=...
IPINFO_TOKEN=...
```

`.env` is git-ignored; `.env.example` is the committed template. A missing key
does **not** crash the run — that tool's row is marked `no_key` with the exact
environment variable to set, so the table is always complete.

## 3. What the Excel workbook contains

`export_workbook()` writes six sheets with frozen panes, autofilters and
status colour-coding (green = ok, amber = no key, red = error):

| Sheet | Purpose |
|-------|---------|
| **Summary** | Run mode, target, resolved IPs, query window, key availability, per-tool verdicts, key provenance |
| **Tool Comparison** | **The required table** — one row per tool, union of all metric columns |
| **Metric Matrix** | Transposed view: one row per metric, one column per tool (direct side-by-side) |
| **Coverage** | X/– map showing which tool answers which metric, plus per-tool coverage count |
| **Raw JSON** | Trimmed provider payloads for verification/audit |
| **README** | Sheet guide, verdict rules, caveats, ethics statement |

Row shape of the comparison table (`Tool Comparison`):

| Tool | Status | Verdict | Malicious / engines | … | Abuse confidence | … | Open ports | … | Coordinates | Latency (ms) | Checked at (UTC) | Endpoint | Error |
|------|--------|---------|---------------------|----|------------------|---|-----------|----|-------------|--------------|------------------|----------|-------|

## 4. How the results are normalised

Each wrapper returns a `ToolReport` with `metrics` (fixed per tool) plus the
trimmed raw payload, so mixed API answers become comparable:

| Metric group | Source | Notes |
|--------------|--------|-------|
| Verdict | all five | `malicious`/`suspicious`/`clean`/`no analysis` (VT), `registered domain` (ST), `high|moderate|low risk`/`no reports` (AbuseIPDB), `internet-facing host`/`not scanned` (Shodan), `geolocated` (IPinfo) |
| Threat | VirusTotal, AbuseIPDB | detections per engine, suspicious engines, community votes, abuse confidence %, 90-day reports |
| Infrastructure | SecurityTrails, Shodan | A/MX/NS records, subdomain count, A-record history entries, open ports, products, TLS services, CVEs |
| Ownership / hosting | SecurityTrails, Shodan, IPinfo, VirusTotal | registrar, WHOIS org, ASN/org, ISP, city/region/country, coordinates, timezone |
| Provenance | all five | endpoint, status, latency, `checked_at` (UTC), error text |

Verdict rules (documented in the workbook too):

* VirusTotal — ≥2 malicious engines → `malicious`; 1 → `suspicious`; else `clean`; no data → `no analysis`.
* AbuseIPDB — confidence ≥75 % → `high risk`; ≥25 % → `moderate risk`; reports > 0 → `low risk`; else `no reports`.

Target handling: the CLI accepts a bare domain, `domain.tld/path`, or a full URL,
extracts the host, then resolves the first IPv4 via `socket.getaddrinfo`. All
five tools run concurrently in a thread pool; one provider's failure or rate
limit is isolated to its own row.

## 5. Repository layout

```
osint-5tool-compare/
├── run_osint_compare.py          # dependency-free launcher
├── requirements.txt              # requests, openpyxl
├── .env.example                  # key template (real .env is git-ignored)
├── osint_compare/
│   ├── cli.py                    # argparse entry point, console output
│   ├── compare.py                # concurrent runner + comparison tables
│   ├── config.py                 # key resolution (env → .env), key catalogue
│   ├── http.py                   # session, retries, rate-limit handling, errors
│   ├── model.py                  # ToolReport / Timer / status constants
│   ├── target.py                 # input normalisation + DNS resolution
│   ├── report.py                 # styled .xlsx (+ companion .json) export
│   ├── demo.py                   # captured fixtures for `--demo`
│   └── tools/                    # one module per provider
│       ├── virustotal.py  ├── securitytrails.py  ├── abuseipdb.py
│       ├── shodan.py      ├── ipinfo.py          └── _common.py
├── tests/test_osint_compare.py   # 17 offline tests
└── output/                       # generated workbooks (git-ignored)
```

## 6. `--demo` mode (why it exists)

The demo transport replays captured provider responses through the **real**
normalisation and export code, so the pipeline and workbook can be validated
without keys or API quota. Demo rows are labelled
`Run mode: demo (captured fixtures, no live API calls)` in the Summary sheet and
the console prints `DEMO` — they must never be presented as live findings.
Run the real thing with your own keys by omitting `--demo`.

## 7. Ethics and limits

* Passive OSINT only: public metadata APIs. No scanning, no login, no
  exploitation, nothing that touches the target directly.
* Results are point-in-time; free tiers may hide fields (e.g. SecurityTrails
  registrant data on low-tier plans returns `redacted/-`).
* A `clean` verdict is *absence of evidence*, not proof of safety. Cross-check
  before acting on any single provider.

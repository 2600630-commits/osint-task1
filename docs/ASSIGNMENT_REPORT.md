# OSINT Task 1 — Report Draft

> **Status of this document.** Sections 1–3 and 6 are complete and describe the
> delivered program. Section 4 holds the *comparison of actual results*; it is
> filled by running the program with your five API keys. Section 4 currently
> contains the pipeline-validation run (`--demo`, captured fixtures), which is
> explicitly labelled as such and must be replaced by a live run before
> submission. Nothing in this file claims to be live intelligence.

---

## 1. Objective

Use the API keys of five OSINT tools introduced in *OSINT Lecture 1* to analyse
one target website, compare the five answers in a single table, and export that
table to an `.xlsx` file.

## 2. Tools selected and justification

The lecture divides domain/IP OSINT into UI platforms, CLI tools and APIs
(section 1.2), then presents an API workflow around *VirusTotal,
SecurityTrails and AbuseIPDB* (section 1.2.3). Five API-key providers named in
the lecture were chosen so that each contributes a different intelligence layer
and the comparison is not five redundant reputation checks:

| Tool | Lecture reference | Intelligence layer | Endpoints queried |
|------|-------------------|--------------------|-------------------|
| VirusTotal | §1.2.1, §1.2.3, Fig. 1.20 | Multi-engine malware/phishing detections, community votes, categories | `/api/v3/domains/{d}`, `/api/v3/ip_addresses/{ip}` |
| SecurityTrails | §1.2.1, Fig. 1.1, §1.3 | Current DNS, WHOIS summary, subdomain inventory, A-record history | `/v1/domain/{d}`, `/subdomains`, `/history/{d}/dns/a` |
| AbuseIPDB | §1.2.2 ("AbuseDB"), Table 1.1 | IP abuse reputation and report volume | `/api/v2/check` |
| Shodan | §1.2.1, Fig. 1.3 | Exposed ports, services/products, TLS, CVEs | `/shodan/host/{ip}` |
| IPinfo | §1.2.4 (geolocation step) | Geolocation, ASN/hosting attribution, anycast flag | `/{ip}/json` |

Design consequence: VirusTotal and SecurityTrails are domain-centric,
AbuseIPDB/Shodan/IPinfo are IP-centric. The program therefore resolves the
domain to an IPv4 address first and passes both forms to every wrapper.

## 3. Methodology

1. **Normalise input** — accept `example.com`, `example.com/path` or a full URL;
   extract the host; resolve the first IPv4 (`socket.getaddrinfo`).
2. **Resolve keys** — environment variable, else `.env`; record provenance
   (`env:`, `file:`, `missing`). A missing key yields a `no_key` row, never a
   crash, so the table stays complete.
3. **Query concurrently** — one `requests.Session` with retry/back-off shared by
   a 5-way thread pool; per-tool exceptions are captured as `error` rows.
4. **Normalise** — each provider payload is reduced to a fixed `metrics` dict
   (Verdict, threat, infrastructure, ownership, provenance) plus trimmed raw JSON.
5. **Compare** — two renderings: rows = tools (required table) and
   rows = metrics (side-by-side matrix).
6. **Export** — styled `.xlsx` with six sheets; optional companion `.json`
   for reproducibility.

Commands used:

```bash
python3 run_osint_compare.py <target> --xlsx output/<target>_comparison.xlsx \
        --json output/<target>_comparison.json
```

## 4. Comparison of results

**To be produced with the five keys.** Run the command above and paste or refer
to the workbook. The table below shows the column layout that the program fills,
using the pipeline-validation run against captured fixtures for
`wikipedia.org` (demo mode — not a live finding).

| Tool | Status | Verdict | Key differentiators seen | Limitations |
|------|--------|---------|--------------------------|-------------|
| VirusTotal | ok | suspicious (1 suspicious engine, 0 malicious of 95) | Only tool giving per-engine detections + community votes | Domain/IP only; no live content; free tier 4 req/min |
| SecurityTrails | ok | registered domain | Richest infrastructure view: 3 A records, 2 MX, 3 NS, subdomain inventory, A-record history, WHOIS org/creation date | Registrant contact data needs a paid tier; 50 queries/month free |
| AbuseIPDB | ok | no reports (0 % confidence, 0 reports/90 d) | Fastest single-purpose reputation signal, includes usage type + ISP | IP-only; absence of reports ≠ safe |
| Shodan | ok | internet-facing host (2 ports, nginx 1.25.3, 1 TLS service, 0 CVEs) | Only tool revealing exposed services, versions, TLS and scan freshness | IP-only; requires a paid-capable key for some endpoints; data can be stale |
| IPinfo | ok | geolocated (Carrollton/Texas, AS14907 Wikimedia Foundation) | Only tool with coordinates/timezone/anycast — maps hosting and CDN behaviour | No security judgement at all |

Cross-tool corroboration to write up after the live run:

* Do Shodan's `org`/`asn` and IPinfo's `org` agree on the hosting provider?
* Does the country reported by AbuseIPDB match IPinfo's geolocation?
* Does VirusTotal's registrar match SecurityTrails' WHOIS org (ownership pivot)?
* Does Shodan's TLS certificate CN/SAN family match SecurityTrails' subdomains?
* Are there AbuseIPDB reports on an IP that VirusTotal calls clean (or vice versa)?

That last group of questions is the actual analytical value of the exercise:
no single provider is authoritative, and disagreement between providers is a
finding in itself.

## 5. Deliverables

| Item | Location |
|------|----------|
| Program | `run_osint_compare.py`, package `osint_compare/` |
| Key template / setup | `.env.example`, `README.md` §2 |
| Excel export | `output/<target>_comparison.xlsx` (6 sheets) |
| Machine-readable export | `output/<target>_comparison.json` |
| Tests | `tests/test_osint_compare.py` (17 offline tests) |
| Repository link | *add after pushing — not uploaded by the assistant* |

## 6. Ethics, limits and lessons learned

* All queries are passive: provider APIs only — no packets sent to the target,
  no authentication attempts, no scanning.
* Verdicts are point-in-time; free tiers redact fields and rate-limit aggressively.
* `clean`/`no reports` means *absence of evidence*, not safety.
* Practical lessons: domain-vs-IP tool asymmetry requires a resolution step;
  keys must never be hard-coded (hence `.env` + git-ignore); retries and
  per-tool isolation are needed because free-tier APIs return 429/502 under
  concurrent load.

"""OSINT Task 1 - five-tool website intelligence comparison.

Queries five API-key based OSINT services introduced in "OSINT Lecture 1"
(section 1.2.1 "Online platforms" and 1.2.3 "Use of APIs"):

    1. VirusTotal      - threat-intelligence aggregation / detections
    2. SecurityTrails  - DNS, WHOIS history and subdomain infrastructure
    3. AbuseIPDB       - IP reputation and abuse reports
    4. Shodan          - exposed ports, services and banners
    5. IPinfo          - geolocation, ASN and hosting attribution

Every tool returns a normalised `ToolReport`, which `compare.py` lays out as a
comparison table and `report.py` exports to a formatted Excel workbook.
"""

__version__ = "1.0.0"

TOOL_ORDER = ("virustotal", "securitytrails", "abuseipdb", "shodan", "ipinfo")

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / "AGENT-HUB/tmp-projeler-gtm-delay.html").read_text(encoding="utf-8", errors="replace")

checks = {
    "ledajans_gtm_delayed_loader": "ledajansGtmLoaded" in html and "loadGtm" in html,
    "inline_gtm_immediate": bool(
        re.search(
            r"<script>\s*\(function\(w,d,s,l,i\)\{.*googletagmanager\.com/gtm\.js",
            html,
            re.I | re.S,
        )
    ),
    "gtm_preconnect": bool(re.search(r'rel=["\']preconnect["\'][^>]+googletagmanager', html, re.I)),
    "gtm_dns_prefetch": "dns-prefetch" in html and "googletagmanager.com" in html,
    "gtm_js_in_head": bool(re.search(r'<script[^>]+src=["\'][^"\']*googletagmanager\.com/gtm\.js', html, re.I)),
    "contact-form-7-js": bool(re.search(r"contact-form-7[^\"']*\.js", html, re.I)),
    "chaty-js": bool(re.search(r"chaty[^\"']*\.js", html, re.I)),
}

print("HTML_GTM_CHECK")
for key, value in checks.items():
    print(f"{key}={value}")

lh_path = ROOT / "AGENT-HUB/lh-mobile-projeler-gtm-delay.json"
if lh_path.exists():
    d = json.loads(lh_path.read_text(encoding="utf-8"))
    a = d["audits"]
    print(
        "LH",
        "perf",
        int(d["categories"]["performance"]["score"] * 100),
        "lcp",
        round(a["largest-contentful-paint"]["numericValue"] / 1000, 2),
        "fcp",
        round(a["first-contentful-paint"]["numericValue"] / 1000, 2),
        "tbt",
        round(a["total-blocking-time"]["numericValue"]),
        "cls",
        round(a["cumulative-layout-shift"]["numericValue"], 4),
    )
    for item in a.get("lcp-breakdown-insight", {}).get("details", {}).get("items", []):
        if item.get("type") == "table":
            for row in item.get("items", []):
                print("breakdown", row.get("subpart"), round(row.get("duration", 0), 1))

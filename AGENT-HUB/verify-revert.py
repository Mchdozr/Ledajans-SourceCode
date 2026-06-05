import json
import re
import urllib.request
from pathlib import Path

req = urllib.request.Request(
    "https://ledajans.com/projeler/",
    headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"},
)
html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")

checks = {
    "preload_template": bool(re.search(r'rel=["\']preload["\'][^>]+template\.css', html, re.I)),
    "blocking_template": bool(re.search(r'rel=["\']stylesheet["\'][^>]+template\.css', html, re.I)),
    "preload_bootstrap": bool(re.search(r'rel=["\']preload["\'][^>]+bootstrap\.css', html, re.I)),
    "blocking_bootstrap": bool(re.search(r'rel=["\']stylesheet["\'][^>]+bootstrap\.css', html, re.I)),
    "gtm_delayed": "ledajansGtmLoaded" in html,
    "cf7_js": bool(re.search(r"contact-form-7[^\"']*\.js", html, re.I)),
    "chaty_js": bool(re.search(r"chaty[^\"']*\.js", html, re.I)),
}
print("HTML", checks)

root = Path(__file__).resolve().parents[1] / "AGENT-HUB"
for label, path in [
    ("gtm_en_iyi", "lh-mobile-projeler-gtm-delay-2.json"),
    ("theme_kotu", "lh-mobile-projeler-theme-css-2.json"),
    ("revert1", "lh-mobile-projeler-revert.json"),
    ("revert2", "lh-mobile-projeler-revert-2.json"),
]:
    d = json.load(open(root / path, encoding="utf-8"))
    a = d["audits"]
    print(
        label,
        int(d["categories"]["performance"]["score"] * 100),
        round(a["largest-contentful-paint"]["numericValue"] / 1000, 2),
        round(a["total-blocking-time"]["numericValue"]),
    )

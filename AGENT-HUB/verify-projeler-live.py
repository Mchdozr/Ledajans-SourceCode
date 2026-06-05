import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / "AGENT-HUB/tmp-projeler-verify.html").read_text(encoding="utf-8", errors="replace")

checks = {
    "contact-form-7-css": bool(re.search(r"contact-form-7[^\"']*\.css", html, re.I)),
    "contact-form-7-js": bool(re.search(r"contact-form-7[^\"']*\.js", html, re.I)),
    "chaty-css": bool(re.search(r"chaty[^\"']*\.css", html, re.I)),
    "chaty-js": bool(re.search(r"chaty[^\"']*\.js", html, re.I)),
    "widget-icon-list-css": "widget-icon-list.min.css" in html,
    "widget-icon-box-css": "widget-icon-box.min.css" in html,
    "widget-social-icons-css": "widget-social-icons.min.css" in html,
    "hero-scroll-bg": "background-attachment: scroll, scroll, scroll" in html,
    "hero-fixed-bg": "background-attachment: fixed, fixed, fixed" in html,
}

print("HTML_ASSET_CHECK")
for key, value in checks.items():
    print(f"{key}={value}")

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / "AGENT-HUB/tmp-projeler-theme-css.html").read_text(encoding="utf-8", errors="replace")

def css_mode(name):
    blocking = bool(
        re.search(
            rf'<link[^>]+rel=["\']stylesheet["\'][^>]+{re.escape(name)}',
            html,
            re.I,
        )
    )
    preload = bool(
        re.search(
            rf'<link[^>]+rel=["\']preload["\'][^>]+as=["\']style["\'][^>]+{re.escape(name)}',
            html,
            re.I,
        )
    )
    return {"blocking": blocking, "preload": preload}

print("THEME_CSS_CHECK")
for css in ("template.css", "bootstrap.css"):
    print(css, css_mode(css))

checks = {
    "gtm_delayed": "ledajansGtmLoaded" in html,
    "cf7_js": bool(re.search(r"contact-form-7[^\"']*\.js", html, re.I)),
    "chaty_js": bool(re.search(r"chaty[^\"']*\.js", html, re.I)),
}
for k, v in checks.items():
    print(k, v)

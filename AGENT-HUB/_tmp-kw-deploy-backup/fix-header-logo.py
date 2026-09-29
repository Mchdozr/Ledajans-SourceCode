from __future__ import annotations

import json
import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
env: dict[str, str] = {}
for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, _, v = line.partition("=")
    env[k.strip()] = v.strip().strip("\"'")
SITE = env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
AUTH = (env["WP_USERNAME"], env["WP_APP_PASSWORD"].replace(" ", ""))
H = {"User-Agent": "Mozilla/5.0 LEDAJANS-LOGOFIX", "Content-Type": "application/json"}

NEW_HEADER = "https://ledajans.com/wp-content/uploads/2026/09/ledajans-logo.webp"
FOOTER_PNG = "https://ledajans.com/wp-content/uploads/2022/12/LedajansLogo.png"

NEW_SCRIPTS = f"""
<script id="ledajans-logo-swap">
(function () {{
  var HEADER = {NEW_HEADER!r};
  var FOOTER = {FOOTER_PNG!r};
  var re = /LedajansLogo|ledajans-logo|leadajans-logo/i;
  function apply() {{
    document.querySelectorAll(".elementor-element-123bc72 .site-branding-logo img, .logo-mm img").forEach(function (img) {{
      if ((img.getAttribute("src") || "") !== HEADER) {{
        img.setAttribute("src", HEADER);
        img.setAttribute("data-src", HEADER);
      }}
    }});
    document.querySelectorAll("img.ledajans-footer-logo").forEach(function (img) {{
      img.setAttribute("src", FOOTER);
      img.setAttribute("data-src", FOOTER);
    }});
    document.querySelectorAll("img").forEach(function (img) {{
      if (img.classList.contains("ledajans-footer-logo") || img.closest(".ledajans-footer")) return;
      if (img.closest(".elementor-element-123bc72 .site-branding-logo, .logo-mm")) return;
      var s = img.getAttribute("src") || "";
      var hit = re.test(s) || img.closest(".gsc-logo");
      if (hit && s !== HEADER) {{
        img.setAttribute("src", HEADER);
        img.setAttribute("data-src", HEADER);
      }}
    }});
  }}
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", apply);
  else apply();
}})();
</script>
"""


def main() -> None:
    r = requests.get(f"{SITE}/wp-json/wp/v2/elementor_snippet/5026", auth=AUTH, headers=H, timeout=40)
    r.raise_for_status()
    code = (r.json().get("meta") or {}).get("_elementor_code") or ""
    code = re.sub(
        r'<script id="ledajans-logo-swap">[\s\S]*?</script>\s*',
        "",
        code,
    )
    code = re.sub(
        r'<script id="ledajans-logo-places">[\s\S]*?</script>\s*',
        "",
        code,
    )
    # insert new scripts before identity block if present, else append
    if 'id="ledajans-header-identity"' in code:
        code = code.replace('<style id="ledajans-header-identity">', NEW_SCRIPTS + '<style id="ledajans-header-identity">')
    else:
        code = code.rstrip() + "\n" + NEW_SCRIPTS
    pr = requests.post(
        f"{SITE}/wp-json/wp/v2/elementor_snippet/5026",
        auth=AUTH,
        headers=H,
        data=json.dumps({"meta": {"_elementor_code": code}}),
        timeout=60,
    )
    print("snippet", pr.status_code, pr.text[:160])
    r2 = requests.get(f"{SITE}/wp-json/wp/v2/elementor_snippet/5026", auth=AUTH, headers=H, timeout=40)
    newc = (r2.json().get("meta") or {}).get("_elementor_code") or ""
    print("places_gone", "ledajans-logo-places" not in newc)
    print("swap_header", NEW_HEADER in newc)
    print("old_web_jpg", "ledajans-logo-web.jpg" in newc)
    requests.delete(f"{SITE}/wp-json/elementor/v1/cache", auth=AUTH, headers=H, timeout=40)
    requests.get(f"{SITE}/?LSCWP_CTRL=purge&litespeed_type=purge_all", headers={"User-Agent": H["User-Agent"]}, timeout=25)


if __name__ == "__main__":
    main()

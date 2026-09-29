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
H = {"User-Agent": "Mozilla/5.0 LEDAJANS-HDR-ID", "Content-Type": "application/json"}

IDENTITY_MARK = "ledajans-header-identity"
IDENTITY_BLOCK = r"""
<style id="ledajans-header-identity">
#page-content,
#wp-main-content {
  margin-top: 0 !important;
}
.wrapper-page > #gva-overlay,
.wrapper-page > .canvas-mobile {
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  overflow: hidden !important;
  pointer-events: none !important;
}
</style>
<script id="ledajans-header-identity-js">
(function () {
  function dropThemeCanvas() {
    document.querySelectorAll(".wrapper-page > .canvas-mobile, .wrapper-page > #gva-overlay").forEach(function (el) {
      el.remove();
    });
  }
  function lockTrLabels() {
    var map = {
      "Contact Us": "İletişim",
      Kontakt: "İletişim",
      Contact: "İletişim",
      Home: "Anasayfa",
      Startseite: "Anasayfa"
    };
    document.querySelectorAll(
      "#menu-anamenu-desktop .menu-title, .elementor-element-123bc72 .gva-main-menu > li > a .menu-title"
    ).forEach(function (el) {
      var t = (el.textContent || "").trim();
      if (map[t]) el.textContent = map[t];
    });
    document.querySelectorAll("header.wp-site-header, #menu-anamenu-desktop").forEach(function (el) {
      el.setAttribute("translate", "no");
    });
  }
  function run() {
    dropThemeCanvas();
    lockTrLabels();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run);
  else run();
})();
</script>
"""

URL_PATCHES = {
    1432: {"object_id": 5002, "object": "page", "type": "post_type", "title": "İç Mekan LED Ekran"},
    1430: {"object_id": 5003, "object": "page", "type": "post_type", "title": "Dış Mekan LED Ekran"},
    1436: {"object_id": 5004, "object": "page", "type": "post_type", "title": "Rental Ekran"},
    1437: {"object_id": 5006, "object": "page", "type": "post_type", "title": "İç Mekan RGB Panel"},
    3786: {"url": "https://ledajans.com/dis-mekan-rgb-panel/", "title": "Dış Mekan RGB Panel"},
    1434: {"object_id": 5008, "object": "page", "type": "post_type", "title": "Kontrol Kartları"},
    3794: {"url": "https://ledajans.com/guc-kaynaklari/", "title": "Güç Kaynakları"},
    4326: {"object_id": 5017, "object": "page", "type": "post_type", "title": "HUIDU"},
    853: {"object_id": 195, "object": "page", "type": "post_type", "title": "Teknik Destek Videoları"},
}


def patch_menu(item_id: int, body: dict) -> None:
    payload = {"menus": 42, "status": "publish", **body}
    r = requests.post(
        f"{SITE}/wp-json/wp/v2/menu-items/{item_id}",
        auth=AUTH,
        headers=H,
        data=json.dumps(payload),
        timeout=40,
    )
    print(f"menu {item_id} {r.status_code} {r.text[:180]}")


def ensure_sertifika() -> None:
    r = requests.get(
        f"{SITE}/wp-json/wp/v2/menu-items",
        params={"menus": 42, "per_page": 100, "context": "edit"},
        auth=AUTH,
        headers=H,
        timeout=40,
    )
    items = r.json()
    for it in items:
        title = it.get("title") or {}
        raw = title.get("raw") if isinstance(title, dict) else str(title)
        url = it.get("url") or ""
        if "sertifika" in raw.lower() or "sertifikalarimiz" in url:
            print("sertifika exists", it.get("id"), url)
            return
    payload = {
        "title": "Sertifikalarımız",
        "status": "publish",
        "type": "post_type",
        "object": "page",
        "object_id": 5010,
        "parent": 785,
        "menus": 42,
        "menu_order": 4,
    }
    r = requests.post(
        f"{SITE}/wp-json/wp/v2/menu-items",
        auth=AUTH,
        headers=H,
        data=json.dumps(payload),
        timeout=40,
    )
    print("sertifika create", r.status_code, r.text[:220])
    r2 = requests.post(
        f"{SITE}/wp-json/wp/v2/menu-items/1428",
        auth=AUTH,
        headers=H,
        data=json.dumps({"menus": 42, "status": "publish", "menu_order": 5, "parent": 785}),
        timeout=40,
    )
    print("firma order", r2.status_code)


def patch_snippet() -> None:
    r = requests.get(f"{SITE}/wp-json/wp/v2/elementor_snippet/5026", auth=AUTH, headers=H, timeout=40)
    r.raise_for_status()
    code = (r.json().get("meta") or {}).get("_elementor_code") or ""
    if IDENTITY_MARK in code:
        code = re.sub(
            r"\n?<style id=\"ledajans-header-identity\">[\s\S]*?</script>\s*",
            "",
            code,
        )
    new_code = code.rstrip() + "\n" + IDENTITY_BLOCK
    pr = requests.post(
        f"{SITE}/wp-json/wp/v2/elementor_snippet/5026",
        auth=AUTH,
        headers=H,
        data=json.dumps({"meta": {"_elementor_code": new_code}}),
        timeout=60,
    )
    print("snippet 5026", pr.status_code, pr.text[:240])
    if pr.status_code >= 400:
        pr = requests.post(
            f"{SITE}/wp-json/wp/v2/elementor_snippet/5026",
            auth=AUTH,
            headers=H,
            data=json.dumps({"meta": {"_elementor_code": new_code, "_elementor_location": "elementor_head", "_elementor_priority": 1}}),
            timeout=60,
        )
        print("snippet retry", pr.status_code, pr.text[:240])


def purge() -> None:
    r = requests.delete(f"{SITE}/wp-json/elementor/v1/cache", auth=AUTH, headers=H, timeout=60)
    print("elementor_cache", r.status_code)
    r = requests.get(
        f"{SITE}/?LSCWP_CTRL=purge&litespeed_type=purge_all",
        headers={"User-Agent": H["User-Agent"]},
        timeout=30,
        allow_redirects=True,
    )
    print("litespeed", r.status_code)


def main() -> None:
    patch_snippet()
    for item_id, body in URL_PATCHES.items():
        patch_menu(item_id, body)
    ensure_sertifika()
    purge()


if __name__ == "__main__":
    main()

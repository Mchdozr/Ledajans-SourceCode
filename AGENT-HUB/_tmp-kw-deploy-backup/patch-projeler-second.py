from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
LIVE_HTML = HERE / "live-projeler-widget.html"
LOCAL = ROOT / "Anasayfa" / "widget-7-projeler.html"

VITRIN_CARD = """
          <article class="ledajans-project-card" data-category="İç Mekan LED Ekran" data-title="Mağaza vitrin LED ekran" data-excerpt="Cadde vitrini ve mağaza içi LED ekran; cam arkası dikey pano + tavan asma ekran, hazır teslim." data-description="Mağaza vitrin LED ekran uygulaması: caddeye bakan cam vitrinde dikey LED pano ve mağaza içinde asma yatay LED ekran. Yakın izleme, ürün vitrini ve kampanya yayını için iç mekan LED çözüm. LEDAJANS keşif, kurulum ve teslim." data-media-type="image" data-media-src="https://ledajans.com/wp-content/uploads/2026/09/magaza-vitrin-led-cadde-1.webp">
            <div class="ledajans-project-image-wrap ledajans-project-image-wrap--cover">
              <a href="https://ledajans.com/magaza-vitrin-led-ekran/">
              <img class="ledajans-project-image" src="https://ledajans.com/wp-content/uploads/2026/09/magaza-vitrin-led-cadde-1.webp" alt="Mağaza vitrin LED ekran" width="1280" height="720" loading="lazy" decoding="async" />
              </a>
              <span class="ledajans-project-category">Mağaza / vitrin</span>
            </div>
            <div class="ledajans-project-body">
              <h3 class="ledajans-project-title"><a href="https://ledajans.com/magaza-vitrin-led-ekran/" style="color:inherit;text-decoration:none;">Mağaza vitrin LED ekran</a></h3>
              <p class="ledajans-project-excerpt">Cadde vitrini ve mağaza içi LED ekran; cam arkası dikey pano + tavan asma ekran, hazır teslim.</p>
              <button type="button" class="ledajans-project-link"><span class="dot"></span>Detay</button>
            </div>
          </article>
"""


def load_env() -> tuple[str, str, str]:
    env: dict[str, str] = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip("\"'")
    return (
        env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/"),
        env["WP_USERNAME"],
        env["WP_APP_PASSWORD"].replace(" ", ""),
    )


def walk_get(nodes):
    if isinstance(nodes, list):
        for n in nodes:
            found = walk_get(n)
            if found:
                return found
        return None
    if not isinstance(nodes, dict):
        return None
    settings = nodes.get("settings") or {}
    val = settings.get("html")
    if isinstance(val, str) and "ledajans-project-card" in val:
        return val
    for key in ("elements", "content"):
        if key in nodes:
            found = walk_get(nodes[key])
            if found:
                return found
    return None


def insert_second(html: str) -> str:
    if 'data-title="Mağaza vitrin LED ekran"' in html:
        html = html.replace(
            "https://ledajans.com/wp-content/uploads/2026/09/magaza-vitrin-led-cadde.webp",
            "https://ledajans.com/wp-content/uploads/2026/09/magaza-vitrin-led-cadde-1.webp",
        )
        html = html.replace(
            'alt="Mağaza vitrin LED ekran cadde uygulaması"',
            'alt="Mağaza vitrin LED ekran"',
        )
        return html
    marker = '<div class="ledajans-projects-grid">'
    i = html.find(marker)
    if i < 0:
        raise RuntimeError("grid missing")
    first_close = html.find("</article>", i)
    if first_close < 0:
        raise RuntimeError("first article missing")
    insert_at = first_close + len("</article>")
    return html[:insert_at] + "\n" + VITRIN_CARD + html[insert_at:]


def main() -> None:
    site, user, pw = load_env()
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages",
        params={"slug": "projeler", "context": "edit"},
        auth=(user, pw),
        headers={"User-Agent": "LEDAJANS-PATCH-PROJ/1.0"},
        timeout=60,
    )
    r.raise_for_status()
    raw = (r.json()[0].get("meta") or {}).get("_elementor_data")
    data = json.loads(raw) if isinstance(raw, str) else raw
    html = walk_get(data)
    if not html:
        raise RuntimeError("no projects widget")
    LIVE_HTML.write_text(html, encoding="utf-8")
    patched = insert_second(html)
    LOCAL.write_text(patched, encoding="utf-8")
    print("live_len", len(html), "patched_len", len(patched))
    print("vitrin", patched.count('data-title="Mağaza vitrin LED ekran"'))
    print("cadde-1", patched.count("magaza-vitrin-led-cadde-1.webp"))
    print("kure", "Küre" in patched or "kure" in patched.lower())


if __name__ == "__main__":
    main()

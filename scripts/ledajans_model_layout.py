"""Model/ürün sayfaları için ortak yerleşim: hero + ürün alanı (tek kaynak).

Kullanan üreticiler:
  scripts/create-rental-model-pages.py
  scripts/create-icrgb-model-pages.py
  scripts/create-disrgb-model-pages.py

Sayfa = [hero bölümü] + [ürün alanı bölümü]. Sol ürün menüsü, slider, "Ürün Özellikleri/Neden Ledajans"
bloğu ve kategori kart ızgarası bilinçli olarak yok.
"""
from __future__ import annotations

import html as htmlmod
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = "elementor_header_footer"
SPEC_DOC_LABEL = "Teknik Döküman İndir"
SPEC_DOC_SLOT = "<!-- la-spec-doc-slot -->"

LA_RM_CSS = """<style>
  .la-rm-specs { width: 100%; border-collapse: collapse; margin: 0 0 1.5rem; font-size: .95rem; }
  .la-rm-specs th, .la-rm-specs td { text-align: left; padding: .75rem 1rem; border-bottom: 1px solid #e5e7eb; }
  .la-rm-specs th { width: 45%; color: #111827; font-weight: 600; background: #f9fafb; }
  .la-rm-specs td { color: #374151; }
  .la-rm-cta { display: flex; flex-wrap: wrap; gap: .75rem; margin-top: 1.25rem; }
  .la-rm-cta a { display: inline-flex; align-items: center; justify-content: center; min-height: 48px; padding: 0 1.4rem; border-radius: 8px; font-weight: 600; text-decoration: none; }
  .la-rm-cta .p { background: #F46F2C; color: #fff; }
  .la-rm-cta .g { border: 1px solid #111827; color: #111827; }
  .la-rm-cta .d { background: #111827; color: #fff; }
</style>"""


@dataclass
class ProductArea:
    title: str
    intro_html: str
    spec_title: str
    specs: list[tuple[str, str]]
    spec_note_html: str
    usage_title: str
    usage_html: str
    links_html: str
    ctas: list[tuple[str, str, str]]  # (sınıf "p"|"g", href, etiket)
    schema: dict[str, Any]
    # Modele özel Google Drive teknik föy linki. None iken buton basılmaz, yalnız SPEC_DOC_SLOT yorumu kalır.
    spec_doc_url: str | None = None
    extra_sections_html: list[str] = field(default_factory=list)


def base_style(section_html: str) -> str:
    return section_html[: section_html.index("</style>") + len("</style>")]


def spec_doc_button(url: str | None) -> str:
    if not url:
        return SPEC_DOC_SLOT
    return (
        f'<div class="la-rm-cta la-rm-doc"><a class="d" href="{htmlmod.escape(url)}" target="_blank" '
        f'rel="noopener">{SPEC_DOC_LABEL}</a></div>'
    )


def render_product_area(style: str, a: ProductArea) -> str:
    rows = "\n".join(
        f'          <tr><th scope="row">{htmlmod.escape(k)}</th><td>{htmlmod.escape(v)}</td></tr>' for k, v in a.specs
    )
    ctas = "\n".join(f'        <a class="{c}" href="{h}">{t}</a>' for c, h, t in a.ctas)
    extra = "\n".join(a.extra_sections_html)
    return f"""{style}
{LA_RM_CSS}

<div class="indoor-content-wrapper">
  <div class="indoor-content">
    <h2 class="indoor-content-title">{a.title}</h2>

    <div class="indoor-content-section">
      <p class="indoor-content-text">
        {a.intro_html}
      </p>
    </div>

    <div class="indoor-content-section">
      <h3 class="indoor-content-section-title">{a.spec_title}</h3>
      <table class="la-rm-specs">
        <tbody>
{rows}
        </tbody>
      </table>
      {spec_doc_button(a.spec_doc_url)}
      <p class="indoor-content-text">
        {a.spec_note_html}
      </p>
    </div>
{extra}
    <div class="indoor-content-section">
      <h3 class="indoor-content-section-title">{a.usage_title}</h3>
      <p class="indoor-content-text">
        {a.usage_html}
      </p>
      <div class="indoor-content-highlight">
        <p class="indoor-content-highlight-text">
          {a.links_html}
        </p>
      </div>
      <div class="la-rm-cta">
{ctas}
      </div>
    </div>
  </div>
</div>
<script type="application/ld+json">
{json.dumps(a.schema, ensure_ascii=False, indent=2)}
</script>
"""


def adapt_hero(h: str, *, name: str, url: str, hub_name: str, hub_url: str, subtitle_html: str) -> str:
    """Kategori sayfasının hero'sunu modele uyarlar: tek H1 + BreadcrumbList'e 4. seviye."""
    h = re.sub(r'aria-label="[^"]*"', f'aria-label="{name}"', h, count=1)
    h = re.sub(r'(<h1 class="ledajans-blog-hero-title">).*?(</h1>)', rf"\g<1>{name}\g<2>", h, count=1, flags=re.S)
    h = re.sub(
        r'<span class="ledajans-blog-hero-subtitle".*?</span>\n',
        lambda _: f'<span class="ledajans-blog-hero-subtitle" style="color:#f46f2c">{subtitle_html}</span>\n',
        h, count=1, flags=re.S,
    )
    crumb = f'{{"@type":"ListItem","position":3,"name":"{hub_name}","item":"{hub_url}"}}'
    assert crumb in h, f"breadcrumb yok: {hub_name}"
    h = h.replace(crumb, crumb + f',\n    {{"@type":"ListItem","position":4,"name":"{name}","item":"{url}"}}')
    assert h.count("<h1") == 1 and name in h and '"position":4' in h, url
    return h


def _section(html: str, sid: str) -> dict[str, Any]:
    return {
        "id": sid, "elType": "section", "settings": {"layout": "full_width", "gap": "no"}, "isInner": False,
        "elements": [{
            "id": f"{sid}c0", "elType": "column", "settings": {"_column_size": 100}, "isInner": False,
            "elements": [{"id": f"{sid}w0", "elType": "widget", "widgetType": "html", "settings": {"html": html},
                          "elements": [], "isInner": False}],
        }],
    }


def build_layout(prefix: str, hero_html: str, product_html: str) -> tuple[list[dict[str, Any]], str]:
    data = [_section(hero_html, f"{prefix}a0"), _section(product_html, f"{prefix}a1")]
    return data, f"{hero_html}\n{product_html}"


def page_meta(data: list[dict[str, Any]], seo: dict[str, Any]) -> dict[str, Any]:
    return {
        "_elementor_data": json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        "_elementor_edit_mode": "builder",
        "_elementor_template_type": "wp-page",
        **seo,
    }


def page_payload(title: str, slug: str, flat: str, meta: dict[str, Any]) -> dict[str, Any]:
    return {"title": title, "slug": slug, "status": "publish", "template": TEMPLATE, "content": flat, "meta": meta}


def word_count(flat: str) -> int:
    return len(re.sub(r"<[^>]+>", " ", re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", flat, flags=re.S)).split())


def write_preview(path: Path, title: str, flat: str) -> None:
    path.write_text(
        f"<!doctype html><meta charset=utf-8><title>{title}</title><body style='margin:0;font-family:sans-serif'>{flat}</body>",
        encoding="utf-8",
    )


def load_env() -> tuple[str, str, str]:
    env: dict[str, str] = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip("\"'")
    return env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/"), env["WP_USERNAME"], env["WP_APP_PASSWORD"].replace(" ", "")


def wp_session(ua: str) -> tuple[requests.Session, str]:
    site, user, pw = load_env()
    s = requests.Session()
    s.auth = (user, pw)
    s.headers.update({"User-Agent": ua, "Content-Type": "application/json"})
    return s, site


def find_page(s: requests.Session, site: str, slug: str) -> dict[str, Any] | None:
    r = s.get(f"{site}/wp-json/wp/v2/pages", params={"slug": slug, "status": "any", "context": "edit", "_fields": "id,status,link"}, timeout=60)
    r.raise_for_status()
    items = r.json()
    return items[0] if items else None


def upsert_page(s: requests.Session, site: str, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    existing = find_page(s, site, payload["slug"])
    if existing:
        r = s.post(f"{site}/wp-json/wp/v2/pages/{existing['id']}", json=payload, timeout=120)
        action = "update"
    else:
        r = s.post(f"{site}/wp-json/wp/v2/pages", json=payload, timeout=120)
        action = "create"
    if r.status_code not in (200, 201):
        raise RuntimeError(f"{payload['slug']} {r.status_code} {r.text[:300]}")
    body = r.json()
    if body.get("slug") != payload["slug"]:
        raise RuntimeError(f"slug çakışması: {payload['slug']} -> {body.get('slug')} (id={body.get('id')})")
    return action, body


def purge_caches(s: requests.Session, site: str, ua: str) -> None:
    r = s.delete(f"{site}/wp-json/elementor/v1/cache", timeout=60)
    print("elementor_cache", r.status_code)
    try:
        r = requests.get(f"{site}/?LSCWP_CTRL=purge&litespeed_type=purge_all", headers={"User-Agent": ua, "Cache-Control": "no-cache"}, timeout=20)
        print("lsc_purge", r.status_code)
    except requests.RequestException as exc:
        print("lsc_purge ERR", type(exc).__name__)

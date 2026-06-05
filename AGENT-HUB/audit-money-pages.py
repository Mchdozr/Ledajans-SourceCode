"""Canlı para sayfa SEO denetimi — GSC checklist ve RankMath audit çıktısı üretir."""
from __future__ import annotations

import json
import re
import ssl
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "AGENT-HUB"

MONEY_PAGES = [
    ("Ana sayfa", "https://ledajans.com/"),
    ("LED ekran hub", "https://ledajans.com/led-ekran/"),
    ("İç mekan", "https://ledajans.com/ic-mekan-led-ekran/"),
    ("Dış mekan", "https://ledajans.com/dis-mekan-led-ekran/"),
    ("Rental", "https://ledajans.com/rental-ekran/"),
    ("COB", "https://ledajans.com/cob-ekran/"),
]

UA = "Mozilla/5.0 (compatible; LEDAJANS-SEO-Audit/1.0)"


def fetch(url: str, timeout: int = 45) -> tuple[int, str, dict]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        headers = {k.lower(): v for k, v in resp.headers.items()}
        return resp.status, body, headers


def meta_content(html: str, name: str) -> str:
    for pat in (
        rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']*)["\']',
        rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']{re.escape(name)}["\']',
    ):
        m = re.search(pat, html, re.I)
        if m:
            return unescape(m.group(1).strip())
    return ""


def canonical_url(html: str) -> str:
    m = re.search(
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
        html,
        re.I,
    )
    if m:
        return m.group(1).strip()
    m = re.search(
        r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
        html,
        re.I,
    )
    return m.group(1).strip() if m else ""


def first_h1(html: str) -> str:
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    if not m:
        return ""
    return re.sub(r"<[^>]+>", "", m.group(1)).strip()


def indexability_note(html: str, canonical: str, url: str) -> str:
    robots = meta_content(html, "robots").lower()
    if "noindex" in robots:
        return "BLOCKED:noindex"
    if canonical and canonical.rstrip("/") != url.rstrip("/"):
        return f"canonical_mismatch->{canonical}"
    return "crawl_ok_gsc_confirm"


def sitemap_urls() -> set[str]:
    urls: set[str] = set()
    for sm in ("https://ledajans.com/sitemap_index.xml", "https://ledajans.com/sitemap.xml"):
        try:
            _, body, _ = fetch(sm)
            root = ET.fromstring(body)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            for loc in root.findall(".//sm:loc", ns):
                if loc.text:
                    urls.add(loc.text.strip())
            for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
                if loc.text:
                    urls.add(loc.text.strip())
        except Exception:
            continue
    return urls


def audit_all() -> list[dict]:
    sm_urls = sitemap_urls()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rows = []
    for label, url in MONEY_PAGES:
        try:
            status, html, headers = fetch(url)
            canon = canonical_url(html)
            row = {
                "label": label,
                "url": url,
                "http_status": status,
                "indexed_guess": "GSC doğrula"
                if indexability_note(html, canon, url) == "crawl_ok_gsc_confirm"
                else indexability_note(html, canon, url),
                "canonical": canon or "(yok)",
                "canonical_ok": canon.rstrip("/") == url.rstrip("/") if canon else False,
                "last_crawl": f"canlı {now} (Last-Modified: {headers.get('last-modified', 'n/a')})",
                "title": (
                    meta_content(html, "title")
                    or meta_content(html, "og:title")
                    or meta_content(html, "twitter:title")
                )[:120],
                "description": meta_content(html, "description"),
                "description_len": len(meta_content(html, "description")),
                "robots": meta_content(html, "robots") or "(yok)",
                "h1": first_h1(html)[:200],
                "in_sitemap": url in sm_urls or url.rstrip("/") in {u.rstrip("/") for u in sm_urls},
                "rankmath_title": meta_content(html, "twitter:title") or meta_content(html, "og:title"),
            }
        except Exception as exc:
            row = {
                "label": label,
                "url": url,
                "http_status": 0,
                "indexed_guess": f"ERROR:{exc}",
                "canonical": "",
                "canonical_ok": False,
                "last_crawl": "",
                "title": "",
                "description": "",
                "description_len": 0,
                "robots": "",
                "h1": "",
                "in_sitemap": False,
                "rankmath_title": "",
            }
        rows.append(row)
    return rows


def write_gsc_checklist(rows: list[dict]) -> None:
    lines = [
        "# GSC Export Checklist (P0)",
        "",
        f"Son güncelleme (otomatik canlı crawl): **{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}**",
        "",
        "> **Indexed** sütunu: canlı crawl + sitemap; kesin durum için GSC URL Inspection ile doğrula.",
        "",
        "## İndirilecek raporlar",
        "",
        "1. **Indexing → Pages** — reason dağılımı",
        "2. **Indexing → Page indexing** — excluded URL listesi",
        "3. **Performance → Search results** — query + page (export)",
        "4. **Sitemaps** — submitted / indexed sayıları",
        "",
        "## Para sayfa URL Inspection (canlı test)",
        "",
        "| URL | Indexed | Canonical | Last crawl | Sitemap | Not |",
        "|-----|---------|-----------|------------|---------|-----|",
    ]
    for r in rows:
        idx = "crawl_ok" if r["indexed_guess"] == "crawl_ok_gsc_confirm" else r["indexed_guess"]
        sm = "evet" if r["in_sitemap"] else "hayır"
        note = "OK" if r["canonical_ok"] else "canonical kontrol"
        lines.append(
            f"| {r['url']} | {idx} | {r['canonical']} | {r['last_crawl']} | {sm} | {note} |"
        )
    lines.extend(
        [
            "",
            "## Kabul kriteri",
            "",
            "- Reason yüzdeleri toplamı %100 (GSC export sonrası)",
            "- P0 para sayfalarında `Duplicate` / `Crawled - currently not indexed` için aksiyon owner atanmış",
            "- Export tarihi ile `SERP-BASELINE.csv` aynı hafta içinde",
            "",
            "## Ham veri",
            "",
            f"Dosya: `AGENT-HUB/audit-money-pages-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json`",
        ]
    )
    (AGENT / "GSC-EXPORT-CHECKLIST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_rankmath_audit(rows: list[dict]) -> None:
    lines = [
        "# RankMath / Meta Audit — Para Sayfalar",
        "",
        f"Tarih: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "| Sayfa | Title (len) | Description (len) | H1 | Canonical OK |",
        "|-------|-------------|-------------------|-----|--------------|",
    ]
    for r in rows:
        tlen = len(r["title"])
        dlen = r["description_len"]
        desc_ok = "OK" if 120 <= dlen <= 160 else ("kısa" if dlen < 120 else "uzun")
        lines.append(
            f"| {r['label']} | {r['title'][:70]}… ({tlen}) | {dlen} ({desc_ok}) | {r['h1'][:50]} | {'evet' if r['canonical_ok'] else 'hayır'} |"
        )
    lines.extend(["", "## Detay", ""])
    for r in rows:
        lines.append(f"### {r['label']} — {r['url']}")
        lines.append(f"- **Title:** {r['title']}")
        lines.append(f"- **Description:** {r['description']}")
        lines.append(f"- **Robots:** {r['robots']}")
        lines.append(f"- **H1:** {r['h1']}")
        lines.append("")
    (AGENT / "RANKMATH-AUDIT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = audit_all()
    out_json = AGENT / f"audit-money-pages-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
    out_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    write_gsc_checklist(rows)
    write_rankmath_audit(rows)
    print(f"Wrote {out_json}")
    print(f"Pages: {len(rows)}, canonical_ok: {sum(1 for r in rows if r['canonical_ok'])}")


if __name__ == "__main__":
    main()

"""Silinen 30 model sayfasının içeriğini Internet Archive kopyasından (13 Mayıs 2026) birebir geri yükler.

Kaynak: AGENT-HUB/_tmp-kw-deploy-backup/wayback-products/<slug>.page.html
(header şablonu 43 ve footer şablonu 75 hariç, yalnız sayfanın kendi Elementor içeriği).
Her üst bölümdeki HTML widget'ı aynı sırayla yeni sayfaya aktarılır; Rank Math alanlarına dokunulmaz.

python scripts/restore-wayback-model-pages.py            # dry-run: önizleme + kontrol
python scripts/restore-wayback-model-pages.py --publish  # canlı: sayfaları güncelle + cache purge
python scripts/restore-wayback-model-pages.py --summary summary-ofc --create --publish  # hedef yoksa oluştur
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from ledajans_model_layout import TEMPLATE, purge_caches, word_count, wp_session, write_preview

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "AGENT-HUB/_tmp-kw-deploy-backup/wayback-products"
PREVIEW = SRC / "preview"
UA = "LEDAJANS-Wayback-Restore/1.0"


def widgets_by_section(page_html: str) -> list[list[str]]:
    soup = BeautifulSoup(page_html, "html.parser")
    root = soup.find(attrs={"data-elementor-type": True})
    sections = []
    for sec in root.find_all(class_="elementor-top-section", recursive=True):
        htmls = []
        for w in sec.find_all(attrs={"data-widget_type": True}):
            if w.get("data-widget_type") != "html.default":
                raise ValueError(f"beklenmeyen widget: {w.get('data-widget_type')}")
            container = w.find(class_="elementor-widget-container") or w
            htmls.append(container.decode_contents().strip())
        sections.append(htmls)
    return sections


def section(sid: str, htmls: list[str]) -> dict[str, Any]:
    return {
        "id": sid, "elType": "section", "settings": {"layout": "full_width", "gap": "no"}, "isInner": False,
        "elements": [{
            "id": f"{sid}c", "elType": "column", "settings": {"_column_size": 100}, "isInner": False,
            "elements": [
                {"id": f"{sid}w{i}", "elType": "widget", "widgetType": "html", "settings": {"html": h},
                 "elements": [], "isInner": False}
                for i, h in enumerate(htmls)
            ],
        }],
    }


def find_target(s, site: str, slug: str) -> tuple[str, dict[str, Any]] | None:
    for kind in ("pages", "posts"):
        r = s.get(f"{site}/wp-json/wp/v2/{kind}", params={"slug": slug, "status": "any", "context": "edit",
                                                         "_fields": "id,status,link,type,template"}, timeout=60)
        r.raise_for_status()
        if r.json():
            return kind, r.json()[0]
    return None


def seo_for_new(title: str, flat: str, archived_desc: str) -> dict[str, str]:
    desc = archived_desc.strip()
    if not desc:
        sub = re.search(r'class="ledajans-blog-hero-subtitle"[^>]*>(.*?)</span>', flat, re.S)
        desc = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", sub.group(1))).strip() if sub else title
    return {
        "rank_math_title": f"{title} | LEDAJANS",
        "rank_math_description": desc[:158],
        "rank_math_focus_keyword": title.lower(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--summary", default="summary")
    ap.add_argument("--create", action="store_true", help="hedef sayfa yoksa yeni sayfa oluştur")
    args = ap.parse_args()

    summary = json.loads((SRC / f"{args.summary}.json").read_text(encoding="utf-8"))
    PREVIEW.mkdir(exist_ok=True)
    jobs = []
    for i, item in enumerate(summary):
        slug = item["slug"]
        sections = widgets_by_section((SRC / f"{slug}.page.html").read_text(encoding="utf-8"))
        flat = "\n".join(h for sec in sections for h in sec)
        title = re.sub(r"\s+", " ", item["h1"][0]).strip()
        h1 = len(re.findall(r"<h1[\s>]", flat))
        specs = [u for u in item["specs"] if u.replace("&amp;", "&") in flat.replace("&amp;", "&")]
        if h1 != 1 or not specs:
            raise RuntimeError(f"{slug}: h1={h1} spec={specs}")
        data = [section(f"wb{i}s{j}", htmls) for j, htmls in enumerate(sections)]
        write_preview(PREVIEW / f"{slug}.html", title, flat)
        print(f"{slug:42} sections={[len(x) for x in sections]} h1={h1} words~{word_count(flat)} spec={specs[0][-40:]}")
        jobs.append((slug, {
            "title": title, "slug": slug, "status": "publish", "template": TEMPLATE, "content": flat,
            "_seo": seo_for_new(title, flat, item.get("desc", "")),
            "meta": {
                "_elementor_data": json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                "_elementor_edit_mode": "builder",
                "_elementor_template_type": "wp-page",
            },
        }))

    s, site = wp_session(UA)
    targets = {slug: find_target(s, site, slug) for slug, _ in jobs}
    missing = [slug for slug, t in targets.items() if not t]
    for slug, t in targets.items():
        print("hedef", slug, t[0] if t else "YOK", t[1]["id"] if t else "")
    if missing and not args.create:
        print("EKSİK HEDEF:", missing)
        return 1
    if not args.publish:
        for slug, payload in jobs:
            if slug in missing:
                print("oluşturulacak", slug, payload["_seo"])
        print(f"DRY_RUN OK — önizleme: {PREVIEW}")
        return 0

    backup = SRC / "live-before-restore"
    backup.mkdir(exist_ok=True)
    results = []
    for slug, payload in jobs:
        seo = payload.pop("_seo")
        if slug in missing:
            payload["meta"].update(seo)
            r = s.post(f"{site}/wp-json/wp/v2/pages", json=payload, timeout=120)
            if r.status_code != 201 or r.json().get("slug") != slug:
                raise RuntimeError(f"{slug} {r.status_code} {r.text[:300]}")
            results.append({"slug": slug, "kind": "pages", "id": r.json()["id"], "link": r.json().get("link")})
            print("create pages", slug, r.json()["id"])
            continue
        kind, t = targets[slug]
        cur = s.get(f"{site}/wp-json/wp/v2/{kind}/{t['id']}", params={"context": "edit"}, timeout=60).json()
        (backup / f"{slug}.json").write_text(json.dumps(cur, ensure_ascii=False), encoding="utf-8")
        payload.pop("slug")
        if kind == "posts":
            payload.pop("template")
        r = s.post(f"{site}/wp-json/wp/v2/{kind}/{t['id']}", json=payload, timeout=120)
        if r.status_code != 200:
            raise RuntimeError(f"{slug} {r.status_code} {r.text[:300]}")
        results.append({"slug": slug, "kind": kind, "id": t["id"], "link": r.json().get("link")})
        print("update", kind, slug, t["id"])
    purge_caches(s, site, UA)
    (SRC / f"restored-{args.summary}.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

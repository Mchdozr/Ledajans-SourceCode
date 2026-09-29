from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WA = "https://wa.me/905438795108"
FILES = {
    ROOT / "SEO-Icerik-Widgets/kullanim-alanlari/cephe-led-ekran.html": "Cephe senaryoları",
    ROOT / "SEO-Icerik-Widgets/temel-rehberler/pitch-secim-rehberi.html": "Pitch ailesi",
    ROOT / "SEO-Icerik-Widgets/kullanim-alanlari/gob-led-ekran.html": "GOB seçenekleri",
    ROOT / "SEO-Icerik-Widgets/kullanim-alanlari/fuar-led-ekran.html": "Fuar senaryoları",
    ROOT / "SEO-Icerik-Widgets/sektor-rehberleri/magaza-vitrin-led-rehberi.html": "Mağaza senaryoları",
    ROOT / "SEO-Icerik-Widgets/sehir-sayfalari/istanbul-led-ekran.html": "İstanbul senaryoları",
}

btn = re.compile(
    r'(<a class="la-kw-btn la-kw-btn-p"[^>]*>.*?</a>\s*<a class="la-kw-btn la-kw-btn-o"[^>]*>.*?</a>)',
    re.S,
)

for path, title in FILES.items():
    html = path.read_text(encoding="utf-8")
    if 'class="la-kw-actions"' not in html:
        html, n = btn.subn(
            rf'<div class="la-kw-actions">\n    \1\n    <a class="la-kw-btn la-kw-btn-o" href="{WA}">WhatsApp teklif</a>\n    </div>',
            html,
            count=1,
        )
        print(path.name, "btn", n)
        if n != 1:
            raise SystemExit(f"btn fail {path.name}")
    if '<h2 class="la-kw-sec"' not in html:
        html = html.replace(
            '<div class="la-kw-grid">',
            f'<h2 class="la-kw-sec">{title}</h2>\n  <div class="la-kw-grid">',
            1,
        )
    if '<div class="la-kw-table-wrap"' not in html:
        html = html.replace("<table>", '<div class="la-kw-table-wrap">\n  <table>', 1)
        html = html.replace("</table>", "</table>\n  </div>", 1)
    path.write_text(html, encoding="utf-8")
    print(
        "OK",
        path.name,
        WA in html,
        '<h2 class="la-kw-sec"' in html,
        '<div class="la-kw-table-wrap"' in html,
    )

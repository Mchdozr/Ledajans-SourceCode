from __future__ import annotations

import json
import re
import sys
from datetime import datetime
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

site = env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
auth = (env["WP_USERNAME"], env["WP_APP_PASSWORD"].replace(" ", ""))
headers = {"User-Agent": "LEDAJANS-DIS-RGB/1.0", "Content-Type": "application/json"}
APPLY = "--apply" in sys.argv
HERE = Path(__file__).parent
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
HUB_PAGE = 3795
HUB_BACKUP = HERE / "dis-rgb-3795-elementor-20260929-150106.json"
HUB_CONTENT_BACKUP = HERE / "dis-rgb-3795-content-20260929-150106.html"
B = "https://ledajans.com/"

PRODUCTS = [
    {"slug": "h2-5-dis-mekan-rgb-panel", "name": "H2.5", "pitch": "2.5 mm", "density": "160.000 nokta/m²", "bright": "≥4500 cd/m²", "refresh": "≥7680 Hz", "tmp": B + "p4-outdoor-rgb-panel/"},
    {"slug": "h3-076-dis-mekan-rgb-panel", "name": "H3.076", "pitch": "3.076 mm", "density": "105.625 nokta/m²", "bright": "≥4500 cd/m²", "refresh": "≥7680 Hz", "tmp": B + "p4-outdoor-rgb-panel/"},
    {"slug": "h4-dis-mekan-rgb-panel", "name": "H4", "pitch": "4 mm", "density": "62.500 nokta/m²", "bright": "≥4500 cd/m²", "refresh": "≥7680 Hz", "tmp": B + "p4-outdoor-rgb-panel/"},
    {"slug": "h5-dis-mekan-rgb-panel", "name": "H5", "pitch": "5 mm", "density": "40.000 nokta/m²", "bright": "≥4500 cd/m²", "refresh": "≥7680 Hz", "tmp": B + "p5-outdoor-rgb-panel/"},
    {"slug": "p10-4s-dis-mekan-rgb-panel", "name": "P10 4S", "pitch": "10 mm", "density": "10.000 nokta/m²", "bright": "≥3500 cd/m²", "refresh": "1920 / 3840 Hz", "tmp": B + "p10-outdoor-rgb-panel/", "scan": "4S (1/4 tarama)"},
]

STYLE = """<style>
.la-rgb-product{max-width:60rem;margin:0 auto;color:#1f2937;line-height:1.7}
.la-rgb-product h2{font-size:1.5rem;font-weight:800;color:#1a1a2e;margin:2rem 0 .75rem}
.la-rgb-product table{width:100%;border-collapse:collapse;margin:1rem 0 1.5rem;font-size:.95rem}
.la-rgb-product th,.la-rgb-product td{border:1px solid #e5e7eb;padding:.65rem .9rem;text-align:left}
.la-rgb-product th{background:#f8fafc;width:40%;font-weight:600}
.la-rgb-product .la-rgb-note{background:#fff7f2;border-left:4px solid #f46f2c;padding:.9rem 1rem;border-radius:8px;font-size:.95rem}
.la-rgb-product .la-rgb-cta{display:inline-block;background:#f46f2c;color:#fff!important;font-weight:700;padding:.85rem 1.6rem;border-radius:10px;text-decoration:none;margin-top:.5rem}
.la-rgb-product ul{padding-left:1.2rem}
</style>"""


def build(p: dict) -> str:
    title = f"{p['name']} Dış Mekan RGB LED Panel"
    rows = [
        ("Model", p["name"]),
        ("Piksel aralığı", p["pitch"]),
        ("Piksel yoğunluğu", p["density"]),
        ("Parlaklık", p["bright"]),
        ("Yenileme hızı", p["refresh"]),
    ]
    if p.get("scan"):
        rows.append(("Tarama", p["scan"]))
    rows += [("Koruma sınıfı", "IP65"), ("Kullanım ortamı", "Dış mekan")]
    trs = "\n".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows)
    siblings = "\n".join(
        f'<li><a href="{B}{o["slug"]}/">{o["name"]} Dış Mekan RGB LED Panel</a> — {o["pitch"]}</li>'
        for o in PRODUCTS if o["slug"] != p["slug"]
    )
    return f"""{STYLE}
<div class="la-rgb-product">
<p><strong>{title}</strong>, <a href="{B}">LEDAJANS</a> <a href="{B}dis-mekan-rgb-panel/">dış mekan RGB LED panel</a> serisinde {p['pitch']} piksel aralığına sahip, IP65 korumalı bir LED modüldür. {p['density']} piksel yoğunluğu ve {p['bright']} parlaklık değeriyle açık hava LED ekran uygulamaları için tasarlanmıştır.</p>

<h2>{p['name']} Dış Mekan RGB LED Panel Teknik Özellikleri</h2>
<table>
<tbody>
{trs}
</tbody>
</table>

<p class="la-rgb-note">Modül ölçüsü, modül çözünürlüğü, ağırlık, güç tüketimi, sürüş/tarama modu ve kabin ölçüleri gibi ayrıntılı değerler ile ürün dökümanı için <a href="{B}iletisim/">bizimle iletişime geçin</a>; projenize uygun teknik föyü paylaşalım.</p>

<h2>Diğer Dış Mekan RGB LED Panel Modelleri</h2>
<ul>
{siblings}
</ul>
<p>Tüm modelleri karşılaştırmak için <a href="{B}dis-mekan-rgb-panel/">Dış Mekan RGB Panel</a> sayfasını inceleyebilirsiniz.</p>

<h2>Fiyat Teklifi ve Teknik Destek</h2>
<p>{title} için güncel fiyat, stok durumu ve proje bazlı teknik destek almak için <a href="{B}iletisim/">iletişim sayfamızdan</a> bize ulaşabilir ya da +90 212 220 40 04 numaralı hattı arayabilirsiniz.</p>
<p><a class="la-rgb-cta" href="{B}iletisim/">FİYAT ALIN</a></p>
</div>"""


def meta(p: dict) -> dict:
    title = f"{p['name']} Dış Mekan RGB LED Panel"
    desc = f"{title}: {p['pitch']} piksel aralığı, {p['density']}, {p['bright']} parlaklık, IP65. LEDAJANS'tan teknik föy ve fiyat teklifi alın."
    return {
        "rank_math_title": f"{title} | {p['pitch']} IP65 | LEDAJANS",
        "rank_math_description": desc[:160],
        "rank_math_focus_keyword": f"{p['name'].lower()} dış mekan rgb led panel,dış mekan rgb led panel",
    }


def get(path, **params):
    return requests.get(f"{site}/wp-json/wp/v2/{path}", params=params, auth=auth, headers=headers, timeout=60)


# 1) slug collision check
existing = get("posts", slug=",".join(p["slug"] for p in PRODUCTS), status="any", context="edit", _fields="id,slug,status").json()
existing_pages = get("pages", slug=",".join(p["slug"] for p in PRODUCTS), status="any", context="edit", _fields="id,slug,status").json()
print("existing posts", existing, "pages", existing_pages)
have = {e["slug"]: e["id"] for e in existing}

for p in PRODUCTS:
    html = build(p)
    (HERE / f"new-{p['slug']}.html").write_text(html, encoding="utf-8")
    m = meta(p)
    print(p["slug"], "| words~", len(html.split()), "|", m["rank_math_title"], "| desc", len(m["rank_math_description"]))

# 2) hub restore plan
page = get(f"pages/{HUB_PAGE}", context="edit").json()
cur_raw = page["meta"]["_elementor_data"]
cur_data = json.loads(cur_raw) if isinstance(cur_raw, str) else cur_raw
cur_content = page["content"]["raw"]
(HERE / f"dis-rgb-3795-elementor-{STAMP}.json").write_text(cur_raw if isinstance(cur_raw, str) else json.dumps(cur_raw, ensure_ascii=False), encoding="utf-8")
(HERE / f"dis-rgb-3795-content-{STAMP}.html").write_text(cur_content, encoding="utf-8")
print("hub backup", STAMP)

old_raw = HUB_BACKUP.read_text(encoding="utf-8")
old_data = json.loads(old_raw)
old_content = HUB_CONTENT_BACKUP.read_text(encoding="utf-8")
expected = json.dumps(old_data, ensure_ascii=False)
exp_content = old_content
for p in PRODUCTS:
    expected = expected.replace(B + p["slug"] + "/", p["tmp"])
    exp_content = exp_content.replace(B + p["slug"] + "/", p["tmp"])
same_el = expected == json.dumps(cur_data, ensure_ascii=False)
norm = lambda s: re.sub(r"\s+", "", s)
same_ct = norm(exp_content) == norm(cur_content)

old_seq = re.findall("|".join(re.escape(B + p["slug"] + "/") for p in PRODUCTS), old_content)
tmp_urls = sorted({p["tmp"] for p in PRODUCTS})
tmp_re = re.compile("|".join(re.escape(u) for u in tmp_urls))
print("tmp urls in old content (must be 0):", len(tmp_re.findall(old_content)), "| seq", len(old_seq), "| cur tmp", len(tmp_re.findall(cur_content)))
it = iter(old_seq)
new_content = tmp_re.sub(lambda m: next(it), cur_content)
print("restored content == old (normalized):", norm(new_content) == norm(old_content))
_x, _y = norm(exp_content), norm(cur_content)
_i = next((i for i in range(min(len(_x), len(_y))) if _x[i] != _y[i]), None)
print("diff at", _i, len(_x), len(_y), repr(_x[(_i or 0) - 80:(_i or 0) + 80]), repr(_y[(_i or 0) - 80:(_i or 0) + 80]))
print("hub unchanged since fix: elementor", same_el, "content", same_ct)
restored_blob = json.dumps(old_data, ensure_ascii=False)
print("old slugs in restore:", {p["slug"]: restored_blob.count(B + p["slug"] + "/") for p in PRODUCTS})
if not (same_el and same_ct):
    print("ABORT: hub page changed by someone else; manual merge needed")
    sys.exit(2)

if not APPLY:
    print("dry-run; pass --apply")
    sys.exit(0)

# 3) create posts
for p in PRODUCTS:
    body = {
        "title": f"{p['name']} Dış Mekan RGB LED Panel",
        "slug": p["slug"],
        "status": "publish",
        "content": build(p),
        "categories": [1],
        "comment_status": "closed",
        "ping_status": "closed",
        "meta": meta(p),
    }
    if p["slug"] in have:
        r = requests.post(f"{site}/wp-json/wp/v2/posts/{have[p['slug']]}", json=body, auth=auth, headers=headers, timeout=120)
    else:
        r = requests.post(f"{site}/wp-json/wp/v2/posts", json=body, auth=auth, headers=headers, timeout=120)
    j = r.json()
    print("post", p["slug"], r.status_code, j.get("id"), j.get("slug"), j.get("status"), j.get("link"))

# 4) hub relink
payload = {
    "meta": {
        "_elementor_data": json.dumps(old_data, ensure_ascii=False, separators=(",", ":")),
        "_elementor_edit_mode": "builder",
    },
    "content": new_content,
}
u = requests.post(f"{site}/wp-json/wp/v2/pages/{HUB_PAGE}", json=payload, auth=auth, headers=headers, timeout=120)
print("hub POST", u.status_code, "" if u.ok else u.text[:300])
c = requests.delete(f"{site}/wp-json/elementor/v1/cache", auth=auth, headers=headers, timeout=60)
print("elementor cache", c.status_code)

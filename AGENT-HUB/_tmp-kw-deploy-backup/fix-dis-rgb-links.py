from __future__ import annotations

import json
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
PAGE_ID = 3795
APPLY = "--apply" in sys.argv

B = "https://ledajans.com/"
MAP = {
    B + "h2-5-dis-mekan-rgb-panel/": B + "p4-outdoor-rgb-panel/",
    B + "h3-076-dis-mekan-rgb-panel/": B + "p4-outdoor-rgb-panel/",
    B + "h4-dis-mekan-rgb-panel/": B + "p4-outdoor-rgb-panel/",
    B + "h5-dis-mekan-rgb-panel/": B + "p5-outdoor-rgb-panel/",
    B + "p10-4s-dis-mekan-rgb-panel/": B + "p10-outdoor-rgb-panel/",
}

r = requests.get(f"{site}/wp-json/wp/v2/pages/{PAGE_ID}", params={"context": "edit"}, auth=auth, headers=headers, timeout=60)
r.raise_for_status()
page = r.json()
raw = (page.get("meta") or {}).get("_elementor_data")
data = json.loads(raw) if isinstance(raw, str) else raw
content = page["content"]["raw"]

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
bdir = Path(__file__).parent
(bdir / f"dis-rgb-3795-elementor-{stamp}.json").write_text(raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False), encoding="utf-8")
(bdir / f"dis-rgb-3795-content-{stamp}.html").write_text(content, encoding="utf-8")
print("backup", stamp)

blob = json.dumps(data, ensure_ascii=False)
new_blob, new_content = blob, content
for old, new in MAP.items():
    print(f"{old} -> {new}  el={blob.count(old)} content={content.count(old)}")
    new_blob = new_blob.replace(old, new)
    new_content = new_content.replace(old, new)

if not APPLY:
    print("dry-run; pass --apply")
    sys.exit(0)

payload: dict = {
    "meta": {
        "_elementor_data": json.dumps(json.loads(new_blob), ensure_ascii=False, separators=(",", ":")),
        "_elementor_edit_mode": "builder",
    }
}
if new_content != content:
    payload["content"] = new_content
u = requests.post(f"{site}/wp-json/wp/v2/pages/{PAGE_ID}", json=payload, auth=auth, headers=headers, timeout=120)
print("POST", u.status_code, u.text[:200] if not u.ok else "")
c = requests.delete(f"{site}/wp-json/elementor/v1/cache", auth=auth, headers=headers, timeout=60)
print("elementor cache", c.status_code)
p = requests.post(f"{site}/wp-json/ledajans/v1/purge", auth=auth, headers=headers, timeout=60)
print("ledajans purge", p.status_code, p.text[:200])

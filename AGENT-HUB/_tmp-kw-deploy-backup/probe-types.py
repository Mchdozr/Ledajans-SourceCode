import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from ledajans_model_layout import wp_session  # noqa: E402

s, site = wp_session("Mozilla/5.0 probe")
types = s.get(f"{site}/wp-json/wp/v2/types", params={"context": "edit"}, timeout=60).json()
for k, v in types.items():
    rb = v.get("rest_base")
    r = s.get(f"{site}/wp-json/wp/v2/{rb}", params={"per_page": 1, "context": "edit", "status": "publish"}, timeout=60)
    total = r.headers.get("X-WP-Total")
    keys = list(r.json()[0].keys()) if r.status_code == 200 and r.json() else []
    meta_keys = list((r.json()[0].get("meta") or {}).keys())[:12] if keys else []
    print(k, rb, r.status_code, total, [x for x in keys if x in ("lang", "translations", "template", "meta")], meta_keys)

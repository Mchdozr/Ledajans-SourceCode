from __future__ import annotations

import json
from pathlib import Path
import sys

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

# apply-elementor.py is not a valid module name; load by path.
import importlib.util

spec = importlib.util.spec_from_file_location(
    "apply_el", Path(__file__).resolve().parent / "apply-elementor.py"
)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

FEATURED = 5823  # cob-led-lobi.webp — OG for /led-ekran/


def main() -> None:
    site, user, pw = mod.load_env()
    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-HUB-IMG/1.0", "Content-Type": "application/json"}
    data = mod.load_el(site, auth, headers, 5001)
    n = mod.walk(data, mod.hub_fn)
    payload = {
        "featured_media": FEATURED,
        "meta": {
            "_elementor_data": json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            "_elementor_edit_mode": "builder",
        },
    }
    r = requests.post(
        f"{site}/wp-json/wp/v2/pages/5001",
        json=payload,
        auth=auth,
        headers=headers,
        timeout=120,
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"POST 5001 {r.status_code} {r.text[:300]}")
    print(f"OK id=5001 widgets_changed={n} featured={FEATURED}")
    c = requests.delete(f"{site}/wp-json/elementor/v1/cache", auth=auth, headers=headers, timeout=60)
    print("elementor_cache", c.status_code)


if __name__ == "__main__":
    main()

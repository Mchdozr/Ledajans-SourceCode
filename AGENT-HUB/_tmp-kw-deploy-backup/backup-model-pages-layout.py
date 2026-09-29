"""30 model sayfasının (rental 7, iç RGB 18, dış RGB 5 post) canlı Elementor/içerik yedeği."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from ledajans_model_layout import load_env  # noqa: E402

GROUPS = {
    "rental": ("pages", [5898, 5899, 5901, 5902, 5903, 5904, 5905]),
    "icrgb": ("pages", list(range(5919, 5937))),
    "disrgb": ("posts", [5913, 5914, 5915, 5916, 5917]),
}


def main() -> int:
    site, user, pw = load_env()
    out = Path(__file__).parent / f"layout-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    out.mkdir()
    index = []
    for group, (ptype, ids) in GROUPS.items():
        for pid in ids:
            r = requests.get(f"{site}/wp-json/wp/v2/{ptype}/{pid}", params={"context": "edit"}, auth=(user, pw),
                             headers={"User-Agent": "LEDAJANS-Layout-Backup/1.0"}, timeout=60)
            r.raise_for_status()
            j = r.json()
            (out / f"{group}-{pid}-{j['slug']}.json").write_text(json.dumps({
                "id": j["id"], "type": ptype, "slug": j["slug"], "status": j["status"], "link": j["link"],
                "title": j["title"]["raw"], "template": j.get("template"), "content": j["content"]["raw"],
                "meta": j.get("meta", {}),
            }, ensure_ascii=False, indent=1), encoding="utf-8")
            el = j.get("meta", {}).get("_elementor_data")
            index.append((group, ptype, pid, j["slug"], j["status"], j.get("template"), len(el or "")))
            print(group, ptype, pid, j["slug"], j["status"], j.get("template"), "el_len", len(el or ""))
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print("BACKUP", out, len(index))
    return 0 if len(index) == 30 else 1


if __name__ == "__main__":
    sys.exit(main())

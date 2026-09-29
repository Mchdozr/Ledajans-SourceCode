from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
items = json.loads((HERE / "raw.json").read_text(encoding="utf-8"))["result"]["value"]

for idx in (3, 10, 26):
    it = items[idx]
    h = it["html"]
    print("=====", it["slug"], len(h))
    print(h[:200].replace("\n", " "))
    for m in re.finditer(r'data-elementor-type="([^"]+)" data-elementor-id="(\d+)"', h):
        print("  doc", m.groups())
    for m in re.finditer(r"<(h1|h2|h3|h4)[^>]*>(.*?)</\1>", h, re.S):
        print("  ", m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()[:90])

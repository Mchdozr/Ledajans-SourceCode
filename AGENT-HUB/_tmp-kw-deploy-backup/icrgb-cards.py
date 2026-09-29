from __future__ import annotations

import re
from pathlib import Path

html = (Path(__file__).resolve().parent / "live-ic-mekan-rgb-panel.html").read_text(encoding="utf-8")
start = html.find("Mekan RGB LED Paneller")
seg = html[start:]
for m in re.finditer(r'href="(https://ledajans\.com/[^"]+)"', seg):
    h = m.group(1)
    if h.rstrip("/").count("/") != 3:
        continue
    ctx = re.sub(r"<[^>]+>", " ", seg[max(0, m.start() - 600) : m.end() + 300])
    ctx = re.sub(r"\s+", " ", ctx).strip()
    print(h, "||", ctx[-260:][:260])
    print()

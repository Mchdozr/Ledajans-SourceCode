from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "icrgb-5006"
OUT.mkdir(exist_ok=True)
data = json.loads((HERE / "page-5006-elementor-20260929-150133.json").read_text(encoding="utf-8"))


def walk(nodes, depth, top):
    for n in nodes:
        s = n.get("settings") or {}
        if n.get("elType") == "widget":
            html = s.get("html") or s.get("editor") or ""
            name = f"{top}-{n['id']}.html"
            (OUT / name).write_text(html, encoding="utf-8")
            first = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", html, flags=re.S)))[:110]
            print("  " * depth, n["widgetType"], name, len(html), first.encode("ascii", "replace").decode())
        else:
            print("  " * depth, n.get("elType"), n["id"], {k: s[k] for k in ("structure", "_column_size", "_inline_size", "layout") if k in s})
        walk(n.get("elements") or [], depth + 1, top)


for i, sec in enumerate(data):
    walk([sec], 0, str(i))

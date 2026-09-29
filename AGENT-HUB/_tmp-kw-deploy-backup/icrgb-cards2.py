from __future__ import annotations

import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
d = Path(__file__).resolve().parent / "icrgb-5006"
for f in ("4-f24e496.html", "5-c4d7dae.html", "6-739a6bc.html"):
    h = (d / f).read_text(encoding="utf-8")
    for m in re.finditer(r"<article[^>]*>(.*?)</article>", h, re.S):
        a = m.group(1)

        def g(p: str) -> str:
            r = re.search(p, a, re.S)
            return r.group(1).strip() if r else ""

        print(f[:1], "|", g(r'href="([^"]+)"'), "|", g(r'badge">([^<]*)'), "|", g(r'title">([^<]*)'), "|", g(r'spec">([^<]*)'))

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
data = json.loads((HERE / "dis-rgb-3795-elementor-20260929-150429.json").read_text(encoding="utf-8"))
out = HERE / "dis-rgb-3795-sections"
out.mkdir(exist_ok=True)


def walk(el, path):
    if el.get("elType") == "widget":
        s = el.get("settings", {})
        html = s.get("html") or s.get("editor") or ""
        heads = [re.sub(r"<[^>]+>|\s+", " ", h).strip()[:60] for h in re.findall(r"<h[1-4][^>]*>(.*?)</h[1-4]>", html, re.S)]
        print(path, el.get("widgetType"), el.get("id"), len(html), heads[:4])
        if html:
            (out / f"{path.replace('/', '-')}-{el.get('id')}.html").write_text(html, encoding="utf-8")
    for i, c in enumerate(el.get("elements", [])):
        walk(c, f"{path}/{i}")


for i, sec in enumerate(data):
    print("SECTION", i, sec.get("elType"), json.dumps(sec.get("settings"), ensure_ascii=False)[:200])
    walk(sec, str(i))

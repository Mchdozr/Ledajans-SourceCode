import re
import ssl
import urllib.request

url = "https://ledajans.com/cephe-led-ekran/"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 LEDAJANS-QA/1.0"})
ctx = ssl.create_default_context()
with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
    html = r.read().decode("utf-8", "replace")

lines = []
for token in ["ledajans-seo-article", "la-kw", "la-card", "la-hero"]:
    idxs = [m.start() for m in re.finditer(re.escape(token), html)]
    lines.append(f"{token} count {len(idxs)} idxs {idxs[:8]}")
    if idxs:
        i = idxs[0]
        snippet = html[max(0, i - 80) : i + 220].replace("\n", " ")
        lines.append(snippet)
        lines.append("---")

for m in re.finditer(r"<h1[\s\S]{0,280}", html, re.I):
    lines.append("H1CTX " + m.group(0).replace("\n", " ")[:280])

for m in re.finditer(r"<img[^>]+>", html):
    tag = m.group(0)
    if any(x in tag for x in ["cephe", "billboard", "istanbul-cephe", "webp"]):
        lines.append("IMG " + tag.replace("\n", " ")[:400])

path = r"c:\Users\kacma\Desktop\Ledajans-SourceCode\AGENT-HUB\_tmp-hero-frames\qa-6-dump.txt"
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote", path, "lines", len(lines))

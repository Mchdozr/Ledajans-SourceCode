#!/usr/bin/env python3
"""LEDAJANS yerel önizleme sunucusu — canlı siteye hiçbir şey göndermez.

Çalıştırma (depo kökünden, Windows'ta `python`):
    python ONIZLEME/server.py            # GÖRÜNÜM önizlemesi → http://localhost:8080/_onizleme/
    python ONIZLEME/server.py --seo      # arşivlenmiş SEO önizlemesi (title/meta/H1 vb.)
    python ONIZLEME/server.py 8090       # farklı port

Görünüm modu: sayfaların HTML'i ve metinleri 24.11.2026 canlı yedeğiyle BİREBİR aynıdır;
üzerine yalnızca ONIZLEME/gorunum/ klasöründeki CSS/JS katmanı eklenir.
Adresler: /<yol> önerilen görünüm · /_once/<yol> canlı yedeği (dokunulmamış) · /_onizleme/ panel
Görseller, CSS ve JS canlı siteden (ledajans.com) okunur; internet bağlantısı gerekir.
"""
from __future__ import annotations
import html as H
import json, re, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent
YEDEK = ROOT.parent / "YEDEK" / "2026-11-24"
GORUNUM = ROOT / "gorunum"
ARSIV = ROOT / "_arsiv-seo"
sys.path.insert(0, str(ROOT))
import build_preview as bp  # noqa: E402

SEO = "--seo" in sys.argv
ORIG = bp.load_originals()
A_HREF = re.compile(r'(<a\b[^>]*?\bhref=["\'])https?://(?:www\.)?ledajans\.com/', re.I)

if SEO:
    REPORT = json.loads((ARSIV / "degisiklikler.json").read_text(encoding="utf-8"))
    REDIRECTS = REPORT["yonlendirmeler"]
    CHANGED = {p["yol"]: len(p["degisiklikler"]) for p in REPORT["sayfalar"]}
else:
    REDIRECTS, CHANGED = {}, {}


def gorunum_manifest() -> dict:
    f = GORUNUM / "degisiklikler.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"degisiklikler": []}


def local_links(html: str, prefix: str = "/") -> str:
    return A_HREF.sub(lambda m: m.group(1) + prefix, html)


def norm(path: str) -> str:
    path = unquote(path)
    if not path.endswith("/") and "." not in path.rsplit("/", 1)[-1]:
        path += "/"
    return path


def overlay(path: str) -> str:
    """Görünüm katmanı: gorunum/degisiklikler.json'da bu sayfa için listelenen CSS/JS dosyaları
    (her istekte diskten okunur; dosyayı kaydedip sayfayı yenilemek yeterli)."""
    if SEO:
        return ""
    files = gorunum_manifest().get("sayfalar", {}).get(path, [])
    parts = []
    for fn in files:
        p = GORUNUM / fn
        if not p.exists():
            continue
        body = p.read_text(encoding="utf-8")
        if fn.endswith(".css"):
            parts.append(f'<style id="lj-gorunum-{H.escape(fn)}">\n{body}\n</style>')
        else:
            parts.append(f'<script id="lj-gorunum-{H.escape(fn)}">\n{body}\n</script>')
    return "\n".join(parts)


def banner(path: str, mode: str) -> str:
    if mode == "once":
        txt, bg = f'<b>ÖNCE</b> · 24.11.2026 canlı yedeği · <a href="{H.escape(path)}">Önerilen görünüm →</a>', "#5a6676"
    else:
        label = "SEO ÖNİZLEMESİ (arşiv)" if SEO else "GÖRÜNÜM ÖNİZLEMESİ"
        txt = (f'<b>{label} · CANLI DEĞİL</b> · <a href="/_once{H.escape(path)}">Canlı halini gör</a> · '
               f'<a href="/_onizleme/">Panel</a>')
        bg = "#1f4fd1"
    css = ("<style>#lj-bant{position:fixed;left:12px;bottom:12px;z-index:2147483647;background:" + bg +
           ";color:#fff;font:14px/1.4 system-ui,sans-serif;padding:10px 14px;border-radius:8px;box-shadow:0 4px 18px rgba(0,0,0,.25);"
           "max-width:calc(100vw - 24px)}#lj-bant a{color:#fff;text-decoration:underline}"
           ".lj-onizleme-giris{background:#fff8e1;border-left:4px solid #e0a100;padding:12px 14px;margin:12px 0}"
           ".lj-yer-tutucu{background:#ffd54f;padding:0 4px;border-radius:3px;font-weight:700}</style>")
    return css + f'<div id="lj-bant">{txt}</div>'


def inject(html: str, path: str, mode: str) -> str:
    add_head = overlay(path) if mode == "sonra" else ""
    if add_head:
        i = html.find("</head>")
        html = html[:i] + add_head + html[i:] if i != -1 else add_head + html
    b = banner(path, mode)
    i = html.rfind("</body>")
    return html[:i] + b + html[i:] if i != -1 else html + b


ROBOTS_ADD = "\n# OpenAI arama\nUser-agent: OAI-SearchBot\nAllow: /\n\nUser-agent: ChatGPT-User\nAllow: /\n\n# Anthropic\nUser-agent: ClaudeBot\nAllow: /\n"


class Handler(BaseHTTPRequestHandler):
    def send(self, code: int, body: str, ctype="text/html; charset=utf-8", headers=None):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Robots-Tag", "noindex")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        sys.stderr.write("  " + (fmt % args) + "\n")

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/_onizleme", "/_onizleme/"):
            panel = (ARSIV / "panel.html") if SEO else (ROOT / "panel.html")
            return self.send(200, panel.read_text(encoding="utf-8"))
        if path == "/_onizleme/degisiklikler.json":
            body = (ARSIV / "degisiklikler.json").read_text(encoding="utf-8") if SEO else json.dumps(gorunum_manifest(), ensure_ascii=False)
            return self.send(200, body, "application/json; charset=utf-8")
        if path == "/robots.txt":
            return self.send(200, (YEDEK / "robots.txt").read_text(encoding="utf-8") + (ROBOTS_ADD if SEO else ""), "text/plain; charset=utf-8")
        if path.endswith(".xml"):
            f = YEDEK / "sitemaps" / path.strip("/")
            return self.send(200, f.read_text(encoding="utf-8"), "application/xml; charset=utf-8") if f.exists() else self.send(404, "yok", "text/plain")
        if path == "/favicon.ico":
            return self.send(404, "", "text/plain")
        mode = "sonra"
        if path.startswith("/_once/"):
            mode, path = "once", path[len("/_once"):]
        path = norm(path)
        f = bp.file_of(path)
        if mode == "once":
            if f not in ORIG:
                return self.send(404, "Yedekte yok")
            return self.send(200, inject(local_links(ORIG[f], "/_once/"), path, "once"))
        if path in REDIRECTS:
            return self.send(301, "", headers={"Location": REDIRECTS[path]})
        if SEO and (ARSIV / "sonra" / f).exists():
            html = (ARSIV / "sonra" / f).read_text(encoding="utf-8")
        elif f in ORIG:
            html = ORIG[f]  # görünüm modu: HTML birebir canlı yedeği
        else:
            return self.send(404, f"<h1>404</h1><p>{H.escape(path)} yedekte yok.</p><p><a href='/_onizleme/'>Panel</a></p>")
        return self.send(200, inject(local_links(html), path, "sonra"))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    port = int(args[0]) if args else 8080
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    mode = "SEO (arşiv)" if SEO else "GÖRÜNÜM"
    print(f"Önizleme hazır — mod: {mode} (canlı siteye dokunmaz)\n  Panel:        http://localhost:{port}/_onizleme/\n"
          f"  Anasayfa:     http://localhost:{port}/\n  Canlı yedeği: http://localhost:{port}/_once/\nDurdurmak için Ctrl+C")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

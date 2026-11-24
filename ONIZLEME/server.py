#!/usr/bin/env python3
"""LEDAJANS SEO önizleme sunucusu — sadece yerelde çalışır, canlı siteye hiçbir şey göndermez.

Çalıştırma (depo kökünden):
    python3 ONIZLEME/build_preview.py      # (yalnızca değişiklik listesi güncellendiyse)
    python3 ONIZLEME/server.py             # → http://localhost:8080/_onizleme/

Adresler:
    /_onizleme/          değişiklik paneli (her sayfa için önce/sonra)
    /<yol>               önerilen hali (değişmeyen sayfalar yedekteki canlı hali + ortak alt metin düzeltmeleri)
    /_once/<yol>         24.11.2026 canlı yedeği, hiç değiştirilmemiş
    /robots.txt, /page-sitemap.xml, /portfolio-sitemap.xml   önerilen halleri
Görseller, CSS ve JS canlı siteden (ledajans.com) okunur; bu yüzden internet bağlantısı gerekir.
"""
from __future__ import annotations
import html as H
import json, re, sys, tarfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent
YEDEK = ROOT.parent / "YEDEK" / "2026-11-24"
SONRA = ROOT / "sonra"
sys.path.insert(0, str(ROOT))
import build_preview as bp  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

REPORT = json.loads((ROOT / "degisiklikler.json").read_text(encoding="utf-8"))
ORIG = bp.load_originals()
REDIRECTS = REPORT["yonlendirmeler"]
CHANGED = {p["yol"]: p for p in REPORT["sayfalar"]}
A_HREF = re.compile(r'(<a\b[^>]*?\bhref=["\'])https?://(?:www\.)?ledajans\.com/', re.I)


def local_links(html: str, prefix: str = "/") -> str:
    return A_HREF.sub(lambda m: m.group(1) + prefix, html)


def banner(path: str, mode: str) -> str:
    p = CHANGED.get(path)
    n = len(p["degisiklikler"]) if p else 0
    if mode == "once":
        txt = f'<b>ÖNCE</b> · 24.11.2026 canlı yedeği · <a href="{H.escape(path)}">Önerilen hali →</a>'
        bg = "#5a6676"
    else:
        extra = f' · {n} değişiklik' if p else ' · bu sayfada içerik değişikliği yok (sadece ortak alt metinler)'
        txt = (f'<b>ÖNİZLEME · CANLI DEĞİL</b>{extra} · <a href="/_once{H.escape(path)}">Canlı halini gör</a> · '
               f'<a href="/_onizleme/#{H.escape(path)}">Panel</a>')
        bg = "#1f4fd1"
    css = ("<style>.lj-onizleme-giris{background:#fff8e1;border-left:4px solid #e0a100;padding:12px 14px;margin:12px 0;"
           "font-size:16px;line-height:1.6;color:#222}.lj-onizleme-giris::before{content:'YENİ GİRİŞ PARAGRAFI (taslak) — ';"
           "font:600 11px monospace;color:#a35b00;letter-spacing:.05em}.lj-yer-tutucu{background:#ffd54f;padding:0 4px;border-radius:3px;"
           "font-weight:700}.lj-guncelleme{font-size:13px;color:#666;margin:4px 0 12px}"
           "#lj-bant{position:fixed;left:12px;bottom:12px;z-index:2147483647;background:" + bg + ";color:#fff;font:14px/1.4 system-ui,sans-serif;"
           "padding:10px 14px;border-radius:8px;box-shadow:0 4px 18px rgba(0,0,0,.25);max-width:calc(100vw - 24px)}#lj-bant a{color:#fff;text-decoration:underline}</style>")
    return css + f'<div id="lj-bant">{txt}</div>'


def inject(html: str, path: str, mode: str) -> str:
    b = banner(path, mode)
    i = html.rfind("</body>")
    return html[:i] + b + html[i:] if i != -1 else html + b


def norm(path: str) -> str:
    path = unquote(path)
    if not path.endswith("/") and "." not in path.rsplit("/", 1)[-1]:
        path += "/"
    return path


def sitemap(name: str) -> str | None:
    f = YEDEK / "sitemaps" / name
    if not f.exists():
        return None
    x = f.read_text(encoding="utf-8")
    if name == "portfolio-sitemap.xml":
        x = re.sub(r"<url>\s*<loc>https://ledajans\.com/case/[^<]*</loc>.*?</url>", "", x, flags=re.S)
    if name == "page-sitemap.xml":
        add = "".join(f"<url><loc>https://ledajans.com{p}</loc></url>" for p in ("/ankara-led-ekran/", "/izmir-led-ekran/"))
        x = x.replace("</urlset>", add + "</urlset>")
    return x


ROBOTS_ADD = """
# OpenAI arama ve kullanıcı istekleri (ChatGPT search)
User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

# Anthropic (Claude)
User-agent: ClaudeBot
Allow: /
"""


class Handler(BaseHTTPRequestHandler):
    def send(self, code: int, body: str, ctype="text/html; charset=utf-8", headers=None):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
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
            return self.send(200, (ROOT / "panel.html").read_text(encoding="utf-8"))
        if path == "/_onizleme/degisiklikler.json":
            return self.send(200, json.dumps(REPORT, ensure_ascii=False), "application/json; charset=utf-8")
        if path == "/robots.txt":
            return self.send(200, (YEDEK / "robots.txt").read_text(encoding="utf-8") + ROBOTS_ADD, "text/plain; charset=utf-8")
        if path.endswith(".xml"):
            x = sitemap(path.strip("/"))
            return self.send(200, x, "application/xml; charset=utf-8") if x else self.send(404, "yok", "text/plain")
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
        if (SONRA / f).exists():
            html = (SONRA / f).read_text(encoding="utf-8")
        elif f in ORIG:
            soup = BeautifulSoup(ORIG[f], "html.parser"); bp.fix_alts(soup); html = str(soup)
        else:
            return self.send(404, f"<h1>404</h1><p>{H.escape(path)} yedekte yok. Canlıda bu tür adresler anasayfaya yönleniyor; "
                                  "önerimiz gerçek 404 ya da en yakın konuya yönlendirme.</p><p><a href='/_onizleme/'>Panel</a></p>")
        return self.send(200, inject(local_links(html), path, "sonra"))


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Önizleme hazır (canlı siteye dokunmaz):\n  Panel:     http://localhost:{port}/_onizleme/\n"
          f"  Anasayfa:  http://localhost:{port}/\n  Canlı yedeği: http://localhost:{port}/_once/\nDurdurmak için Ctrl+C")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

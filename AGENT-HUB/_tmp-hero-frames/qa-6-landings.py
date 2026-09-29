import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

URLS = [
    "https://ledajans.com/cephe-led-ekran/",
    "https://ledajans.com/pitch-secim-rehberi/",
    "https://ledajans.com/gob-led-ekran/",
    "https://ledajans.com/fuar-led-ekran/",
    "https://ledajans.com/magaza-vitrin-led-ekran/",
    "https://ledajans.com/istanbul-led-ekran/",
]
BANNED = ["Basliksiz", "IcMekanRGBPanel", "DisMekanRGBPanel"]
UA = {"User-Agent": "Mozilla/5.0 LEDAJANS-QA/1.0", "Accept": "text/html,*/*"}
CTX = ssl.create_default_context()


def fetch(url, method="GET"):
    req = urllib.request.Request(url, headers=UA, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25, context=CTX) as r:
            body = r.read() if method == "GET" else b""
            return r.status, dict(r.headers), body, r.geturl()
    except urllib.error.HTTPError as e:
        body = e.read() if method == "GET" else b""
        return e.code, dict(e.headers), body, url
    except Exception as e:
        return 0, {}, str(e).encode(), url


def absurl(base, src):
    return urllib.parse.urljoin(base, src)


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.imgs = []
        self.h1s = []
        self.links = []
        self.robots = []
        self.canonical = []
        self.in_h1 = False
        self.h1_buf = []
        self.capture_ld = False
        self.jsonld_buf = []
        self.jsonlds = []
        self.widget_h1s = []
        self.in_widget = 0
        self.body_started = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class") or ""
        if "elementor-widget" in cls or "ledajans-seo" in cls or "la-kw" in cls:
            self.in_widget += 1
        if tag == "img":
            self.imgs.append(a)
        if tag == "h1":
            self.in_h1 = True
            self.h1_buf = []
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
        if tag == "meta":
            n = (a.get("name") or a.get("property") or "").lower()
            if n == "robots":
                self.robots.append(a.get("content", ""))
        if tag == "link" and (a.get("rel") or "").lower() == "canonical":
            self.canonical.append(a.get("href", ""))
        if tag == "script" and "ld+json" in (a.get("type") or "").lower():
            self.capture_ld = True
            self.jsonld_buf = []

    def handle_endtag(self, tag):
        if tag == "h1" and self.in_h1:
            self.in_h1 = False
            text = "".join(self.h1_buf).strip()
            self.h1s.append(text)
            if self.in_widget:
                self.widget_h1s.append(text)
        if tag == "script" and self.capture_ld:
            self.capture_ld = False
            self.jsonlds.append("".join(self.jsonld_buf))
        if tag == "div" and self.in_widget:
            self.in_widget = max(0, self.in_widget - 1)

    def handle_data(self, data):
        if self.in_h1:
            self.h1_buf.append(data)
        if self.capture_ld:
            self.jsonld_buf.append(data)


img_status_cache = {}
link_status_cache = {}
results = []

for url in URLS:
    rec = {"url": url, "issues": [], "warn": [], "ok": []}
    status, headers, body, final = fetch(url)
    rec["http"] = status
    rec["final"] = final
    print("FETCH", url, status, flush=True)
    if status != 200:
        rec["issues"].append(f"page HTTP {status}")
        rec["pass"] = False
        results.append(rec)
        continue
    html = body.decode("utf-8", "replace")
    rec["x_robots"] = headers.get("X-Robots-Tag") or headers.get("x-robots-tag") or ""

    banned_hits = [b for b in BANNED if b.lower() in html.lower()]
    rec["banned"] = banned_hits
    if banned_hits:
        rec["issues"].append("banned: " + ",".join(banned_hits))
    else:
        rec["ok"].append("banned filename yok")

    p = P()
    try:
        p.feed(html)
    except Exception as e:
        rec["warn"].append(f"html parse: {e}")

    robots_join = " | ".join(p.robots)
    rec["robots"] = robots_join
    rec["canonical"] = p.canonical[:2]
    rec["h1s"] = p.h1s
    rec["widget_h1s"] = p.widget_h1s
    if rec["x_robots"] and "noindex" in rec["x_robots"].lower():
        rec["issues"].append("X-Robots-Tag noindex")
    if any("noindex" in r.lower() for r in p.robots):
        rec["issues"].append("meta robots noindex: " + robots_join)
    else:
        rec["ok"].append("noindex yok")

    rec["h1_count"] = len(p.h1s)
    rec["widget_h1_count"] = len(p.widget_h1s)
    if rec["widget_h1_count"] == 1:
        rec["ok"].append("widget H1 1: " + p.widget_h1s[0][:80])
    elif rec["widget_h1_count"] == 0 and rec["h1_count"] == 1:
        rec["ok"].append("page H1 1: " + p.h1s[0][:80])
        rec["warn"].append("H1 widget class disinda")
    elif rec["h1_count"] == 0:
        rec["issues"].append("H1 yok")
    else:
        rec["issues"].append(
            f"H1 page={rec['h1_count']} widget={rec['widget_h1_count']}: "
            + " || ".join(h[:50] for h in p.h1s)
        )

    faq_ok = False
    faq_q = 0
    rec["ld_types"] = []
    for raw in p.jsonlds:
        try:
            data = json.loads(raw)
        except Exception:
            rec["warn"].append("json-ld parse fail")
            continue
        items = data if isinstance(data, list) else [data]
        graph = []
        for it in items:
            if isinstance(it, dict) and "@graph" in it:
                g = it["@graph"]
                graph.extend(g if isinstance(g, list) else [g])
            else:
                graph.append(it)
        for it in graph:
            if not isinstance(it, dict):
                continue
            t = it.get("@type")
            rec["ld_types"].append(t)
            types = t if isinstance(t, list) else [t]
            if any(x and "FAQ" in str(x) for x in types):
                faq_ok = True
                main = it.get("mainEntity") or []
                faq_q = len(main) if isinstance(main, list) else (1 if main else 0)
    rec["faq"] = faq_ok
    rec["faq_q"] = faq_q
    if faq_ok:
        rec["ok"].append(f"FAQ JSON-LD ({faq_q} S)")
    else:
        rec["issues"].append("FAQ JSON-LD yok")

    img_srcs = []
    for img in p.imgs:
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or ""
        srcset = img.get("srcset") or img.get("data-srcset") or ""
        if src:
            img_srcs.append(src)
        if srcset:
            for part in srcset.split(","):
                u = part.strip().split(" ")[0]
                if u:
                    img_srcs.append(u)
    rec["imgs"] = []
    seen_img = set()
    wp_ok = 0
    wp_fail = 0
    for src in img_srcs:
        full = absurl(url, src)
        if full in seen_img:
            continue
        seen_img.add(full)
        path = urllib.parse.urlparse(full).path
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        rec["imgs"].append({"src": full, "ext": ext})
        if any(b.lower() in full.lower() for b in BANNED):
            rec["issues"].append("banned img: " + path.split("/")[-1])
        if "ledajans.com" in full and "/wp-content/" in full:
            if full not in img_status_cache:
                st, _, _, _ = fetch(full, "HEAD")
                if st in (0, 405, 403):
                    st, hdrs, body2, _ = fetch(full, "GET")
                img_status_cache[full] = st
            st = img_status_cache[full]
            if st != 200:
                wp_fail += 1
                rec["issues"].append(f"img HTTP {st}: {path.split('/')[-1][:70]}")
            else:
                wp_ok += 1
                if ext in ("jpg", "jpeg", "png", "gif"):
                    rec["warn"].append(f"img not webp ({ext}): {path.split('/')[-1][:50]}")
    if wp_fail == 0:
        rec["ok"].append(f"wp img 200 ({wp_ok})")

    internal = []
    for href in p.links:
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        full = absurl(url, href).split("#")[0]
        host = urllib.parse.urlparse(full).netloc.lower()
        if "ledajans.com" in host and full not in internal:
            internal.append(full)
    rec["internal_n"] = len(internal)
    broken = []
    for href in internal:
        if href not in link_status_cache:
            st, _, _, _ = fetch(href, "HEAD")
            if st in (0, 405, 403):
                st, _, _, _ = fetch(href, "GET")
            link_status_cache[href] = st
        st = link_status_cache[href]
        if st not in (200, 301, 302):
            broken.append(f"{st} {href.replace('https://ledajans.com', '')[:80]}")
        elif st in (301, 302):
            rec["warn"].append(
                f"redirect {st}: {href.replace('https://ledajans.com', '')[:70]}"
            )
    if broken:
        rec["issues"].append("kirik link: " + "; ".join(broken[:8]))
    else:
        rec["ok"].append(f"ic link OK ({len(internal)})")

    rec["pass"] = len(rec["issues"]) == 0
    results.append(rec)
    print("DONE", url, "PASS" if rec["pass"] else "FAIL", rec["issues"], flush=True)

out = []
print("\n===== SUMMARY =====")
for rec in results:
    verdict = "PASS" if rec.get("pass") else "FAIL"
    notes = []
    if rec.get("issues"):
        notes.extend(rec["issues"])
    if rec.get("warn"):
        notes.append("WARN: " + "; ".join(rec["warn"][:6]))
    if rec.get("ok") and rec.get("pass"):
        notes.append(" | ".join(rec["ok"]))
    line = {
        "url": rec["url"],
        "verdict": verdict,
        "http": rec.get("http"),
        "h1s": rec.get("h1s"),
        "widget_h1s": rec.get("widget_h1s"),
        "faq": rec.get("faq"),
        "faq_q": rec.get("faq_q"),
        "ld_types": rec.get("ld_types"),
        "robots": rec.get("robots"),
        "banned": rec.get("banned"),
        "issues": rec.get("issues"),
        "warn": rec.get("warn"),
        "ok": rec.get("ok"),
        "img_exts": sorted({i["ext"] for i in rec.get("imgs", [])}),
        "img_files": [i["src"].split("/")[-1][:80] for i in rec.get("imgs", [])[:12]],
        "notes": " ; ".join(notes),
    }
    out.append(line)
    print("---")
    print(json.dumps(line, ensure_ascii=False, indent=2))

with open(
    r"c:\Users\kacma\Desktop\Ledajans-SourceCode\AGENT-HUB\_tmp-hero-frames\qa-6-landings.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("WROTE json")

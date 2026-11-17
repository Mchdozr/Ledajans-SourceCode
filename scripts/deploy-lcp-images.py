#!/usr/bin/env python3
"""LEDAJANS canli dagitim: mobil hiz yamasi v1.3.x + mobil gorsel varyantlari + bozuk 30 gorselin yenisi.

Ne yapar (sirayla):
  1. assets/replacements/wp-content/uploads/...  -> wp-content/uploads/ ayni yollar (bozuk/eksik gorseller)
  2. assets/ledajans-mobile/*                    -> wp-content/uploads/ledajans-mobile/
  3. wordpress-mobil-hiz-patch.php               -> mevcut mu-plugin dosyasinin YERINE (ledajans_mp_v11_active iceren)
Her yazilan dosyanin eskisi wp-content/uploads/ledajans-backup/<tag>/ altina yedeklenir.

Yontem: repodaki diger install-*.py betikleri gibi wp-admin'e giris + eklenti zip yukleme + REST ile etkinlestirme.
Gecici "LEDAJANS Deployer" eklentisi parca parca yuklenir, dosyalari kopyalar, sonra silinir.

Kullanim (repo kokunde, .env dolu):
  python scripts/deploy-lcp-images.py --dry-run      # canliya yazmaz; paket + kontrol
  python scripts/deploy-lcp-images.py                # dagit
  python scripts/deploy-lcp-images.py --rollback TAG # yedekten geri al
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile

try:
    import requests
except ImportError:  # pragma: no cover
    print("HATA: 'requests' gerekli -> pip install requests")
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "LEDAJANS-Deploy-LCP/1.0"
PLUGIN_DIR = "ledajans-deployer"
REST_PLUGIN = "ledajans-deployer/ledajans-deployer"
PATCH = os.path.join(ROOT, "wordpress-mobil-hiz-patch.php")
REPL = os.path.join(ROOT, "assets", "replacements", "wp-content", "uploads")
MOBILE = os.path.join(ROOT, "assets", "ledajans-mobile")
DEPLOYER = os.path.join(ROOT, "deploy", "ledajans-deployer.php")
MOBILE_UA = "Mozilla/5.0 (Linux; Android 11; moto g power (2022)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Mobile Safari/537.36"


def load_env() -> tuple[str, str, str]:
    data: dict[str, str] = {}
    path = os.path.join(ROOT, ".env")
    if os.path.isfile(path):
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    data[k.strip()] = v.strip().strip("\"'")
    site = (data.get("WP_SITE_URL") or os.environ.get("WP_SITE_URL") or "https://ledajans.com").rstrip("/")
    user = data.get("WP_USERNAME") or os.environ.get("WP_USERNAME") or ""
    pw = (data.get("WP_APP_PASSWORD") or os.environ.get("WP_APP_PASSWORD") or "").replace(" ", "")
    return site, user, pw


def collect() -> list[tuple[str, str]]:
    """(yerel dosya, hedef) listesi; mu-plugin en sonda."""
    items: list[tuple[str, str]] = []
    for base, _, files in os.walk(REPL):
        for fn in sorted(files):
            p = os.path.join(base, fn)
            rel = os.path.relpath(p, REPL).replace(os.sep, "/")
            items.append((p, "uploads/" + rel))
    items.sort(key=lambda x: x[1])
    for fn in sorted(os.listdir(MOBILE)):
        items.append((os.path.join(MOBILE, fn), "uploads/ledajans-mobile/" + fn))
    items.append((PATCH, "mu:auto"))
    return items


def plan_parts(items, limit: int) -> list[list[tuple[str, str]]]:
    parts: list[list[tuple[str, str]]] = []
    cur: list[tuple[str, str]] = []
    size = 0
    for p, d in items:
        s = os.path.getsize(p)
        if cur and size + s > limit:
            parts.append(cur)
            cur, size = [], 0
        cur.append((p, d))
        size += s
    if cur:
        parts.append(cur)
    return parts


def make_zip(files, tag: str, part: str, mode: str = "deploy") -> bytes:
    buf = io.BytesIO()
    manifest = {"tag": tag, "part": part, "mode": mode, "files": []}
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(DEPLOYER, f"{PLUGIN_DIR}/ledajans-deployer.php")
        for i, (p, d) in enumerate(files):
            ext = os.path.splitext(p)[1].lower()
            arc = f"payload/{i:03d}{'.txt' if ext == '.php' else ext}"
            zf.write(p, f"{PLUGIN_DIR}/{arc}", compress_type=zipfile.ZIP_STORED if ext in (".png", ".jpg", ".jpeg", ".webp") else zipfile.ZIP_DEFLATED)
            manifest["files"].append({"src": arc, "dest": d})
        zf.writestr(f"{PLUGIN_DIR}/manifest.json", json.dumps(manifest, ensure_ascii=False))
    return buf.getvalue()


def lint_patch() -> bool:
    raw = open(PATCH, "rb").read()
    for sig in (b"function ledajans_mp_v11_active", b"ledajans_mp_v13_optimize", b"GTM-WDLJTMSV"):
        if sig not in raw:
            print("HATA: yama imzasi yok:", sig.decode())
            return False
    if shutil.which("php"):
        r = subprocess.run(["php", "-l", PATCH], capture_output=True, text=True)
        print("php -l:", (r.stdout or r.stderr).strip())
        return r.returncode == 0
    print("UYARI: php yok, lint atlandi (repoda php -l temiz dogrulandi)")
    return True


def check_live_images(site: str, items) -> None:
    bad = 0
    for _, d in items:
        if not d.startswith("uploads/") or d.startswith("uploads/ledajans-mobile/"):
            continue
        url = f"{site}/wp-content/{d}"
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=30, allow_redirects=False)
            ok = r.status_code == 200 and r.headers.get("content-type", "").startswith("image/")
        except requests.RequestException:
            ok = False
        bad += 0 if ok else 1
    print(f"canli durum: {bad} hedef gorsel su an bozuk/eksik (301/yonlendirme veya image degil)")


def login(site, user, pw) -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    s.get(f"{site}/wp-login.php", timeout=30)
    r = s.post(f"{site}/wp-login.php", data={"log": user, "pwd": pw, "wp-submit": "Log In",
               "redirect_to": f"{site}/wp-admin/", "testcookie": "1"}, timeout=30, allow_redirects=True)
    if "wp-admin" not in r.url:
        print("HATA: wp-login basarisiz (kullanici/sifre .env)")
        sys.exit(1)
    return s


def upload_limit(s: requests.Session, site: str) -> int:
    page = s.get(f"{site}/wp-admin/plugin-install.php?tab=upload", timeout=30).text
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(MB|KB|GB)", re.sub("<[^>]+>", " ", page.split("pluginzip")[0][-4000:]), re.I)
    if not m:
        return 1_500_000
    n = float(m.group(1).replace(",", "."))
    mult = {"KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}[m.group(2).upper()]
    return int(n * mult)


def upload_zip(s, site, data: bytes) -> bool:
    page = s.get(f"{site}/wp-admin/plugin-install.php?tab=upload", timeout=30)
    nm = re.search(r'name="_wpnonce" value="([^"]+)"', page.text)
    if not nm:
        print("HATA: upload nonce yok")
        return False
    r = s.post(f"{site}/wp-admin/update.php?action=upload-plugin",
               data={"_wpnonce": nm.group(1), "_wp_http_referer": "/wp-admin/plugin-install.php?tab=upload",
                     "install-plugin-submit": "Install Now"},
               files={"pluginzip": ("ledajans-deployer.zip", data, "application/zip")}, timeout=300)
    ok = "Eklenti kuruldu" in r.text or "Plugin installed" in r.text or "Eklenti başarıyla kuruldu" in r.text
    if not ok:
        print("upload FAIL:", re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", r.text))[:300])
    return ok


def rest(method, site, auth, path, **kw):
    return requests.request(method, f"{site}/wp-json/{path}", auth=auth, headers={"User-Agent": UA}, timeout=120, **kw)


def remove_deployer(site, auth) -> None:
    rest("POST", site, auth, f"wp/v2/plugins/{REST_PLUGIN}", json={"status": "inactive"})
    rest("DELETE", site, auth, f"wp/v2/plugins/{REST_PLUGIN}")


def run_part(s, site, auth, data: bytes, label: str) -> dict | None:
    remove_deployer(site, auth)
    if not upload_zip(s, site, data):
        return None
    r = rest("POST", site, auth, f"wp/v2/plugins/{REST_PLUGIN}", json={"status": "active"})
    if r.status_code not in (200, 201):
        print(f"{label}: etkinlestirme HATA {r.status_code} {r.text[:200]}")
        remove_deployer(site, auth)
        return None
    res = rest("GET", site, auth, "ledajans-deploy/v1/result").json()
    remove_deployer(site, auth)
    return res


def verify(site: str, items) -> bool:
    ok = True
    for path in ("/", "/dis-mekan-led-ekran/", "/projeler/", "/kontrol-kartlari/"):
        r = requests.get(site + path, headers={"User-Agent": MOBILE_UA}, timeout=60)
        html = r.text
        fatal = "critical error" in html.lower() or "kritik bir hata" in html.lower()
        roboto = "google-fonts/css/roboto.css" in html
        pre = len(re.findall(r'<link[^>]+rel="preload"[^>]+as="image"', html))
        print(f"  {path}: HTTP {r.status_code} kritik_hata={fatal} roboto_301_linki={roboto} image_preload={pre}")
        ok = ok and r.status_code == 200 and not fatal
    d = requests.get(site + "/", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/136.0 Safari/537.36"}, timeout=60)
    print(f"  masaustu /: HTTP {d.status_code} (yama masaustunde no-op)")
    bad = []
    for p, dpath in items:
        if not dpath.startswith("uploads/"):
            continue
        r = requests.get(f"{site}/wp-content/{dpath}", headers={"User-Agent": UA}, timeout=60, allow_redirects=False)
        if r.status_code != 200 or hashlib.md5(r.content).hexdigest() != hashlib.md5(open(p, "rb").read()).hexdigest():
            bad.append((dpath, r.status_code))
    print(f"  gorseller: {len([1 for _, d in items if d.startswith('uploads/')]) - len(bad)} dogru, {len(bad)} sorunlu")
    for b in bad[:10]:
        print("   -", b)
    return ok and not bad


def main() -> int:
    ap = argparse.ArgumentParser(description="LEDAJANS canli dagitim (yama + gorseller)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--rollback", metavar="TAG")
    args = ap.parse_args()

    site, user, pw = load_env()
    items = collect()
    total = sum(os.path.getsize(p) for p, _ in items)
    print(f"site: {site}\ndosya: {len(items)} ({total // 1024} KiB) — {sum(1 for _, d in items if d.startswith('uploads/') and 'ledajans-mobile' not in d)} gorsel, "
          f"{sum(1 for _, d in items if 'ledajans-mobile' in d)} mobil varyant, 1 mu-plugin")
    if not lint_patch():
        return 1

    if args.dry_run:
        parts = plan_parts(items, 1_500_000)
        for i, p in enumerate(parts, 1):
            print(f"  parca {i}: {len(p)} dosya, {sum(os.path.getsize(x) for x, _ in p) // 1024} KiB")
        check_live_images(site, items)
        print("hedefler:")
        for _, d in items:
            print("  ", d)
        print("DRY-RUN OK — canliya yazilmadi. Gercek dagitim icin --dry-run olmadan calistirin.")
        return 0

    if not user or not pw:
        print("HATA: .env icinde WP_USERNAME / WP_APP_PASSWORD gerekli")
        return 1
    auth = (user, pw)
    me = rest("GET", site, auth, "wp/v2/users/me", params={"context": "edit"})
    if me.status_code != 200:
        print("HATA: REST yetki", me.status_code)
        return 1
    plugins = rest("GET", site, auth, "wp/v2/plugins").json()
    for p in plugins if isinstance(plugins, list) else []:
        if p.get("name") == "LEDAJANS Mobile Perf" and p.get("status") == "active":
            print("HATA: 'LEDAJANS Mobile Perf' normal eklenti olarak da aktif; once onu devre disi birakin (cakisma).")
            return 1
    s = login(site, user, pw)

    if args.rollback:
        res = run_part(s, site, auth, make_zip([], args.rollback, "rollback", "rollback"), "rollback")
        print(json.dumps(res, ensure_ascii=False, indent=1)[:2000])
        return 0 if res and not res.get("err") else 1

    limit = max(400_000, min(int(upload_limit(s, site) * 0.8), 6_000_000))
    parts = plan_parts(items, limit)
    tag = time.strftime("lcp-%Y%m%d-%H%M%S")
    print(f"etiket: {tag}  yukleme limiti ~{limit // 1024} KiB/parca  parca: {len(parts)}")
    for i, p in enumerate(parts, 1):
        res = run_part(s, site, auth, make_zip(p, tag, f"{i}/{len(parts)}"), f"parca {i}")
        if res is None:
            print(f"DUR: parca {i} basarisiz. Geri almak icin: python scripts/deploy-lcp-images.py --rollback {tag}")
            return 1
        print(f"parca {i}/{len(parts)}: yazildi {len(res.get('ok', []))}, yedek {len(res.get('backup', []))}, hata {len(res.get('err', []))}")
        for e in res.get("err", []):
            print("   HATA:", e)
        if res.get("err"):
            print(f"DUR. Geri almak icin: python scripts/deploy-lcp-images.py --rollback {tag}")
            return 1
    print("dogrulama (nginx cache ~5 dk olabilir):")
    good = verify(site, items)
    print("SONUC:", "OK" if good else "KONTROL GEREKLI", f"| geri alma: python scripts/deploy-lcp-images.py --rollback {tag}")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())

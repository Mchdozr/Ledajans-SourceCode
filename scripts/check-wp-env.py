"""WP .env yükleme kontrolü — şifre değerini yazdırmaz."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(ROOT, ".env")

if not os.path.isfile(env_path):
    print("NO_ENV_FILE")
    sys.exit(1)

with open(env_path, encoding="utf-8-sig") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value

user = os.environ.get("WP_USERNAME", "")
pw = os.environ.get("WP_APP_PASSWORD", "").replace(" ", "")
print(f"username={user!r}")
print(f"password_len={len(pw)}")
if not pw:
    print("ERROR: WP_APP_PASSWORD bos")
    sys.exit(1)
if pw.startswith('"') or pw.endswith('"'):
    print("WARN: tirnak karakteri sifrede kalmis olabilir")

try:
    import requests
except ImportError:
    print("requests yok")
    sys.exit(1)

site = os.environ.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Check"}
r0 = requests.get(f"{site}/wp-json/", timeout=30, headers=headers)
print(f"wp-json_public={r0.status_code}")

url = f"{site}/wp-json/wp/v2/users/me"
r = requests.get(url, auth=(user, pw), timeout=30, headers=headers)
print(f"http_status={r.status_code}")
if r.status_code != 200:
    try:
        msg = r.json().get("message", r.text[:120])
    except Exception:
        msg = r.text[:120]
    print(f"message={msg}")
    if r.status_code == 403 and "nginx" in (r.text or "").lower():
        print("hint=Basic Auth engelli; scripts/WP-REST-403-FIX.md")
        print("detail=python scripts/diagnose-wp-rest.py")

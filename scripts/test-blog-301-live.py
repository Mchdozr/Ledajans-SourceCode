import requests

TESTS = [
    ("https://ledajans.com/led-ekran-nasil-secilir-rehber/", "/blog/led-ekran-nasil-secilir-rehber"),
    ("https://ledajans.com/led-ekran-fiyatlari-2026/", "/blog/led-ekran-fiyatlari-2026"),
    ("https://ledajans.com/ic-mekan-led-ekran-fiyatlari-2026/", "/blog/ic-mekan-led-ekran-fiyatlari-2026"),
    ("https://ledajans.com/blog/led-ekran-nasil-secilir-rehber/", None),
]
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

print("redirect test:")
ok_count = 0
for url, expect in TESTS:
    r = requests.get(url, allow_redirects=False, timeout=25, headers=H)
    loc = r.headers.get("Location", "")
    path = url.replace("https://ledajans.com", "")
    if r.status_code in (301, 302, 307, 308) and expect and expect in loc:
        print(f"PASS {r.status_code} {path}")
        print(f"     -> {loc}")
        ok_count += 1
    elif r.status_code == 200 and "/blog/" in path:
        print(f"PASS {r.status_code} {path} (yeni URL)")
        ok_count += 1
    else:
        print(f"FAIL {r.status_code} {path}")
        if loc:
            print(f"     -> {loc}")

r2 = requests.get(TESTS[0][0], allow_redirects=True, timeout=25, headers=H)
print(f"\nchain: {r2.status_code} {r2.url}")
print(f"score: {ok_count}/{len(TESTS)}")

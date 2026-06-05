from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPLACEMENTS = [
    ("https://ledajans.com/power-supply/", "https://ledajans.com/guc-kaynaklari/"),
    ("http://ledajans.com/power-supply/", "https://ledajans.com/guc-kaynaklari/"),
    ('href="http://ledajans.com"', 'href="https://ledajans.com/"'),
    ("href='http://ledajans.com'", "href='https://ledajans.com/'"),
    ("https://www.ledajans.com", "https://ledajans.com"),
    # Canonical para sayfalar (long-tail iç link planı)
    ("https://ledajans.com/urunler/ic-mekan-led-ekran/", "https://ledajans.com/ic-mekan-led-ekran/"),
    ("https://ledajans.com/urunler/dis-mekan-led-ekran/", "https://ledajans.com/dis-mekan-led-ekran/"),
    ("https://ledajans.com/urunler/rental-led-ekran/", "https://ledajans.com/rental-ekran/"),
    ("https://ledajans.com/urunler/cob-smart-screen/", "https://ledajans.com/cob-ekran/"),
    ("https://ledajans.com/urunler/led-panel/", "https://ledajans.com/led-ekran/"),
    ("https://ledajans.com/urunler/", "https://ledajans.com/led-ekran/"),
    ("/urunler/ic-mekan-led-ekran/", "/ic-mekan-led-ekran/"),
    ("/urunler/dis-mekan-led-ekran/", "/dis-mekan-led-ekran/"),
    ("/urunler/rental-led-ekran/", "/rental-ekran/"),
    ("/urunler/cob-smart-screen/", "/cob-ekran/"),
]

changed = 0
for path in ROOT.rglob("*.html"):
    if "AGENT-HUB" in path.parts:
        continue
    text = path.read_text(encoding="utf-8")
    new = text
    for old, val in REPLACEMENTS:
        new = new.replace(old, val)
    if new != text:
        path.write_text(new, encoding="utf-8")
        changed += 1
print(f"files_changed={changed}")

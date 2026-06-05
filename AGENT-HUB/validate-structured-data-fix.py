import json
import re
from pathlib import Path

FILES = [
    Path("SEO-Icerik-Widgets/schema/organization-schema.html"),
    Path("Urunlerimiz/Dis-Mekan-Led-Ekran/urun-ozellikleri.html"),
    Path("Urunlerimiz/Ic-Mekan-Led-Ekran/urun-ozellikleri.html"),
    Path("Urunlerimiz/Rental-Ekran/urun-ozellikleri.html"),
]

count = 0
for path in FILES:
    html = path.read_text(encoding="utf-8")
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>',
        html,
        flags=re.S,
    )
    if not blocks:
        raise SystemExit(f"No JSON-LD block: {path}")
    for block in blocks:
        json.loads(block)
        count += 1

print(f"json_ld_blocks_ok={count}")

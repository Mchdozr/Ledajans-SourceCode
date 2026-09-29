from __future__ import annotations

from pathlib import Path

from PIL import Image

SRC = Path(r"C:\Users\kacma\.cursor\projects\c-Users-kacma-Desktop-Ledajans-SourceCode\assets")
DST = Path(__file__).resolve().parent / "media"
DST.mkdir(parents=True, exist_ok=True)

KEEP = [
    "cephe-led-ekran-bina.png",
    "led-billboard-otoyol.png",
    "istanbul-cephe-led-kurulum.png",
    "pitch-dis-mekan-p10.png",
    "rental-led-sahne.png",
    "gob-led-yuzey.png",
    "cob-led-lobi.png",
    "fuar-led-stand.png",
    "fuar-fuaye-led.png",
    "magaza-vitrin-led.png",
    "avm-led-ekran.png",
]

for name in KEEP:
    src = SRC / name
    im = Image.open(src).convert("RGB")
    im = im.resize((1280, 720), Image.Resampling.LANCZOS)
    out = DST / (src.stem + ".webp")
    im.save(out, "WEBP", quality=78, method=6)
    print(f"{out.name} {out.stat().st_size}")

from __future__ import annotations

from pathlib import Path

from PIL import Image

SRC = Path(r"C:\Users\kacma\.cursor\projects\c-Users-kacma-Desktop-Ledajans-SourceCode\assets")
DST = Path(__file__).resolve().parent / "media"
DST.mkdir(parents=True, exist_ok=True)
for name in ("ic-mekan-rgb-panel.png", "dis-mekan-rgb-panel.png"):
    im = Image.open(SRC / name).convert("RGB").resize((1280, 720), Image.Resampling.LANCZOS)
    out = DST / (Path(name).stem + ".webp")
    im.save(out, "WEBP", quality=78, method=6)
    print(out.name, out.stat().st_size)

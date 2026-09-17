#!/usr/bin/env python3
"""3x3 kontakt şeridi → frame-01.webp … frame-09.webp (scroll sequence)."""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Anasayfa" / "assets" / "kabin-explode"
TARGET = (1120, 630)


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if src is None or not src.is_file():
        print("Kullanim: split-kabin-explode.py <kontakt-seridi.png>")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB")
    arr = np.array(im)
    h, w = arr.shape[:2]
    for r in range(3):
        for c in range(3):
            n = r * 3 + c + 1
            x0, y0 = int(c * w / 3), int(r * h / 3)
            x1, y1 = int((c + 1) * w / 3), int((r + 1) * h / 3)
            cell = arr[y0:y1, x0:x1].copy()
            ch, cw = cell.shape[:2]
            cell[int(ch * 0.82):, :int(cw * 0.16)] = 0
            dest = OUT / f"frame-{n:02d}.webp"
            Image.fromarray(cell).resize(TARGET, Image.Resampling.LANCZOS).save(
                dest, "WEBP", quality=88, method=6
            )
            print(f"frame-{n:02d}: {dest.stat().st_size // 1024}KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

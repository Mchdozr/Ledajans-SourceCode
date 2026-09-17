#!/usr/bin/env python3
"""Flattened explode render → transparent WebP katmanları."""
from __future__ import annotations

from collections import deque
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Anasayfa" / "assets" / "kabin-explode"
NAMES = ("maske", "modul", "pcb", "kabin")
PAD = 16


def components(mask: np.ndarray) -> list[tuple[int, int, int, int]]:
    small = mask[::4, ::4]
    h, w = small.shape
    visited = np.zeros_like(small, dtype=np.uint8)
    raw: list[tuple[int, int, int, int, int]] = []
    for y in range(h):
        for x in range(w):
            if not small[y, x] or visited[y, x]:
                continue
            q = deque([(y, x)])
            visited[y, x] = 1
            minx = maxx = x
            miny = maxy = y
            n = 0
            while q:
                cy, cx = q.popleft()
                n += 1
                minx = min(minx, cx)
                maxx = max(maxx, cx)
                miny = min(miny, cy)
                maxy = max(maxy, cy)
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < h and 0 <= nx < w and small[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = 1
                        q.append((ny, nx))
            if n > 40:
                raw.append((n, minx * 4, miny * 4, (maxx + 1) * 4, (maxy + 1) * 4))
    raw.sort(key=lambda t: t[1])
    return [(a, b, c, d) for _, a, b, c, d in raw]


def refine(mask: np.ndarray, box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    h, w = mask.shape
    x0, y0, x1, y1 = box
    x0 = max(0, x0 - 8)
    y0 = max(0, y0 - 8)
    x1 = min(w, x1 + 8)
    y1 = min(h, y1 + 8)
    sub = mask[y0:y1, x0:x1]
    ys = np.where(np.any(sub, axis=1))[0]
    xs = np.where(np.any(sub, axis=0))[0]
    return (
        max(0, x0 + int(xs[0]) - PAD),
        max(0, y0 + int(ys[0]) - PAD),
        min(w, x0 + int(xs[-1]) + 1 + PAD),
        min(h, y0 + int(ys[-1]) + 1 + PAD),
    )


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT / "source.png"
    if not src.is_file():
        print(f"HATA: kaynak yok: {src}")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGBA")
    arr = np.array(im)
    mask = arr[:, :, 3] > 20
    boxes = components(mask)
    if len(boxes) != 4:
        print(f"HATA: 4 parça beklenirdi, {len(boxes)} bulundu")
        return 1
    for box, name in zip(boxes, NAMES):
        x0, y0, x1, y1 = refine(mask, box)
        dest = OUT / f"part-{name}.webp"
        im.crop((x0, y0, x1, y1)).save(dest, "WEBP", quality=86, method=6)
        print(f"{name}: ({x0},{y0})-({x1},{y1}) {dest.stat().st_size // 1024}KB")
    full = OUT / "exploded-full.webp"
    im.save(full, "WEBP", quality=82, method=6)
    print(f"full: {full.stat().st_size // 1024}KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from pathlib import Path

import requests
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MEDIA = HERE / "media"
MAP = HERE / "media-urls.json"
ASSETS = Path(r"C:\Users\kacma\.cursor\projects\c-Users-kacma-Desktop-Ledajans-SourceCode\assets")
NAME = "ic-mekan-led-ekran.webp"
ALT = "İç mekan LED ekran"
SUFFIX = "image-0304720c-8c33-4b62-9cf6-c89df7a32665.png"


def find_src() -> Path:
    matches = list(ASSETS.glob(f"*{SUFFIX}"))
    if not matches:
        raise FileNotFoundError(SUFFIX)
    matches.sort(key=lambda p: (len(p.name), p.stat().st_mtime), reverse=True)
    return matches[0]


def main() -> None:
    env: dict[str, str] = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip("\"'")
    site = env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
    auth = (env["WP_USERNAME"], env["WP_APP_PASSWORD"].replace(" ", ""))
    src = find_src()
    dst = MEDIA / NAME
    im = Image.open(src).convert("RGB")
    print("src", src.name, im.size)
    fitted = ImageOps.fit(im, (1280, 720), method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))
    dst.parent.mkdir(parents=True, exist_ok=True)
    fitted.save(dst, "WEBP", quality=78, method=6)
    print("dst", dst.name, dst.stat().st_size)
    with dst.open("rb") as fh:
        r = requests.post(
            f"{site}/wp-json/wp/v2/media",
            auth=auth,
            headers={
                "User-Agent": "LEDAJANS-IC-MEKAN/1.0",
                "Content-Disposition": f'attachment; filename="{NAME}"',
            },
            files={"file": (NAME, fh, "image/webp")},
            data={"alt_text": ALT, "title": ALT},
            timeout=180,
        )
    print(NAME, r.status_code)
    if r.status_code not in (200, 201):
        print("ERR", r.text[:300])
        raise SystemExit(1)
    js = r.json()
    url = js.get("source_url") or ""
    mid = str(js.get("id") or "")
    print(" ", url, "id", mid)
    existing = json.loads(MAP.read_text(encoding="utf-8")) if MAP.exists() else {}
    existing[NAME] = url
    existing[NAME + ":id"] = mid
    MAP.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

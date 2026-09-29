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

JOBS = [
    (
        "magaza-vitrin-led-cadde.webp",
        "Mağaza vitrin LED ekran",
        "image-2d95305a-5541-4afe-a0f1-39a37a8befb4.jpg",
    ),
    (
        "cephe-led-ekran.webp",
        "Cephe LED ekran",
        "image-d83582b7-5312-4b8e-a59a-366404a4ed5c.jpg",
    ),
]


def find_src(suffix: str) -> Path:
    matches = list(ASSETS.glob(f"*{suffix}"))
    if not matches:
        raise FileNotFoundError(suffix)
    matches.sort(key=lambda p: (len(p.name), p.stat().st_mtime), reverse=True)
    return matches[0]


def to_webp(src: Path, dst: Path) -> None:
    im = Image.open(src).convert("RGB")
    print("src", src.name, im.size)
    fitted = ImageOps.fit(im, (1280, 720), method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))
    dst.parent.mkdir(parents=True, exist_ok=True)
    fitted.save(dst, "WEBP", quality=78, method=6)
    print("dst", dst.name, dst.stat().st_size, fitted.size)


def load_env() -> tuple[str, str, str]:
    env: dict[str, str] = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip("\"'")
    return (
        env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/"),
        env["WP_USERNAME"],
        env["WP_APP_PASSWORD"].replace(" ", ""),
    )


def main() -> None:
    site, user, pw = load_env()
    auth = (user, pw)
    existing = json.loads(MAP.read_text(encoding="utf-8")) if MAP.exists() else {}
    for name, alt, suffix in JOBS:
        src = find_src(suffix)
        dst = MEDIA / name
        to_webp(src, dst)
        with dst.open("rb") as fh:
            r = requests.post(
                f"{site}/wp-json/wp/v2/media",
                auth=auth,
                headers={
                    "User-Agent": "LEDAJANS-USER-MEDIA/1.0",
                    "Content-Disposition": f'attachment; filename="{name}"',
                },
                files={"file": (name, fh, "image/webp")},
                data={"alt_text": alt, "title": alt},
                timeout=180,
            )
        print(name, r.status_code, dst.stat().st_size)
        if r.status_code not in (200, 201):
            print("ERR", r.text[:300])
            raise SystemExit(1)
        js = r.json()
        url = js.get("source_url") or ""
        mid = str(js.get("id") or "")
        print(" ", url, "id", mid)
        existing[name] = url
        existing[name + ":id"] = mid
    MAP.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", MAP.name)


if __name__ == "__main__":
    main()

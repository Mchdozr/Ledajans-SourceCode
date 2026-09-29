from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]


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
    headers = {"User-Agent": "LEDAJANS-EL-CHECK/1.0"}
    for pid in (4969, 4987, 5804, 4956, 5001):
        r = requests.get(
            f"{site}/wp-json/wp/v2/pages/{pid}",
            params={"context": "edit"},
            auth=auth,
            headers=headers,
            timeout=60,
        )
        print("pid", pid, r.status_code)
        js = r.json()
        meta = js.get("meta") or {}
        raw = meta.get("_elementor_data")
        mode = meta.get("_elementor_edit_mode")
        print("  mode", mode, "el", type(raw).__name__, "len", len(raw) if isinstance(raw, str) else raw)
        content = js.get("content")
        if isinstance(content, dict):
            rawc = content.get("raw") or ""
            print("  content.raw", len(rawc), "cadde-1", "cadde-1.webp" in rawc, "cephe-led-ekran.webp", "cephe-led-ekran.webp" in rawc)


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "live-projeler-widgets.json"


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


def walk(nodes, found: list) -> None:
    if isinstance(nodes, list):
        for n in nodes:
            walk(n, found)
        return
    if not isinstance(nodes, dict):
        return
    settings = nodes.get("settings") or {}
    for key in ("html", "editor"):
        val = settings.get(key)
        if isinstance(val, str) and "ledajans-project-card" in val:
            found.append(
                {
                    "id": nodes.get("id"),
                    "widgetType": nodes.get("widgetType"),
                    "key": key,
                    "len": len(val),
                    "head": val[:180].replace("\n", " "),
                    "titles": val.count("data-title="),
                    "has_kure": "K\u00fcre" in val or "kure" in val.lower(),
                    "has_vitrin": "Ma\u011faza vitrin LED ekran" in val,
                }
            )
    for key in ("elements", "content"):
        if key in nodes:
            walk(nodes[key], found)


def main() -> None:
    site, user, pw = load_env()
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages",
        params={"slug": "projeler", "context": "edit"},
        auth=(user, pw.replace(" ", "")),
        headers={"User-Agent": "LEDAJANS-CHECK/1.0"},
        timeout=60,
    )
    r.raise_for_status()
    page = r.json()[0]
    raw = (page.get("meta") or {}).get("_elementor_data")
    data = json.loads(raw) if isinstance(raw, str) else raw
    found: list = []
    walk(data, found)
    OUT.write_text(json.dumps(found, ensure_ascii=False, indent=2), encoding="utf-8")
    print("widgets", len(found))
    for item in found:
        print(item)


if __name__ == "__main__":
    main()

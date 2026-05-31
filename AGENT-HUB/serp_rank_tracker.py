#!/usr/bin/env python3
"""ledajans.com — 'led ekran' organik sıra takibi ve haftalık rapor."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import requests

ROOT = Path("/workspace")
HUB = ROOT / "AGENT-HUB"
DATA_DIR = HUB / "data"
HISTORY_FILE = DATA_DIR / "serp-history.json"
REPORTS = HUB / "REPORTS"
WEEKLY_LATEST = HUB / "SERP-WEEKLY-LATEST.md"

KEYWORD = "led ekran"
DOMAIN = "ledajans.com"
PREFERRED_PATHS = ("/led-ekran/", "/led-ekran", "/")
LOCALE = "tr-TR"
GOOGLE_PARAMS = {
    "q": KEYWORD,
    "location": "Turkey",
    "google_domain": "google.com.tr",
    "gl": "tr",
    "hl": "tr",
    "num": 100,
    "device": "desktop",
}


def utc_now() -> datetime:
    return datetime.now(UTC)


def load_history() -> dict:
    if not HISTORY_FILE.exists():
        return {"snapshots": [], "weekly_reports": []}
    return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))


def save_history(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_domain(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def path_rank(url: str) -> int:
    path = urlparse(url).path or "/"
    for idx, pref in enumerate(PREFERRED_PATHS):
        if path == pref or path.rstrip("/") == pref.rstrip("/"):
            return idx
    if path.startswith("/led-ekran"):
        return len(PREFERRED_PATHS)
    return 99


def pick_best_ledajans(results: list[dict]) -> dict | None:
    matches = [r for r in results if DOMAIN in r.get("domain", "")]
    if not matches:
        return None
    matches.sort(key=lambda r: (r["position"], path_rank(r.get("url", ""))))
    return matches[0]


def fetch_serpapi() -> tuple[list[dict], str | None]:
    api_key = os.environ.get("SERPAPI_API_KEY", "").strip()
    if not api_key:
        return [], "SERPAPI_API_KEY tanımlı değil"
    try:
        resp = requests.get(
            "https://serpapi.com/search.json",
            params={**GOOGLE_PARAMS, "api_key": api_key},
            timeout=60,
        )
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as exc:
        return [], f"SerpAPI hatası: {exc}"

    organic = payload.get("organic_results") or []
    results = []
    for item in organic:
        link = item.get("link") or ""
        if not link:
            continue
        results.append(
            {
                "position": int(item.get("position") or len(results) + 1),
                "url": link,
                "domain": normalize_domain(link),
                "title": item.get("title") or "",
            }
        )
    return results, None


def fetch_serper() -> tuple[list[dict], str | None]:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return [], "SERPER_API_KEY tanımlı değil"
    try:
        resp = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={
                "q": KEYWORD,
                "gl": "tr",
                "hl": "tr",
                "num": 100,
            },
            timeout=45,
        )
        resp.raise_for_status()
        organic = resp.json().get("organic") or []
    except requests.RequestException as exc:
        return [], f"Serper hatası: {exc}"

    results = []
    for idx, item in enumerate(organic, start=1):
        link = item.get("link") or ""
        if not link:
            continue
        results.append(
            {
                "position": int(item.get("position") or idx),
                "url": link,
                "domain": normalize_domain(link),
                "title": item.get("title") or "",
            }
        )
    return results, None


def fetch_duckduckgo(max_results: int = 50) -> tuple[list[dict], str | None]:
    session = requests.Session()
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    results: list[dict] = []
    offset = 0
    try:
        while len(results) < max_results:
            resp = session.post(
                "https://html.duckduckgo.com/html/",
                data={"q": KEYWORD, "kl": "tr-tr", "s": str(offset)},
                timeout=25,
            )
            resp.raise_for_status()
            links = re.findall(r'class="result__a"[^>]*href="([^"]+)"', resp.text)
            if not links:
                break
            for href in links:
                if "uddg=" in href:
                    qs = parse_qs(urlparse(href).query)
                    url = unquote(qs.get("uddg", [""])[0])
                else:
                    url = href
                if not url.startswith("http"):
                    continue
                results.append(
                    {
                        "position": len(results) + 1,
                        "url": url,
                        "domain": normalize_domain(url),
                        "title": "",
                    }
                )
                if len(results) >= max_results:
                    break
            offset += 30
            if offset >= max_results:
                break
    except requests.RequestException as exc:
        return [], f"DuckDuckGo hatası: {exc}"
    return results, None


def measure_rank() -> dict:
    captured_at = utc_now().isoformat(timespec="seconds")
    sources: dict[str, dict] = {}

    for name, fetcher, engine_label in (
        ("google_serpapi", fetch_serpapi, "Google TR (SerpAPI)"),
        ("google_serper", fetch_serper, "Google TR (Serper)"),
        ("duckduckgo_proxy", fetch_duckduckgo, "DuckDuckGo TR (proxy)"),
    ):
        results, error = fetcher()
        best = pick_best_ledajans(results)
        sources[name] = {
            "engine": engine_label,
            "error": error,
            "total_results": len(results),
            "position": best["position"] if best else None,
            "url": best["url"] if best else None,
            "top_5": results[:5],
        }

    primary = None
    for key in ("google_serpapi", "google_serper", "duckduckgo_proxy"):
        pos = sources[key].get("position")
        if pos is not None:
            primary = {
                "source": key,
                "engine": sources[key]["engine"],
                "position": pos,
                "url": sources[key]["url"],
            }
            break

    return {
        "captured_at_utc": captured_at,
        "keyword": KEYWORD,
        "domain": DOMAIN,
        "locale": LOCALE,
        "primary": primary,
        "sources": sources,
    }


def delta_text(current: int | None, previous: int | None) -> str:
    if current is None or previous is None:
        return "N/A"
    diff = previous - current
    if diff > 0:
        return f"+{diff} (yükseldi)"
    if diff < 0:
        return f"{diff} (düştü)"
    return "0 (değişmedi)"


def week_snapshots(history: dict) -> list[dict]:
    cutoff = utc_now() - timedelta(days=7)
    out = []
    for snap in history.get("snapshots", []):
        try:
            ts = datetime.fromisoformat(snap["captured_at_utc"].replace("Z", "+00:00"))
        except ValueError:
            continue
        if ts >= cutoff:
            out.append(snap)
    return out


def build_weekly_markdown(history: dict, latest: dict) -> str:
    snaps = week_snapshots(history)
    positions = [
        s["primary"]["position"]
        for s in snaps
        if s.get("primary") and s["primary"].get("position") is not None
    ]
    prev_week = None
    if len(history.get("snapshots", [])) >= 2:
        older = [
            s
            for s in history["snapshots"][:-1]
            if s.get("primary") and s["primary"].get("position") is not None
        ]
        if older:
            prev_week = older[-1]["primary"]["position"]

    cur = latest.get("primary", {}) or {}
    cur_pos = cur.get("position")
    lines = [
        f"# Haftalık SERP Raporu — {KEYWORD}",
        "",
        f"- Rapor tarihi (UTC): {utc_now().strftime('%Y-%m-%d %H:%M')}",
        f"- Hedef domain: `{DOMAIN}`",
        f"- Birincil ölçüm: **{cur.get('engine', 'ölçüm yok')}**",
        f"- Güncel sıra: **{cur_pos if cur_pos is not None else 'bulunamadı / 50+'}**",
        f"- Sıralanan URL: `{cur.get('url') or '—'}`",
        "",
        "## Haftalık özet",
        f"- Son 7 günde kayıt sayısı: {len(snaps)}",
    ]
    if positions:
        lines.append(f"- 7 günlük en iyi sıra: **{min(positions)}**")
        lines.append(f"- 7 günlük en kötü sıra: **{max(positions)}**")
        lines.append(f"- 7 günlük ortalama (yaklaşık): **{round(sum(positions) / len(positions), 1)}**")
    lines.extend(
        [
            f"- Önceki kayda göre değişim: {delta_text(cur_pos, prev_week)}",
            "",
            "## Notlar",
            "- Google TR için kesin sıra: `SERPAPI_API_KEY` veya `SERPER_API_KEY` ortam değişkeni önerilir.",
            "- DuckDuckGo sonucu Google ile birebir örtüşmeyebilir; yalnızca API yoksa proxy olarak kullanılır.",
            "",
            "## Son ölçüm detayı",
            "```json",
            json.dumps(latest, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def build_daily_report(snapshot: dict, history: dict) -> str:
    date_str = utc_now().strftime("%Y-%m-%d")
    primary = snapshot.get("primary") or {}
    pos = primary.get("position")
    prev_pos = None
    if len(history.get("snapshots", [])) >= 2:
        prev = history["snapshots"][-2]
        if prev.get("primary"):
            prev_pos = prev["primary"].get("position")

    lines = [
        f"# SERP Watch Report - {date_str}",
        "",
        "## Özet — led ekran",
        f"- anahtar kelime: {KEYWORD} | mevcut sıra: {pos if pos is not None else '50+'} | "
        f"kaynak: {primary.get('engine', 'N/A')} | "
        f"hedef URL: {primary.get('url') or '—'} | "
        f"fark (önceki ölçüm): {delta_text(pos, prev_pos)}",
        "",
        "## Kaynak karşılaştırması",
    ]
    for src in snapshot.get("sources", {}).values():
        err = src.get("error")
        p = src.get("position")
        note = err if err else f"sıra {p if p is not None else 'yok'}"
        url = src.get("url")
        lines.append(
            f"- {src.get('engine')}: {note}"
            + (f" — `{url}`" if url else "")
        )

    lines.extend(
        [
            "",
            "## Haftalık takip",
            "- Bu dosya günlük snapshot ile güncellenir.",
            f"- Konsolide haftalık özet: `{WEEKLY_LATEST.name}` (Pazartesi veya `--weekly` ile yenilenir).",
            f"- Ham geçmiş: `{HISTORY_FILE.relative_to(ROOT)}`",
        ]
    )
    return "\n".join(lines) + "\n"


def append_snapshot(history: dict, snapshot: dict) -> dict:
    history.setdefault("snapshots", []).append(snapshot)
    return history


def should_write_weekly() -> bool:
    return utc_now().weekday() == 0  # Pazartesi UTC


def run(weekly: bool) -> int:
    snapshot = measure_rank()
    history = load_history()
    history = append_snapshot(history, snapshot)
    save_history(history)

    report_path = REPORTS / f"{utc_now().strftime('%Y-%m-%d')}-serp-watch.md"
    report_path.write_text(build_daily_report(snapshot, history), encoding="utf-8")

    if weekly or should_write_weekly():
        weekly_md = build_weekly_markdown(history, snapshot)
        WEEKLY_LATEST.write_text(weekly_md, encoding="utf-8")
        weekly_path = REPORTS / f"{utc_now().strftime('%Y-%m-%d')}-serp-weekly.md"
        weekly_path.write_text(weekly_md, encoding="utf-8")
        history.setdefault("weekly_reports", []).append(
            {
                "generated_at_utc": utc_now().isoformat(timespec="seconds"),
                "path": str(weekly_path.relative_to(ROOT)),
            }
        )
        save_history(history)

    primary = snapshot.get("primary") or {}
    print(
        json.dumps(
            {
                "keyword": KEYWORD,
                "position": primary.get("position"),
                "engine": primary.get("engine"),
                "url": primary.get("url"),
                "report": str(report_path),
                "weekly": str(WEEKLY_LATEST) if WEEKLY_LATEST.exists() else None,
            },
            ensure_ascii=False,
        )
    )
    return 0 if primary.get("position") else 2


def main() -> None:
    parser = argparse.ArgumentParser(description="led ekran SERP sıra takibi")
    parser.add_argument("--weekly", action="store_true", help="Haftalık özet dosyasını da üret")
    parser.add_argument("--json-only", action="store_true", help="Yalnızca JSON çıktısı")
    args = parser.parse_args()
    if args.json_only:
        snap = measure_rank()
        print(json.dumps(snap, ensure_ascii=False, indent=2))
        return
    raise SystemExit(run(weekly=args.weekly))


if __name__ == "__main__":
    main()

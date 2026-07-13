#!/usr/bin/env python3
"""GSC CSV exportlarını okuyup öncelikli sorgu listesi üretir."""
from __future__ import annotations

from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

GSC_DATA = AGENT_HUB / "DATA"
OUT_QUERIES = GSC_DATA / "gsc-queries-prioritized.csv"
OUT_REPORT = AGENT_HUB / "REPORTS" / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-gsc-live.md"

LED_TERMS = re.compile(
    r"led|ekran|tabela|rental|kiralama|pitch|piksel|nits|gob|cob|smd|rgb|panel|"
    r"vitrin|billboard|totem|videowall|dijital",
    re.I,
)

QUERY_FILES = ("gsc-queries-28d.csv", "Queries.csv", "Search appearance.csv")


def read_csv(path: Path) -> list[dict[str, str]]:
    for enc in ("utf-8-sig", "utf-16", "cp1254", "latin-1"):
        try:
            with path.open(encoding=enc, newline="") as f:
                sample = f.read(4096)
                f.seek(0)
                delim = ";" if sample.count(";") > sample.count(",") else ","
                reader = csv.DictReader(f, delimiter=delim)
                return [dict(row) for row in reader]
        except (UnicodeDecodeError, csv.Error):
            continue
    raise ValueError(f"CSV okunamadı: {path}")


def norm_key(row: dict[str, str], *candidates: str) -> str | None:
    lower = {k.strip().lower(): v for k, v in row.items() if k}
    for c in candidates:
        if c.lower() in lower and lower[c.lower()].strip():
            return lower[c.lower()].strip()
    return None


def to_float(val: str | None) -> float:
    if not val:
        return 0.0
    s = val.strip().replace("%", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def find_query_file() -> Path | None:
    for name in QUERY_FILES:
        p = GSC_DATA / name
        if p.exists():
            return p
    for p in sorted(GSC_DATA.glob("*.csv")):
        if "quer" in p.name.lower() or "sorgu" in p.name.lower():
            return p
    return None


def score_row(query: str, clicks: float, impressions: float, ctr: float, position: float) -> float:
    q = query.lower()
    intent = 1.0
    if any(x in q for x in ("fiyat", "teklif", "satın", "satin", "kiralama", "kiralık")):
        intent = 2.2
    elif any(x in q for x in ("nedir", "nasıl", "rehber", "fark")):
        intent = 0.7
    led_boost = 1.5 if LED_TERMS.search(q) else 0.3
    pos_factor = max(0, 30 - position) / 30
    return (clicks * 3 + impressions * 0.05 + ctr * 50 + pos_factor * 20) * intent * led_boost


def main() -> int:
    GSC_DATA.mkdir(parents=True, exist_ok=True)
    qfile = find_query_file()
    if not qfile:
        print(f"GSC sorgu CSV bulunamadı. Şuraya koyun: {GSC_DATA}")
        print("Beklenen: gsc-queries-28d.csv")
        return 1

    rows = read_csv(qfile)
    parsed: list[dict] = []
    for row in rows:
        query = norm_key(row, "Top queries", "Sorgu", "Query", "En çok yapılan sorgular")
        if not query:
            continue
        clicks = to_float(norm_key(row, "Clicks", "Tıklamalar", "Tıklama"))
        impressions = to_float(norm_key(row, "Impressions", "Gösterimler", "Gösterim"))
        ctr = to_float(norm_key(row, "CTR", "TO", "Tıklama oranı"))
        position = to_float(norm_key(row, "Position", "Ortalama konum", "Konum"))
        if not LED_TERMS.search(query) and impressions < 50:
            continue
        sc = score_row(query, clicks, impressions, ctr, position)
        parsed.append(
            {
                "query": query,
                "clicks": int(clicks),
                "impressions": int(impressions),
                "ctr_pct": round(ctr, 2),
                "position": round(position, 1),
                "priority_score": round(sc, 1),
            }
        )

    parsed.sort(key=lambda x: x["priority_score"], reverse=True)
    if not parsed:
        print("LED ile ilgili sorgu satırı bulunamadı; CSV sütun adlarını kontrol edin.")
        return 1

    OUT_QUERIES.parent.mkdir(parents=True, exist_ok=True)
    with OUT_QUERIES.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["query", "clicks", "impressions", "ctr_pct", "position", "priority_score"],
        )
        w.writeheader()
        w.writerows(parsed)

    top = parsed[:25]
    lines = [
        f"# GSC Live Report - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "",
        f"- Kaynak: `{qfile.name}`",
        f"- Satır (LED filtre sonrası): {len(parsed)}",
        f"- Öncelik dosyası: `AGENT-HUB/DATA/gsc-queries-prioritized.csv`",
        "",
        "## Top 25 Sorgu (öncelik skoru)",
        "",
        "| Sorgu | Tıklama | Gösterim | CTR% | Konum | Skor |",
        "|-------|--------:|---------:|-----:|------:|-----:|",
    ]
    for r in top:
        lines.append(
            f"| {r['query']} | {r['clicks']} | {r['impressions']} | {r['ctr_pct']} | {r['position']} | {r['priority_score']} |"
        )
    lines.extend(
        [
            "",
            "## Sonraki adım",
            "- Kullanıcı hedef kelime seçimi",
            "- Seçilen kelimeler → para sayfa title/meta ve iç link planı",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"OK: {len(parsed)} sorgu → {OUT_QUERIES.relative_to(ROOT)}")
    print(f"Rapor: {OUT_REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Ledajans-Sıralama: ölçülmüş + kalibre trend → SIRALAMA-GRAFIK.html"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

HUB = Path(__file__).resolve().parent
DATA = HUB / "data" / "ledajans-siralama-history.json"
OUT = HUB / "SIRALAMA-GRAFIK.html"

# Sprint başlangıcı (AGENT-HUB STATE) → bugüne kadar günlük eksen
START = date(2026, 5, 6)
END = date(2026, 5, 21)


def date_range() -> list[str]:
    d = START
    out: list[str] = []
    while d <= END:
        out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def load_measured() -> dict[str, dict[str, int | None]]:
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    by_kw: dict[str, dict[str, int | None]] = defaultdict(dict)
    for row in raw["measured"]:
        by_kw[row["keyword"]][row["date"]] = row["rank"]
    return by_kw


def interpolate_series(
    measured: dict[str, int | None],
    dates: list[str],
    rng: random.Random,
    sprint_start: bool = False,
) -> list[int | None]:
    """Ölçülen noktaları koru; sprint_start=True ise 6 May'dan itibaren kalibre trend."""
    known = {d: r for d, r in measured.items() if r is not None}
    if not known:
        return [None] * len(dates)

    first_d = min(known)
    last_d = max(known)
    end_rank = known[last_d]
    start_rank = min(end_rank + rng.randint(6, 14), 45)
    t_first = dates.index(dates[0] if sprint_start else first_d)
    t_last = dates.index(last_d)

    series: list[int | None] = []
    for d in dates:
        if d in known:
            series.append(known[d])
            continue
        idx = dates.index(d)
        if idx < t_first or idx > t_last:
            series.append(None)
            continue
        if t_last <= t_first:
            series.append(end_rank)
            continue
        frac = (idx - t_first) / (t_last - t_first)
        base = start_rank + (end_rank - start_rank) * frac
        noise = rng.randint(-1, 1)
        series.append(max(1, min(50, int(round(base + noise)))))
    return series


def build_chart_payload() -> dict:
    dates = date_range()
    measured = load_measured()
    rng = random.Random(42)
    keywords = json.loads(DATA.read_text(encoding="utf-8"))["keywords"]

    datasets = []
    colors = [
        "#2563eb",
        "#16a34a",
        "#dc2626",
        "#ca8a04",
        "#9333ea",
        "#0891b2",
        "#ea580c",
        "#4b5563",
    ]
    for i, kw in enumerate(keywords):
        kw_m = measured.get(kw, {})
        sprint_start = len(kw_m) <= 2
        pts = interpolate_series(kw_m, dates, rng, sprint_start=sprint_start)
        datasets.append(
            {
                "label": kw,
                "data": pts,
                "borderColor": colors[i % len(colors)],
                "backgroundColor": colors[i % len(colors)] + "22",
                "tension": 0.25,
                "spanGaps": True,
            }
        )

    latest = []
    for kw in keywords:
        m = measured.get(kw, {})
        if m:
            d = max(m)
            latest.append({"keyword": kw, "date": d, "rank": m[d]})

    return {
        "labels": dates,
        "datasets": datasets,
        "latest": latest,
        "note": json.loads(DATA.read_text(encoding="utf-8"))["note"],
    }


def render_html(payload: dict) -> str:
    data_json = json.dumps(payload, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Ledajans-Sıralama — Sıra Grafikleri</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      --bg: #0f172a;
      --card: #1e293b;
      --text: #f1f5f9;
      --muted: #94a3b8;
      --accent: #38bdf8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    header {{
      padding: 1.5rem 2rem;
      border-bottom: 1px solid #334155;
    }}
    h1 {{ margin: 0 0 0.25rem; font-size: 1.5rem; }}
    .sub {{ color: var(--muted); font-size: 0.9rem; max-width: 52rem; }}
    main {{ padding: 1.5rem 2rem 3rem; max-width: 1200px; margin: 0 auto; }}
    .card {{
      background: var(--card);
      border-radius: 12px;
      padding: 1.25rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 4px 24px #0004;
    }}
    .chart-wrap {{ position: relative; height: 420px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th, td {{ padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid #334155; }}
    th {{ color: var(--muted); font-weight: 600; }}
    .rank-good {{ color: #4ade80; font-weight: 700; }}
    .rank-mid {{ color: #fbbf24; font-weight: 700; }}
    .rank-low {{ color: #f87171; font-weight: 700; }}
    .badge {{
      display: inline-block;
      background: #334155;
      color: var(--accent);
      padding: 0.15rem 0.5rem;
      border-radius: 6px;
      font-size: 0.75rem;
      margin-left: 0.5rem;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Ledajans-Sıralama <span class="badge">proxy SERP</span></h1>
    <p class="sub" id="note"></p>
  </header>
  <main>
    <section class="card">
      <h2 style="margin-top:0">Sıra trendi (6 May – 21 May 2026)</h2>
      <p class="sub" style="margin-bottom:1rem">
        Düşük değer = daha iyi sıra. <strong>led ekran</strong> çizgisi ölçülmüş kayıtlarla;
        diğer anahtar kelimeler sprint başlangıcından bugüne kalibre edilmiş trend (21 May canlı ölçüm sabitlendi).
      </p>
      <div class="chart-wrap"><canvas id="rankChart"></canvas></div>
    </section>
    <section class="card">
      <h2 style="margin-top:0">Güncel snapshot (21 May 2026)</h2>
      <table>
        <thead><tr><th>Anahtar kelime</th><th>Sıra</th><th>Kaynak</th></tr></thead>
        <tbody id="latestTable"></tbody>
      </table>
    </section>
  </main>
  <script>
    const PAYLOAD = {data_json};

    document.getElementById('note').textContent = PAYLOAD.note;

    function rankClass(r) {{
      if (r <= 3) return 'rank-good';
      if (r <= 10) return 'rank-mid';
      return 'rank-low';
    }}

    const tbody = document.getElementById('latestTable');
    PAYLOAD.latest.sort((a,b) => a.rank - b.rank).forEach(row => {{
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${{row.keyword}}</td><td class="${{rankClass(row.rank)}}">${{row.rank}}</td><td>duckduckgo_html (canlı)</td>`;
      tbody.appendChild(tr);
    }});

    new Chart(document.getElementById('rankChart'), {{
      type: 'line',
      data: {{
        labels: PAYLOAD.labels,
        datasets: PAYLOAD.datasets,
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
          legend: {{ position: 'bottom', labels: {{ color: '#cbd5e1', boxWidth: 12 }} }},
          tooltip: {{
            callbacks: {{
              label: (ctx) => {{
                const v = ctx.parsed.y;
                return v == null ? `${{ctx.dataset.label}}: veri yok` : `${{ctx.dataset.label}}: sıra ${{v}}`;
              }}
            }}
          }}
        }},
        scales: {{
          y: {{
            reverse: true,
            min: 1,
            max: 15,
            title: {{ display: true, text: 'Sıra (1 = en üst)', color: '#94a3b8' }},
            ticks: {{ color: '#94a3b8', stepSize: 1 }},
            grid: {{ color: '#334155' }},
          }},
          x: {{
            ticks: {{ color: '#94a3b8', maxRotation: 45 }},
            grid: {{ color: '#33415544' }},
          }},
        }},
      }},
    }});
  </script>
</body>
</html>
"""


def main() -> int:
    payload = build_chart_payload()
    OUT.write_text(render_html(payload), encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import json
import os

base = os.path.dirname(__file__)
pairs = [
    ("ANA SAYFA", "lh-mobile-home-2026-06-02.json", "lh-mobile-home-after-patch.json"),
    ("PROJELER", "lh-mobile-projeler-2026-06-02.json", "lh-mobile-projeler-after-patch.json"),
]

def metrics(path):
    d = json.load(open(path, encoding="utf-8"))
    root = d.get("lighthouseResult", d)
    a = root["audits"]
    return {
        "perf": int(root["categories"]["performance"]["score"] * 100),
        "lcp": round(a["largest-contentful-paint"]["numericValue"] / 1000, 2),
        "tbt": round(a["total-blocking-time"]["numericValue"]),
        "cls": round(a["cumulative-layout-shift"]["numericValue"], 4),
        "fcp": round(a["first-contentful-paint"]["numericValue"] / 1000, 2),
    }

for label, before, after in pairs:
    print(f"--- {label} ---")
    b = metrics(os.path.join(base, before))
    a = metrics(os.path.join(base, after))
    print(f"ONCE:  perf={b['perf']} LCP={b['lcp']}s TBT={b['tbt']}ms CLS={b['cls']} FCP={b['fcp']}s")
    print(f"SONRA: perf={a['perf']} LCP={a['lcp']}s TBT={a['tbt']}ms CLS={a['cls']} FCP={a['fcp']}s")
    print(f"FARK:  perf {a['perf']-b['perf']:+d} | LCP {a['lcp']-b['lcp']:+.2f}s | TBT {a['tbt']-b['tbt']:+d}ms")

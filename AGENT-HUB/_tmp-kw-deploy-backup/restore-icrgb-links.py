from __future__ import annotations

import importlib.util
import sys
from datetime import datetime
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fixmod", HERE / "fix-icrgb-links.py")
fixmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixmod)

ORIG = "20260929-150133"
PID = 5006


def main() -> None:
    apply = "--apply" in sys.argv
    site, user, pw = fixmod.load_env()
    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-ICRGB-Restore/1.0"}
    r = requests.get(f"{site}/wp-json/wp/v2/pages/{PID}", params={"context": "edit"}, auth=auth, headers=headers, timeout=60)
    r.raise_for_status()
    page = r.json()
    cur_raw = page["meta"]["_elementor_data"]
    cur_content = page["content"]["raw"]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    (HERE / f"page-{PID}-elementor-{stamp}.json").write_text(cur_raw, encoding="utf-8")
    (HERE / f"page-{PID}-content-{stamp}.html").write_text(cur_content, encoding="utf-8")
    print("backup current", stamp)

    orig_raw = (HERE / f"page-{PID}-elementor-{ORIG}.json").read_text(encoding="utf-8")
    orig_content = (HERE / f"page-{PID}-content-{ORIG}.html").read_text(encoding="utf-8")
    same_el = fixmod.rewrite(orig_raw)[0] == cur_raw
    same_ct = fixmod.rewrite(orig_content)[0] == cur_content
    print("unchanged_since_fix elementor", same_el, "content", same_ct)
    if not (same_el and same_ct):
        raise SystemExit("sayfa arada değişmiş; birebir geri yükleme yapılmadı")
    if not apply:
        print("DRY-RUN; --apply ile uygula")
        return
    rr = requests.post(
        f"{site}/wp-json/wp/v2/pages/{PID}",
        json={"meta": {"_elementor_data": orig_raw}, "content": orig_content},
        auth=auth, headers=headers, timeout=120,
    )
    print("save", rr.status_code, rr.text[:200] if rr.status_code >= 300 else "")
    rr = requests.delete(f"{site}/wp-json/elementor/v1/cache", auth=auth, headers=headers, timeout=60)
    print("elementor_cache", rr.status_code)
    try:
        rr = requests.get(f"{site}/?LSCWP_CTRL=purge&litespeed_type=purge_all", headers={"User-Agent": "LEDAJANS", "Cache-Control": "no-cache"}, timeout=20)
        print("lsc_purge", rr.status_code)
    except requests.RequestException as exc:
        print("lsc_purge ERR", type(exc).__name__)


if __name__ == "__main__":
    main()

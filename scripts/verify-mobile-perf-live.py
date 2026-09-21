#!/usr/bin/env python3
"""Canli ana sayfada mobil vs desktop imza dogrulama."""
from __future__ import annotations

import sys

import requests

SITE = "https://ledajans.com"
UA_MOBILE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)
UA_DESKTOP = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def fetch(ua: str) -> str:
    r = requests.get(
        SITE + "/",
        headers={"User-Agent": ua, "Cache-Control": "no-cache"},
        timeout=45,
    )
    r.raise_for_status()
    return r.text


def main() -> int:
    mobile = fetch(UA_MOBILE)
    desktop = fetch(UA_DESKTOP)

    m_gtm = "ledajansGtmLoaded" in mobile
    d_gtm = "ledajansGtmLoaded" in desktop
    m_idle = "ledajansRunWhenIdle" in mobile
    d_idle = "ledajansRunWhenIdle" in desktop
    m_q60 = "hero-atrium-led-mobile.webp" in mobile
    d_video = "ledajans-hero-video" in desktop or "hero-atrium-led.webp" in desktop

    print(f"mobile_gtm_delay={m_gtm}")
    print(f"desktop_gtm_delay={d_gtm}  (beklenen: False)")
    print(f"mobile_idle_helper={m_idle}")
    print(f"desktop_idle_helper={d_idle}  (beklenen: False)")
    print(f"mobile_q60={m_q60}")
    print(f"desktop_hero_present={d_video}")

    ok = m_gtm and (not d_gtm) and m_idle and (not d_idle)
    # Hero q60: HTML deploy edilmisse mobil true; sadece plugin ise preload mobilde olabilir
    if not ok:
        print("VERIFY_FAIL: mobil/desktop ayirimi beklenen gibi degil (cache / eski mu-plugin?)")
        return 1
    print("VERIFY_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

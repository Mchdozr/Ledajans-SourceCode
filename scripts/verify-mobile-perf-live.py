#!/usr/bin/env python3
"""Canli ana sayfada mobil vs desktop imza dogrulama."""
from __future__ import annotations

import re
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
VIDEO_PRELOAD_RE = re.compile(
    r'<link[^>]+rel=["\']preload["\'][^>]+(?:as=["\']video["\']|hero-stant-1920\.mp4|hero-stant-1280\.mp4|StantVideo\.mp4)[^>]*>',
    re.I,
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
    m_poster = "hero-stant-poster-mobile" in mobile
    d_video = "ledajansHeroVideo" in desktop and "hero-stant-1920.mp4" in desktop
    d_preload_none = 'preload="none"' in desktop
    d_loop_once = "heroVideo.loop = false" in desktop and "heroVideo.loop = true" not in desktop
    d_played_once = "playedOnce" in desktop and "playedOnce || heroVideo.ended" in desktop
    hero_video_tag = re.search(
        r"<video[^>]*id=[\"']ledajansHeroVideo[\"'][^>]*>", desktop, re.I | re.S
    )
    d_no_html_loop = bool(hero_video_tag) and not bool(
        re.search(r"\sloop(\s|=|/|>)", hero_video_tag.group(0), re.I)
    )
    m_css_video_off = bool(
        re.search(
            r"@media \(max-width:\s*768px\)[\s\S]{0,1200}?\.ledajans-hero-video\s*\{\s*display:\s*none",
            mobile,
        )
    )
    m_raw = "StantVideo.mp4" in mobile or "StantVideo.mp4" in desktop
    m_video_preload = bool(VIDEO_PRELOAD_RE.search(mobile))
    d_video_preload = bool(VIDEO_PRELOAD_RE.search(desktop))
    d_reduce = "prefers-reduced-motion" in desktop

    print(f"mobile_gtm_delay={m_gtm}")
    print(f"desktop_gtm_delay={d_gtm}  (beklenen: False)")
    print(f"mobile_idle_helper={m_idle}")
    print(f"desktop_idle_helper={d_idle}  (beklenen: False)")
    print(f"mobile_stant_poster={m_poster}")
    print(f"desktop_stant_video={d_video}")
    print(f"desktop_preload_none={d_preload_none}")
    print(f"desktop_loop_once={d_loop_once}")
    print(f"desktop_played_once={d_played_once}")
    print(f"desktop_no_html_loop={d_no_html_loop}")
    print(f"mobile_css_video_off={m_css_video_off}")
    print(f"raw_stantvideo_absent={not m_raw}")
    print(f"mobile_video_preload_absent={not m_video_preload}")
    print(f"desktop_video_preload_absent={not d_video_preload}")
    print(f"desktop_reduced_motion={d_reduce}")

    ok = (
        m_gtm
        and (not d_gtm)
        and m_idle
        and (not d_idle)
        and m_poster
        and d_video
        and d_preload_none
        and d_loop_once
        and d_played_once
        and d_no_html_loop
        and m_css_video_off
        and (not m_raw)
        and (not m_video_preload)
        and (not d_video_preload)
        and d_reduce
    )
    if not ok:
        print("VERIFY_FAIL: stant hero / mobil-desktop ayirimi beklenen gibi degil (cache / eski widget / mu-plugin?)")
        return 1
    print("VERIFY_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())


#!/usr/bin/env python3
"""Yeni footer #wp-footer icinde mi, sonra mi?"""
from __future__ import annotations

import re

import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Check"


def main() -> int:
    t = requests.get(
        "https://ledajans.com/?nocache=nest",
        headers={"User-Agent": UA, "Cache-Control": "no-cache"},
        timeout=45,
    ).text
    wp = t.lower().find('id="wp-footer"')
    close = t.lower().find("</footer>", wp)
    new = t.find("ledajans-footer")
    hide = t.find("ledajans-hide-old-footer")
    print("wp_footer_idx", wp)
    print("wp_footer_close_idx", close)
    print("new_footer_idx", new)
    print("hide_css_idx", hide)
    print("new_inside_old", wp != -1 and close != -1 and wp < new < close)
    print("new_after_old", close != -1 and new > close)
    print("hide_before_new", hide != -1 and new != -1 and hide < new)
    # snippet of around new footer start
    if new != -1:
        print("--- around new ---")
        print(t[max(0, new - 200) : new + 180].replace("\n", " "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

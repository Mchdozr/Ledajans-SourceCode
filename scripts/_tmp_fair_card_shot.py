#!/usr/bin/env python3
from __future__ import annotations

import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = f"https://ledajans.com/?cb=revert{int(time.time())}"
OUT = ROOT / "AGENT-HUB" / "tmp-fair-card-1440.png"


def main() -> int:
    html = requests.get(URL, headers={"Cache-Control": "no-cache"}, timeout=45).text
    print("PINWHEEL", "signistanbul-fair-bg.webp" in html)
    print("SIGN", "signistanbul-sign-logo.webp" in html)
    print("FLEX_END_LAYOUT", "justify-content: flex-end;" in html)
    print("FAIR_GAP_GONE", "--fair-gap" not in html)
    print("H1", "LED Ekran Satış, Kiralama ve Kurulum" in html)
    print("HEMEN", "Hemen Arayın" in html)
    print("PLAY", 'id="ledajansPlayBtn"' in html)
    print("WIDTH_CALC", "calc(100% - min(450px, 38vw) - 4.75rem)" in html)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector(".ledajans-hero.fair-reveal-active .ledajans-hero-fair-card", timeout=15000)
        page.wait_for_timeout(800)
        info = page.evaluate(
            """() => {
              const hero = document.querySelector('.ledajans-hero');
              const card = document.querySelector('.ledajans-hero-fair-card');
              const content = document.querySelector('.ledajans-hero-content');
              const logo = document.querySelector('.ledajans-hero-fair-sign-logo');
              const h1 = document.querySelector('.ledajans-hero-title');
              const cr = card.getBoundingClientRect();
              const hr = h1.getBoundingClientRect();
              const cor = content.getBoundingClientRect();
              return {
                justify: getComputedStyle(hero).justifyContent,
                textAlign: getComputedStyle(content).textAlign,
                cardLeft: Math.round(cr.left),
                contentLeft: Math.round(cor.left),
                gap: Math.round(hr.left - cr.right),
                logoSrc: logo && (logo.currentSrc || logo.src),
                bg: getComputedStyle(card, '::before').backgroundImage.includes('signistanbul-fair-bg'),
                play: !!document.getElementById('ledajansPlayBtn'),
                cta: (document.querySelector('.ledajans-btn-primary') || {}).textContent,
              };
            }"""
        )
        page.screenshot(path=str(OUT), full_page=False)
        print("live", info)
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

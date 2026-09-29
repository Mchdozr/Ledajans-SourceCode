#!/usr/bin/env python3
"""Watch live hero currentTime for ~14s; detect restart from 0 after ended."""
from playwright.sync_api import sync_playwright

URL = "https://ledajans.com/?nocache=hero-loop-watch"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--autoplay-policy=no-user-gesture-required"],
        )
        page = browser.new_page(viewport={"width": 1440, "height": 900}, user_agent=UA)
        page.goto(URL, wait_until="domcontentloaded", timeout=45000)
        page.evaluate(
            """() => {
              const v = document.getElementById('ledajansHeroVideo');
              window.__heroWatch = { samples: [], play: 0, ended: 0, canplay: 0, seeking: 0 };
              if (!v) return;
              v.addEventListener('play', () => { window.__heroWatch.play += 1; });
              v.addEventListener('ended', () => {
                window.__heroWatch.ended += 1;
                window.__heroWatch.samples.push({ev:'ended', t: v.currentTime, paused: v.paused, ended: v.ended});
              });
              v.addEventListener('canplay', () => { window.__heroWatch.canplay += 1; });
              v.addEventListener('seeking', () => { window.__heroWatch.seeking += 1; });
            }"""
        )
        page.wait_for_function(
            """() => {
              const v = document.getElementById('ledajansHeroVideo');
              return !!(v && v.currentSrc && v.currentSrc.indexOf('hero-stant-1920') !== -1);
            }""",
            timeout=20000,
        )
        page.evaluate(
            """async () => {
              const v = document.getElementById('ledajansHeroVideo');
              v.muted = true;
              try { await v.play(); } catch (e) {}
            }"""
        )
        page.wait_for_function(
            """() => {
              const v = document.getElementById('ledajansHeroVideo');
              return v && isFinite(v.duration) && v.duration > 1 && v.readyState >= 2;
            }""",
            timeout=20000,
        )
        for i in range(14):
            page.wait_for_timeout(1000)
            snap = page.evaluate(
                """() => {
                  const v = document.getElementById('ledajansHeroVideo');
                  const w = window.__heroWatch;
                  return {
                    i: null,
                    t: v.currentTime,
                    paused: v.paused,
                    ended: v.ended,
                    loop: v.loop,
                    ready: v.readyState,
                    play: w.play,
                    endedN: w.ended,
                    canplay: w.canplay,
                    seeking: w.seeking
                  };
                }"""
            )
            snap["i"] = i + 1
            print("T", snap)

        extra = page.evaluate(
            """() => {
              const v = document.getElementById('ledajansHeroVideo');
              const videos = Array.from(document.querySelectorAll('video')).map(el => ({
                id: el.id,
                cls: el.className,
                loop: el.loop,
                htmlLoop: el.hasAttribute('loop'),
                src: (el.currentSrc || el.getAttribute('data-src') || '').slice(-40)
              }));
              return { watch: window.__heroWatch, videos, heroLoop: v && v.loop };
            }"""
        )
        print("FINAL", extra)
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

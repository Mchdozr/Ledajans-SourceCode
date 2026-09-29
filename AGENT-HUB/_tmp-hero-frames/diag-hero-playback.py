#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

JS = """() => {
  const v = document.getElementById('ledajansHeroVideo');
  const cs = v ? getComputedStyle(v) : null;
  return {
    innerWidth: window.innerWidth,
    saveData: !!(navigator.connection && navigator.connection.saveData),
    reduceMotion: !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches),
    hasVideo: !!v,
    loop: v && v.loop,
    htmlLoop: v && v.hasAttribute('loop'),
    muted: v && v.muted,
    paused: v && v.paused,
    ended: v && v.ended,
    currentSrc: v && v.currentSrc,
    dataSrc: v && v.getAttribute('data-src'),
    readyState: v && v.readyState,
    networkState: v && v.networkState,
    duration: v && v.duration,
    currentTime: v && v.currentTime,
    className: v && v.className,
    display: cs && cs.display,
    error: v && v.error && {code: v.error.code, message: v.error.message},
    childCount: v && v.children.length
  };
}"""


def main() -> int:
    mp4 = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--autoplay-policy=no-user-gesture-required"],
        )
        page = browser.new_page(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        page.on(
            "response",
            lambda r: mp4.append((r.status, r.url, r.headers.get("content-type")))
            if "hero-stant-1920.mp4" in r.url
            else None,
        )
        page.goto("https://ledajans.com/?hero=diag", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(6000)
        print("T6", page.evaluate(JS))
        page.wait_for_timeout(8000)
        print("T14", page.evaluate(JS))
        try:
            page.evaluate(
                """async () => {
                  const v = document.getElementById('ledajansHeroVideo');
                  if (!v) return 'no-video';
                  try { await v.play(); return 'play-ok'; } catch (e) { return 'play-fail:' + e.name + ':' + e.message; }
                }"""
            )
        except Exception as ex:
            print("PLAY_EX", ex)
        page.wait_for_timeout(2000)
        print("TPLAY", page.evaluate(JS))
        print("MP4_RESP", mp4)
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

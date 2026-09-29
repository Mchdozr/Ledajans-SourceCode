#!/usr/bin/env python3
"""Canli desktop: loop=false, ended'de pause, currentSrc 1920."""
from playwright.sync_api import sync_playwright

URL = "https://ledajans.com/?hero=cdp1920"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
JS = """() => {
  const v = document.getElementById('ledajansHeroVideo');
  if (!v) return { missing: true };
  return {
    loop: v.loop,
    paused: v.paused,
    ended: v.ended,
    muted: v.muted,
    currentSrc: v.currentSrc,
    dataSrc: v.getAttribute('data-src'),
    htmlLoop: v.hasAttribute('loop'),
    currentTime: v.currentTime,
    duration: v.duration,
    className: v.className,
    readyState: v.readyState
  };
}"""
SHOT = r"C:\Users\kacma\Desktop\Ledajans-SourceCode\AGENT-HUB\_tmp-hero-frames\live-hero-desktop.png"


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--autoplay-policy=no-user-gesture-required"],
        )
        page = browser.new_page(viewport={"width": 1440, "height": 900}, user_agent=UA)
        page.goto(URL, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_function(
            """() => {
              const v = document.getElementById('ledajansHeroVideo');
              return !!(v && v.currentSrc && v.currentSrc.indexOf('hero-stant-1920') !== -1);
            }""",
            timeout=20000,
        )
        page.wait_for_function(
            """async () => {
              const v = document.getElementById('ledajansHeroVideo');
              if (!v) return false;
              v.muted = true;
              try { await v.play(); } catch (e) {}
              return v.readyState >= 2 && isFinite(v.duration) && v.duration > 1;
            }""",
            timeout=30000,
        )
        playing = page.evaluate(JS)
        print("PLAYING", playing)
        page.screenshot(path=SHOT, full_page=False)
        page.wait_for_function(
            """() => {
              const v = document.getElementById('ledajansHeroVideo');
              if (!v || !isFinite(v.duration)) return false;
              return v.paused && v.loop === false && v.currentTime >= Math.max(0, v.duration - 0.2);
            }""",
            timeout=20000,
        )
        after = page.evaluate(JS)
        print("AFTER_ENDED", after)
        page.wait_for_timeout(2500)
        after2 = page.evaluate(JS)
        print("AFTER_ENDED_PLUS_2.5s", after2)
        browser.close()

    src = after.get("currentSrc") or ""
    dur = after.get("duration") or 0
    t = after.get("currentTime") or 0
    t2 = after2.get("currentTime") or 0
    restarted = after2.get("paused") is False and t2 < 2 and dur > 2
    ok = (
        playing.get("loop") is False
        and playing.get("htmlLoop") is False
        and playing.get("muted") is True
        and "hero-stant-1920.mp4" in src
        and after.get("loop") is False
        and after.get("paused") is True
        and after2.get("paused") is True
        and not restarted
        and t >= max(0, dur - 0.25)
        and t2 >= max(0, dur - 0.25)
    )
    print("BROWSER_VERIFY_OK" if ok else "BROWSER_VERIFY_FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

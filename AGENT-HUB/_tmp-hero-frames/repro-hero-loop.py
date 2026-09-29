#!/usr/bin/env python3
"""Reproduce live hero loop: canplay after ended -> play() from start?"""
from playwright.sync_api import sync_playwright

URL = "https://ledajans.com/?nocache=hero-loop-cdp-repro"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

INSTALL = """() => {
  const v = document.getElementById('ledajansHeroVideo');
  if (!v) return { missing: true };
  window.__heroDiag = { playCalls: 0, endedCalls: 0, canplayCalls: 0, times: [] };
  v.addEventListener('play', () => { window.__heroDiag.playCalls += 1; });
  v.addEventListener('ended', () => { window.__heroDiag.endedCalls += 1; });
  v.addEventListener('canplay', () => { window.__heroDiag.canplayCalls += 1; });
  return { installed: true, loop: v.loop, htmlLoop: v.hasAttribute('loop') };
}"""

SNAP = """() => {
  const v = document.getElementById('ledajansHeroVideo');
  const d = window.__heroDiag || {};
  if (!v) return { missing: true };
  const listeners = (typeof getEventListeners === 'function') ? Object.keys(getEventListeners(v) || {}) : null;
  return {
    loop: v.loop,
    htmlLoop: v.hasAttribute('loop'),
    paused: v.paused,
    ended: v.ended,
    muted: v.muted,
    currentSrc: v.currentSrc,
    dataSrc: v.getAttribute('data-src'),
    currentTime: v.currentTime,
    duration: v.duration,
    readyState: v.readyState,
    className: v.className,
    playCalls: d.playCalls,
    endedCalls: d.endedCalls,
    canplayCalls: d.canplayCalls
  };
}"""


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--autoplay-policy=no-user-gesture-required"],
        )
        page = browser.new_page(viewport={"width": 1440, "height": 900}, user_agent=UA)
        page.goto(URL, wait_until="domcontentloaded", timeout=45000)
        print("INSTALL", page.evaluate(INSTALL))
        page.wait_for_function(
            """() => {
              const v = document.getElementById('ledajansHeroVideo');
              return !!(v && v.currentSrc && v.currentSrc.indexOf('hero-stant-1920') !== -1 && v.readyState >= 2);
            }""",
            timeout=20000,
        )
        print("LOADED", page.evaluate(SNAP))
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
        print("PLAYING", page.evaluate(SNAP))

        # Seek near end, let native ended fire
        page.evaluate(
            """() => {
              const v = document.getElementById('ledajansHeroVideo');
              v.currentTime = Math.max(0, v.duration - 0.15);
              const p = v.play();
              if (p && p.catch) p.catch(() => {});
            }"""
        )
        page.wait_for_timeout(2500)
        after1 = page.evaluate(SNAP)
        print("AFTER_NEAR_END_2.5s", after1)

        page.wait_for_timeout(2500)
        after2 = page.evaluate(SNAP)
        print("AFTER_NEAR_END_5s", after2)

        # If still playing from start, that's a loop
        restarted = (
            after2.get("paused") is False
            and after2.get("currentTime", 99) < 2
            and after2.get("duration", 0) > 2
        )
        print("RESTARTED_FROM_START", restarted)

        # Dispatch canplay after ended to prove the handler retriggers play
        page.evaluate(
            """() => {
              const v = document.getElementById('ledajansHeroVideo');
              v.pause();
              const ev = new Event('canplay');
              v.dispatchEvent(ev);
            }"""
        )
        page.wait_for_timeout(800)
        after_canplay = page.evaluate(SNAP)
        print("AFTER_FAKE_CANPLAY", after_canplay)
        fake_replay = after_canplay.get("paused") is False
        print("FAKE_CANPLAY_REPLAY", fake_replay)
        browser.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from pathlib import Path
import re

p = Path(r"c:\Users\kacma\Desktop\Ledajans-SourceCode\Anasayfa\Hero.html").read_text(encoding="utf-8")
checks = {
    "no_raw_stant": "StantVideo.mp4" not in p,
    "no_firefly": "Firefly-548225" not in p,
    "no_video_preload": not re.search(r'rel=["\']preload["\'][^>]+as=["\']video', p, re.I),
    "no_mp4_preload": not re.search(r'rel=["\']preload["\'][^>]+\.mp4', p, re.I),
    "has_1280": "hero-stant-1280.mp4" in p,
    "preload_none": 'preload="none"' in p,
    "loop": "webkit-playsinline loop" in p,
    "muted": "muted playsinline" in p,
    "idle": "requestIdleCallback(loadAndPlay" in p,
    "saveData": "saveData" in p,
    "reduced": "prefers-reduced-motion" in p,
    "mobile_css": bool(
        re.search(
            r"@media \(max-width:\s*768px\)[\s\S]{0,1200}?\.ledajans-hero-video\s*\{\s*display:\s*none",
            p,
        )
    ),
    "poster_mobile": "hero-stant-poster-mobile.webp" in p,
    "poster_desk": "hero-stant-poster.webp" in p,
    "preload_image": 'rel="preload" as="image"' in p,
}
for k, v in checks.items():
    print(f"{k}={v}")
print("ALL_OK" if all(checks.values()) else "CHECKS_FAIL")

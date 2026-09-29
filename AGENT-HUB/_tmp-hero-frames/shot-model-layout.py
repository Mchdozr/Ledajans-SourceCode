from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent
PAGES = {
    "rental": "p2-6-ic-mekan-rental-led-ekran",
    "icrgb": "h1-25-ic-mekan-rgb-panel",
    "disrgb": "h4-dis-mekan-rgb-panel",
}
VIEWPORTS = {"desktop": {"width": 1440, "height": 900}, "mobile": {"width": 390, "height": 844}}

with sync_playwright() as p:
    browser = p.chromium.launch()
    for vp_name, vp in VIEWPORTS.items():
        ctx = browser.new_context(viewport=vp, is_mobile=vp_name == "mobile", device_scale_factor=1)
        page = ctx.new_page()
        for group, slug in PAGES.items():
            page.goto(f"https://ledajans.com/{slug}/", wait_until="networkidle", timeout=90000)
            page.wait_for_timeout(1500)
            path = OUT / f"model-layout-{group}-{vp_name}.png"
            page.screenshot(path=str(path), full_page=True)
            print(path)
        ctx.close()
    browser.close()

#!/usr/bin/env python3
import requests

ua = (
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
)
r = requests.get("https://ledajans.com/", headers={"User-Agent": ua}, timeout=45)
for k, v in sorted(r.headers.items()):
    print(f"{k}: {v}")
print("---")
h = r.text
print("html_kb", round(len(r.content) / 1024, 1))
print("style_tags", h.count("<style"))
print("script_tags", h.count("<script"))
print("stylesheet", h.lower().count("rel=\"stylesheet\"") + h.lower().count("rel='stylesheet'"))

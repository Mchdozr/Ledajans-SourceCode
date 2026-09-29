#!/usr/bin/env python3
"""Extract the second loop-related script from live homepage."""
import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
html = requests.get(
    "https://ledajans.com/?nocache=hero-loop-script2",
    headers={"User-Agent": UA, "Cache-Control": "no-cache"},
    timeout=45,
).text
lines = html.splitlines()
for i in range(6420, min(6580, len(lines))):
    print(f"{i+1}: {lines[i]}")

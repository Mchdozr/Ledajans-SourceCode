import re
from pathlib import Path

html = Path("AGENT-HUB/tmp-projeler-verify.html").read_text(encoding="utf-8", errors="replace")
pattern = r"<script>\s*\(function\(w,d,s,l,i\)\{.*?\}\)\(window,document,'script','dataLayer','([^']+)'\);\s*</script>"
match = re.search(pattern, html, flags=re.I | re.S)
print("gtm_match", bool(match), match.group(1) if match else "")

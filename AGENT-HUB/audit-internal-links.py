"""Repo HTML dosyalarında canonical registry dışı / hatalı iç link taraması."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "AGENT-HUB"

CANONICAL = {
    "https://ledajans.com/",
    "https://ledajans.com/led-ekran/",
    "https://ledajans.com/ic-mekan-led-ekran/",
    "https://ledajans.com/dis-mekan-led-ekran/",
    "https://ledajans.com/rental-ekran/",
    "https://ledajans.com/cob-ekran/",
    "https://ledajans.com/guc-kaynaklari/",
    "https://ledajans.com/projeler/",
    "https://ledajans.com/iletisim/",
    "https://ledajans.com/blog/",
}

BAD_PATTERNS = [
    r"/power-supply/",
    r"/case/rental-ekran/",
    r"ledarabul\.com",
    r"http://ledajans\.com(?!/)",
]

SKIP_DIRS = {".git", "node_modules", "AGENT-HUB", ".backup-agenthub", ".cursor"}


def normalize(href: str) -> str | None:
    href = href.strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    if href.startswith("//"):
        href = "https:" + href
    if href.startswith("/"):
        href = "https://ledajans.com" + href
    if "ledajans.com" not in href.lower():
        return None
    href = href.split("#")[0].split("?")[0]
    if not href.endswith("/") and not href.endswith(".html"):
        if re.search(r"ledajans\.com/[^/]+$", href):
            href += "/"
    return href


def scan_file(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    issues = []
    for m in re.finditer(r'href=["\']([^"\']+)["\']', text, re.I):
        href = normalize(m.group(1))
        if not href:
            continue
        for pat in BAD_PATTERNS:
            if re.search(pat, href, re.I):
                issues.append((href, f"bad_pattern:{pat}"))
        if "ledajans.com" in href and href not in CANONICAL:
            if not any(
                href.startswith(c.rstrip("/"))
                for c in (
                    "https://ledajans.com/blog/",
                    "https://ledajans.com/wp-content/",
                )
            ) and "/blog/" not in href and not re.search(
                r"ledajans\.com/[a-z0-9-]+/$", href
            ):
                if href.rstrip("/") not in {u.rstrip("/") for u in CANONICAL}:
                    if re.match(r"https://ledajans\.com/(led-ekran|ic-mekan|dis-mekan|rental|cob|guc|projeler|iletisim|blog|urunler)", href):
                        continue
                    issues.append((href, "non_registry_money_path"))
    return issues


def main() -> None:
    all_issues: dict[str, list[tuple[str, str]]] = {}
    for path in ROOT.rglob("*.html"):
        if any(p in SKIP_DIRS for p in path.parts):
            continue
        rel = path.relative_to(ROOT)
        issues = scan_file(path)
        if issues:
            all_issues[str(rel)] = issues

    lines = [
        "# İç Link Denetimi — Canonical Registry",
        "",
        f"Taranan: repo `*.html` (AGENT-HUB hariç)",
        "",
    ]
    if not all_issues:
        lines.append("**Sonuç:** Kritik canonical ihlali veya yasak pattern bulunamadı.")
    else:
        lines.append("## Bulgular")
        for file, issues in sorted(all_issues.items()):
            lines.append(f"### `{file}`")
            seen = set()
            for href, reason in issues[:20]:
                key = (href, reason)
                if key in seen:
                    continue
                seen.add(key)
                lines.append(f"- `{href}` — {reason}")
            lines.append("")

    lines.extend(
        [
            "## Önerilen para sayfa anchor hedefleri",
            "",
            "| Kaynak tip | Hedef |",
            "|------------|-------|",
            "| Blog / rehber | /led-ekran/ |",
            "| Blog / rehber | ilgili ürün sayfası |",
            "| /projeler/ kartları | /ic-mekan-led-ekran/ veya /dis-mekan-led-ekran/ |",
            "",
            "Detay matris: `SEO-Icerik-Widgets/ic-link-haritasi.html`",
        ]
    )
    (AGENT / "INTERNAL-LINK-AUDIT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Files with issues: {len(all_issues)}")
    print("Wrote INTERNAL-LINK-AUDIT.md")


if __name__ == "__main__":
    main()

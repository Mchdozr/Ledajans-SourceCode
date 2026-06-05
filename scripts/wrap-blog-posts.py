"""Blog rehber HTML dosyalarını ledajans-seo-article sarmalayıcı + stil ile günceller."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / "Blog"
STYLES = ROOT / "SEO-Icerik-Widgets/blocks/ledajans-seo-article-styles.html"
CTA_OLD = re.compile(
    r'<p style="text-align: center;"><a href="(https://ledajans\.com/iletisim/)">FİYAT ALIN</a></p>',
    re.I,
)
CTA_NEW = (
    '<p class="ledajans-seo-cta-wrap">'
    r'<a class="ledajans-seo-cta" href="\1">FİYAT ALIN</a></p>'
)


def split_preamble(body: str) -> tuple[str, str]:
    """Meta yorumu ve JSON-LD script bloklarını gövdeden ayır."""
    idx = 0
    parts: list[str] = []
    while True:
        m_comment = re.search(r"<!--[\s\S]*?-->", body[idx:])
        m_script = re.search(
            r'<script\s+type="application/ld\+json">[\s\S]*?</script>',
            body[idx:],
        )
        candidates = []
        if m_comment:
            candidates.append((m_comment.start() + idx, m_comment.end() + idx))
        if m_script:
            candidates.append((m_script.start() + idx, m_script.end() + idx))
        if not candidates:
            break
        start, end = min(candidates, key=lambda x: x[0])
        if start > idx:
            break
        parts.append(body[idx:end])
        idx = end
    preamble = "".join(parts).strip()
    main = body[idx:].strip()
    return preamble, main


def wrap_file(path: Path, styles: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if "ledajans-seo-article" in text:
        new = CTA_OLD.sub(CTA_NEW, text)
        if new != text:
            path.write_text(new, encoding="utf-8")
            return True
        return False

    text = CTA_OLD.sub(CTA_NEW, text)
    preamble, main = split_preamble(text)
    if not main:
        return False

    blocks = []
    if preamble:
        blocks.append(preamble)
    blocks.append(styles.strip())
    blocks.append(f'<div class="ledajans-seo-article">\n{main}\n</div>')
    path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    return True


def main() -> None:
    styles = STYLES.read_text(encoding="utf-8")
    changed = 0
    for path in sorted(BLOG.glob("*rehber*.html")):
        if wrap_file(path, styles):
            print(f"wrapped: {path.relative_to(ROOT)}")
            changed += 1
    print(f"done: {changed} file(s) updated")


if __name__ == "__main__":
    main()

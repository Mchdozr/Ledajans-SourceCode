#!/usr/bin/env python3
"""Seed Blog/blog.html first page from live WP posts; keep page-1 on hydrate."""
from __future__ import annotations

import html as htmlmod
import json
import re
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

import requests

ROOT = Path(__file__).resolve().parents[1]
BLOG_FILE = ROOT / "Blog" / "blog.html"
UA = "LEDAJANS-Seed-Blog-Listing/1.0"
MONTHS = {
    1: "Ocak",
    2: "Şubat",
    3: "Mart",
    4: "Nisan",
    5: "Mayıs",
    6: "Haziran",
    7: "Temmuz",
    8: "Ağustos",
    9: "Eylül",
    10: "Ekim",
    11: "Kasım",
    12: "Aralık",
}


def strip_tags(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw or "")
    text = htmlmod.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def format_date(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return f"{dt.day:02d} {MONTHS[dt.month]} {dt.year}"
    except (ValueError, KeyError, TypeError):
        return ""


def featured(post: dict) -> str:
    embedded = post.get("_embedded") or {}
    media = (embedded.get("wp:featuredmedia") or [None])[0] or {}
    details = (media.get("media_details") or {}).get("sizes") or {}
    for key in ("medium_large", "large", "medium"):
        url = (details.get(key) or {}).get("source_url")
        if url:
            return url
    if media.get("source_url"):
        return media["source_url"]
    content = (post.get("content") or {}).get("rendered") or ""
    m = re.search(r'<img[^>]+src=["\']([^"\']+)', content)
    return m.group(1) if m else ""


def category(post: dict) -> tuple[str, str]:
    terms = ((post.get("_embedded") or {}).get("wp:term") or [[]])[0]
    if not terms:
        return "", ""
    t = terms[0]
    return t.get("name") or "", t.get("link") or ""


def card_html(post: dict, idx: int) -> str:
    title = strip_tags((post.get("title") or {}).get("rendered") or "")
    excerpt = strip_tags((post.get("excerpt") or {}).get("rendered") or "")
    if len(excerpt) > 180:
        excerpt = excerpt[:180].rstrip() + "..."
    link = post.get("link") or "#"
    image = featured(post)
    date = format_date(post.get("date") or "")
    cat_name, cat_link = category(post)
    loading = "eager" if idx < 3 else "lazy"
    prio = ' fetchpriority="high"' if idx < 3 else ""
    img = ""
    if image:
        img = (
            f'<img src="{escape(image)}" alt="{escape(title)}" '
            f'class="ledajans-blog-card-img" width="640" height="400" '
            f'loading="{loading}" decoding="async"{prio}>'
        )
    cat = ""
    if cat_name:
        cat = (
            f'<a href="{escape(cat_link or "#")}" class="ledajans-blog-category">'
            f"{escape(cat_name)}</a>"
        )
    return (
        '          <article class="ledajans-blog-card">\n'
        '            <div class="ledajans-blog-card-img-wrap">\n'
        f'              <a href="{escape(link)}">\n'
        f"                {img}\n"
        "              </a>\n"
        "            </div>\n"
        '            <div class="ledajans-blog-card-body">\n'
        '              <div class="ledajans-blog-meta">\n'
        f"                <span>{escape(date)}</span><span>Ledajans Ekibi</span>\n"
        f"                {cat}\n"
        "              </div>\n"
        f'              <h3><a href="{escape(link)}">{escape(title)}</a></h3>\n'
        f'              <p class="ledajans-blog-excerpt">{escape(excerpt)}</p>\n'
        f'              <a href="{escape(link)}" class="ledajans-blog-link">Devamını oku</a>\n'
        "            </div>\n"
        "          </article>"
    )


NEW_JS_INIT = r"""
  function cardTitle(el){
    var h = el && el.querySelector('h3');
    return (h && (h.textContent || '') || '').replace(/\s+/g,' ').trim();
  }

  function appendRemainingPages(cards){
    var existingPages = getPages();
    var page1 = existingPages[0];
    if (!page1) {
      rebuildPages(cards);
      return Math.max(1, Math.ceil(cards.length / PAGE_SIZE));
    }
    existingPages.slice(1).forEach(function(p){ p.parentNode.removeChild(p); });
    var totalPages = Math.max(1, Math.ceil(cards.length / PAGE_SIZE));
    for (var p = 2; p <= totalPages; p++) {
      var page = document.createElement('div');
      page.className = 'ledajans-blog-page';
      page.setAttribute('data-page', String(p));
      var grid = document.createElement('div');
      grid.className = 'ledajans-blog-grid';
      cards.slice((p - 1) * PAGE_SIZE, p * PAGE_SIZE).forEach(function(card){ grid.appendChild(card); });
      page.appendChild(grid);
      pagesContainer.appendChild(page);
    }
    return totalPages;
  }

  async function init(){
    if (searchInput) searchInput.addEventListener('input', runSearch);
    goToPage(1);
    try {
      var posts = await fetchAllPosts();
      var cards = (posts || []).map(buildCard);
      var existing = getAllCards();
      var sameFirst = existing.length && cards.length && cardTitle(existing[0]) === cardTitle(cards[0]);
      if (sameFirst) {
        appendRemainingPages(cards);
        goToPage(currentPage);
      } else {
        rebuildPages(cards);
        goToPage(1);
      }
    } catch (e) {
      goToPage(1);
    }
  }

  init();
"""

OLD_JS_INIT = r"""
  async function init(){
    try {
      var posts = await fetchAllPosts();
      var cards = (posts || []).map(buildCard);
      rebuildPages(cards);
      goToPage(1);
    } catch (e) {
      var fallbackCards = getAllCards();
      rebuildPages(fallbackCards);
      goToPage(1);
    }
    if (searchInput) searchInput.addEventListener('input', runSearch);
  }

  init();
"""


def main() -> int:
    r = requests.get(
        "https://ledajans.com/wp-json/wp/v2/posts",
        params={
            "status": "publish",
            "orderby": "date",
            "order": "desc",
            "_embed": "1",
            "per_page": 6,
        },
        headers={"User-Agent": UA},
        timeout=60,
    )
    print("posts", r.status_code)
    if r.status_code != 200:
        print(r.text[:300])
        return 1
    posts = r.json()
    print("count", len(posts))
    for i, p in enumerate(posts):
        print(i, strip_tags((p.get("title") or {}).get("rendered") or ""), featured(p)[-60:])

    cards = "\n\n".join(card_html(p, i) for i, p in enumerate(posts))
    src = BLOG_FILE.read_text(encoding="utf-8")
    src2, n = re.subn(
        r'<article class="ledajans-blog-card">[\s\S]*?</article>(?:\s*<article class="ledajans-blog-card">[\s\S]*?</article>)*',
        cards,
        src,
        count=1,
    )
    print("cards_replaced", n)
    if n != 1:
        return 2
    if OLD_JS_INIT not in src2:
        print("HATA: eski init yok")
        return 3
    src2 = src2.replace(OLD_JS_INIT, NEW_JS_INIT, 1)
    if "appendRemainingPages" not in src2:
        print("HATA: js patch yok")
        return 3
    BLOG_FILE.write_text(src2, encoding="utf-8")
    print("wrote", BLOG_FILE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

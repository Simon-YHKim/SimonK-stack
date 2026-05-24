"""
blog-42morrow-mirror.py — AI 탐구노트 (42morrow.tistory.com) 910 글 풀 미러
사용:
    python scripts/blog-42morrow-mirror.py [--category <name>] [--limit N]

출력:
    E:/Coding Infra/obsidian/SimonKWiki/raw/clipped/blog-42morrow/<category>/<slug>.md

전제:
    uv pip install --system requests beautifulsoup4 lxml html2text
또는:
    pip install --user requests beautifulsoup4 lxml html2text

rate limit: 0.5초/요청, 카테고리 list 후 본문 fetch 순차
"""
import argparse
import os
import re
import sys
import time
from urllib.parse import urljoin

try:
    import requests
    from bs4 import BeautifulSoup
    import html2text
except ImportError as e:
    print(f"FATAL: missing dependency — {e}")
    print("Install: pip install --user requests beautifulsoup4 lxml html2text")
    sys.exit(1)

# Windows PowerShell CP949 console에서 한국어 + 특수문자 print 안전 처리
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE = "https://42morrow.tistory.com"
OUT_DIR = r"E:\Coding Infra\obsidian\SimonKWiki\raw\clipped\blog-42morrow"

# 카테고리: (URL path, max page count from earlier WebFetch)
CATEGORIES = {
    "AI-기술": ("/category/AI%20%EA%B8%B0%EC%88%A0", 39),
    "AI-관련-소식": ("/category/AI%20%EA%B4%80%EB%A0%A8%20%EC%86%8C%EC%8B%9D", 23),
    "DIY-테스트": ("/category/DIY%20%ED%85%8C%EC%8A%A4%ED%8A%B8", 12),
    "기술-팁": ("/category/%EA%B8%B0%EC%88%A0%20%ED%8C%81", 12),
    "유용한-정보": ("/category/%EC%9C%A0%EC%9A%A9%ED%95%9C%20%EC%A0%95%EB%B3%B4", 5),
    "생각하며-살기": ("/category/%EC%83%9D%EA%B0%81%ED%95%98%EB%A9%B0%20%EC%82%B4%EA%B8%B0", 2),
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0) SimonKWiki-Mirror/1.0 (personal archive, +https://github.com/Simon-YHKim/SimonKWiki)"
}

h2t = html2text.HTML2Text()
h2t.body_width = 0
h2t.ignore_images = False
h2t.ignore_links = False

def sanitize(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name).strip()
    return name[:120]

def fetch_url_list(cat_path: str, max_pages: int) -> list:
    """카테고리 페이지 모두 fetch → 글 URL list 추출 (중복 제거)"""
    urls = {}  # href → title
    for p in range(1, max_pages + 1):
        page_url = f"{BASE}{cat_path}?page={p}"
        try:
            r = requests.get(page_url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select('a[href^="/entry/"], a[href^="/m/entry/"]'):
                href = a.get('href', '').replace('/m/entry/', '/entry/')
                title = (a.get_text() or '').strip()
                # title이 비어있으면 부모 또는 형제에서 시도
                if not title:
                    parent = a.find_parent()
                    if parent:
                        title_el = parent.select_one('.title, .name, .post-title, h3, h4')
                        if title_el:
                            title = title_el.get_text().strip()
                if href and title and len(title) > 2 and not title.isdigit():
                    if href not in urls:
                        urls[href] = title
            time.sleep(0.5)
        except Exception as e:
            print(f"  page {p} error: {e}")
    return list(urls.items())

def fetch_article(url: str) -> tuple:
    """글 본문 fetch → (markdown, html_date) 반환"""
    full = urljoin(BASE, url)
    try:
        r = requests.get(full, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # date 추출
        date_str = ""
        for sel in ['.date', '.tt_post_date', 'time', '[itemprop="datePublished"]', '.entry-date']:
            d = soup.select_one(sel)
            if d:
                date_str = (d.get('datetime') or d.get_text() or '').strip()
                if date_str:
                    break

        # 본문 selector — tistory 여러 패턴
        content = None
        for sel in [
            '.entry-content', '.article-view', '.tt_article_useless_p_margin',
            '.post-content', '.contents_style', 'article.post', '#article'
        ]:
            content = soup.select_one(sel)
            if content:
                break

        if not content:
            # fallback: largest text block
            article = soup.find('article')
            if article:
                content = article

        if content:
            # 불필요 요소 제거
            for sel in ['script', 'style', '.share', '.related', '.tags', '.comment']:
                for el in content.select(sel):
                    el.decompose()
            md = h2t.handle(str(content))
            return (md.strip(), date_str)
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
    return (None, "")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', help='Single category name (default: all)')
    parser.add_argument('--limit', type=int, help='Max articles per category (default: all)')
    parser.add_argument('--skip-existing', action='store_true', default=True)
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)

    cats = {args.category: CATEGORIES[args.category]} if args.category else CATEGORIES

    total_new = 0
    total_skip = 0
    total_fail = 0

    for cat_name, (cat_path, max_pages) in cats.items():
        print(f"\n=== {cat_name} ({max_pages} pages) ===")
        cat_dir = os.path.join(OUT_DIR, cat_name)
        os.makedirs(cat_dir, exist_ok=True)

        urls = fetch_url_list(cat_path, max_pages)
        print(f"  collected {len(urls)} URLs")

        if args.limit:
            urls = urls[:args.limit]

        for i, (href, title) in enumerate(urls, 1):
            safe = sanitize(title)
            out_path = os.path.join(cat_dir, f"{safe}.md")
            if args.skip_existing and os.path.exists(out_path):
                total_skip += 1
                continue

            md, date_str = fetch_article(href)
            if md:
                front = f"""---
title: "{title.replace('"', "'")}"
source: "{BASE}{href}"
category: "{cat_name}"
fetched: "2026-05-25"
date: "{date_str}"
---

# {title}

"""
                try:
                    with open(out_path, 'w', encoding='utf-8') as f:
                        f.write(front + md)
                    total_new += 1
                    if total_new % 10 == 0:
                        print(f"  [{i}/{len(urls)}] {total_new} fetched: {title[:50]}")
                except Exception as e:
                    print(f"  WRITE ERROR {out_path}: {e}")
                    total_fail += 1
            else:
                total_fail += 1
            time.sleep(0.3)

    print(f"\n=== DONE: {total_new} new, {total_skip} skip, {total_fail} fail ===")

if __name__ == "__main__":
    main()

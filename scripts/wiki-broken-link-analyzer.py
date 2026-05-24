"""
wiki-broken-link-analyzer.py — SimonKWiki broken wikilinks 분류 + 자동 fix 후보 추출

사용:
    python scripts/wiki-broken-link-analyzer.py [--vault <path>] [--fix-suggest <out.md>]

분류:
    1. v1 → v2 migration 잔여 (예: 'rel-001-...' → 'soha-wife')
    2. 누락된 페이지 (실제로 작성 안 됨 — 후보 page list)
    3. typo (slug 약간 다름)
    4. 외부 link (http → 무시)

출력:
    markdown report — 카테고리별 broken count + fix 후보
"""
import argparse
import os
import re
import sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

WIKI = r"E:\Coding Infra\obsidian\SimonKWiki"
V1_TO_V2_PATTERNS = {
    # known v1 prefix → v2 slug (사용자 정정 가능)
    "self-001": "three-simons", "self-002": "9-circuits", "self-003": "birkman-9-components",
    "self-004": "mbti-recheck", "self-005": "life-arcs", "self-006": "decisive-events",
    "self-007": "current-pivot",
    "obj-001": "lg-innotek", "obj-002": "calendar-6y", "obj-003": "maps-timeline-9y",
    "obj-004": "toolstack-now", "obj-005": "sr-plasma-analysis",
    "rel-001": "soha-wife", "rel-002": "brother", "rel-003": "parents", "rel-004": "grandmother",
    "proj-001": "android-app-launch", "proj-002": "simonk-stack", "proj-003": "ai-pivot",
    "fut-001": "5y-vision", "fut-002": "body-health", "fut-003": "assessment-roadmap",
    "ai-001": "claude-personalization", "ai-002": "wiki-staleness-risks", "ai-003": "cowork-v2-bootstrap",
}

def find_all_pages(vault):
    """vault 안 모든 .md 파일 slug list (확장자 제거)"""
    slugs = {}
    for root, _, files in os.walk(os.path.join(vault, "wiki")):
        for f in files:
            if f.endswith(".md"):
                slug = f[:-3]
                slugs[slug.lower()] = os.path.relpath(os.path.join(root, f), vault)
    return slugs

def extract_wikilinks(filepath):
    """파일에서 [[wikilink]] 추출"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        # [[link]] / [[link|display]] / [[link#section]]
        return re.findall(r'\[\[([^\]|#]+)(?:\|[^\]]+)?(?:#[^\]]+)?\]\]', content)
    except Exception:
        return []

def normalize(link):
    """relative path normalize, /, \\ → /"""
    return link.replace('\\', '/').strip()

def slug_from_link(link):
    """link → slug (path 마지막 segment)"""
    parts = normalize(link).split('/')
    return parts[-1].lower()

def classify_broken(link, all_slugs):
    """broken link 분류"""
    if link.startswith('http'):
        return 'external'
    if link.startswith('_COMMUNITY'):
        return 'graphify-leak'
    slug = slug_from_link(link)
    # v1 prefix?
    for v1_pfx, v2_slug in V1_TO_V2_PATTERNS.items():
        if slug.startswith(v1_pfx.lower()):
            if v2_slug.lower() in all_slugs:
                return f'v1-migration: {v1_pfx} → {v2_slug}'
            else:
                return f'v1-migration-missing: {v1_pfx} → {v2_slug} (page 없음)'
    # typo check (Levenshtein 간략)
    for existing in all_slugs.keys():
        if abs(len(existing) - len(slug)) <= 2:
            # 60% 글자 같으면 typo 후보
            common = sum(1 for c in slug if c in existing)
            if common / max(len(slug), 1) > 0.6:
                return f'typo-candidate: {existing}'
    return 'missing-page'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vault', default=WIKI)
    parser.add_argument('--fix-suggest', default=None)
    args = parser.parse_args()

    all_slugs = find_all_pages(args.vault)
    print(f"# Wiki Broken Link Analyzer\n")
    print(f"vault: `{args.vault}`")
    print(f"existing pages: {len(all_slugs)}\n")

    broken = defaultdict(list)  # category → [(source, link)]
    total = 0

    for root, _, files in os.walk(os.path.join(args.vault, "wiki")):
        for f in files:
            if not f.endswith(".md"):
                continue
            fp = os.path.join(root, f)
            links = extract_wikilinks(fp)
            for link in links:
                slug = slug_from_link(link)
                if slug not in all_slugs:
                    category = classify_broken(link, all_slugs)
                    broken[category].append((os.path.relpath(fp, args.vault), link))
                    total += 1

    print(f"## Total broken: {total}\n")

    for category, items in sorted(broken.items(), key=lambda x: -len(x[1])):
        print(f"### {category} ({len(items)})")
        for src, link in items[:10]:
            print(f"- `{src}` → `[[{link}]]`")
        if len(items) > 10:
            print(f"- ... and {len(items)-10} more")
        print()

    if args.fix_suggest:
        with open(args.fix_suggest, 'w', encoding='utf-8') as f:
            f.write(f"# Wiki Broken Link Fix Suggestions\n\n")
            f.write(f"Total: {total} broken\n\n")
            for category, items in sorted(broken.items(), key=lambda x: -len(x[1])):
                f.write(f"## {category} ({len(items)})\n\n")
                for src, link in items:
                    f.write(f"- `{src}` → `[[{link}]]`\n")
                f.write("\n")
        print(f"\nFix suggestions saved: {args.fix_suggest}")

if __name__ == "__main__":
    main()

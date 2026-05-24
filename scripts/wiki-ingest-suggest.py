"""
wiki-ingest-suggest.py — raw/clipped/ 자료 → wiki/ 분류 추천 (Karpathy 7 카테고리)

사용:
    python scripts/wiki-ingest-suggest.py [--source <path>] [--limit N]

작동:
    1. raw/clipped/ (또는 명시 path) 안 .md 파일 list
    2. 각 파일의 title + 첫 paragraph → keyword 추출
    3. Karpathy 7 카테고리 매핑 (concepts/entities/events/arcs/projects/protocols/assessments)
    4. 추천 결과 markdown 표 출력

목적:
    사용자가 raw에 자료 누적 후 *어디로 ingest할지* 결정 보조.
    wiki-ingest skill의 사전 분류 추천 (실제 Write는 사용자 명시 후 simonK 진행).

전제:
    Python 표준 라이브러리만 (외부 X)
"""
import argparse
import os
import re
import sys

# Karpathy 7 카테고리 + keyword 매핑
CATEGORY_KEYWORDS = {
    "concepts": [
        # 추상 개념·프레임워크·이론
        "회로", "circuit", "이론", "theory", "framework", "프레임워크", "개념", "concept",
        "원리", "principle", "패턴", "pattern", "심리", "psychology", "Brain Trinity",
        "9 회로", "Birkman", "MBTI", "INTJ", "ISTJ", "self-analysis"
    ],
    "entities/people": [
        # 사람
        "와이프", "wife", "남편", "형", "동생", "부모님", "아버지", "어머니",
        "친구", "회장", "팀장", "공장장", "선배", "후배",
        "김재민", "성대한", "용걸이", "황승익"
    ],
    "entities/orgs": [
        # 조직
        "LG", "LG이노텍", "Innotek", "유라", "Yura", "HKMC", "Apple", "Tesla", "JLR", "PSA",
        "Google", "OpenAI", "Anthropic", "Microsoft", "회사", "기업"
    ],
    "entities/tools": [
        # 도구
        "Claude", "GPT", "Gemini", "Codex", "Cursor", "VS Code", "Obsidian", "Graphify",
        "OpenHarness", "Zotero", "NotebookLM", "TradingAgents", "Ollama", "BigQuery",
        "tool", "CLI", "API", "SDK", "framework", "library", "package"
    ],
    "entities/works": [
        # 본인 작품
        "SimonK-stack", "SimonKWiki", "Android app", "안드 앱", "Resonance",
        "SR Plasma", "MTBF", "Birkman 리포트", "Google Takeout"
    ],
    "events": [
        # 결정적 사건 (시점 + 한정된 사건, 사실만)
        "사건", "event", "면접", "interview", "출시", "launch", "골드런", "주차장",
        "파장동", "영국", "핸즈", "Award", "Q1", "Q2", "Q3", "Q4"
    ],
    "arcs": [
        # 시기 단위 호
        "Arc", "호", "시기", "year", "년", "decade", "phase", "period"
    ],
    "projects": [
        # 진행 중 프로젝트
        "project", "프로젝트", "안드 앱", "출시", "AI 피벗", "current pivot",
        "Phase 1", "Phase 2", "Phase 3", "Phase 4", "Phase 5", "Phase 6"
    ],
    "protocols": [
        # AI 운영·메타 규칙·SOP
        "SOP", "manual", "매뉴얼", "policy", "정책", "protocol", "operations",
        "blueprint", "청사진", "boundary", "회고", "retrospective", "lint"
    ],
    "assessments": [
        # 진단·검사 결과
        "Birkman", "MBTI", "Big5", "CliftonStrengths", "VIA", "ACT",
        "진단", "검사", "assessment", "test", "result"
    ],
}

def extract_title_and_intro(filepath: str) -> tuple:
    """파일에서 title + 첫 100자 추출"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(2000)  # 첫 2KB만
        title_match = re.search(r'^(?:title:\s*"?([^"\n]+)"?|# (.+))', content, re.MULTILINE)
        title = title_match.group(1) or title_match.group(2) if title_match else os.path.basename(filepath).replace('.md', '')
        # frontmatter 후 첫 paragraph
        body = re.sub(r'^---.*?---', '', content, flags=re.DOTALL).strip()
        intro = body[:200]
        return (title.strip(), intro.strip())
    except Exception as e:
        return (os.path.basename(filepath), f"<read error: {e}>")

def score_category(text: str) -> dict:
    """text에서 각 카테고리 keyword count → score dict 반환"""
    text_lower = text.lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw.lower() in text_lower:
                score += 1
        if score > 0:
            scores[cat] = score
    return scores

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default=r'E:\Coding Infra\obsidian\SimonKWiki\raw\clipped',
                        help='raw 자료 위치 (default: raw/clipped/)')
    parser.add_argument('--limit', type=int, default=50,
                        help='최대 분석 파일 수 (default: 50)')
    args = parser.parse_args()

    files = []
    for root, _, fnames in os.walk(args.source):
        for fn in fnames:
            if fn.endswith('.md'):
                files.append(os.path.join(root, fn))
    files = sorted(files)[:args.limit]

    print(f"# wiki-ingest 추천 — {len(files)} 자료\n")
    print(f"source: `{args.source}`\n")
    print("| # | title | top category | score | filename |")
    print("|---|-------|--------------|-------|----------|")

    for i, fp in enumerate(files, 1):
        title, intro = extract_title_and_intro(fp)
        scores = score_category(title + ' ' + intro)
        if scores:
            top = max(scores.items(), key=lambda x: x[1])
            top_cat, top_score = top[0], top[1]
        else:
            top_cat, top_score = "(unmatched — manual review)", 0
        # title sanitize for table
        title_safe = title.replace('|', '/').replace('\n', ' ')[:60]
        fn = os.path.basename(fp)[:50]
        print(f"| {i} | {title_safe} | `{top_cat}` | {top_score} | {fn} |")

    print("\n## 추천 활용")
    print("1. top category가 `entities/tools` 이면 → `wiki/entities/tools/<slug>.md` ingest")
    print("2. `(unmatched)` 이면 → 사용자 본인 분류 (Claude 추정 X, Karpathy 규칙 6 준수)")
    print("3. 본 추천은 *keyword 기반* — 의미 분석 X. wiki-ingest skill (LLM) 이 본격 처리.")

if __name__ == "__main__":
    main()

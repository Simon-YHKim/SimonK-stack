"""
fetch-model-benchmarks.py — LLM 벤치마크 leaderboard fetcher + wiki updater

목적:
    SimonKWiki 의 wiki/concepts/ai-model-benchmarks.md 를 최신 벤치마크 데이터로 갱신.
    주 1회 cron 실행 (run-wiki-lint.ps1 통합).

수집 대상:
    1. lmarena.ai/leaderboard      — Arena Elo (코딩 / general)
    2. vellum.ai/llm-leaderboard   — comprehensive (SWE-bench, MMLU 등)
    3. llm-stats.com               — 가격 + speed
    4. aider.chat/docs/leaderboards — Polyglot code edit
    5. swebench.com                — SWE-bench Verified

출력:
    - wiki/concepts/ai-model-benchmarks.md `last-updated` 자동 bump
    - .simonk/benchmarks-cache.json (raw fetched data, 백업)
    - wiki/log.md LINT 기록

사용:
    python scripts/fetch-model-benchmarks.py [--dry-run] [--source lmarena|vellum|all]

주의:
    - HTML 구조 변경 시 parser 갱신 필요 (sites 마다 frequent redesign)
    - rate limit 준수 (User-Agent 박음, 2초 sleep 사이)
    - API 가 있으면 우선 사용 (HTML scrape 는 fallback)
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

WIKI_DIR = os.environ.get('SIMON_WIKI_DIR', r'C:\Coding\obsidian\SimonKWiki')
WIKI_PAGE = os.path.join(WIKI_DIR, 'wiki', 'concepts', 'ai-model-benchmarks.md')
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', '.simonk')
CACHE_FILE = os.path.join(CACHE_DIR, 'benchmarks-cache.json')
USER_AGENT = 'SimonK-stack-benchmark-fetcher/0.1 (+https://github.com/Simon-YHKim/SimonK-stack)'

SOURCES = {
    'lmarena': {
        'url': 'https://lmarena.ai/leaderboard',
        'name': 'LM Arena',
        'description': 'Arena Elo by category (코딩, general, vision, ...)',
    },
    'vellum': {
        'url': 'https://www.vellum.ai/llm-leaderboard',
        'name': 'Vellum LLM Leaderboard',
        'description': 'SWE-bench / MMLU / GPQA / HLE comprehensive',
    },
    'llm-stats': {
        'url': 'https://llm-stats.com/',
        'name': 'LLM Stats',
        'description': '300+ models, price + intelligence + speed',
    },
    'aider': {
        'url': 'https://aider.chat/docs/leaderboards/',
        'name': 'Aider Polyglot',
        'description': '다국어 code edit 정확도',
    },
    'swebench': {
        'url': 'https://www.swebench.com/',
        'name': 'SWE-bench Verified',
        'description': '실제 GitHub issue resolve rate',
    },
}


def fetch(url: str, timeout: int = 30) -> str | None:
    """단순 GET, User-Agent 박음. 실패 시 None."""
    req = Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='replace')
    except (URLError, HTTPError) as e:
        print(f"[fetch-fail] {url}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[fetch-error] {url}: {e}", file=sys.stderr)
        return None


def parse_lmarena(html: str) -> dict:
    """LM Arena leaderboard 파싱.

    lmarena.ai 는 Next.js SPA. JSON endpoint 시도:
    - /api/leaderboard (직접)
    - _next/data/<build-id>/leaderboard.json (Next.js static data)
    """
    out = {
        'source': 'lmarena',
        'fetched_at': datetime.utcnow().isoformat(),
        'models': [],
    }
    # 1) Try direct JSON endpoint
    json_url = 'https://lmarena.ai/api/leaderboard'
    json_html = fetch(json_url)
    if json_html:
        try:
            data = json.loads(json_html)
            # JSON 구조 추정: {"models": [{"name": "...", "arena_score": 1548, ...}, ...]}
            if isinstance(data, dict) and 'models' in data:
                for m in data['models'][:30]:
                    out['models'].append({
                        'name': m.get('name') or m.get('model'),
                        'arena_elo': m.get('arena_score') or m.get('elo'),
                        'category': m.get('category'),
                    })
                out['status'] = f"parsed {len(out['models'])} models from /api/leaderboard JSON"
                return out
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    # 2) Fallback: parse HTML for model+score patterns (rough regex)
    if html:
        # Pattern: 'model_name' followed by 4-digit score
        matches = re.findall(r'"name"\s*:\s*"([^"]+)"[^}]*?"(?:arena_score|elo|score)"\s*:\s*(\d{3,5})', html)
        for name, score in matches[:30]:
            out['models'].append({'name': name, 'arena_elo': int(score)})
        out['status'] = f"parsed {len(out['models'])} models (HTML regex fallback)"
    else:
        out['status'] = 'fetch failed (both JSON endpoint + HTML)'
    return out


def parse_vellum(html: str) -> dict:
    """Vellum leaderboard 파싱.

    TODO: vellum.ai 의 leaderboard table 구조. React/Next.js SPA 가능성 → JSON 우선.
    """
    return {
        'source': 'vellum',
        'fetched_at': datetime.utcnow().isoformat(),
        'status': 'TODO: parser 미구현',
        'raw_length': len(html) if html else 0,
        'models': [],
    }


def parse_swebench(html: str) -> dict:
    """SWE-bench leaderboard. JSON endpoint 또는 정적 table."""
    # SWE-bench 는 github io static page — table 가능성
    out = {
        'source': 'swebench',
        'fetched_at': datetime.utcnow().isoformat(),
        'models': [],
    }
    if not html:
        out['status'] = 'fetch failed'
        return out
    # 가장 간단한 패턴: model name + percentage
    matches = re.findall(r'([A-Z][\w\-\s\.]+(?:Opus|Sonnet|Haiku|GPT|Gemini|Claude|Grok)[\w\-\.]*)\s*[|\s]\s*(\d+\.?\d*)%', html)
    for name, score in matches[:20]:
        out['models'].append({'name': name.strip(), 'swe_bench_verified_pct': float(score)})
    out['status'] = f"parsed {len(out['models'])} models (rough regex)"
    return out


PARSERS = {
    'lmarena': parse_lmarena,
    'vellum': parse_vellum,
    'llm-stats': lambda h: {'source': 'llm-stats', 'status': 'TODO', 'models': []},
    'aider': lambda h: {'source': 'aider', 'status': 'TODO', 'models': []},
    'swebench': parse_swebench,
}


def collect(source_filter: str = 'all') -> dict:
    """모든 source fetch + parse. dict source_id → parsed data."""
    out = {}
    targets = SOURCES.keys() if source_filter == 'all' else [source_filter]
    for sid in targets:
        if sid not in SOURCES:
            print(f"[skip] unknown source: {sid}")
            continue
        url = SOURCES[sid]['url']
        print(f"[fetch] {sid}: {url}")
        html = fetch(url)
        out[sid] = PARSERS[sid](html or '')
        time.sleep(2)  # rate limit
    return out


def update_wiki_timestamp() -> bool:
    """wiki page 의 last-updated frontmatter 만 갱신 (실 데이터 merge 는 TODO)."""
    if not os.path.exists(WIKI_PAGE):
        print(f"[wiki-update] page missing: {WIKI_PAGE}", file=sys.stderr)
        return False
    content = open(WIKI_PAGE, encoding='utf-8').read()
    today = datetime.now().strftime('%Y-%m-%d')
    new_content = re.sub(r'^last-updated:\s*\S+', f'last-updated: {today}', content, count=1, flags=re.MULTILINE)
    if new_content != content:
        open(WIKI_PAGE, 'w', encoding='utf-8').write(new_content)
        print(f"[wiki-update] last-updated → {today}")
        return True
    return False


def save_cache(data: dict) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[cache] {CACHE_FILE} ({sum(len(d.get('models', [])) for d in data.values())} models total)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', default='all', help='all | lmarena | vellum | llm-stats | aider | swebench')
    ap.add_argument('--dry-run', action='store_true', help='fetch + cache, wiki 갱신 X')
    args = ap.parse_args()

    print(f"# fetch-model-benchmarks.py — {datetime.now().isoformat()}")
    print(f"sources: {args.source}, dry-run: {args.dry_run}")

    data = collect(args.source)
    save_cache(data)

    if not args.dry_run:
        update_wiki_timestamp()

    # Summary
    total_models = sum(len(d.get('models', [])) for d in data.values())
    print(f"\n=== Summary ===")
    for sid, d in data.items():
        print(f"  {sid}: {d.get('status', '?')} ({len(d.get('models', []))} models)")
    print(f"  Total: {total_models} model entries cached")
    print(f"  Wiki page: {WIKI_PAGE}")
    print(f"  Cache: {CACHE_FILE}")

    # TODO: 다음 sprint
    # 1. 각 parser 실제 구현 (HTML inspect 후 정확한 selector)
    # 2. Vellum / llm-stats API endpoint 발견 시 JSON 우선
    # 3. 신규 모델 자동 감지 → wiki 의 § 1 Frontier 모델 table 행 추가
    # 4. 가격 변동 감지 → § 4 가격 + 컨텍스트 table 갱신
    # 5. 작업 type → best model 매핑 자동 재계산 (벤치마크 가중 평균)
    return 0


if __name__ == '__main__':
    sys.exit(main())

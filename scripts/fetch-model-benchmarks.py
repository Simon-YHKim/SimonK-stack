"""
fetch-model-benchmarks.py — unverified leaderboard collection, not a Wiki updater

목적:
    Collect raw benchmark candidates for later review. No validated data merge
    exists here, so this command never edits Wiki content, dates, logs or routing.

수집 대상:
    1. lmarena.ai/leaderboard      — Arena Elo (코딩 / general)
    2. vellum.ai/llm-leaderboard   — comprehensive (SWE-bench, MMLU 등)
    3. llm-stats.com               — 가격 + speed
    4. aider.chat/docs/leaderboards — Polyglot code edit
    5. swebench.com                — SWE-bench Verified

출력:
    - .simonk/benchmarks-cache.json: source-keyed, UNVERIFIED raw observations
    - attempted_at is a collection attempt, never the source data's as-of date
    - rc=0: every requested source yielded structurally usable raw rows
    - rc=2: incomplete/invalid collection or cache write failure; prior cache kept
    - --dry-run performs collection but never writes any files

사용:
    python scripts/fetch-model-benchmarks.py [--dry-run] [--source lmarena|vellum|all]

주의:
    - HTML 구조 변경 시 parser 갱신 필요 (sites 마다 frequent redesign)
    - rate limit 준수 (User-Agent 박음, 2초 sleep 사이)
    - API 가 있으면 우선 사용 (HTML scrape 는 fallback)
"""

import argparse
import json
import math
import os
import re
import sys
import time
import tempfile
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

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
        'models': [],
    }
    # 1) Try direct JSON endpoint
    json_url = 'https://lmarena.ai/api/leaderboard'
    json_html = fetch(json_url)
    if json_html:
        try:
            data = json.loads(json_html)
            # JSON 구조 추정: {"models": [{"name": "...", "arena_score": 1548, ...}, ...]}
            if isinstance(data, dict) and isinstance(data.get('models'), list):
                for m in data['models'][:30]:
                    if not isinstance(m, dict):
                        out['models'].append(m)  # Collection gate reports invalid rows.
                        continue
                    out['models'].append({
                        'name': m.get('name') or m.get('model'),
                        'arena_elo': m.get('arena_score', m.get('elo')),
                        'category': m.get('category'),
                    })
                out['status'] = f"parsed {len(out['models'])} models from /api/leaderboard JSON"
                return out
            out['status'] = 'incompatible JSON model list'
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
        'status': 'TODO: parser 미구현',
        'raw_length': len(html) if html else 0,
        'models': [],
    }


def parse_swebench(html: str) -> dict:
    """SWE-bench leaderboard. JSON endpoint 또는 정적 table."""
    # SWE-bench 는 github io static page — table 가능성
    out = {
        'source': 'swebench',
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


def usable_row(source: str, row) -> bool:
    """Shape/range checks only, NOT benchmark authenticity or model validation."""
    if not isinstance(row, dict) or not isinstance(row.get('name'), str) or not row['name'].strip():
        return False
    metric = {'lmarena': 'arena_elo', 'swebench': 'swe_bench_verified_pct'}.get(source)
    score = row.get(metric)
    if type(score) not in (int, float) or not math.isfinite(score) or score < 0:
        return False
    return metric is not None and (source != 'swebench' or score <= 100)


def collect(source_filter: str = 'all') -> dict:
    """Return source-keyed unverified observations; a timestamp is not freshness."""
    if source_filter != 'all' and source_filter not in SOURCES:
        raise ValueError('Unknown source')
    out = {}
    targets = SOURCES.keys() if source_filter == 'all' else [source_filter]
    for sid in targets:
        attempted_at = datetime.now(timezone.utc).isoformat()
        url = SOURCES[sid]['url']
        print(f"[fetch] {sid}: {url}")
        try:
            html = fetch(url)
            item = PARSERS[sid](html or '')
            rows = item.get('models')
            if not isinstance(rows, list):
                raise ValueError('Parser did not return a model list')
            invalid = sum(not usable_row(sid, row) for row in rows)
            item.update(complete=bool(rows) and not invalid, invalid_rows=invalid)
        except Exception as exc:
            # Do not include arbitrary response/error text in the cache.
            item = {'models': [], 'complete': False, 'invalid_rows': 0,
                    'status': 'parser/collection failure: ' + type(exc).__name__}
        item.update(source=sid, source_url=url, attempted_at=attempted_at,
                    validation_status='unverified', data_as_of=None, wiki_updated=False)
        out[sid] = item
        time.sleep(2)  # rate limit
    return out


def save_cache(data: dict) -> None:
    """Replace a complete raw snapshot atomically; never truncate a prior cache."""
    payload = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    directory = os.path.dirname(os.path.abspath(CACHE_FILE))
    os.makedirs(directory, exist_ok=True)
    pending = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=directory,
                                         prefix='.benchmark-', suffix='.tmp', delete=False) as f:
            pending = f.name
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(pending, CACHE_FILE)
        pending = None
    finally:
        if pending is not None:
            os.unlink(pending)  # Only this invocation's temporary file.


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', default='all', choices=['all', *SOURCES])
    ap.add_argument('--dry-run', action='store_true', help='collect and report only; no files written (network is still used)')
    args = ap.parse_args()

    print(f"# fetch-model-benchmarks.py — {datetime.now(timezone.utc).isoformat()}")
    print(f"sources: {args.source}, dry-run: {args.dry_run}")

    data = collect(args.source)
    # Summary
    total_models = sum(len(d.get('models', [])) for d in data.values())
    print(f"\n=== Summary ===")
    for sid, d in data.items():
        state = 'raw-complete' if d['complete'] else 'incomplete'
        print(f"  {sid}: {state}; {d.get('status', '?')} ({len(d['models'])} raw rows, {d['invalid_rows']} invalid)")
    print(f"  Total: {total_models} raw rows; validation_status=unverified; data_as_of=unknown")
    print('  Wiki unchanged: no validated data merge is implemented; routing registry unchanged.')
    if not data or not all(item['complete'] for item in data.values()):
        print('  Collection incomplete; cache not written, any previous cache preserved.')
        return 2
    if args.dry_run:
        print('  Dry-run: cache not written; no files changed.')
        return 0
    try:
        save_cache(data)
    except (OSError, TypeError, ValueError) as exc:
        print('  Cache not written: ' + type(exc).__name__, file=sys.stderr)
        return 2
    print(f"  Unverified raw cache written: {CACHE_FILE}")
    return 0


if __name__ == '__main__':
    sys.exit(main())

"""
analyze-42morrow.py — 42morrow.tistory.com 940+ 글 자동 태그 + 카탈로그 생성

raw/clipped/blog-42morrow/ 폴더 walk → 제목 기반 키워드 분류 → wiki/concepts/blog-42morrow-curated.md 자동 생성.

사용:
    python scripts/analyze-42morrow.py [--dry-run]
"""

import os
import re
import sys
from collections import defaultdict
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

VAULT = os.environ.get('SIMON_WIKI_DIR', r'C:\Coding\obsidian\SimonKWiki')
RAW_DIR = os.path.join(VAULT, 'raw', 'clipped', 'blog-42morrow')
OUT_PAGE = os.path.join(VAULT, 'wiki', 'concepts', 'blog-42morrow-curated.md')
OUT_INDEX = os.path.join(VAULT, 'wiki', 'concepts', 'blog-42morrow-full-index.md')

# 기술 영역 태그 — 키워드 매핑 (제목에서 keyword 매칭 시 해당 태그 부여)
TAGS = {
    'LLM': ['LLM', 'GPT', 'Claude', 'Gemini', 'Qwen', 'DeepSeek', 'Llama', 'Mistral', 'Grok', 'GLM', '언어모델', '대형 언어', 'Mixtral', 'Phi', 'Yi', 'Falcon', '챗봇', 'ChatGPT', 'chatgpt', 'Anthropic', 'OpenAI'],
    'RAG': ['RAG', 'retrieval', 'augmented', '검색 증강', '벡터DB', 'pinecone', 'chroma', 'qdrant', 'weaviate', '검색', 'search engine', 'embedding'],
    'Agent': ['agent', 'Agent', '에이전트', 'autonomous', '자율', 'AutoGPT', 'CrewAI', 'LangGraph', 'multi-agent', 'AI 에이전트', 'AI Agent'],
    'Vision': ['vision', 'image', '이미지', '비전', 'OCR', 'segmentation', 'detection', '이미지 생성', 'Stable Diffusion', 'SDXL', 'FLUX', 'ControlNet', 'Midjourney', 'DALL-E', '그림', '사진', 'photo', '복원', 'upscale', 'inpaint', 'background', '배경 제거', '얼굴', 'face'],
    'Video': ['video', '비디오', '영상', 'Sora', 'Runway', 'Pika', 'animatediff', 'V2V', 'AnimateDiff', '동영상', '편집', 'editing', '움직임', 'motion', 'frame', 'clip'],
    'Audio_Music': ['audio', 'music', '음악', '음성', 'TTS', 'STT', 'Whisper', 'Suno', 'Udio', 'MusicGen', 'voice', '보컬', '노래', '사운드', 'sound', '오디오', '말투', 'speech'],
    'Avatar_3D': ['avatar', '아바타', '3D', 'NeRF', 'gaussian', 'mesh', 'rigging', 'character', '캐릭터', 'animation', '애니메이션', 'lip-sync', '립싱크', 'face animation'],
    'Code_AI': ['code', 'coding', '코드', '개발', 'Copilot', 'Codex', 'Cursor', 'Cline', 'Aider', 'Devin', 'SWE', 'programming', '프로그래밍', 'GitHub', 'IDE', 'Claude Code'],
    'MCP': ['MCP', 'Model Context Protocol'],
    'Local_LLM': ['Ollama', 'LM Studio', 'llama.cpp', '로컬', 'local', 'quantization', 'GGUF', 'GGML', 'on-device', 'CPU', '오픈소스', 'open-source', 'open source'],
    'Tool_Workflow': ['워크플로', 'workflow', '자동화', 'automation', 'n8n', 'ComfyUI', 'Make', 'Zapier', 'Pipedream', '플로우', 'flow'],
    'Training_Finetune': ['fine-tuning', 'finetune', '파인튜닝', 'LoRA', 'PEFT', '학습', 'training', 'RLHF', 'DPO', 'pretraining', '사전 학습', '데이터셋', 'dataset'],
    'Reasoning': ['reasoning', '추론', 'CoT', 'chain of thought', 'o1', 'o3', 'thinking', 'reflection', '사고', '논리'],
    'Robotics': ['robot', 'robotics', '로봇', 'embodied', 'manipulation', '로보', '드론', 'drone'],
    'Game_AI': ['game', '게임', 'NPC', 'Unity', 'Unreal', 'minecraft', 'roblox'],
    'API_Service': ['API', 'service', '서비스', 'OpenRouter', 'together.ai', 'Groq', 'Cerebras', 'Replicate', 'Hugging Face', 'HuggingFace', 'huggingface'],
    'Benchmark_Eval': ['benchmark', 'eval', '평가', 'MMLU', 'SWE-bench', 'HLE', 'GPQA', '리더보드', 'leaderboard', '성능 비교', '비교'],
    'Hardware_GPU': ['GPU', 'NVIDIA', 'CUDA', 'A100', 'H100', 'B200', '하드웨어', 'Apple Silicon', 'M3', 'M4', '칩', 'chip'],
    'Korean': ['한국어', '한글', 'KoBALT', 'Naver', '네이버', 'Kakao', '카카오', 'LG AI Research', 'EXAONE', '한국'],
    'AI_News': ['소식', '뉴스', '발표', 'announce', 'release', '출시', '공개', '업데이트', 'update', '발표회'],
    'Web_App': ['웹', 'web', '앱', 'app', 'application', '사이트', 'site', 'platform', '플랫폼'],
    'Tutorial_Howto': ['튜토리얼', 'tutorial', 'how to', '방법', '사용법', '가이드', 'guide', '쉽게', '간단하게'],
    'Data_Analysis': ['데이터', 'data', '분석', 'analysis', '시각화', 'visualization', '차트', 'chart', 'graph', '그래프'],
    'Healthcare': ['헬스', 'health', '의료', 'medical', '진단', 'diagnosis', '건강'],
    'Finance': ['금융', 'finance', '주식', 'stock', '트레이딩', 'trading', '코인', 'crypto'],
    'Productivity': ['생산성', 'productivity', '효율', 'efficiency', '시간 관리', '업무'],
    'Education_Learning': ['교육', 'education', '학습', 'learning', '강의', 'lecture', '수업', '연구', 'research'],
    'Research_Paper': ['paper', '논문', '연구', 'research', 'arXiv', '학회'],
}

CATEGORY_DESC = {
    'AI-기술': '핵심 AI 기술·기법·모델 (385+ 글)',
    'AI-관련-소식': 'AI 산업·연구 뉴스 (230+ 글)',
    'DIY-테스트': '실험·구현 사례 (121+ 글)',
    '기술-팁': '실무 팁·trick (123+ 글)',
    '유용한-정보': '리소스·툴 추천 (52+ 글)',
    '생각하며-살기': '메타·사색 (15+ 글)',
}


def tag_title(title: str) -> list[str]:
    """제목 → 태그 list (대소문자 무시)"""
    title_low = title.lower()
    tags = []
    for tag, kws in TAGS.items():
        for kw in kws:
            if kw.lower() in title_low:
                tags.append(tag)
                break
    return tags or ['Unclassified']


def main():
    if not os.path.isdir(RAW_DIR):
        print(f"[error] raw dir 미존재: {RAW_DIR}", file=sys.stderr)
        return 1

    # Walk
    posts = []  # (category, title, tags, filename)
    cat_count = defaultdict(int)
    tag_count = defaultdict(int)
    tag_to_posts = defaultdict(list)  # tag → [(category, title, filename)]

    for cat in sorted(os.listdir(RAW_DIR)):
        cat_dir = os.path.join(RAW_DIR, cat)
        if not os.path.isdir(cat_dir):
            continue
        for fname in os.listdir(cat_dir):
            if not (fname.endswith('.html') or fname.endswith('.md')):
                continue
            # title = filename without ext
            title = os.path.splitext(fname)[0]
            tags = tag_title(title)
            posts.append((cat, title, tags, fname))
            cat_count[cat] += 1
            for t in tags:
                tag_count[t] += 1
                tag_to_posts[t].append((cat, title, fname))

    total = len(posts)
    print(f"Total posts: {total}")
    print(f"Categories: {dict(cat_count)}")
    print(f"Top 10 tags:")
    for t, c in sorted(tag_count.items(), key=lambda x: -x[1])[:10]:
        print(f"  {t}: {c}")

    # Generate wiki page
    lines = [
        '---',
        'title: "blog-42morrow 큐레이션 카탈로그 — 기술 영역별 태그 분류"',
        'category: concepts',
        'type: catalog',
        f'created: 2026-05-25',
        f'last-updated: {datetime.now().strftime("%Y-%m-%d")}',
        'status: refined',
        'source: "raw/clipped/blog-42morrow/ (940+ 글, 2026-05 mirror)"',
        'auto-generated: scripts/analyze-42morrow.py',
        'tags: [catalog, blog, 42morrow, ai-curated, korean, learning-resource]',
        'related:',
        '  - "[[../entities/tools/blog-42morrow]]"',
        '  - "[[ai-model-benchmarks]]"',
        '  - "[[multi-agent-dispatch]]"',
        '  - "[[../projects/ai-pivot]]"',
        '---',
        '',
        '# blog-42morrow 큐레이션 카탈로그',
        '',
        f'42morrow.tistory.com 풀 미러 **{total} 글** 자동 분류 (제목 기반 키워드 태깅). raw 보존: `raw/clipped/blog-42morrow/`.',
        '',
        '> 자동 생성 — `python scripts/analyze-42morrow.py` 재실행 시 갱신.',
        '',
        '## 카테고리별 분포 (raw 폴더 기준)',
        '',
        '| 카테고리 | 글 수 | 설명 |',
        '|---|---|---|',
    ]
    for cat, cnt in sorted(cat_count.items(), key=lambda x: -x[1]):
        desc = CATEGORY_DESC.get(cat, '')
        lines.append(f'| `{cat}` | {cnt} | {desc} |')

    lines += [
        '',
        '## 기술 영역 태그별 분포 (자동 분류)',
        '',
        '| 태그 | 글 수 | 기존 wiki 연결 |',
        '|---|---|---|',
    ]
    # Tag → related wiki page mapping
    TAG_WIKI = {
        'LLM': '[[ai-model-benchmarks]]',
        'Agent': '[[multi-agent-dispatch]] · [[../entities/tools/omc]] · [[../entities/tools/openharness]]',
        'Code_AI': '[[../projects/simonk-stack]] · [[../entities/tools/omc]]',
        'MCP': '[[../protocols/mcp-integration]] · [[../entities/tools/openharness]]',
        'Local_LLM': '[[../entities/tools/openharness]] · [[../projects/ai-pivot]]',
        'Benchmark_Eval': '[[ai-model-benchmarks]]',
        'Korean': '[[ai-model-benchmarks]] § 한국어 (Claude Sonnet 4.6 / GLM-5)',
        'Training_Finetune': '[[../projects/ai-pivot]]',
        'Reasoning': '[[ai-model-benchmarks]] § REASONING_ABSTRACT',
        'RAG': '[[chatgpt-ingest-method]] (유사 패턴)',
        'Vision': '[[ai-model-benchmarks]] § VISION (Gemini 3.1 Pro)',
        'Tool_Workflow': '[[../entities/tools/toolstack-now]]',
        'API_Service': '[[ai-model-benchmarks]] § 가격',
    }
    for t, c in sorted(tag_count.items(), key=lambda x: -x[1]):
        link = TAG_WIKI.get(t, '—')
        lines.append(f'| **{t}** | {c} | {link} |')

    lines += [
        '',
        '## 우선순위 학습 path (Simon AI 도메인 pivot)',
        '',
        '본인 [[../projects/ai-pivot]] 직접 연관 태그 우선:',
        '',
        '1. **Code_AI + Agent** — [[../projects/simonk-stack]] 직접 적용',
        '2. **LLM + Benchmark_Eval** — [[ai-model-benchmarks]] 매트릭스 갱신',
        '3. **Local_LLM + MCP** — [[../entities/tools/openharness]] 폐쇄망 운영',
        '4. **Training_Finetune** — Phase 4 (7~9월) 후보',
        '5. **Korean** — 한국어 도메인 specialty',
        '',
        '나머지 태그 (Vision/Video/Audio/Game) — 본인 도메인 외, 참조 정도.',
        '',
        '## Sample 글 (태그별 top 3, raw filename)',
        '',
    ]

    # Top tags 별 sample 3개 (link 형식: special char filename 은 markdown link fallback)
    def safe_link(cat, stem, disp):
        """Obsidian wikilink 처리 못 하는 special char (nested bracket, trailing space, nbsp 등) 면 markdown link."""
        path = f'../../raw/clipped/blog-42morrow/{cat}/{stem}'
        # wikilink 깨지는 패턴: [ ] | # · trailing whitespace · nbsp(\xa0) · tab/CR/LF
        if (any(ch in stem for ch in '[]|#')
                or stem != stem.strip()
                or '\xa0' in stem
                or any(c in stem for c in '\t\r\n')):
            from urllib.parse import quote
            encoded = quote(path + '.md', safe='/')
            return f'[{disp}]({encoded})'
        return f'[[{path}|{disp}]]'

    for t, c in sorted(tag_count.items(), key=lambda x: -x[1])[:8]:
        lines.append(f'### {t} ({c} 글)')
        for cat, title, fname in tag_to_posts[t][:3]:
            stem = os.path.splitext(fname)[0]
            disp = title[:60] + ('...' if len(title) > 60 else '')
            lines.append(f'- {safe_link(cat, stem, disp)}')
        if len(tag_to_posts[t]) > 3:
            lines.append(f'- ... 외 {len(tag_to_posts[t]) - 3} 글 — 전체 link 는 [[blog-42morrow-full-index]] 참조')
        lines.append('')

    lines += [
        '## 갱신 cadence',
        '',
        '- 매주 cron (`.simonk-cron/run-wiki-lint.ps1`) 의 fetch + analyze 시 자동 갱신',
        '- 신규 42morrow 글 발견 시 (Section 3.5 RSS Monitor) 그 글의 태그 자동 추가',
        '- 태그 매핑 추가/수정 시 `scripts/analyze-42morrow.py` 의 `TAGS` dict 갱신 후 재실행',
        '',
        '## 관련',
        '',
        '- [[blog-42morrow-full-index]] — 942 글 전체 wikilink 인덱스 (graph hub, 자동 생성)',
        '- [[blog-42morrow-papers]] — raw/clipped/papers/ 6 글 인덱스 (script 외부, manual)',
        '- [[../entities/tools/blog-42morrow]] — 블로그 자체 entity 페이지',
        '- [[ai-model-benchmarks]] — 모델 매트릭스 (LLM/Benchmark 태그 연결)',
        '- [[multi-agent-dispatch]] — Agent 태그 패턴 적용',
        '- [[../projects/ai-pivot]] — Simon AI 도메인 pivot project (학습 source)',
        '- [[../protocols/mcp-integration]] — MCP 태그 연결',
        '- [[chatgpt-ingest-method]] — ingest 방법론 (RAG 패턴 유사)',
    ]

    content = '\n'.join(lines) + '\n'

    if '--dry-run' in sys.argv:
        print(f"\n[DRY-RUN] Would write {OUT_PAGE} ({len(content)} chars)")
        print("---preview---")
        print(content[:1500])
        return 0

    os.makedirs(os.path.dirname(OUT_PAGE), exist_ok=True)
    with open(OUT_PAGE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n[done] {OUT_PAGE} ({len(content)} chars)")

    # === Full index page (graph hub) — 942 글 전체 wikilink ===
    idx_lines = [
        '---',
        'title: "blog-42morrow — 942 글 전체 wikilink 인덱스 (graph hub)"',
        'category: concepts',
        'type: graph-hub',
        'created: 2026-05-25',
        f'last-updated: {datetime.now().strftime("%Y-%m-%d")}',
        'status: refined',
        'source: "raw/clipped/blog-42morrow/ (940+ 글)"',
        'auto-generated: scripts/analyze-42morrow.py',
        'tags: [catalog, blog, 42morrow, graph-hub, auto-generated]',
        'related:',
        '  - "[[blog-42morrow-curated]]"',
        '  - "[[../entities/tools/blog-42morrow]]"',
        '---',
        '',
        '# blog-42morrow — 942 글 전체 wikilink 인덱스',
        '',
        '> **목적**: 942 raw 글을 Obsidian graph 의 단일 hub 로 묶기. 사람용 카탈로그는 [[blog-42morrow-curated]].',
        f'> **자동 생성** — `python scripts/analyze-42morrow.py` 재실행 시 갱신. 총 {total} 글.',
        '',
    ]
    # 카테고리 별 sub-section
    posts_by_cat = defaultdict(list)
    for cat, title, tags, fname in posts:
        posts_by_cat[cat].append((title, tags, fname))
    from urllib.parse import quote
    for cat in sorted(posts_by_cat.keys(), key=lambda c: -len(posts_by_cat[c])):
        idx_lines.append(f'## {cat} ({len(posts_by_cat[cat])} 글)')
        idx_lines.append('')
        for title, tags, fname in sorted(posts_by_cat[cat], key=lambda x: x[2]):
            stem = os.path.splitext(fname)[0]
            disp = title[:80] + ('...' if len(title) > 80 else '')
            tag_str = ' · '.join(tags[:3])
            path = f'../../raw/clipped/blog-42morrow/{cat}/{stem}'
            # special char (nested bracket, trailing whitespace, nbsp, control char) → markdown link fallback
            if (any(ch in stem for ch in '[]|#')
                    or stem != stem.strip()
                    or '\xa0' in stem
                    or any(c in stem for c in '\t\r\n')):
                encoded = quote(path + '.md', safe='/')
                link = f'[{disp}]({encoded})'
            else:
                link = f'[[{path}|{disp}]]'
            idx_lines.append(f'- {link} — `{tag_str}`')
        idx_lines.append('')

    idx_content = '\n'.join(idx_lines) + '\n'
    with open(OUT_INDEX, 'w', encoding='utf-8') as f:
        f.write(idx_content)
    print(f"[done] {OUT_INDEX} ({len(idx_content)} chars, {total} wikilinks)")

    return 0


if __name__ == '__main__':
    sys.exit(main())

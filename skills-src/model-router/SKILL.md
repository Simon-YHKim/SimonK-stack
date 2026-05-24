---
name: model-router
description: "Use when the user needs the best LLM model for a specific task type, or when simonk/multi-agent dispatch needs to assign models to parallel subtasks. Trigger phrases: '어떤 모델이 좋아', '모델 추천', '베스트 모델', 'which model is best', 'best model for', 'model router', 'task별 모델', '모델 자동 배치', '병렬로 모델 다르게'. Reads SimonKWiki wiki/concepts/ai-model-benchmarks.md as source of truth (latest May 2026 frontier matrix). Produces: (1) task type classification (CODE_NEW / CODE_FIX / CODE_REVIEW / RESEARCH / AGENTIC / COMPUTER_USE / DESIGN_UI / KOREAN_DOC / BULK_LIGHT / REASONING_ABSTRACT / VISION), (2) primary + secondary + cost-fallback model recommendation with API IDs, (3) rationale based on specific benchmark scores (SWE-bench / OSWorld / GPQA / Aider Polyglot / Arena Elo). Optionally outputs JSON config consumable by multi-terminal dispatch (sprint v23 Phase B)."
version: 0.1.0
---

# model-router — Task → Best LLM Selector

> [[wiki/concepts/ai-model-benchmarks]] (SimonKWiki PRIVATE) 의 매트릭스를 사용해 task type 별 best model 추천. simonk 의 Phase 3 위임 시 활용. Sprint v23 Phase B 의 multi-terminal dispatch 의 결정 layer.

## 0. 운영 컨텍스트

- **Source of truth**: `E:\Coding Infra\obsidian\SimonKWiki\wiki\concepts\ai-model-benchmarks.md`
- **갱신 cadence**: 주 1회 cron (`scripts/fetch-model-benchmarks.py`)
- **API key 가용**: Anthropic primary (Claude Opus 4.7 / Sonnet 4.6 / Haiku 4.5). 외부 (OpenAI / Google / xAI / DeepSeek / GLM) 는 사용자 key 확보 시 활성.

## 1. Task type 분류 (11 카테고리)

사용자 prompt 또는 sub-task description 을 다음 중 하나로 분류:

| Type | 키워드 / 패턴 | Best 1차 | Best 2차 | Cost-fallback |
|---|---|---|---|---|
| `CODE_NEW` | "구현해", "만들어", "scaffold", "implement", "build" | Claude Sonnet 4.6 | Claude Opus 4.7 | Claude Haiku 4.5 |
| `CODE_FIX` | "버그", "fix", "고쳐", "debug", "에러" | Claude Sonnet 4.6 | Claude Opus 4.7 | DeepSeek V3 |
| `CODE_REVIEW` | "review", "검토", "PR", "audit", "리뷰" | Claude Opus 4.7 | GPT-5.3 Codex | Claude Sonnet 4.6 |
| `RESEARCH` | "조사", "research", "분석", "compare", "papers" | Claude Opus 4.7 [1M] | Gemini 3.1 Pro | Claude Sonnet 4.6 |
| `AGENTIC` | "자동화", "agent", "multi-step", "execute", "워크플로" | Claude Opus 4.7 | GPT-5.4 | Claude Sonnet 4.6 |
| `COMPUTER_USE` | "브라우저", "screen", "click", "OS", "computer use" | GPT-5.4 | Claude Opus 4.7 | — |
| `DESIGN_UI` | "디자인", "UI", "landing", "랜딩", "Figma", "mockup" | Claude Opus 4.7 | GPT-5.4 | Claude Sonnet 4.6 |
| `KOREAN_DOC` | 한국어 prompt + 문서 작성 / 보고서 | Claude Sonnet 4.6 | GLM-5 | Claude Haiku 4.5 |
| `BULK_LIGHT` | "리스트", "대량", "bulk", "summarize many", "tag" | Gemini 3.5 Flash | Claude Haiku 4.5 | DeepSeek V3 |
| `REASONING_ABSTRACT` | "추상", "logic", "ARC", "math proof", "복잡 추론" | Gemini 3.1 Pro | Claude Opus 4.7 | Grok 4 |
| `VISION` | "이미지", "screenshot", "diagram", "vision", "OCR" | Gemini 3.1 Pro | Claude Sonnet 4.6 | GPT-5 |

분류 시 핵심 신호:
- 키워드 매칭 우선
- 한국어 prompt + 한국 도메인 → `KOREAN_DOC` 가산점
- 외부 도구 호출 동반 (Bash, Web, MCP) → `AGENTIC` 또는 `COMPUTER_USE`

## 2. 사용 흐름 (호출 패턴)

### 패턴 1: 단일 task 모델 추천

사용자: "이 버그 어떤 모델로 고쳐야 가장 정확할까?"
→ 분류: `CODE_FIX`
→ 출력:
```
Primary: Claude Sonnet 4.6 (claude-sonnet-4-6)
  - SWE-bench Verified: 79.6% (top tier)
  - 가격: $3/$15 per 1M tok
  - 권장 사유: 실 PR-grade fix 정확도 + 비용 균형
Secondary: Claude Opus 4.7 (claude-opus-4-7)
  - 더 복잡한 root cause 분석 필요시
  - 비용 5배 ($15/$75) — 해당 안 되면 Primary 가성비 ↑
Cost-fallback: DeepSeek V3 (deepseek-v3)
  - 가격 1/10, 정확도 65% 정도
```

### 패턴 2: simonk Phase 3 위임 시 자동 호출

simonk skill 의 Phase 2 (Sprint plan) 에서 task N 개 split → 각 task 마다 model-router 호출 → Phase 3 (Task tool delegation) 시 적절한 model 명시.

예: sprint = 3 tasks
- Task A (CODE_NEW) → Claude Sonnet 4.6 worktree 1
- Task B (RESEARCH) → Claude Opus 4.7 [1M] worktree 2
- Task C (BULK_LIGHT) → Gemini 3.5 Flash worktree 3

### 패턴 3: Multi-terminal dispatch (Sprint v23 Phase B)

`wiki/concepts/multi-agent-dispatch.md` 의 흐름과 통합. model-router 가 JSON config 출력:
```json
{
  "dispatch_id": "v23-multi-001",
  "tasks": [
    {"id": "t1", "type": "CODE_NEW", "model": "claude-sonnet-4-6", "terminal": "wt-tab-1"},
    {"id": "t2", "type": "RESEARCH", "model": "claude-opus-4-7", "terminal": "wt-tab-2"},
    {"id": "t3", "type": "BULK_LIGHT", "model": "gemini-3.5-flash", "terminal": "wt-tab-3"}
  ]
}
```

이 config 를 multi-terminal launcher (B2) 가 consume.

## 3. 가용 API key 확인 (fallback chain)

사용자 환경의 API key 확인 후 권장:
1. Primary 가용 → Primary 추천
2. Primary key 없음 → Secondary 추천 + "Primary key 박으면 정확도 +5~10% 가능" 안내
3. 모두 없음 → Cost-fallback (DeepSeek / open-weight)
4. fallback 도 없음 → Claude default (어차피 simonk 호출 = Claude Code 안)

key 확인: `~/.claude/.env` 또는 KeePassXC vault (`scripts/keepass-inject.ps1`).

## 4. 추천 출력 형식

기본 format (Markdown table):
```
| 순위 | 모델 | API ID | 사유 | 가격 |
|---|---|---|---|---|
| 1차 | Claude Sonnet 4.6 | claude-sonnet-4-6 | SWE-bench 79.6%, 한국어 OK | $3/$15 |
| 2차 | Claude Opus 4.7 | claude-opus-4-7 | flagship, agentic 강점 | $15/$75 |
| 비용 | Claude Haiku 4.5 | claude-haiku-4-5-20251001 | 1차의 1/3 비용, 70% 정확도 | $1/$5 |
```

JSON format (`--format json` 또는 simonk integration):
```json
{
  "task_type": "CODE_FIX",
  "primary": {"name": "Claude Sonnet 4.6", "id": "claude-sonnet-4-6", "price_in": 3, "price_out": 15},
  "secondary": {"name": "Claude Opus 4.7", "id": "claude-opus-4-7", "price_in": 15, "price_out": 75},
  "fallback": {"name": "DeepSeek V3", "id": "deepseek-v3", "price_in": 0.27, "price_out": 1.10},
  "rationale": "SWE-bench Verified 79.6% (Claude Sonnet 4.6 top tier). 한국어 prompt 호환."
}
```

## 5. 안전 가드

- **벤치마크 의존 위험**: 매트릭스가 outdated 면 잘못된 추천. wiki page `last-updated` 7일 초과 시 경고: *"벤치마크 갱신 X (last fetched: YYYY-MM-DD). `scripts/fetch-model-benchmarks.py` 실행 권장."*
- **모델명 환각 방지**: API ID 가 wiki § 1 Frontier 모델 table 에 없으면 추천 X (e.g. "Claude Sonnet 5" 같은 검증 안 된 vendor 마케팅 문구).
- **비용 폭증 방지**: simonk 통합 시 task 5+ 동시 + Claude Opus 4.7 → 사용자 명시 확인.

## 6. 갱신 cadence

- 매주 (cron): `fetch-model-benchmarks.py` 가 wiki 매트릭스 갱신 → 자동으로 이 skill 의 추천도 갱신
- 매 신규 frontier 모델 출시 (대형 event): manual 매트릭스 추가 (사용자 결정)
- 매 sprint v23 Phase B 진입 시: multi-terminal dispatch 통합 검증

## 7. 관련 자산

- **Wiki (SimonKWiki PRIVATE)**:
  - `[[ai-model-benchmarks]]` — source of truth 매트릭스
  - `[[multi-agent-dispatch]]` — 이 skill 의 사용 흐름 패턴
- **Script**: `scripts/fetch-model-benchmarks.py` — 주 1회 cron 갱신
- **External vendor**:
  - `external/oh-my-claudecode/` (OMC) — Team Mode 19 agents → model 배치 reference
  - `external/oh-my-openagent/` (OMO) — model-agnostic harness 6M lines reference
  - `external/OpenHarness/` — multi-agent infrastructure
- **Skills**:
  - `simonk` — Phase 3 위임 시 model-router 호출
  - (v23) `multi-terminal-dispatcher` — 이 skill 의 출력 consume

## 8. Roadmap

- v0.1 (현재): task type 분류 + 추천 매트릭스 + Markdown/JSON output
- v0.2 (Phase B): simonk Phase 3 자동 호출 hook + multi-terminal config 출력
- v0.3: 사용자 API key 자동 detect (KeePassXC 읽기)
- v0.4: 작업 history 기반 학습 (어떤 task 에서 어떤 모델이 실제 잘 했는지 누적)
- v1.0: 벤치마크 → 매핑 자동 재계산 (수동 매트릭스 → 가중치 기반 알고리즘)

---
name: simon-research
description: Research-first principle — mandatory external-source investigation (official docs, competitive products, recent engineering blogs) BEFORE any major planning or architecture decision. Use this skill whenever the user says things like "리서치 해줘", "조사 해줘", "기술 비교", "레퍼런스 수집", "Supabase vs Firebase", "research this stack", "competitive analysis", "find examples of X"—or before running /plan-ceo-review, /ultraplan, app-dev-orchestrator, dev-orchestrator, or security-orchestrator. Produces a dated research doc (docs/research/<date>-<topic>.md) with citations, competitive comparison table (3+ products), and recommendations. Rejects unsourced claims, stale blogs (>1 year), and AI-summary articles as primary sources.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon
---

# Simon Research

ECC `research-first` 스킬의 핵심 추출. 플래닝 전에 외부 리서치를 선행 수행하여 출처 있는 결정을 만든다.

## When to use

- `app-dev-orchestrator` 단계 2 (`/office-hours` 이후, `/plan-ceo-review` 이전)
- 새 기술 스택·라이브러리 선택
- 경쟁 제품 벤치마킹
- 사용자가 "리서치 해줘", "조사", "기술 비교", "레퍼런스" 요청
- `/plan-ceo-review` 진입 전에 근거 수집

## Workflow

### 1. 주제 3줄 요약

사용자 요청을 3줄로 압축:
- **What**: 리서치 대상
- **Why**: 왜 필요한가 (의사결정 맥락)
- **Success**: 어떤 결과물이 나와야 충분한가

### 2. 검색 키워드 5-10개 추출

- 공식 문서 키워드
- 경쟁 제품 이름
- 최근 6개월 블로그/컨퍼런스
- 실패 사례·안티패턴 키워드
- 한국어 + 영어 병기

### 3. 1차 자료 수집 (병렬 WebFetch)

우선순위:
1. **공식 문서** (anthropic.com, stripe.com, supabase.com 등)
2. **공식 GitHub 레포** README·examples
3. **RFC·명세서** (OpenAPI, JWT, OAuth)
4. 최근 6개월 **엔지니어링 블로그**

금기:
- ❌ 1년 이상 된 블로그 단일 출처
- ❌ 출처 불명의 요약 글
- ❌ AI 요약 기사 (2차 가공 자료)

### 4. 경쟁 제품 3개 이상 비교표

| 항목 | Product A | Product B | Product C | 비고 |
|---|---|---|---|---|
| 가격 | ... | ... | ... | |
| 핵심 기능 | ... | ... | ... | |
| 제약 | ... | ... | ... | |
| 통합 용이성 | ... | ... | ... | |
| 커뮤니티 | ... | ... | ... | |

### 5. Context7 MCP 활용 (설치돼 있을 때)

라이브러리 최신 문서는 Context7 MCP (`query-docs`) 로 확인:
- React, Next.js, Prisma, Supabase, Stripe 등
- 공식 문서가 training cutoff 이후 업데이트됐을 수 있음

**현재 환경**: MCP 서버 연결 상태 변동 가능. 실행 전 `claude mcp list` 로 확인.

### 6. 결과 저장

`docs/research/<YYYY-MM-DD>-<topic>.md` 형식:

```md
# Research: <topic>

**Date**: YYYY-MM-DD
**Author**: Claude (on behalf of <user>)
**Context**: <왜 필요한가>
**Decision deadline**: <언제까지 결정 필요>

## Summary (3 lines)
...

## Sources
1. Title — URL — YYYY-MM-DD — 공식/블로그 — 1차/2차
2. Title2 — URL — ...

## Competitive landscape
<비교표>

## Findings
- Finding 1 (source: [1])
- Finding 2 (source: [2])

## Recommendations
1. ...
2. Title2 — URL — ...

## Open questions
- ...
```

**필수 메타데이터**:
- URL, 발행일, 저자/기관
- 1차 (공식) / 2차 (해설) 구분
- 한국 특이사항 섹션 (현지 API·가격·언어 대응)

### 7. 플래닝에 투입

산출물을 다음 스킬에 입력으로 전달:
- `/office-hours` — YC forcing question 근거
- `/plan-ceo-review` — 10-star 스코프 입력
- `/plan-eng-review` — 기술 선택 근거
- `/ultraplan` (code.claude.com) — 대형 플래닝 컨텍스트

### 8. Wiki에 file back (영속 누적)

`llm-wiki-builder` 가 설치돼 있으면 리서치 결과를 wiki에 자동 누적:

```bash
# 리서치 docs/research/<date>-<topic>.md 가 ingest 대상
bash skills-src/llm-wiki-builder/scripts/wiki-init.sh   # 첫 사용 시
# LLM 이 ingest 워크플로 실행:
#   - raw/articles/ 에 research doc 복사
#   - wiki/sources/<date>-<topic>.md 요약 페이지
#   - 관련 entity/concept 갱신 (예: 경쟁 제품 비교 → entities/<product>.md)
#   - log.md append
bash skills-src/llm-wiki-builder/scripts/log-append.sh ingest "<topic> research"
```

**왜?** 리서치가 한 프로젝트에서 끝나지 않고 영속 자산으로 누적됨. 다음 프로젝트에서
"이 기술 비교 전에 했던 거 같은데" 가 grep 한 번이면 끝남 (`grep "ingest" log.md`).

Karpathy llm-wiki 패턴: research 결과는 chat history에 사라지지 않고 wiki 페이지로 살아남음.

## Checklist

- [ ] 주제 3줄 요약 작성
- [ ] 검색 키워드 5개 이상
- [ ] 공식 문서 최소 1개 소스
- [ ] 경쟁 제품 3개 이상 비교
- [ ] 출처마다 URL·발행일·저자 기록
- [ ] 1차/2차 구분
- [ ] `docs/research/<date>-<topic>.md` 저장
- [ ] 한국 특이사항 섹션 포함 (해당 시)
- [ ] 플래닝 스킬로 전달됨
- [ ] (선택) `llm-wiki-builder` 로 wiki 에 ingest — 영속 누적

## Anti-patterns

- ❌ 출처 없는 주장 ("X가 Y보다 빠르다고 함")
- ❌ 1년 이상 된 블로그 단일 출처
- ❌ 공식 문서 확인 skip, 블로그만 의존
- ❌ 리서치 결과 저장 안 함 — 휘발성 지식
- ❌ 경쟁 제품 1개만 조사 — 비교 가치 없음
- ❌ AI 요약 기사 (2차 가공) 를 1차 자료로 취급
- ❌ 한국 서비스인데 해외 비교만, 국내 경쟁 조사 누락

## Related skills

- `/office-hours` — 리서치 결과를 forcing question 에 투입
- `/plan-ceo-review` — CEO 리뷰 근거
- `/plan-eng-review` — 엔지니어링 선택 근거
- `/learn` — Gstack 프로젝트 학습 저장 (상호보완)
- `app-dev-orchestrator` — 단계 2
- `llm-wiki-builder` — research 결과를 영속 wiki 에 file back (Karpathy llm-wiki 패턴)
- `karpathy-guidelines` — 원칙 1 (Think Before Coding) 의 research 단계 적용
- `domain-glossary` — 리서치에서 발견한 산업 표준 용어 (예: Stripe "idempotency key", DDD "bounded context") 를 프로젝트 `CONTEXT.md` 로 promote. Research → glossary 흐름은 동일 세션에서 inline 진행 권장.

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.

---
name: simon-research
description: Research-first principle — mandatory external-source investigation (official docs, competitive products, recent engineering blogs) BEFORE any major planning or architecture decision. Use this skill whenever the user says things like "리서치 해줘", "조사 해줘", "기술 비교", "레퍼런스 수집", "Supabase vs Firebase", "research this stack", "competitive analysis", "find examples of X"—or before running /plan-ceo-review, /ultraplan, or app-dev-orchestrator. Produces a dated research doc (docs/research/<date>-<topic>.md) with citations, competitive comparison table (3+ products), and recommendations. Rejects unsourced claims, stale blogs (>1 year), and AI-summary articles as primary sources.
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

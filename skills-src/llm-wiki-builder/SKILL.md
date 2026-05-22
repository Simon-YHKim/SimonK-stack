---
name: llm-wiki-builder
description: "Use when the user asks to build, ingest into, query, or maintain a personal LLM-maintained knowledge wiki—triggers \"wiki에 추가해줘\", \"리서치 누적\", \"지식베이스 만들어줘\", \"이 자료 정리해서 wiki에\", \"ingest this\", \"build a knowledge base\", \"add to wiki\". Produces a 3-layer Karpathy llm-wiki pattern: raw sources (immutable) + LLM-owned markdown wiki + schema file. Implements Ingest/Query/Lint operations with index.md catalog and log.md chronological journal. Default wiki repo: Simon-YHKim/Simon-LLM-Wiki (override via SIMON_WIKI_REPO env). Persistent knowledge that compounds across sessions—anti-RAG. DEPRECATED 2026-05-23: superseded by wiki-ingest/wiki-query/wiki-lint for SimonKWiki v2."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# llm-wiki-builder

Andrej Karpathy의 [llm-wiki 패턴](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 구현.

> "The wiki is a persistent, compounding artifact. Obsidian = IDE, LLM = programmer, wiki = codebase." — Karpathy

## RAG vs Wiki

| | RAG (기존) | LLM Wiki (이 skill) |
|---|---|---|
| 매 질문 | raw에서 새로 합성 | wiki에서 검색 |
| 누적 | 없음 | **있음** (영속 자산) |
| 교차참조 | 매번 재발견 | **이미 존재** |
| 모순 발견 | 안 됨 | **flag됨** |
| 비용 | 매 질문 LLM 호출 | 한 번 컴파일, 검색만 |

## Wiki 레포

**기본**: `https://github.com/Simon-YHKim/Simon-LLM-Wiki.git` (사용자 본인 레포, 빈 상태)

**환경변수 override**:
```bash
export SIMON_WIKI_REPO=https://github.com/your/wiki.git
```

**Local clone 위치**: `~/.claude/wiki/<repo-name>/`

스크립트가 자동으로 clone (없으면) 또는 pull (있으면).

## 3계층 아키텍처

```
~/.claude/wiki/Simon-LLM-Wiki/
├── raw/                    ← 1. Raw sources (불변, 사람이 큐레이션)
│   ├── articles/
│   ├── papers/
│   └── assets/             ← 이미지 (Obsidian 호환)
├── wiki/                   ← 2. LLM 소유 markdown
│   ├── entities/           ← 사람·조직·제품 페이지
│   ├── concepts/           ← 추상 개념·기법
│   ├── sources/            ← 소스별 요약
│   ├── index.md            ← 카탈로그 (content-oriented)
│   └── log.md              ← 시간순 (append-only)
└── CLAUDE.md               ← 3. Schema (이 wiki의 규약)
```

## 3개 연산

### Ingest

새 소스 추가 → wiki 갱신.

```bash
bash skills-src/llm-wiki-builder/scripts/ingest.sh <source-path-or-url> [--topic "토픽명"]
```

워크플로:
1. Source를 `raw/`에 복사 (URL이면 다운로드)
2. LLM이 source 읽고 사용자와 핵심 포인트 논의
3. `wiki/sources/<slug>.md` 요약 페이지 작성
4. 관련 entity/concept 페이지 갱신 (10-15개 페이지 영향 가능)
5. `wiki/index.md` 갱신
6. `wiki/log.md` 에 entry append:
   ```
   ## [YYYY-MM-DD] ingest | <Source Title>
   - Updated: entities/X.md, concepts/Y.md
   - New: sources/Z.md
   - Tokens: ~N
   ```

### Query

Wiki에 질문 → 답변 + **답변도 wiki에 file back**.

```bash
bash skills-src/llm-wiki-builder/scripts/query.sh "질문 텍스트"
```

워크플로:
1. `wiki/index.md` 읽기 (관련 페이지 후보)
2. 후보 페이지 read
3. 합성 답변 작성 (citation 필수)
4. **답변이 가치 있으면** `wiki/queries/<slug>.md` 로 file back
5. log.md entry:
   ```
   ## [YYYY-MM-DD] query | "질문 요약"
   - Cited: [page1, page2, ...]
   - Filed back: queries/Z.md (yes/no)
   ```

핵심: 탐험이 chat history로 사라지지 않고 **누적**됨.

### Lint

Wiki health check.

```bash
bash skills-src/llm-wiki-builder/scripts/lint.sh
```

체크 항목:
- **Contradictions**: 같은 entity의 다른 페이지에서 모순 주장
- **Stale claims**: 새 source가 superseded한 오래된 주장
- **Orphan pages**: 어디서도 link 되지 않은 페이지
- **Missing pages**: 자주 언급되는데 자기 페이지 없는 entity/concept
- **Broken cross-refs**: 깨진 wiki link
- **Data gaps**: 보강하면 좋을 외부 search 후보

산출: `wiki/lint-report-<date>.md` + 사용자 confirm 후 자동 수정 PR.

## Index + Log 컨벤션

### `wiki/index.md`
```markdown
# Wiki Index

## Entities
- [[John Doe]] — CEO of X (5 sources)
- [[OpenAI]] — AI company (12 sources)

## Concepts
- [[RAG]] — retrieval-augmented generation (8 sources)
- [[LLM Wiki Pattern]] — anti-RAG persistent wiki (3 sources)

## Sources
- [[2026-04-04 Karpathy llm-wiki gist]]
- [[2026-01-27 Karpathy LLM coding mistakes tweet]]
```

### `wiki/log.md` (append-only, parseable)
```markdown
## [2026-05-04] ingest | Karpathy llm-wiki gist
- Updated: concepts/RAG.md, concepts/Memex.md
- New: sources/2026-04-04-karpathy-llm-wiki.md, concepts/llm-wiki-pattern.md

## [2026-05-04] query | "RAG vs llm-wiki 차이"
- Cited: concepts/RAG.md, concepts/llm-wiki-pattern.md
- Filed back: queries/rag-vs-llm-wiki.md
```

Unix-friendly:
```bash
grep "^## \[" log.md | tail -10   # 최근 10개 활동
grep "ingest" log.md              # 모든 ingest 이력
```

## Schema 파일 (`CLAUDE.md`)

Wiki 레포 루트에 자동 생성. LLM이 wiki를 어떻게 다룰지 명시.

핵심 섹션:
1. Wiki 디렉토리 구조 설명
2. 페이지 명명 규약 (kebab-case, entity = PascalCase 등)
3. Frontmatter 표준 (tags, sources, last_updated)
4. Cross-link 형식 (`[[wiki-link]]` Obsidian 스타일)
5. Ingest 워크플로 단계
6. Lint 기준
7. 금기 사항 (raw/ 수정 금지 등)

## 인간 vs LLM 역할

| 인간 | LLM |
|---|---|
| 소스 큐레이션 | 요약 |
| 좋은 질문 | 교차참조 |
| 탐험 방향 | 파일링 |
| 판단·통찰 | bookkeeping |
| Wiki 큰 그림 | 일관성 유지 |

Karpathy 명언:
> "The tedious part of maintaining a knowledge base is not the reading or the thinking — it's the bookkeeping. LLMs don't get bored."

## 도구 통합 (선택)

| 도구 | 용도 |
|---|---|
| **Obsidian** | wiki/ 폴더 열기 — graph view, link, search |
| **Obsidian Web Clipper** | 웹 → markdown으로 raw/ 에 빠르게 |
| **qmd** | wiki 전용 BM25+vector 검색 (CLI + MCP) |
| **Marp** | wiki 페이지 → 슬라이드 |
| **git** | wiki 자체가 git repo — 버전 관리 무료 |

## 다른 skill과의 통합

| Skill | 통합 |
|---|---|
| `simon-research` | research 결과를 자동 ingest (파일로 끝나지 않고 wiki에 누적) |
| `simon-instincts` | instincts도 영속 누적 — 사상 동일, 도메인만 다름 (코딩 vs 일반 지식) |
| `app-dev-orchestrator` | 단계 2 (research) 결과가 wiki에 자동 누적 |
| `karpathy-guidelines` | wiki 자체가 원칙 4 (Goal-Driven)의 구현 — 매 작업이 검증 가능한 산출물 |

## 적용 시나리오

- **개인**: 목표·건강·심리·자기계발 — journal/article/podcast 누적
- **리서치**: 논문·기사·리포트 → 시간 지나며 종합 thesis 형성
- **책 읽기**: chapter별 ingest → 인물/테마/플롯 wiki (Tolkien Gateway 스타일)
- **비즈니스**: Slack/회의록/고객 콜 → 팀 wiki (사람이 review)
- **경쟁 분석, due diligence, 여행 계획, 강의 노트, 취미** — 모든 누적 지식 작업

## 출처

- [Karpathy llm-wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — 원본 디자인 패턴
- Vannevar Bush (1945) — Memex 개념의 LLM 시대 구현

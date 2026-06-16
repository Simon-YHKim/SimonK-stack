---
name: tech-preference-tracker
description: "Use when the user is choosing a programming language, framework, or platform AND wants the decision to be consistent with prior projects—triggers \"이 프로젝트 뭐로 할까\", \"언어 뭐 쓰지\", \"플랫폼 정해줘\", \"이전 프로젝트랑 일관성 있게\", \"성능 좋고 업데이트 쉬운\", \"choose stack\", \"consistent tech stack\", \"language for performance and updates\", \"what should I use\". Different from app-platform-selector (hybrid vs native) and db-selector (which DB): this tracks the USER'S CUMULATIVE PREFERENCES across all their projects (lang/runtime/framework/deploy target/state lib/test lib/lint) and recommends choices that maximize update-ease and cross-project transfer. Reads E:/Coding Infra/obsidian/SimonKWiki/wiki/protocols/llm-wiki/entities/simon-yhkim.md tech matrix, lints new project for drift, and updates the matrix when the user deliberately changes preference."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# tech-preference-tracker

새 프로젝트의 언어/플랫폼을 고를 때, 사용자의 **누적 선호도**를 참고하여
**일관된** 선택을 권고합니다. 성능 + 업데이트 용이성 + 학습 비용 회수가 기준.

## 발동 조건

- "이번 프로젝트 뭐로 만들지?"
- "Next.js 로 갈까 Remix 로 갈까?"
- "FastAPI vs Express"
- "Supabase 또 쓸까?"
- 새 레포 스캐폴딩 시 자동 발동 후보

## 사용자가 명시한 기준

> "어떤 프로그래밍 언어로 하면, 어떤 플랫폼을 사용하면, 성능이 우수한지? 업데이트가 용이한지? 에 대한 고민. 일관성 있게."

핵심: **일관성** — 매번 새 스택을 시도하면 누적되는 자산이 0.

## 다른 스킬과의 차이

| 스킬 | 관점 |
|---|---|
| `app-platform-selector` | Hybrid vs PWA vs Native — 1회 결정 |
| `db-selector` | DB 카탈로그 매칭 — 1회 결정 |
| `stack-architect` | 새 스택 _설계_ — 큰 그림 |
| **`tech-preference-tracker`** | **누적 선호도 기반 _일관성_ 권고 — 매 프로젝트** |

## Preference Matrix

`E:/Coding Infra/obsidian/SimonKWiki/wiki/protocols/llm-wiki/entities/simon-yhkim.md` 의 `## Tech Preferences` 섹션에서 읽어오기.
없으면 빈 매트릭스로 시작.

```yaml
# 예시 (실제는 wiki 에서 읽음)
languages:
  default: typescript
  for_scripts: python
  for_perf_critical: rust  # tentative
runtime:
  web: bun  # 또는 node
  scripts: python3
frameworks:
  web_frontend: nextjs
  web_backend: hono | fastapi
  mobile: expo-rn  # 또는 capacitor
deploy:
  static: vercel
  server: fly.io | cloudflare
  mobile: expo-eas
db:
  default: supabase  # postgres + auth + RLS
  cache: upstash-redis
state_mgmt: zustand
testing: vitest | playwright
lint: biome | ruff
ci: github-actions
```

## 워크플로

### 1. Audit 모드 (새 프로젝트 시작 전)
```bash
# 이 skill 이 자동 수행
- Read wiki/protocols/llm-wiki/entities/simon-yhkim.md § Tech Preferences
- 새 프로젝트 요구사항 vs 매트릭스 매칭
- 권고 + 차이점 explain
```

### 2. Drift 감지 (기존 프로젝트 검사)
- 사용자가 25+ 레포 보유 — 어느 레포가 매트릭스에서 _drift_ 했는지 스캔
- `package.json`, `requirements.txt`, `pyproject.toml` 읽기
- 드리프트 리포트:
  ```
  drift report:
  - Career-manager: state_mgmt=jotai (matrix=zustand)
  - LGIT-MPAP: runtime=node (matrix=bun)
  ```
- 사용자 결정: 드리프트 fix vs 매트릭스 update

### 3. Matrix 갱신
사용자가 _의도적으로_ 새 기술 채택 시:
- wiki 의 entities/simon-yhkim.md § Tech Preferences 갱신
- log.md 에 entry append (`refactor` action)
- 변경 이유 한 줄 기록

### 4. 성능 vs 업데이트 용이성 평가

새 후보 평가 시 다음 5축으로 점수 (1-5):

| 축 | 의미 |
|---|---|
| 성능 | benchmark 기반, 사용자 케이스 적합 |
| 업데이트 용이성 | 한 명이 1주일에 1회 배포 가능한가 |
| 학습 비용 회수 | 이미 알고 있는가, 또는 한 번 배우면 N개 프로젝트에 쓸 수 있는가 |
| 생태계 안정성 | 1년 후에도 살아있을 가능성 |
| 한국 시장 적합 | 한국 결제·인증·OS 호환성 |

기존 매트릭스 옵션이 동점 이상이면 _기존 유지_ 권고.

## 산출

| 모드 | 산출 |
|---|---|
| audit-new | 권고 스택 + 매트릭스 정합성 리포트 |
| audit-existing | 25+ 레포 드리프트 리포트 |
| update-matrix | wiki 갱신 PR draft |

## 안티패턴

- ❌ "최신이니까 이걸로" — 매번 새 스택 시도 → 0 누적
- ❌ 매트릭스 없이 매번 직관적 추천 → 불일관
- ❌ 매트릭스에 잠금 → 새 기술 도입 영원히 차단 (출구 통로 = update-matrix 모드)
- ❌ 한국 시장 무시한 글로벌 추천 (Stripe vs 토스/카카오페이)

## 사용자 강조 원칙

> "일관성 있게."

매 프로젝트마다 _이전과 같은_ 도구를 쓰는 것이 가장 큰 누적 자산.
이 skill 은 그 일관성을 _측정 가능_ 하게 만든다.

## Wiki 연동

- 읽기: `wiki/protocols/llm-wiki/entities/simon-yhkim.md § Tech Preferences`
- 쓰기: 사용자 승인 후 같은 섹션 update + `wiki/log.md` entry
- 새 mistake (예: "또 새 framework 시도해서 시간 낭비") → `wiki/concepts/recurring-mistakes.md` 새 mistake 항목

## Related Skills

- `app-platform-selector` — Hybrid/PWA/Native 결정 (이 skill 이전 단계)
- `db-selector` — DB 결정 (이 skill 의 한 행)
- `stack-architect` — 새 스택 설계 (이 skill 후속)
- `llm-wiki-builder` — preference 누적 저장소

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.

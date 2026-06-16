---
name: simon-ohmo
description: "Use when the user invokes \"simon-ohmo\", \"/simon-ohmo\", \"personal agent\", \"self.md agent\", \"closed-network agent\", \"폐쇄망 운영\", or \"시그니처 작품 활성\". Phase 6 (27Y Q1+) placeholder. Produces (1) status check (5 entry conditions: OpenHarness ✓ / Ollama model / self.md / v0 prototype / on-prem GPU), (2) prerequisite verification, (3) deferral notice with checklist. Do NOT use as production agent yet — use simonK for current autonomous work."
allowed-tools: Read, Bash
version: 0.1.1
author: simon-stack
---

# simon-ohmo (Phase 6 placeholder)

> **상태**: ⏳ Phase 6 (27Y Q1+) 진입 시 본격 작성. *현재 placeholder*.

## 발동 조건

다음 트리거 중 하나로 호출됨:
- `simon-ohmo`, `/simon-ohmo`
- "personal agent", "self.md agent", "closed-network agent"
- "폐쇄망 운영", "시그니처 작품 활성"

## Phase 6 진입 전제 조건

본 skill은 아래 5개 조건이 *모두 충족*되어야 본격 활성:

| # | 조건 | 현재 상태 (2026-05-25) |
|---|---|---|
| **1** | OpenHarness v0.1.9+ 설치 | ✅ (Phase 3 사전 진입) |
| **2** | 로컬 LLM (qwen2.5-coder 또는 glm-4) | ⏳ Ollama install ✓ / 모델 ❌ |
| **3** | self.md schema (사용자 본인 agent CLAUDE.md) | ⏳ wiki/CLAUDE.md 있지만 *agent self.md* 별도 작성 필요 |
| **4** | v0 클라우드 프로토타입 | ❌ Phase 5 (Q4) 완성 예정 |
| **5** | on-prem GPU 서버 폐쇄망 | ❌ 27Y Q1 인프라 협상 후 |

→ 5/5 충족 시 v1.0 정식 작성. 그 전에 호출되면 *deferral notice* 출력.

## 현재 호출 시 동작 (placeholder)

```
사용자: /simon-ohmo
→ 본 skill 응답:

  ## Phase 6 진입 전 상태 점검

  - [✅] OpenHarness v0.1.9 (Phase 3 사전)
  - [⏳] 로컬 LLM 모델 (디스크 결정 대기)
  - [⏳] self.md schema (Phase 5 Q4 작성 예정)
  - [❌] v0 클라우드 프로토타입 (Phase 5 Q4 완성 예정)
  - [❌] on-prem GPU 서버 폐쇄망 (27Y Q1 인프라 협상)

  현재 자율 작업은 simonK 사용 권장:
  → simonK <task>
```

## Phase 6 도래 시 SKILL.md 본격 내용 (예정)

다음 섹션들이 Phase 6 진입 시 작성:

### 1. self.md schema (personal agent OS — example 구조)

```
- WHO: <사용자 identity>
- WHY: <Polaris — 사용자 결정>
- VALUES: <Brain Trinity 5 가치>
- CIRCUITS: <9 회로 활성·억제 상태>
- ROLES: <7 모자 비중>
- BOUNDARY: <외부 leak 차단 + 시간 boundary>
- VOICE: <응답 규칙>
- REFLEXES: <자동 반응 패턴>
```

→ 실제 본인 self.md는 *Phase 6 진입 시* SimonKWiki 누적 자료에서 자동 추출 (script 작성 예정).

### 2. OpenHarness + 로컬 LLM + ohmo 통합 흐름

```
사용자: simon-ohmo "<task>"
  ↓ OpenHarness multi-agent
  ├─ 도메인 데이터 (on-prem) ← analytics 환경
  ├─ 로컬 LLM (외부 API 호출 0)
  ├─ self.md schema 자동 inject
  └─ MCP: on-prem 동등 도구 (외부 → on-prem 대체)
  ↓
self.md 기반 응답 (사용자 본인 톤 + 진단 감안)
```

### 3. 통합 자산 (Phase 6 시점)

- A01~A14 (Wiki + MCP 외부)
- C01~C03 (kepano + OpenHarness + ohmo)
- SimonK-stack v3 (Stage 3 글로벌 노출 후 큐레이션)
- self.md schema (본 skill 본문에 박힘)
- v1.0 agent (on-prem GPU 호스트)

### 4. Closed network 운영 가드

- 외부 API 호출 0 (모든 LLM = 로컬)
- 도메인 데이터 외부 leak 0 (CSO audit pass)
- self.md 갱신은 *사용자 본인만* (LLM 자동 갱신 X)

## 현재 사용자에게 권장

Phase 6는 27Y Q1 도래. 그 전 (2026-2027 Q4) 까지는:

1. **Phase 1-3** (5/22~6/30) — simonK 통합 자율 하네스
2. **Phase 4** (7월~9월) — 로컬 LLM 모델 다운 + R&D 클라우드 단계
3. **Phase 5** (10월~12월) — v0 클라우드 프로토타입 + self.md draft
4. **Phase 6** (27Y Q1) — 본 skill 정식 활성

## 교차참조

- `wiki/protocols/system-blueprint` § Phase 6 — 마스터 청사진
- `wiki/protocols/simon-ohmo-architecture` — 본 skill의 architecture (별도 wiki)
- `wiki/entities/tools/openharness` — C02 install 완료
- `simon-instincts` skill — self.md schema 사전 데이터 누적

---

*v0.1.1 placeholder 2026-05-25 (사내 식별 reference 마스킹 처리). v1.0 정식 활성: Phase 6 진입 (27Y Q1) 시.*

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.

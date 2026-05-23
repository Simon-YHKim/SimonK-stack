---
name: simon-ohmo
description: "Use when the user invokes Simon-ohmo personal agent (Phase 6, 27Y Q1+). Triggers 'simon-ohmo', '/ohmo', 'personal agent', 'self.md agent', 'Max Capa Agent v1.0', '폐쇄망 운영', '시그니처 작품 활성'. Routes to OpenHarness + Ollama + self.md schema for closed-network multi-agent operation. Placeholder skill — full activation reserved for Phase 6 (Simon-ohmo signature, 27Y Q1). Currently produces: (1) status check (Phase 6 entry conditions), (2) prerequisite verification (OpenHarness v0.1.9 ✓ / Ollama install ✓ / self.md draft / Max Capa Agent v0 prototype), (3) explicit deferral notice with Phase 6 entry checklist. Do NOT use as production agent yet — use simonK for current autonomous work."
allowed-tools: Read, Bash
version: 0.1.0
author: simon-stack
---

# simon-ohmo (Phase 6 placeholder)

> **상태**: ⏳ Phase 6 (27Y Q1+) 진입 시 본격 작성. *현재 placeholder*.

## 발동 조건

다음 트리거 중 하나로 호출됨:
- `simon-ohmo`, `/ohmo`
- "personal agent", "self.md agent"
- "Max Capa Agent v1.0", "폐쇄망 운영"
- "시그니처 작품 활성"

## Phase 6 진입 전제 조건

본 skill은 아래 5개 조건이 *모두 충족*되어야 본격 활성:

| # | 조건 | 현재 상태 (2026-05-25) |
|---|---|---|
| **1** | OpenHarness v0.1.9+ 설치 | ✅ (Phase 3 사전 진입) |
| **2** | Ollama 로컬 LLM (qwen2.5-coder 또는 glm-4) | ⏳ install ✓ / 모델 ❌ |
| **3** | self.md schema (Simon 본인 CLAUDE.md) | ⏳ wiki/CLAUDE.md 있지만 *agent self.md* 별도 작성 필요 |
| **4** | Max Capa Agent v0 클라우드 프로토타입 | ❌ Phase 5 (Q4) 완성 예정 |
| **5** | 사내 GPU 서버 폐쇄망 (LG이노텍) | ❌ 27Y Q1 인프라 협상 후 |

→ 5/5 충족 시 v1.0 정식 작성. 그 전에 호출되면 *deferral notice* 출력.

## 현재 호출 시 동작 (placeholder)

```
사용자: /simon-ohmo
→ 본 skill 응답:

  ## Phase 6 진입 전 상태 점검

  - [✅] OpenHarness v0.1.9 (Phase 3 사전)
  - [⏳] Ollama 모델 (사용자 디스크 결정 대기)
  - [⏳] self.md schema (Phase 5 Q4 작성 예정)
  - [❌] Max Capa Agent v0 (Phase 5 Q4 완성 예정)
  - [❌] LG 사내 GPU 서버 폐쇄망 (27Y Q1 인프라 협상)

  현재 자율 작업은 simonK 사용 권장:
  → simonK <task>
```

## Phase 6 도래 시 SKILL.md 본격 내용 (예정)

다음 섹션들이 Phase 6 진입 시 작성:

### 1. self.md schema (Simon personal agent OS)

```
- WHO: 김양환 / Simon Kim
- WHY: AI 도메인 전문가 + Max Capa Agent 시그니처
- VALUES: 노력화폐·진정성·장인정신·솔직함·카르마
- CIRCUITS: 1~9 (활성·억제 상태 추적)
- ROLES: 7 모자 (현재 비중)
- BOUNDARY: LG 사내 정보 보안 + 와이프 시간
- VOICE: 직설·관찰형 · italic 강조 · 옵션 나열 금지
```

### 2. OpenHarness + Ollama + ohmo 통합 흐름

```
사용자: simon-ohmo "사내 라인 X MTBF 패턴 분석"
  ↓ OpenHarness multi-agent
  ├─ 사내 데이터 (LG 폐쇄망) ← BigQuery on-prem
  ├─ Ollama 로컬 LLM (외부 API 호출 0)
  ├─ self.md schema 자동 inject
  └─ MCP: 사내 Zotero / NotebookLM 동등 도구
  ↓
self.md 기반 응답 (사용자 본인 톤 + 회로 감안)
```

### 3. 통합 자산 (Phase 6 시점)

- A01~A14 (Wiki + MCP 외부)
- C01~C03 (kepano + OpenHarness + ohmo)
- SimonK-stack v3 (Stage 3 글로벌 노출 후 큐레이션)
- self.md schema (본 skill 본문에 박힘)
- Max Capa Agent v1.0 (사내 GPU 호스트)

### 4. Closed network 운영 가드

- 외부 API 호출 0 (모든 LLM = 로컬)
- 사내 데이터 외부 leak 0 (CSO audit pass)
- self.md 갱신은 *사용자 본인만* (LLM 자동 갱신 X)

## 현재 사용자에게 권장

Phase 6는 27Y Q1 도래. 그 전 (2026-2027 Q4) 까지는:

1. **Phase 1-3** (5/22~6/30) — simonK 통합 자율 하네스
2. **Phase 4** (7월~9월) — Ollama 모델 다운 + Max Capa R&D 클라우드
3. **Phase 5** (10월~12월) — Max Capa Agent v0 프로토타입 + self.md draft
4. **Phase 6** (27Y Q1) — 본 skill 정식 활성 + Simon-ohmo 베타 발표

## 교차참조

- `[[SimonKWiki/wiki/protocols/system-blueprint]] § Phase 6` — 마스터 청사진
- `[[SimonKWiki/wiki/entities/tools/openharness]]` — C02 install 완료
- `simon-instincts` skill — self.md schema 사전 데이터 누적

---

*v0.1.0 placeholder 2026-05-25. v1.0 정식 활성: Phase 6 진입 (27Y Q1) 시.*

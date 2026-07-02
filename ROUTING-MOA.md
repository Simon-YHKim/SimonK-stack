# ROUTING-MOA.md — Mixture-of-Agents 교차검증 레인 (SPEC-1 구현)

> **상태**: 구현 문서 — `ROUTING.md §1.6`이 흡수·참조 **완료**(2026-07-02), hub-daemon 프롬프트에 verify-request 훅 **배선 완료**(2026-07-03). Claude(라우팅 single-writer) 작성.
> **출처**: Sakana **Fugu**(MoA, 2026-06-22 정식 릴리즈) 통찰 + 우리 `ai-debate`가 이미 MoA라는 인식. 상세 배경 `C:\Coding Infra\reports\external-knowledge-integration-spec-20260702.md` SPEC-1.
> **핵심 원칙**: Fugu의 *메커니즘*(decompose→delegate→verify→synthesize)은 채택, *불투명성*(단일 엔드포인트 은닉)은 거부 — 우리는 BOARD/DECISIONS로 투명 유지.

---

## 1. 고정 능력레인 + 동적 태스크라우팅

Fugu는 stateless API 모델 풀을 자유조합하지만 **우리 seat는 하드웨어·쿼터·계정에 묶여 있다**. 따라서 **능력레인은 고정, 과제 배정만 동적**.

| Seat | 고정 능력레인 (불변) | 동적 확장 (Fugu 반영) |
|---|---|---|
| **Claude** | 오케스트레이션 · 코딩 · 머지/BOARD single-writer | decompose→fan-out 주체(§27.10 병렬 기본) |
| **Codex (GPT)** | UI/UX · 이미지 · 테스트 작성 | Thinker(초기 계획)·요약 보조 |
| **Antigravity (Gemini)** | Android 네이티브 에뮬 QA (**하드웨어 바운드=대체불가**) | + research/vision/long-context (강점 재배치, 병행) |
| **Grok** | X/소셜 live 리서치 (**live 데이터=moat**) | + 실시간 외부사실 Verifier |

> Fugu가 제시한 모델별 역할 고정분담(Claude=Worker/Grok=Verifier 등)은 **Sakana 비공식(추론)** — 그대로 이식하지 않고 위 우리 실제 제약에 맞춘다.

---

## 2. MoA 실행 흐름 (decompose → fan-out → verify → synthesize)

1. **Decompose** (Claude): 과제를 독립 하위과제로 분해.
2. **Fan-out** (병렬): 하위과제를 능력레인에 배정, 독립 병렬 실행(§27.10 / agent-delegate — 컨텍스트 봉투 필수).
3. **Cross-verify** (아래 §3): **고위험 산출물만** 다른 seat가 교차검증.
4. **Synthesize** (Claude→BOARD): 파편 결과를 rationale와 함께 병합. 단순 머지 금지. **소수의견 보존**.

---

## 3. 교차검증 트리거 (고위험 산출물 한정 — 쿼터 보호)

일상 산출물엔 **미적용**. 아래만 작성자와 **다른 seat**에 크로스체크 1회:

| 고위험 산출물 | Verifier seat (작성자 ≠ 검증자) |
|---|---|
| 머지 diff · 스키마 변경 | Gemini(코드리뷰/long-context) 또는 Codex |
| 보안민감 코드 · credentials 흐름 | Claude(작성자 아니면) 또는 Gemini |
| 수학/계산 · 정량 결과 | Grok(수학) |
| 실시간 외부사실·시장/트렌드 주장 | **Grok(live 데이터)** |
| UI/UX 산출물 | Codex(UI 레인) + persona-sim |

**과반 반박 시 kill**(다관점 verify). verify는 `ai-debate`의 별도-심판 원칙 재사용.

---

## 4. `ai-debate`와의 경계 (둘 다 MoA 계열)

| | ai-debate | MoA cross-verify (이 문서) |
|---|---|---|
| 대상 | **결정**(설계·아키텍처·비가역, PROTOCOL §35.1) | **일상 실행 산출물** |
| 형태 | 패널 → 별도심판 → DECISIONS(D-code) | 다른 seat 1회 교차검증 |
| 빈도 | 결정 지점만 | 고위험 산출물마다 |

> 즉 우리는 이미 결정 레이어에서 MoA(패널→심판→종합)를 하고 있었다. 이 문서는 그것을 **실행 레이어**로 확장한다.

---

## 5. 적용 지점
- `model-router` 스킬 §9(SimonKCore, 커밋 10acd5f)에 트리거·규칙 반영 완료.
- `ROUTING.md §1.6` 링크·흡수 완료(2026-07-02).
- **런타임(2026-07-03)**: hub-daemon Invoke-AI 프롬프트에 "고위험 산출물이면 §3 매핑의 다른 seat에 verify request 1건 발행 + `verify: requested` frontmatter" 훅 배선. Claude 머지 게이트에서 verify 회신을 종합(synthesize).
- 첫 검증: 최초 고위험 머지에서 다른-seat verify 로그 → `DECISIONS.md` 기록 (대기).

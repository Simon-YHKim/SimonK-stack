---
name: skaihub
version: 0.1.0
description: >
  Use when the user wants to build an AI product or feature and needs a single
  entry point to diagnose intent and route to the right AI-build skill —
  SimonKAIHub 오케스트레이터. 트리거 "AI 기능 만들어", "LLM 앱", "챗봇", "RAG",
  "AI 에이전트", "프롬프트", "AI 평가", "어떤 모델 쓰지", "skaihub", 또는 /skaihub.
  Produces an AskUserQuestion intent diagnosis, a routed sub-skill pipeline
  (model selection → prompt → eval → safety, as needed), and per-step iterative
  develop loops — never skipping the eval and safety gates before production.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
  - Skill
---

# /skaihub — SimonKAIHub 오케스트레이터

AI 제품/기능 빌드의 진입점. **평가·안전 없이 출시하지 않는다.** 의도를 좁히고, 적절한 AI 파이프라인으로 라우팅하고, 단계마다 디벨롭한다.

## 0. SimonKCore 감지 (graceful degrade)
- `agent-delegate`, `model-router`, `persona-validate`, `simon-research` 설치 확인.
- 있으면: 멀티에이전트 위임 `agent-delegate`, 본 스택 내부 라우팅 `model-router`, 출시 전 검증 `persona-validate`, AI 리서치 `simon-research`.
- 없으면: "SimonKCore 미설치 — 위임/검증 제한. `/plugin install simonk-core@simonk-core` 권장." 안내 후 계속.
- `gcloud-helper`(Vertex/Gemini 인증)는 본 플러그인에 번들 → AI 빌드 단독 완주. `model-router`는 스택 내부 라우팅 메타-인프라라 Core 의존(제품 모델 결정은 `ai-model-selector`).

## 1. 의도 진단 (러프 + 쉬운말 + 티어)
대화로 **사용자 수준(AI 개발자/비개발 기획자)**을 감지하고 맞춰 질문한다.
`AskUserQuestion` **1회**, 각 선택지에 **일상어 별칭**:
- LLM 기능·챗봇 — "텍스트 AI 기능 붙이기"
- RAG·문서 Q&A — "내 문서로 답하는 AI"
- AI 에이전트 — "스스로 도구 쓰는 AI"
- 프롬프트 개선 — "AI 답 품질 올리기"
- 모델 선택 — "어떤 AI 모델 쓸지"
- 평가·레드팀 — "AI 성능·안전 점검"
- 가드레일·안전 — "AI 오작동·악용 막기"
- (선택) **단계** 아이디어 / 프로토타입 / 프로덕션 · **제약** 비용·프라이버시·온디바이스

**복합 목표**(RAG+에이전트, 기능+평가+안전)는 단일 선택으로 자르지 말고 순차 실행.

## 2. 라우팅 (의도 → 파이프라인)
| 의도 | 파이프라인 |
|---|---|
| LLM 기능·앱 | `ai-model-selector` → `prompt-engineering` → `llm-eval` → `ai-safety-eval` |
| RAG·문서 Q&A | `rag-builder`(인제스천·청킹·임베딩·검색·인용·평가) → `prompt-engineering` → `llm-eval` |
| AI 에이전트 | `agent-builder` → `prompt-engineering` → `ai-safety-eval` → `llm-eval` |
| 모델 선택 | `ai-model-selector` |
| 프롬프트 개선 | `prompt-engineering` → `llm-eval` |
| 평가·레드팀 | `llm-eval` → `ai-safety-eval` |
| 안전·가드레일 | `ai-safety-eval` |
| AI 인프라 인증(Vertex/Gemini) | `gcloud-helper` |
| 실제 앱/배포 연계 | SimonKStack `/skstack` 핸드오프(빌드·배포는 거기서) |
| 비용 가드 | `paid-api-guard`(Stack) 참조 |

하위 스킬은 `Skill`로 호출.

## 3. 반복 디벨롭 (핵심)
단계마다 산출물 → 평가 → 사용자 확인 → 다음.
- AI는 **eval-driven**: 프롬프트/RAG/에이전트 변경마다 `llm-eval`로 회귀 확인.
- 근거 없는 "잘 된다" 금지 — 평가셋 점수로 말한다.

## 4. AI 무결성 원칙 (게이트)
- **안전 게이트**: 출시 전 `ai-safety-eval`(가드레일·레드팀·PII) 필수.
- **평가 게이트**: 평가셋 없이 프로덕션 금지.
- 비용·레이턴시 상한 명시, 시크릿(API 키) 하드코딩 금지(env), 모델 호출 로깅.
- 환각: 근거·인용·불확실성 표현·휴먼인루프.

## 5. 페르소나 인지 + 전파 (필수)
AI 개발자=스펙·SDK 위주, 비개발 기획자=개념·트레이드오프 설명 위주. §1 감지 신호를 **하위 산출물까지** 전파 — 전문어(임베딩·토큰·temperature·RAG·eval) 첫 등장 1줄 풀이, TL;DR+다음 행동.

## 6. 출시 전 검증 게이트 (Core 유무에 graceful)
- **Core 있으면**: `persona-validate` 호출 — AI 전문가(ML엔지니어·AI안전/평가·프롬프트엔지니어) + 대상 사용자 패널.
- **Core 없으면(솔로/비개발)**: 인라인 경량 self-check 강제 — ① 평가셋(`llm-eval`) 통과 ② 안전 체크리스트(`ai-safety-eval`: 인젝션·PII·탈옥) ③ 전문가 렌즈 1개를 직접 적용한 자기검토. (§0 degrade와 일관 — Core 미설치가 완주를 막지 않는다.)

## 완료 기준
기능이 평가셋 기준을 통과하고 안전 게이트를 지났으며, §6 검증(Core 있으면 `persona-validate`, 없으면 인라인 self-check)에서 치명 리스크 0, 사용자가 확인했을 때.
**완료 후**: `completion-report`(Core)로 HTML 보고서 생성 — 사용자 언어 + 현지시간 로케일 형식(KR: `[YYYY-MM-DD / HH:MM:SS KST]`) + 표·차트(eval 점수·안전 게이트 결과).
(주의: 평가·안전 게이트는 "선언"이 아니라 실제 차단이어야 함 — 회귀 게이트 exit code·적대셋 grader 실구현은 BACKLOG 라운드 참고.)

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.

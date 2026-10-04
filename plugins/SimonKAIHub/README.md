# SimonKAIHub

![version](https://img.shields.io/badge/version-0.2.0-5b8cff) ![license](https://img.shields.io/badge/license-MIT-green) [![validate](https://github.com/Simon-YHKim/SimonKAIHub/actions/workflows/validate-plugin.yml/badge.svg)](https://github.com/Simon-YHKim/SimonKAIHub/actions/workflows/validate-plugin.yml)

> **AI 제품/기능을 끝까지 빌드하는 오케스트레이션 플러그인** — LLM 앱·에이전트·RAG·프롬프트·평가·AI 인프라·AI 안전을, 평가/안전 게이트를 건너뛰지 않고 단계별로.

SimonK 플러그인 스위트의 AI 도메인 워크스테이션. 사용자가 만드는 AI 제품/기능을 돕는다(이 플러그인 자체의 내부 동작이 아님).

## 진입점

```
/skaihub
```

의도를 러프하게 진단(쉬운말·티어) → 적절한 AI 파이프라인으로 라우팅 → 산출물마다 반복 디벨롭 → **평가·안전 게이트 + persona-validate**로 마무리.

### 사용 예시

```
/skaihub 내 앱에 챗봇 붙이고 싶어
/skaihub PDF 문서로 답하는 RAG 만들어줘
/skaihub 우리 LLM 기능 출시 전에 안전 점검해줘
```

인자 없이 `/skaihub` 만 입력하면 무엇을 만들지부터 물어본다.

## 설치

```
/plugin marketplace add Simon-YHKim/SimonKAIHub
/plugin install simonk-aihub@simonk-aihub
```

**권장 동반**: `SimonKCore`(agent-delegate·model-router·persona-validate 등). 실제 앱 빌드·배포 연계는 `SimonKStack`.

## 수록 스킬

**오케스트레이터**
- `skaihub` — AI 빌드 진입점·라우터·게이트

**AI 빌드 (net-new)**
| 스킬 | 하는 일 |
|---|---|
| `prompt-engineering` | 프롬프트 설계(패턴·structured output·인젝션 방어·eval 루프) + 템플릿·eval 러너 |
| `rag-builder` | RAG 파이프라인(청킹·임베딩·벡터스토어·하이브리드·리랭크·인용강제·평가) + pgvector 스키마·eval 스크립트 |
| `agent-builder` | tool-use 에이전트(도구 스키마·실행 루프·가드레일·멀티에이전트) + 루프/가드레일 템플릿 |
| `llm-eval` | 평가 하네스(골든·엣지·적대셋·LLM-judge·회귀 게이트·레드팀) + CI 게이트 스크립트 |
| `ai-model-selector` | 제품용 모델/프로바이더 결정(작업적합·비용·레이턴시·프라이버시·라우팅·폴백) |
| `ai-safety-eval` | AI 안전(입출력 가드레일·모더레이션·PII·탈옥 레드팀·편향·환각 완화) |

**AI 인프라 (자급자족 번들)**
- `gcloud-helper`(Vertex/Gemini 인증) — `model-router`(스택 내부 라우팅)는 Core 의존

## 원칙 (게이트)

- **평가 우선**: 프롬프트/RAG/에이전트 변경마다 `llm-eval` 회귀 확인. 평가셋 없이 프로덕션 금지.
- **안전 게이트**: 출시 전 `ai-safety-eval`(가드레일·레드팀·PII) 필수.
- **검증 게이트**: 완료 직전 `persona-validate`(Core)로 AI 전문가 + 대상 사용자 패널 점검, 치명 리스크 0.
- 시크릿(API 키) env, 비용·레이턴시 상한, 모델 호출 로깅, 환각엔 근거·인용·휴먼인루프.
- 모델·effort·구독 가용성은 `/vibe`의 최신 중앙 레지스트리와 실행 시점의 계정·쿼터 관측으로 확인한다. README의 예시 모델명만으로 라우팅하거나 과금 안전성을 판단하지 않는다.

## 기여

스킬 추가·수정은 **평가셋(`evals/cases.json`) + CI 품질게이트**를 통과해야 한다.
자세한 절차·스키마는 [`CONTRIBUTING.md`](./CONTRIBUTING.md) 참고.

```bash
python -B -m unittest discover -s .github/skill-ci -p test_run_ci_encoding.py
python -B .github/skill-ci/run_ci.py   # 머지 전 로컬 게이트
```

품질 게이트는 자식 Python을 UTF-8로 실행하고 결과를 엄격하게 해석하므로
Windows 기본 CP949 콘솔에서도 같은 검증을 수행한다. 모델/API 호출은 없다.

## 라이선스 / 출처

MIT. 일부 인프라 스킬은 Simon 의 기존 SimonK 스택에서 가져왔고 gstack(garrytan, MIT) 출신이 섞일 수 있으며 출처는 각 SKILL.md·NOTICE 에 유지. © Simon Kim (Simon-YHKim).

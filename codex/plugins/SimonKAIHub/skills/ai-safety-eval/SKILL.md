---
name: ai-safety-eval
description: >
  Use when designing or auditing the safety and guardrails of the user's AI product. 트리거: "AI 안전", "가드레일", "콘텐츠 필터", "탈옥 방어", "프롬프트 인젝션", "환각 줄이기", "PII 마스킹", "jailbreak", "guardrail", "hallucination", /ai-safety-eval. Produces a risk-rated table across seven layers (input/output guardrails, moderation, PII/logging/audit, jailbreak/injection red-team, bias/fairness, hallucination mitigation, regulation) plus a red-team test suite and a guardrail config template. Targets the user's AI feature, not this plugin.
allowed-tools: Read, Write, WebSearch, WebFetch, AskUserQuestion, Bash
version: 1.1.0
author: simon-stack
---

# ai-safety-eval — AI 제품 안전·가드레일 평가

> 사용자가 LLM을 붙인 제품/기능(챗봇, 요약기, 분류기, 에이전트 등)의 **안전성**을 7개 레이어로 점검하고 가드레일을 설계한다. 점검 대상은 "내가 만드는 AI 기능"이며, 이 플러그인/하네스 내부 동작이 아니다.

## 0. 진단 먼저 (AskUserQuestion)

코드/표를 내놓기 전에 다음을 확정한다. 답이 안 나오면 `AskUserQuestion`으로 묻는다.

| 질문 | 왜 필요한가 |
|---|---|
| 누가 쓰나? (성인 / 미성년 포함 / 기업 / 불특정 다수) | 연령·동의·모더레이션 강도 결정 |
| 무엇을 하나? (대화 / 생성 / 분류 / 검색·RAG / 에이전트 실행) | 위험 표면이 다름 |
| 출력이 어디로 가나? (사용자에게 직접 / 다운스트림 시스템 / 외부 게시) | 인젝션·자동화 위험 |
| PII·민감정보를 다루나? (이름·연락처·건강·금융 등) | 로깅·마스킹·보존정책 결정 |
| 도메인 규제는? (의료 / 금융 / 아동 / 일반) | 휴먼인루프·면책 필요 여부 |

진단 결과로 아래 7개 레이어 중 **해당되는 것만** 깊게 판다. 전부 똑같이 다루지 않는다.

## 1. 7-레이어 점검 모델

| # | 레이어 | 핵심 질문 | 산출물 |
|---|---|---|---|
| L1 | 입력 가드레일 | LLM 호출 전에 무엇을 차단·정규화하나 | 분류기 + 차단 규칙 |
| L2 | 출력 가드레일 | 모델 응답을 사용자에게 주기 전 무엇을 검사하나 | 후처리 검사 체인 |
| L3 | 콘텐츠 모더레이션 | 유해 카테고리별 임계값·대응은 | 카테고리 정책 표 |
| L4 | PII·로깅·감사 | 무엇을 남기고 무엇을 지우나 | 로깅 스키마 + 보존정책 |
| L5 | 탈옥·인젝션 레드팀 | 공격에 뚫리나 | 테스트 스위트 + 통과 기준 |
| L6 | 편향·공정성 | 집단별로 다르게 대하나 | 평가 셋 + 격차 지표 |
| L7 | 환각 완화 | 모르는 걸 아는 척하나 | 근거·불확실성·HITL 규칙 |

## 2. L1 입력 가드레일

LLM 호출 **전** 단계. 순서대로 통과시켜야 한다.

1. **정규화**: 유니코드 NFKC, 제로폭/동형문자(homoglyph) 제거, 과도한 공백·base64 의심 토큰 플래그.
2. **분류(classify)**: 위험 의도(자해, 폭력, 불법, 성적, 증오)와 인젝션 패턴을 분류. 레드존이면 LLM 호출 자체를 **단락(short-circuit)** — 안전 응답으로 즉시 대체.
3. **레이트·길이 제한**: 토큰 폭탄·반복 공격 차단.

> 참고: 2nd-Brain 레포는 이 패턴을 C9(`classifyInput()` runs before any LLM call, 레드존 단락)로 강제한다. 같은 구조를 권장한다.

> **결정론 + 모델 이중 레이어 (필수 구조)**: L1 입력과 L2 출력 가드레일은 모두 (1) 결정론 게이트(정규식/lexicon — 모델 불필요)와 (2) 모델 보조 분류기 두 겹으로 동작한다. **결정론이 최종 차단권을 가진다(fail-closed)**: 모델이 "안전"이라 해도 결정론 block/crisis 는 유지되고, 모델은 위험도를 **올리기만** 한다(merge_max_severity, OR 결합). 따라서 모델 미연결 상태에서도 block/crisis 게이트는 실제로 작동한다. 모델은 재현율을 더하는 보조일 뿐이다. 구현 참조: `scripts/classify.mjs`(결정론 분류 + `callModel()` 교체 지점), 명세: `templates/guardrail-config.json` 의 `deterministic_classifier`.

## 3. L2 출력 가드레일 / L3 콘텐츠 모더레이션

응답을 사용자에게 주기 전 검사 체인. 위험도별 대응:

| 위험도 | 예시 카테고리 | 입력 시 | 출력 시 |
|---|---|---|---|
| 차단(Block) | 아동 성착취, 무기·폭발물 제조, 신용카드 탈취 | 호출 차단 + 안전 메시지 | 응답 폐기 + 안전 메시지 + 감사 로그 |
| 위기 단락(Crisis) | 자해·자살 신호 | 즉시 위기 응답 라우팅(전문 자원 안내) | 위기 자원으로 대체, 모델 원문 미노출 |
| 완화(Soften) | 경미한 욕설, 민감 주제 | 통과 + 톤 가이드 | 정책 톤으로 리라이트 |
| 경고(Warn) | 의료·금융·법률 조언 | 통과 | 면책 문구 부착 + 출처 권고 |
| 허용(Allow) | 일반 | 통과 | 통과 |

규칙:
- 차단/위기 대응은 **모델 신뢰에 의존하지 말 것**. 결정론적 룰 레이어가 최종 게이트.
- 모든 차단·위기 이벤트는 L4 감사 로그에 기록(원문 PII는 마스킹 후).
- 임계값은 코드 상수가 아니라 **단일 출처 정책 파일**(예: `lexicon.ts` / `moderation-policy.json`)에서 관리. 런타임 분류와 CI 스캔이 같은 파일을 본다.

## 4. L4 PII · 로깅 · 감사

| 항목 | 권장 |
|---|---|
| 수집 최소화 | 기능에 불필요한 PII는 애초에 입력받지 않는다 |
| 마스킹 시점 | **로그 기록 직전** 마스킹(이메일·전화·주민/카드번호·주소). 평문 PII가 로그·LLM 프롬프트·외부 호출에 새지 않게 |
| 감사 로그 | 모든 LLM 호출에 1건씩 기록(mock·crisis 포함): `ts, route, model, input_class, output_action, pii_masked, latency` |
| 보존정책 | 원문 보존 기간 명시(예: 30일) 후 파기. 동의 철회 시 삭제 경로 |
| 분리 | 감사 로그는 append-only, 일반 DB와 권한 분리 |

> 시크릿·API 키는 **절대 로그·프롬프트·코드에 평문 금지**. 환경변수/시크릿 매니저로만.

## 5. L5 탈옥·프롬프트 인젝션 레드팀

`templates/redteam-suite.md`의 테스트 카테고리를 대상 제품에 맞춰 실행한다.

| 공격 유형 | 대표 기법 | 방어 |
|---|---|---|
| 직접 탈옥 | "이전 지시 무시", DAN, 롤플레이 우회 | 시스템 프롬프트 분리, L1 분류기, 출력 게이트 |
| 간접 인젝션 | RAG 문서·웹페이지·이메일에 숨긴 지시 | 외부 콘텐츠를 **데이터로만** 취급(명령 아님), 출처 격리, 도구권한 최소 |
| 인코딩 우회 | base64·leetspeak·다국어·이모지 치환 | L1 정규화 + 디코드 후 재분류 |
| 시스템 프롬프트 추출 | "네 지침을 그대로 출력해" | 프롬프트 비노출 정책, 출력 필터 |
| 데이터 유출 | 학습/문맥의 PII·시크릿 끌어내기 | 컨텍스트 최소화, 출력 PII 스캔 |
| 도구 남용(에이전트) | 위험 도구 호출 유도(삭제·송금·메일발송) | 도구 allowlist, 파괴적 행위 휴먼 승인 |

통과 기준: 각 카테고리 공격 셋에 대해 **차단/안전응답 비율**을 기록. 회귀 방지를 위해 CI에 스냅샷.

`templates/redteam-suite.md` 는 9개 카테고리(RT-1~9: 직접탈옥·간접인젝션·인코딩우회·프롬프트추출·PII유출·도구남용·유해콘텐츠·위기우회·편향)별 케이스와 측정 방법, 결정론 must-catch 여부를 담는다. 결정론 게이트는 `scripts/classify.mjs` 로 모델 없이 단독 실행해 block/crisis must-catch 100% 를 회귀 기준으로 고정한다.

## 6. L6 편향·공정성

- **평가 셋 구성**: 동일 프롬프트의 보호속성(성별·연령·지역·인종 등)만 바꾼 변형 쌍을 만들어 응답 차이 측정.
- **지표**: 거부율 격차, 톤·도움 정도 격차, 고정관념 표현 빈도.
- **대응**: 시스템 프롬프트에 공정성 지침, 문제 패턴은 출력 가드레일에서 리라이트, 반복되면 데이터·프롬프트 수정.
- 과잉교정(over-refusal)도 편향이다 — 무해 요청을 집단에 따라 더 자주 거부하는지 함께 측정.

## 7. L7 환각 완화

| 기법 | 적용 |
|---|---|
| 근거 강제(grounding) | RAG·인용 의무화. 출처 없으면 "확실하지 않음" 표기 |
| 불확실성 표현 | 추측은 추측으로 — 단정 금지 프롬프트, 신뢰도 낮으면 사용자에게 명시 |
| 휴먼인루프(HITL) | 의료·금융·법률·미성년 영향 등 고위험 출력은 사람 검토/승인 게이트 |
| 검증 가능성 | 사실 주장은 검증 가능한 형태(링크·날짜·수치 출처)로 |
| 거절 허용 | "모른다"가 정답일 수 있게 — 빈칸 채우기 강요 금지 |

## 8. 규제 관점 (개인정보·연령)

- **연령**: 미성년 대상이면 연령대별 가입·동의 분리. 14세 미만은 검증 가능한 보호자 동의(PIPA §22-2 / COPPA). 13~17세 처리 시 데이터 최소화·광고 제한.
- **개인정보**: 수집·이용 동의, 보존·파기, 처리위탁(LLM vendor 포함) 고지, 국외이전 고지. GDPR 대상이면 적법근거·DPA·삭제권.
- **AI 고지**: AI 생성·자동결정 사실 고지. 고위험 자동결정은 사람 개입·이의제기 경로.
- **vendor 데이터 정책 확인**: 모델 제공자가 입력을 학습에 쓰는지(opt-out 여부), 데이터 리전, 보존기간을 `WebSearch`/`WebFetch`로 최신 확인 후 반영.

## 9. 산출 흐름 (실행 절차)

1. **진단**(§0) — `AskUserQuestion`으로 5개 확정.
2. **레이어 선별** — 해당 위험 표면만 §2~§8에서 선택.
3. **정책 파일 1개** — 차단/위기/완화 임계값을 단일 소스로(예: `moderation-policy.json`). `templates/guardrail-config.json` 복사 후 수정.
4. **레드팀 스위트** — `templates/redteam-suite.md`를 제품에 맞게 채우고 실행, 통과율 기록.
5. **위기 놓침 게이트** — `templates/crisis-fn-eval.jsonl` 에 놓치면 안 되는 위기 케이스를 추가하고 `node scripts/crisis_fn_gate.mjs --set templates/crisis-fn-eval.jsonl` 로 측정. **must_not_miss recall < 1.0 이면 빌드 실패.** 위양성은 별도 보고(대조 케이스로 통제).
6. **감사·로깅 스키마** — §4 표대로 정의, PII 마스킹 위치 명시.
7. **CI 게이트** — 정책 파일 JSON lint + `crisis_fn_gate.mjs`(exit 1=놓침) + 레드팀 스냅샷을 파이프라인에 고정.
7. **위험도별 대응 표 + 미해결 위험** 요약 반환.

## 10. 출력 형식

요약은 항상 다음 3블록:

```
[적용 레이어]  L1, L3, L4, L5, L7  (대상: <기능 한 줄>)
[위험도 표]    Block / Crisis / Soften / Warn / Allow 별 대응
[미해결·후속]  남은 위험 + 다음 조치(예: vendor 학습 opt-out 확인)
```

## 11. 안전 가드 (이 스킬 자체)

- 실제 공격 페이로드를 **작동하는 형태로 산출하지 않는다**. 레드팀 스위트는 카테고리·의도·기대 방어를 기술하고, 구체 페이로드는 사용자 환경 내 테스트용으로만 추상화해 제공.
- 차단/위기 임계값을 사용자 승인 없이 낮추지 않는다(약화 = 안전 후퇴).
- vendor·규제 사실은 기억에 의존하지 말고 `WebSearch`/`WebFetch`로 최신 확인 후 날짜 명시.
- 임상·치료 용어로 안전 기능을 포장하지 않는다(제품이 의료기기로 오인되지 않게).

## 12. 관련 자산

- **스크립트** (의존성 0, Node 18+ — 결정론 부분은 모델 없이 작동):
  - `scripts/classify.mjs` — 결정론 분류기(정규식/lexicon 게이트) + 모델 보조(`callModel()` 교체 지점). 라이브러리(`classify()`)·CLI 양용. exit 0=allow/soften/warn, 3=crisis, 4=block.
  - `scripts/crisis_fn_gate.mjs` — 위기 false-negative 게이트. must_not_miss recall 측정, 놓침 시 exit 1(빌드 실패). FP 별도 보고.
- **템플릿**:
  - `templates/redteam-suite.md` — 9개 공격 카테고리(탈옥·인젝션·인코딩·프롬프트추출·PII·도구남용·유해·위기우회·편향) 케이스 표 + 측정 방법
  - `templates/guardrail-config.json` — 위험도별 정책 단일 소스. block/crisis 에 결정론 분류기 명세(정규식·임계·KO/EN 위기 신호) 포함
  - `templates/crisis-fn-eval.jsonl` — 위기 놓침 평가셋(KO/EN/혼용/인코딩 우회 + 대조 케이스)
- **스킬 연계**:
  - `security-orchestrator` / `cso` — 제품 전반 보안 감사
  - `authz-designer` — 도구·데이터 접근권한(에이전트 인젝션 방어와 연계)
  - `paid-api-guard` — vendor 호출 비용·남용 가드
  - `ai-model-selector` — 사용자 제품의 안전 분류용 경량 모델 선택 (`model-router`는 스택 내부용)

## 13. Roadmap

- v1.0: 7-레이어 점검 + 위험도 표 + 레드팀/정책 템플릿
- v1.1 (현재): 결정론 분류기(`classify.mjs`, 정규식/lexicon, KO/EN 위기 신호) + 위기 놓침 게이트(`crisis_fn_gate.mjs`, recall<1.0 빌드 실패) + 위기 FN 평가셋 + 레드팀 9카테고리 확충 + 결정론·모델 이중 레이어 명시
- v1.2: 레드팀 스위트 자동 실행 러너(전 카테고리 스냅샷 회귀)
- v1.3: 편향 평가 셋 생성기(보호속성 변형 쌍 자동 생성)
- v1.4: vendor 데이터정책 fetch 캐시 + 규제 변경 알림

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.

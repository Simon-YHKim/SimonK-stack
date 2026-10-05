---
name: spec
description: "기능 스펙·요구사항을 인터뷰로 끌어내 spec.md 를 산출할 때 사용 — 트리거 \"스펙 정리\", \"기능 명세\", \"PRD 초안\", \"요구사항 정리\", \"이 기능 스펙 잡아줘\", \"명세서 만들어줘\", \"draft a spec\", \"write a PRD\", \"requirements doc\", 또는 /spec. 문제·대상 사용자·성공 기준·범위(in/out)·엣지 케이스·수용 기준(Given-When-Then)·의존·리스크를 한 번에 하나씩 묻는 인터뷰로 메우고, 빈칸을 추정으로 채우지 않으며, 최종적으로 docs/specs/<slug>/spec.md 한 장으로 정리한다. dev-orchestrator 0단계(진단)로 핸드오프해 구현에 넘긴다. 새 앱 전체 기획은 app-dev-orchestrator, 완성된 스펙 깨부수기는 grill-me 로 분리한다."
allowed-tools: Read, Write, Edit, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# spec

하나의 기능을 만들기 전에 **무엇을 / 누구를 위해 / 어디까지 / 무엇이 성공인가**를 인터뷰로 끌어내
구현 가능한 한 장짜리 `spec.md` 로 정리한다.

이 skill 의 본질은 **빈칸을 추정으로 채우지 않는 것**이다. AI가 가장 흔히 실패하는 지점은
"이해했다고 착각하고 엉뚱한 걸 만드는 것"이다. spec 은 코드 한 줄 쓰기 전에 모든 결정 분기를
사용자에게 확인해 misalignment 를 차단한다.

## 발동 조건

- "이 기능 스펙 정리해줘", "기능 명세 잡아줘", "PRD 초안 써줘", "요구사항 정리하자"
- "draft a spec", "write a PRD", "requirements doc"
- 명시적 호출: `/spec`

**발동하지 않는 경우**:

| 요청 | 올바른 skill |
|---|---|
| "새 앱 처음부터 만들자" (전체 기획) | `app-dev-orchestrator` |
| "이 스펙 구멍 찾아줘 / 깨봐" (완성된 스펙 검증) | `grill-me` |
| "이 기능 바로 구현해줘" (스펙 이미 명확) | `dev-orchestrator` |
| "그냥 한 줄만 고쳐" (자명한 변경) | 인터뷰 생략, 바로 작업 |

## 핵심 원칙

1. **한 번에 하나씩.** 질문을 묶지 않는다. 한 답을 받은 뒤 다음 질문.
2. **추정 금지.** 모르는 칸은 비워두고 `OPEN:` 으로 표시한다. 임의로 채우지 않는다.
3. **추천 답 동봉.** 각 질문에 "내 추천: X (이유 Y)" 를 붙여 사용자가 빠르게 동의/반박하게 한다.
4. **읽어서 알 수 있으면 묻지 않는다.** 기존 코드·문서에 답이 있으면 `Read` 로 먼저 확인.
5. **수용 기준은 Given-When-Then.** 모호한 형용사("빠르게", "직관적으로") 금지. 측정 가능하게.
6. **한 장으로 끝낸다.** spec 은 소설이 아니다. 구현자가 5분 안에 읽고 시작할 수 있어야 한다.

## 인터뷰 — 9개 슬롯

`AskUserQuestion` 으로 아래 순서대로, 한 번에 하나씩 묻는다.
각 슬롯에 추천 답을 제시하되, 사용자 답이 우선한다.

| # | 슬롯 | 끌어낼 것 | 비었을 때 |
|---|---|---|---|
| 1 | 문제 (Problem) | 지금 무엇이 불편한가. 이 기능이 없으면 무슨 일이? | BLOCKER — 문제 없는 기능은 만들지 않는다 |
| 2 | 대상 사용자 (Who) | 누가 쓰는가. 1차/2차 사용자, 권한 등급 | BLOCKER |
| 3 | 성공 기준 (Success) | 무엇이 보이면 "됐다"인가. 측정 지표 1~3개 | BLOCKER |
| 4 | 범위 In (In Scope) | 이번에 만드는 것 (구체 동작 목록) | BLOCKER |
| 5 | 범위 Out (Out of Scope) | 이번에 **안** 만드는 것. 다음으로 미루는 것 | 명시 권장 (scope creep 차단) |
| 6 | 엣지 케이스 (Edge) | 빈 값/최대치/동시성/권한 거부/오프라인/실패 | OPEN 허용 |
| 7 | 수용 기준 (Acceptance) | Given-When-Then 시나리오 (3~7개) | BLOCKER — 테스트의 씨앗 |
| 8 | 의존 (Dependencies) | 필요한 API/테이블/권한/외부 서비스/secret | OPEN 허용 |
| 9 | 리스크 (Risks) | 깨질 수 있는 것, 되돌리기(rollback), 관측(observability) | OPEN 허용 |

### 질문 형식 예

> **(3/9) 성공 기준**
> 이 기능이 "됐다"고 말하려면 무엇이 관찰돼야 하나요?
> 내 추천: "사용자가 3탭 안에 항목을 저장하고, 재방문 시 그대로 보인다" — 동작+지속성 두 축이 측정 가능해서.
> 다른 기준이 있으면 알려주세요.

### 엣지 케이스 체크리스트 (슬롯 6에서 제시)

빠짐없이 훑되, 해당 없는 건 N/A 로 적는다.

- 빈 입력 / null / 길이 0
- 최대치 (긴 문자열, 큰 목록, 동시 요청)
- 네트워크 끊김 / 타임아웃 / 재시도
- 권한 거부 (비로그인, 타인 리소스 접근 — IDOR)
- 동시성 / 경쟁 상태 (같은 항목 두 번 저장)
- 기존 데이터 마이그레이션 (이미 있는 레코드는 어떻게)

## RN/Expo + 웹 맥락

해당 프로젝트가 RN/Expo 또는 웹이면 스펙에 다음을 별도로 확인한다 (해당 없으면 생략):

- **플랫폼 차이**: iOS / Android / Web 동작이 다른가? (back 버튼, 권한 prompt, deep link)
- **오프라인 상태**: 네트워크 없을 때 어떻게 보이나
- **secret**: API 키·토큰은 코드에 박지 않고 env(`EXPO_PUBLIC_*` 는 공개됨에 주의)·서버로 보낸다. spec 의 의존 슬롯에 "secret: 서버 경유" 로 명기
- **i18n**: 사용자 노출 문자열은 EN/KO 키 쌍이 필요한가

## 산출물 — spec.md

`docs/specs/<slug>/spec.md` 한 장. `<slug>` 는 기능명 kebab-case.
템플릿: `templates/spec-template.md`.

구조:

```markdown
# Spec: <기능명>

- 작성일: YYYY-MM-DD
- 상태: draft | ready
- slug: <kebab-slug>

## 1. 문제
## 2. 대상 사용자
## 3. 성공 기준
## 4. 범위
### In Scope
### Out of Scope
## 5. 엣지 케이스
## 6. 수용 기준 (Given-When-Then)
## 7. 의존
## 8. 리스크 & 롤백
## 9. 미해결 질문 (OPEN)
```

`OPEN:` 항목이 남아 있으면 상태는 `draft`. 모두 해소되면 `ready` 로 올린다.

## 검증

작성 직후 결정론 스크립트로 필수 슬롯 누락·OPEN 잔여를 점검한다.

```bash
bash scripts/check-spec.sh docs/specs/<slug>/spec.md
```

- exit 0 — 필수 슬롯 충족, OPEN 없음 → 상태 `ready` 가능
- exit 1 — 필수 슬롯 누락 또는 OPEN 잔여 → 인터뷰 재개
- exit 2 — 파일 없음/읽기 불가

스크립트는 BLOCKER 슬롯(문제/대상/성공/범위 In/수용 기준)의 섹션이 비어 있는지,
`OPEN:` 마커가 몇 개 남았는지를 헤딩과 본문으로 판정한다 (LLM 호출 없음, 결정론).

## 핸드오프 — dev-orchestrator 0단계

spec 이 `ready` 가 되면 구현으로 넘긴다.

- `dev-orchestrator` 의 **단계 1(진단)** 입력으로 `spec.md` 를 그대로 전달.
- 진단 단계는 spec 의 § 1~4 를 "무엇을·왜·어디서" 요약으로 흡수하고,
  § 6 수용 기준은 `simon-tdd` RED 단계의 실패 테스트 씨앗이 된다.
- 핸드오프 한 줄: *"docs/specs/<slug>/spec.md 기준으로 dev-orchestrator 시작"*.

스펙에 handwaving 이 남아 있으면 넘기기 전에 `grill-me` 로 한 번 더 깨본다.

## 안티패턴

- ❌ 9개 슬롯을 한 번에 다 묻기 (한 번에 하나)
- ❌ 빈칸을 그럴듯한 추정으로 채우기 (→ `OPEN:` 으로 남길 것)
- ❌ 수용 기준을 형용사로 ("직관적으로 동작") → Given-When-Then 으로
- ❌ Out of Scope 비워두기 (scope creep 의 입구)
- ❌ spec 없이 곧장 코드 — 자명한 변경이 아니라면
- ❌ secret 을 spec 본문/예시에 노출

## Related skills

- `dev-orchestrator` — spec 의 핸드오프 대상 (구현 7단계의 0단계 진단)
- `grill-me` — 완성된 spec 을 한 문항씩 깨부수는 검증 (이 skill 의 하류)
- `simon-tdd` — § 6 수용 기준이 RED 단계 실패 테스트로 변환됨
- `release-notes` — 출시 시 spec 의 In Scope 가 사용자 공지의 재료
- `app-dev-orchestrator` — 새 앱 전체 기획 (이 skill 은 단일 기능 단위)

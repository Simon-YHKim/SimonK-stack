---
name: human-voice-guard
description: "Use when the user wants to check or rewrite text to sound human instead of LLM-generated—triggers \"어투 검사\", \"AI 티 나는데 고쳐줘\", \"자연스럽게 다시\", \"GPT 어투 빼줘\", \"진짜 사람처럼\", \"문체 일관성\", \"human voice\", \"de-AI this\", \"sound less robotic\", \"remove LLM tone\", \"natural rewrite\". Different from consistency-guard (which is data/schema consistency): this guards voice/tone. Detects LLM tells (excessive em-dashes, '~을 도와드립니다', 'In conclusion', 'leverage', 'robust', emoji overload, 3-bullet syndrome, list-of-3 closures, '저는 ... 입니다' formality drift, English-translation Korean) and rewrites in plain human voice. Produces a diff with each change tagged by reason, plus a per-project STYLE.md so subsequent text stays consistent."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.0
author: simon-stack
---

# human-voice-guard

LLM 특유의 어투를 감지·제거하고 _진짜 사람이 쓴 것 같은_ 글로 다시 씁니다.
**프로젝트 단위 STYLE.md** 도 함께 만들어 다음 번에도 어투가 흔들리지 않도록.

## 발동 조건

- "이거 AI 티 나는데 고쳐줘"
- "어투 좀 자연스럽게"
- "Claude/GPT 냄새 빼줘"
- "문체 일관성 확인해줘"
- 릴리즈 노트, 마케팅 카피, 블로그 글, 앱 내 텍스트, README 검사 시

## 감지하는 LLM Tell (한국어)

| 패턴 | 예시 | 교정 |
|---|---|---|
| 과도한 공손체 | "~을 도와드립니다", "~을 제공해 드립니다" | "~합니다", "~할 수 있어요" |
| 영어 직역 | "그것은 ~합니다", "당신의 ~을 위해" | 능동·구어체 한국어 |
| 마케팅 공허어 | "혁신적", "강력한", "원활한", "직관적", "최적화" | 구체 수치/예시 |
| 3-bullet 증후군 | 모든 답변이 3개 불릿 | 의미 있는 만큼만 |
| Closing 의식 | "결론적으로...", "정리하자면...", "이상입니다" | 자연 종결 |
| 이모지 도배 | 🎉✨🚀 한 줄에 3개 | 의미 있는 1개 |
| 과도한 — 대시 | "—을 통해—" | 쉼표·괄호 |
| 미사여구 | "여러분의 소중한 의견을 반영하여" | 직접 |
| 자기 인용 | "저는 AI 어시스턴트로서..." | 삭제 |
| 모호 권유 | "고려해 보시는 것은 어떨까요?" | "X 하세요" 또는 "X 가 낫습니다" |

## 감지하는 LLM Tell (English)

| 패턴 | 교정 |
|---|---|
| "leverage", "robust", "seamless", "delve" | 평범한 동사 |
| "In conclusion", "It's worth noting" | 삭제 |
| "Not only X, but also Y" | 단순 등위 |
| "I hope this helps!" | 삭제 |
| Em-dash 폭주 | 쉼표/괄호 |
| "**Bold the answer**" 강박 | 의미 있을 때만 |
| 모든 응답이 numbered list | 산문 사용 |

## 워크플로

### 1. 입력 받기
- 파일 경로 또는 텍스트 블록
- (선택) 대상 채널: 스토어 / 블로그 / 앱 내 / 트윗 / README — 어조 다름

### 2. 스캔
- 위 표 기준으로 LLM tell 식별
- 각 발견을 `(파일:줄, 패턴, 원문, 제안)` 으로 기록

### 3. 리라이팅
- Edit tool 로 in-place 교정 (사용자 승인 후)
- 또는 `<file>.rewritten.md` 별도 산출

### 4. STYLE.md 생성/갱신
프로젝트 루트에 `STYLE.md` — 다음 번에도 일관성 유지:

```markdown
# Voice & Style — <Project>

## 톤
- 채널: <store / blog / in-app>
- 어투: <친근 반말 / 정중 존댓말 / 무성격 정보전달>
- 페르소나: <누구처럼 말하는가 — 친한 친구 / 도서관 사서 / 동네 가게 주인>

## 어휘 금지 목록
- 혁신적, 강력한, 원활한, ...
- leverage, robust, ...

## 어휘 선호
- "도움" 대신 "쓸모"
- "기능" 대신 "할 수 있는 것"
- ...

## 구조 규칙
- 글머리표 한 글에 5개 이하
- 이모지 단락당 1개 이하
- 한 문장 30자 이하 권장

## 예시 (good / bad)
- ❌ "본 서비스는 사용자의 효율적인 일정 관리를 지원합니다"
- ✅ "일정이 한눈에 보입니다"
```

### 5. 회귀 방지
- `STYLE.md` 가 있는 프로젝트에서 새 텍스트 작성 시 이 skill 이 _자동 참고_
- CI 옵션: `scripts/voice-lint.sh` (이 skill 이 생성) — 금지어 grep

## 산출

| 모드 | 산출 |
|---|---|
| audit | 발견 목록 (수정 안 함) |
| rewrite | 교정된 파일 + 발견 목록 + STYLE.md |
| init | STYLE.md 만 생성 (새 프로젝트) |

## 안티패턴

- ❌ 모든 텍스트를 같은 어조로 강제 (스토어 vs 블로그 다름)
- ❌ "자연스럽게" 라는 모호한 목표 — 페르소나 구체화 필수
- ❌ 한 번 통과 후 잊기 — STYLE.md 가 영구 회귀 방지

## 사용자 강조 원칙

> "claude, gpt, gemini 등 LLM 특유의 어투 방지하고, 마치 진짜 사람이 말하고 쓰는 듯한 어투를 지향함."

이 skill 은 그 원칙을 _코드화_ 한 것. 발견된 LLM tell 은 wiki 의 [[concepts/recurring-mistakes]] 에 새 mistake 코드로 append 후보.

## Related Skills

- `consistency-guard` — 데이터/스키마 일관성 (다른 도메인)
- `release-notes` — § 4 어투 가드에서 이 skill 호출
- `document-release` — 문서 본문 어투 통일 시 연동

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.

---
name: html-default-output
description: "Use when producing a spec, plan, report, PR explanation, or any artifact a person will read and judge — triggers \"HTML로 만들어줘\", \"스펙 정리해줘\", \"리포트 만들어줘\", \"PR 설명\", \"산출물 포맷\", \"make this HTML\", \"output as HTML\", \"one-off editor\". Produces such artifacts as self-contained HTML instead of markdown, and flags candidates for interactive one-off editors (sliders, drag-sort, copy-as-prompt). Length alone never makes a file: HTML is made only when the output serves re-reading, a decision, structure, comparison, accumulation or sharing, and its format floor is global instruction §6."
allowed-tools: Read, Write, Edit, Grep, Glob
version: 1.1.0
author: simon-stack
---

# html-default-output

사람이 읽고 판단할 산출물을 HTML 로 만들지 정하고, 양방향 일회용 에디터 후보를 식별하는 skill.

근거 출처: Anthropic 엔지니어 Thariq Shihab 의 HTML 출력 논의 + Karpathy 의 출력 진화 단계 (Simon-LLM-Wiki `concepts/ai-output-format.md`).

## 전역 지침과의 관계 (먼저 읽는다)

- **형식 바닥선은 사용자 전역 지침 §6(산출물 규격)이다.** 등급(S/M/L)·헤더·요약/상세 탭·메모 사이드바·외부 네트워크 0·색과 테마·산출 전 자가 감사는 전부 거기서 정한다. 이 스킬은 그 규칙을 옮겨 적지 않는다(§0-2). 부딪치면 §6 이 이긴다.
- **파일을 만들지 말지는 전역 §2 가 먼저다.** 기본은 인라인 답이다. 별도 산출물은 재열람·결정·구조·비교·누적·공유 중 하나가 목적일 때만 만든다. 길이는 이유가 아니다.
- 이 스킬이 더하는 것은 둘이다: ① 만들기로 했을 때 HTML 인가 마크다운인가 ② 인터랙션 깊이(Lv1~Lv4).

## 핵심 명제

마크다운은 2000년대 초 _사람이 사람에게_ 쓰던 포맷이다. 지금 산출물을 쓰는 건 AI 이고 받는 건 사람이다. 따라서 산출물은 사람이 가장 잘 받아들이는 형태여야 한다.

출력 진화 단계 (Karpathy): 텍스트 → 마크다운 → **HTML** → 인터랙티브. 지금 HTML 이 새 디폴트가 되는 단계.

100줄 넘는 마크다운은 작성자도 사용자도 끝까지 안 읽는다. 그렇다고 길이가 파일을 만들 이유는 아니다 — 먼저 줄이고, 남는 것이 위 6개 목적 중 하나일 때 HTML 로 만든다.

## HTML 기본 정책

다음 산출물이 위 6개 목적 중 하나를 가질 때 HTML 로 만든다:

| 산출물 유형 | HTML 이 주는 것 |
|---|---|
| 스펙·계획 | 디자인 옵션 그리드 비교, 트레이드오프 라벨 |
| 코드 리뷰·PR 설명 | diff 옆 주석 + 위험도별 색상 |
| 디자인 프로토타입 | 슬라이더로 파라미터 튜닝 |
| 리포트·리서치 | SVG 다이어그램 + 발표자료급 레이아웃 |
| 커스텀 에디터 | 드래그·정렬 후 "copy as markdown" 회수 |

## 인터랙션 깊이 Lv1~Lv4 (Thariq Shihipar / html-it 패턴)

전역 §6 의 등급(S/M/L)과는 다른 축이다. 등급은 **무엇을 담나**(탭·사이드바 구성), Lv 는 **얼마나 만지나**(인터랙션). 헤더에 적는 것은 §6 등급뿐이고, Lv 는 설계 판단에만 쓴다.

| Lv | 형태 | 예시 | 추가 비용 |
|---|---|---|---|
| **Lv1 Static doc** | 마크다운을 HTML 형식으로 (목차·앵커·코드 하이라이트) | 스펙·계획·보고서 | 거의 0 |
| **Lv2 Visual artifact** | SVG·표·diagram·dashboard | 비교 매트릭스·diff 시각화·timeline | 중 |
| **Lv3 Interactive** | 슬라이더·토글·필터 + export-as-prompt | 프롬프트 튜닝·A/B 비교·파라미터 sweep | 높음 |
| **Lv4 Throwaway tool** | 미니앱 (칸반·설정 편집기·체크리스트) | 30분 작업을 위한 30분 도구 (아래 § 일회용 에디터 패턴) | 매우 높음 |

판단 흐름:
1. **사람이 _읽기만_ 하나** → Lv1
2. **데이터·관계 비교가 핵심**인가 → Lv2 (SVG/table)
3. **값을 _조작_ 해야 결정 가능**한가 → Lv3 (slider/toggle)
4. **작업 자체가 도구 만들기**인가 → Lv4 (mini-app)

Lv3+ 일 때는 반드시 "copy as prompt / markdown" 회수 패턴 포함 — 도구가 끝나도 출력이 회수 가능.

## HTML vs 마크다운 판단

만들기로 정한 뒤(전역 §2 통과) 포맷을 고른다.

- **HTML 우선** — 사람이 읽고 _판단_ 할 산출물, 비교·시각화·인터랙션이 가치를 더하는 경우.
- **마크다운 유지** — git 추적이 핵심인 코드·문서 (HTML 은 diff 노이즈가 큼), 짧은 답변, 커밋 메시지, 채팅 인라인 응답.

판단이 애매하면: "사람이 이걸 끝까지 읽고 결정해야 하나?" 가 yes 면 HTML.

## 일회용 에디터 패턴

30분짜리 작업을 위해 30분짜리 _도구_ 를 만든다. 도구 제작이 작업보다 빠른 시대의 패턴.

식별 기준 — 다음에 해당하면 일회용 에디터 후보:

- 항목 여러 개를 _분류·정렬·우선순위_ 하는 작업 (예: 티켓 30개를 Now/Next/Later/Cut)
- 값을 _튜닝_ 해보고 마음에 드는 것을 고르는 작업 (애니메이션 파라미터, 색상)
- 사람의 결정을 받아 다시 시스템에 넣어야 하는 작업

에디터 구성 요소:

1. 인터랙션 UI — 드래그, 슬라이더, 체크박스
2. AI 의 사전 분류 — 빈 화면이 아니라 추천 상태에서 시작
3. 회수 버튼 — "copy as markdown" / "copy as prompt" 로 결과를 텍스트로 추출
4. 사람이 추출한 결과를 AI 에게 재투입 → 양방향 루프

핵심은 사람과 AI 가 _같은 루프_ 안에 머무는 것. 사람이 산출물을 안 읽으면 AI 결정을 그냥 따라가게 되어 검토 루프가 붕괴한다.

## Workflow

1. **만들지 판단** — 전역 §2. 인라인으로 끝나면 파일을 만들지 않는다.
2. **포맷 분류** — 위 "HTML vs 마크다운 판단".
3. **HTML 이면 등급과 Lv 결정** — 전역 §6 등급(기본 S) + 위 Lv. 구조·바닥선은 §6 을 따른다(자체완결, 외부 의존 0).
4. **일회용 에디터 후보 점검** — 분류·튜닝·결정 회수 작업이면 인터랙티브 요소 + 회수 버튼 추가.
5. **구현 위임** — 실제 HTML 생성은 `design-html` (gstack) 패턴을 따른다.
6. **비용 고지** — 토큰 2~4배, git diff 노이즈를 사용자에게 한 줄 안내.

## 비용 (정직하게)

- 토큰 2~4배, 응답 시간 증가.
- HTML 은 git diff 가 지저분 (줄바꿈 노이즈).
- 트레이드오프: 안 읽히는 산출물의 손해 vs 토큰 비용. 읽혀야 하는 문서면 HTML 이 이긴다.

## 시작법 (사용자용)

스킬·설정 없이도 프롬프트 끝에 "HTML 로 만들어줘" 한 줄이면 된다. 이 skill 은 그 한 줄을 _기본 동작_ 으로 끌어올려, 사용자가 매번 명시하지 않아도 산출물 유형에 따라 HTML 을 제안한다.

## 피해야 할 함정

- 길이만 보고 파일 만들기 — 줄여서 인라인으로 끝날 답을 HTML 로 부풀리지 않는다 (전역 §2).
- 모든 것을 HTML 로 — 커밋 메시지·코드까지 HTML 화하면 git 추적이 망가진다. 분류가 먼저.
- 외부 CDN·웹폰트 의존 HTML — 자체 완결형이어야 공유·오프라인 열람이 된다.
- 빈 에디터 — AI 사전 분류 없이 빈 화면을 주면 사람이 처음부터 해야 한다.
- 회수 버튼 누락 — 사람이 만진 결과를 텍스트로 못 뽑으면 루프가 끊긴다.

## Related skills

- `design-html` (gstack) — HTML 산출 자체의 구현 패턴
- `simon-design-first` — HTML 디자인 시 AI slop 방지 프록시
- `simonk-report` — 세션 보고서 전용 고정 스키마 (§6 S 등급 템플릿 포함)
- `session-context-tracker` — 산출물 포맷과 세션 관리는 같은 날 흡수한 자매 정책
- `release-notes` — dev/user 산출물 분리. 포맷 정책과 결합 가능

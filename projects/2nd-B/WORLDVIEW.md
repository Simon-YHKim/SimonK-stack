---
owner: claude
status: canon (정본)
mutability: STRUCTURE-IMMUTABLE  # 큰 틀(아래 §1~§8)은 불변. 구현 디테일만 진화한다.
source: C:\2ndB\2ndb-thought-organization-synthesis.html  (2026-06-17 통합 정본)
last-sync: 2026-06-17 KST
applies-to: [claude, codex, antigravity, grok]   # 4-AI 전원이 매 사이클 인지
---

# WORLDVIEW.md — 2nd-Brain 세계관·구조 정본 (4-AI 공통 인지)

> **목적**: 2nd-B 디벨롭(리팩토링)을 4-AI가 같은 그림으로 진행하도록, `2ndb-thought-organization-synthesis.html`의 **불변 큰 틀**을 허브 정본으로 고정한다.
> **불변 원칙**: 아래 §1~§8 구조(북극성/7별/두뇌0-3/L1-L5/밝기=품질/propose-ratify/용어매핑/C-code)는 **바꾸지 않는다**. 작업은 *새로 짓기*가 아니라 *잇고·정의하고·표면화하는* **리팩토링**이며, **완벽해질 때까지 반복 개선**한다.
> **읽는 주체**: Claude(구현·머지)·Codex(UI/UX)·Antigravity(네이티브 QA)·Grok(소비자 advisory) — 매 사이클 시작 시 이 파일을 인지하고, 자기 lane 작업이 이 정본과 어긋나지 않게 한다.

---

## §0. 한 문단 요지
가장 강한 카드는 새 기능이 아니라 **이미 배포된 검증 엔진 하나를 끝까지 잇는 것**이다.
`지금의 나(BFI-44) → 데이터 품질 점수 → 별 밝기 → 그래프 → 비서가 그 위에서 답함 → 비서가 다음 학습 한 걸음을 제안(propose-ratify)`.
이 **단일 루프**가 "AI가 나를 데이터로 축적해 전용 비서가 되어 북극성을 향하게 한다"는 비전 전체를 증명한다. 나머지는 "설계됨, 일부만 시연"으로 **정직하게** 표시한다.

## §1. 두뇌 0/1/2/3 — 앱은 '다리'다 (정본 한 문장)
> **"2nd-Brain은 당신의 2nd brain(데이터의 유기적 망)을 짓고 3rd brain(AI 비서)을 배선해, 1st brain(물리 뇌)을 0th brain의 북극성(철학)을 향해 정진시키는 다리(bridge)다."**
앱은 결코 '두뇌'가 아니라 **다리/비계**다.

| 층 | 정체 | 바인딩 |
|---|---|---|
| **0th brain** | 북극성 = 철학·역할의 집합. **사용자 소유**. | 항상 최대 밝기(열망, 데이터 노드 아님) |
| **1st brain** | 물리 뇌 = 사용자 본인. 모든 것이 섬기는 대상. | — |
| **2nd brain** | LLM Wiki = 내 데이터 유기망(records·sources·personas·wiki_pages). **앱이 짓는다**. | Axis-1 |
| **3rd brain** | LLM AI 비서(SecondB on `gemini.ts`, RAG). **앱이 배선한다**. | Axis-2/3 |

## §2. 북극성 + 북두칠성 7별 (별 토폴로지 — D1 채택안)
- **레벨 혼합 제거**가 근본 수정이다. **역할(Roles)·액션(Action)·지식(Knowledge)은 별이 아니다** → 북극성 아래 **목표트리**(Who/Why/What → Roles → Projects → Tasks)로 렌더. 측정축이 아니다(밝기·신뢰도 만들지 않음).
- **7별 = 자기이해 렌즈 한 종류**. 각 별은 (a)추정 구성 (b)elicitation 경로 (c)스코어러 (d)밝기 판독값을 갖는다.
- **"지금의 나" = 별1(도구)**. **소울 코어/페르소나 카드 = 7별을 종합한 판독값(AGGREGATE, 별 아님)** = 북극성 밝기의 표시기. (D2)

| 별 | 이름 | 구성(construct) | 엔진 | 상태 |
|---|---|---|---|---|
| ★1 | 지금의 나 (Trait State) | Big Five | `persona/bfi.ts` + MBTI 스크리너 | SHIPPED |
| ★2 | 회상 (Narrative Origins) | McAdams 내러티브 정체성 | `interview/probe.ts` 시기×층 | SHIPPED |
| ★3 | 보여지는 나 (Reputation/Other-view) | 타인평정 Big Five + 평판(+타당도 도구) | 360 peer Likert | ABSENT(NEW) |
| ★4 | 순간의 나/리듬 (Momentary State) | 개인내 변동성·상태정서+맥락 | `esm.tsx` (채점 연결 필요) | STUB |
| ★5 | 관계의 나 (Relational Self) | 애착 불안/회피 | `persona/attachment.ts`(ECR-S) | SHIPPED |
| ★6 | 될 수 있는 나 (Possible/Future Self) | Possible Selves(Markus&Nurius 1986) | 희망/두려운/예상 자기 | ABSENT(NEW) |
| ★7 | 가치의 나 (Values & Strivings) | SDT(자율·유능·관계)+VIA+Emmons 분투 | `sdt:* / via:*` 태그(승격) | PARTIAL |

## §3. 단일 L1~L5 가치 사다리 (DIKW·Bloom·밝기·신뢰도 통합)
떠다니던 다섯 척도를 **하나의 순서척도**로 붕괴. 이 한 정수가 동시에 **노드·별 밝기 = 데이터 품질 = 출처 신뢰도 = 드릴 정지레벨**이다. 노드는 증거 조건 충족 시에만 상승하고, **AI는 상승을 제안(propose)하고 사용자가 승인(ratify)**한다.

| 레벨 | 이름 | 밝기 | DIKW · Bloom | 상승 조건 |
|---|---|---|---|---|
| L1 | Raw / 날것 | 20% | Data · Remember | 단일 Log 캡처, 미처리 |
| L2 | Tagged / 태깅됨 | 40% | Information · Understand | 분류 + 프레임워크/도메인 태그(clipper kind, BFI/SDT id) |
| L3 | Connected / 연결됨 | 60% | Knowledge · Apply/Analyze | Pattern Link로 ≥2 노드 연결 |
| L4 | **교차검증** | 80% | Evaluate | ≥2 독립 경로 일치(BFI+감사+peer 수렴). 라벨=**"교차검증(cross-source agreement)"** |
| L5 | 실행가능 | 100% | Wisdom · Create | 사용자가 **승인한** 자기모델 수정/추천 구동 |

**v1 밝기 공식(IRT 불필요, 오늘 계산 가능)**: 축별 품질 티어 = 증거경로 중 최대값 — `검증도구 완료→4~5 · 관찰 ≥15→4 · 5~14→3 · 1~4→2 · 기본→1`, 그리고 **≥2 독립경로 일치(교차수렴) 시 +1 티어(최대 5 상한)**. `traitConfidenceFor()` 그대로 재사용. 별 밝기와 다음행동 넛지가 **같은 정의**를 공유한다. 북극성은 사다리 면제(항상 최대).

## §4. 측정 하네스 (lean v1) — 핵심 down-scope
- **풀 IRT/CAT는 post-XPRIZE로 강등**(솔로 2개월에 과설계, item 데이터 없음). v1 = **경량 신뢰도 프록시** = f(완성도 + 관찰수 + 최신성 + 교차경로 합의).
- **정지규칙(인터뷰)**: 소프트 50턴 캡이 아니라 **별 종합레벨이 목표 L(기본 L4)에 도달**할 때까지 프로브. 자유텍스트 경로는 **삼각측정/수렴**(≥2 독립경로 일치 OR 추정치 포화)으로 멈춤.
- **self-other 타당도(Vazire SOKA)**: self=내적·저관찰 특성(신경증·애착불안) 우세, other(peer)=외적·고관찰 특성(외향성·지성/개방성) 동등 이상. 특성별 합의=타당도=밝기. 큰 불일치=성장 인사이트(비임상 프레이밍).

## §5. LLM vs 도구 분리 (하네스 순수성)
- **INSTRUMENT 층(결정론·코드)**: 검증 item 뱅크·구성 정의·역코딩·스코어러 — **오직 이 층만 trait 점수를 방출**(이미 bfi/ecr에 존재).
- **LLM 층(`gemini.ts` 경유, C1)**: 단 두 가지 — (1)다음 질문 자연스럽게 표현 (2)자유텍스트를 `{construct_id, direction, strength, quote}` 타입 증거로 추출. **responseSchema+검증기가 LLM이 내놓은 숫자 점수를 거부.**
- **계약 테스트**: 모의 LLM이 쓰레기 점수를 반환해도 페르소나 점수 불변 단언. 현재 휴리스틱 채점은 이미 결정론 TS이므로 "뜯어내라"가 아니라 "이 속성을 보존하고 자유텍스트 추출 경로를 짓기 전에 가드를 둬라". 새 LLM 경로엔 **C3 감사 + C9 선분류 필수**.

## §6. propose → ratify 신뢰 루프
AI는 자기모델(페르소나 trait·코어 밝기/L·트리니티 도메인·북극성 문장)을 **직접 변경하지 않는다**. AI는 **제안 diff**(before→after, 근거 인용, 목표 L)를 방출하고 **사용자 승인 시에만 쓰기**가 일어나며 노드는 **L5(실행가능)**로 상승. 제안·승인 모두 `ai_audit_log`(C3)에 기록. **승인이 L5에 도달하는 유일한 경로.**

## §7. 용어 정본 매핑 (표시 라벨만 변경 · 내부 키/슬러그 동결)
> **내부 DB 키(core/work/relation/knowledge/records/taste)와 라우트 슬러그는 동결.** 표시 라벨·개념 문서만 바뀐다. 매핑은 `characters.ts · chat/personas.ts · graph/relatedness.ts::VILLAGE_LABEL`에 산다. **새 디렉토리(constellation/) 만들지 말 것 — 기존 3파일 확장.**

| 희망 용어 | 정본 개념 | 기존/배포 이름(키 동결) |
|---|---|---|
| 북극성 | 0th brain 철학의 히어로 노드(항상 최대 밝기) | Soul Core (Tier1, 키 `core`, 마스코트 SecondB) |
| 페르소나 | 사용자가 쓰는 역할/렌즈 | 5 Pattern Cores = 별자리(Growth/Bond/Wisdom/Narrative/Muse) |
| 별/stars | 자기이해 **차원**(렌즈) | 별1~7 — 코어 밝기를 먹이는 하위층 |
| 밝기 | 품질 신호 | L1~L5 가치 사다리(밝기의 유일한 의미) |
| 브레인 트리니티 | (레거시) | 별자리 개념 + /trinity 도메인(표시만), UI 라벨만 갱신 |

## §8. 하드 제약 (C-code · CI 가드 — 절대 위반 금지)
- **C1**: 모든 LLM 호출은 `gemini.ts` 단일 경유. · **C3**: 모든 호출 `ai_audit_log` INSERT. · **C9**: `classifyInput` 선행.
- **C10**: 14-17 self / <14 보호자. peer 미성년 실데이터 미수집.
- **임상어휘 하드밴드**: `clinically validated`/`임상적으로 검증된`/`diagnosis`/`treatment`/`cure`/`healing`/`therapy`/`정신건강`/`심리치료`/`심리상담`/`치유` 금지 → L4 라벨은 **"교차검증(cross-source agreement)"**. `check-forbidden-lexicon.ts` 실행. ('wisdom·knowledge·connected·actionable·별자리·페르소나·북극성'은 안전.)
- **anti-slop**: em dash·hex 노출·gradient·glassmorphism·pill(9999 radius) 금지. `check-emdash.ts`.
- **$0/mo 무료티어** · **4-tier 시각 위계(128/82/38/30, 링크 전부 cyan)** · **한 화면 = 한 메시지 + 한 그래픽**(디테일은 드릴다운, 노드 위 모달 금지, Back은 별자리 홈 한 곳).

---

## §9. 화면 구조 (42 라우트 → 별자리 홈 1 + 7별 + 5허브)
캐노니컬 셸 = **deep-space**(캐릭터 주도), gameboy 그래프는 같은 별자리 홈의 **스킨**(평행 내비 폐기). **신규 화면은 5개뿐**: 별3 보여지는 나(`/peer-review`)·별4 리듬(`/esm`)·별5 미래(`/future`)·트렌드제안(`/discover`)·점검리뷰(`/review`). 나머지는 유지(KEEP)/수정(MODIFY). 홈 `/` = 북극성(Soul Core 128px) + 7별(82px) + Pattern Link(cyan) + SecondB 단일 인사이트.

## §10. 채택된 결정 (D1~D12 — synthesis §6, 추천안 채택)
D1 **(a) 7별=자기이해 렌즈, 역할/액션/지식=목표트리 강등** · D2 별1=trait-state 도구·소울코어=종합 판독값 · D3 **경량 신뢰도 v1**(IRT post-XPRIZE) · D4 peer=**후순위 또는 성인 mock**(C10/PIPA) · D5 별6 Possible Selves·별7 Values/Strivings(XPRIZE엔 잠긴 별) · D6 드릴 정지=**L4 기본**(peer 없으면 self-only는 L3 상한) · D7 노드=북극성 · D8 소울코어 밝기=**가중평균+"모든 별 켜지면 북극성↑" 보너스**(결정론) · D9 품질 티어 **persist**(Supabase 마이그레이션) · D10 회상↔별1 모순은 **인사이트만**(스코어러 순수성) · D11 propose 트리거=**비서 열 때만**(+소울코어 넛지 1개) · D12 셸 컷오버=**F1-F4 수정 후 deep-space default**.
> **의존성**: D1이 뿌리(토폴로지가 밝기·화면맵·점수법을 정함). D4(peer)가 D6(정지레벨)을 제약. D9가 마이그레이션 강제. **먼저 D1·D2·D3·D4 고정 → 나머지 따라옴.**

## §11. XPRIZE 스코프 (마감 2026-08-17 06:00 KST · 솔로 · $0/mo)
전략: **11항목을 폭넓게 반쯤 짓지 말고, 한 축을 끝까지 깊게.** 최소 시연 루프(6노드): ①지금의나/도구(BFI-44, BUILT) → ②데이터 품질·밝기(build.ts 재사용, **NEW**) → ③Graphify/2nd brain(NavGraph, BUILT) → ④비서가 근거로 답(secondb+retrieve, BUILT) → ⑤다음 한 걸음 제안(propose-template, **NEW**) → ⑥`.iden` export(BUILT, 옵션). **신규는 ②밝기·⑤제안 두 개뿐**, 매 패스마다 별이 더 켜져 북극성이 밝아진다.

## §12. 작업 순서 (리팩토링 단계 — 4-AI lane 배정)
- **0단계 (DOCS-ONLY, 코드 0줄, 착수 게이트)**: 2nd-B `CONTEXT.md`에 **세 글로사리 블록 잠금** — (A)두뇌 0/1/2/3 다리맵 (B)L1~L5 사다리+상승조건 (C)용어 매핑. 그 다음 `worldview-naming.test.ts` 확장(사다리 정확히 5레벨·Soul Core=북극성·5코어=페르소나·금지어휘 0). `npm run check:lexicon` + `check-emdash.ts` 통과 후에만 UI 라벨/신규 화면 착수.
- **Phase A (값싼 점등)**: 별자리를 7렌즈+북극성 역할트리로 재구조 · ECR-S→별5 승격, ESM→별4 채점 연결(또는 제거) · **결정론적 밝기 함수**(§3 공식) 추가.
- **Phase B (핵심 방법론)**: 경량 신뢰도 정지규칙 · LLM/도구 분리+계약 테스트 · 새 LLM 경로 C3감사+C9선분류.
- **Phase C (최고가치 신규)**: 최소 시연 루프 닫기(밝기② + propose-ratify⑤) · 품질 티어 영속화 마이그레이션 · 별3 peer(성인 mock)/별6·7 잠긴 별.

**lane 배정(ROUTING 준수)**: 구현·머지=**Claude**(0단계 글로사리 락·밝기 함수·정지규칙·계약 테스트·마이그레이션) · UI/UX·라벨·신규 화면 디자인=**Codex**(용어 매핑 §7 라벨, anti-slop 준수) · 네이티브/에뮬 QA·SVG 렌더락/OOM·콜드스타트(전부 L1) 검수=**Antigravity** · 소비자·XPRIZE 심사 프레이밍·표현 민감도 advisory=**Grok**.

---
> **이 정본을 어길 것 같으면 멈추고 `type: consensus_request`로 합의(§14)**. 큰 틀(§1~§8) 변경 제안은 Simon 확인. 구현 디테일·단계 순서는 4-AI 합의로 진화.

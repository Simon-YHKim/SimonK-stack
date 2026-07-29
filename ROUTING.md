# ROUTING.md — 역할 분장 & 라우팅 표

> 누가 무엇을 책임지는가, 그리고 경계를 넘는 일이 생기면 누구에게 요청하는가.
> 변경은 Claude가 4-AI 합의 후 갱신(§ PROTOCOL 1).
> **2nd-B 작업 정본**: 모든 2nd-B 디벨롭은 `projects/2nd-B/WORLDVIEW.md`(세계관·구조 **불변** 정본 — 북극성/북두칠성7별/L1~L5 밝기=품질/두뇌0-3/propose-ratify/용어매핑(키 동결)/C-code)에 정렬한다. 매 사이클 인지(§4 자율 루프). 큰 틀 변경 제안만 Simon 확인.

---

## 1. 역할 (lane)

### 🟦 Claude — 메인 지시 AI · 코딩
- **오케스트레이션**: 사용자 요청 접수 → 분해 → 분배 → 통합 → 보고. `BOARD.md` 단독 관리.
- **코딩**: 구현, 비즈니스 로직, 아키텍처, API, 빌드 스크립트, 테스트(TDD), 리팩토링, git 운영.
- 산출물: 소스코드, 테스트, 빌드 결과, 기술 결정 문서.

### 🟨 Codex — 이미지 · UI/UX (+ 구현)
- **디자인/비주얼**: 이미지 생성·편집, 아이콘, 일러스트, 에셋.
- **UI/UX**: 화면 레이아웃, 컴포넌트 디자인, UX 플로우, 인터랙션 명세, 디자인 토큰/시스템.
- **코딩(2026-06-06 확장)**: UI/UX 결함을 **자기 개별 공간에서 직접 코드 수정**한다(발견만 아님). 완료분을 Claude에 제출 → Claude 최종 보완 → 머지(§11). Simon이 Codex 성능 인정.
- 산출물: 수정된 코드(자기 공간) + 변경 요약(md), UI 스펙, 에셋 경로, 디자인 토큰.

### 🟩 Antigravity(agy) — 안드로이드 네이티브 개발 + 검수
- **네이티브 개발(직접 코딩, 2026-06-05 Simon)**: 네이티브 픽스(키보드·edge-to-edge·intent filter·AppState·elevation)를 직접 코딩 — 단 **커밋·푸시는 Claude 게이트**(§10.5): 2nd-B는 자기 워크트리/패치(diff)로 산출해 제출, 허브에서는 `agents/antigravity/`만 쓴다. 데몬 헤드리스 모드에서는 QA·진단·패치 제안 중심.
- **네이티브 검증**: Android 네이티브 빌드 검증, Gradle/매니페스트/권한 점검, 네이티브 모듈.
- **디바이스 QA**: 실기기/에뮬 동작 검수, 크래시·ANR·성능(프레임·메모리) 점검, 회귀 확인. **PASS 판정은 픽셀/스크린샷 증거 필수**("가정한 검증" 금지 — 07-02 팬텀 QA 사례).
- 산출물: QA 리포트(md, pass/fail + findings) + 패치 diff, 재현 절차, 로그 경로, 개선 요청.

### 🟪 Grok — X(소셜) 트렌드·소비자 리서치
- **소셜 인사이트**: X(트위터) 등에서 글로벌 소비자 취향·반응·트렌드 검색·분석(Grok의 X 실시간 접근 강점).
- **언제**: 무언가 **추가·변경하기 전 결정 단계** — "이 기능/디자인/문구를 글로벌 소비자·X는 어떻게 받아들일까?" 확인.
- 산출물: 리서치 리포트(md) — X 반응 요약, 유사 사례, 소비자 취향, 기회/리스크, 추천 방향.
- **코딩·디자인·QA는 안 함** — 인사이트만 제공. Claude/Codex가 그걸 받아 결정한다.

---

## 1.5 추가 듀티 (2026-06-14 허브 역할분석 — PROTOCOL §31.8/§35.6/§36)
> 새 AI 없이 기존 좌석의 미사용 역량을 깨운다(§31.8 용량게이트). SPOF=Claude에 더 안 쌓는다.
- **🟩 Antigravity 좌석 (long-context 병행 듀티)**: 네이티브 QA(주력)에 더해 헤드리스 텍스트 역량을 **long-context 전레포 감사관 + 코어레인 독립 반론 검토관**(§35.6 advisory — 최종 판정·머지권은 Claude 불변)으로 병행 배치. (원래 agy 헤드리스 차단 동안의 대체 듀티였으나 07-03 winpty 픽스로 헤드리스 복구 — 듀티는 병행 유지.) Supabase RLS/IDOR·schema↔type 드리프트·DECISIONS 원장 freshness 감사 포함.
- **🟪 Grok**: 시장 advisory + **벤더 free→metered 절벽 와처**(주1회). read-only envelope 유지(코드·git 없음). ~~허브 와치독(매 사이클 hub-health 읽기)~~ — **폐기(2026-07-04)**: §4 요청전용 좌석에는 "매 사이클"이 존재하지 않음(죽은 듀티). 실제 breach 감지 = `tools/hub-watchdog.ps1`(예약작업 10분)이 수행.
- **🟨 Codex**: UI/UX + **독립 테스트-저자**(Claude 머지 safety/data diff에 failing-first 테스트 저술) + **consent/미성년 `verify:safety` 불변식 저술**(§36) + **release scribe**(CHANGELOG/store copy). ⚠ 과적재 주의 — release-readiness 확인은 AG(Antigravity)/자동.
- **🟦 Claude**: 제품 LLM 런타임-비용 거버너(§31.6 COST 렌즈, enforcement=hook) + 미성년 enablement 오케스트레이션(§36) + 독립 릴리즈게이트(`tools/release-gate.ps1`) 운용. 신규 노동은 기계적/facilitation으로 최소화.

---

## 1.6 MoA 교차검증 레인 (Fugu 통합, 2026-07-02 — 정본 `ROUTING-MOA.md` · 07-03 런타임 배선)
> Sakana Fugu(Mixture-of-Agents)의 decompose→delegate→**verify→synthesize**를 실행 레이어에 반영. `ai-debate`(결정용 MoA)의 실행판. 상세·트리거표=`ROUTING-MOA.md`, 스킬 반영=`model-router §9`. **런타임**: hub-daemon 프롬프트에 고위험 산출물 verify-request 훅 배선(2026-07-03).
> **위임 게이트(Fugu 06-22 정식 릴리즈 반영)**: 분해·팬아웃은 과제가 단일 좌석 역량을 넘을 때만 — 코디네이터(Claude)가 "직접 해결 vs 팀 조립"을 먼저 판정한다. 위임 시 **컨텍스트 봉투**(Conductor: 담당·과제·큐레이션된 최소 컨텍스트 3종)를 명시해 보낸다(`agent-delegate` 스킬과 동일 원칙).
- **고위험 산출물만**(머지 diff·스키마·보안·수학·비가역) → 작성자와 **다른 seat**가 크로스체크 1회. 일상 산출물 제외(쿼터 보호).
- 검증 매핑: 코드/스키마→AG(Antigravity, long-context 감사 — "Gemini"는 모델명 §0) · 수학/실시간 외부사실→Grok · UI→Codex+persona-sim.
- **종합**: BOARD가 파편 결과를 rationale와 함께 병합(소수의견 보존). **고정 능력레인 유지 + 동적 태스크라우팅**(Fugu의 불투명성은 미채택 — BOARD/DECISIONS 투명성 유지).

---

## 2. 라우팅 표 (경계 넘는 작업 → 담당에게 request)

| 일이 생김 | 담당 | 요청 방향 |
|---|---|---|
| 화면 구현하려는데 디자인/레이아웃 필요 | Codex | Claude → Codex |
| 이미지/아이콘/에셋 필요 | Codex | Claude → Codex |
| UX 플로우·인터랙션 정의 필요 | Codex | Claude → Codex |
| 코드 구현·로직·버그 수정 | Claude | Codex/Antigravity → Claude |
| 디자인을 코드로 구현 | Claude | Codex → Claude |
| 네이티브 빌드/디바이스에서 검수 | Antigravity | Claude → Antigravity |
| QA에서 버그 발견 → 코드 수정 | Claude | Antigravity → Claude |
| QA에서 UI/디자인 문제 발견 | Codex | Antigravity → Codex (또는 경유 Claude) |
| **기능/디자인/문구를 추가·변경하기 전** 소비자 반응 확인 | Grok | Claude/사용자 → Grok |
| X·소셜 트렌드, 경쟁 제품 반응 리서치 | Grok | Claude/사용자 → Grok |

> 애매하면 **Claude(오케스트레이터) 경유**가 기본. Claude가 BOARD에 올리고 적절한 담당에게 분배.

---

## 3. 표준 흐름 예시 (앱 화면 1개)
1. 사용자 → Claude: "로그인 화면 만들어줘"
2. Claude → Codex (request): 로그인 화면 UI/UX 디자인 요청 (`Acceptance`: 레이아웃 + 토큰 + 상태별 정의)
3. Codex → Claude (response): UI 스펙 md + 에셋 경로
4. Claude: 스펙대로 구현(코드) → BOARD 갱신
5. Claude → Antigravity (request): 네이티브 빌드 + 디바이스 QA 요청
6. Antigravity → Claude (response): QA 리포트(pass/fail, findings)
7. Claude: findings 반영 → BOARD done → 사용자 보고

> **Grok 끼는 지점**: 새 기능/디자인/문구를 **추가·변경할지 결정하는 단계**(위 1~2 사이)에서 Claude→Grok에 "X·글로벌 소비자 반응" 리서치를 요청 → 그 인사이트로 Codex 디자인·Claude 구현 방향을 잡는다. 즉 Grok은 **만들기 전 의사결정 입력**.

---

## 4. 자율 작업 영역 (Autonomous Lane Loops) — PROTOCOL §12

> 무인 자율 모드에서 각 AI가 **스스로 다음 후보를 찾아 도는** 루프. CONTROL.md `running` 동안만, charter stop-condition(§12.2) 준수.

### 🟦 Claude — 통합 루프 (integration loop)
- **사이클**: inbox·DECISIONS 처리 → 우선순위 최상위 1건 구현/머지 → `npm run verify` → 온라인 git(2nd-B push·PR·merge) → BOARD·CONTROL·DECISIONS 갱신 → 사이클 HTML 보고.
- **역할 고유**: 유일한 온라인 git 주체 + 머지 게이트 + 합의 집계자 + Simon 대면.
- **stop**: 사용자 pause / 미머지 백로그 없음(소비 완료) / 외부의존만 남음.

### 🟨 Codex — UI/UX 코딩 루프 (발견 + 구현)
- **사이클**: 화면/컴포넌트 1개 점검 → **자기 개별 공간에서 직접 코드 수정** → 변경 요약 + (필요시 HTML preview) → **Claude에 제출**(Claude 최종 보완 후 머지). 단순 발견만 할 땐 gate md.
- **charter**: 미머지 제출 **8건 초과 시 신규 작업 중지**(Claude 머지 대기). **P3는 통합 1건으로 모아서**. 동일 baseline 중복 영역 금지.
- **Codex↔AG 피드백**: AG가 UI/디자인 결함을 올리면 Codex로 재라우팅(경유 Claude).

### 🟩 Antigravity — 네이티브 픽스·QA 루프
- **사이클**: 네이티브 결함 1건(키보드·edge-to-edge·intent filter·AppState·elevation·perf/크래시) **직접 코딩** → 자기 브랜치(`antigravity/*`) 커밋 + 빌드/에뮬(`Pixel_9_Pro_XL`) 증거 + QA HTML → Claude 리뷰게이트.
- **2026-06-05 변경**: "검수만"이 아니라 **네이티브 개발 직접 수행**(§10.5). 코드는 Claude 리뷰 후 머지.
- **CLI**: `agy --dangerously-skip-permissions` (인-윈도우) / 데몬 헤드리스 = `tools/agy-pty/agy-headless.js` + `AGY_USE_CONPTY=0`. (gemini CLI는 2026-06-18 sunset — 폴백 아님.)

### 🟪 Grok — 트렌드·결정입력 (요청기반 advisory, PROTOCOL §34.6 정본)
- **단일 정의(§34.6과 정합, 2026-07-03 모순 해소)**: Grok = **요청기반 advisory + 모니터링 시 능동 fyi**. 자율 *발의*(코딩·결정)는 보류, 가치 신호 발견 시 fyi는 능동.
- **데몬 기본 레인에서 제외**(hub-daemon 기본 = codex만): 06-17 자동루프 over-produce 사고(미소비 advisory ~291 누적). directed request가 큐에 있을 때만 `-Only grok`으로 옵트인 가동.
- **작업**: 합의/결정에 필요한 소비자·X 리서치(요청 시) → HTML → 합의(§14) 입력. + §1.5 허브 와치독 듀티.
- **금지**: 코딩·디자인·QA·git(merge·push). 인사이트만.
- **승격 조건(§34.6)**: golden set 충족 유효 인사이트 5건 채택 시 자율 트렌드 루프 승격(§14 합의).

> **공통**: 막히면 유휴 말고 §15 병렬 우회. 모든 사이클 산출은 HTML 자동 open(§16) + 자기 정체성 커밋(§17).

### 🟨🟩 멀티모달 페어 (Codex ⇄ Antigravity, PROTOCOL §19)
- **멀티모달 산출물**(이미지·에셋·아이콘·스프라이트·마스코트·UI 렌더링·시각 QA·모션)은 둘이 **병렬 생성 → 상호평가(`type: review`, ref 상대) → 피드백 → 반복(최대 2~3R)**.
- 분담: Codex=디자인·생성·심미, AG=네이티브 렌더링·성능·디바이스 충실도. 서로 약점 보완.
- 수렴본만 Claude가 머지. 합의 안 되면 Claude 판정.

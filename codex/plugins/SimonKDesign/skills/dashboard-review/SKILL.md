---
name: dashboard-review
version: 0.1.0
description: Use when reviewing, building, or QA-ing any data dashboard, admin panel, table-heavy screen, chart view, or data-dense UI — triggers "대시보드 리뷰", "대시보드 점검", "dashboard 검수", "데이터 UI 리뷰", "테이블 UI", "차트 배치", "_hubdash 점검", "관리자 화면", "dashboard review", "data table UI", "chart layout", "admin panel review", or /dashboard-review. Reviews against the 3 amateur "tells" (data doesn't drive the form · no progressive disclosure · ignored invisible UI) plus the empty/loading/error-state gap, and produces a prioritized fix list (file → element → before→after). Complements design-review (general visual QA) — this one is specialized for data-fed surfaces. Different from design-system-keeper (tokens) and simon-design-first (intake).
---

# dashboard-review — 데이터 대시보드 검수

> "Designing a dashboard isn't hard, but **orchestrating** one is." 데이터를 나열하는 것과, 데이터가 UI 형태를 **결정하게** 하는 것은 다르다. 초보가 만든 대시보드를 즉시 드러내는 3가지 tell을 잡고 고친다.

## 언제 쓰나
`_hubdash`(허브 상태), 우리가 만드는 HTML 리포트, 2nd-B의 데이터뷰(constellation/graph·persona 패널), usage/health 모니터 등 **데이터가 화면을 채우는 모든 표면**. 일반 시각 QA는 `design-review`, 이건 데이터 표면 전용.

## 3대 결함 · tell · 고침

### 결함 1 — 데이터가 폼을 이끌지 않음
**tell**: 무엇이든 일단 평범한 테이블에 붓는다("nothing driving the form").
**고침**:
- 값이 고정 집합(상태·부서·타입) → **chip**. 자유 텍스트 → 그대로.
- **숫자는 우측 정렬**(자릿수 place value 정렬) + 단위·소수 자리 통일.
- 긴 텍스트 **truncate**(다른 열에 숨쉴 공간), 비활성 행은 **shade out**.
- **색은 데이터에서** 나온다 — red=urgent, avatar=누가 했는지(이름 읽기보다 빠름). 장식용 색 금지.
- **시간 차원 데이터는 timeline/chart**로 — 타임스탬프 열을 눈으로 훑게 하지 말 것. 요약은 chart로 roll-up.

### 결함 2 — 점진적 공개(progressive disclosure) 부재
**tell**: 모든 액션이 항상 박혀 있음 / 로그인 즉시 6-bullet 모달로 제품 전체 설명(dismiss하면 잊힘).
**고침** — **explicitness 스펙트럼**(전역 상시 버튼=높음 → hover 복사아이콘=낮음):
- **primary action만 상시 노출**(예: 검색창 최상단). 2차 액션(공유·삭제)은 **hover + tooltip** 또는 popover(페이지 이동 없이).
- 온보딩 = **시퀀싱**: 툴팁 1개 → 완료 후 다음 → 코너 체크리스트. 한 번에 다 보여주지 않음(기능을 숨기는 게 아니라 **순서를 매기는 것**).

### 결함 3 — 보이지 않는 UI 무시
**tell**: 초보 대시보드엔 **툴팁이 거의 없음**(unequivocally missing). hover 상태·복사칩·코멘트 표시·drawer/modal 숨은 상태 부재.
**고침**: "UI는 보이는 것만큼 안 보이는 것"이다. 아이콘/모호한 라벨엔 **tooltip** 필수(사용자가 다 이해한다고 가정 금지). 셀 hover 복사칩, 코멘트 삼각표시, 숨은 액션·상태를 설계. 새 기능이 꼭 전용 페이지를 요구하지 않는다.

### 결함 4(우리 확장) — 빈/로딩/에러 상태
데이터 표면인데 **empty("아직 노드 없음")·loading·error(데이터소스 불통)** 상태가 없으면 미완성. `_hubdash`의 data.json/health-loop 실패, 2nd-B 그래프의 무데이터가 대표 위험.

## 검수 체크리스트 (8)
1. 데이터가 폼을 이끄는가? (categorical→chip, time→timeline/chart)
2. 숫자 우측정렬 + 단위·소수 통일, 긴 텍스트 truncate
3. primary action만 상시, 2차는 hover/popover + tooltip
4. 온보딩은 시퀀싱(툴팁→체크리스트), 모달 덤프 아님
5. 아이콘·모호 라벨에 tooltip
6. 숨은 상태(복사칩·코멘트·hover) 설계됨
7. 색은 데이터 의미 인코딩(장식 아님)
8. empty·loading·error 상태 존재

## 우리 표면 적용 노트
- **_hubdash**: 원시 data.json 그리드 → chip/timeline화, latency 우측정렬, 상태색 tooltip, 데이터/health 실패 시 에러상태.
- **HTML 리포트**: 복사버튼은 hover로, primary action 강조, 숫자 포맷. (이 스킬로 우리 리포트도 dogfooding.)
- **2nd-B**: 그래프는 이미 data-drives-form ✓ — 위험은 persona 패널 첫실행 과부하(툴팁 시퀀싱) + 그래프 empty/loading 상태.

## 산출
파일 → 요소 → before→after의 우선순위 수정 목록. 심각도 = 빈도 × 영향. 자동 수정은 하지 않고 제안(적용은 사용자 확인). 토큰·스펙 정본은 `design-system-keeper`와 연동.

# Retention Report — <YYYY-MM-DD>

- 담당: <name>
- 데이터 소스: <PostHog | SQL(events) | 기타>
- 기간 단위: <day | week | month>
- 코호트 기준: <signup | behavioral(첫 행동: ...)>
- 리텐션 정의: <n-day | unbounded | bracket>  ← **한 리포트엔 하나만**
- Return 이벤트: <session_start | app_open | ...>

## 1. 코호트 리텐션 커브

`retention_calc.py curve` 출력(삼각행렬) 붙여넣기. NA = 미성숙(right-censored) 셀, 비교 제외.

| cohort | size | P0 | P1 | P2 | P3 | ... |
|---|---|---|---|---|---|---|
| | | 100% | | | | |

- 초기 급락(P0→P1) 폭: <%> → 원인 추정: <온보딩/활성화 | 기대 불일치 | ...>
- Retention floor (마지막 N개 성숙 기간 평균): <%>
- Floor 해석: <0 초과 = 코어 존재(PMF+) | 0 수렴 = PMF 미달 신호>
- 코호트 추세 (oldest→newest, 동일 P 기준): <개선 / 평탄 / 악화> <±%>

## 2. 퍼널 드롭오프

| 단계 | 진입 | 통과 | 통과율 |
|---|---|---|---|
| 가입 | | | 100% |
| 활성화 (aha) | | | |
| 반복 사용 | | | |
| 결제 | | | |

- 최대 이탈 단계(bottleneck): <단계명> (<통과율>)
- 리텐션 초기 급락과 동일 원인 여부: <예/아니오 — 근거>

## 3. RFM 세그먼트

`retention_calc.py rfm` 출력 붙여넣기.

| 세그먼트 | 인원 | 비중 | 다음 행동 |
|---|---|---|---|
| Champions | | | 리퍼럴 요청 |
| Loyal | | | 업셀/구독 |
| At-risk | | | 윈백 캠페인 |
| Hibernating | | | 재활성 1회 후 손절 |
| New | | | 온보딩 |

## 4. 이탈 선행지표 (상관·가설 — 결론 아님)

`retention_calc.py drivers` 출력 붙여넣기.

| 행동(behavior) | retained 평균 | churned 평균 | lift | r |
|---|---|---|---|---|
| | | | | |

- Top lever 후보: <behavior> — 가설: "<첫 N기간에 X 하면 리텐션 ↑>"
- 검증 경로: `experiment-analyzer` 로 A/B 설계 → 판정

## 5. 함정 점검

| 함정 | 상태 | 메모 |
|---|---|---|
| 정의 단일 (n-day/bracket 혼동 없음) | ☐ | |
| 누적(cumulative) 리텐션 아님 | ☐ | |
| 미성숙 코호트 NA 처리 | ☐ | |
| 코호트 크기 충분 (>=100) | ☐ | |
| 이탈 유저 행동도 분석 (생존편향 회피) | ☐ | |
| 4개 이상 코호트로 추세 확인 | ☐ | |
| 선행지표 = 가설 라벨 (인과 단정 X) | ☐ | |

## 6. 다음 실험 백로그 (ICE 우선순위)

ICE = Impact × Confidence × Ease (각 1~10). 점수 높은 순.

| 실험 가설 | 타깃 지점 | Impact | Confidence | Ease | ICE | 검증 skill |
|---|---|---|---|---|---|---|
| | <P0급락 / bottleneck / At-risk / lever> | | | | | experiment-analyzer |
| | | | | | | |

상위 1~2개만 즉시 착수. 나머지는 백로그 유지.

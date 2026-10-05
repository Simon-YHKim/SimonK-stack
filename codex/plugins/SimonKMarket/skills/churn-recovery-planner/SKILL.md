---
name: churn-recovery-planner
description: >
  Use when defending against involuntary churn and revenue leakage. 트리거 "이탈 방어", "dunning", "결제 실패 회복", "구독 해지 방어", "윈백", "카드 만료 대응", "involuntary churn", "payment recovery", "cancel flow", "save offer", 또는 /churn-recovery-planner. Produces a payment-retention recovery plan: 스마트 dunning 리트라이 스케줄 → 카드 만료 프리덩닝 → 취소 흐름 save-offer 분기 → 윈백 시퀀스 → 회복률 KPI. 결제·세금 규제는 global-payment-planner, 발송 배관은 lifecycle-campaign-designer, 매출 시뮬레이션은 revenue-scenario-tester로 위임.
allowed-tools: Read, Write, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# churn-recovery-planner

비자발적 이탈(결제 실패·카드 만료·갱신 누락)로 새어나가는 매출을 방어하는 skill.

> 구독 매출이 줄어드는 가장 큰 이유는 "유저가 떠나서"가 아니라 "결제가 조용히 실패해서"인 경우가 많다.
> 카드 한도·만료·발급사 거절은 유저가 떠나려던 게 아니다. 이 skill은 그 매출을 되살린다.

## 자발적 vs 비자발적 이탈 (이 skill의 초점)

| 구분 | 원인 | 이 skill 대응 |
|---|---|---|
| **비자발적(involuntary)** | 결제 실패, 카드 만료/한도/거절, 갱신 누락 | dunning 리트라이 + 프리덩닝 + 결제수단 갱신 유도 (1~3단계) |
| **자발적(voluntary)** | 유저가 직접 취소 클릭 | 취소 흐름 save-offer 분기 (4단계) |
| **둘 다 실패한 후** | 이미 비활성/만료됨 | 윈백 시퀀스 (5단계) |

비자발적 이탈은 전체 구독 이탈의 상당 부분을 차지하면서도 가장 회복하기 쉽다 — 유저가 떠날 의사가 없었기 때문이다. 여기서 가장 큰 ROI가 나온다.

## 경계 (위임 규칙)

| 이 skill이 하는 것 | 위임 |
|---|---|
| dunning 스케줄·취소분기·윈백 시퀀스 설계 | PG/결제 SDK 연동, 카드 갱신 UI 구현 → `payment-integrator` |
| 회복 메시지의 "언제·무엇을" 설계 | 이메일/푸시/인앱 발송 배관 → `lifecycle-campaign-designer` |
| 회복률·구제 매출 KPI 정의 | dunning 시나리오 통합 테스트 → `revenue-scenario-tester` |
| 결제 실패 후 가격/플랜 다운셀 설계 | 가격 구조·플랜 설계 → `monetization-planner` |
| — | 국가별 환불·자동갱신 규제, 세금 → `global-payment-planner` |

발송 배관이 없으면 `lifecycle-campaign-designer`를 선행/병행한다. 결제 webhook이 없으면 `payment-integrator`를 선행한다.

## 진단 먼저 (AskUserQuestion)

설계 전 확인. 답이 없으면 추측하지 말고 묻는다.

1. **결제 인프라** — Stripe / PortOne(아임포트) / RevenueCat / Paddle / 앱스토어 IAP 중 무엇인가? (리트라이·webhook 능력이 다름)
2. **결제 주기** — 월간 / 연간 / 혼합? (연간은 실패 1건의 금액 충격이 커서 리트라이 윈도가 길어야 함)
3. **결제 수단** — 카드 위주 / 간편결제(카카오·네이버) / 자동이체? (카드만 만료·프리덩닝 대상)
4. **현재 누수 규모** — 결제 실패율, 실패 후 자동복구율 대략치. (없으면 "측정부터" 권고)
5. **발송 채널** — 이메일 동의율 / 푸시 권한 / 인앱 노출 가능 여부. (회복 메시지 도달 상한)

스토어 IAP(앱스토어·구글플레이)는 리트라이를 플랫폼이 직접 관장한다 — 이 경우 dunning은 플랫폼의 Billing Grace Period 설정 + 인앱 안내로 한정됨을 명시한다.

## 1단계 — 스마트 dunning 리트라이 스케줄

결제 실패 후 무작정 매일 재시도하면 발급사가 차단(hard decline)한다. 실패 코드별로 전략을 나눈다.

### 실패 코드 분류

| 코드 유형 | 예시 | 재시도 가치 | 전략 |
|---|---|---|---|
| **soft decline** | 잔액 부족, 일시 한도 초과, 발급사 일시 거절 | 높음 | 시간차 리트라이 (급여일·요일 고려) |
| **hard decline** | 카드 분실/도난, 계정 폐쇄, 사기 의심 | 없음 | 즉시 리트라이 중단, 결제수단 교체만 유도 |
| **expired card** | 카드 만료 | 중간 | 리트라이 무의미 → 갱신 유도 (프리덩닝이 더 중요, 2단계) |
| **do not honor / generic** | 발급사 일반 거절 | 중간 | 1~2회만 시간차 재시도 후 갱신 유도 |

> hard decline에 리트라이를 반복하면 PG 계정 위험도(decline rate)가 올라가 정상 결제까지 막힌다. 코드 분기는 선택이 아니라 필수다.

### 권장 리트라이 윈도 (soft decline 기준)

월간 구독의 기본 골격. 실제 간격은 PG 데이터로 조정한다.

| 시도 | 시점 | 채널 동반 메시지 | 비고 |
|---|---|---|---|
| 1차(원결제 실패) | D0 | 인앱 + 이메일: "결제가 처리되지 않았어요" | 부드러운 톤, 비난 금지 |
| 2차 | D+2 | (메시지 없이 조용히 재시도) | 주말 회피, 평일 오전 |
| 3차 | D+4 | 이메일: 결제수단 갱신 1-클릭 링크 | CTA 단일화 |
| 4차 | D+6 | 푸시 + 이메일: "곧 서비스가 중단돼요" | grace period 고지 |
| 최종 | D+7~14 | 이메일: 최종 안내 + 다운셀 옵션 | 실패 시 비활성 전이 |

조정 규칙:
- **연간 플랜**: 금액이 크므로 윈도를 D+21까지 늘리고 사람이 직접 연락(고가치 한정)할 가치가 있다.
- **급여일 정렬**: 잔액 부족 실패는 월말·급여일 직후 재시도 성공률이 높다. 가능하면 다음 급여 주기에 맞춰 1회 더.
- **시간대**: 발급사 점검·야간 거절을 피해 평일 오전(KST) 재시도.
- `scripts/dunning-schedule.ts`로 입력(주기·실패코드유형·최대시도)에서 결정론적 스케줄 JSON을 생성한다.

## 2단계 — 카드 만료 프리덩닝 (실패 전 예방)

만료는 달력으로 예측 가능하다. 실패하기 **전에** 갱신받는 게 회복보다 압도적으로 싸다.

- 만료월 **D-30 / D-7 / D-1** 3회 리마인드 (over-messaging 금지, 3회 상한).
- 메시지: "○○카드(끝자리 1234)가 다음 달 만료돼요. 지금 갱신하면 서비스가 끊기지 않아요." — 카드 식별은 마스킹된 끝자리만.
- **Account Updater 우선**: Stripe Card Account Updater / 카드사 자동 갱신(VAU/ABU)이 가능하면 그걸 먼저 켠다 — 유저 행동 없이 자동 갱신되는 비율이 가장 높다. 메시지는 그게 실패한 카드만 대상.
- 프리덩닝으로 막은 건 1단계 dunning에 진입하지 않으므로, 두 지표를 분리 측정한다(예방 vs 회복).

## 3단계 — 취소 흐름 save-offer 분기 (자발적 이탈 방어)

유저가 "구독 취소"를 누른 순간이 마지막 대화 기회다. 이유를 먼저 묻고, 이유별로 다른 제안을 한다. 모두에게 할인을 뿌리면 마진만 깎이고 "취소하면 할인"을 학습시킨다.

| 취소 이유 | save-offer 분기 | 하지 말 것 |
|---|---|---|
| 너무 비쌈 | 다운셀(저가 플랜) / 연간 전환 할인 / 일시정지(pause) | 무조건 N% 할인 |
| 안 씀 / 가치 못 느낌 | 일시정지 제안 + 핵심 가치 재안내 | 할인 (가치 문제는 가격으로 안 풀림) |
| 기능 부족 | 로드맵 안내 + 대체 기능 가이드 + (해당 시) 상위 플랜 체험 | 즉시 할인 |
| 버그·불만 | 지원 연결 우선, 문제 해결 후 보상 | 할인으로 무마 |
| 일시적 필요 종료 | **일시정지(pause)**를 기본 제안 — 완전 해지보다 복귀 쉬움 | 강한 만류 |
| 기타/응답 안 함 | 가벼운 가치 리마인드 1회 | 집요한 재확인 |

설계 원칙:
- **이유 수집 먼저, 제안은 그 다음.** 한 화면에 이유 선택 → 분기.
- **pause를 1순위 옵션으로.** 일시정지는 해지율을 낮추고 복귀율을 높이는 가장 저렴한 수단.
- 다크패턴 금지 — 취소 버튼을 숨기거나 단계를 늘려 막지 않는다(아래 컴플라이언스).
- save-offer는 **유저당 빈도 제한** (예: 6개월 1회) — 반복 수령 학습 방지.

## 4단계 — 윈백 시퀀스 (이미 떠난 후)

dunning·취소방어가 모두 실패해 비활성/만료된 유저 대상. lifecycle-campaign-designer의 윈백과 같은 골격이되, 여기서는 **결제 복구**가 목표다.

- ① 가치 리마인드(혜택 없이) → ② 그간의 개선/신기능 → ③ 조건부 복귀 혜택(마지막, 빈도 제한) → 무반응 시 발송 빈도 다운그레이드 후 종료.
- 비자발적 이탈자(결제만 실패한 채 떠난 유저)는 **자발적 해지자보다 윈백 성공률이 높다** — 떠날 의사가 없었으므로 우선순위 1.
- 시퀀스 카피 골격은 `templates/recovery-sequences.md` 참조. 발송은 `lifecycle-campaign-designer`로 위임.

## 5단계 — 회복률 KPI & 측정

회복은 "보낸 메시지 수"가 아니라 **구제된 매출(recovered MRR)**로 측정한다.

| 지표 | 정의 | 왜 중요한가 |
|---|---|---|
| **결제 실패율** | 실패 결제 / 전체 갱신 시도 | 누수의 입구 크기 |
| **dunning 회복률** | 회복된 구독 / dunning 진입 구독 | 1단계 효과 |
| **프리덩닝 예방율** | 만료 전 갱신 / 만료 예정 카드 | 2단계 효과(예방) |
| **취소 save율** | 취소 시도 후 유지 / 취소 화면 진입 | 3단계 효과 |
| **윈백율** | 복귀 결제 / 윈백 대상 | 4단계 효과 |
| **구제 매출(recovered MRR)** | 회복된 구독의 월 매출 합 | 최종 비즈니스 임팩트 |
| **involuntary churn rate** | 비자발 이탈 구독 / 전체 활성 | 방어 후 줄었는가 |

- `scripts/recovery-kpi.ts`로 단계별 카운트에서 회복률·구제 MRR·funnel 누수를 계산한다.
- save-offer/윈백 혜택은 **holdout 대조군**으로 incremental(순증) 효과를 봐야 한다 — "어차피 남았을 유저"에게 할인을 준 건 손실이다. holdout lift 계산은 `lifecycle-campaign-designer`의 `holdout-lift.ts` 재사용.

## 산출물

1. 실패코드 분류표 + dunning 리트라이 스케줄 (`scripts/dunning-schedule.ts` 생성 JSON)
2. 카드 만료 프리덩닝 플랜 (D-30/-7/-1 + Account Updater 정책)
3. 취소 흐름 이유별 save-offer 분기 매트릭스
4. 윈백 시퀀스 3단계 골격 (`templates/recovery-sequences.md`)
5. 회복 KPI 정의 + 측정 설계 (`scripts/recovery-kpi.ts`)

## 검증 체크리스트

- [ ] 실패 코드를 soft/hard/expired로 분기 — hard decline에 리트라이 반복하지 않음
- [ ] dunning 최대 시도 횟수·grace period가 명시됨 (무한 재시도 금지)
- [ ] 카드 만료 프리덩닝이 dunning보다 **먼저** 작동 (예방 우선)
- [ ] Account Updater 자동 갱신을 우선 검토 (유저 무행동 회복)
- [ ] 취소 흐름이 이유 수집 → 분기 구조, pause가 1순위 옵션
- [ ] save-offer 빈도 제한 적용 (반복 수령 학습 방지)
- [ ] 회복 효과를 holdout 대조군으로 incremental 측정
- [ ] 마케팅성 회복 메시지는 수신 동의 확인 (거래성 결제실패 고지는 별도)
- [ ] 다크패턴 없음 — 취소 버튼 은닉/단계 부풀리기 금지
- [ ] 스토어 IAP는 플랫폼 grace period에 의존함을 명시 (자체 리트라이 불가)

## 컴플라이언스

- **거래성 vs 마케팅성**: 결제 실패·만료·서비스 중단 고지는 거래성 메시지(동의 불필요)지만, 윈백·할인 제안은 마케팅성(사전 opt-in 필요) — 정보통신망법. 둘을 한 메시지에 섞지 말 것.
- **자동갱신 고지**: 갱신 D-N일 전 고지 의무(전자상거래법/스토어 정책). dunning과 별개로 유지.
- **취소 다크패턴 금지**: 미국 FTC click-to-cancel·EU·한국 모두 "가입만큼 쉬운 해지"를 요구하는 추세. save-offer는 1단계로 제시하되 취소 자체를 막거나 숨기지 않는다.
- **카드 정보 표시**: 메시지에 카드 끝자리/만료월 외 노출 금지. 전체 번호·PAN 절대 표기·로깅 금지(PCI).
- **미성년·14~17세**: 결제·갱신 관련 메시지는 보호자 동의/연령 정책 준수(프로젝트 C10류).

## 사용 예시

```
나: "구독 결제 실패가 자꾸 나는데 이탈 방어 좀 짜줘"

Claude: [churn-recovery-planner 발동]
  진단(AskUserQuestion): Stripe / 월간 / 카드 위주 / 실패율 미측정 / 이메일+인앱
  → 1단계: soft decline 리트라이 D0·D2·D4·D6·D7 스케줄 (dunning-schedule.ts 생성)
  → 2단계: 카드 만료 D-30/-7/-1 프리덩닝 + Stripe Account Updater 우선
  → 3단계: 취소 흐름 이유별 분기 (비쌈→다운셀/pause, 안씀→pause)
  → 4단계: 윈백 3단계 (비자발 이탈자 우선)
  → 5단계: dunning 회복률·구제 MRR KPI + holdout 측정
  발송 배관은 lifecycle-campaign-designer로, Stripe 리트라이 설정은 payment-integrator로 위임 안내.
```

## Related Skills

- `revenue-scenario-tester` — dunning/구독 상태머신을 시나리오로 적대적 검증(Subscription Agent). 이 skill의 설계를 테스트.
- `payment-integrator` — PG/구독 SDK 연동, Stripe Smart Retries·Account Updater·취소 UI 구현. 선행 또는 위임.
- `lifecycle-campaign-designer` — 회복 메시지의 발송 배관(이메일/푸시/인앱) + 윈백 시퀀스 + holdout-lift.ts.
- `monetization-planner` — 결제 실패·취소 시 제안할 다운셀 플랜·가격 구조.
- `global-payment-planner` — 국가별 환불·자동갱신 규제, 세금 처리.

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.

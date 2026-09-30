# Grok Bot 사용량

> 갱신 26.09.30 · 공개 문서·포럼 원문으로 확인한 내용. 로그인이 필요한 화면은 열지 않았다.

## 어디에 무엇이 나오나 — 미터가 셋이다

| 화면 | 보이는 것 | 위젯에서 |
|---|---|---|
| **Grok Bot 앱** → Settings → Usage & Billing (계정 메뉴에도 요약) | **Weekly usage**(주간 포함 사용률 %, 리셋까지 카운트다운), **On-demand usage**("Billed through Cursor"), **On-demand monthly limit** | Grok Bot 카드에 **직접 입력**(유일한 출처) |
| **Cursor 대시보드 Spending** (`cursor.com/dashboard/spending`) | Cursor 플랜 두 풀(Cursor Models / Other Models)의 사용량·남은 한도·**On-demand 요금**·결제주기 리셋일, **Monthly Limit** 설정 | On-demand 사용액·월 한도를 옮겨 적는 곳. **Grok Bot 주간 %는 여기 없다**(Cursor 직원: "you can see the Grok Bot meter inside the Grok Bot app") |
| **grok.com** → Settings → Usage | SuperGrok **공용 풀** 사용률, 제품별 %(API·Build·Chat·Imagine·Voice), 주간 리셋 날짜·시각, Extra Usage Credits | 위젯의 **Grok 카드**(Grok Build CLI, 자동 조회)가 이 풀이다. Grok Bot은 목록에 없다 |

- Grok Bot 사용량은 **Cursor 계정에서 계량**된다. "metered on your Cursor account, not on Grok or X … does not create a second meter on Grok or X"(Cursor Grok Bot 플랜 문서).
- SuperGrok 연동과 Cursor 플랜은 **합산되지 않는다.** 둘 중 사용량이 많은 쪽을 쓴다(xAI Grok Bot FAQ: "Grok Bot uses whichever has more usage").
- 주간 포함량을 다 쓰면 **주간 풀 → 추천·프로모 크레딧 → 유료 On-demand** 순으로 차감된다(Cursor 직원, 26.09.01). On-demand는 Spending의 Monthly Limit에 합산되고, 꺼져 있으면 "reached your Grok Bot usage limit" 후 주간 리셋 때 재개된다.
- 리셋은 "resets weekly"만 문서화돼 있고 요일·시각 규칙은 **미확인**이다. 포럼상 계정마다 카운트다운이 따로 돌고(예: "left 4 days"), 08.26·09.01의 전체 일괄 리셋 뒤에도 카운트다운은 그대로 이어졌다.
- 개인 계정이 이 값을 프로그램으로 읽는 **공식 경로는 없다**: Cursor 개인 사용량 API·CLI 없음(직원, 26.05.19), Admin/Analytics API는 Enterprise 팀 전용이고 Grok Bot 주간 %가 없음, Cursor CLI `/usage`는 Cursor 플랜 기준. 대시보드 스크래핑은 약관 §1.5(viii) 위반이다.

## 위젯 카드 사용법

위젯의 **사용량 현황 → Grok Bot** 카드에서:

1. **주간 사용률(%)** — Grok Bot 앱의 Weekly usage 값을 입력하고 **기록**. (필수)
2. **리셋·On-demand (선택)** 을 펼치면:
   - **리셋까지** — 앱의 카운트다운을 "N일 N시간"으로. 카드와 작업 표시줄에 남은 시간이 나오고, 그 시각이 지나면 옛 사용률을 숨기고 새 값 입력을 안내한다. 사용률만 다시 기록하면 아직 지나지 않은 리셋 시각은 유지된다.
   - **On-demand 사용액 / 월 한도($)** — Cursor Spending 또는 앱의 On-demand 행 값. 빈칸이면 지운다.
3. 사용률이 **100%** 면 "주간 포함량 소진 · 이후 사용은 크레딧, 그다음 On-demand로 청구될 수 있음"을 표시한다(작업 표시줄 값은 경고색).

표시 규칙: 기록 후 24시간이 지나면 오래된 값, 7일 뒤에는 숫자를 숨긴다. 위젯의 새로고침 버튼은 수동 값을 갱신하지 않는다. **Cursor Spending 열기** 링크는 `cursor.com/dashboard/spending`을 연다.

## 하지 않는 것

자동 동기화, Grok CLI(SuperGrok 풀) 수치를 Grok Bot 값으로 재사용, 내부 RPC·화면 스크래핑. Cursor가 개인 주간 사용량 인터페이스를 공식 제공하면 수동 입력을 그 조회로 바꾼다(DECISIONS 26.09.30 15:37).

## 미확인

Grok Bot 리셋 요일·시각·타임존 규칙, grok.com Usage 화면의 직접 URL, 위젯 Grok 카드의 `_x.ai/billing` `creditUsagePercent`가 grok.com Settings → Usage의 전체 %와 같은지, On-demand를 제품별로 나눠 보여 주는지(문서와 직원 답변이 어긋남).

## 근거

- Cursor: [Grok Bot 플랜·사용량](https://cursor.com/help/grok-bot/plans) · [Grok Bot 설정](https://cursor.com/docs/grok-bot/settings) · [SuperGrok 연동](https://cursor.com/help/grok-bot/supergrok) · [사용 한도(Spending 탭)](https://cursor.com/help/models-and-usage/usage-limits) · [Spend limits](https://cursor.com/help/account-and-billing/spend-limits) · [Admin API](https://cursor.com/docs/account/teams/admin-api) · [약관](https://cursor.com/terms-of-service)
- Cursor 포럼(직원 답변 포함): [개인 사용량 API 없음](https://forum.cursor.com/t/usage-api-cli-command/160967) · [Grok Bot 미터는 앱 안에](https://forum.cursor.com/t/is-grok-bot-eating-at-cursor-usage-i-thought-it-had-its-seperate-usage/170990) · [주간 소진 후 차감 순서](https://forum.cursor.com/t/grok-bot-gives-no-warning-before-weekly-usage-spills-into-paid-on-demand/169679) · [조기 리셋과 카운트다운](https://forum.cursor.com/t/grok-bot-reset-usage-early/170283)
- xAI: [Grok FAQ(Settings → Usage, 공용 풀)](https://docs.x.ai/grok/faq.md) · [Grok Bot 설정·알림](https://docs.x.ai/grok-bot/settings-and-notifications.md) · [Grok Bot FAQ](https://docs.x.ai/grok-bot/faq.md)

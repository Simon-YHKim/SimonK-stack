# Grok Bot 사용량

> 갱신 26.09.30 · 근거 = 사용자 본인 화면 캡처 2장(grok.com Usage, Grok Bot 앱 "사용량 및 청구"), 공식 grok CLI 실측(`_x.ai/billing`, 읽기 전용), 공개 문서·포럼. 로그인이 필요한 화면을 위젯이나 에이전트가 직접 열지 않았다.
> 같은 날 앞선 판(공개 문서만 근거)은 "grok.com 사용량 화면에 Grok Bot이 없다"고 적었는데, 사용자 화면에서 **틀린 것으로 확인**됐다(DECISIONS 26.09.30 17:42 줄).

## 어디에 무엇이 나오나

| 화면 | 보이는 것(실제 라벨) | 위젯에서 |
|---|---|---|
| **grok.com → Settings → Usage** (`https://grok.com/?_s=usage`) | ① "Weekly SuperGrok Heavy Limit" — `N% used`, `Resets <날짜> at <시각>`, 제품별 %(예: Imagine) ② **"Weekly Grok Bot Limit"** — `N% used`, `Resets <날짜> at <시각>`(분 단위, 브라우저 시간대) ③ 한도 도달 시 "You've reached this week's Grok Bot limit · Buy extra credits to continue" ④ Extra Usage Credits | ①은 위젯 **Grok 카드**가 grok CLI로 자동으로 읽는다. ②는 CLI 응답에 없어 Grok Bot 카드에 **직접 입력**한다(정확한 리셋 일시는 여기서만 보임) |
| **Grok Bot 앱 → 설정 → 사용량 및 청구** | "주간 사용량" 막대와 %, "N일 후 재설정"(일 단위만), "온디맨드 월 한도 · Cursor를 통해 청구"(예: 없음), "Cursor에서 온디맨드 청구 관리 → 청구 관리" | 주간 사용률과 On-demand 월 한도를 옮겨 적는 곳. 리셋은 일 단위라 grok.com 값이 더 정확하다 |
| **Cursor 대시보드 Spending** (`https://cursor.com/dashboard/spending`) | Cursor 플랜 사용량, On-demand 요금, Monthly Limit(공개 문서 기준. 사용자 캡처는 아직 받지 못함) | On-demand 사용액·월 한도를 옮겨 적는 곳 |

## 실측으로 확인한 것 (26.09.30)

- **위젯 Grok 카드 = grok.com의 SuperGrok 한도.** SuperGrok Heavy 계정의 `_x.ai/billing`은 `creditUsagePercent: 100`, `currentPeriod.end: 2026-10-03T14:12:19Z`(한국 시각 10월 3일 오후 11:12)였고, 같은 시각 grok.com은 "Weekly SuperGrok Heavy Limit 100% used · Resets October 3, 2026 at 11:12 PM"을 보였다. 값과 리셋이 일치.
- **Grok Bot 한도는 CLI 응답에 없다.** 응답 필드는 `config.{creditUsagePercent, currentPeriod, onDemandCap, onDemandUsed, prepaidBalance, isUnifiedBillingUser, billingPeriodStart/End}`와 `subscription_tier`뿐. 제품별 %(Imagine 등)도 없다. 그래서 Grok Bot은 수동 입력을 유지한다.
- **앱의 "N일 후 재설정"은 일 단위라 부정확하다.** 같은 시각 grok.com은 Grok Bot 리셋을 10월 3일 오전 8:11로 보였고(약 2일 15시간 뒤), 앱은 "3일 후 재설정"이었다(1회 관찰 — 올림인지 반올림인지는 미확인). 그래서 카드의 리셋 입력은 일·시간이 아니라 **grok.com의 일시**를 받는다.
- 앱의 On-demand 월 한도가 "없음"이면, 주간 한도 도달 뒤에는 **리셋까지 멈춘다**(grok.com에서 추가 크레딧을 사면 계속). 월 한도가 있으면 추가 크레딧, 그다음 On-demand가 Cursor로 청구된다(Cursor 문서·직원 답변).

## 위젯 카드 사용법

위젯의 **사용량 현황 → Grok Bot** 카드에서:

1. **주간 사용률(%)** — grok.com의 Weekly Grok Bot Limit이나 앱의 주간 사용량을 입력하고 **기록**. (필수)
2. **리셋·On-demand (선택)** 을 펼치면:
   - **리셋 일시** — grok.com "Weekly Grok Bot Limit"의 `Resets …` 일시. 지금부터 8일 안의 미래만 받는다. 카드와 작업 표시줄에 남은 시간이 나오고, 그 시각이 지나면 옛 사용률을 숨기고 새 값을 안내한다. 사용률만 다시 기록하면 아직 지나지 않은 리셋 일시는 유지된다.
   - **On-demand 사용액 / 월 한도($)** — 앱에서 월 한도가 "없음"(꺼짐)이면 **0**. `$`·천 단위 쉼표를 써도 된다. 빈칸이면 지운다. 사용액은 사용률과 함께 기록된 값이라 사용률이 최신일 때만 보인다.
3. 사용률이 **100%** 면 월 한도에 따라 "리셋까지 멈춤"(0) 또는 "추가 크레딧, 그다음 On-demand로 청구될 수 있음"(0보다 큼)을 표시하고, 모르면(빈칸) 둘 다 해당될 수 있다고 적는다. 작업 표시줄 값은 경고색.
4. 링크: **grok.com 사용량 열기**(`grok.com/?_s=usage`), **Cursor Spending 열기**(`cursor.com/dashboard/spending`).

표시 규칙: 기록 후 24시간이 지나면 오래된 값, 7일 뒤에는 숫자를 숨긴다. 위젯의 새로고침 버튼은 수동 값을 갱신하지 않는다. 값이 있으면(최신·오래됨) 안내 문단은 접힌 영역("어디서 보나·리셋·On-demand")으로 들어간다. **직접 고친 칸만 저장**된다 — 리셋이나 On-demand만 고쳐 기록해도 기존 사용률의 기록 시각은 바뀌지 않고, 리셋이 지났거나 만료된 카드는 옛 사용률을 입력칸에 채우지 않는다("지난 값 N%" 안내만).

## 자동으로 읽을 수 있나 — Cursor 쪽 포함 (26.09.30 조사)

사용자 질문("그록에서 알 수 없으면 커서에서 알 수 있는 건 아니야?")에 대한 답.

- **값은 Cursor 계정 쪽에 있다.** Cursor 문서: "Grok Bot usage is metered on your Cursor account, not on Grok or X"([플랜 문서](https://cursor.com/help/grok-bot/plans)). Grok Bot 앱과 grok.com이 보여 주는 주간 %는 이 계량에서 온다.
- **개인 계정이 이 값을 읽는 공식 통로는 없다.** Cursor 직원: 개인 플랜 사용량의 공개 API·CLI 명령 없음([포럼](https://forum.cursor.com/t/usage-api-cli-command/160967)). Admin·Analytics API는 Enterprise 팀 전용([API 문서](https://cursor.com/docs/api)). 사용자들의 공개 요청 글도 답이 없다([포럼 169926](https://forum.cursor.com/t/per-agent-grok-bot-usage-who-worked-tokens-cache-and-cost-vs-the-weekly-pool/169926)). Grok Bot 앱에도 사용량을 내주는 CLI·로컬 API·MCP가 없다.
- **앱의 로그인을 빌려 비공개 서버를 부르는 방식은 하지 않는다.** 앱 토큰 재사용과 공식 앱 흉내가 필요해 위젯 절대 규칙(사칭 금지, 다른 도구 자격증명 사용 금지)과 Cursor 약관(§1.5 역공학·스크래핑 금지)에 걸린다. 화면 긁기(grok.com·cursor.com·앱 UI)도 같은 이유로 하지 않는다.
- **Cursor CLI의 `/usage`** 는 Cursor 플랜의 포함 사용량·On-demand·결제주기를 보여 준다고 문서화돼 있고([CLI 변경기록 2026-07-13](https://cursor.com/docs/cli/changelog)) Grok Bot 언급은 없다. 대화형 화면 전용이라 위젯이 쓰려면 구조화 출력이 있는지부터 확인해야 한다(미설치·미시험, 사용자 결정 대기).
- **가장 가까운 공식 경로는 xAI 쪽이다.** 공개된 grok CLI 소스([xai-org/grok-build](https://github.com/xai-org/grok-build), Apache-2.0)에 Grok Bot 주간 사용량을 돌려주는 호출이 정의돼 있지만 grok.com·모바일 앱용이고, grok CLI 명령·확장으로는 열려 있지 않다. CLI가 이것을 `_x.ai/billing`처럼 노출하면 지금 Grok 카드와 같은 방식으로 자동 조회할 수 있다.
- **그래서 위젯은**: 수동 입력을 유지하고, grok CLI 사용량 응답에 **처음 보는 필드 이름이 생기면 로그에 이름만 남긴다**(`grok billing has unrecognized fields`, 값은 기록하지 않음, 이름에 bot·product가 들어가면 `productLike: true`). 그 로그가 보이면 다시 실측해 자동 조회로 바꾼다.

## 하지 않는 것

grok.com·Cursor 화면 스크래핑이나 내부 RPC 호출(Cursor 약관 §1.5(viii) 스크래핑 금지), Grok CLI 수치를 Grok Bot 값으로 재사용. 공식 CLI나 공개 API가 Grok Bot 한도를 돌려주게 되면 수동 입력을 그 조회로 바꾼다.

## 미확인

Grok Bot 리셋 주기의 규칙(계정별 7일 롤링으로 보이지만 문서 없음), Cursor Spending 화면에 Grok Bot On-demand가 어떻게 나뉘어 보이는지(사용자 캡처 미수신), grok CLI 이후 버전이 Grok Bot 한도를 응답에 넣을지.

## 근거

- 사용자 화면 캡처(26.09.30, 리포에 넣지 않음): grok.com Usage 모달, Grok Bot 앱 설정 "사용량 및 청구"
- grok CLI 1.0.41 `_x.ai/billing` 실측(26.09.30, 위젯 계정 폴더, 식별자 가림 — 방법은 HANDOFF "실측 도구")
- Cursor: [Grok Bot 플랜·사용량](https://cursor.com/help/grok-bot/plans) · [Grok Bot 설정](https://cursor.com/docs/grok-bot/settings) · [SuperGrok 연동](https://cursor.com/help/grok-bot/supergrok) · [Spend limits](https://cursor.com/help/account-and-billing/spend-limits) · [약관](https://cursor.com/terms-of-service)
- Cursor 포럼(직원 답변 포함): [개인 사용량 API 없음](https://forum.cursor.com/t/usage-api-cli-command/160967) · [주간 소진 후 차감 순서](https://forum.cursor.com/t/grok-bot-gives-no-warning-before-weekly-usage-spills-into-paid-on-demand/169679) · [조기 리셋과 카운트다운](https://forum.cursor.com/t/grok-bot-reset-usage-early/170283)
- xAI: [Grok FAQ](https://docs.x.ai/grok/faq.md) · [Grok Bot 설정·알림](https://docs.x.ai/grok-bot/settings-and-notifications.md) · [Grok Bot FAQ](https://docs.x.ai/grok-bot/faq.md)

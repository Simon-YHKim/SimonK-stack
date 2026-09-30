# Grok Bot 사용량

> 갱신 26.09.30 · 근거 = 사용자 본인 화면 캡처 2장(grok.com Usage, Grok Bot 앱 "사용량 및 청구"), 공식 grok CLI 실측(`_x.ai/billing`, 읽기 전용), 공개 문서·포럼. 로그인이 필요한 화면을 위젯이나 에이전트가 직접 열지 않았다.
> 같은 날 앞선 판(공개 문서만 근거)은 "grok.com 사용량 화면에 Grok Bot이 없다"고 적었는데, 사용자 화면에서 **틀린 것으로 확인**됐다(DECISIONS 26.09.30 17:42 줄).

## 현재 동작

Windows의 Grok Bot 앱에 로그인되어 있으면 위젯이 시작 시와 5분마다 **Grok Bot 주간 사용률**을 자동 조회한다. Grok CLI 계정이 활성화되어 있으면 작업표시줄의 같은 Grok 칸에 `WK`·`Bot`을 **위아래 두 줄로** 표시하고, 사용량 팝업에서도 같은 Grok 카드 안에 구분한다. Grok CLI 계정이 없으면 Bot만 독립 항목으로 표시한다. 두 제품의 한도와 로그인은 서로 별개이며, 한쪽 조회가 실패해도 다른 쪽의 유효한 값은 그대로 표시한다. 새로고침 버튼으로 즉시 다시 조회할 수 있다.

자동 조회는 **비공식**이다. 설치된 Grok Bot의 `%APPDATA%\Grok Bot\sand-secrets.json`과 `Local State`에서 현재 Windows 사용자 세션의 access token을 읽고, Cursor의 문서화되지 않은 `GetSandUsageStatus`에 읽기 전용 요청을 보낸다. 토큰은 메인 프로세스 메모리에서만 다루며 파일에 쓰거나 렌더러·로그로 보내지 않는다. refresh token은 읽지 않는다. 앱·서버 형식이나 공급자 정책이 바뀌면 조회가 중단될 수 있다. 로그인 만료 시 공식 Grok Bot 앱에서 다시 로그인한다. 공식 개인 계정용 사용량 API는 확인되지 않았다.

자동 조회에 실패하면 아래 공식 화면의 사용률과 리셋 시각을 **사용량 현황 → Grok Bot**에서 직접 기록할 수 있다. 수동 값은 자동 측정에 우선하지 않는다. 리셋 시각을 모를 때는 추측하지 않는다.
한 번 감지된 Grok Bot의 자동 조회가 인증 만료·오류·세션 부재로 바뀌어도 작업표시줄의 `Bot` 행은 `—`로 남고, 마우스를 올리면 원인과 재로그인 안내를 볼 수 있다. Grok Bot을 한 번도 감지하지 못한 환경에는 빈 Bot 행을 추가하지 않는다.

## 어디에 무엇이 나오나

| 화면 | 보이는 것(실제 라벨) | 위젯에서 |
|---|---|---|
| **grok.com → Settings → Usage** (`https://grok.com/?_s=usage`) | ① "Weekly SuperGrok Heavy Limit" — `N% used`, `Resets <날짜> at <시각>`, 제품별 %(예: Imagine) ② **"Weekly Grok Bot Limit"** — `N% used`, `Resets <날짜> at <시각>`(분 단위, 브라우저 시간대) ③ 한도 도달 시 "You've reached this week's Grok Bot limit · Buy extra credits to continue" ④ Extra Usage Credits | ①은 Grok CLI가 자동으로 읽고, ②는 별도 비공식 자동 조회로 읽는다. 자동 조회가 실패하면 ②의 값과 정확한 리셋 일시를 직접 기록한다. Grok CLI 응답에는 ②가 없다 |
| **Grok Bot 앱 → 설정 → 사용량 및 청구** | "주간 사용량" 막대와 %, "N일 후 재설정"(일 단위만), "온디맨드 월 한도 · Cursor를 통해 청구"(예: 없음), "Cursor에서 온디맨드 청구 관리 → 청구 관리" | 자동 조회 실패 시 주간 사용률과 On-demand 월 한도를 옮겨 적는 곳. 정확한 리셋 일시는 grok.com에서 확인한다 |
| **Cursor 대시보드 Spending** (`https://cursor.com/dashboard/spending`) | Cursor 플랜 사용량, On-demand 요금, Monthly Limit(공개 문서 기준. 사용자 캡처는 아직 받지 못함) | On-demand 사용액·월 한도를 옮겨 적는 곳 |

## 실측으로 확인한 것 (26.09.30)

- **위젯 Grok 카드 = grok.com의 SuperGrok 한도.** SuperGrok Heavy 계정의 `_x.ai/billing`은 `creditUsagePercent: 100`, `currentPeriod.end: 2026-10-03T14:12:19Z`(한국 시각 10월 3일 오후 11:12)였고, 같은 시각 grok.com은 "Weekly SuperGrok Heavy Limit 100% used · Resets October 3, 2026 at 11:12 PM"을 보였다. 값과 리셋이 일치.
- **Grok Bot 한도는 Grok CLI 응답에 없다.** 응답 필드는 `config.{creditUsagePercent, currentPeriod, onDemandCap, onDemandUsed, prepaidBalance, isUnifiedBillingUser, billingPeriodStart/End}`와 `subscription_tier`뿐. 제품별 %(Imagine 등)도 없다. Bot의 비공식 자동 조회는 Grok CLI와 별도 경로를 사용한다.
- **앱의 "N일 후 재설정"은 일 단위라 부정확하다.** 같은 시각 grok.com은 Grok Bot 리셋을 10월 3일 오전 8:11로 보였고(약 2일 15시간 뒤), 앱은 "3일 후 재설정"이었다(1회 관찰 — 올림인지 반올림인지는 미확인). 그래서 카드의 리셋 입력은 일·시간이 아니라 **grok.com의 일시**를 받는다.
- 앱의 On-demand 월 한도가 "없음"이면, 주간 한도 도달 뒤에는 **리셋까지 멈춘다**(grok.com에서 추가 크레딧을 사면 계속). 월 한도가 있으면 추가 크레딧, 그다음 On-demand가 Cursor로 청구된다(Cursor 문서·직원 답변).

## 자동 조회 실패 시 카드 사용법

위젯의 **사용량 현황 → Grok Bot** 카드에서:

1. **주간 사용률(%)** — grok.com의 Weekly Grok Bot Limit이나 앱의 주간 사용량을 입력하고 **기록**. 수동으로 주간 사용률을 남길 때 필요하다.
2. **리셋·On-demand (선택)** 을 펼치면:
   - **리셋 일시** — grok.com "Weekly Grok Bot Limit"의 `Resets …` 일시. 지금부터 8일 안의 미래만 받는다. 카드와 작업 표시줄에 남은 시간이 나오고, 그 시각이 지나면 옛 사용률을 숨기고 새 값을 안내한다. 사용률만 다시 기록하면 아직 지나지 않은 리셋 일시는 유지된다.
   - **On-demand 사용액 / 월 한도($)** — 앱에서 월 한도가 "없음"(꺼짐)이면 **0**. `$`·천 단위 쉼표를 써도 된다. 빈칸이면 지운다. 사용액은 사용률과 함께 기록된 값이라 사용률이 최신일 때만 보인다.
3. 사용률이 **100%** 면 월 한도에 따라 "리셋까지 멈춤"(0) 또는 "추가 크레딧, 그다음 On-demand로 청구될 수 있음"(0보다 큼)을 표시하고, 모르면(빈칸) 둘 다 해당될 수 있다고 적는다. 작업 표시줄 값은 경고색.
4. 링크: **grok.com 사용량 열기**(`grok.com/?_s=usage`), **Cursor Spending 열기**(`cursor.com/dashboard/spending`).

수동 값 표시 규칙: 기록 후 24시간이 지나면 오래된 값, 7일 뒤에는 숫자를 숨긴다. 위젯의 새로고침 버튼은 자동 조회를 다시 시도하지만 수동 기록의 시각을 갱신하지 않는다. 값이 있으면(최신·오래됨) 안내 문단은 접힌 영역("어디서 보나·리셋·On-demand")으로 들어간다. **직접 고친 칸만 저장**된다 — 리셋이나 On-demand만 고쳐 기록해도 기존 사용률의 기록 시각은 바뀌지 않고, 리셋이 지났거나 만료된 카드는 옛 사용률을 입력칸에 채우지 않는다("지난 값 N%" 안내만).

## 공식 조회 경로 조사와 이후 결정 변경 (26.09.30)

아래 조사는 사용자 질문("그록에서 알 수 없으면 커서에서 알 수 있는 건 아니야?")에 대한 당시 답이다. 18:35에는 비공식 조회를 기각했지만, 22:16 사용자가 공개 구현 사례를 지정하며 다시 요청해 현재는 위의 **비공식 자동 조회**를 사용한다(DECISIONS 26.09.30 18:35·22:16). 공식 개인 계정용 조회 경로가 없다는 조사 결과는 그대로다.

- **값은 Cursor 계정 쪽에 있다.** Cursor 문서: "Grok Bot usage is metered on your Cursor account, not on Grok or X"([플랜 문서](https://cursor.com/help/grok-bot/plans)). Grok Bot 앱과 grok.com이 보여 주는 주간 %는 이 계량에서 온다.
- **개인 계정이 이 값을 읽는 공식 통로는 없다.** Cursor 직원: 개인 플랜 사용량의 공개 API·CLI 명령 없음([포럼](https://forum.cursor.com/t/usage-api-cli-command/160967)). Admin·Analytics API는 Enterprise 팀 전용([API 문서](https://cursor.com/docs/api)). 사용자들의 공개 요청 글도 답이 없다([포럼 169926](https://forum.cursor.com/t/per-agent-grok-bot-usage-who-worked-tokens-cache-and-cost-vs-the-weekly-pool/169926)). Grok Bot 앱에도 사용량을 내주는 CLI·로컬 API·MCP가 없다.
- **비공식 경로는 당시 기각했으나 이후 사용자가 지정한 공개 구현 사례를 토대로 도입했다.** 공식 앱 사칭, refresh token 사용, 화면 긁기(grok.com·cursor.com·앱 UI)는 하지 않는다. 비공식 서버 호출은 공급자 정책과 구현 변경 위험이 있으므로 사용자가 UI에서 출처를 구분할 수 있어야 한다.
- **Cursor CLI의 `/usage`** 는 Cursor 플랜의 포함 사용량·On-demand·결제주기를 보여 준다고 문서화돼 있고([CLI 변경기록 2026-07-13](https://cursor.com/docs/cli/changelog)) Grok Bot 언급은 없다. 이후 설치·시험 결과 사용량 조회 명령·구조화 출력 항목은 없고 `/usage`는 대화형 화면이었다(DECISIONS 26.09.30 20:17).
- **가장 가까운 공식 경로는 xAI 쪽이다.** 공개된 grok CLI 소스([xai-org/grok-build](https://github.com/xai-org/grok-build), Apache-2.0)에 Grok Bot 주간 사용량을 돌려주는 호출이 정의돼 있지만 grok.com·모바일 앱용이고, grok CLI 명령·확장으로는 열려 있지 않다. CLI가 이것을 `_x.ai/billing`처럼 노출하면 지금 Grok 카드와 같은 방식으로 자동 조회할 수 있다.
- **현재 위젯은**: 비공식 자동 조회를 우선하고 수동 입력을 대체 경로로 유지한다. grok CLI 사용량 응답에 **처음 보는 필드 이름이 생기면 로그에 이름만 남기는** 기존 감시도 유지한다(`grok billing has unrecognized fields`, 값은 기록하지 않음, 이름에 bot·product가 들어가면 `productLike: true`). 공식 조회 경로가 나오면 비공식 조회를 교체한다.

## 하지 않는 것

grok.com·Cursor 화면 스크래핑, 공식 Grok Bot 앱 사칭, refresh token 사용, Grok CLI 수치를 Grok Bot 값으로 재사용. 공식 CLI나 공개 API가 Grok Bot 한도를 돌려주게 되면 비공식 조회를 교체한다.

## 미확인

Grok Bot 리셋 주기의 규칙(계정별 7일 롤링으로 보이지만 문서 없음), Cursor Spending 화면에 Grok Bot On-demand가 어떻게 나뉘어 보이는지(사용자 캡처 미수신), grok CLI 이후 버전이 Grok Bot 한도를 응답에 넣을지, 비공식 자동 조회의 장기 호환성.

## 근거

- 사용자 화면 캡처(26.09.30, 리포에 넣지 않음): grok.com Usage 모달, Grok Bot 앱 설정 "사용량 및 청구"
- grok CLI 1.0.41 `_x.ai/billing` 실측(26.09.30, 위젯 계정 폴더, 식별자 가림 — 방법은 HANDOFF "실측 도구")
- Cursor: [Grok Bot 플랜·사용량](https://cursor.com/help/grok-bot/plans) · [Grok Bot 설정](https://cursor.com/docs/grok-bot/settings) · [SuperGrok 연동](https://cursor.com/help/grok-bot/supergrok) · [Spend limits](https://cursor.com/help/account-and-billing/spend-limits) · [약관](https://cursor.com/terms-of-service)
- Cursor 포럼(직원 답변 포함): [개인 사용량 API 없음](https://forum.cursor.com/t/usage-api-cli-command/160967) · [주간 소진 후 차감 순서](https://forum.cursor.com/t/grok-bot-gives-no-warning-before-weekly-usage-spills-into-paid-on-demand/169679) · [조기 리셋과 카운트다운](https://forum.cursor.com/t/grok-bot-reset-usage-early/170283)
- xAI: [Grok FAQ](https://docs.x.ai/grok/faq.md) · [Grok Bot 설정·알림](https://docs.x.ai/grok-bot/settings-and-notifications.md) · [Grok Bot FAQ](https://docs.x.ai/grok-bot/faq.md)
- 공개 구현 사례: [Windows Grok Usage HUD](https://github.com/lqiaoqing/grok-usage-hud) · [GrokBot Meter](https://github.com/nuno/grokbot-meter). 비공식 엔드포인트는 공급자 정책과 구현 변경에 따른 중단 위험이 있다.

# Grok Bot 주간 사용량

Grok Bot은 Grok Build CLI(`grok`)와 다른 주간 사용량을 사용한다. SuperGrok Heavy를 Cursor 계정에 연결했다면 Grok Bot의 **Settings → Usage & Billing → Weekly usage**에 표시되는 사용률을 기준으로 한다. Cursor 플랜 사용량과 SuperGrok 할당량은 합산되지 않는다.

위젯의 **사용량 현황 → Grok Bot** 카드에서 공식 앱에 보이는 주간 **사용률(0~100%)**을 입력하고 **기록**을 누른다. 카드에는 사용률과 남은 비율, 작업표시줄에는 선택한 표시 방식(사용/남음)과 **수동 기록** 표지가 나온다. 기록 후 24시간이 지나면 오래된 값으로 표시하고, 7일 뒤에는 숫자를 숨긴다. 위젯의 새로고침 버튼은 이 수동 값을 갱신하지 않는다.

개인 계정의 Grok Bot 주간 잔량을 반환하는 공개 API·CLI·SDK는 현재 확인되지 않았다. 따라서 자동 동기화나 xAI Grok CLI 수치 재사용은 하지 않는다. 향후 공식 인터페이스가 제공되면 수동 입력을 해당 조회로 대체할 수 있다.

근거: [Grok Bot 설정](https://cursor.com/docs/grok-bot/settings), [Grok Bot 플랜](https://cursor.com/help/grok-bot/plans), [개인 사용량 API 관련 Cursor 답변](https://forum.cursor.com/t/usage-api-cli-command/160967).

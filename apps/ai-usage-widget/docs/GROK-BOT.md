# Grok Bot 주간 사용량

Grok Bot은 Grok Build CLI(`grok`)와 다른 주간 사용량을 사용한다. SuperGrok Heavy를 Cursor 계정에 연결했다면 Grok Bot의 **Settings → Usage & Billing → Weekly usage**에 표시되는 사용률을 기준으로 한다. Cursor 플랜 사용량과 SuperGrok 할당량은 합산되지 않는다.

Windows의 Grok Bot 앱에 로그인되어 있으면 위젯이 시작 시와 5분마다 **Grok Bot 주간 사용률**을 자동 조회한다. Grok CLI 계정이 활성화되어 있으면 작업표시줄의 **같은 Grok 칸**과 사용량 팝업의 **같은 Grok 카드** 안에 `Grok`·`Bot`을 구분해 표시한다. Grok CLI 계정이 없으면 Bot만 독립 항목으로 표시한다. Bot에는 사용률·남은 비율·리셋 카운트다운·조회 시각이 나오고, 새로고침 버튼으로 즉시 다시 조회할 수 있다. 두 제품의 한도와 로그인은 서로 별개다.

이 자동 조회는 **비공식**이다. 설치된 Grok Bot의 `%APPDATA%\Grok Bot\sand-secrets.json`과 `Local State`에서 현재 Windows 사용자 세션의 access token을 읽고, Cursor의 문서화되지 않은 `GetSandUsageStatus`에 읽기 전용 요청을 보낸다. 토큰은 메인 프로세스 메모리에서만 다루며 파일에 쓰거나 렌더러·로그로 보내지 않는다. refresh token은 읽지 않는다. Grok Bot 업데이트로 형식이나 API가 바뀌면 자동 조회가 실패할 수 있다. 로그인 만료 시 Grok Bot 앱에서 다시 로그인한다.

자동 조회가 안 될 때는 **사용량 현황 → Grok Bot** 카드에서 공식 앱의 **Settings → Usage & Billing → Weekly usage**에 보이는 사용률(0~100%)을 입력하고 **기록**할 수 있다. 수동 값은 자동 측정에 우선하지 않으며, 24시간 뒤 오래됨, 7일 뒤 숫자 만료로 처리한다. 리셋 시각은 수동 값에서 추측하지 않는다. 공식 공개 개인 계정 API는 여전히 확인되지 않았다.

근거: [Grok Bot 설정](https://cursor.com/docs/grok-bot/settings), [Grok Bot 플랜](https://cursor.com/help/grok-bot/plans), [개인 사용량 API 관련 Cursor 답변](https://forum.cursor.com/t/usage-api-cli-command/160967), [Windows Grok Usage HUD](https://github.com/lqiaoqing/grok-usage-hud), [GrokBot Meter](https://github.com/nuno/grokbot-meter), [Cursor 이용약관](https://cursor.com/terms-of-service). 비공식 엔드포인트는 공급자 정책과 구현 변경에 따른 중단 위험이 있다.

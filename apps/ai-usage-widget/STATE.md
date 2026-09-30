# STATE — AI Usage Widget v2
> 덮어쓰기. 네 절만. 갱신 26.09.30 17:17 KST · Claude Code(E:\Coding Infra 세션, 워크트리 `SimonK-stack-aiuw-improve-260930`)

## 완료
- 09.15~20: v1 분석·재구성, 공급자 4종(Claude 브리지·Codex app-server·Grok ACP·Antigravity `agy /usage`) 실계정 실측, T8 GUI 전 항목, NSIS 설치, v1 정리, SimonK-stack `apps/ai-usage-widget/`로 통합(PR #48). 세부는 DECISIONS·HANDOFF의 09.20 블록
- **main 밖 스택(원격에 push됨, PR 없음)** — 브랜치가 이어진다: `feat/aiuw-auth-recovery-260923` → `feat/aiuw-usage-clarity-260925` → `feat/aiuw-banked-reset-260926` → `feat/aiuw-model-notice-260930` → `feat/aiuw-improve-260930`(이 브랜치, 끝)
  - 09.23 재인증 알림(확정 logged-out이면 계정당 1회 Windows 알림 → 공식 CLI 로그인)
  - 09.25 수치 단위(`남음`/`소모`) 명시, 계정별 빠른 소모 강조
  - 09.26 Codex 초기화권 수량 표시·사용자 1회 사용(ai-debate 판정), 설치 창 숨김, 크레딧 없는 초기화권 상태
  - 09.30 Codex 버전별 실행 파일 해석(09.29 npm 0.159 이후 `cli-unsupported-install`), 새 모델 알림(공식 문서·발표 6시간 주기)과 급증 말풍선, Grok Bot 수동 카드(09.19 "카드 없음" 번복)
  - **09.30 이 세션**: Antigravity `/usage` 서버 5xx면 같은 조회 안에서 3초 뒤 1회 재시도(`51aee9b`) · Codex `account/rateLimits/read` 20초 한도 + 실패 로그 `phase`·`elapsedMs` + 모든 공급자 일시 오류 1건은 신선한 직전 값 유지(`1d70eba`) · Grok Bot 리셋 카운트다운·On-demand 사용액/월 한도·주간 소진 경고·Cursor Spending 링크·"grok.com은 다른 미터" 안내(`f7e411b`, 근거 `docs/GROK-BOT.md`) · 새 모델 알림 출처별 상태를 설정 탭에 표시(`9ff57d3`) · 값이 최신이면 Grok Bot 안내 문단 접기(`bf5dd38`)
- 원인 규명(09.30): 09.28 Codex timeout 34건 = rateLimits 응답만 10초 한도에 걸림(Codex 자체 `logs_2.sqlite` 사본 대조, 같은 프로세스의 initialize·account/read 0.1초, models 0.2~3.9초). Antigravity 실패 7건 = Google 쿼터 서비스 `UNKNOWN (code 500)`, 모두 다음 주기 복구
- 검증(26.09.30 17:16, `bf5dd38`): `pnpm verify` exit 0(57파일·638테스트), `pnpm build` 0, `--smoke` ok:true·errors 0. 오프스크린 캡처로 Grok Bot 카드(입력·리셋 지남)·작업 표시줄 항목·설정 탭 상태 줄을 눈으로 확인(캡처 스크립트는 세션 스크래치패드, 리포 밖)
- 설치본 = 09.30 15:49 빌드(`3a19dd1` 무렵, 다른 세션). **이 브랜치의 변경은 아직 설치 안 됨**

## 진행중
- 없음

## 다음
- 사용자의 Cursor Spending·grok 화면 캡처 2장과 Grok Bot 카드 필드·라벨 대조(09.30 `/goal` 인자로 붙여 전달 안 됨 → 일반 메시지로 재첨부 요청). 위젯 Grok 카드 값(`_x.ai/billing`)이 grok.com Settings → Usage 전체 %와 같은지도 그 캡처로 확인
- 스택 전체(커밋 16개)를 main으로 올릴 PR — merge commit(스쿼시 금지, subtree 이력). 생성·머지는 사용자 확인 후
- 이 브랜치 설치(`skills-src/ai-usage-widget-install`) — 사용자 확인 후
- 설치 후 관찰: Codex timeout 재발 시 로그의 `phase`·`elapsedMs`로 20초 한도 효과 판정, Antigravity 실패 시 `reasonField`로 실패 JSON 키 확정
- 검토 후보: 새 모델 알림 끄기 설정(현재 없음, 백그라운드 웹 조회 8곳/6시간), Grok CLI가 위젯 계정 폴더에 쌓는 `logs/unified.jsonl`(09.30 각 약 3.9MB) 정리 여부, Codex app-server가 기동마다 받는 원격 플러그인 카탈로그(캐시 27MB) 비활성 옵션 유무
- 보류 계약 필드(codex credits/blocked, grok overageAvailable, `onStdoutChunk`) 필요성 재검토

## 막힌 것
- 사용자 캡처 2장 미수신(위 "다음" 첫 항목). PR·머지·설치는 사용자 확인 대기
- 관찰된 불안정: `src/main/providers/claude/bridge-script.test.ts` 한 케이스가 전체 실행 부하에서 5초 제한을 1회 넘김(09.30 17:0x, 단독 실행·재실행은 통과, 이번 변경과 무관)
- 미확인으로 남은 것: agy 로그아웃 문구(정규식 추정), Orca의 `~/.claude` statusLine 덮어쓰기 여부, Grok Bot 리셋 요일·시각 규칙, 09.25 Codex `protocol-error` 1건 원인

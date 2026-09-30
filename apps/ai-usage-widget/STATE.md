# STATE — AI Usage Widget v2
> 덮어쓰기. 네 절만. 갱신 26.09.30 20:3x KST · Claude Code(E:\Coding Infra 세션, 워크트리 `SimonK-stack-aiuw-improve-260930`)

## 완료
- 09.15~20: v1 분석·재구성, 공급자 4종 실계정 실측, T8 GUI, NSIS 설치, v1 정리, SimonK-stack `apps/ai-usage-widget/` 통합(PR #48). 세부는 DECISIONS·HANDOFF의 09.20 블록
- **09.23~30 스택 main 반영(사용자 승인 26.09.30)**, 모두 merge commit·CI 통과 후:
  - PR #58(`2bc9961`): 재인증 알림, 수치 단위·빠른 소모, Codex 초기화권, Codex 실행 파일 해석, 새 모델 알림, Grok Bot 카드 + 이 세션의 안정성(Antigravity 5xx 재시도, Codex rateLimits 20초, 일시 오류 유예)·Grok Bot 캡처 대조·5관점 검토 반영·grok billing 새 필드 감시
  - PR #59(`7e04e54`): 새 모델 알림 영어 고정(Gemini `?hl=pt-br` 번역 페이지 리다이렉트가 원인)
  - PR #60(`a4c52ae`): 실패 출처 15분 뒤 재확인 / PR #61(`1864f92`): 그 테스트의 경쟁 상태 수정
  - 스택 CI(skills-ci·validate-plugin·Cloudflare Pages)는 위젯 테스트를 돌리지 않음 → 위젯 근거는 로컬·설치 스킬 안의 `pnpm verify`
- **설치**: 설치 스킬로 20:04·20:13·20:27 재설치(20:22 1회는 검증 실패로 설치 전 중단 → #61로 해결). 설치 스킬 안 검증 648 통과, 프로세스 정상. "renderer process gone: crashed" 로그는 설치 스크립트 강제 종료 시각과 겹치고 Windows 이벤트 로그 앱 오류 0건 → 실제 충돌 아님
- **설치본 실측**: Antigravity 서버 500 → 3초 뒤 재시도 성공(20:16 로그 `serverError`·`retry`, 뒤 실패 없음). Gemini 목록은 서버가 가끔 20~30초+ 멈춤(12회 중 2회) → 요청 제한 12→30초(이번 PR)
- **Grok Bot**: 위젯 Grok 카드 = grok.com SuperGrok 한도 일치. Grok Bot 주간 사용량은 Cursor 계정 계량, 개인용 공식 통로 없음 → 수동 유지 + grok billing 새 필드 감시(DECISIONS 18:35, `docs/GROK-BOT.md`)
- **Cursor CLI 시험(사용자 승인)**: 공식 설치(`%LOCALAPPDATA%\cursor-agent`, 2026.09.28-64d2043, `cursor-agent`로 호출 — PATH상 `agent`는 grok 사본). 사용량 명령·JSON 항목 없음, `/usage`는 대화형 → 위젯 자동 조회 경로 아님. 로그인 안 함

## 진행중
- 없음

## 다음
- 이번 PR(요청 제한 30초) 머지·재설치 후 시작 직후 로그와 설정 탭 "새 모델 알림" 줄 확인
- 관찰: `grok billing has unrecognized fields` 로그(생기면 재실측→Grok Bot 자동 조회), Codex timeout의 `phase`·`elapsedMs`, Antigravity 실패의 `reasonField`(지금까지 `error`)
- 후보: 새 모델 알림 끄기 설정 없음, Grok CLI `unified.jsonl` 누적(각 약 3.9MB), Codex 원격 플러그인 카탈로그(캐시 27MB), 설치 스크립트가 위젯을 강제 종료해 남기는 "crashed" 로그
- 업스트림 공개 요청(xai-org/grok-build·Cursor 포럼)은 하지 않음(사용자 결정 26.09.30)

## 막힌 것
- 없음. 미확인: Grok Bot 리셋 주기 규칙, grok.com·앱의 100% 초과 표시 여부(수동 입력은 100까지), Cursor Spending의 Grok Bot On-demand 표시, agy 로그아웃 문구, Orca의 `~/.claude` statusLine 덮어쓰기 여부

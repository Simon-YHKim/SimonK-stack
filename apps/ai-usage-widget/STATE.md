# STATE — AI Usage Widget v2
> 덮어쓰기. 네 절만. 갱신 26.09.30 20:2x KST · Claude Code(E:\Coding Infra 세션, 워크트리 `SimonK-stack-aiuw-improve-260930`)

## 완료
- 09.15~20: v1 분석·재구성, 공급자 4종 실계정 실측, T8 GUI, NSIS 설치, v1 정리, SimonK-stack `apps/ai-usage-widget/` 통합(PR #48). 세부는 DECISIONS·HANDOFF의 09.20 블록
- **09.23~30 스택 main 반영(사용자 승인)**: PR #58(`2bc9961`, merge commit, 23커밋) — 재인증 알림, 수치 단위·빠른 소모, Codex 초기화권, Codex 실행 파일 해석, 새 모델 알림, Grok Bot 카드, 그리고 이 세션의 안정성·Grok Bot·검토 반영. PR #59(`7e04e54`) — 새 모델 알림 영어 고정(Gemini 번역 페이지 리다이렉트 원인). 둘 다 CI(skills-ci·validate-plugin·Cloudflare Pages) 통과 후 머지. 스택 CI는 위젯 테스트를 돌리지 않음 → 위젯 근거는 로컬 `pnpm verify`
- **설치**: 20:04(#58 코드), 20:13(#59 코드) 설치 스킬로 재설치. 설치 스킬 안의 검증 통과(647), 프로세스 실행 확인. 20:12:39 로그의 "renderer process gone: crashed"는 설치 스크립트의 강제 종료 시각과 겹치고 Windows 이벤트 로그에 앱 오류 0건 → 실제 충돌 아님으로 판단
- **사용자 캡처 대조·Grok Bot 판정**: 위젯 Grok 카드 = grok.com SuperGrok 한도 일치. Grok Bot 주간 사용량은 Cursor 계정 계량이나 개인용 공식 통로 없음 → 수동 유지 + grok billing 새 필드 감시(DECISIONS 18:35, `docs/GROK-BOT.md`)
- **Cursor CLI 시험(사용자 승인)**: 공식 설치(`%LOCALAPPDATA%\cursor-agent`, 2026.09.28-64d2043, 명령은 `cursor-agent`로 호출 — PATH상 `agent`는 grok 사본이 먼저). 명령 목록에 사용량 조회 없음, `status`·`about --format json`에 사용량 항목 없음(about은 `subscriptionTier`만), `/usage`는 대화형 화면 전용 → 위젯 자동 조회 경로 아님. 로그인은 하지 않음
- 이 세션 마지막 수정: 실패 출처가 있으면 15분 뒤 한 번 재확인(이번 PR, 설치 전 상태면 아래 "다음")
- 검증: `pnpm verify` exit 0(57파일·648테스트 목표), build·smoke·오프스크린 캡처 확인(스크립트는 세션 스크래치패드)

## 진행중
- 없음

## 다음
- 마지막 수정(이른 재확인) PR 머지·재설치 결과를 이 파일과 HANDOFF에 반영
- 설치 후 관찰: 설정 탭 "새 모델 알림" 줄(실패 출처), `grok billing has unrecognized fields` 로그, Codex timeout의 `phase`·`elapsedMs`, Antigravity 실패의 `reasonField`
- 남은 검토 후보: 새 모델 알림 끄기 설정 없음, Grok CLI `unified.jsonl` 누적(각 약 3.9MB), Codex 원격 플러그인 카탈로그(캐시 27MB) 비활성 옵션 유무, 설치 스크립트의 강제 종료가 남기는 "crashed" 로그
- 업스트림 공개 요청(xai-org/grok-build·Cursor 포럼)은 하지 않기로 함(사용자 결정 26.09.30)

## 막힌 것
- 없음. 미확인: Grok Bot 리셋 주기 규칙, grok.com·앱에 100% 초과 값이 보이는지(수동 입력은 100까지), Cursor Spending에서 Grok Bot On-demand 표시, Cursor CLI 로그인 후 `/usage` 화면 내용(대화형이라 위젯에는 무관), agy 로그아웃 문구, Orca의 `~/.claude` statusLine 덮어쓰기 여부

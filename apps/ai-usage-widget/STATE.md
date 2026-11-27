# STATE — AI Usage Widget v2
> 덮어쓰기. 네 절만. 갱신 26.11.28 08:50 KST · Claude Code(설치 소스 detached `99b89fe`)

## 완료
- 09.15~10.25: v1 재구성, 공급자 4종 실측, NSIS 설치, SimonK-stack 통합(PR #48), 이후 PR #58~#201 반영·재설치. 세부는 HANDOFF 각 블록과 DECISIONS
- 26.11.28: "Claude 로그인했는데 사용량 안 보임" 원인 규명 — 기본 프로필 브리지의 기록 대상이 삭제된 옛 계정에 묶여 있었음. 상태 파일 대상만 새 계정으로 바꿔 즉시 복구(캡처로 `WK 22% 남음` 확인, DECISIONS 08:27)
- 26.11.28: 브리지 카드에서 설치 후에도 기록 대상을 다시 지정하는 UI(PR #214). `pnpm verify` exit 0(59파일·694테스트), `pnpm build` exit 0. PR #214·#215 머지, 설치 스킬 재설치(app.asar `41985a406d64`), 캡처 Claude `WK 21% 남음`(허브 D-132)

## 진행중
- 없음

## 다음
- 팝업 계정 탭 브리지 카드에 "기록을 받을 계정: 개인" 표시 확인(테스트로만 확인됨)
- 관찰: Claude 5H 창이 10.31 이후 상태줄 입력에 없음(원본 stdin 확인 필요, HANDOFF 26.11.28 관찰). `grok billing has unrecognized fields`, Codex timeout `phase`, Antigravity `reasonField`, agy 모델 목록 `empty model catalog` 경고(11.28 로그, 15분마다)
- 후보: 새 모델 알림 끄기 설정, 기본 프로필 신원을 공식 CLI로 비교해 같은 계정일 때만 자동 재지정

## 막힌 것
- 없음. 미확인: Claude 5H 누락 원인, Grok Bot 리셋 주기 규칙, Orca의 `~/.claude` statusLine 덮어쓰기 여부(11.28 현재 statusLine은 위젯 브리지)

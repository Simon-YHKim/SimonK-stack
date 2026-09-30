# STATE — AI Usage Widget v2
> 덮어쓰기. 네 절만. 갱신 26.09.30 18:36 KST · Claude Code(E:\Coding Infra 세션, 워크트리 `SimonK-stack-aiuw-improve-260930`)

## 완료
- 09.15~20: v1 분석·재구성, 공급자 4종 실계정 실측, T8 GUI, NSIS 설치, v1 정리, SimonK-stack `apps/ai-usage-widget/` 통합(PR #48). 세부는 DECISIONS·HANDOFF의 09.20 블록
- **main 밖 스택(원격 push, PR 없음)**: `feat/aiuw-auth-recovery-260923` → `feat/aiuw-usage-clarity-260925` → `feat/aiuw-banked-reset-260926` → `feat/aiuw-model-notice-260930` → `feat/aiuw-improve-260930`(끝). origin/main 위 커밋 22개(다른 세션 10 + 이 세션 12)
  - 09.23~30 다른 세션: 재인증 알림, 수치 단위·빠른 소모 강조, Codex 초기화권, Codex 실행 파일 해석, 새 모델 알림·급증 말풍선, Grok Bot 수동 카드
  - **09.30 이 세션**: Antigravity 서버 5xx 1회 재시도 · Codex rateLimits 20초 한도+실패 단계 로그 · 신선한 직전 값이 있으면 일시 오류는 경고 없이 유지(초기화권 사용·재로그인 직후는 제외) · Grok Bot 카드를 사용자 화면에 맞춤(리셋=grok.com 정확한 일시, grok.com·Cursor Spending 링크, On-demand 월 한도 "없음"=꺼짐→"리셋까지 멈춤", 직접 고친 칸만 저장, 지난 값은 입력칸에 채우지 않음) · 새 모델 알림 출처별 상태를 설정 탭에 표시(Anthropic 기사 전부 실패=실패, 실패 기사 재시도) · grok billing 새 필드 이름 감시 로그 · 불안정하던 Claude 테스트 2묶음 30초 제한
- **사용자 캡처 대조 완료(26.09.30 17:30경)**: grok.com Usage와 Grok Bot 앱 "사용량 및 청구". 위젯 Grok 카드 값 = grok.com "Weekly SuperGrok Heavy Limit"(100%, 10.03 오후 11:12 리셋) 일치. grok.com에 "Weekly Grok Bot Limit"이 따로 있음(앞선 "다른 미터" 문구는 틀려서 고침). Cursor Spending 캡처는 받지 못함
- **Grok Bot 자동 조회 조사 완료(18:30)**: 값은 Cursor 계정 쪽. 개인용 공식 API·CLI·로컬 통로 없음 → 규칙 안에서 자동화 불가, 수동 유지 + 감시 로그. 근거와 기각 사유는 `docs/GROK-BOT.md` "자동으로 읽을 수 있나"와 DECISIONS 18:35
- 검토: 5관점 워크플로(에이전트 41개, 지적 40건 중 상위 18건 이중 검증) → 확정 14건·분할 1건 반영(`f9f7253` 외)
- 검증(26.09.30 18:3x): `pnpm verify` exit 0(57파일·646테스트), `pnpm build` 0, `--smoke` ok(17:1x 기준), 오프스크린 캡처로 카드·작업 표시줄·설정 줄 확인(스크립트는 세션 스크래치패드, 리포 밖)
- 설치본 = 09.30 15:49 빌드(`3a19dd1` 무렵). **이 브랜치 변경은 아직 설치 안 됨**

## 진행중
- 없음

## 다음
- 사용자 결정 대기: ① 스택 22개를 main으로 올릴 PR(merge commit, 스쿼시 금지) ② 이 브랜치 설치(`skills-src/ai-usage-widget-install`) ③ Cursor CLI 설치·`/usage` 1회 시험 여부 ④ xai-org/grok-build·Cursor 포럼에 Grok Bot 사용량 노출 공개 요청 여부
- 설치 후 관찰: `grok billing has unrecognized fields` 로그(생기면 재실측→자동 조회), Codex timeout의 `phase`·`elapsedMs`, Antigravity 실패의 `reasonField`
- 검토에서 미검증으로 남긴 하위 지적 22건 중 남은 것: 새 모델 알림 끄기 설정 없음, Grok CLI `unified.jsonl` 누적(각 약 3.9MB), Codex 원격 플러그인 카탈로그(캐시 27MB) 비활성 옵션 유무

## 막힌 것
- 없음(위 "다음" ①~④는 사용자 결정). 미확인: Grok Bot 리셋 주기 규칙, grok.com·앱에 100% 초과 값이 보이는지(수동 입력은 100까지), Cursor Spending에서 Grok Bot On-demand가 어떻게 보이는지, agy 로그아웃 문구, Orca의 `~/.claude` statusLine 덮어쓰기 여부

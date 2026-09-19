# HANDOFF — AI Usage Widget v2
> prepend 전용 로그. 새 블록을 맨 위에 얹고 직전 `## Latest`는 날짜 헤더로 강등한다. 덮어쓰지 않는다.

## Latest
- **목적**: v1 위젯을 소스 프로젝트로 재구성. 위젯 새로고침 버튼, Grok 구독 한도, 공식 CLI 로그인 위임 기반 다중 계정, Windows 테마, v1 문제 전부 해결
- **최종 갱신**: 26.09.20 08:59 KST · Claude Code(E:\Coding Infra 세션)
- **아이콘(08:59)**: Codex·Grok 아이콘을 공식 자산으로 교체(DECISIONS 26.09.20 08:57). 원본은 `resources/icons/{grok,codex}.png`, 표시용은 `*_64.png`, 단색 글리프 경로는 `src/renderer/src/brand-marks.ts`(출처 URL 주석). 새 공급자 아이콘도 같은 규칙: 공식 도메인에서 받고 출처·해시를 DECISIONS에 남긴다
- **지금까지**: 사용자가 계정 4개를 추가·로그인했고 Claude(기본 프로필 브리지)·Codex·Antigravity 수치가 실제로 표시됨(사용자 캡처). Grok만 "한도 미제공"이었는데, 실제 `_x.ai/billing` 응답에 `creditUsagePercent`가 없어서였음(주간 리셋 직후, proto3 JSON의 0 생략). 온전한 주간 config일 때만 0%로 읽도록 `providers/grok/billing.ts` 수정, 실계정 재조회로 weekly 0% 확인. `pnpm verify` 0(563테스트) / dist:dir 0 / 배포본 스모크 0 / 위젯 재실행
- **다음 1개**: Grok 0% 추론 확증 — 사용량이 쌓인 뒤 `creditUsagePercent`가 나타나는지, grok.com 주간 수치와 위젯 값이 맞는지 확인. 어긋나면 DECISIONS 26.09.20 08:40대로 되돌림
- **막힌 것**: 사용자 결정 대기 P-08 보조 모니터, SEC-06 제거 시 복원, 코드 서명, Antigravity 위젯 막대 그룹 선택 / C:\dev 이동 주체 확인
- **TODO**: codex 로그인 2회 실패 후 성공한 원인 분석 → T8 GUI 실측 → NSIS 설치(사용자 확인) → v1 교체(사용자 확인)
- **미해결 질문**: 보류한 계약 필드(codex credits/blocked, grok overageAvailable, `onStdoutChunk`). agy 로그아웃 출력 문구(정규식은 추정). Orca가 `~/.claude` statusLine을 다시 쓰면 브리지가 사라지는지
- **요청**: 없음

## 26.09.19 11:55 KST
- **목적**: v1 위젯을 소스 프로젝트로 재구성. 위젯 새로고침 버튼, Grok 구독 한도, 공식 CLI 로그인 위임 기반 다중 계정, Windows 테마, v1 문제 전부 해결
- **최종 갱신**: 26.09.19 11:55 KST · Claude Code(E:\Coding Infra 세션)
- **지금까지**: T6 실측 성공 → Antigravity 공급자 추가(`src/main/providers/antigravity/**`, `PROVIDER_TRAITS`, 팝업 label 표시, 설치 링크). 공식 `agy -p "/usage" --output-format json`만 사용, 계정 1개·위젯 로그인 없음, `/usage`가 AI 프롬프트로 처리되면 재시작 전까지 호출 중단. `pnpm verify` 0(561테스트) / `pnpm dist:dir` 0 / 배포본 스모크 0(providers 4종) / 실제 agy 1.2.7로 실경로 확인. 배포본을 다시 실행해 둠
- **다음 1개**: 사용자가 위젯 [계정 관리] 탭에서 Antigravity 계정 추가 → 5H·WK 수치 표시 확인(T6b), 이어서 T1(Codex 로그인)
- **Grok Bot**: 조사 완료, 카드 미추가(DECISIONS 26.09.19 11:56) — CLI·개인 계정용 usage API 없음, Cursor 계정에서 별도 계량. 재검토 조건 = Cursor가 usage API 또는 CLI usage 명령을 문서화
- **막힌 것**: 사용자 결정 대기 P-08 보조 모니터, SEC-06 제거 시 복원, 코드 서명, Antigravity 위젯 막대 그룹 선택 / C:\dev 이동 주체 확인
- **TODO**: T6b·T1·T2·T3·T4 실측 → T8 GUI 실측 → NSIS 설치(사용자 확인) → v1 교체(사용자 확인)
- **미해결 질문**: 보류한 계약 필드(codex credits/blocked, grok overageAvailable, `onStdoutChunk`)를 실측 후 추가할지. agy 로그아웃 출력 문구(정규식은 추정)
- **요청**: REQ-260915-01 실측 단계에서 브라우저 로그인·코드 입력(사용자)

## 26.09.19 11:22 KST
- **목적**: v1 위젯을 소스 프로젝트로 재구성. 위젯 새로고침 버튼, Grok 구독 한도, 공식 CLI 로그인 위임 기반 다중 계정, Windows 테마, v1 문제 전부 해결
- **최종 갱신**: 26.09.19 11:22 KST · Claude Code(E:\Coding Infra 세션에서 이어받음)
- **지금까지**: 소스 위치가 `E:\Coding Infra\dev\ai-usage-widget`로 바뀜(C:\dev 없음). 이동 중 빠진 src·resources를 `git restore`로, node_modules를 `pnpm install --frozen-lockfile --config.confirmModulesPurge=false`로 복구. CLI 설치 안내 URL 3건 확정(`links.ts`). `pnpm verify` 0(539테스트) / `pnpm build` 0 / `pnpm dist:dir` 0 / 배포본 스모크 0(ok:true, packaged:true, CLI claude 2.1.277·codex 0.155.1·grok 1.0.34)
- **다음 1개**: 사용자 참관 실측 T1(Codex 로그인) — 배포본 실행 → 첫 실행 팝업의 [계정 관리] 탭 → [Codex 계정 추가] → device code 로그인
- **막힌 것**: 사용자 결정 대기 P-08 보조 모니터, SEC-06 제거 시 복원, 코드 서명 / C:\dev 이동 주체 확인
- **TODO**: T1·T2·T3·T4 실측 → T8 GUI 실측 → NSIS 설치(사용자 확인) → v1 교체(사용자 확인)
- **미해결 질문**: 보류한 계약 필드(codex credits/blocked, grok overageAvailable, `onStdoutChunk`)를 실측 후 추가할지
- **요청**: REQ-260915-01 실측 단계에서 브라우저 로그인·코드 입력(사용자)

## 26.09.15 05:10 KST
- **목적**: v1 위젯을 소스 프로젝트로 재구성. 위젯 새로고침 버튼, Grok 구독 한도, 공식 CLI 로그인 위임 기반 다중 계정, Windows 테마, v1 문제 전부 해결
- **최종 갱신**: 26.09.15 05:10 KST · Claude Code(리뷰 2차 수정 에이전트)
- **지금까지**: 리뷰 1차(54ac8ab)·2차 수정 반영. 2차 = RR-01 위치 미리보기 중 팝업 고정(`WindowManager.reposition`), RR-02 설정 변경 직렬화·자동 실행 되돌림(`controller.updateSettings`). `pnpm verify` 0(535테스트) / `pnpm dist:dir` 0 / 배포본 스모크 0(ok:true)
- **다음 1개**: 사용자 참관 실측 T1(Codex 로그인) — 위젯 계정 탭에서 Codex 계정 추가 → device code 로그인
- **막힌 것**: CLI 설치 안내 URL 미확정(`src/main/platform/links.ts` 비어 있음) / 사용자 결정 대기 P-08 보조 모니터, SEC-06 제거 시 복원, 코드 서명
- **TODO**: T1·T2·T3·T4 실측 → T8 GUI 실측(오프셋 슬라이더 드래그 right·left 정렬에서 값이 튀지 않는지, 드래그 후 팝업이 한 번만 옮겨지는지 포함) → NSIS 설치(사용자 확인) → v1 교체(사용자 확인)
- **미해결 질문**: 보류한 계약 필드(codex credits/blocked, grok overageAvailable, `onStdoutChunk`)를 실측 후 추가할지
- **요청**: REQ-260915-01 실측 단계에서 브라우저 로그인·코드 입력(사용자)

## 26.09.15 04:10 KST
- **목적**: v1 위젯을 소스 프로젝트로 재구성. 위젯 새로고침 버튼, Grok 구독 한도, 공식 CLI 로그인 위임 기반 다중 계정, Windows 테마, v1 문제 전부 해결
- **최종 갱신**: 26.09.15 04:10 KST · Claude Code(통합 에이전트)
- **지금까지**: 모듈 5개(shell·codex·claude·grok·renderer) main 병합, 실제 어댑터 연결, 계약 변경 반영(DECISIONS 04:06). `pnpm verify` 0 / `pnpm build` 0 / `pnpm dist:dir` 0 / 배포본 스모크 0(ok:true). 퓨즈 확인. 워크트리·병합 브랜치 정리
- **다음 1개**: 사용자 참관 실측 T1(Codex 로그인) — 위젯 계정 탭에서 Codex 계정 추가 → device code 로그인
- **막힌 것**: CLI 설치 안내 URL 미확정(`src/main/platform/links.ts` 비어 있음)
- **TODO**: T1·T2·T3·T4 로그인·수치 실측 → 결과로 codex 오류 판정·grok billing 파서·claude needs-paste 조정 → T8 GUI 실측(팝업 blur, SetWindowPos topmost, 전체화면, 재질 #48031, 테마 이벤트, 배포본 자동 시작 Run 값 'AIUsageWidgetV2') → 기본 프로필 브리지 대상 계정 삭제 시 확인 UI → NSIS 설치(사용자 확인) → v1 교체(사용자 확인)
- **미해결 질문**: 보류한 계약 필드(codex credits/blocked, grok overageAvailable, `onStdoutChunk`)를 실측 후 추가할지
- **요청**: REQ-260915-01 실측 단계에서 브라우저 로그인·코드 입력(사용자)

## 26.09.15 02:23 KST
- **목적**: v1 위젯을 소스 프로젝트로 재구성. 위젯 새로고침 버튼, Grok 구독 한도, 공식 CLI 로그인 위임 기반 다중 계정, Windows 테마, v1 문제 전부 해결
- **최종 갱신**: 26.09.15 02:23 KST · Claude Code
- **지금까지**: 조사 완료(docs/RESEARCH-auth-quota.md), v1 명세(docs/SPEC-v1-baseline.md), 서비스별 방식 확정 — Claude=statusline 브리지, Codex=app-server, Grok=grok ACP만, Gemini 제거, Antigravity 보류, Orca 미사용(DECISIONS 02:23)
- **다음 1개**: 뼈대 구현 워크플로 실행
- **막힌 것**: 없음
- **TODO**: 스캐폴딩(`pnpm verify`) → 모듈 구현 → 통합·리뷰 → 사용자와 로그인 실측(T1·T2·T4·T6)·T8 → 패키징·설치 → v1 교체(사용자 확인)
- **미해결 질문**: 없음
- **요청**: 실측 단계에서 브라우저 로그인·코드 입력(사용자)

## 26.09.15 01:36 KST
- **목적**: v1 위젯을 소스 프로젝트로 재구성. 위젯 새로고침 버튼, Grok 구독 한도, 공식 CLI 로그인 위임 기반 다중 계정, Windows 테마, v1 문제 전부 해결
- **최종 갱신**: 26.09.15 01:36 KST · Claude Code
- **지금까지**: v1 분석 완료, 사용자 결정 4건(DECISIONS.md), 리포 생성, 조사 워크플로 진행 중
- **다음 1개**: 조사 결과로 서비스별 인증·조회 설계 확정
- **막힌 것**: 없음
- **TODO**: 설계 확정 → 스캐폴딩(`pnpm verify`) → 서비스별 구현 → UI/테마 → 패키징·설치 → v1 교체(사용자 확인)
- **미해결 질문**: 없음
- **요청**: 없음

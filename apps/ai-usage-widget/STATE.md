# STATE — AI Usage Widget v2
> 덮어쓰기. 네 절만. 갱신 26.09.20 17:16 KST · Claude Code(E:\Coding Infra 세션)

## 완료
- v1 전수 분석 → docs/SPEC-v1-baseline.md(V1-01~43), 조사 → docs/RESEARCH-auth-quota.md, 결정 → DECISIONS.md
- 뼈대·모듈 5개·통합·리뷰 1·2차(09.15)
- 09.19 CLI 설치 안내 URL 확정, **Antigravity 공급자 추가**(공식 `agy -p "/usage"`, 계정 1개·위젯 로그인 없음, 요청 소모 차단기), Grok Bot 조사 → 카드 미추가
- 09.19~20 **실사용 실측 통과**(사용자): 계정 4개 로그인, 기본 `~/.claude` 브리지(Orca statusLine을 감쌈), 공급자 4종 수치 표시(T1·T2·T3·T4·T6b), **T8 GUI 전 항목 OK**(팝업 blur·전체화면 숨김·테마 전환·슬라이더·자동 시작)
- 09.20 수정·규명: Grok 0% 해석(확증), Codex 주간 창만 오는 것은 정상, Codex 첫 로그인 `protocol-error`(app-server 2개 경합 → `quiesce`), Codex 2번째 `login-failed`(로그인 완료 직후 account/read가 옛 상태 → 재조회 + 성공 신뢰, 정황 근거), agy 1회 실패(규명 불가 → 진단 로그 보강), 자동 조회 공급자별 최소 간격, 아이콘(공식 SVG·투명 배경·테마색, 사용자 확인), 자동 시작 Run 값이 옛 실행 파일을 가리키던 문제
- 09.20 **설치 완료**: NSIS 사용자 전용 설치본 `%LOCALAPPDATA%\Programs\ai-usage-widget`(설치 파일 sha256 052A7F515C47C777…, 서명 없음), 실행 중, Run 값이 설치본 경로로 자동 교정됨(로그 `autostart re-registered`)
- 09.20 **v1 정리**: v1 자동 실행 값 제거, v1 폴더·userData는 휴지통(복구 가능). 결정 4건 확정(SEC-06 자동 복원 없음·P-08 보류·코드 서명 제외·Antigravity 첫 그룹)
- 09.20 **리포 통합**: 공개 리포 SimonK-stack의 `apps/ai-usage-widget/`로 이력 포함 이전 + 설치 스킬 `skills-src/ai-usage-widget-install`(DECISIONS 26.09.20 12:05). 공개 전 전체 이력 스캔 0건
- 검증(26.09.20 17:15, 새 위치의 통합 브랜치): `pnpm install --frozen-lockfile` 0, `pnpm verify` exit 0(52파일·577테스트). 스택 CI 게이트(`run_ci.py`) PASS 141 skills, 플러그인 검증 OK. 설치 스크립트는 PowerShell 5.1에서 `-Status`·`-DryRun`·`-Uninstall` 거절(exit 3) 실측

## 진행중
- 없음

## 다음
- 실패가 다시 나오면 로그로 확정: agy 실패 JSON의 실제 필드(현재 error·message·response 순 추정), Codex 로그인 완료 직후 account/read 지연(정황 근거)
- 보류 중인 계약 필드(codex credits/blocked, grok overageAvailable, `onStdoutChunk`) 필요성 재검토

## 막힌 것
- 없음. 미확인으로 남긴 것: agy 로그아웃 상태의 출력 문구(정규식은 추정), Orca가 나중에 `~/.claude` statusLine을 덮어쓰는지(09.20 10:48까지는 유지)

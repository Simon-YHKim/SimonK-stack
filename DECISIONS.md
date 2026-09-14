# DECISIONS — AI Usage Widget v2
> append-only. 요약·재작성·삭제 금지. 1줄 = `YY.MM.DD HH:MM · 결정 · 이유 · 뒤집는 조건`
> 100KB 도달 시 기간으로 쪼갠다(`DECISIONS-2026H2.md`).

26.09.15 01:36 · 원본 v1(C:\AI.Usage.Widget-1.0.2-win, Electron 34 빌드 산출물만 존재)을 수정하지 않고 새 소스 프로젝트로 재구성한다 · 원본 소스 없음·git 없음이라 직접 수정은 되돌릴 수 없고, v1 폴더는 Authenticated Users 쓰기 권한 문제가 있음 · 원본 소스가 발견되면 그 소스 기반으로 전환 검토
26.09.15 01:36 · 소스 위치 C:\dev\ai-usage-widget(git, main), 설치 위치 %LOCALAPPDATA%\Programs\AI Usage Widget(사용자 전용 쓰기) · 사용자 선택(설치·교체 질문) + 폴더 권한 문제 해소 · 사용자가 다른 위치 지정
26.09.15 01:36 · 기존 v1 앱 종료·자동 실행(HKCU Run 'electron.app.AI Usage Widget') 해제·폴더 삭제는 v2 검증 완료 후 사용자 확인을 받고 실행한다 · 되돌릴 수 없는 작업(§3) · 없음
26.09.15 01:36 · 인증 = 공식 CLI 로그인 위임 + 계정별 격리 설정 폴더(다중 계정) · 사용자 선택. 실제 인증과 다중 계정을 공식 앱 사칭·차용 client ID 없이 달성 · 특정 CLI가 설정 폴더 격리나 비대화형 로그인을 지원하지 않는 것으로 확인되면 그 서비스만 재결정(사용자 확인)
26.09.15 01:36 · Grok 측정 대상 = 구독 한도(세션·주간 사용률, 리셋 시각). xAI API 크레딧은 범위 밖 · 사용자 선택. grok CLI(auth.x.ai OIDC)로 구독 사용 중 · 사칭 없이 비대화형 조회가 불가능하면 사용자에게 대안 보고 후 재결정
26.09.15 01:36 · Gemini CLI·Antigravity는 사칭 없이 실제 수치를 읽는 공식 경로가 확인된 것만 유지하고, 나머지는 제거 후 이유를 보고한다 · 사용자 선택 · 조사 결과
26.09.15 01:36 · 조회 실패 시 가짜 수치(customMock) 표시 금지. 상태를 '조회 실패/미확인'으로 두고 마지막 실측값과 측정 시각을 표시한다 · v1 문제 1(목업을 정상 값으로 표시). 미확인은 0%와 구분 · 없음
26.09.15 01:36 · 요청 헤더에 공식 클라이언트 사칭 User-Agent·ideType을 쓰지 않는다. 자체 UA `ai-usage-widget/<버전>` 사용 · v1 문제 3 · 공급자가 자체 UA를 거부하는 것이 확인되면 그 서비스 조회를 비활성화하고 보고(사칭으로 우회하지 않음)
26.09.15 01:36 · (Claude 결정) Windows 테마 = 시스템 라이트/다크 자동 추종 + 시스템 강조색 + Win11 Mica/Acrylic 반투명. '투명 효과' 꺼짐이면 불투명 폴백. 기존 4테마는 유지 · 사용자 요청 "윈도우 테마와 매칭되게 자연스러운 테마" · 사용자가 다른 스타일 요청
26.09.15 01:36 · (Claude 결정) 새로고침 버튼은 작업표시줄 위젯 막대 자체에 둔다(팝업 없이 동작, 조회 중 회전 표시, 연타 방지) · 사용자 요청 1 · 사용자가 위치 변경 요청
26.09.15 01:36 · 코드 서명 인증서 구매는 이번 범위에서 제외(비용 발생, §3 비용 게이트). 서명 없이 가능한 보강(asar·무결성 퓨즈·RunAsNode 비활성·사용자 전용 설치 경로)만 적용 · 비용은 사용자 승인 필요 · 사용자가 인증서 구매 승인
26.09.15 02:23 · Claude 수치 = 공식 statusline 브리지(Claude Code가 statusLine 명령에 주는 stdin JSON의 rate_limits를 위젯 전용 파일에 기록). 위젯은 Claude 토큰을 읽지 않고 /api/oauth/usage를 호출하지 않는다. 브리지 설치는 settings.json 백업 후 기존 statusLine 명령을 감싸 보존한다 · 사용자 선택. Anthropic 정책이 제3자 앱의 구독 자격증명 사용을 금지(docs/RESEARCH-auth-quota.md 3-1) · statusline에 rate_limits가 없는 것으로 실측되면 사용자에게 보고 후 재결정
26.09.15 02:23 · Claude 로그인 = 위젯 계정 폴더를 CLAUDE_CONFIG_DIR로 `claude auth login --claudeai`를 파이프 실행(URL 표시 + 코드 붙여넣기 UI, 타임아웃·kill). 계정 표시는 `claude auth status --json`. ~/.claude·Orca 폴더를 계정 폴더로 쓰지 않고 `--console`은 노출하지 않는다 · 연구 3-1 · T2 실측 실패
26.09.15 02:23 · Codex = 위젯 계정 폴더(먼저 생성)를 CODEX_HOME으로 `codex app-server`(stdio) 실행 → `account/login/start{type:chatgptDeviceCode}` 로그인 → `account/rateLimits/read` 조회 후 종료. experimentalApi·chatgptAuthTokens·apiKey·~/.codex 공유 금지. npm .cmd shim은 node + JS 엔트리로 직접 실행(shell 없음) · 연구 3-2 · T1 실측 실패
26.09.15 02:23 · Grok = 계정별 GROK_HOME + `grok login --device-auth`. 수치는 공식 grok 바이너리 ACP(`grok agent stdio`)의 x.ai/billing만 사용하고, 없으면 '측정 불가'. /billing 직접 호출·OIDC refresh 직접 수행·Orca 값 금지 · 사용자 선택, 사칭 금지 원칙과 일치 · T4에서 ACP 경로가 없으면 보고 후 재결정
26.09.15 02:23 · Gemini CLI 카드 제거 · 공식 비대화형 쿼터가 없고 약관이 제3자 직접 접근을 정지 사유로 명시(연구 3-4). 01:36 'Google 계열' 결정 적용 · 공식 쿼터 경로가 생기면 재검토
26.09.15 02:23 · Antigravity 카드는 뼈대에서 제외하고, T6(`agy -p "/usage" --output-format json`)가 요청 소모 없이 수치를 주면 추가 · 로컬 language server RPC는 약관 위반(연구 3-5) · T6 성공
26.09.15 02:23 · Orca를 수치·계정 소스로 쓰지 않는다 · 01:36 인증 방식 A 선택. Orca 상류가 사칭 호출·캐시 값·전권 런타임 토큰(연구 4절) · 사용자가 Orca 연동 요청
26.09.15 02:23 · 로그인 실측(T1 Codex·T2 Claude·T4 Grok·T6 Antigravity)은 뼈대 완성 후 위젯 화면에서 사용자와 함께 한다. 브라우저 로그인·코드 입력은 사용자가 직접 한다 · 사용자 선택 · 없음
26.09.15 02:23 · (Claude 결정) 스택 = Electron 44.3.0 고정, electron-vite 5 + Vite 7 + TypeScript(UI 프레임워크 없음), pnpm, vitest, electron-builder 26.15.3 NSIS per-user(%LOCALAPPDATA%\Programs), 퓨즈(runAsNode·NodeOptions·CliInspect off, asar integrity·onlyLoadAppFromAsar·cookie encryption on), app:// 프로토콜 + CSP 응답 헤더 · 지원 중인 최신 stable, 연구 5절 · Electron 45 stable 후 패치 1~2회 나오면 업그레이드
26.09.15 02:23 · (Claude 결정, 01:36 테마 결정 보완) 새 'Windows' 테마의 기본은 불투명 시스템 색(라이트/다크·강조색·고대비 추종)이고 Mica/Acrylic은 설정 옵션으로 두며 T8 실측 전까지 기본 off · Electron #48031(창이 가려지거나 절전일 때 재질이 검정·회색으로 깨짐, not planned) · T8에서 문제가 없으면 기본 on
26.09.15 02:23 · (Claude 결정) 위치 = screen workArea/bounds + display 이벤트. 최상위 유지·전체화면 감지는 koffi로 user32를 메인에서 호출하고 TaskbarDock.exe는 제거한다. koffi가 실패하면 해당 기능만 끄고 표시 · v1 외부 exe가 무서명이고 반복 spawn됨 · T8에서 koffi 패키징 실패 시 재결정

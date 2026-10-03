# HANDOFF — AI Usage Widget v2
> prepend 전용 로그. 새 블록을 맨 위에 얹고 직전 `## Latest`는 날짜 헤더로 강등한다. 덮어쓰지 않는다.

## Latest
- **목적**: D-63(REINSTALL_THEN_FIX) 이행. 검증된 main으로 임시 재설치한 뒤, 사용자가 요청한 경고 표시 교체를 main 위에서 세 모드 모두 구분되게 다시 만든다
- **최종 갱신**: 26.10.04 00:55 KST · Claude Code(워크트리 `SimonK-stack-aiuw-warn-261004`, 브랜치 `fix/aiuw-warn-shape-261004`)
- **지금까지**:
  - 임시 재설치 완료: 소스 = 고정 워크트리 `SimonK-stack-aiuw-main-261004`(detached `fb5c9cf`), 설치 스킬 `-Source` 명시. 설치 스킬 안 `pnpm verify` exit 0(58파일·674테스트). 설치본 app.asar sha256 앞 12자리 `E26D90FA195E`(새 빌드와 일치). 프로세스 5개, 로그 `rendered:"accounts"`, 위젯 캡처에 계정 수치 표시. 계정·설정·브리지 파일 해시와 statusLine·Run 값 변화 없음
  - 설치 전 증분 백업: 위젯을 멈추고 10.03 백업 이후 바뀐 런타임 파일 30개를 `aiuw-backup-261003\incr-261004-003827\`에 복사(해시 일치, manifest 포함). 자격증명 파일은 바뀌지 않았다
  - 경고 교체(이 브랜치): 빠른 소모 = 상자 없는 하늘색·민트·보라 배경 디밍 + 아이콘 아래쪽 삼각형(`.pace-mark`), 값 변경 = 숫자 색 깜박임 + 밑줄. 모션 감소·고대비에서도 삼각형과 밑줄은 남는다. 근거는 DECISIONS 26.10.04 00:54
  - 게이트: 격리 Electron에서 일반 다크·라이트, 모션 감소 다크·라이트, 고대비 5가지 153프레임 모두 삼각형은 경고 계정에만, 밑줄은 값 변경 숫자에만 검출. `pnpm verify` exit 0(58파일·675테스트)
- **다음 1개**: 사용자가 PR을 CI 뒤 머지하면 설치 스킬로 다시 설치한다(명시적 `-Source` + 머지 커밋 고정). 그 전에는 재설치하지 않는다
- **막힌 것**: PR 머지는 사용자 몫이다
- **작업 규칙 변화**:
  - 렌더러 테스트(vitest renderer 프로젝트)에서 `*.css?raw`는 빈 문자열이다(vitest CSS 처리 꺼짐). CSS 규칙을 정적으로 검사하는 테스트는 계약 파일(`vitest.config.ts`)을 고치지 않고는 못 만든다 → DOM 테스트 + 격리 Electron 게이트로 검증한다
  - 게이트 모양 단서 판정: 삼각형 = 경고 계정의 `.pace-mark` 영역에서 채움 색 픽셀 60개 이상, 다른 계정 같은 자리 10개 미만. 밑줄 = 숫자 상자 아래 띠에서 글자색이 폭 70% 이상인 가로 행 2개 이상, 다른 계정 0개

## 26.10.04 00:16 KST
- **목적**: D-61(허브 D-54 재개 판정) 이행. 이미 설치된 값 변경 표시 갱신은 유지하고, 사용자 데이터 백업·사본 복원 리허설을 마친 뒤 경고 구분 검증 결과로 main 반영 범위를 정한다
- **최종 갱신**: 26.10.04 00:16 KST · Claude Code(워크트리 `SimonK-stack-aiuw-land-261003`, 브랜치 `feat/aiuw-value-flash-land-261003`)
- **지금까지**:
  - 설치본은 `d767272` 빌드 그대로다(app.asar sha256 앞 12자리 `77D19EE5FC5D`, 이번 작업 재설치 0회).
  - 백업 위치는 `%USERPROFILE%\.claude\flat-link-archive\aiuw-backup-261003`이다. 상속을 끊고 사용자·SYSTEM·Administrators만 접근하게 했다. 내용은 3폴더 7,683파일(210,591,478바이트), `~/.claude/settings.json`의 statusLine 값, Run 값 1개, setup 2개(현재 `3DA00E69…`, 직전 후보 `52BD8014…`), `manifest.json`이다.
  - 일관된 복사를 위해 위젯을 26.10.03 23:45:59~23:46:26 KST 동안 정지했다. 재시작 뒤 프로세스 5개가 돌고 로그에 `rendered:"accounts"`가 찍혔다.
  - 사본 복원 리허설은 임시 폴더에서 했다(라이브 경로 미접촉). 파일 수·바이트·해시가 전부 일치했다. Run 값은 임시 키로 가져와 일치를 확인한 뒤 그 키를 지웠다. 바이트 일치는 토큰 유효성이나 재로그인 없는 복구를 증명하지 않는다.
  - 경고 구분 게이트 결과 `d767272`는 일반 FAIL·모션 감소 FAIL·고대비 PASS였다. 그래서 PR에는 `2c21eec`만 cherry-pick했다. 근거는 DECISIONS 26.10.04 00:16이다. `pnpm verify` exit 0(58파일·674테스트).
- **다음 1개**: `d767272`의 경고 표시를 값 변경 표시와 다른 색·모양으로 고칠지 후속 판단한다. 판단 전에는 main 기반 재설치를 보류한다. main으로 설치하면 경고는 `2c21eec`의 노란 상자로, 값 변경 표시는 `2c21eec`식(글자색)으로 돌아간다.
- **막힌 것**: PR 머지는 사용자 승인 대기다.
- **작업 규칙 변화**:
  - 화면 구분 검증 절차: 임시 vitest 프로브로 실제 WidgetApp DOM을 덤프한다. 격리 Electron(임시 `--user-data-dir`, offscreen)에서 CDP `Emulation.setEmulatedMedia`로 모션 감소·forced-colors를 켠다. 애니메이션 시각을 고정해 캡처하고 ΔE00을 잰다.
  - forced-colors를 검증할 때는 `data-high-contrast='true'`도 함께 준다. 실제 고대비에서는 둘이 같이 켜지고 `.widget-root`가 `forced-color-adjust: none`이다.
  - CDP 명령은 페이지를 로드한 뒤에 보낸다. 창을 여러 번 열 때는 `window-all-closed`를 무시해야 한다.

## 26.09.30 22:41 KST
- **목적**: Grok CLI와 Grok Bot 사용량을 한 칸의 `WK`·`Bot` 두 행으로 구분 표시
- **최종 갱신**: 26.09.30 22:41 KST · Codex
- **지금까지**: 작업표시줄 Grok 칸과 팝업 Grok 카드 안에 Bot 주간 계량을 묶었다. 별도 계량·로그인·오류 상태는 유지하며 Grok 계정이 없으면 Bot만 표시한다. `docs/GROK-BOT.md` 참고.
- **다음 1개**: 비공식 Grok Bot 조회가 공급자 변경으로 중단되면 공식 인터페이스로 교체한다.

## 26.09.30 22:16 KST
- **목적**: Grok Bot 주간 사용량 자동 추적
- **최종 갱신**: 26.09.30 22:16 KST · Codex
- **지금까지**: Windows Grok Bot 로그인 세션에서 비공식 Cursor 주간 사용량을 읽는 경로를 위젯에 연결했다. 실제 로컬 세션에서 HTTP 200·사용률·리셋 필드 응답을 확인했다. 실패 시 이전 수동 기록 폴백. `docs/GROK-BOT.md` 참고.
- **다음 1개**: 공급자 공식 인터페이스가 공개되면 비공식 조회를 교체한다.

## 26.09.30 20:3x KST
- **목적**: 설치본에서 나온 결함 마무리(새 모델 알림 재확인·테스트 경쟁·요청 제한)
- **최종 갱신**: 26.09.30 20:3x KST · Claude Code(E:\Coding Infra 세션)
- **지금까지**: PR #60(15분 재확인)·#61(테스트 경쟁 상태, 설치 스킬 검증에서 1회 실패해 설치가 멈춘 원인) 머지 후 20:27 설치. 설치본에서 Antigravity 5xx 재시도 성공 확인. Gemini 목록은 서버 간헐 지연(12회 중 19.7초·30초+ 각 1회) → 요청 제한 30초(이번 PR). main = #58~#61 머지 반영
- **다음 1개**: 이번 PR 머지·재설치 후 시작 직후 로그에 Gemini 실패가 없는지 확인
- **막힌 것**: 없음
- **작업 규칙 변화**: 설치 스킬은 설치 전에 `pnpm verify`를 다시 돌린다 — 부하에 민감한 테스트는 여기서 먼저 드러난다(#61). 새 시간 의존 테스트는 전체 병렬 실행과 겹쳐 반복 돌려 본다

## 26.09.30 20:2x KST
- **목적**: 사용자 승인(1 PR·머지, 2 설치, 3 Cursor CLI 시험; 4 공개 요청은 안 함) 실행과 설치 뒤 발견한 결함 수정
- **최종 갱신**: 26.09.30 20:2x KST · Claude Code(E:\Coding Infra 세션)
- **지금까지**: PR #58(`2bc9961`)·#59(`7e04e54`) main 머지(merge commit, CI 통과 확인 후). 설치 2회(20:04, 20:13), 프로세스 정상. 설치 직후 Gemini 모델 목록이 또 비어 원인 규명 — Google이 가끔 `?hl=pt-br` 번역 페이지로 리다이렉트 → 영어 고정+패턴 확장(#59). 재설치 뒤엔 12초 시간 초과 1회 → 실패 출처 15분 뒤 재확인(이번 PR). Cursor CLI 설치·시험: 사용량 조회 명령·JSON 항목 없음, `/usage`는 대화형 → 자동 조회 경로 아님
- **다음 1개**: 이번 PR 머지·재설치 후 설정 탭 "새 모델 알림" 줄이 전부 읽음으로 바뀌는지 확인
- **막힌 것**: 없음
- **작업 규칙 변화**: 설치 스크립트는 위젯을 강제 종료하므로 "renderer process gone: crashed" 한 줄이 남을 수 있다(Windows 이벤트 로그로 실제 충돌 여부 확인). Cursor CLI는 `cursor-agent`로 부른다(`agent`는 PATH상 grok 사본)

## 26.09.30 18:36 KST
- **목적**: 위젯 개선(안정성·UX·Grok Bot·빠진 기록) + 사용자 캡처로 Grok Bot 대조 + "커서에서 알 수 있나" 조사(사용자 지시 26.09.30)
- **최종 갱신**: 26.09.30 18:36 KST · Claude Code(E:\Coding Infra 세션)
- **어디서**: `feat/aiuw-improve-260930`(워크트리 `SimonK-stack-aiuw-improve-260930`), origin/main 위 22개(이 세션 12개). main 병합·설치 안 함
- **지금까지**: 캡처 2장(grok.com Usage, Grok Bot 앱) 대조 완료 — 위젯 Grok 카드 값 일치, grok.com에 "Weekly Grok Bot Limit" 별도 존재, 앱 리셋은 일 단위라 카드는 grok.com 정확한 일시를 받게 바꿈(`30612f2`·`17830c6`). 5관점 검토 워크플로 확정 14건 반영(`f9f7253`: 직접 고친 칸만 저장, 지난 값 미리 채우기 금지, 초기화권·재로그인 뒤 유예 해제, 모델 알림 Anthropic 실패 판정 등). Claude 테스트 불안정 해소(`acb80be`). Grok Bot 자동 조회: 값은 Cursor 계정 쪽이나 개인용 공식 통로 없음 → 수동 유지 + grok billing 새 필드 이름 감시 로그(DECISIONS 18:35, `docs/GROK-BOT.md`). `pnpm verify` 0(646)
- **다음 1개**: 사용자에게 PR·설치·Cursor CLI 시험·공개 요청 4가지 결정 받기(STATE "다음" ①~④)
- **막힌 것**: 없음(사용자 결정 대기). REQ-260930-01(캡처)은 grok.com·앱 2장으로 닫음, Cursor Spending 캡처는 선택
- **작업 규칙 변화**: 다른 앱의 설치본·데이터를 풀어 보는 조사는 결과를 공개 리포 문서에 옮기지 않는다(공개 출처만 인용, 스크래치 사본은 삭제). 워크플로 검증자는 raw JSON을 받아 수동 종합(스키마 미사용)

## 26.09.30 17:17 KST
- **목적**: 위젯 개선 — 로그로 드러난 안정성 문제(Codex 조회 시간 초과, Antigravity 서버 500), 화면·UX, 새 기능, Grok Bot 보완, 빠진 기록 정리(사용자 지시 26.09.30)
- **최종 갱신**: 26.09.30 17:17 KST · Claude Code(E:\Coding Infra 세션)
- **어디서**: 브랜치 `feat/aiuw-improve-260930`, 워크트리 `E:\Coding Infra\Harrness Eng\SimonK-stack-aiuw-improve-260930`(node_modules는 그 워크트리에 따로 설치, junction 아님). `3a19dd1`(아래 Codex 블록) 위에 커밋 6개. main은 09.20 이후 위젯 커밋 0개 — 09.23~30 스택 16개 전부 브랜치에만 있다
- **지금까지**: 09.23~30 다른 세션 커밋 10개가 이 파일·STATE에 없어서 복원해 STATE에 적었다. 이번 세션: Antigravity 5xx 1회 재시도(`51aee9b`), Codex rateLimits 20초 한도·실패 단계 로그·일시 오류 1건 유예(`1d70eba`, 09.28 34건의 원인 = rateLimits 응답만 10초 초과), Grok Bot 리셋 카운트다운·On-demand·소진 경고·Spending 링크·미터 구분 안내(`f7e411b`, `docs/GROK-BOT.md` 전면 갱신), 새 모델 알림 출처별 상태 표시(`9ff57d3`), Grok Bot 안내 접기(`bf5dd38`). `pnpm verify` 0(638테스트)·build 0·smoke ok, 오프스크린 캡처로 화면 확인. DECISIONS에 결정 5줄 + 시각 정정 1줄(추정 시각을 적었던 것을 정정)
- **다음 1개**: 사용자가 다시 붙일 Cursor Spending·grok 화면 캡처로 Grok Bot 카드 필드·라벨과 위젯 Grok 카드 값을 대조
- **막힌 것**: 캡처 미수신. PR(스택 16개 → main, merge commit)·설치는 사용자 확인 대기
- **TODO**: STATE "다음" 절 그대로(설치 후 Codex `phase`·Antigravity `reasonField` 관찰, 새 모델 알림 끄기 설정 검토, Grok CLI `unified.jsonl` 누적, Codex 플러그인 카탈로그 27MB)
- **미해결 질문**: Q-260930-01 새 모델 알림 끄기 설정을 넣을까(지금은 끌 수 없음, 공개 페이지 8곳을 6시간마다 조회) — 안 정하면 막히는 것 없음, 3회 이월 시 폐기 제안
- **작업 규칙 변화**: 화면 확인은 리포 밖 오프스크린 캡처(보이지 않는 Electron 창 + 번들을 127.0.0.1로 서빙 + 가짜 preload로 상태 주입, `window-all-closed` 무시 필요). 커밋 메시지·DECISIONS를 PowerShell 큰따옴표 문자열로 쓰면 `` `a `` 같은 이스케이프가 제어 문자를 넣는다 — 작은따옴표 문자열 또는 Edit 도구
- **요청**: REQ-260930-01 Cursor Spending·grok 화면 캡처 2장을 `/goal` 인자가 아닌 일반 메시지로 첨부(`/goal` 인자에 붙인 이미지는 텍스트만 남음)

## 26.09.30 15:37 KST
- **목적**: Grok Bot의 SuperGrok Heavy 주간 사용량을 AI Usage Widget에서 확인
- **최종 갱신**: 26.09.30 15:37 KST · Codex
- **지금까지**: 사용자의 직접 요청으로 Grok Bot 주간 미터를 별도 카드로 추가했다. 공식 앱에서 수동 입력한 사용률과 남음을 작업표시줄에 표시하고 출처·기록 시각·24시간 오래됨·7일 만료를 표시한다. Grok Build CLI 사용량과 섞지 않는다. 사용법은 `docs/GROK-BOT.md`.
- **다음 1개**: 개인 계정용 공식 주간 사용량 인터페이스가 나오면 수동 입력을 자동 조회로 교체한다.

## 26.09.20 17:16 KST
- **목적**: v1 위젯을 소스 프로젝트로 재구성. 위젯 새로고침 버튼, Grok 구독 한도, 공식 CLI 로그인 위임 기반 다중 계정, Windows 테마, v1 문제 전부 해결
- **최종 갱신**: 26.09.20 17:16 KST · Claude Code(E:\Coding Infra 세션)
- **지금까지**: 사용자 T8 전 항목 OK·결정 4건 확정. **설치 완료**(`%LOCALAPPDATA%\Programs\ai-usage-widget`, 자동 시작 경로 자동 교정), **v1 정리 완료**(Run 값 제거, 폴더·userData 휴지통). 원인 규명 2건: Codex 2번째 `login-failed` = 로그인 완료 직후 account/read가 옛 상태(재조회 + 성공 신뢰, 정황 근거), agy 1회 실패 = 규명 불가(진단 로그 보강). **리포 통합**: 이 폴더는 이제 공개 리포 SimonK-stack의 `apps/ai-usage-widget/`이고 설치는 `skills-src/ai-usage-widget-install`이 한다. `pnpm verify` 0(577테스트), 스택 CI 게이트 PASS
- **다음 1개**: 없음(운영 단계). 실패 로그가 다시 나오면 STATE "다음"의 두 항목을 확정
- **막힌 것**: 없음
- **작업 규칙 변화**: 공개 리포라 커밋 전 식별자 확인, 스택 리포 동시 작업 규칙(fetch 먼저·경로 명시 add·워크트리)은 `CLAUDE.md`에 추가됨. 옛 단독 폴더 `E:\Coding Infra\dev\ai-usage-widget`는 `Legacy-` 접두로 남김(삭제는 사용자 판단)
- **요청**: 없음

## 26.09.20 11:00 KST
- **목적**: v1 위젯을 소스 프로젝트로 재구성. 위젯 새로고침 버튼, Grok 구독 한도, 공식 CLI 로그인 위임 기반 다중 계정, Windows 테마, v1 문제 전부 해결
- **최종 갱신**: 26.09.20 11:00 KST · Claude Code(E:\Coding Infra 세션)
- **지금까지**: 공급자 4종이 실계정으로 표시됨(사용자 확인). 이번 라운드: Grok 0% 해석 확증(`creditUsagePercent` 29% 등장), Codex는 서버가 주간 창만 줌(정상), Codex 첫 로그인 `protocol-error` = 같은 CODEX_HOME에서 app-server 두 개가 겹친 경합 → `quiesce` 수정 + 재현 테스트, 자동 조회 공급자별 최소 간격(claude 15·codex 60·grok 60·antigravity 120초), T8 부분 실측(창 위치·topmost·Run 키), NSIS 설치 파일 빌드 확인(실행 안 함). `pnpm verify` 0(571테스트) / dist:dir 0 / 배포본 스모크 0
- **다음 1개**: 사용자와 T8 나머지(팝업 blur·전체화면 숨김·재질·테마 전환·슬라이더·자동 시작) → SEC-06 결정 → NSIS 설치(사용자 확인) → v1 정리(사용자 확인)
- **막힌 것**: 사용자 결정 4건(P-08 보조 모니터, SEC-06 제거 시 statusLine 복원, 코드 서명, Antigravity 막대 그룹) / 원격 저장소 없음
- **실측 도구**: 공급자 실제 응답을 볼 때는 어댑터 모듈을 esbuild로 묶어 위젯 계정 폴더로 직접 호출(세션 스크래치패드의 `grok-probe.cjs`·`codex-probe.cjs` 방식, 토큰·이메일 마스킹). 응답에 accountId 같은 식별자가 섞여 나오므로 보고서·커밋에는 옮기지 않는다
- **요청**: 없음

## 26.09.20 09:58 KST
- **목적**: v1 위젯을 소스 프로젝트로 재구성. 위젯 새로고침 버튼, Grok 구독 한도, 공식 CLI 로그인 위임 기반 다중 계정, Windows 테마, v1 문제 전부 해결
- **최종 갱신**: 26.09.20 09:58 KST · Claude Code(E:\Coding Infra 세션)
- **아이콘(09:58)**: Codex·Grok = 공식 SVG 경로(`src/renderer/src/brand-marks.ts`, 출처 URL 주석)를 투명 배경·`currentColor`로 그림. 색 규칙은 `styles.css`의 `.ai-brand-icon` 한 곳(`--p-fg` → `--w-fg` → `--text-main` 순 폴백)이라 새 테마는 이 변수만 정의하면 된다. 색이 있는 브랜드(Claude·Antigravity)만 PNG. 새 공급자 아이콘도 같은 규칙: 공식 도메인에서 받고 출처를 DECISIONS에 남긴다(DECISIONS 26.09.20 08:57·09:54)
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

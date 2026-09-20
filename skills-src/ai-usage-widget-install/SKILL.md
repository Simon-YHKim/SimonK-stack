---
name: ai-usage-widget-install
description: "Use when the user wants the AI Usage Widget (the Windows taskbar widget in apps/ai-usage-widget that shows Claude, Codex, Grok and Antigravity subscription usage) installed, updated, checked or removed - triggers \"AI 사용량 위젯 설치\", \"사용량 위젯 깔아줘\", \"위젯 업데이트\", \"위젯 재설치\", \"위젯 상태 확인\", \"위젯 제거\", \"install the usage widget\", \"update the usage widget\", \"/ai-usage-widget-install\". Produces a verified per-user install built from source (pnpm install, verify gate, silent NSIS install, launch check), a status report (installed exe, processes, autostart target, Claude bridge, provider CLIs), and a guarded uninstall that refuses while the Claude statusline bridge is still installed. NOT for changing the widget's code (work in apps/ai-usage-widget and read its CLAUDE.md first) and NOT for signing in - browser sign-in and device codes stay with the user."
allowed-tools: Read, Bash, PowerShell
version: 1.0.0
author: simon-stack
---

# ai-usage-widget-install - AI 사용량 위젯 설치·갱신·점검·제거

Windows 작업 표시줄 옆에 Claude·Codex·Grok·Antigravity 구독 사용량을 띄우는 위젯(`apps/ai-usage-widget`)을
**소스에서 빌드해 사용자 전용으로 설치**한다. 설치 파일을 어디서 받아 오지 않는다 - 검증 게이트를 통과한
소스만 설치한다.

## 언제 쓰나

- "AI 사용량 위젯 설치해줘 / 깔아줘", "위젯 업데이트·재설치", "install the usage widget"
- "위젯 떠 있나 확인해줘", "자동 시작이 어디를 가리키지?" → `-Status`
- "위젯 지워줘" → `-Uninstall` (아래 안전장치 먼저 읽기)

위젯 **코드를 고치는 일**은 이 스킬이 아니다. `apps/ai-usage-widget/CLAUDE.md`의 고정 읽기 목록
(`CLAUDE.md` → `DECISIONS.md` → `STATE.md` → `docs/HANDOFF.md`)부터 읽고 그 폴더에서 작업한다.

## 실행

스크립트 하나가 전부 한다. Windows PowerShell 5.1에서도 돈다(ASCII 전용).

```powershell
$s = "E:\Coding Infra\Harrness Eng\SimonK-stack\skills-src\ai-usage-widget-install\scripts\install-widget.ps1"

& $s -Status      # 아무것도 바꾸지 않고 현재 상태만
& $s -DryRun      # 무엇을 할지와 사전 점검만
& $s              # 설치 또는 갱신
& $s -Uninstall   # 제거 (브리지가 남아 있으면 거절, exit 3)
```

| 옵션 | 뜻 |
|---|---|
| `-Source <폴더>` | 위젯 소스 폴더를 직접 지정. 생략하면 ① 이 스크립트가 든 SimonK-stack 체크아웃 ② `$env:SIMONK_STACK_ROOT` ③ `E:\Coding Infra\Harrness Eng\SimonK-stack` ④ 공개 리포를 `%LOCALAPPDATA%\AIUsageWidget\src`에 얕게 클론 |
| `-SkipVerify` | `pnpm verify` 생략. **사용자가 명시적으로 요청했을 때만.** 기본은 검증 통과가 설치 조건 |
| `-NoLaunch` | 설치 후 실행하지 않음 |
| `-Force` | `-Uninstall`의 브리지 안전장치를 넘김. 사용자 확인 없이 쓰지 않는다 |

종료 코드: `0` 성공 · `1` 단계 실패 · `2` 전제 미충족(node·pnpm·git 없음 등) · `3` 안전상 거절.

## 설치가 하는 일 (순서 고정)

1. `node`·`pnpm`·`git` 확인, 소스 폴더 결정
2. `pnpm install --frozen-lockfile` (폴더를 옮긴 뒤 깨진 `node_modules`는 자동으로 비우고 다시 설치)
3. `pnpm verify` = typecheck + lint + test. **실패하면 여기서 멈춘다** - 실패 출력을 그대로 보고한다
4. 실행 중인 위젯 종료(설치본과 개발 빌드의 exe 이름이 같아 둘 다 닫아야 패키징됨)
5. `pnpm dist` → `release\ai-usage-widget-setup-<버전>.exe` (서명 없음, 사용자 전용 NSIS)
6. 설치 파일 `/S` 실행 → `%LOCALAPPDATA%\Programs\ai-usage-widget\`
7. 설치본 실행 후 `-Status`와 같은 점검을 출력

계정·설정(`%APPDATA%\AIUsageWidgetV2`)과 CLI 로그인 폴더(`%LOCALAPPDATA%\AIUsageWidget`)는 설치·제거와
무관하게 남는다. 그래서 갱신해도 다시 로그인할 필요가 없다.

## 보고할 때 반드시 확인할 것

스크립트가 `done`을 찍었다고 끝이 아니다. 마지막 상태 블록에서 세 가지를 읽고 보고한다.

- `running` 경로가 **설치본**(`%LOCALAPPDATA%/Programs/ai-usage-widget/`)인가. 개발 빌드 경로면 옛 프로세스가 남은 것
- `autostart`가 설치본을 가리키는가. 다른 exe를 가리키면 설치본을 한 번 실행하면 앱이 스스로 다시 등록한다
  (켜 둔 사용자에게만 해당. 작업 관리자에서 끈 항목은 앱이 건드리지 않는다)
- `cli ...` 줄에 `(not on PATH)`가 있으면 그 공급자 카드는 "CLI 없음"으로 뜬다. 위젯 [계정 관리] 탭의
  [CLI 설치 안내 열기]가 공식 문서를 연다

## 설치 뒤 사용자 몫 (대신 하지 않는다)

- **로그인**: 위젯 → [계정 관리] → 공급자별 [계정 추가] → [로그인]. 브라우저 로그인과 기기 코드 입력은 사용자가 한다.
  Antigravity는 위젯 로그인이 없다 - 터미널에서 `agy`로 로그인해 둔 상태를 그대로 쓴다(계정 1개)
- **Claude 수치**: 평소 쓰는 `~/.claude`에 브리지가 있어야 들어온다. [계정 관리] → Claude → [기본 Claude 프로필에 설치].
  기존 statusLine 명령(예: Orca 훅)은 감싸서 보존하고 `settings.json.aiuw-backup-*`를 남긴다

## 제거 안전장치

제거 프로그램은 `~/.claude/settings.json`의 statusLine을 **되돌리지 않는다**(결정: apps/ai-usage-widget/DECISIONS.md
26.09.20 11:43). 브리지가 설치된 채 앱만 지우면 Claude Code 상태줄이 사라진 스크립트를 계속 부른다.
그래서 `-Uninstall`은 브리지가 보이면 exit 3으로 거절한다. 사용자에게 위젯에서 [기본 프로필에서 제거]를
먼저 누르게 한 뒤 다시 실행한다. `-Force`는 사용자가 백업에서 직접 복원하겠다고 한 경우에만.

## 하지 않는 것

- 토큰·자격증명 파일을 읽거나 옮기지 않는다. `accounts.json`에는 토큰이 없고, CLI 로그인 폴더는 열어 보지 않는다
- 코드 서명·배포를 하지 않는다(설치 파일은 서명 없음 - SmartScreen 경고는 정상)
- v1(`AI Usage Widget 1.0.2`) 같은 다른 위젯을 지우지 않는다. 그건 사용자 확인이 필요한 별개 작업

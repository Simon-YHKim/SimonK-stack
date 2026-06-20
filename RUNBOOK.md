---
owner: claude
note: "정본=PROTOCOL.md. 이 파일은 PROTOCOL §28(운영안전)·§13(pause)의 prose를 'FAIL 신호 -> 복구 명령' 룩업표로 옮긴 운영 런북. 충돌 시 PROTOCOL 우선."
last-sync: 2026-06-14
---

# RUNBOOK.md — 허브 장애 복구 룩업 (FAIL 신호 → 명령)

> **목적**: 무인 운용 중 `hub-health.ps1`/`monitor.ps1`가 뱉는 FAIL 신호를, 사람이 PROTOCOL을 다시 읽지 않고도 **즉시 복구 명령**으로 바꾼다.
> **사용**: 모든 경로는 `E:\Coding Infra\AI Infra\Communication` 기준. PowerShell에서 실행.
> **원칙**: 파괴적(`reset --hard`·force-push·대량삭제)·실비용·secrets 명령은 **항상 Simon 확인**(PROTOCOL §11-5) — 아래 ⚠ 표기.

## 0. 첫 진단 (무엇이 깨졌나)
```
powershell -ExecutionPolicy Bypass -File tools\hub-health.ps1          # 19개 read-only 셀프테스트
powershell -ExecutionPolicy Bypass -File tools\monitor.ps1             # 실시간 state·cyc·pend·데몬
```
`-Json`을 붙이면 머신 판독(와치독·스크립트용).

## 1. FAIL → 복구 룩업표

| FAIL 신호 (hub-health / monitor) | 원인 | 복구 명령 |
|---|---|---|
| **models.json best-model contract FAIL** | 모델 id가 정본(MODELS.md)과 불일치 (refresh 제안이 잘못 적용/환각 id) | `MODELS.md` 정본 표와 `tools\models.json` 대조 → Edit로 교정 → `hub-health.ps1`로 재확인. 제안본은 `tools\models.proposed.json` |
| **daemon-log stale (mtime > N분)** | 데몬 hang 또는 죽음 (단, 로그 mtime만으론 hang 구분 불가) | `tools\hub-daemon.ps1` 살아있는 PID 확인(아래 §2) → 없으면 재기동(HUB-STARTUP 모드 A) |
| **commit guard 구문 FAIL** | `commit.ps1`/`hub-daemon.ps1` 등 스크립트 PowerShell 구문 깨짐 | `powershell -NoProfile -Command "[void][ScriptBlock]::Create((Get-Content tools\<file>.ps1 -Raw))"` 로 파싱 검증 → Edit 수정 |
| **상태파일 U+FFFD / cp949 손상** | `Out-File`/`Set-Content` 라운드트립으로 한글 깨짐 (§28.1) | `git checkout HEAD~1 -- <file>` 로 복구 → 이후 **Edit/Write로만** 갱신 |
| **STATUS.md size FAIL (>256KB)** | append 무한증식 (§28 commit guard) | 내용 잘라내기 → `.gitignore`된 `*.log`로 회전. 상태 보드는 작게 유지 |
| **pend ≥ 3 (RED, monitor)** | Claude 머지 백로그 적체 — 미처리 outbox ≥3 | Claude 머지 sweep(§34.3 cherry-pick) 또는 charter throttle(미머지 8↑ 발견중지) |
| **CONTROL.state 불명/혼선** | STATUS=paused vs CONTROL=running 불일치 | `CONTROL.md`가 런-스테이트 **정본**. STATUS는 요약일 뿐 → CONTROL 기준으로 행동 |
| **release-gate NO-GO** | 2nd-B verify FAIL / tree dirty / rollback SHA 없음 | 머지 **금지**. `tools\release-gate.ps1` reasons 확인 → 원인 수정 후 재실행. ⚠ 절대 NO-GO 우회 머지 금지(#222 교훈) |
| **leaderless (Claude 행 죽음 + CONTROL=running)** | 오케스트레이터 세션 종료인데 게이트가 살아있다고 표시 | §2 데몬 정지 → Claude 재기동 → CONTROL 재확인. 와치독(Grok)이 `incident` 올리면 우선 처리 |

## 2. 데몬 생존 / 정지 (자주 쓰는 것)
```
# 살아있는 데몬 + PID
Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" |
  Where-Object { $_.CommandLine -match 'hub-daemon\.ps1' } |
  ForEach-Object { if($_.CommandLine -match '-Only (\w+)'){ "ALIVE: $($matches[1]) (PID $($_.ProcessId))" } }

# 전체 데몬 정지 (재기동 전)
Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" |
  Where-Object { $_.CommandLine -match 'hub-daemon\.ps1' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```
재기동은 `HUB-STARTUP.html` 모드 A(백그라운드 데몬) 또는 모드 B(인-윈도우 루프).

## 3. pause / resume (§13)
- **정지**: `CONTROL.md`의 `state: paused` + `pause_reason` + `updated`(실시각 KST) → `commit.ps1 -As claude`. 각 AI는 다음 루프에서 현재 사이클만 마무리 후 대기.
- **재개**: `state: running` 복원 + `resume_reason`. 새 환경이면 경로 먼저 확인.
- **예산 폭주 kill-switch**(§28.7): `state: paused` + `reason: budget` 자동 기록 → 전 AI 정지 → 재개는 Simon 승인.

## 4. 커밋 함정 (복구 중 재발 방지)
- 커밋 메시지 본문에 `"`(큰따옴표)·em-dash 금지(§28.2) → word-split pathspec 실패. 필요 시 `git commit -F <tempfile>`.
- `git add -A`/`git add .` 금지(§1 single-writer) → 낯선 파일 휩쓸림. **명시 경로만** stage. 허브 커밋은 `tools\commit.ps1 -As <ai> -Files ...`.
- 푸시 경고에 낯선 파일명 보이면 즉시 `git show --stat`로 확인.

## 5. 인시던트 기록
복구 후 한 줄을 `INCIDENTS.md`(append-only)에 남긴다: `[YYYY-MM-DD / HH:MM:SS KST] | 신호 | 원인 | 복구 | 재발방지`. 반복 패턴은 SimonKWiki 교훈(§18)으로 승격.

## 6. 반복 패턴 룩업 (O-15 — hub-health/와치독 FAIL → 복구)
- **데몬 중복** (monitor `loops`에 각 AI 2개+): 후발 PID kill — `Get-CimInstance Win32_Process | ? { $_.CommandLine -match 'hub-daemon\.ps1' } | Sort CreationDate | Select -Skip 1 | % { Stop-Process $_.ProcessId -Force }`. 재발방지=hub-daemon.ps1 lane(-Only) named-mutex 가드(중복이면 자동 exit 0). 재기동은 HUB-STARTUP 모드A "이미 떠있으면 skip".
- **STATUS.md 비대** (commit.ps1 `[SIZE] ... STATUS cap`): 해당 AI가 STATUS를 최신 N줄만 남기고 과거를 `agents/<ai>/*-status-archive.log`(gitignored)로 회전 후 재커밋. 캡=64KB(`commit.ps1 $StatusLimitBytes`).
- **UTF-8 BOM** (hub-health `no-BOM integrity FAIL`): `$c=[IO.File]::ReadAllText($f); [IO.File]::WriteAllText($f,$c,(New-Object Text.UTF8Encoding $false))`. 쓰기 측은 `Set-Content -Encoding utf8`(PS5.1=BOM)을 `[IO.File]::WriteAllText(...,UTF8Encoding($false))`로 교정(hub-watchdog 적용 완료).
- **frontmatter malformed** (hub-health WARN): 신규 메시지는 `to/from/type/ts` 필수키 준수. 기존은 비차단 — 점진 정리.

## 7. 에뮬레이터 dev 서버 연결 (O-26 — "Cannot connect to Expo CLI" 재발방지)
**증상**: 안드로이드 에뮬 콘솔 `Cannot connect to Expo CLI` / `10.0.2.2:8081` / `Error: undefined`. 앱버그 아님 = 에뮬이 PC Metro(8081)에 못 붙음. (Reanimated `Reduced motion` 경고는 무관 — 에뮬 '동작 줄이기' OFF 권고.)
**해결 = 매 네이티브/에뮬 QA 사이클 시작 전 pre-QA 보장 스크립트 실행(수동 1회성 adb reverse 금지)**:
```
pwsh -File E:\2ndB\scripts\pre-emulator-qa.ps1 -StartMetro
```
스크립트가 4조건 보장(exit 0이면 OK): ①adb 해석(PATH 또는 `%LOCALAPPDATA%\Android\Sdk\platform-tools`) ②에뮬 `device` 인식(`adb devices`) ③Metro `packager-status:running`@8081(없고 `-StartMetro`면 `npx expo start` 자동기동) ④`adb reverse tcp:8081 tcp:8081`(에뮬 재시작·Metro 재시작 시 소실되므로 멱등 재설정). **함정**: Metro `/status`는 Content-Type 없어 PS `Invoke-WebRequest`가 Content를 byte[]로 줌 → 문자열 match 전 `[Text.Encoding]::ASCII.GetString()` 디코딩 필수(스크립트 반영됨). exit 2=adb없음·3=에뮬없음(부팅)·4=Metro없음(-StartMetro)·6=reverse실패.

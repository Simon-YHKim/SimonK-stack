# DESIGN — AI Usage Widget v2
> 원본(손으로 고치는 문서). 작성 2026-09-15 03:12 KST · 발행 Claude Code(스캐폴딩 에이전트)
> 결정의 근거는 `DECISIONS.md`, 사실의 근거는 `docs/RESEARCH-auth-quota.md`, v1 동작은 `docs/SPEC-v1-baseline.md`에 있다. 이 문서는 그 셋을 코드 구조로 옮긴 설계다. 충돌하면 `DECISIONS.md`가 우선한다.

읽는 순서: §1 목표 → §2 구조 → §5 계약 → 자기 모듈 절(§7 공급자 / §8 셸 / §9 렌더러) → §13 소유권.

---

## 1. 목표와 범위

| 사용자 요청 | 설계 반영 위치 |
|---|---|
| (1) 작업 표시줄 위젯 자체의 새로고침 버튼(팝업 없이 동작) | 렌더러 위젯 막대의 버튼 → `usage:refresh-now` → 셸 스케줄러. 진행 상태는 `AppStateSnapshot.refresh`(V1-23) |
| (2) Grok 구독 한도 | `providers/grok` — 계정별 `GROK_HOME` + 공식 `grok agent stdio`(ACP)의 `x.ai/billing`만 사용 |
| (3) 공식 CLI 로그인 위임 + 공급자별 다중 계정 | 계정마다 격리 폴더(`CLAUDE_CONFIG_DIR` / `CODEX_HOME` / `GROK_HOME`). 로그인·토큰 갱신은 CLI가 하고 위젯은 토큰을 읽지 않는다 |
| (4) v1 문제 전부 해결 | §12 표에서 V1-01~43을 모듈에 배정 |
| (5) Windows와 어울리는 테마 | `ThemeTokens`(라이트/다크·강조색·고대비·투명도 감소). 재질 Mica/Acrylic은 옵션, 기본 off(DECISIONS 02:23) |

범위 밖: Gemini CLI·Antigravity 카드(DECISIONS 02:23), Orca 연동, 코드 서명, 앱 내 OAuth 서버.

---

## 2. 아키텍처

```
┌──────────────────────────── Electron main (Node 24.20, Electron 44.3.0) ────────────────────────────┐
│                                                                                                     │
│  index.ts (bootstrap: userData 경로, 단일 인스턴스, app:// 프로토콜, 보안 훅)                          │
│     │                                                                                               │
│     ├─ ipc/dispatch ── 발신 프레임 검증 → shared/ipc 검증기 → 핸들러 → IpcResult                     │
│     ├─ store/      settings.json · accounts.json (원자적 쓰기, normalizeSettings)                    │
│     ├─ scheduler/  주기·수동 새로고침, 계정별 병렬, 백오프, 결과 즉시 브로드캐스트                      │
│     ├─ login/      로그인 세션(sessionId), 붙여넣기 전달, 로그인 URL 검증 후 openExternal              │
│     ├─ windows/ tray/ platform/{theme,taskbar,zorder(koffi user32)}                                   │
│     │                                                                                               │
│     └─ providers/registry ─┬─ claude  ─┐                                                            │
│                            ├─ codex   ─┼─ cli/spawn (shell:false, env 화이트리스트, 트리 kill)        │
│                            └─ grok    ─┘        │                                                   │
└─────────────────────────────────────────────────┼───────────────────────────────────────────────────┘
          ▲ state:changed / theme:changed / login:event │ 자식 프로세스(계정별 격리 HOME)
          │ invoke(허용 채널만)                         ▼
┌─────────┴──────────┐                    claude.exe auth login|status   (CLAUDE_CONFIG_DIR)
│ preload (sandbox)  │                    node codex.js app-server       (CODEX_HOME)
│ window.aiUsage     │                    grok.exe login|agent stdio     (GROK_HOME)
└─────────┬──────────┘
┌─────────┴──────────────────────────┐
│ renderer ×2 (app://bundle, CSP 헤더) │  widget(?view=widget) · popup(?view=popup)
└────────────────────────────────────┘
```

---

## 3. 프로세스 모델

| 프로세스 | 수 | 권한 | 역할 |
|---|---|---|---|
| main | 1 | Node 전체 | 상태 소유, 파일, 자식 프로세스, 창·트레이, koffi FFI |
| renderer | 2(widget, popup) | `sandbox:true`, `contextIsolation:true`, `nodeIntegration:false` | DOM 표시만. 토큰·경로·원본 이메일을 받지 않는다 |
| preload | 창마다 1 | sandbox preload(CJS 번들, `require('electron')`만) | `window.aiUsage = { invoke, on }`. 채널 이름을 허용 목록으로 거른다 |
| CLI 자식 | 조회·로그인마다 | 부모 환경의 화이트리스트만 상속 | 단발 실행(`run`)은 종료까지, 상주형(`spawnLongLived`)은 JSON-RPC 대화 후 kill |

- 퓨즈 `runAsNode:false` 때문에 Electron 실행 파일을 Node로 쓸 수 없다. npm shim(codex)은 **시스템 node.exe + JS 엔트리**로 실행한다(`cli/resolve.ts`). node가 없으면 `node-not-found`로 표시한다.
- 자식 프로세스는 `src/main/cli/spawn.ts`만 만든다. ESLint `no-restricted-imports`가 그 밖의 `child_process` import를 막는다.

---

## 4. 데이터 폴더

| 경로 | 내용 | 비고 |
|---|---|---|
| `%APPDATA%\AIUsageWidgetV2\` (userData) | `settings.json`, `accounts.json`, `logs\main.log`(1MB×3 회전, 마스킹) | `app.setPath('userData')`를 ready 전에 명시. v1의 `ai-usage-taskbar-widget`과 분리 |
| `%LOCALAPPDATA%\AIUsageWidget\profiles\<provider>\<accountId>\` | 계정별 CLI 홈(CLI가 자격증명을 여기에 쓴다) | 로밍 폴더 밖. ACL은 사용자 프로필 기본값. `profileDirFor()`가 id 패턴·루트 이탈을 검사 |
| `%LOCALAPPDATA%\AIUsageWidget\bridge\` | Claude statusline 브리지 기록(`claude\<accountId>.json` 등, claude 모듈이 확정) | 토큰 없음. `rate_limits`만 |
| `<resources>\resources\` | 트레이·공급자 아이콘, `claude-bridge\` 스크립트 | 개발: `<appPath>\resources`, 배포: `process.resourcesPath\resources`(`resolveResourcesDir`) |
| 설치 | `%LOCALAPPDATA%\Programs\AI Usage Widget\ai-usage-widget.exe` | NSIS oneClick per-user. exe 이름을 v1(`AI Usage Widget.exe`)과 다르게 해 프로세스를 구분 |

- `accounts.json`에 저장된 `profileDir`는 신뢰하지 않는다. 로드할 때 `profileDirFor(profilesRoot, provider, id)`로 다시 계산한다(셸 store 규칙).
- `--smoke` 또는 `--user-data-dir`로 실행하면 userData를 그 경로(없으면 임시 폴더)로, local 데이터 루트를 `<userData>\local`로 바꿔 실제 프로필을 건드리지 않는다.

---

## 5. 계약(Contracts)

모듈은 계약 파일을 고치지 않는다. 필요한 변경은 작업 보고서의 "계약 변경 요청"에 적고, 통합 단계에서 반영한다(§13).

### 5-1. `src/shared/types.ts`
- `ProviderId = 'claude'|'codex'|'grok'`.
- `Account { id, provider, label, enabled, order, profileDir(main 전용), createdAt }` / `AccountDTO { id, provider, label, enabled, order, emailMasked?, plan?, loginState }`. 변환은 반드시 `toAccountDTO()`(필드를 명시적으로 골라 새 필드가 새지 않게 함).
- `QuotaWindow { kind:'session'|'weekly'|'other', usedPercent:number|null, resetsAt:number|null(epoch ms), windowMinutes:number|null, label? }`. **모르는 값은 null이며 0으로 쓰지 않는다.**
- `UsageSnapshot { accountId, provider, state, windows, plan?, measuredAt, lastSuccessAt, errorCode?, source }`
  - `state`: `ok` 측정 성공 / `stale` 오래됨 / `loading` 첫 조회 중 / `error` 실패(윈도우는 마지막 실측값일 수 있음) / `unavailable` 공급원이 수치를 주지 않음 / `logged-out` / `reset` 모든 창의 리셋 시각이 지남.
  - `source`: `'codex-app-server'|'claude-statusline'|'grok-acp'`.
- `ErrorCode`(20종): 렌더러는 코드만 받아 i18n 문구로 바꾼다. 공급자 원문 오류는 UI로 가지 않는다.
- `LoginEvent`: `url` / `device-code {userCode, verificationUrl, expiresAt?}` / `needs-paste` / `progress {stage}` / `success {emailMasked?, plan?}` / `error {code}`. IPC에서는 `LoginEventMessage { sessionId, accountId, at, event }`.
- `ThemeTokens { scheme, taskbarScheme, highContrast, accent('#rrggbb'), reducedTransparency, effectiveMaterial }`.
- `AppStateSnapshot { locale, settings, accounts, usage, refresh, theme, cli }` — 렌더러가 받는 유일한 상태.

### 5-2. `src/shared/settings.ts`
v1 키(SPEC §1-2) 중 의미가 남은 것 + v2 추가. mock 관련 키는 없다.

| 키 | 기본 | 허용 | 비고 |
|---|---|---|---|
| `theme` | `windows` | `windows`,`1a`~`1d` | `windows`가 새 기본 |
| `iconStyle` | `color` | `color`,`monochrome` | |
| `alignment` | `right` | `right`,`left` | |
| `offsetPx` | 20 | 정수 0~350 | |
| `verticalOffsetPx` | 0 | 정수 -40~40 | v1은 UI·범위 없음(V1-38) |
| `refreshIntervalSec` | 60 | 15/30/60/120/300 | NaN 등은 거부(V1-20) |
| `alphaPercent` | 85 | 정수 10~100 | 문구를 "카드 배경 불투명도"로 정정(V1-35) |
| `showWeeklyLimit` | true | bool | UI 노출(V1-38) |
| `colorByUsage` | true | bool | |
| `showCardBackground` | true | bool | 기본값 단일 정의(V1-41), floating 강제 변경은 UI에 표시 |
| `showUsedPercent` | false | bool | |
| `placementMode` | `docked` | `docked`,`floating` | |
| `alwaysOnTop` | true | bool | |
| `openAtLogin` | **false** | bool | v1 기본 ON 동의 없음(V1-14) |
| `material` | `none` | `none`,`mica`,`acrylic` | |
| `language` | `auto` | `auto`,`ko`,`en` | `auto`: OS 로케일이 `ko*`면 ko, 아니면 en |

- `parseSettingsPatch(input)`: 알 수 없는 키·잘못된 값이 하나라도 있으면 전체 거부. 빈 patch도 거부.
- `normalizeSettings(raw)`: 디스크 값 로드용. 기본값에서 시작해 유효한 키만 덮는다. 절대 throw하지 않는다.
- `applySettingsPatch(base, patch)`: 병합만 한다(숨은 강제 규칙 없음).

### 5-3. `src/shared/ipc.ts`
모든 invoke는 `IpcResult<T> = {ok:true,value} | {ok:false,error:{code:IpcErrorCode, detail?:ErrorCode}}`로 끝난다. 예외는 브리지를 건너지 않는다.

| 채널(renderer→main) | 요청 | 응답 | 검증 규칙 |
|---|---|---|---|
| `app:get-state` | null | `AppStateSnapshot` | |
| `app:renderer-ready` | `{view, rendered, cspEnforced}` | null | 스모크 판정용 |
| `settings:get` | null | `Settings` | |
| `settings:update` | `{patch}` | `Settings` | `parseSettingsPatch` |
| `accounts:list` | null | `AccountDTO[]` | |
| `accounts:add` | `{provider, label}` | `AccountDTO` | provider 열거형, label 1~64자·제어/양방향 문자 제거 |
| `accounts:remove` | `{accountId}` | null | id `^[A-Za-z0-9_-]{1,64}$` |
| `accounts:rename` | `{accountId, label}` | `AccountDTO` | |
| `accounts:toggle` | `{accountId, enabled}` | `AccountDTO` | |
| `accounts:reorder` | `{accountId, direction:'up'|'down'}` | `AccountDTO[]` | |
| `login:start` | `{accountId}` | `{sessionId}` | |
| `login:cancel` | `{sessionId}` | null | |
| `login:submit-paste` | `{sessionId, text}` | null | 1~4096자, 줄바꿈 금지, 앞뒤 공백 제거 |
| `usage:refresh-now` | `{accountId:string|null}` 또는 null | null | null = 활성 계정 전체 |
| `shell:open-external` | `{kind:'link', key}` 또는 `{kind:'login', sessionId, url}` | null | key 열거형. login은 https·자격정보 없는 URL·2048자 이하. **main은 그 URL이 해당 세션이 방출한 URL인지 다시 확인한다** |
| `window:toggle-popup` | null | null | |
| `window:show-popup` | `{tab:PopupTab|null}` | null | 빈 상태 클릭 시 `accounts` 탭(V1-35·43) |
| `window:hide-popup` | null | null | |
| `window:set-popup-lock` | `{locked}` | null | 설정 조작 중에만 잠금(V1-09) |
| `window:resize-widget` | `{width, height}` | null | 유한 양수. main이 `clampWidgetSize`(32~1200 × 24~120)로 제한(V1-20) |
| `claude-bridge:status` | null | `ClaudeBridgeStatus` | |
| `claude-bridge:install-default` | `{accountId}` | `ClaudeBridgeStatus` | 사용자 확인 대화 후에만 호출 |
| `claude-bridge:uninstall-default` | null | `ClaudeBridgeStatus` | |

| 이벤트(main→renderer) | 페이로드 |
|---|---|
| `state:changed` | `AppStateSnapshot` |
| `theme:changed` | `ThemeTokens` |
| `login:event` | `LoginEventMessage` |

- `IpcErrorCode`: `invalid-request` `forbidden-sender` `not-found` `conflict` `busy` `not-implemented` `internal`.
- 발신자 검증(`ipc/dispatch.ts`): 최상위 프레임 URL이 `app://bundle/…`(개발 시 dev server origin)일 때만 처리한다. 하위 프레임은 거부.
- `EXTERNAL_LINK_KEYS`(`claude-cli-install` `codex-cli-install` `grok-cli-install`)의 실제 URL 표는 셸이 main에 두며, 공식 문서에서 확인한 https 주소만 넣는다.

### 5-4. `src/shared/i18n/`
- `ko.ts`가 키 집합의 원본, `en.ts`는 `Record<keyof typeof ko, string>`이라 키가 어긋나면 typecheck가 실패한다. 테스트가 키 집합·자리표시자 일치·빈 문구 0건을 확인한다.
- `t(locale, key, params)` / `createTranslator(locale)`. main(트레이)과 렌더러가 같은 사전을 쓰고, 로케일은 main이 정해 스냅샷으로 보낸다(V1-34).
- 유니온→키 표(`ERROR_MESSAGE_KEYS`, `USAGE_STATE_KEYS`, `LOGIN_STATE_KEYS`, `LOGIN_STAGE_KEYS`, `PROVIDER_NAME_KEYS`, `USAGE_SOURCE_KEYS`, `THEME_KEYS`, `MATERIAL_KEYS`, `LANGUAGE_KEYS`, `REFRESH_INTERVAL_KEYS`)는 `Record<Union, MessageKey>`라 새 코드에 문구가 없으면 typecheck가 실패한다.
- v1 86키 대비 변경(§14).

### 5-5. `src/shared/usage.ts`, `validate.ts`, `mask.ts`
- `classifyWindowKind(minutes)`: 300→session, 10080→weekly, 그 외 other. `normalizePercent`(비수치→null, 0~100 clamp), `epochSecondsToMs`.
- `deriveDisplayState(snapshot, now, intervalSec)`: 측정 상태에만 시간 규칙 적용. 모든 창 리셋 경과→`reset`, `max(5분, 주기×3)` 초과→`stale`.
- `applyFetchFailure(prev, failed)`: 실패해도 마지막 실측 창·측정 시각·플랜을 유지(DECISIONS 01:36).
- `createEmptySnapshot`, `formatCountdown`(v1 `j()` 형식), `usageLevel`(≥85 critical, ≥60 warn), `displayPercent`.
- `maskEmail`, `maskSecrets`(JWT·Bearer·sk-/xai- 키·`code=` 등 key=value·이메일·40자 이상 불투명 문자열), `redact`(민감 키 `[redacted]`, 이메일 키 마스킹).

### 5-6. `src/main/providers/types.ts`, `registry.ts`
```ts
interface ProviderAdapter {
  readonly id: ProviderId;
  detectCli(signal?): Promise<CliInfo>;               // {found, path?, version?, errorCode?}
  ensureProfileDir(account): Promise<void>;           // 멱등
  startLogin(account, emit, signal): Promise<void>;   // success 또는 error를 emit한 뒤 resolve
  submitPaste?(account, text): Promise<void>;
  getIdentity(account, signal): Promise<ProviderIdentity>; // {loggedIn, emailMasked?, plan?}
  fetchUsage(account, signal): Promise<UsageSnapshot>;     // 예상 가능한 실패는 snapshot으로 반환
  removeProfile(account): Promise<void>;              // profilesRoot 밖이면 거부
}
interface ClaudeProviderAdapter extends ProviderAdapter { id:'claude'; bridge: ClaudeBridgeController }
```
- `ProviderDeps { logger, now, appVersion, localDataRoot, profilesRoot, bridgeRoot, resourcesDir, homeDir, env }` — 테스트는 임시 폴더를 주입한다. 모든 경로는 주입값에서만 만든다(`os.homedir()` 직접 호출 금지).
- `ProviderError(code)`는 프로그래머 오류나 내부 전달용이다. UI로 가는 실패는 snapshot의 `errorCode`다.
- `registry.ts`는 `providers/<id>/index.ts`의 `create<Id>Adapter`를 import한다. 공급자 모듈은 그 **export 이름과 시그니처를 유지**한 채 내부를 구현한다. 지금 들어 있는 것은 `placeholder.ts` 기반 자리표시자(`not-implemented`, 가짜 수치 없음)다.

### 5-7. `src/main/cli/` (완전 구현, 테스트 포함)
| API | 동작 |
|---|---|
| `buildChildEnv(parent, {allow, remove?, set?})` | 대소문자 무시 화이트리스트 → remove → set 순. `BASE_ENV_ALLOW`는 Windows 기본 변수만(자격증명 변수 없음) |
| `run(cmd, args, {env, cwd?, timeoutMs, signal?, stdin?, maxOutputBytes?})` | `shell:false`, `windowsHide:true`. 종료·타임아웃·중단 시 resolve, 실행 실패만 `SpawnError('cli-not-found'|'spawn-failed'|'invalid-command')`로 reject. `.cmd/.bat/.ps1`·상대 경로·NUL 인수 거부. stdin EPIPE 무시(V1-19) |
| `spawnLongLived(cmd, args, opts)` | spawn 이벤트 후 핸들 반환: `writeLine/writeJson`, `onStdoutLine/onStderrLine`(UTF-8 안전 줄 분할, 1MiB 상한), `closeStdin`, `exited`(reject 안 함), `kill()`. `timeoutMs`는 전체 수명 상한 |
| `killProcessTree(pid)` | Windows `%SystemRoot%\System32\taskkill.exe /PID n /T /F`(spawn 헬퍼 자체 경유), 실패 시 `process.kill` |
| `resolveCommand(nameOrPath)` | PATH+PATHEXT 탐색(`where` 미사용). `.exe` 직접, npm `.cmd` shim은 파싱해 `node.exe + <shim폴더 내부 JS 엔트리>`(shim 옆 node.exe 우선), `.ps1`/폴더 밖 엔트리는 `unsupported-shim` |
| `createJsonRpcClient(transport, {dialect, defaultTimeoutMs})` | `dialect:'codex'`는 `"jsonrpc"` 필드 생략, `'jsonrpc2'`는 포함. id 매칭, 요청별 타임아웃·AbortSignal, 알림 구독, 서버→클라이언트 요청 핸들러(미등록은 -32601), 전송 종료 시 대기 요청 전부 reject. JSON이 아닌 줄은 무시 |
| `stripAnsi`, `createLineSplitter` | CSI·OSC 8 제거(Claude 출력), CRLF·UTF-8 경계 처리 |

### 5-8. `src/main/log.ts`, `src/main/paths.ts`
- `createLogger({sinks, minLevel, scope})`, `logger.child(scope)`, `createFileSink(path,{maxBytes,keep})`, `createConsoleSink`, `nullLogger`. 메시지와 data는 **항상** `maskSecrets`/`redact`를 거친다. Error는 name·message·code만 남긴다.
- `USER_DATA_DIR_NAME='AIUsageWidgetV2'`, `resolveLocalDataRoot(env, override?)`, `profilesRootFor`, `bridgeRootFor`, `profileDirFor`, `isPathInside`(Windows 대소문자 무시, 형제 접두어 구분), `resolveResourcesDir`.

---

## 6. 상태·새로고침 모델

1. 앱 시작: store 로드 → 계정마다 `ensureProfileDir` → `detectCli`(공급자당 1회, `cli` 상태 `unknown→found|missing`, V1-37) → 활성 계정 `getIdentity` → 첫 `fetchUsage`(state `loading`).
2. 주기 조회: `settings.refreshIntervalSec`. 계정별 병렬(공급자당 동시 1개), 계정 하나가 끝날 때마다 스냅샷을 합쳐 `state:changed` **1회** 브로드캐스트(V1-16·39).
3. 수동 새로고침(위젯 버튼·트레이·팝업): 같은 계정이 조회 중이면 합류하고 새로 띄우지 않는다. 연타는 계정당 최소 5초 간격. 진행 중에는 `refresh.inFlight=true`, `refresh.accountIds`에 계정이 들어가 위젯 버튼이 회전한다(V1-23).
4. 실패: `applyFetchFailure`로 마지막 실측값 유지 + `errorCode`. 백오프 `min(30초·2^(n-1), 15분)` + 지터, `rate-limited`는 최소 5분. 성공하면 초기화(V1-11).
5. 표시: 렌더러는 `deriveDisplayState`로 `stale`/`reset`을 계산하고, `usedPercent:null`은 "미확인"으로 표시한다(0% 금지).
6. 절전 복귀(`powerMonitor` resume)·디스플레이 변경 시 즉시 1회 조회·재배치.

---

## 7. 공급자 흐름(확정안)

공통 규칙
- 자식 환경 = `BASE_ENV_ALLOW` + 공급자 HOME 변수 set + 자격증명 계열 변수 remove. 부모의 사용자 설정 폴더(`~/.claude`, `~/.codex`, `~/.grok`)는 절대 계정 폴더로 쓰지 않는다.
- 위젯 코드는 CLI 자격증명 파일(`.credentials.json`, `auth.json`)을 **읽지도 쓰지도 않는다.** 공급자 HTTP API를 사용자 토큰으로 직접 부르지 않는다. 사칭 헤더·client ID 없음.
- 로그인 이벤트의 URL·코드는 렌더러에 보여 주되 로그에는 남기지 않는다(`userCode`는 redact 키).
- 모든 호출에 타임아웃. 로그인 전체 10분, 단발 조회 30초 이내(모듈이 실측 후 조정·보고).
- 실측(T1·T2·T4) 전 추정으로 확정할 수 없는 응답 필드는 알 수 없는 필드를 허용하는 파서로 처리하고, 파서 테스트에 근거(스키마 파일·문서 경로)를 주석 1줄로 남긴다.

### 7-1. Claude (`providers/claude`, `resources/claude-bridge`) — DECISIONS 02:23
| 단계 | 방법 |
|---|---|
| CLI 탐지 | `resolveCommand('claude')`(예: `%USERPROFILE%\.local\bin\claude.exe`) + `claude --version` |
| env remove | `ANTHROPIC_API_KEY` `ANTHROPIC_AUTH_TOKEN` `CLAUDE_CODE_OAUTH_TOKEN` `CLAUDE_CODE_USE_BEDROCK` `CLAUDE_CODE_USE_VERTEX` `CLAUDE_CODE_USE_FOUNDRY` `ANTHROPIC_PROFILE` `ANTHROPIC_FEDERATION_RULE_ID` `ANTHROPIC_ORGANIZATION_ID` `AWS_BEARER_TOKEN_BEDROCK` `ANTHROPIC_CUSTOM_HEADERS` (RESEARCH 3-1) |
| env set | `CLAUDE_CONFIG_DIR=<profileDir>` |
| 로그인 | `spawnLongLived(claude, ['auth','login','--claudeai'])`. stdout을 `stripAnsi` 후 URL을 찾으면 `url`, `Paste code here if prompted` 프롬프트를 보면 `needs-paste`. `submitPaste`는 `code#state` 한 줄 쓰기. `Login successful.` + exit 0 → `getIdentity` 후 `success`. `#` 없는 입력은 끝나지 않으므로 타임아웃·kill 필수. `--console`은 노출하지 않는다 |
| 계정 표시 | `claude auth status --json`(미로그인 exit 1 → `logged-out`). 이 명령은 위젯 폴더에 `.claude.json`·`backups/`를 만든다(위젯 폴더라 허용). 이메일은 adapter 안에서 `maskEmail` |
| 수치 | statusline 브리지: 계정 폴더 `settings.json`의 `statusLine.command`가 Claude Code의 stdin JSON에서 `rate_limits`만 뽑아 `bridgeRoot` 아래 위젯 전용 파일에 쓴다. `fetchUsage`는 그 파일만 읽는다(5시간·7일 `used_percentage`, `resets_at` epoch 초→ms). 파일이 없으면 `unavailable`+`bridge-no-data`, 기록 시각이 오래되면 `stale` |
| 기본 프로필 브리지 | 사용자가 평소 `~/.claude`로 일하면 위젯 폴더에는 기록이 생기지 않는다(RESEARCH 3-1 추론). `bridge.installDefault(target)`는 사용자 확인 후 `<homeDir>\.claude\settings.json`을 백업하고 기존 `statusLine.command`를 감싸 보존한 채 설치, 기록을 `target` 계정에 연결한다. `uninstallDefault`는 원래 명령을 복원한다. 테스트는 `homeDir`에 임시 폴더를 주입하고 실제 `~/.claude`를 절대 건드리지 않는다 |
| 금지 | `/api/oauth/usage` 호출, `anthropic-ratelimit-*` 헤더 조회, PTY `/usage` 스크래핑, `setup-token` |
| 미결(모듈이 실측·보고) | 브리지 실행기(PowerShell 5.1 스크립트 vs node — `runAsNode:false`라 위젯 exe는 불가), `claude -p`에서 statusline 실행 여부(T3) |

### 7-2. Codex (`providers/codex`) — DECISIONS 02:23
| 단계 | 방법 |
|---|---|
| CLI 탐지 | `resolveCommand('codex')` → npm shim이면 `node.exe + …\@openai\codex\bin\codex.js`. `--version` |
| 폴더 | `CODEX_HOME` 폴더를 **spawn 전에 생성**(keyring 키가 canonicalize 경로 해시라서, RESEARCH 3-2) |
| env | set `CODEX_HOME=<profileDir>`, remove `OPENAI_API_KEY` `CODEX_API_KEY` 계열 |
| 연결 | `spawnLongLived(codex, ['app-server'])` + `createJsonRpcClient(dialect:'codex')` → `initialize {clientInfo:{name:'ai-usage-widget', version}}`(`experimentalApi` 없음) → 응답의 `codexHome`이 `profileDir`와 같은지 검증(다르면 `protocol-error`로 중단) → `initialized` 알림. 제한 init 30초 / rpc 10초 |
| 로그인 | `account/login/start {type:'chatgptDeviceCode'}` → `{loginId, userCode, verificationUrl}` → `device-code` 이벤트 → `account/login/completed` 알림 대기 → `account/read`로 email(마스킹)·planType → `success`. device code가 계정 설정에서 꺼져 있으면 `device-auth-disabled` |
| 수치 | `account/rateLimits/read` → `rateLimitsByLimitId` 각 버킷의 primary/secondary `{usedPercent, windowDurationMins, resetsAt(초)}` → `QuotaWindow`(kind는 분 단위로 분류, 버킷 id는 `label`). 결과를 받으면 프로세스 종료. `planType`은 모르는 값도 허용 |
| 금지 | `chatgptAuthTokens`, `apiKey`, `account/rateLimitResetCredit/consume`, `account/sendAddCreditsNudgeEmail`, `~/.codex`·Orca 폴더 공유, `wham/usage` 직접 호출 |
| 미결 | 실제 버킷 키·창 길이(T1), 조회가 auth.json을 다시 쓰는지 |

### 7-3. Grok (`providers/grok`) — DECISIONS 02:23
| 단계 | 방법 |
|---|---|
| CLI 탐지 | `resolveCommand('grok')`, PATH에 없으면 `<homeDir>\.grok\bin\grok.exe` 후보. `--version` |
| env | set `GROK_HOME=<profileDir>`, remove `XAI_API_KEY` 계열. leader 모드는 켜지 않는다 |
| 로그인 | `grok login --device-auth`를 상주 실행해 출력의 URL·코드를 `device-code`로 방출, 폴링 완료(exit 0) → `success` |
| 수치 | `spawnLongLived(grok, ['agent','stdio'])` + `dialect:'jsonrpc2'`(ACP) → `initialize` → `x.ai/billing` 호출 → 주간 `creditUsagePercent` + `currentPeriod.end`(주간 창), 없으면 월간. 5시간 창은 없다. **100%를 차단으로 표시하지 않는다**(추가 크레딧 사용 가능). 메서드가 없으면 `unavailable`+`quota-unavailable` |
| ACP 규칙 | 세션·프롬프트를 만들지 않는다(쿼터 소모 금지). 서버→클라이언트 요청(권한·파일)은 거부 응답 |
| 금지 | `/billing` HTTP 직접 호출, `auth.json` 읽기, OIDC refresh 직접 수행, Orca 값 |
| 미결 | `x.ai/billing` 존재·응답 형태(T4). 없으면 사용자에게 보고 후 재결정(DECISIONS 01:36 Grok 조건) |

---

## 8. 셸(main) 설계 요점

- **부트스트랩**(`index.ts`, 스캐폴드 구현됨): `configureUserData` → `setAppUserModelId('local.aiusagewidget')` → `registerSchemesAsPrivileged(app: standard+secure)` → 단일 인스턴스 락 → `hardenApp` → ready 후 `hardenSession`·`protocol.handle('app')`·registry·창 생성·IPC 등록. `--smoke`는 두 렌더러의 `app:renderer-ready`(CSP eval 차단 확인 포함)를 기다려 JSON 보고서를 쓰고 스스로 종료(0 성공 / 1 실패 / 2 강제 타임아웃).
- **store**: 쓰기는 `<file>.<ts>.tmp` → rename. 로드는 `normalizeSettings`·계정 검증. 빈 계정 배열을 존중(기본 계정 부활 없음, V1-15). 계정 객체는 복사해서 넘긴다(V1-04).
- **login 세션**: `sessionId = randomUUID()` 기반 id, 세션마다 AbortController, 계정당 동시 1개. 방출된 URL 목록을 세션에 보관해 `shell:open-external {kind:'login'}` 검증에 쓴다. 세션 종료 시 목록 폐기.
- **창·위치**: 위젯은 `screen` workArea/bounds 차이 + `display-added/removed/metrics-changed`로 재배치, 자동 숨김·좌우 작업 표시줄은 koffi `SHAppBarMessage`(실패 시 해당 기능만 끄고 폴백, V1-18·29). docked 최상위 유지는 koffi `SetWindowPos(HWND_TOPMOST)`를 같은 HWND에 재기동 없이(V1-12·28), 전체화면 감지는 koffi로 전경 창·모니터 비교 후 `showInactive()` 복원(V1-30). TaskbarDock.exe는 쓰지 않는다.
- **팝업**: 위젯/트레이 클릭은 잠금 없이 열고 blur 시 숨김. 설정 조작 중에만 `window:set-popup-lock`(V1-09). 위젯 이동·디스플레이 변경 시 열린 팝업도 재배치(V1-27).
- **트레이**: 메뉴 `trayToggleWidget`·`trayOpenPopup`·`trayAutoLaunch`·`trayRefreshNow`·`trayAddAccount`·`trayQuit`. 문구는 `shared/i18n`.
- **자동 시작**: `setLoginItemSettings({openAtLogin, path: process.execPath, args:['--autostart']})`, 조회도 같은 path·args(V1-31). `--autostart`/`--hidden`이면 위젯만 비활성 표시. Run 값 이름은 v1의 `electron.app.AI Usage Widget`과 달라야 한다(appUserModelId/productName 확인은 T8에서).
- **second-instance**: 기존 인스턴스가 위젯 표시 + 팝업 열기(V1-32, 스캐폴드에 최소 처리 있음).

---

## 9. 렌더러 설계 요점

- 프레임워크 없는 TS/DOM. HTML 문자열 금지: `h()`(`src/renderer/src/dom.ts`)처럼 `createElement`·`textContent`만 쓴다. ESLint가 `innerHTML`·`outerHTML`·`insertAdjacentHTML`·`document.write`를 막는다(V1-06).
- 상태 변경 시 전체 재렌더 대신 키 기반 부분 갱신, 입력·포커스·스크롤 보존, 애니메이션은 표시할 때만(V1-25·26).
- 위젯 막대: 계정별 아이콘·5H/주간 값·리셋 카운트다운(매초가 아니라 분 단위로 로컬 재계산), **새로고침 버튼**(회전 표시, `refresh` 상태 기준 비활성). 빈 상태 클릭 → 팝업 계정 탭.
- 테마 1a~1d의 v1 수치·색 규칙(SPEC §2)을 유지하되 조건 통일(V1-22), 모노크롬 규칙 단일 정의(V1-33), SVG gradient id는 인스턴스별 고유(V1-42). `windows` 테마는 `ThemeTokens` CSS 변수만 쓴다.
- 접근성: `role=tablist/tab`, 화살표 키 이동, 아이콘 버튼 `aria-label`, `:focus-visible`, `forced-colors`, `prefers-reduced-motion`(V1-36).
- 로그인 UI: `url`→"브라우저에서 열기"(`shell:open-external {kind:'login'}`) + 붙여넣기 입력, `device-code`→코드 크게 표시 + 주소 열기, `progress`/`error` 문구는 i18n 표.

---

## 10. 보안 모델

| 위협 | 대응 | 위치 |
|---|---|---|
| 렌더러 XSS → 권한 상승 | sandbox·contextIsolation, CSP 응답 헤더 `default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'`, DOM API만 사용 | `protocol/urls.ts`, ESLint |
| 임의 IPC 호출 | preload 채널 허용 목록, main 발신 프레임 URL 검증, 모든 페이로드 런타임 검증, 오류는 코드만 | `preload/index.ts`, `ipc/dispatch.ts`, `shared/ipc.ts` |
| 외부 이동·새 창·webview | `setWindowOpenHandler` deny, `will-navigate`/`will-redirect` 비신뢰 URL 차단, `will-attach-webview` 차단, 권한 요청 전부 거부 | `security/index.ts` |
| 파일 프로토콜 경로 이탈 | `app://bundle` 호스트만, 디코드 후 `\`·NUL 거부, 루트 내부 검사, GET만 | `protocol/urls.ts` |
| 임의 URL 열기 | 고정 키 또는 활성 로그인 세션이 방출한 https URL만 | `shared/ipc.ts` + 셸 login |
| 토큰 노출 | 위젯은 토큰을 보관·조회하지 않음(CLI 소유). DTO는 `toAccountDTO`, 로그는 마스킹. 위젯이 비밀을 가져야 하면 `safeStorage`(현재 없음) | 계약 전반 |
| 명령 주입·셸 해석 | `shell:false`, argv 배열, `.cmd` 직접 실행 금지(shim 파싱), 절대 경로만, env 화이트리스트 | `cli/spawn.ts`, `cli/resolve.ts` |
| 좀비·폭주 프로세스 | 모든 실행에 타임아웃, Abort, `taskkill /T /F` 트리 종료 | `cli/spawn.ts` |
| 앱 파일 변조 | per-user 설치, asar + 퓨즈 `runAsNode:false` `enableNodeOptionsEnvironmentVariable:false` `enableNodeCliInspectArguments:false` `enableEmbeddedAsarIntegrityValidation:true` `onlyLoadAppFromAsar:true` `enableCookieEncryption:true` `grantFileProtocolExtraPrivileges:false`. 무서명이라 심층방어 수준(RESEARCH §5) | `electron-builder.yml` |
| v1 간섭 | v1 폴더·프로세스·Run 값 미접촉, userData·exe 이름 분리 | `paths.ts`, `electron-builder.yml` |

---

## 11. 테마 모델

- main이 `nativeTheme`(`shouldUseDarkColors`, `shouldUseDarkColorsForSystemIntegratedUI`, `inForcedColorsMode`, `prefersReducedTransparency`)와 `systemPreferences.getAccentColor()`를 읽어 `computeThemeTokens()`로 `ThemeTokens`를 만든다. `nativeTheme 'updated'`와 `systemPreferences 'accent-color-changed'`(트리거로만 쓰고 재조회)에서 `theme:changed`를 보낸다.
- 위젯 막대는 작업 표시줄 위에 있으므로 `taskbarScheme`, 팝업은 `scheme`을 쓴다.
- `effectiveMaterial`: 고대비 또는 투명도 감소면 강제로 `none`. `mica`/`acrylic`은 `frame:false` + `backgroundMaterial` + `transparent` 미사용이어야 하므로 셸이 창을 다시 만든다. #48031(가려짐·절전 시 검정/회색) 때문에 T8 전까지 기본 `none`.
- 렌더러는 `data-scheme`, `data-high-contrast`, `--accent` 변수만 받는다. 고대비에서는 `forced-colors`에 맡기고 브랜드 색을 강제하지 않는다.

---

## 12. v1 문제(V1-01~43) 배정

| V1 | 요지 | 해결 위치(모듈) | 스캐폴드 상태 |
|---|---|---|---|
| 01 | customMock을 정상 값으로 표시 | 계약 `usedPercent:null`, `applyFetchFailure` / codex·claude·grok·renderer | 계약 완료 |
| 02 | 폴더 권한·퓨즈 꺼짐 | `electron-builder.yml` per-user + 퓨즈 | 완료(dist:dir에서 퓨즈 적용 확인) |
| 03 | 공식 클라이언트 사칭·자격증명 재사용 | CLI 위임 / codex·claude·grok | 계약 완료 |
| 04 | 공유 계정 객체에 토큰 주입 | shell store 복사, 위젯 토큰 비보관 | 규칙 명시 |
| 05 | 평문 토큰·렌더러 전송 | `toAccountDTO` / shell | 계약 완료 |
| 06 | innerHTML·CSP·IPC 검증·네비게이션 | CSP 헤더, dispatch, hardenApp, ESLint / renderer | 완료 |
| 07 | netstat CSRF 토큰 전송 | Antigravity 경로 제거 | 해당 없음 |
| 08 | 지원 종료 Electron | Electron 44.3.0 | 완료 |
| 09 | 팝업 항상 잠금 | `window:set-popup-lock` / shell·renderer | 계약 완료 |
| 10 | Antigravity PowerShell 반복 | 제거 | 해당 없음 |
| 11 | Claude 백오프·상태 코드 | shell scheduler 백오프, ErrorCode | 계약 완료 |
| 12 | 슬라이더마다 저장·staytop 재기동 | renderer 미리보기/확정 1회 저장, shell koffi 재기동 없음 | — |
| 13 | node:sqlite 추정 | 제거 | 해당 없음 |
| 14 | 자동 실행 기본 ON, `--hidden` 미사용 | 기본 false, `--autostart/--hidden` 파싱 / shell | 계약·인수 파싱 완료 |
| 15 | 기본 계정 부활 | shell store 빈 배열 존중 | — |
| 16 | fetch 타임아웃 없음·전체 정체 | `cli/spawn` 타임아웃, 계정별 즉시 브로드캐스트 / shell | spawn 완료 |
| 17 | weekly 라벨 오표시 | `kind`를 창 길이로 분류 / providers | 계약 완료 |
| 18 | 좌우·자동 숨김·보조 모니터 | shell platform/taskbar(koffi) | — |
| 19 | exe 선택 기준·stdin error | `resolveCommand` 고정 규칙, stdin error 처리 | 완료 |
| 20 | 렌더러 입력 무검증 | `shared/ipc` 검증기, `clampWidgetSize` | 완료 |
| 21 | 앱 내 OAuth 결함 | 앱 내 OAuth 없음 | 해당 없음 |
| 22 | 배포 번들 Mock API·테마 조건 | mock은 테스트만 / renderer | — |
| 23 | isRefreshing 항상 false | `RefreshStatus` / shell·renderer | 계약 완료 |
| 24 | 오류 삼킴·영구 loading | ErrorCode + i18n / shell·providers | 계약 완료 |
| 25 | 전체 재렌더 | renderer 부분 갱신 | — |
| 26 | 슬라이더 키보드 포커스 소실 | renderer | — |
| 27 | 팝업 재배치 누락 | shell | — |
| 28 | floating에서도 moveTop | shell zorder | — |
| 29 | 상단 작업 표시줄 floating 화면 밖 | shell taskbar | — |
| 30 | 복원 시 포커스 탈취 | shell `showInactive` | — |
| 31 | 로그인 항목 조회 불일치 | shell 같은 path·args | — |
| 32 | second-instance 무반응 | shell | 최소 처리 있음 |
| 33 | 모노크롬 범위 불일치 | renderer 단일 규칙 | — |
| 34 | i18n 이원화·하드코딩 | 단일 사전, main이 로케일 결정 | 완료 |
| 35 | 문구·동작 모순 | 문구 정정, 빈 상태 클릭 → 계정 탭 | 문구·스캐폴드 뷰 완료 |
| 36 | 접근성 | renderer | — |
| 37 | 감지 목록 하드코딩 | `cli` 상태 `unknown` 시작, 실제 탐지 / shell | 계약 완료 |
| 38 | UI 없는 설정·죽은 코드 | `verticalOffsetPx` 범위, `showWeeklyLimitLabel` / renderer | 계약 완료 |
| 39 | 브로드캐스트 2회 | shell 1회 | — |
| 40 | 로컬 추정치 | 제거 | 해당 없음 |
| 41 | showCardBackground 기본값 불일치 | `DEFAULT_SETTINGS` 단일 정의 / renderer 강제 표시 | 계약 완료 |
| 42 | SVG gradient id 충돌 | renderer 고유 id | — |
| 43 | 미사용 IPC | 미이식, `show-popup {tab}` | 완료 |

---

## 13. 모듈 소유권 맵

각 모듈은 아래 경로만 만들고 고친다. 테스트는 소유 코드 옆에 둔다. 계약 파일 변경·의존성 추가는 보고서의 "계약 변경 요청"으로만 한다.

| 모듈 키 | 소유 경로 |
|---|---|
| `shell` | `src/main/index.ts`, `src/main/app/**`, `src/main/ipc/**`, `src/main/windows/**`, `src/main/tray/**`, `src/main/scheduler/**`, `src/main/store/**`, `src/main/login/**`, `src/main/platform/**`, `src/main/protocol/**`, `src/main/security/**` |
| `codex` | `src/main/providers/codex/**` |
| `claude` | `src/main/providers/claude/**`, `resources/claude-bridge/**` |
| `grok` | `src/main/providers/grok/**` |
| `renderer` | `src/renderer/**`, `src/preload/**` |

계약(어느 모듈도 수정 금지): `src/shared/**`, `src/main/cli/**`, `src/main/log.ts`, `src/main/log.test.ts`, `src/main/paths.ts`, `src/main/paths.test.ts`, `src/main/providers/types.ts`, `src/main/providers/registry.ts`, `src/main/providers/registry.test.ts`, `src/main/providers/placeholder.ts`, `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `tsconfig.json`, `tsconfig.node.json`, `tsconfig.web.json`, `eslint.config.mjs`, `vitest.config.ts`, `electron.vite.config.ts`, `electron-builder.yml`, `.gitignore`, `.gitattributes`, `.editorconfig`, `CLAUDE.md`, `DECISIONS.md`(append만), `docs/DESIGN.md`.

모듈 공통 완료 조건
- `pnpm verify` 종료코드 0, `pnpm build` 종료코드 0.
- 자식 프로세스는 `cli/spawn.ts`만, 경로는 `ProviderDeps`/`paths.ts`만 사용.
- 실제 로그인·로그아웃·계정 전환 실행 금지, 실제 자격증명 파일 읽기 금지. CLI 기능 탐색은 `C:\Users\202502\AppData\Local\Temp\claude\widget-v2-build\` 아래 **새 빈 HOME**에서 타임아웃을 걸고 로그인 메서드를 부르지 않는 범위만.
- 수치·계정이 필요한 테스트는 테스트 코드 안의 고정 fixture만 사용(앱 코드에 mock 금지).

---

## 14. i18n 키 변경 기록(v1 86키 기준)

- **유지(이름 그대로)**: `trayToggleWidget` `trayOpenPopup` `trayAutoLaunch` `trayRefreshNow` `trayQuit` `trayTooltip` `popupTitle` `accountsActive` `refresh` `close` `tabUsage` `tabAccounts` `tabSettings` `noActiveAccounts` `addAccountHint` `realtimeMonitoring` `sessionLimit5h` `usageLabel` `resetLabel` `weeklyLimit` `moveUp` `moveDown` `deleteAccountTitle` `deleteAccountBtn` `redetect` `checkedAccountsHint` `save` `cancel` `confirmDeleteAccount` `widgetTheme` `theme1a`~`theme1d` `iconStyleLabel` `iconColor` `iconMono` `launchAtLogin` `colorByUsageLabel` `showCardBg` `showUsedPercentLabel` `placementLabel` `placementDocked` `placementFloating` `alwaysOnTopLabel` `alwaysOnTopDesc` `alignmentLabel` `alignRightFloating` `alignRightDocked` `alignLeftFloating` `alignLeftDocked` `offsetLabel` `alphaLabel` `refreshIntervalLabel` `interval15`~`interval300` `unitUsed` `unitLeft` `widgetTooltip` `widgetTooltipNoWeekly` `noAccountTitle` `widgetClickTitle`. 문구 정정: `accountsActive`(복수형 회피), en `usageLabel`="Used"(중복 해소), `resetLabel`("리셋: -- 남음" 제거), `alphaLabel`·`noAccountTitle`(V1-35), "작업 표시줄" 표기 통일, `confirmDeleteAccount`(격리 폴더 삭제 안내).
- **이름 변경**: `trayAddGoogle`→`trayAddAccount`, `modelQuotaTitle`→`otherWindowsTitle`, `detectingApps`→`detectingCli`, `localInstallDetected`→`cliDetected`/`cliDetectedNoVersion`, `loginFailedAlert`→`loginFailed`.
- **삭제**(mock·Google OAuth·로컬 IDE 전용): `localIdeNoAuth` `runningNow` `presetReady` `added` `addToWidget` `localDetectTitle` `addCustomAccountTitle` `accountAlias` `iconLetterLabel` `brandColorLabel` `usage5h` `usageWeekly` `addGoogleOAuth` `addManually` `resetDefaults` `confirmResetDefaults`.
- **추가**: 창·상태(`windowOtherMinutes` `percentUnknown` `resetUnknown` `lastMeasured` `neverMeasured` `sourceLabel` `errorDetail` `state_*` `source_*` `provider_*`), 새로고침(`widgetRefresh` `refreshing`), 계정(`addAccountTitle` `addAccountFor` `accountLabelLabel` `accountLabelPlaceholder` `rename` `enableAccount` `cliNotFound` `cliInstallGuide`), 로그인(`login*`, `loginStage_*`, `loginState_*`), 브리지(`bridge*`), 테마·언어(`themeWindows` `material*` `language*` `showWeeklyLimitLabel` `verticalOffsetLabel` `pixels`), 오류(`error_*` 20개).

---

## 15. 빌드·패키징

| 항목 | 내용 |
|---|---|
| 스택 | electron 44.3.0, electron-vite 5.0.0, vite 7.3.6, typescript 5.9.3, vitest 5.0.0(+happy-dom 20.14.5), eslint 9.39.5 + typescript-eslint 8.70.0, electron-builder 26.15.3, koffi 3.2.1 |
| Electron 바이너리 | Electron 42+ 패키지는 postinstall이 없다. `node_modules/electron/index.js`가 첫 `require('electron')`에서 `install.js`를 실행하는 지연 다운로드만 있다. 그래서 루트 `postinstall: install-electron`(electron 패키지의 bin)으로 설치 시점에 받는다(이미 있으면 즉시 종료). electron-builder는 `@electron/get` 캐시에서 zip을 따로 받는다 |
| pnpm 11 빌드 승인 | `pnpm-workspace.yaml` `allowBuilds`: `electron`·`esbuild`·`koffi` true, `electron-winstaller` false(Squirrel 미사용). 미승인 패키지가 있으면 pnpm 11은 `ERR_PNPM_IGNORED_BUILDS`로 install을 실패시킨다(실측) |
| 스크립트 | `dev` / `build`(electron-vite build) / `typecheck`(두 tsconfig) / `lint`(`--max-warnings 0`) / `test`(vitest run, node·renderer 프로젝트) / `verify`(= typecheck && lint && test) / `dist:dir` / `dist`(NSIS) |
| 출력 | `out/main/index.js`(CJS), `out/preload/index.js`(CJS, sandbox 호환), `out/renderer/`(app://bundle로 제공) |
| 퓨즈 키 | app-builder-lib 26.15.3 `scheme.json`의 `FuseOptionsV1`과 대조해 7개 키 모두 일치 |
| koffi | 실제 `.node`는 `@koromix/koffi-win32-x64/win32_x64/koffi.node`. `asarUnpack`에 `koffi`와 `@koromix/koffi-win32-x64`를 둘 다 넣었다. `npmRebuild:false`(prebuilt) |
| 아이콘 | 256px 이상 앱 아이콘이 없어 `win.icon` 미설정(기본 Electron 아이콘). `resources/tray-icon.ico`는 16·32px뿐 |
| 스모크 | `electron . --smoke --smoke-out=<json> --user-data-dir=<임시>` / 배포본 `release\win-unpacked\ai-usage-widget.exe --smoke …` |

---

## 16. 실측 대기(사용자 참관, DECISIONS 02:23)

T1 Codex device code 로그인·버킷 / T2 Claude 파이프 로그인 / T3 statusline `rate_limits` 기록 / T4 Grok ACP `x.ai/billing` / T8 재질·강조색·koffi 패키징·NSIS 퓨즈. 결과는 `DECISIONS.md`에 결정으로 남기고 이 문서의 해당 절을 갱신한다.

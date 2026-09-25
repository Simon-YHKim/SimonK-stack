# DESIGN — AI Usage Widget v2
> 원본(손으로 고치는 문서). 작성 2026-09-15 03:12 KST · 발행 Claude Code(스캐폴딩 에이전트) / 갱신 2026-09-15 04:06 KST · Claude Code(통합 에이전트: 모듈 병합, 계약 변경 반영)
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
| `%LOCALAPPDATA%\AIUsageWidget\bridge\claude\` | `<key16>.json`(브리지 레코드: five_hour/seven_day `used_percentage`·`resets_at`, model id/이름만), `<key16>.wrap.json`(설치 전 statusLine 원본 `{v, previous:{present, value}}`), `default-profile.json`(기본 프로필 연결 `{v, targetAccountId, installedAt, backupPath}`), `bin\aiuw-claude-bridge.cjs`·`.ps1`(settings.json이 가리키는 고정 복사본) | 토큰·cwd·session_id·transcript·cost 없음. `key16` = sha256(정규화한 CONFIG_DIR — 절대경로·역슬래시·끝 슬래시 제거·소문자, 기본 프로필이면 `'~/.claude default'`)의 앞 16자. 경로는 `ProviderDeps.bridgeRoot`에서만 만든다 |
| `%LOCALAPPDATA%\AIUsageWidget\cli-detect\codex\`, `tmp\claude-detect\` | `--version` 실행용 위젯 소유 CLI 홈 | 실제 `~/.codex`·`~/.claude`를 초기화하지 않기 위함 |
| `<resources>\resources\` | 트레이·공급자 아이콘, `claude-bridge\` 스크립트 | 개발: `<appPath>\resources`, 배포: `process.resourcesPath\resources`(`resolveResourcesDir`) |
| 설치 | `%LOCALAPPDATA%\Programs\AI Usage Widget\ai-usage-widget.exe` | NSIS oneClick per-user. exe 이름을 v1(`AI Usage Widget.exe`)과 다르게 해 프로세스를 구분 |

- `accounts.json`에 저장된 `profileDir`는 신뢰하지 않는다. 로드할 때 `profileDirFor(profilesRoot, provider, id)`로 다시 계산한다(셸 store 규칙).
- `--smoke` 또는 `--user-data-dir`로 실행하면 userData를 그 경로(없으면 임시 폴더)로, local 데이터 루트를 `<userData>\local`로 바꿔 실제 프로필을 건드리지 않는다.

---

## 5. 계약(Contracts)

모듈은 계약 파일을 고치지 않는다. 필요한 변경은 작업 보고서의 "계약 변경 요청"에 적고, 통합 단계에서 반영한다(§13).

### 5-1. `src/shared/types.ts`
- `ProviderId = 'claude'|'codex'|'grok'|'antigravity'`. `PROVIDER_TRAITS: Record<ProviderId, {maxAccounts:number|null, widgetLogin:boolean}>`는 main(계정 수 강제)과 렌더러(버튼 표시)가 함께 쓴다(DECISIONS 26.09.19 11:42).
- `Account { id, provider, label, enabled, order, profileDir(main 전용), createdAt }` / `AccountDTO { id, provider, label, enabled, order, emailMasked?, plan?, loginState }`. 변환은 반드시 `toAccountDTO()`(필드를 명시적으로 골라 새 필드가 새지 않게 함).
- `QuotaWindow { kind:'session'|'weekly'|'other', usedPercent:number|null, resetsAt:number|null(epoch ms), windowMinutes:number|null, label? }`. **모르는 값은 null이며 0으로 쓰지 않는다.** `label`(codex 버킷 id, antigravity 모델 그룹)은 팝업 상자 제목 아래에 텍스트로 표시해 같은 kind의 창을 구분한다. 위젯 막대에는 표시하지 않는다.
- `UsageSnapshot { accountId, provider, state, windows, plan?, measuredAt, lastSuccessAt, errorCode?, source }`
  - `state`: `ok` 측정 성공 / `stale` 오래됨 / `loading` 첫 조회 중 / `error` 실패(윈도우는 마지막 실측값일 수 있음) / `unavailable` 공급원이 수치를 주지 않음 / `logged-out` / `reset` 모든 창의 리셋 시각이 지남.
  - `source`: `'codex-app-server'|'claude-statusline'|'grok-acp'|'antigravity-cli-usage'`.
- `ErrorCode`(21종, 통합 때 `cli-unsupported-install` 추가 — CLI는 있으나 npm shim 등 실행기를 셸 없이 해석할 수 없음): 렌더러는 코드만 받아 i18n 문구로 바꾼다. 공급자 원문 오류는 UI로 가지 않는다.
- `LoginEvent`: `url` / `device-code {userCode, verificationUrl, expiresAt?}` / `needs-paste` / `progress {stage}` / `success {emailMasked?, plan?}` / `error {code}`. IPC에서는 `LoginEventMessage { sessionId, accountId, at, event }`.
- `ThemeTokens { scheme, taskbarScheme, highContrast, accent('#rrggbb'), reducedTransparency, effectiveMaterial }`.
- `AppStateSnapshot { locale, settings, accounts, usage, refresh, theme, cli, effectivePlacementMode }` — 렌더러가 받는 유일한 상태. `effectivePlacementMode`는 실제 적용된 배치(docked가 좌우·자동 숨김 작업 표시줄에서 floating으로 폴백하면 floating, 배치 전 null).

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
| `showCardBackground` | true | bool | 기본값 단일 정의(V1-41). v1의 'floating 선택 시 강제 켜기'는 이식하지 않는다(숨은 강제 규칙 없음, DECISIONS 04:06) |
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
| `window:resize-widget` | `{width, height}` | null | 유한 양수. main이 `clampWidgetSize`(32~3840 × 24~120)로 제한(V1-20). 배치가 다시 모니터 안으로 제한하고, 잘릴 때도 새로고침 버튼은 보인다 |
| `window:preview-placement` | `{patch:{offsetPx?, verticalOffsetPx?}|null}` | null | 두 키만 허용(`parseSettingsPatch`). 저장하지 않고 위젯 위치만 바꾼다. 설정 저장 시 해제, `null`이면 저장값으로 복귀(V1-12) |
| `cli:redetect` | `{provider:ProviderId|null}` | null | 사용자가 요청한 CLI 재탐지(설치 후 '다시 감지'). 탐지 중 `cli[provider].state`는 `unknown` |
| `claude-bridge:status` | null | `ClaudeBridgeStatus` | |
| `claude-bridge:install-default` | `{accountId}` | `ClaudeBridgeStatus` | 사용자 확인 대화 후에만 호출 |
| `claude-bridge:uninstall-default` | null | `ClaudeBridgeStatus` | |

| 이벤트(main→renderer) | 페이로드 |
|---|---|
| `state:changed` | `AppStateSnapshot` |
| `theme:changed` | `ThemeTokens` |
| `login:event` | `LoginEventMessage` |
| `popup:show` | `{tab: PopupTab|null}` — main이 팝업을 **표시할 때마다**(토글·트레이·첫 실행·`window:show-popup {tab}`) 팝업 창에만 보낸다. `tab`이 있으면 그 탭, `null`이면 현재 탭(계정 0개면 계정 탭). 두 창이 backgroundThrottling:false라 visibilitychange가 오지 않으므로 표시 처리(입장 애니메이션·계정 탭 갱신)는 이 이벤트로만 한다 |

- `IpcErrorCode`: `invalid-request` `forbidden-sender` `not-found` `conflict` `busy` `not-implemented` `internal`.
- 뷰 제한(`ipc/handlers.ts`): 상태를 바꾸는 채널(`settings:update`, `accounts:add·remove·rename·toggle·reorder`, `login:*`, `shell:open-external`, `window:hide-popup·set-popup-lock·preview-placement`, `cli:redetect`, `claude-bridge:install-default·uninstall-default`)은 팝업 뷰만, `window:resize-widget`은 위젯 뷰만 허용. 나머지(상태 읽기·새로고침·팝업 열기·브리지 상태)는 두 뷰 모두(DECISIONS 26.09.15 04:49).
- 발신자 검증(`ipc/dispatch.ts`): 최상위 프레임 URL이 `app://bundle/…`(개발 시 dev server origin)일 때만 처리한다. 하위 프레임은 거부.
- `EXTERNAL_LINK_KEYS`(`claude-cli-install` `codex-cli-install` `grok-cli-install` `antigravity-cli-install`)의 실제 URL 표는 셸이 main에 두며(`src/main/platform/links.ts`), 공식 문서에서 확인한 https 주소만 넣는다. 세 키 모두 확정(DECISIONS 26.09.19 11:20). 같은 파일의 `EXTERNAL_LINK_HOSTS`가 키별 허용 호스트이고 `links.test.ts`가 https·호스트·자격증명/포트/프래그먼트 없음을 강제한다(antigravity 주소는 CLI 탭을 고르는 쿼리를 쓴다). 표에 없는 키는 `not-found`.

### 5-4. `src/shared/i18n/`
- `ko.ts`가 키 집합의 원본, `en.ts`는 `Record<keyof typeof ko, string>`이라 키가 어긋나면 typecheck가 실패한다. 테스트가 키 집합·자리표시자 일치·빈 문구 0건을 확인한다.
- `t(locale, key, params)` / `createTranslator(locale)`. main(트레이)과 렌더러가 같은 사전을 쓰고, 로케일은 main이 정해 스냅샷으로 보낸다(V1-34). 렌더러는 `state.locale`을 따르고 `navigator.language`는 폴백으로만 쓴다.
- 사전 밖 허용 항목: 상대 시각은 `Intl.RelativeTimeFormat(locale)`로 만든다(사전 키 없음). 위젯 상태 표식(`···` `!` `—` `⊘` `↺`)과 행 태그(`5H` `WK`, 기타 창 `30m`/`1H`/`1D`)는 v1 전례대로 번역하지 않는 기호 상수다. 그 밖의 사용자 문구는 모두 사전을 거친다.
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
  readonly loginUrlHosts: readonly string[];          // shell:open-external 허용 호스트(하위 도메인 포함). 빈 배열 = 열지 않음
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
- `getIdentity`: `loggedIn:false`는 **확정된 미로그인**에만 쓴다. 판단 불가(타임아웃·CLI 없음·네트워크)면 `ProviderError(code)`로 reject하고, 셸은 이를 loginState `unknown`으로 표시한다(`logged-out` 아님).
- `loginUrlHosts`(통합 시 확정): claude `claude.com`·`claude.ai`(경로는 어댑터가 정확히 검사), codex `openai.com`(문서 예시 `auth.openai.com/codex/device`, T1에서 확인), grok `x.ai`·`grok.com`.
- `registry.ts`는 `providers/<id>/index.ts`의 `create<Id>Adapter`를 import한다(통합 완료, 실제 어댑터). 팩토리는 테스트용 두 번째 인수를 가질 수 있다(`ProviderFactory`와 호환). `placeholder.ts`는 테스트와 미래 공급자용으로만 남는다.

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
- 모든 호출에 타임아웃. 로그인 전체 10분. 셸 스케줄러는 계정 조회 1회(`getIdentity` + `fetchUsage`가 같은 슬롯에서 연달아 실행)에 120초 AbortSignal을 건다(어댑터 예산 합: codex identity 세션 50초 + usage 세션 60초, DECISIONS 04:49). 어댑터 내부 제한: codex init 30초·rpc 10초, grok init 30초·요청 20초·수명 60초, claude auth status 30초·`--version` 15초. 실측 시간이 나오면 조정한다.
- 자동 조회 간격 = max(설정 `refreshIntervalSec`, `PROVIDER_TRAITS[provider].minRefreshSec`) × 배터리 배수. 최소값: claude 15초(로컬 브리지 파일만 읽음), codex·grok 60초, antigravity 120초(`agy` 1회 7~9초). 수동 새로고침은 이 하한과 무관하게 즉시 조회한다. 설정 탭 `refreshIntervalHint`가 같은 상수로 안내한다(DECISIONS 26.09.20 10:54).
- 실측(T1·T2·T4) 전 추정으로 확정할 수 없는 응답 필드는 알 수 없는 필드를 허용하는 파서로 처리하고, 파서 테스트에 근거(스키마 파일·문서 경로)를 주석 1줄로 남긴다.

### 7-1. Claude (`providers/claude`, `resources/claude-bridge`) — DECISIONS 02:23
| 단계 | 방법 |
|---|---|
| CLI 탐지 | `resolveCommand('claude')`(예: `%USERPROFILE%\.local\bin\claude.exe`) + `claude --version` |
| env remove | `ANTHROPIC_API_KEY` `ANTHROPIC_AUTH_TOKEN` `CLAUDE_CODE_OAUTH_TOKEN` `CLAUDE_CODE_USE_BEDROCK` `CLAUDE_CODE_USE_VERTEX` `CLAUDE_CODE_USE_FOUNDRY` `ANTHROPIC_PROFILE` `ANTHROPIC_FEDERATION_RULE_ID` `ANTHROPIC_ORGANIZATION_ID` `AWS_BEARER_TOKEN_BEDROCK` `ANTHROPIC_CUSTOM_HEADERS` (RESEARCH 3-1) |
| env set | `CLAUDE_CONFIG_DIR=<profileDir>` |
| 로그인 | `spawnLongLived(claude, ['auth','login','--claudeai'])`. stdout을 `stripAnsi`(OSC 8 포함) 후 URL을 찾으면 `url`. claude.exe 2.1.270은 `Paste code here if prompted > `를 **줄바꿈 없이** URL 줄 직후 같은 콜백에서 출력하므로, 줄 단위 API로는 프롬프트를 볼 수 없어 URL 줄을 받는 즉시 `needs-paste`를 낸다(CLI가 순서를 바꾸면 조정, T2). `submitPaste`는 `^[A-Za-z0-9._~+/=-]{1,2048}#[A-Za-z0-9._~+/=-]{1,2048}$`만 stdin에 한 줄로 쓴다(틀리면 `parse-error`, 쓰지 않음). `Login successful.`(프롬프트와 같은 줄에 붙어 나오는 경우 포함) + exit 0 → `auth status` 확인 후 `success`. `#` 없는 입력은 끝나지 않으므로 타임아웃·kill 필수. `--console`은 노출하지 않는다. 허용 URL은 `https://claude.com/cai/oauth/authorize`(CLAUDE_AI_AUTHORIZE_URL)와 구버전용 `https://claude.ai/oauth/authorize` 두 개, 경로 정확히 일치·포트/자격정보 거부, 목록 밖 URL이면 kill + `protocol-error`. CLI가 브라우저를 스스로 연다('Opening browser to sign in…'); 렌더러 '브라우저에서 열기'는 대체 수단 |
| 계정 표시 | `claude auth status --json`(미로그인 exit 1 → `logged-out`). 이 명령은 위젯 폴더에 `.claude.json`·`backups/`를 만든다(위젯 폴더라 허용). 이메일은 adapter 안에서 `maskEmail` |
| 수치 | statusline 브리지: 계정 폴더 `settings.json`의 `statusLine.command`가 Claude Code의 stdin JSON에서 `rate_limits`만 뽑아 `bridgeRoot\claude\<key16>.json`에 원자적으로 쓴다(ensureProfileDir에서 멱등 설치). `fetchUsage`는 그 파일만 읽는다(5시간·7일 `used_percentage`, `resets_at` epoch 초→ms). 레코드 없음 → `unavailable`+`bridge-no-data`, 깨짐 → `error`+`parse-error`, 5분보다 오래됨 → `stale`. **리셋 시각이 지난 창은 `usedPercent:null`**(0%나 이전 값으로 표시하지 않음), 모든 창이 지나면 `reset`. 미래 기록 시각·31일 초과 리셋은 무시, 퍼센트 0~100 clamp. 계정이 기본 프로필 대상이면 자기 레코드와 기본 프로필 레코드 중 창마다 최신 값. 로그아웃은 감지하지 않는다(셸이 `getIdentity`로 반영). 병합: 창이 들어오면 교체, `rate_limits`는 있는데 창이 빠지면 이전 창이 이미 리셋된 경우에만 유지, `rate_limits` 자체가 없으면 이전 창 유지 |
| 브리지 실행기(확정) | **node**(설치 시점 `resolveCommand('node')`), 없으면 PowerShell 5.1. 실측 기동 node 약 260ms / PowerShell 약 850ms, `runAsNode:false`라 위젯 exe 불가(DECISIONS 04:06). 명령 형식: node `node '<bin/aiuw-claude-bridge.cjs>' --key <k> --out '<dir>'`, PowerShell `powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File '<bin/aiuw-claude-bridge.ps1>' -Key <k> -Out '<dir>'`. 작은따옴표·슬래시 경로라 Git Bash·PowerShell 모두 동일 해석, 경로에 `'`·제어문자가 있으면 설치 거부. 감싼 원래 명령은 Claude Code 셸 선택을 흉내 내 실행(CLAUDE_CODE_GIT_BASH_PATH → PATH git의 bash → Program Files\Git\bin\bash.exe → powershell -EncodedCommand), 30초 타임아웃(초과 시 `taskkill /PID <pid> /T /F`로 셸과 자식 트리 종료), stdout·종료코드 그대로 전달 |
| 기본 프로필 브리지 | 사용자가 평소 `~/.claude`로 일하면 위젯 폴더에는 기록이 생기지 않는다(RESEARCH 3-1 추론). `bridge.installDefault(target)`는 사용자 확인 후, 브리지가 statusLine을 처음 차지할 때 `settings.json.aiuw-backup-<UTC타임스탬프>[-n]`로 백업하고(제거할 때도 백업, 최근 3개만 유지, 이미 설치된 명령을 고칠 때는 백업 없음) 기존 `statusLine` 객체(padding 등 유지)를 감싸 sidecar에 원본을 남긴 채 설치, 기록을 `target` 계정에 연결한다. JSON 객체가 아니면 쓰지도 백업하지도 않고 `parse-error`. `uninstallDefault`는 원본 객체를 복원(없었으면 키 삭제)하고, 사용자가 이미 다른 statusLine으로 바꿨으면 손대지 않는다. 기본 프로필 경로는 env `CLAUDE_CONFIG_DIR`가 위젯 profiles 밖의 절대경로일 때만 그 경로, 아니면 `<homeDir>\.claude`. 키는 두 경우 모두 해석된 폴더 경로의 해시다. 이미 설치된 명령의 `--key`/`-Key`로 sidecar를 찾아 원본을 이어받고(다른 키로 설치돼 있어도 '설치됨'으로 표시하고 제거 가능), sidecar가 있는데 읽을 수 없으면 설치·제거를 거부한다(`parse-error`). bin 복사 전에 스크립트 SHA-256을 빌드 상수 `__AIUW_BRIDGE_SHA256__`(main 번들, asar 무결성 범위)과 대조하고 다르면 거부(`internal`). 앱 제거기는 settings.json을 되돌리지 않으므로 브리지 카드와 설치 확인 문구에 '삭제 전 [기본 프로필에서 제거]'와 백업 위치를 표시한다(DECISIONS 04:49). 재직렬화라 한 줄 배열이 펼쳐지는 등 서식은 바뀔 수 있고 BOM은 제거된다(백업으로 대응). 대상 계정을 지워도 `targetAccountId`는 남는다(후속: 삭제 시 제거 여부 확인 UI). 테스트는 `homeDir`에 임시 폴더를 주입하고 실제 `~/.claude`를 절대 건드리지 않는다 |
| 금지 | `/api/oauth/usage` 호출, `anthropic-ratelimit-*` 헤더 조회, PTY `/usage` 스크래핑, `setup-token` |
| 미결(실측) | `claude -p`에서 statusline 실행 여부·trust 수락 필요 여부(T3), 줄바꿈 없는 프롬프트 직접 감지(`LongLivedProcess.onStdoutChunk`, T2 후 결정) |

### 7-2. Codex (`providers/codex`) — DECISIONS 02:23
| 단계 | 방법 |
|---|---|
| CLI 탐지 | `resolveCommand('codex')` → npm shim이면 `node.exe + …\@openai\codex\bin\codex.js`. `--version` |
| 폴더 | `CODEX_HOME` 폴더를 **spawn 전에 생성**(keyring 키가 canonicalize 경로 해시라서, RESEARCH 3-2) |
| env | set `CODEX_HOME=<profileDir>`, remove `OPENAI_API_KEY` `CODEX_API_KEY` 계열 |
| 연결 | `spawnLongLived(codex, ['app-server'])` + `createJsonRpcClient(dialect:'codex')` → `initialize {clientInfo:{name:'ai-usage-widget', version}}`(`experimentalApi` 없음) → 응답의 `codexHome`이 `profileDir`와 같은지 검증(다르면 `protocol-error`로 중단) → `initialized` 알림. 제한 init 30초 / rpc 10초 |
| 로그인 | `account/login/start {type:'chatgptDeviceCode'}` → `{loginId, userCode, verificationUrl}` → `device-code` 이벤트 → `account/login/completed` 알림 대기 → `account/read`로 email(마스킹)·planType → `success`. device code가 계정 설정에서 꺼져 있으면 `device-auth-disabled` |
| 수치 | `account/rateLimits/read` → `rateLimitsByLimitId` 각 버킷의 primary/secondary `{usedPercent, windowDurationMins, resetsAt(초)}` → `QuotaWindow`(kind는 분 단위로 분류, 버킷 id는 `label`). 결과를 받으면 프로세스 종료. `planType`은 모르는 값도 허용 |
| 금지 | `chatgptAuthTokens`, `apiKey`, `account/rateLimitResetCredit/consume`, `account/sendAddCreditsNudgeEmail`, `logout`, `~/.codex`·Orca 폴더 공유, `wham/usage` 직접 호출 |
| 확인된 스키마(codex-cli 0.154.0, 빈 CODEX_HOME) | `account/read`는 params 필수(`{}` 전송). 미인증 `rateLimits/read` → -32600 'codex account authentication required…'. `rateLimitsByLimitId`는 nullable이라 없으면 단일 `rateLimits` 사용. `account/login/cancel {loginId}` → `{status: canceled|notFound}`(중단·타임아웃 시 호출). `--version`도 CODEX_HOME을 초기화하므로 `<localDataRoot>\cli-detect\codex`에서 실행. shim 해석 불가는 `cli-unsupported-install` |
| 실측(T1, 26.09.20, codex 0.155.1, plan pro) | `account/rateLimits/read` = 버킷 `codex` 하나, `primary{usedPercent, windowDurationMins:10080, resetsAt(초)}`, **`secondary:null`**(5시간 창 없음 → 위젯은 주간 한 줄), `credits{hasCredits,unlimited,balance:'0'}`, 추가 필드 `ordinaryUsageAllowed`·`normalModelSlug`·`individualLimit`·`spendControlReached`·`rateLimitUpsell`·`accountId`(무시). 조회 약 1초. 로그인: `startLogin`은 세션을 열기 전에 같은 계정의 진행 중 작업을 중단하고 그 app-server 종료를 기다린다(`quiesce`) — 새 CODEX_HOME을 두 프로세스가 동시에 초기화하면 `protocol-error`(DECISIONS 26.09.20 10:51) |
| 미결 | verificationUrl 호스트(실계정 로그인은 성공했으나 호스트 기록 없음), 2번째 시도 `login-failed`의 원인, 조회가 auth.json을 다시 쓰는지, device-auth-disabled·login-expired·rate-limited·network 판정 문구(정규식 추정). credits·한도 도달 차단(`rateLimitReachedType`) 표시는 T1 후 계약 필드 추가 여부 결정. libuv가 HOMEDRIVE·HOMEPATH·USERNAME 등을 자식에 자동으로 다시 넣는다(자격증명 아님) |

### 7-3. Grok (`providers/grok`) — DECISIONS 02:23
| 단계 | 방법 |
|---|---|
| CLI 탐지 | `resolveCommand('grok')`, PATH에 없으면 `<homeDir>\.grok\bin\grok.exe` 후보. `--version` |
| env | set `GROK_HOME=<profileDir>`, remove `XAI_API_KEY` 계열. leader 모드는 켜지 않는다 |
| 로그인 | `grok login --device-auth`를 상주 실행해 출력의 URL·코드를 `device-code`로 방출, 폴링 완료(exit 0) → `success` |
| 수치 | `spawnLongLived(grok, ['agent','--no-leader','stdio'])` + `dialect:'jsonrpc2'`(ACP) → `initialize {protocolVersion:1}` → **`_x.ai/billing`**(ACP는 확장 메서드 앞에 `_`를 붙인다. 접두어 없는 `x.ai/billing`은 -32601, 그때만 한 번 더 시도) → 주간 창은 `currentPeriod.type`이 주간일 때 `creditUsagePercent` + `currentPeriod.end`, 그 외 `used/monthlyLimit`로 `other` 창(label `monthly`). 5시간 창은 없다. **100%를 차단으로 표시하지 않는다**(on-demand·선불 크레딧, 파서의 `overageAvailable`은 T4 후 계약 필드 추가 여부 결정). 두 메서드 모두 -32601이면 `unavailable`+`quota-unavailable`, -32000 'Authentication required' → `logged-out`. `getIdentity`는 billing 결과로 로그인 여부를 판단하고 판단 불가면 `ProviderError`; 같은 계정의 identity·usage가 15초 안에 이어지면 결과를 한 번만 조회해 공유 |
| ACP 규칙 | 세션·프롬프트를 만들지 않는다(쿼터 소모 금지). 호출은 `initialize`와 billing뿐, 끝나면 항상 프로세스 종료. 서버→클라이언트 요청(권한·파일)은 거부 응답. `initialize`는 확장 메서드 목록을 광고하지 않는다(실측) |
| 금지 | `/billing` HTTP 직접 호출, `auth.json` 읽기, OIDC refresh 직접 수행, Orca 값, `x.ai/auth/*`(check_subscription 포함, 부작용 미확인) |
| 실측(T4, 26.09.20, grok 1.0.34) | `_x.ai/billing` = `{config:{currentPeriod:{type:'USAGE_PERIOD_TYPE_WEEKLY',start,end}, onDemandCap:{val}, onDemandUsed:{val}, prepaidBalance:{val}, isUnifiedBillingUser, billingPeriodStart, billingPeriodEnd}, subscription_tier}`(0.8~0.9초). proto3 JSON이라 **0인 스칼라는 생략**된다: 주간 리셋 직후에는 `creditUsagePercent`가 없다. 파서는 weekly `currentPeriod` + 리셋 시각 + 동반 필드 2개 이상이 있을 때만 그 부재를 0%로 읽고, 필드가 있는데 못 읽는 값이면 미확인으로 둔다(DECISIONS 26.09.20 08:40). 같은 날 10:49 재조회에서 `creditUsagePercent: 29`가 나타나 "0일 때만 생략"이 확증됨(DECISIONS 26.09.20 10:51) |
| 미결 | `grok login --device-auth` 실제 출력(호스트·코드 형식·stdin 대기), 만료 토큰 자동 갱신 여부, 다중 GROK_HOME 동시 실행 |

### 7-4. Antigravity (`providers/antigravity`) — DECISIONS 26.09.19 11:42
| 단계 | 방법 |
|---|---|
| 계정 | **1개, 위젯 로그인 없음.** `PROVIDER_TRAITS.antigravity = {maxAccounts:1, widgetLogin:false}`(`src/shared/types.ts`). main은 `providerIsFull`로 두 번째 계정을 `conflict`로 거절하고, 렌더러는 [계정 추가]·[로그인] 버튼을 숨기고 안내 문구(`externalLoginHint`)를 보여 준다. 사용자가 터미널에서 `agy`로 로그인해 둔 상태를 그대로 쓴다(agy에 설정 폴더 오버라이드·login 서브커맨드 없음) |
| CLI 탐지 | `resolveCommand('agy')`, PATH에 없으면 `%LOCALAPPDATA%\agy\bin\agy.exe`. `--version` |
| env | `BASE_ENV_ALLOW` + set `AGY_CLI_DISABLE_AUTO_UPDATE=1`(자동 업데이터의 UAC 권한 상승 방지)·`NO_COLOR=1`, remove `GEMINI_API_KEY`·`GOOGLE_API_KEY` 계열. cwd는 위젯 소유의 빈 `profileDir` |
| 수치 | `run(agy, ['-p','/usage','--output-format','json','--print-timeout','30s'])`(하드 타임아웃 45초) → `command.data.groups[].buckets[]`의 `window`(`5h`→session, `weekly`→weekly, 그 외 other)·`remaining_fraction`(used = (1−x)×100, 범위 밖·비숫자는 null)·`reset_time`(ISO). 그룹 순서 유지, 그룹 안에서는 session→weekly, 버킷마다 `label`=그룹 이름(제어 문자 제거·40자 제한). 사람이 읽는 `response` 문자열은 파싱하지 않는다. 실측(agy 1.2.6·1.2.7): 6.9~8.6초, `num_turns:0`·토큰 0 |
| 차단기 | 응답이 `command.name==='usage'` + `num_turns===0`이 아니면(슬래시가 AI 프롬프트로 처리됨) 앱을 다시 켤 때까지 agy를 호출하지 않고 `unavailable`+`cli-unsupported-version`. 요청 소모를 1회로 제한한다 |
| 신원 | `/usage` 성공 = `loggedIn:true`(e-mail·plan은 제공되지 않음). 로그아웃 문구가 보이면 `logged-out`, 그 외 실패는 `ProviderError`(unknown). identity·usage가 15초 안에 이어지면 agy 실행 1회를 공유하고, 같은 계정의 동시 호출도 한 실행을 공유한다 |
| 금지 | wincred(`gemini:antigravity`) 읽기, 로컬 language server RPC, `cloudcode-pa` 직접 호출, Orca 값(RESEARCH 3-5) |
| 미결 | 로그아웃 상태의 실제 출력 문구(현재 정규식은 추정), 위젯 막대에 표시할 그룹 선택(현재 첫 그룹) |

---

## 8. 셸(main) 설계 요점

- **부트스트랩**(`index.ts`, 스캐폴드 구현됨): `configureUserData` → `setAppUserModelId('local.aiusagewidget')` → `registerSchemesAsPrivileged(app: standard+secure)` → 단일 인스턴스 락 → `hardenApp` → ready 후 `hardenSession`·`protocol.handle('app')`·registry·창 생성·IPC 등록. `--smoke`는 두 렌더러의 `app:renderer-ready`(CSP eval 차단 확인 포함)를 기다려 JSON 보고서를 쓰고 스스로 종료(0 성공 / 1 실패 / 2 강제 타임아웃).
- **store**: 쓰기는 `<file>.<ts>.tmp` → rename. 로드는 `normalizeSettings`·계정 검증. 빈 계정 배열을 존중(기본 계정 부활 없음, V1-15). 계정 객체는 복사해서 넘긴다(V1-04). 쓰기가 성공한 뒤에만 메모리를 바꾸고, 파싱 안 되는 본 파일은 `.bak`을 덮지 않는다. 계정 변경(add·remove·rename·toggle·reorder)은 컨트롤러에서 한 번에 하나씩 실행한다. 로그인 여부는 identity가 기준이라 logged-out으로 확인된 계정은 identity 재조회(30분·로그인 성공·수동 새로고침) 전까지 수치를 조회하지 않는다(DECISIONS 04:49).
- **login 세션**: `sessionId = randomUUID()` 기반 id, 세션마다 AbortController, 계정당 동시 1개. 방출된 URL 목록을 세션에 보관해 `shell:open-external {kind:'login'}` 검증에 쓴다. 세션 종료 시 목록 폐기.
- **재인증 알림**: 공급자 identity/사용량 조회가 확정된 `logged-out`을 반환하면 계정당 한 번 Windows 알림을 보낸다. 알림 클릭은 기존 계정 관리 탭을 열고 Claude·Codex·Grok의 공식 CLI 로그인 세션을 시작한다(이미 복구된 계정은 열기만 함). Antigravity는 자체 CLI 터미널 로그인 안내만 보여 준다. 네트워크 오류·상태 미확인에는 알리지 않으며 로그인 성공 또는 정상 수치 복귀 후 다시 만료되면 재알림한다. `--smoke`에서는 알림을 내지 않는다.
- **창·위치**: 위젯은 `screen` workArea/bounds 차이 + `display-added/removed/metrics-changed`로 재배치, 자동 숨김·좌우 작업 표시줄은 koffi `SHAppBarMessage`(실패 시 해당 기능만 끄고 폴백, V1-18·29). docked 최상위 유지는 koffi `SetWindowPos(HWND_TOPMOST)`를 같은 HWND에 재기동 없이(V1-12·28), 전체화면 감지는 koffi로 전경 창·모니터 비교 후 `showInactive()` 복원(V1-30). TaskbarDock.exe는 쓰지 않는다.
- **팝업**: 위젯/트레이 클릭은 잠금 없이 열고 blur 시 숨김. 설정 조작 중에만 `window:set-popup-lock`(V1-09). 잠금 중에 온 blur는 기억했다가 잠금이 풀리면 숨긴다. 재질 전환으로 창을 다시 만들면 열려 있던 팝업을 설정 탭으로 다시 연다. 위젯 이동·디스플레이 변경 시 열린 팝업도 재배치(V1-27). 단 위치 미리보기 중에는 팝업을 옮기지 않고 미리보기 해제·설정 저장 때 재배치한다(슬라이더 되먹임 방지, DECISIONS 26.09.15 05:10).
- **트레이**: 메뉴 `trayToggleWidget`·`trayOpenPopup`·`trayAutoLaunch`·`trayRefreshNow`·`trayAccounts`·`trayQuit`. 문구는 `shared/i18n`.
- **자동 시작**: `setLoginItemSettings({openAtLogin, path: process.execPath, args:['--autostart']})`, 조회도 같은 path·args(V1-31). `--autostart`/`--hidden`이면 위젯만 비활성 표시. Run 값 이름은 v1의 `electron.app.AI Usage Widget`과 달라야 한다(appUserModelId/productName 확인은 T8에서).
- **second-instance**: 기존 인스턴스가 위젯 표시 + 팝업 열기(V1-32, 스캐폴드에 최소 처리 있음).

---

## 9. 렌더러 설계 요점

- 프레임워크 없는 TS/DOM. HTML 문자열 금지: `h()`(`src/renderer/src/dom.ts`)처럼 `createElement`·`textContent`만 쓴다. ESLint가 `innerHTML`·`outerHTML`·`insertAdjacentHTML`·`document.write`를 막는다(V1-06).
- 상태 변경 시 전체 재렌더 대신 키 기반 부분 갱신, 입력·포커스·스크롤 보존, 애니메이션은 표시할 때만(V1-25·26).
- 위젯 막대: 계정별 아이콘·5H/주간 값·리셋 카운트다운(매초가 아니라 분 단위로 로컬 재계산), **새로고침 버튼**(회전 표시, `refresh` 상태 기준 비활성). 빈 상태 클릭 → 팝업 계정 탭.
- 수치 단위는 위젯 값 옆에 `남음`/`left` 또는 `소모`/`used`로 직접 표시한다. 팝업 수치는 항상 소모율이므로 `소모`/`used`를 붙인다.
- 빠른 소모 강조는 실제 토큰 개수가 아닌 **계정별 한도 사용률 증가**를 비교한다. 위젯 실행 중 쌓인 같은 창의 관측치로 최근 15~30분과 앞선 45~90분을 비교해 최근 증가가 3%p 이상·시간당 6%p 이상·이전의 2배 이상이고, 여러 번 나누어 증가한 경우에만 계정 테두리와 hover 말풍선을 표시한다. 리셋·조회 실패·미확인 수치·단일 지연 업데이트는 제외한다. 이력은 메모리에만 있어 재시작 후 약 1시간의 학습이 필요하며, 말풍선은 한도 사용률 추정임을 밝힌다.
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
| 01 | customMock을 정상 값으로 표시 | 계약 `usedPercent:null`, `applyFetchFailure` / codex·claude·grok·renderer | 완료(위젯도 조회 실패 시 마지막 실측값을 흐리게 + '!', 리뷰 1차) |
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
| 12 | 슬라이더마다 저장·staytop 재기동 | renderer 드래그 중 `window:preview-placement` 미리보기(저장 없음)·확정 1회 저장, 미리보기 중 팝업 고정(되먹임 방지), shell koffi 재기동 없음 | 완료(리뷰 2차, 드래그 체감은 T8 실측) |
| 13 | node:sqlite 추정 | 제거 | 해당 없음 |
| 14 | 자동 실행 기본 ON, `--hidden` 미사용 | 기본 false, `--autostart/--hidden` 파싱 / shell | 계약·인수 파싱 완료 |
| 15 | 기본 계정 부활 | shell store 빈 배열 존중 | — |
| 16 | fetch 타임아웃 없음·전체 정체 | `cli/spawn` 타임아웃, 계정별 즉시 브로드캐스트 / shell | spawn 완료 |
| 17 | weekly 라벨 오표시 | `kind`를 창 길이로 분류 / providers | 계약 완료 |
| 18 | 좌우·자동 숨김·보조 모니터 | shell platform/taskbar(koffi) | **부분**: 좌우·자동 숨김(floating 폴백 + 설정 탭 안내)·최대화 창 판정 완료. 보조 모니터 선택은 보류(사용자 결정, DECISIONS 04:49) |
| 19 | exe 선택 기준·stdin error | `resolveCommand` 고정 규칙, stdin error 처리 | 완료(Authenticode 확인은 하지 않음, DECISIONS 04:49) |
| 20 | 렌더러 입력 무검증 | `shared/ipc` 검증기, `clampWidgetSize` | 완료 |
| 21 | 앱 내 OAuth 결함 | 앱 내 OAuth 없음 | 해당 없음 |
| 22 | 배포 번들 Mock API·테마 조건 | mock은 테스트만 / renderer | — |
| 23 | isRefreshing 항상 false | `RefreshStatus` / shell·renderer | 계약 완료 |
| 24 | 오류 삼킴·영구 loading | ErrorCode + i18n / shell·providers | 계약 완료 |
| 25 | 전체 재렌더 | renderer 키 기반 부분 갱신, 표시 애니메이션은 `popup:show` 때만 | 완료(리뷰 1차) |
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
| `antigravity` | `src/main/providers/antigravity/**` |
| `renderer` | `src/renderer/**`, `src/preload/**` |

계약(어느 모듈도 수정 금지): `src/shared/**`, `src/main/cli/**`, `src/main/log.ts`, `src/main/log.test.ts`, `src/main/paths.ts`, `src/main/paths.test.ts`, `src/main/providers/types.ts`, `src/main/providers/registry.ts`, `src/main/providers/registry.test.ts`, `src/main/providers/placeholder.ts`, `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `tsconfig.json`, `tsconfig.node.json`, `tsconfig.web.json`, `eslint.config.mjs`, `vitest.config.ts`, `electron.vite.config.ts`, `electron-builder.yml`, `.gitignore`, `.gitattributes`, `.editorconfig`, `CLAUDE.md`, `DECISIONS.md`(append만), `docs/DESIGN.md`.

모듈 공통 완료 조건
- `pnpm verify` 종료코드 0, `pnpm build` 종료코드 0.
- 자식 프로세스는 `cli/spawn.ts`만, 경로는 `ProviderDeps`/`paths.ts`만 사용.
- 실제 로그인·로그아웃·계정 전환 실행 금지, 실제 자격증명 파일 읽기 금지. CLI 기능 탐색은 `C:\Users\202502\AppData\Local\Temp\claude\widget-v2-build\` 아래 **새 빈 HOME**에서 타임아웃을 걸고 로그인 메서드를 부르지 않는 범위만.
- 수치·계정이 필요한 테스트는 테스트 코드 안의 고정 fixture만 사용(앱 코드에 mock 금지).

---

## 14. i18n 키 변경 기록(v1 86키 기준)

- **유지(이름 그대로)**: `trayToggleWidget` `trayOpenPopup` `trayAutoLaunch` `trayRefreshNow` `trayQuit` `trayTooltip` `popupTitle` `accountsActive` `refresh` `close` `tabUsage` `tabAccounts` `tabSettings` `noActiveAccounts` `addAccountHint` `sessionLimit5h` `resetLabel` `weeklyLimit` `moveUp` `moveDown` `deleteAccountTitle` `deleteAccountBtn` `redetect` `checkedAccountsHint` `save` `cancel` `confirmDeleteAccount` `widgetTheme` `theme1a`~`theme1d` `iconStyleLabel` `iconColor` `iconMono` `launchAtLogin` `colorByUsageLabel` `showCardBg` `showUsedPercentLabel` `placementLabel` `placementDocked` `placementFloating` `alwaysOnTopLabel` `alwaysOnTopDesc` `alignmentLabel` `alignRightFloating` `alignRightDocked` `alignLeftFloating` `alignLeftDocked` `offsetLabel` `alphaLabel` `refreshIntervalLabel` `interval15`~`interval300` `unitUsed` `unitLeft` `widgetTooltip` `widgetTooltipNoWeekly` `noAccountTitle` `widgetClickTitle`. 문구 정정: `accountsActive`(복수형 회피), `resetLabel`("리셋: -- 남음" 제거), `alphaLabel`·`noAccountTitle`(V1-35), "작업 표시줄" 표기 통일, `confirmDeleteAccount`(격리 폴더 삭제 안내).
- **이름 변경**: `trayAddGoogle`→`trayAccounts`(계정 관리 열기), `modelQuotaTitle`→`otherWindowsTitle`, `detectingApps`→`detectingCli`, `localInstallDetected`→`cliDetected`/`cliDetectedNoVersion`, `loginFailedAlert`→`loginFailed`.
- **삭제**(mock·Google OAuth·로컬 IDE 전용): `localIdeNoAuth` `runningNow` `presetReady` `added` `addToWidget` `localDetectTitle` `addCustomAccountTitle` `accountAlias` `iconLetterLabel` `brandColorLabel` `usage5h` `usageWeekly` `addGoogleOAuth` `addManually` `resetDefaults` `confirmResetDefaults`.
- **추가**: 창·상태(`windowOtherMinutes` `percentUnknown` `resetUnknown` `lastMeasured` `neverMeasured` `sourceLabel` `errorDetail` `state_*` `source_*` `provider_*`), 새로고침(`widgetRefresh` `refreshing`), 계정(`addAccountFor` `accountLabelLabel` `accountLabelPlaceholder` `rename` `enableAccount` `cliNotFound` `cliInstallGuide`), 로그인(`login*`, `loginStage_*`, `loginState_*`), 브리지(`bridge*`), 테마·언어(`themeWindows` `material*` `language*` `showWeeklyLimitLabel` `verticalOffsetLabel` `pixels` `placementFallbackHint`), 오류(`error_*` 21개).
- **리뷰 1차(26.09.15 04:49)**: 참조 0건 키 삭제 `trayAddAccount` `realtimeMonitoring` `usageLabel` `addAccountTitle`. 추가 `placementFallbackHint` `bridgeRemoveBeforeUninstall`. `redetect`는 계정 탭 공급자 헤더의 '다시 감지' 버튼에서 쓴다. `bridgeInstallNote`에 백업 위치·제거 전 복원 안내를 넣었다.

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

# SPEC — v1 baseline (AI Usage Widget 1.0.2)
> 생성물 성격: v1 빌드 산출물에서 추출한 참고 명세. v1 원본은 수정 금지. 작성 26.09.15 KST · Claude Code

- 출처: `M:n` = `resources/app/dist-electron/main.js` n행, `R:n` = `dist/assets/index-Cr6Kc0g0.js` n행, `CSS .sel` = `dist/assets/index-BmVKEU5y.css`(1행) 선택자, `P` = `dist-electron/preload.cjs`, `C#:n` = `resources/app/native/TaskbarDock.cs` n행.
- 표시: **[제외]** v2에서 버리는 mock·가짜 데이터(§7) / **[결정]** v2가 정해야 함 / **V1-NN** §6 항목. CSS의 `MONO` = `Cascadia Code,Consolas,monospace`.
- 근거는 정적 읽기와 스크립트 대조뿐이다(실행·렌더 실측 없음). "추정" 치수는 글꼴 측정에 따라 달라진다. 추출본 간 모순은 코드를 다시 읽어 확정했다(§8-1).

---

## 0. 요약

1. **구성**: Electron 34.5.8, 프레임워크 없는 Vite 번들(템플릿 문자열 → `innerHTML`). 창 2개(투명 위젯 막대, 팝업 380×440), 트레이, .NET 헬퍼 `TaskbarDock.exe`(실사용 명령 `staytop`·`fswatch`).
2. **위젯**: 활성 계정마다 브랜드 아이콘, 5H·주간 %(기본 남은 %, 옵션 소모 %), 리셋 카운트다운. 테마 4종(1a 바 게이지 / 1b 10칸 세그먼트 / 1c 이중 링 / 1d 초압축). 색은 소모율 ≥85 `#F43F5E`, ≥60 `#F97316`, 그 외 `#10B981`.
3. **크기·위치**: 렌더러 실측(`w+24`, `max(34,h+4)`) → main `Ee()` 재배치. docked(작업표시줄 위에 겹친 최상위 창, 트레이 220px 왼쪽) / floating(작업표시줄 4px 위), 좌/우 정렬, 오프셋 0-350px.
4. **팝업**: 위젯·트레이 클릭으로 토글(열 때 포커스+잠금). 헤더(제목·활성 수 배지·↻·×) + 탭 3개(사용량 현황 / 계정 관리 / 위젯 설정).
5. **사용량 탭**: 계정 카드(아이콘 24, 이름, email·projectId·오류, tier 배지, 5시간·주간 소모 % 박스, 모델별 쿼터).
6. **계정 관리**: 로컬 앱 감지(Antigravity / Claude Code / Codex CLI)와 원클릭 추가, 활성 체크, ▲▼ 순서, 삭제(confirm), Google OAuth, 기본값 복원.
7. **설정**: 컨트롤 12개. 변경마다 `config.json` 통째 저장 후 위젯 즉시 반영. 갱신 주기 15-300초(main 최소 10초).
8. **창 정책**: 항상 위(`screen-saver`, 9999) + docked staytop 600ms + 2초 `moveTop`. 같은 모니터 전경 창이 전체화면이면 자동 숨김. 단일 인스턴스, 로그인 자동 실행 기본 ON, 트레이 메뉴 6항목.
9. **i18n**: ko/en 86키. 렌더러·main 사전이 문자 단위로 같다(스크립트 대조). 로케일이 `ko`로 시작하면 ko.
10. **v2 필수 차이**: 가짜 수치(customMock·Mock API·하드코딩 감지 목록)와 사칭 경로 제거, 실패는 error/unknown + 마지막 실측값·시각. §6 V1-01~43 전부 해결.

---

## 1. 데이터 모델·설정·IPC

### 1-1. 영속화 (`yt` AccountStore, M:117-248)

| 항목 | v1 동작 | 근거 |
|---|---|---|
| 위치 | `app.getPath("userData")`(실패 시 `cwd/.data`), 없으면 생성. `app.name="ai-usage-taskbar-widget"`(M:2174) → `%APPDATA%\ai-usage-taskbar-widget` | M:123-129 |
| 파일 | `config.json`, `accounts.json`, `JSON.stringify(x,null,2)` 평문 | M:129,171,174 |
| 설정 로드 | `{..._e, ...JSON.parse(file)}`, 실패 시 `{..._e}` | M:131-141 |
| 계정 로드 | 배열이고 `length>0`일 때만, 아니면 `[...Oe]`(전부 지우면 다음 기동에 부활, V1-15) | M:142-153 |
| 쓰기 | `${path}.${Date.now()}.tmp` 쓰기 후 rename, 실패 시 직접 쓰기+tmp 삭제 | M:154-169 |
| `saveConfig(e)` | 기본값 병합 없이 통째 교체. 렌더러는 항상 `{...state.config, key:v}` 전체 전송 | M:170-172, R:378 |
| 공유 참조 | `getAccounts()`는 배열만 얕은 복사 → fetch 중 `e.tokens` 변경(M:447,463)이 저장소 객체·상수 `Oe`에 반영(V1-04) | M:179-181 |

### 1-2. `AppConfig` (`_e`, M:43-58)

| 키 | 기본 | 범위·UI | main 효과 | 렌더러 효과 |
|---|---|---|---|---|
| `theme` | `"1a"` | 1a~1d 버튼 | — | `1b→Ae`, `1c→we`, `1d→ye`, 그 외 `he` (R:473) |
| `iconStyle` | `"color"` | color/monochrome | — | §2-2. mono 적용 범위는 테마마다 다름(V1-33) |
| `alignment` | `"right"` | right/left | `Ee()` x | 라벨만 모드별로 바뀜, DOM 영향 없음 |
| `offsetPx` | `20` | range 0-350 | `Ee()`: `max(0, offsetPx ?? 20)` | 라벨 `{n}px` |
| `verticalOffsetPx` | `0` | 제한 없음, **UI 없음** | `Ee()` y에 가산(M:1863,1866) | `--vertical-offset`(쓰는 CSS 0건) |
| `refreshIntervalSec` | `60` | select 15/30/60/120/300 | 시작 `startPolling(sec)`(즉시 1회), 변경 `startPolling(sec,false)`, 주기 `max(10,sec)*1000`(M:1829) | — |
| `alphaPercent` | `85` | range 10-100 | — | `--bg-alpha=clamp(a/100,.1,1)`, `no-card-bg`면 무효 |
| `showWeeklyLimit` | `true` | **UI 없음** | — | 1a/1b: `!==false && !!weeklyQuota`일 때만 WK 행. 1c/1d 무시 |
| `colorByUsage` | `true` | 스위치 | — | `C()` 임계색, 끄면 5H=`usage.brandColor`, WK=`#9CA3AF` |
| `showCardBackground` | `true` | 스위치, floating 선택 시 강제 true | — | `.has-card-bg`/`.no-card-bg`, 렌더러 fallback `?? false`(R:471) |
| `showUsedPercent` | `false` | 스위치 | — | 위젯 값 used/left, 툴팁 `{unit}`. **팝업은 항상 percentUsed** |
| `placementMode` | `"docked"` | docked/floating | `Ee()` 분기, `Ze()`(§4-1) | "항상 위" 그룹 표시, 정렬 라벨 |
| `alwaysOnTop` | `true` | 스위치(floating만 보임) | floating에서만 의미, docked 무시(M:2195) | `checked = !==false` |
| `openAtLogin` | `true` | 스위치 + 트레이 체크 | `Ie()`(§4-7) | 체크 |

**UPDATE_CONFIG 순서** (M:2403-2405): ① 이전 설정 보관, `saveConfig(e)` → ② `openAtLogin` 변경·not undefined면 `Ie()`(트레이 재구성) → ③ `refreshIntervalSec` 변경 시 `startPolling(new,false)` → ④ `ue()` bounds 재적용 → ⑤ `Ze(e)`(docked면 staytop 재기동) → ⑥ `Q()` 후 `z()` 반환. ④⑤는 매번 실행.

### 1-3. 계정 `Account` (`accounts.json`)

| 필드 | 규칙 | 근거 |
|---|---|---|
| `id` | 기본 `local-antigravity` `local-claude-code` `local-codex` `google-gemini`, OAuth `google-${now}`, 커스텀 `custom-${now}` | M:58-116,2410,2427 |
| `name` | 표시명. OAuth는 email `@` 앞 | M:2411 |
| `provider` | `antigravity` `claude` `codex` `google` `custom`, fetch 분기 기준 | M:1791-1808 |
| `enabled` | 위젯·사용량 탭 표시 여부 | M:1731-1738 |
| `isLocalIde?` | antigravity만 true, 계정 탭 부제 `localIdeNoAuth` | M:64,225; R:139 |
| `tokens?` | `{accessToken, refreshToken, expiresAt(ms, 없으면 now+3600000), email?, projectId?}` 평문(V1-05) | M:2414-2420 |
| `customMock?` | `{primaryPercent, primaryReset, weeklyPercent, weeklyReset, iconLetter, brandColor}` **[제외]** | M:65-72 |

**기본 계정 `Oe`** (M:58-116, 4개 모두 customMock — grep 4건, 모두 enabled): `local-antigravity` "Antigravity (Local IDE)" `isLocalIde:true` / `local-claude-code` "Claude Code" / `local-codex` "Codex CLI" / `google-gemini` "Gemini Advanced". 문구는 "3대"인데 4개(V1-15).

| 연산 | 동작 | 근거 |
|---|---|---|
| `addAccount(a)` | 같은 `id` 또는 `tokens.email`이면 `{...old,...a,enabled:true}` 병합, 아니면 끝에 추가 | M:182-188 |
| `restoreDetectedAccount(app)` | `{id,name,provider,enabled:true,isLocalIde:id==="local-antigravity",customMock}` → addAccount (customMock **[제외]**) | M:189-229 |
| `resetToDefaultAccounts` / `removeAccount` / `toggleAccount` | `[...Oe]` / filter / enabled 변경, 저장 | M:230-239 |
| `reorderAccount(id,"up"/"down")` | 이웃과 swap, 범위 밖 무시 | M:240-247 |

**감지 앱 `DetectedApp`** (`At.detectAll`, M:1881-1947): `{id,name,provider,installed,running,description,iconLetter,brandColor}`, 항상 3개·이 순서.

| id / name | installed | running | brand |
|---|---|---|---|
| `local-antigravity` / Google Antigravity | 항상 true | `language_server` 프로세스(30초 캐시) | `#2563EB` |
| `local-claude-code` / Claude Code | `where.exe claude` 또는 `~/.claude/.credentials.json` 존재 | 그 파일에 `claudeAiOauth.accessToken` | `#D97757` |
| `local-codex` / Codex CLI | codex.exe 탐색, `where.exe codex`, auth.json 중 하나 | `%APPDATA%/orca/codex-runtime-home/home/auth.json` 또는 `~/.codex/auth.json` 존재 | `#6366F1` |

`description`(한국어 고정)은 렌더러가 안 쓴다. 부제 = `running ? runningNow : installed ? localInstallDetected : presetReady`(R:154).

### 1-4. 사용량 `QuotaUsage`

```ts
interface QuotaInfo { remainingFraction: number; percentLeft: number; percentUsed: number /*정수 0..100*/;
  resetTime?: string; resetCountdown: string /*j() 또는 "--"*/; isExhausted: boolean }
interface ModelQuota { modelId: string; displayName: string; quota: QuotaInfo }
interface QuotaUsage { id: string; name: string; provider: string; iconLetter: string; brandColor: string;
  email?: string; tier?: string; projectId?: string; status: "ready" | "loading" | "error"; errorMessage?: string;
  primaryQuota: QuotaInfo; weeklyQuota?: QuotaInfo; models?: ModelQuota[]; updatedAt: string }
```

| 소스 (조건) | icon/brand | tier | email·project | models | 근거 |
|---|---|---|---|---|---|
| Antigravity 로컬 LSP (`antigravity`‖`isLocalIde`) | A `#2563EB` | `${planName‖"Pro"} (로컬 감지)` | userStatus.email | Gemini 최고 버전 1개, 없으면 `Gemini (대표 모델)` | M:664,723-751 |
| Antigravity 클라우드 (로컬 null/error/목업 시, ready면 대체) | A `#2563EB` | `${currentTier.name‖"Antigravity Pro"} (클라우드 세션)` | vscdb profile/tokens.email | 최고 1개 | M:892-1001,1792-1798 |
| Claude | C `#D97757` | `${(subscriptionType‖"Pro").toUpperCase()} (실시간 세션)` | — | 없음 | M:1017-1045 |
| Codex app-server (1순위) | X `#6366F1` | `${formatPlanName} (공식 app-server)` | account.email | `codex-5h` "Codex 세션 한도 (5시간)", `codex-weekly` "Codex 주간 한도 (7일)" | M:1282-1363 |
| Codex Orca (2순위) | X `#6366F1` | `${workspaceLabel‖"Personal (Plus)"} (Orca 직결)` | systemDefault.email | `gpt-5.6-terra` "Codex (5시간)", `…-weekly` "Codex (1주일)" | M:1433-1492 |
| Codex 로컬 추정 (3순위) | X `#6366F1` | `${plan} (로컬 세션)` | JWT email | 최근 thread model 1개 | M:1552-1666 |
| Google CloudCode (`tokens`‖`google`) | G `#4285F4` | `currentTier.name‖"Standard"` | tokens.email, `cloudaicompanionProject` | 최고 Gemini 1개 | M:440-567 |

`isExhausted`: 로컬·클라우드·Google `remainingFraction<=0.01`, Claude `percentUsed>=100`, app-server·Orca `percentLeft<=1`, 로컬 추정 `>=100`. Codex 로컬 추정은 3시간/7일 토큰 합 ÷ 200,000/2,000,000, weekly 리셋 `"--"` 고정(V1-40). `Ve.fetchClaudeUsage`(M:1496-1529)는 호출 0건.

**status 결정** (M:1786-1819 재확인)

| 조건 | 결과 |
|---|---|
| 공급자 정상 | 그 값(`ready`) |
| `getFallback` 비mock 분기(Claude M:1107-1123, Codex M:1691-1707, Antigravity M:777-800) | `error`+`errorMessage`. Claude·Codex는 weekly 없음, Antigravity는 0%/`--` weekly |
| `r` null(Google `wt` 예외 M:1806, Antigravity 클라우드 예외 M:1796은 warn 후 삼킴) | `createInitialUsage` 비mock: `loading`, brand `#4285F4`, primary 0%/`--`, **weekly 없음**(M:1762-1777) |
| 공급자 함수 throw(M:1815 catch) | 기존(없으면 initial)에 `status="error"`, `errorMessage=err.message` |
| customMock + (null 또는 error) | **[제외]** mock `ready`, 원결과에 errorMessage가 있으면 tier `목업 (로컬 대기)`(M:1809-1812) |

- 화면에 나오는 errorMessage 원문: `Antigravity 미실행`(M:650), `Antigravity 연결 대기 중`(M:663), `Claude 로그인 세션 파일 없음 (~/.claude)`(M:1012), `Claude OAuth 토큰 누락`(M:1016), `Anthropic 사용량 응답 오류`(M:1019), Claude 예외 message(M:1048), `Codex 세션 파일 없음 (~/.codex/auth.json)`(M:1565). `Account has no authentication tokens`(M:457)·`fetchAvailableModels failed`(M:502/935)·`Google OAuth Client ID/Secret 환경변수…`(M:868)는 삼켜져 표시되지 않는다(V1-24).
- **[결정]** mock 제거 시 토큰 없는 `google-gemini`는 영원히 `loading` → v2는 error/unknown + 원인.
- 렌더러는 weekly 부재 시 `percentLeft ?? 100`, `percentUsed ?? 0`, `resetCountdown || "--"`(R:90,126,378). TypeError 없음.

**`resetCountdown` = `j(i)`** (M:423-437): falsy·NaN → `"--"` / ≤0 → `"0m"` / ≥1일 `${d}d ${h%24}h`(`5d 8h`) / ≥1시간 `${h}h ${mm}m`(분만 2자리, `3h 07m`) / 그 외 `${m}m`. floor. **조회 시점 문자열로 굳어** 다음 갱신까지 줄지 않고, 캐시 적중(Claude·클라우드·Codex 로컬 15초, app-server 10초) 시 옛 문자열. 예외: Codex 로컬 sqlite `${h}h ${m}m`(0 채움 없음, M:1611-1614), Orca는 resetsAt 없으면 `resetDescription` 원문(M:1438,1501).

**갱신 루프** (`kt`, M:1711-1837): `refreshAll()`은 `isRefreshing`이면 즉시 현재 값 반환 → 비활성 캐시 삭제 → `Promise.allSettled` 병렬 → `finally` `notify()`→`Q()`. 분기 `antigravity‖isLocalIde` → `claude` → `codex` → `tokens‖google`(`custom`은 fetch 없음). `startPolling(sec,immediate=true)`: 타이머 교체, `max(10,sec)*1000`, immediate면 즉시 1회.

### 1-5. 앱 상태와 IPC

`z()`(M:2181-2189) = `{config, accounts, usages, isRefreshing:false, lastRefreshedAt:new Date().toISOString()}`. usages는 enabled만 계정 순서(순서 = 위젯 표시 순서). `isRefreshing` 항상 false(V1-23), `lastRefreshedAt`은 스냅샷 시각, accounts는 tokens째 전송(V1-05). `Q()`(M:2190-2193)는 두 창에 `state:changed`.

preload(`P`): `exposeInMainWorld("api")` invoke 래퍼 20개 + `onStateChange(cb)`(payload만, 해제 함수 반환). 상수 21개(M:21-43), handle 20개(M:2403-2459). `contextIsolation:true`, `nodeIntegration:false`, sandbox 기본. `preload.js`(14채널 구버전) 미사용(M:2170-2173).

| # | 채널 (preload) | 반환 | main 동작 | 렌더러 호출처 |
|---|---|---|---|---|
| 1 | `app:get-state` (`getState`) | AppState | `z()` | 두 뷰 초기화 R:477 |
| 2 | `app:update-config` (`updateConfig(config)`) | AppState | §1-2 순서 | 설정 탭 16곳 R:378 |
| 3 | `app:refresh-quota` (`refreshQuota`) | AppState(갱신 후) | `await refreshAll(); Q(); z()`(브로드캐스트 2회, V1-39) | ↻, 다시 감지 직후 |
| 4 | `account:add-google-oauth` (`addGoogleAccount`) | `{success,error?}` | 루프백 OAuth(180초) → `addAccount({id:"google-"+now,name,provider:"google",enabled:true,tokens})` → await refresh → Q. 실패 `error‖"Login canceled or failed"`(M:2406-2424) | `#btn-add-google`, 실패 `alert(loginFailedAlert)` |
| 5 | `account:add-custom-account` (`addCustomAccount`) | AppState | **[제외]** `{id‖"custom-"+now, name‖"Custom Account", provider‖"custom", enabled:true, customMock}` → 비동기 refresh+Q(M:2425-2440) | `#btn-save-custom` |
| 6 | `account:restore-detected-app` (`restoreDetectedApp(app)`) | AppState | restore → 비동기 refresh+Q | `.btn-add-detected` |
| 7 | `account:reset-default-accounts` (`resetDefaultAccounts`) | AppState | `[...Oe]` → 비동기 refresh+Q | `#btn-reset-defaults`(confirm) |
| 8 | `account:toggle-account` (`toggleAccount(id,en)`) | AppState(갱신 전) | 저장 → 비동기 refresh+Q | `.chk-account` |
| 9 | `account:remove-account` (`removeAccount(id)`) | AppState | 저장 → 즉시 Q(refresh 없음) | `.btn-delete-account`(confirm) |
| 10 | `account:reorder-account` (`reorderAccount(id,dir)`) | AppState | swap → 즉시 Q | `.btn-move-up/down` |
| 11 | `window:show-popup` | void | `Ae(false,false)` | **0건** |
| 12 | `window:hide-popup` | void | `pe(true)` | ×(unlock 뒤), Esc |
| 13 | `window:toggle-popup` | void | `tt()` | 위젯 클릭 |
| 14 | `window:lock-popup` | void | `te=true; ae()` | accounts/settings 탭, 오프셋 슬라이더 누름 |
| 15 | `window:unlock-popup` | void | `te=false` | × |
| 16 | `window:resize-widget` (`resizeWidget(w,h)`) | void | 둘 다 >0이면 `ee/ie=round` + `ue()`, 상한 없음(V1-20) | 위젯 렌더 후 rAF |
| 17 | `state:changed` (`onStateChange`) | push | `Q()`, 팝업 새로 표시 때도(M:2283) | 팝업 `E()`, 위젯 `X()` |
| 18 | `window:open-settings` | void | `Ae(true,true)`, 탭 전환 없음 | **0건** |
| 19 | `app:detect-local-apps` | DetectedApp[] | `At.detectAll()` | `#btn-detect-apps` |
| 20 | `window:schedule-hide-popup` (`ms?`) | void | `et(ms‖400)` | **0건** |
| 21 | `window:cancel-hide-popup` | void | `ae()` | **0건** |

---

## 2. 위젯 테마 1a~1d

### 2-1. 렌더 파이프라인 (R:471-477)

1. 뷰: `?view=` → `#view=` → hash에 `popup`이면 popup, 아니면 widget. `body.is-widget-view` / `body.is-popup-view`(규칙 없음), `documentElement.lang`=ko/en.
2. `Le()`: `await getState()` → `X(state)` → `onStateChange(X)`.
3. `X()`: `--bg-alpha`·`--vertical-offset` 설정 → usages 0개면 빈 상태, 아니면 테마 함수 결과 `join("")` → 루트 `<div class="widget-root {is-empty?} {has-card-bg|no-card-bg}" id="widget-container" title="{widgetClickTitle}">`.
4. 캐시 키 `` `${html}_${showCardBackground}_${theme}_${iconStyle}` ``가 바뀌면 `innerHTML` 교체 → rAF에서 `#widget-container` 실측, `w=ceil(width)+24`, `h=max(34,ceil(height)+4)`, 직전 전송값(`F`/`N`)과 다를 때만 `resizeWidget`. 루트 34 고정이라 높이는 사실상 **38**.
5. 빈 상태: `<div class="widget-root is-empty …"><div class="white-circle-dot" title="{noAccountTitle}"></div></div>`.
6. DOM을 매번 새로 만들어 `.progress-fill`(width .4s)·`.segment-rect`(fill .2s) transition이 실제로는 안 보인다. **[결정]** v1처럼 애니메이션 없음 / 요소 재사용으로 살림.

### 2-2. 공통 헬퍼

**색 `C(pctUsed, colorByUsage, fallback)`** (R:1): `t ? (e>=85?"#F43F5E":e>=60?"#F97316":"#10B981") : n`. 임계는 표시 모드와 무관하게 **percentUsed 기준**.

**브랜드 `V(provider,name)`** (R:38): provider 소문자 일치 또는 name 소문자 포함, 먼저 맞는 항목.

| # | 조건 | name | 그림 | brand |
|---|---|---|---|---|
| 1 | `antigravity` / `antigravity` `agy` | Antigravity | PNG(`dist/icons/antigravity_64.png`와 base64 일치) + svg `re` | `#2563EB` |
| 2 | `claude` / `claude` `anthropic` | Claude | PNG `claude_64.png` + svg `ae` | `#D97757` |
| 3 | `codex` `openai` / `codex` `gpt` `openai` | Codex | PNG `codex_64.png` + svg `ie` | `#6366F1` |
| 4 | `google` / `google` `gemini` | Gemini | svg `se` | `#4E82EE` |
| 5 | 그 외 | AI | svg `le` | `#8B5CF6` |

원본 아이콘 `dist/icons/{antigravity,claude,codex}.png` + `_64.png`. `bgMono #374151`·`colorMono #D1D5DB` 필드는 미사용.

```text
SVG viewBox 0 0 24 24, 기본 width="16" height="16" (R:1-38)
ae Claude fill=currentColor: M12 2l1.2 5.5L18 4l-3 4.8 5.8.5-5 3 4.2 4-5.4.3 2 5.4-4.8-3-1 5.8-1.5-5.5-4.5 3.5 1.5-5.5-5.5-1 5-3.2-4-4.5 5.5 1L10.5 2z
ie Codex: fill=#6366F1 d=M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z
          + stroke=#FFFFFF stroke-width=1.6 round cap/join fill=none d=M7.5 11.5l2.5 2.5-2.5 2.5M12.5 16.5h3
se Gemini: linearGradient#geminiGrad (0,0)->(100%,100%) #4E82EE / #9B72CB@50% / #D96570
          d=M12 1C12 7.075 7.075 12 1 12C7.075 12 12 16.925 12 23C12 16.925 16.925 12 23 12C16.925 12 12 7.075 12 1Z
re Antigravity: linearGradient#agyArchGrad x1=0% y1=100% x2=100% y2=100% #1E70F5 / #43B957@25% / #EB572A@50% / #7E57C2@75% / #2176FF
          d=M12 2C7.5 2 3.5 12 1 20c1.5 2 4.5 2 6-1 1.5-3 3-9 5-9s3.5 6 5 9c1.5 3 4.5 3 6 1-2.5-8-6.5-18-11-18z
le generic fill=currentColor: M19 9l1.25-2.75L23 5l-2.75-1.25L19 1l-1.25 2.75L15 5l2.75 1.25L19 9zm-7.5.5L9 4 6.5 9.5 1 12l5.5 2.5L9 20l2.5-5.5L17 12l-5.5-2.5zM19 15l-1.25 2.75L15 19l2.75 1.25L19 23l1.25-2.75L23 19l-2.75-1.25L19 15z
```

**아이콘 `U(provider,name,iconStyle="color",size=18)`** (R:38): `div.ai-brand-icon.is-color|is-mono`, `title=V.name`, 인라인 `width/height/min-width:{size}px; inline-flex; center; flex-shrink:0; background:transparent; color:{mono?#9CA3AF:V.brandColor}`, mono면 `filter:grayscale(100%) brightness(1.25) contrast(1.1); opacity:.88`. 안쪽 `span`(flex center 100%)에 PNG면 `<img width height style="object-fit:contain;display:block">`, 아니면 SVG `width="16" height="16"`을 size로 치환. CSS 규칙 없음. 크기: 1a·1b 18, 1d 15, 팝업 카드 24, 계정 행 20, 감지 목록 18.

**공통 값**: 5H = `showUsedPercent ? primary.percentUsed : primary.percentLeft`, WK = `showUsedPercent ? (weekly?.percentUsed ?? 0) : (weekly?.percentLeft ?? 100)`, 리셋 `resetCountdown || "--"`, `{unit}`=`unitUsed`/`unitLeft`, 값은 반올림 없이 `${v}%`. 툴팁: 1c·1d는 항상 `widgetTooltip`, 1a·1b는 WK 행 없으면 `widgetTooltipNoWeekly`. `{name}`=`usage.name`, `replaceAll`, 이스케이프 없음(V1-06). 색: 1b/1c/1d는 mono면 5H `#D1D5DB`·WK `#9CA3AF`, 아니면 `c5=C(primary.percentUsed,colorByUsage,usage.brandColor)`, `cW=C(weekly.percentUsed,colorByUsage,"#9CA3AF")`. 1a는 mono여도 `C()`.

### 2-3. 전역·루트 CSS

```css
:root{--bg-alpha:.85;--taskbar-bg:rgba(22,22,26,var(--bg-alpha));--taskbar-border:rgba(255,255,255,.1);
 --text-main:#f3f4f6;--text-muted:#9ca3af;--text-dim:#6b7280;--bar-bg:rgba(255,255,255,.12)}
*{box-sizing:border-box;margin:0;padding:0;user-select:none}
html,body{height:100vh;min-height:100vh;width:100vw;overflow:hidden}
body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Noto Sans KR,sans-serif;color:var(--text-main);background:transparent;font-size:11px;line-height:1.2}
head,title,meta,link,script{display:none!important}  /* index.html 인라인. lang="ko", 빈 title, CSP 없음 */
#app{height:100vh;width:100%;display:flex;align-items:center;justify-content:flex-start;overflow:hidden}
body.is-widget-view{background:#00000001;display:block}  body.is-widget-view #app{height:100%;width:100%;cursor:pointer}
.widget-root{display:inline-flex;align-items:center;gap:8px;padding:3px 8px;height:34px;border-radius:6px;background:var(--taskbar-bg);
 backdrop-filter:blur(16px);border:1px solid var(--taskbar-border);box-shadow:0 2px 8px rgba(0,0,0,.35);cursor:pointer;
 transition:transform .15s ease,background .2s ease,border-color .2s ease}
.widget-root:hover{background:rgba(36,36,44,.95);border-color:rgba(255,255,255,.25)}  .widget-root:active{transform:scale(.98)}
.widget-root.no-card-bg{background:#00000001!important;backdrop-filter:none!important;border:none!important;box-shadow:none!important;padding:1px 4px}
.widget-root.no-card-bg:hover{background:rgba(255,255,255,.08)!important;border-radius:6px}
.widget-root.no-card-bg .account-item+.account-item{border-left:1px solid rgba(255,255,255,.12);padding-left:10px}
.widget-root.is-empty{padding:4px 8px;min-width:24px;justify-content:center}
.white-circle-dot{width:10px;height:10px;border-radius:50%;background-color:#fff;box-shadow:0 0 6px rgba(255,255,255,.8),0 0 12px rgba(255,255,255,.3);
 display:inline-block;transition:transform .2s ease,box-shadow .2s ease;animation:pulseDot 2.4s infinite ease-in-out}
.widget-root:hover .white-circle-dot{transform:scale(1.25);box-shadow:0 0 10px #fff,0 0 16px rgba(255,255,255,.6)}
@keyframes pulseDot{0%,100%{opacity:.85;transform:scale(1)}50%{opacity:1;transform:scale(1.15)}}
.account-item{display:flex;align-items:center;gap:8px;position:relative}
.account-item+.account-item{padding-left:10px;border-left:1px solid rgba(255,255,255,.1)}
```
- 내용 높이 card 켬 26px(가로 패딩+테두리 18) / 끔 32px(8). hover 배경은 alpha 무시. 빈 점 hover `scale(1.25)`는 애니메이션에 가려 glow만 변함(미실측).
- `#app` `flex-start` → 위젯은 창 왼쪽, 오른쪽 24px 투명 여백(클릭은 됨).
- 죽은 CSS(재현 불필요): `.ai-icon`(+`.monochrome`), `.theme-1b .status-dot`, `.theme-1b .segment-meter`, `.theme-1b .segment(.active)`. `.ring-center-icon.monochrome`·`.has-card-bg`는 규칙 없음.

### 2-4. 테마별 명세

| 항목 | 1a 바 게이지 | 1b 세그먼트 | 1c 이중 링 | 1d 초압축 |
|---|---|---|---|---|
| 함수 | `he` R:378 | `Ae`+`z` R:401 | `we` R:420 | `ye` R:454 |
| 아이콘 | `U(18)` 항목 왼쪽 | `U(18)` 왼쪽 | 링 중앙 인라인 SVG(PNG 안 씀) | `U(15)` 윗줄 첫 요소 |
| 라벨 | `5H` `WK` | 없음 | `5H` `WK` 태그 | 없음 |
| 게이지 | 바 38×4 ×2 | 10칸 SVG 47×6 ×2 | 동심원 2개 32px | 5H만 2px 바 |
| showWeeklyLimit | 적용 | 적용 | 무시 | 무시 |
| mono | 아이콘만 | 아이콘+게이지·% | 링·%·중앙 color | 아이콘+값·바 |
| 폭 / 높이 | 항목 최소 151 / 2행 25·1행 12 | 최소 143 / 25·12 | 32+8+data-col(추정 60-70) / 32 | max(80,내용) / 약 31 |

**1a** (`he`):
```html
<div class="account-item" data-account-id="{id}" title="{tooltip}">{U(…,18)}
 <div class="theme-1a">
  <div class="row"><span class="label">5H</span><div class="progress-track"><div class="progress-fill" style="width: {p}%; background-color: {c5};"></div></div>
   <span class="percent" style="color: {c5}">{p}%</span><span class="reset-time">{primaryReset}</span></div>
  <!-- WK 행: showWeeklyLimit!==false && weeklyQuota 일 때만, 같은 구조 (w, cW, weeklyReset) -->
 </div></div>
```
```css
.theme-1a{display:flex;flex-direction:column;justify-content:center;gap:1px;min-width:96px}
.theme-1a .row{display:flex;align-items:center;gap:4px;line-height:11px}
.theme-1a .label{font-size:8.5px;line-height:12px;font-weight:600;color:var(--text-dim);width:14px;font-family:MONO}
.theme-1a .progress-track{width:38px;height:4px;background:var(--bar-bg);border-radius:2px;overflow:hidden;position:relative}
.theme-1a .progress-fill{height:100%;border-radius:2px;transition:width .4s cubic-bezier(.16,1,.3,1)}
.theme-1a .percent{font-family:MONO;font-size:9.5px;line-height:12px;font-weight:600;width:25px;text-align:right}
.theme-1a .reset-time{font-size:8.5px;line-height:12px;color:var(--text-muted);min-width:36px;width:auto;text-align:right;white-space:nowrap;flex-shrink:0}
```
바 너비는 **표시값** 기준, clamp 없음(overflow로 잘림). 행 폭 14+4+38+4+25+4+max(36,리셋) ≥ 125.

**1b** (`Ae`): `.account-item > U(18) + .theme-1b > .data-stack > .row×(1|2)`, 행 = `<span class="percent-mono" style="color: {c};">{v}%</span>{z(v,c,10)}<span class="reset-mono">{reset}</span>`. `z(pct,color,n=10)`: `filled=Math.round(pct/100*n)`, `<svg class="segment-meter-svg" viewBox="0 0 47 6" width="47" height="6">`에 i=0..9 `<rect class="segment-rect" x="{(i*4.8).toFixed(1)}" y="0.4" width="3.2" height="5.2" rx="0.8" fill="{i<filled ? color : 'rgba(255, 255, 255, 0.14)'}"/>`(표시값 기준).
```css
.theme-1b{display:flex;align-items:center;gap:5px;white-space:nowrap;flex-shrink:0}
.theme-1b .data-stack{display:flex;flex-direction:column;justify-content:center;gap:1px}
.theme-1b .row{display:flex;align-items:center;gap:4px;line-height:12px}
.theme-1b .percent-mono{font-family:MONO;font-size:10px;line-height:12px;font-weight:700;width:26px;text-align:right;flex-shrink:0}
.theme-1b .segment-meter-svg{display:block;flex-shrink:0;shape-rendering:geometricPrecision}
.theme-1b .segment-rect{transition:fill .2s ease}
.theme-1b .reset-mono{font-family:MONO;font-size:8.5px;line-height:12px;color:var(--text-muted);min-width:36px;width:auto;text-align:right;white-space:nowrap;flex-shrink:0}
```

**1c** (`we`):
```html
<div class="account-item" data-account-id="{id}" title="{widgetTooltip}"><div class="theme-1c">
 <div class="ring-container"><svg class="ring-svg" viewBox="0 0 36 36">
  <circle cx="18" cy="18" r="15.5" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="2.5" />
  <circle cx="18" cy="18" r="11.5" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="2.5" />
  <circle cx="18" cy="18" r="15.5" fill="none" stroke="{c5}" stroke-width="2.5" stroke-dasharray="{Co}" stroke-dashoffset="{Co*(1-min(100,p)/100)}" stroke-linecap="round" />
  <circle cx="18" cy="18" r="11.5" fill="none" stroke="{cW}" stroke-width="2.5" stroke-dasharray="{Ci}" stroke-dashoffset="{Ci*(1-min(100,w)/100)}" stroke-linecap="round" />
 </svg>
 <div class="ring-center-icon {monochrome?}" style="background: transparent; color: {mono?#9CA3AF:V().brandColor}; box-shadow: none;">
  <span style="display: flex; align-items: center; justify-content: center; transform: scale(0.9);">{V().svg 16×16}</span></div></div>
 <div class="data-col">
  <div class="row"><span class="percent" style="color: {c5};">{p}%</span><span class="tag">5H</span><span class="reset">{primaryReset}</span></div>
  <div class="row"><span class="percent" style="color: {cW};">{w}%</span><span class="tag">WK</span><span class="reset">{weeklyReset}</span></div>
 </div></div></div>
```
`Co=2π·15.5≈97.389`, `Ci=2π·11.5≈72.257`. `rotate(-90deg)` → 12시 시작 시계 방향. 0%여도 round cap 점이 보일 수 있음. 중앙 color는 `currentColor` SVG(`ae`,`le`)만 따르고 Codex·Antigravity·Gemini는 mono에서도 원색. weekly 없으면 남은 % 모드에서 내부 링 가득.
```css
.theme-1c{display:flex;align-items:center;gap:8px}
.theme-1c .ring-container{position:relative;width:32px;height:32px;display:flex;align-items:center;justify-content:center}
.theme-1c .ring-svg{transform:rotate(-90deg);width:32px;height:32px}
.theme-1c .ring-center-icon{position:absolute;width:16px;height:16px;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:800;color:#fff}
.theme-1c .data-col{display:flex;flex-direction:column;gap:2px}
.theme-1c .row{display:flex;align-items:center;gap:4px}
.theme-1c .percent{font-family:MONO;font-size:10px;font-weight:700}
.theme-1c .tag{font-size:8px;color:var(--text-dim)}
.theme-1c .reset{font-size:9px;color:var(--text-muted);margin-left:2px}
```
`.percent` 고정 폭 없음 → 자릿수 변화 때 창 폭 재조정.

**1d** (`ye`):
```html
<div class="account-item" data-account-id="{id}" title="{widgetTooltip}"><div class="theme-1d">
 <div class="top-line">{U(…,15)}<strong class="quota-val" style="color: {c5};">{p}%</strong><span class="quota-time">{primaryReset}</span></div>
 <div class="sub-line"><span class="quota-val-sub" style="color: {cW};">{w}%</span><span class="quota-time-sub">{weeklyReset}</span></div>
 <div class="stack-bar-track"><div class="stack-bar-fill" style="width: {p}%; background-color: {c5};"></div></div>
</div></div>
```
```css
.theme-1d{display:flex;flex-direction:column;justify-content:center;min-width:80px}
.theme-1d .top-line{display:flex;align-items:center;gap:4px;line-height:1}
.theme-1d .quota-val{font-family:MONO;font-size:11px;font-weight:700;line-height:1}
.theme-1d .quota-time{font-size:9px;color:var(--text-muted);margin-left:auto;line-height:1}
.theme-1d .sub-line{display:flex;align-items:center;justify-content:space-between;font-size:9px;color:var(--text-muted);padding-left:19px;line-height:1;margin-top:2px}
.theme-1d .quota-val-sub{font-family:MONO;font-size:9px}
.theme-1d .quota-time-sub{font-size:9px;color:var(--text-dim)}
.theme-1d .stack-bar-track{width:100%;height:2px;background:var(--bar-bg);border-radius:1px;margin-top:3px;overflow:hidden;position:relative}
.theme-1d .stack-bar-fill{height:100%;border-radius:1px}
```

**창 폭(추정)** = `ceil(Σ항목 + (n−1)·19 + 가로 패딩·테두리) + 24` (1a·3계정·card 켬 약 533px).

### 2-5. 위젯 상호작용 (R:477)

클릭: `#app`의 `click`·`pointerup(button===0)` 공용 핸들러, `stopPropagation`, 300ms 내 재호출 무시 → `togglePopup()`. 우클릭 무시. 툴팁은 가장 안쪽 title(아이콘 `V.name` > 항목 `widgetTooltip*` > 루트 `widgetClickTitle`). 빈 상태도 팝업을 연다.

---

## 3. 팝업·계정 관리·설정 탭

### 3-1. 렌더링 모델 (R:55-84, 477)

- 모듈 상태 `x`(탭, 기본 `usage`), `Q`(커스텀 폼 열림), `G`(렌더 동결), `H`(감지 목록). 팝업 창은 숨김/표시만 반복하므로 **닫았다 열어도 유지**.
- `Le()`: `getState()` → `keydown` Escape면 `hidePopup()` → `E(#app,state)` → `onStateChange(E)`.
- `E()`: `G`면 무시. 아니면 `innerHTML` 전체 교체 + `me()`로 리스너 재바인딩 → 스크롤 초기화·`popupSlideUp` 재생·폼/포커스 소실·옛 state 클로저(V1-25). **[결정]** v2는 재현하지 않되 첫 표시 애니메이션 유지.
- **[제외]** `window.api` 부재 시 Mock API와 가짜 state(R:477).

### 3-2. 헤더·탭 (R:56-78)

```text
.popup-root
 ├ .popup-header
 │  ├ .popup-title > <span>{popupTitle}</span> + <span.popup-title-badge>{accountsActive count=usages.length}</span>
 │  └ .popup-actions > button.icon-button#btn-refresh[.refreshing if isRefreshing] title=refresh "&#8635;"
 │                    + button.icon-button#btn-close-popup title=close "&times;"
 ├ .popup-tabs > div.popup-tab[data-tab=usage|accounts|settings](.active)  라벨 tabUsage/tabAccounts/tabSettings
 └ .popup-body
```
배지 = enabled 계정 수(loading·error 포함). ↻ `refreshQuota()`, × `unlockPopup()`→`hidePopup()`. 탭 클릭은 `.popup-tabs` 위임 + `closest(".popup-tab")`, accounts·settings는 `lockPopup()` 추가. usage로 돌아가도 잠금 유지.

### 3-3. 사용량 탭 (`ge`, R:85-131)

- 빈 상태: `<div style="text-align:center;padding:40px 10px;color:var(--text-muted)"><p>{noActiveAccounts}</p><p style="margin-top:8px;font-size:11px">{addAccountHint}</p></div>`.
- usage 1개당 `.card`(계정 순서):

| 위치 | 요소 | 내용 |
|---|---|---|
| 헤더 좌 | `U(…,24)` + `.card-account-name` / `.card-account-email` | name / `email ‖ projectId ‖ (error ? errorMessage : realtimeMonitoring)` |
| 헤더 우 | `span.card-badge`(+`.error`) | `tier ‖ status` 원문 |
| 그리드 1 | `.card-quota-grid > .quota-box` | `.quota-box-title`(`sessionLimit5h` ↔ `usageLabel`), `.quota-box-percent` `${primary.percentUsed}%`, `.quota-box-reset` `resetLabel{time:"<strong>"+resetCountdown+"</strong>"}` |
| 그리드 2 | `.quota-box` | `weeklyLimit` ↔ `usageLabel`, `${weekly?.percentUsed ?? 0}%`, `weekly?.resetCountdown ‖ "--"`. **weekly 없어도 항상 그림** |
| 모델 | `.model-list-title`{modelQuotaTitle} + `.model-item`×N | `.model-name`{displayName} ↔ `.model-pct`(color) `{percentUsed}% ({resetCountdown})`. 비면 생략 |

- 색: 5H `C(…,brandColor)`, 주간 `C(…,"#9CA3AF")`, mono면 `#D1D5DB`/`#9CA3AF`. 모델 %는 mono 무시(V1-33).
- Antigravity 축약: 모델 2개 이상이면 `/gemini[\s\-_]*([0-9]+)(?:\.([0-9]+))?/i`로 `major*1000+minor` 최대 1개, 매칭 없으면 첫 모델.
- 상태별: `loading` → 초록 배지 `loading`, 부제 `realtimeMonitoring`, 0%/`--` ×2 / `ready` → tier·실측 / `error` → tier 또는 빨강 `error`, 부제 errorMessage, 0%/`--`.

### 3-4. 계정 관리 탭 (`ve`, R:132-225)

배치(`column; gap:8px`): ① 감지 카드 ② `checkedAccountsHint`(11px muted, `margin:4px 0 2px 0`) ③ 계정 행 × 전체 계정(비활성 포함) ④ 하단 버튼(또는 **[제외]** 커스텀 폼).

**감지 카드** (R:147-170): `.card` + `padding:10px 12px; background:rgba(37,99,235,.08); border-color:rgba(37,99,235,.3)`. 머리 `space-between; margin-bottom:6px`: `<strong style="font-size:11px;color:#60a5fa">{localDetectTitle}</strong>` + `button.btn-secondary#btn-detect-apps`(`padding:2px 8px;font-size:10px`){redetect}. 목록 `#local-apps-list`(column, gap 2), 행 `space-between; padding:6px 0; border-top:1px solid rgba(255,255,255,.06)`, 좌 아이콘 18 + 이름(`600 11px #fff`) + 부제(`9px muted`). 우: 이미 있음(`accounts.some(a=>a.id===app.id)`) → `<span style="color:#34d399;font-weight:600;font-size:10px;background:rgba(52,211,153,.12);padding:3px 8px;border-radius:4px">{added}</span>` / 없음 → `button.btn-primary.btn-add-detected[data-app-id]`(`padding:3px 10px;font-size:10px;background:#2563EB`){addToWidget} → `restoreDetectedApp(app)`.
- `H` 초기값 하드코딩 3개(antigravity·claude running:true, codex false) **[제외]**(V1-37). **[결정]** 권장: 탭 진입 시 자동 감지.
- 다시 감지: 목록을 `<div style="color:#60a5fa;padding:6px 0;font-size:11px">{detectingApps}</div>`로 교체 → `await detectLocalApps()` → 결과 ≥1이면 `H` 교체 → 옛 state로 `E()` → `refreshQuota()`.

**계정 행** (R:134-147): `.card` + `padding:10px 12px; flex-direction:row; align-items:center; justify-content:space-between`. 좌(`gap:8px`): `input[type=checkbox].chk-account[data-id]`(checked=enabled) → 아이콘 20 → 이름(`600 11px`)/부제(`9px dim`) = `tokens?.email ‖ (isLocalIde ? localIdeNoAuth : provider.toUpperCase())`. 우(`gap:5px`): `button.btn-order.btn-move-up` `▲` title `moveUp`, `.btn-move-down` `▼` title `moveDown`, `button.btn-danger.btn-delete-account` title `deleteAccountTitle` 텍스트 `deleteAccountBtn`. 첫 ▲·마지막 ▼는 `disabled` + 인라인 `opacity:0.25; cursor:default`. 체크 → toggle / ▲▼ → reorder / 삭제 → `confirm(confirmDeleteAccount)` 후 remove.

**하단 버튼** (R:203-216):
```html
<div style="display:flex; flex-direction:column; gap:6px; margin-top:10px;">
 <div style="display:flex; gap:8px;">
  <button class="btn-primary" id="btn-add-google" style="flex:1;"><span>{addGoogleOAuth}</span></button>
  <button class="btn-secondary" id="btn-show-custom-form">{addManually}</button></div>  <!-- [제외] -->
 <button class="btn-secondary" id="btn-reset-defaults" style="font-size:11px; padding:6px; background:rgba(255,255,255,.05); border-color:rgba(255,255,255,.15);">{resetDefaults}</button>
</div>
```
- Google: `r=await addGoogleAccount()`, `!r.success && r.error`면 `alert(loginFailedAlert{error})`(오류 원문 미번역). **[결정]** v2는 CLI 로그인 위임이라 대체 흐름 필요.
- 기본값 복원: `confirm(confirmResetDefaults)` → `resetDefaultAccounts()`. **[결정]** 권장: mock 없는 3개로 문구와 일치.

### 3-5. 위젯 설정 탭 (`fe`, R:226-377 / 핸들러 R:378)

컨테이너 `column; gap:14px`, `.form-group` `margin-bottom:12px`. 변경은 `updateConfig({...state.config, key:v})`(반환값 미사용, 브로드캐스트로 갱신).

| # | 라벨 키 | 컨트롤 | 바인딩·조건 | 이벤트 → 값 |
|---|---|---|---|---|
| 1 | `widgetTheme` | `.form-row > button.theme-button[data-theme]` ×4(`theme1a`~`theme1d`) | `.active`=현재 | click → `theme` |
| 2 | `iconStyleLabel` | `#btn-icon-color`(`iconColor`), `#btn-icon-mono`(`iconMono`) | active | `iconStyle` |
| 3 | `launchAtLogin` | 스위치 `#chk-open-at-login` | | change → `openAtLogin` |
| 4 | `colorByUsageLabel` | 스위치 `#chk-color-usage` | | `colorByUsage` |
| 5 | `showCardBg` | 스위치 `#chk-show-card-bg` | | `showCardBackground` |
| 6 | `showUsedPercentLabel` | 스위치 `#chk-show-used-percent` | | `showUsedPercent` |
| 7 | `placementLabel` | `#btn-place-docked`(`placementDocked`), `#btn-place-floating`(`placementFloating`) | docked active = `!=="floating"` | docked → `placementMode:"docked"` / floating → `placementMode:"floating", showCardBackground:true` |
| 8 | `alwaysOnTopLabel` + `alwaysOnTopDesc`(9px muted, 400) | `#group-always-on-top > #chk-always-on-top` | floating 아니면 그룹 `display:none`, checked `!==false` | `alwaysOnTop` |
| 9 | `alignmentLabel` | `#btn-align-right`, `#btn-align-left` | 라벨 floating `alignRightFloating`/`alignLeftFloating`, 아니면 `…Docked` | `alignment` |
| 10 | `offsetLabel` + `#label-offset` `{n}px` | `input[type=range].range-slider#slider-offset` 0-350 | | mousedown/touchstart → `G=true`+`lockPopup()` / input → 라벨 + 50ms 디바운스 `offsetPx`(실시간 이동) / change·mouseup·touchend → `G=false`+`offsetPx` |
| 11 | `alphaLabel` + `#label-alpha` `{n}%` | `#slider-alpha` 10-100 | | input → 라벨만 / **change에서만** `alphaPercent`(R:378 재확인) |
| 12 | `refreshIntervalLabel` | `select#sel-interval`(인라인 `background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);color:#fff;padding:6px;border-radius:4px`) | 15/30/60/120/300 = `interval15`…`interval300`, 목록 밖 값이면 selected 없음 | `refreshIntervalSec:parseInt` |

스위치(3-6, 8): `<label class="form-label switch-container" for="{id}"><span>{label}</span><div class="md-switch"><input type="checkbox" id="{id}"><div class="md-switch-track"><div class="md-switch-thumb"></div></div></div></label>`. 8번 라벨은 `<div><span/><div style="font-size:9px;color:var(--text-muted);font-weight:400">{desc}</div></div>`. UI 없는 키 `verticalOffsetPx`·`showWeeklyLimit`(V1-38). 키보드로 오프셋 조작 시 `G` 미설정 → 포커스 소실(V1-26).

### 3-6. 닫기·키보드·접근성

닫기: × / Esc(창 포커스 필요) / 위젯·트레이 재클릭 / blur(잠금 아닐 때 600ms, 실사용에선 거의 늘 잠금 V1-09). confirm·alert 중에도 안 닫힘. 탭은 `<div>`, `role`·`aria-*` 없음(V1-36).

### 3-7. 팝업 CSS (8자리 hex는 rgba로)

| 선택자 | 규칙 |
|---|---|
| `.popup-root` | `100vw×100vh; flex column; background:rgba(22,22,28,.95); backdrop-filter:blur(28px); border:1px solid rgba(255,255,255,.12); border-radius:12px; box-shadow:0 16px 36px rgba(0,0,0,.45); overflow:hidden; animation:popupSlideUp .25s cubic-bezier(.16,1,.3,1) forwards`(불투명도 0.95 고정) |
| `@keyframes popupSlideUp` | `0%{opacity:0;transform:translateY(16px) scale(.98)} to{opacity:1;transform:translateY(0) scale(1)}` |
| `.popup-header` | `flex; space-between; center; padding:12px 16px; border-bottom:1px solid rgba(255,255,255,.08)` |
| `.popup-title` / `-badge` | `flex; gap:8px; 13px; 700; letter-spacing:-.2px` / `9px; padding:2px 6px; background:rgba(66,133,244,.2); color:#60a5fa; border-radius:10px; 600` |
| `.popup-actions` / `.icon-button` | `flex; gap:6px` / `28×28; background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.1); color:var(--text-main); border-radius:6px; flex center; 12px; transition:all .15s`; `:hover{background:rgba(255,255,255,.15); border-color:rgba(255,255,255,.25)}`; `.refreshing{animation:spin 1s linear infinite}`(`spin`→`rotate(360deg)`) |
| `.popup-tabs` / `.popup-tab` | `flex; padding:0 16px; gap:16px; border-bottom:1px solid rgba(255,255,255,.08)` / `padding:10px 0; 12px; 600; color:var(--text-dim); border-bottom:2px solid transparent; cursor:pointer; transition:all .2s`; `:hover{color:var(--text-main)}`; `.active{color:#60a5fa; border-color:#60a5fa}` |
| `.popup-body` | `flex:1; padding:14px 16px; overflow-y:auto; flex column; gap:12px`; `::-webkit-scrollbar{width:4px}`; `::-webkit-scrollbar-thumb{background:rgba(255,255,255,.15); border-radius:2px}` |
| `.card` | `background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.08); border-radius:8px; padding:12px; flex column; gap:10px; transition:border-color .15s`; `:hover{border-color:rgba(255,255,255,.16)}` |
| `.card-header` / `.card-account-info` / `-name` / `-email` | `flex; space-between; center` / `flex; center; gap:8px` / `600 12px` / `10px; dim` |
| `.card-badge` | `9px; padding:2px 6px; border-radius:4px; background:rgba(16,185,129,.2); color:#34d399`; `.error{background:rgba(244,63,94,.2); color:#fb7185}` |
| `.card-quota-grid` / `.quota-box` | `grid; 1fr 1fr; gap:8px` / `background:rgba(0,0,0,.2); padding:8px; border-radius:6px; flex column; gap:4px` |
| `.quota-box-title` / `-percent` / `-reset` | `flex; space-between; 10px; muted` / `MONO; 14px; 700` / `9px; dim` |
| `.model-list-title` / `.model-item` | `10px; 600; dim; margin-top:4px` / `flex; space-between; center; padding:4px 0; border-top:1px dashed rgba(255,255,255,.05); 10px`; `.model-name{muted}`; `.model-pct{MONO; 600}` |
| `.form-group` / `.form-label` / `.form-row` | `flex column; gap:6px; margin-bottom:12px` / `11px; 600; muted; flex; space-between` / `flex; gap:8px` |
| `.theme-button` | `flex:1; padding:8px 6px; background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.1); color:var(--text-main); border-radius:6px; center; 11px; 600; transition:all .15s`; `:hover{background:rgba(255,255,255,.1)}`; `.active{background:rgba(96,165,250,.2); border-color:#60a5fa; color:#93c5fd}` |
| `.range-slider` | `width:100%; accent-color:#60a5fa` |
| `.btn-primary` | `background:#2563eb; color:#fff; border:none; padding:8px 14px; border-radius:6px; 11px; 600; flex center; gap:6px; transition:background .15s`; `:hover{background:#1d4ed8}`(인라인 bg가 있는 추가 버튼은 hover 불변) |
| `.btn-secondary` | `background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.12); color:var(--text-main); padding:8px 14px; border-radius:6px; 11px; 600`; `:hover{background:rgba(255,255,255,.14)}` |
| `.btn-danger` | `background:rgba(239,68,68,.15); border:1px solid rgba(239,68,68,.3); color:#f87171; padding:4px 8px; border-radius:4px; 10px`; `:hover{background:rgba(239,68,68,.25)}` |
| `.btn-order` | `background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.15); color:var(--text-main); padding:3px 6px; border-radius:4px; 9px; line-height:1; transition:all .15s`; `:hover:not(:disabled){background:rgba(255,255,255,.18); border-color:rgba(255,255,255,.3)}`; `:disabled{opacity:.25; cursor:default}` |
| `.switch-container` | `flex; space-between; center; cursor:pointer; padding:3px 0; transition:color .15s`; `:hover{color:#fff}` |
| `.md-switch` | `relative; 38×22; flex-shrink:0; pointer-events:none`; `input{opacity:0; 0×0; absolute}` |
| `.md-switch-track` | `absolute inset 0; background:rgba(255,255,255,.12); border:1.5px solid rgba(255,255,255,.28); border-radius:22px; transition:background-color .25s, border-color .25s cubic-bezier(.4,0,.2,1)` |
| `.md-switch-thumb` | `absolute; 14×14; left:2.5px; top:50%; translateY(-50%); background:#9ca3af; radius 50%; box-shadow:0 1px 3px rgba(0,0,0,.4); transition:transform .25s, width/height .2s, background .25s` |
| checked / hover / focus | track `#2563eb`, border `#3b82f6`, thumb `translateY(-50%) translate(16px); 15×15; #fff; box-shadow:0 2px 5px rgba(0,0,0,.45)` / track `border-color:rgba(255,255,255,.45); background:rgba(255,255,255,.18)`, checked+hover `#1d4ed8`·border `#60a5fa` / `input:focus-visible + .md-switch-track{box-shadow:0 0 0 2px rgba(96,165,250,.5)}` |

---

## 4. 창·위치·트레이·수명주기

### 4-1. 위젯 창 `bt()` (M:2202-2235)

- 옵션: `Ee()` 좌표, 520×36, `frame:false, transparent:true, alwaysOnTop:true, skipTaskbar:true, resizable:false, hasShadow:false, focusable:true, show:false, title:""`, `webPreferences{preload:Xe(), nodeIntegration:false, contextIsolation:true, backgroundThrottling:false}`. 앱 스위치 `disable-renderer-backgrounding`(M:2177).
- 생성 직후: `setAlwaysOnTop(true,"screen-saver",9999)`, `setVisibleOnAllWorkspaces(true,{visibleOnFullScreen:true})`, `did-fail-load`·`console-message` → main 콘솔, `once ready-to-show` → `showInactive()` → `ue()` → `Ze(config)`, `closed` → `y=null`.
- 로드: 개발 `${VITE_DEV_SERVER_URL}#view=widget`, 배포 `loadFile(dist/index.html,{hash:"view=widget",query:{view:"widget"}})`.
- `ue()`(M:2197-2201) → `Z.applyBounds(y,config,ee,ie)` → `Ee()`로 `setBounds`(반올림, M:2058-2067).
- **`Ze(config)`**(M:2194-2196): floating → `Z.stopStayTop()` 후 `alwaysOnTop!==false ? setAlwaysOnTop(true,"screen-saver",9999) : setAlwaysOnTop(false)`. docked → `alwaysOnTop` 무시, `setAlwaysOnTop(true,…)` + `Z.startStayTop(y)`. ready-to-show·모든 UPDATE_CONFIG에서 실행.
- **2초 moveTop**(M:2464-2466): 위젯이 보이면 모드 무관 `y.moveTop()`(V1-28).

### 4-2. 팝업 창 `Ke()` (M:2255-2280)

`ze(Ee().x, ee, 380, 440, 위젯Y)`, 380×440, `frame:false, transparent:true, alwaysOnTop:true`(+`setAlwaysOnTop(true,"screen-saver",9999)`), `skipTaskbar:true, resizable:false, show:false, title:""`, preload·isolation 동일(`backgroundThrottling`·`hasShadow`·`setVisibleOnAllWorkspaces` 없음). 로드 `#view=popup`. `blur` → `te` false면 `et(600)`. `closed` → `x=null`(다음 `Ae()`에서 재생성). 시작 시 숨김 생성.

### 4-3. 좌표 공식 (M:1838-1879 재확인)

**`Ye()`** (주 모니터 `bounds`·`workArea`만):

| 조건 | taskbarY | taskbarHeight | position |
|---|---|---|---|
| `wa.y===b.y && wa.height<b.height` | `wa.height` | `b.height-wa.height` | bottom |
| `wa.y>b.y` | `b.y` | `wa.y-b.y` | top |
| 그 외(좌/우·자동 숨김) | `b.height-48` | 48 | bottom |

**`Ee(config,w,h)`** (`a=max(0,offsetPx??20)`, `vo=verticalOffsetPx||0`, x는 `bounds` 기준):

| 모드 | right | left | x clamp | y |
|---|---|---|---|---|
| floating | `b.x+b.width-w-a` | `b.x+a` | `[b.x, b.x+b.width-w]` | `taskbarY-h-4+vo` |
| docked | `b.x+b.width-220-w-a` | `b.x+64+a` | `[b.x+12, b.x+b.width-w-12]` | `taskbarY+max(0,floor((taskbarHeight-h)/2))+vo` |

docked는 SetParent가 아니라 작업표시줄 좌표에 겹친 최상위 투명 창. 상단 작업표시줄+floating은 화면 위로 벗어남(V1-29).

**`ze(wx,ww,pw=380,ph=440,wy)`** (`workArea` 기준): x = `round(wx+ww/2-pw/2)` → `[wa.x+12, wa.x+wa.width-pw-12]`. bottom `y=(wy<taskbarY?wy:taskbarY)-ph-8`, 최소 `wa.y+8`. top `y=(wy>taskbarY?wy+36:taskbarY+taskbarHeight)+8`, 최대 `wa.y+wa.height-ph-12`(`36` 하드코딩).

**`xt()`**(M:2236-2254): 위젯 `getBounds()`(없으면 `Ee()`·`ee`) → `ze()` → `setBounds`. **안 보이던 팝업을 띄울 때만**(V1-27). 디스플레이 이벤트 3종은 `ue()`만(M:2469-2472).

### 4-4. 팝업 상태기계 (M:2281-2298)

| 함수 | 동작 |
|---|---|
| `Ae(focus=false,lock=false)` | 타이머 취소 → lock면 `te=true` → 창 없으면 `Ke()` → 보이면 focus일 때 `focus()`만 / 안 보이면 `xt()` 후 `focus ? show()+focus() : showInactive()` + `STATE_CHANGED(z())` |
| `et(ms=400)` | `te`면 무시, 아니면 타이머 재설정 → 만료 시 여전히 비잠금이면 `pe(true)` |
| `ae()` | 타이머 해제 |
| `pe(force=false)` | `!force && te`면 무시, 아니면 `te=false` → 타이머 해제 → 보이면 `hide()` |
| `tt()` | 타이머 해제 → 보이면 `pe(true)`, 아니면 `Ae(true,true)` |

진입점: 위젯 클릭·트레이 좌클릭 → `tt()` / 트레이 "상세 팝업 열기"·`OPEN_SETTINGS` → `Ae(true,true)` / `SHOW_POPUP` → `Ae(false,false)` / `HIDE_POPUP`·Esc → `pe(true)` / 탭·슬라이더 → lock / × → unlock+hide / 위젯 숨김(트레이·전체화면) → `pe(true)`. 사용자 경로는 모두 잠금으로 열려 blur 숨김이 동작하지 않음(V1-09).

### 4-5. TaskbarDock.exe (M:1949-2069, C#:1-317)

- `Z.getDockerPath()`(M:1950-1963): 캐시 → `app.getAppPath()/native` → `process.resourcesPath/native` → `dirname(exe)/native` → `<dist-electron>/../../native` → `<dist-electron>/../native`. 없으면 1번 캐시 후 호출부에서 경고·중단. 서명 미검증. `Z.getHwnd(win)`(M:1964-1971): `getNativeWindowHandle().readBigUInt64LE(0)`(실패 시 UInt32) → `"0x"+hex`.
- main.js 사용 명령은 2개(`dock` C#:179-220, `setpos` C#:221-238, `isfgfullscreen` C#:239-244, `gettaskbar` C#:270-286은 호출 0건):

| 명령 | 호출 | spawn | 동작 |
|---|---|---|---|
| `staytop <hwnd> 600` | `Z.startStayTop(y)`(M:1975-1998), docked `Ze()` | `detached:false, stdio:"ignore", windowsHide:true` | 무효 HWND면 `INVALID_CHILD_HWND` exit 4. `IsWindow` 동안 600ms마다 `SetWindowPos(HWND_TOPMOST, SWP_NOMOVE\|NOSIZE\|NOACTIVATE)`(C#:146-178, 기본 40·최소 10) |
| `fswatch 1000 <hwnd>` | `Z.startFullscreenWatcher(y,cb)`(M:2015-2039), 시작 시 1회 | `windowsHide:true`, stdout 파이프 | 1000ms(최소 200)마다 판정, 첫 회·변화 시에만 `"1"`/`"0"` 출력(C#:245-269). 상주 방식은 .NET 반복 spawn 비용 회피(M:2008-2014 주석) |

- stdout: 누적 → `/\r?\n/` 분할 → 마지막 조각 보관 → 정확히 `"1"`/`"0"`일 때만 `cb`. `error`는 경고만, 재시작 없음. 시작 전 기존 프로세스 정지, 위젯 `closed`에서도 staytop 정리.
- `IsForegroundFullscreen`(C#:105-138): 전경 창 없음 / 클래스 `Progman` `WorkerW` `Shell_TrayWnd` `Shell_SecondaryTrayWnd` / 위젯과 다른 모니터 → false. 창 사각형이 `rcMonitor`(작업 영역 아님) 전체를 덮으면 true. `Main`(C#:287-316): `OpenDesktop("default",0,false,0x01FF)` 후 스레드에서 `SetThreadDesktop`+동작, 예외 `ERROR:` exit 99.
- 콜백(M:2466-2468): `!y‖destroyed‖xe`면 무시. `isFs && visible` → `ye=true; y.hide(); pe(true)`. `!isFs && ye` → `ye=false; y.show(); ue()`(showInactive 아님, V1-30). 팝업 복원 없음.

### 4-6. 트레이 (M:2299-2401)

- 아이콘 `Lt()`: `<dist-electron>/../public/tray-icon.ico` → `.png` → `app.getAppPath()/public/…` → `process.resourcesPath/public/…` → 폴백 base64 16×16 PNG(M:2315). 실제 `public/tray-icon.ico`(499B, 16+32px), `tray-icon.png`(283B, 32×32). `dist/tray-icon.*`는 탐색 목록 밖.
- `Et()`: `new Tray(icon)` → `setToolTip(trayTooltip)`(고정) → `Le()` → `click` → `tt()`. double/right-click 핸들러 없음.

| # | 메뉴 키 (`Le()` M:2338-2395, `Ie()`마다 재구성) | 타입 | 동작 |
|---|---|---|---|
| 1 | `trayToggleWidget` | normal | 보이면 `xe=true; y.hide(); pe(true)`, 아니면 `xe=false; ye=false; y.show(); ue()` |
| 2 | `trayOpenPopup` | normal | `Ae(true,true)` |
| — | separator | | |
| 3 | `trayAutoLaunch` | checkbox | checked: 배포 `getLoginItemSettings().openAtLogin ?? config.openAtLogin ?? true`, 개발 `config.openAtLogin ?? false`(M:2340). 클릭 → `saveConfig({...config,openAtLogin})` → `Ie()` → `Q()` |
| 4 | `trayRefreshNow` | normal | `refreshAll().then(Q)` |
| 5 | `trayAddGoogle` | normal | `re.startLogin()` → 성공+email이면 IPC #4와 같은 addAccount → await refresh → Q. 실패 피드백 없음 |
| — | separator | | |
| 6 | `trayQuit` | normal | `app.quit()` |

### 4-7. 자동 시작·단일 인스턴스 (M:2168-2177, 2320-2337)

- `Ie(enabled)`: 개발 → `setLoginItemSettings({openAtLogin:false,path:execPath})` / 배포 → `{openAtLogin:enabled, path:process.execPath, args:["--hidden"]}` → `Le()`, 예외 warn. `--hidden`을 읽는 코드 0건(grep, V1-14). 호출: 시작 `Ie(openAtLogin ?? true)`, 트레이 체크, UPDATE_CONFIG 변경 시.
- 로케일 `Ct(Tt(app.getLocale()))`(M:2169), `requestSingleInstanceLock()` 실패 → `app.quit(); process.exit(0)`(M:2175-2176), `second-instance` 핸들러 0건(V1-32).

### 4-8. 시작·종료 (M:2461-2484 재확인)

- `whenReady`: `new yt()` → `new kt(_)` → `q.addListener(Q)` → `It()` → `bt()` → `Ke()` → `Et()` → `Ie(openAtLogin ?? true)` → `startPolling(refreshIntervalSec)` → `setInterval(moveTop,2000)` → `startFullscreenWatcher(y,cb)` → `screen.on(3종, ue)`.
- `window-all-closed` 빈 핸들러(트레이 상주). `before-quit`: `ae()` → `stopPolling()` → `stopStayTop()` → `stopFullscreenWatcher()` → `J.close()`(대기 요청 reject, `kill("SIGTERM")`, M:1260-1278) → `K.destroy()`. moveTop 인터벌 미해제.

---

## 5. i18n 사전 (ko/en)

- 로케일: 렌더러 `ce(navigator.language)`(R:55, 적용 R:471), main `Tt(app.getLocale())`(M:2070, 적용 M:2169). 소문자 `ko` 시작이면 ko, 기본 `ko`, 런타임 전환 없음.
- 번역: 렌더러 `o(key,params)` = `de[key][lang]` + `{k}`→`String(v)` `replaceAll`. main `oe(key)`는 치환 없음. 없는 키는 대체값 없이 TypeError.
- 대조(스크립트): 렌더러 `de` 86키 = main `Pt` 86키(M:2073-2160), 한쪽 전용 0건, ko·en 불일치 0건. main은 `tray*`(1-7, M:2342-2398), 렌더러는 나머지 79개(팝업 R:60-378, 위젯 R:378-474). **[제외]** 커스텀 폼 전용: 36-43, 45.

| # | key | ko | en |
|---|---|---|---|
| 1 | `trayToggleWidget` | 위젯 표시/숨김 | Show/Hide Widget |
| 2 | `trayOpenPopup` | 상세 팝업 열기 | Open Details |
| 3 | `trayAutoLaunch` | 윈도우 시작 시 자동 실행 | Launch at Login |
| 4 | `trayRefreshNow` | 지금 새로고침 | Refresh Now |
| 5 | `trayAddGoogle` | Google 계정 추가... | Add Google Account... |
| 6 | `trayQuit` | 종료 | Quit |
| 7 | `trayTooltip` | AI 토큰 사용량 위젯 | AI Token Usage Widget |
| 8 | `popupTitle` | AI 토큰 사용량 | AI Token Usage |
| 9 | `accountsActive` | {count} 계정 활성 | {count} accounts active |
| 10 | `refresh` | 새로고침 | Refresh |
| 11 | `close` | 닫기 | Close |
| 12 | `tabUsage` | 사용량 현황 | Usage |
| 13 | `tabAccounts` | 계정 관리 | Accounts |
| 14 | `tabSettings` | 위젯 설정 | Settings |
| 15 | `noActiveAccounts` | 활성화된 계정이 없습니다. | No active accounts. |
| 16 | `addAccountHint` | [계정 관리] 탭에서 감지된 로컬 계정을 추가하세요. | Add a detected local account from the [Accounts] tab. |
| 17 | `realtimeMonitoring` | 실시간 모니터링 중 | Live monitoring |
| 18 | `modelQuotaTitle` | 모델별 세부 쿼터 | Per-model quota |
| 19 | `sessionLimit5h` | 5시간 세션 한도 | 5-Hour Session Limit |
| 20 | `usageLabel` | 사용량 | Usage |
| 21 | `resetLabel` | 리셋: {time} 남음 | Resets in {time} |
| 22 | `weeklyLimit` | 주간 누적 한도 | Weekly Limit |
| 23 | `localIdeNoAuth` | 로컬 IDE 무인증 연동 | Local IDE (no login required) |
| 24 | `moveUp` | 위로 이동 | Move Up |
| 25 | `moveDown` | 아래로 이동 | Move Down |
| 26 | `deleteAccountTitle` | 계정 삭제 | Delete Account |
| 27 | `deleteAccountBtn` | 삭제 | Delete |
| 28 | `runningNow` | 현재 프로세스 실행 중 | Currently running |
| 29 | `localInstallDetected` | 로컬 설치 감지됨 | Installed locally |
| 30 | `presetReady` | 프리셋 준비됨 | Preset ready |
| 31 | `added` | ✓ 추가됨 | ✓ Added |
| 32 | `addToWidget` | + 위젯에 추가 | + Add to widget |
| 33 | `localDetectTitle` | 로컬 AI 앱 자동 감지 (원클릭 추가) | Auto-detect local AI apps (one-click add) |
| 34 | `redetect` | 다시 감지 | Re-scan |
| 35 | `checkedAccountsHint` | 체크된 계정이 작업표시줄 위젯에 실시간 표시됩니다. | Checked accounts are shown live on the taskbar widget. |
| 36 | `addCustomAccountTitle` | 새 커스텀 계정 추가 | Add Custom Account |
| 37 | `accountAlias` | 계정 별칭 | Account Name |
| 38 | `iconLetterLabel` | 아이콘 글자 | Icon Letter |
| 39 | `brandColorLabel` | 브랜드 색상 | Brand Color |
| 40 | `usage5h` | 5H 사용량 (%) | 5H Usage (%) |
| 41 | `usageWeekly` | 주간 사용량 (%) | Weekly Usage (%) |
| 42 | `save` | 저장 | Save |
| 43 | `cancel` | 취소 | Cancel |
| 44 | `addGoogleOAuth` | + Google OAuth 로그인 | + Sign in with Google |
| 45 | `addManually` | + 직접 입력 | + Add Manually |
| 46 | `resetDefaults` | 🔄 기본 3대 AI (Antigravity · Claude · Codex) 전체 초기화/복원 | 🔄 Reset to Default 3 AIs (Antigravity · Claude · Codex) |
| 47 | `detectingApps` | 로컬 프로세스 및 CLI 설치 경로 실시간 탐색 중... | Scanning local processes and CLI install paths... |
| 48 | `confirmDeleteAccount` | 이 계정을 위젯에서 제거하시겠습니까? (로컬 앱 감지에서 언제든 다시 추가할 수 있습니다) | Remove this account from the widget? (You can re-add it anytime via local app detection.) |
| 49 | `confirmResetDefaults` | 기본 3대 AI (Antigravity · Claude · Codex) 프리셋으로 복원하시겠습니까? | Restore the default 3 AI presets (Antigravity · Claude · Codex)? |
| 50 | `loginFailedAlert` | 로그인 실패: {error} | Login failed: {error} |
| 51 | `widgetTheme` | 위젯 테마 디자인 | Widget Theme |
| 52 | `theme1a` | 1a. 바 게이지 | 1a. Bar Gauge |
| 53 | `theme1b` | 1b. 세그먼트 | 1b. Segments |
| 54 | `theme1c` | 1c. 이중 링 | 1c. Dual Ring |
| 55 | `theme1d` | 1d. 초압축 | 1d. Ultra Compact |
| 56 | `iconStyleLabel` | AI 아이콘 스타일 | AI Icon Style |
| 57 | `iconColor` | 오리지널 컬러 | Original Color |
| 58 | `iconMono` | 채도 없음 (모노크롬) | Monochrome |
| 59 | `launchAtLogin` | 윈도우 시작 시 자동 실행 | Launch at Login |
| 60 | `colorByUsageLabel` | 사용량 임계값 색상 변화 (녹색 → 주황 → 빨강) | Color by Usage (Green → Orange → Red) |
| 61 | `showCardBg` | 위젯 배경 카드 표시 (해제 시 완전 투명 일체화) | Show Background Card (off = fully transparent) |
| 62 | `showUsedPercentLabel` | 작업표시줄 바 표시 방식 (소모량 %로 표시) | Taskbar Display Mode (show used %) |
| 63 | `placementLabel` | 위젯 배치 위치 | Widget Placement |
| 64 | `placementDocked` | 작업표시줄 오버레이 (권장) | Taskbar Overlay (Recommended) |
| 65 | `placementFloating` | 작업 표시줄 바로 위 | Above Taskbar |
| 66 | `alwaysOnTopLabel` | 항상 위에 표시 | Always on Top |
| 67 | `alwaysOnTopDesc` | 다른 전체 화면 및 일반 창보다 항상 위에 떠 있도록 고정합니다 | Keeps the widget pinned above other windows and fullscreen apps |
| 68 | `alignmentLabel` | 위젯 위치 정렬 | Widget Alignment |
| 69 | `alignRightFloating` | 우측 정렬 (화면 끝) | Right (screen edge) |
| 70 | `alignRightDocked` | 우측 정렬 (트레이 좌측) | Right (left of tray) |
| 71 | `alignLeftFloating` | 좌측 정렬 (화면 끝) | Left (screen edge) |
| 72 | `alignLeftDocked` | 좌측 정렬 (시작버튼 우측) | Left (right of Start button) |
| 73 | `offsetLabel` | 위치 오프셋 간격 | Offset Distance |
| 74 | `alphaLabel` | 작업표시줄 배경 투명도 | Taskbar Background Opacity |
| 75 | `refreshIntervalLabel` | 데이터 갱신 주기 | Refresh Interval |
| 76 | `interval15` | 15초 | 15s |
| 77 | `interval30` | 30초 | 30s |
| 78 | `interval60` | 1분 (기본) | 1 min (default) |
| 79 | `interval120` | 2분 | 2 min |
| 80 | `interval300` | 5분 | 5 min |
| 81 | `unitUsed` | 소모 | used |
| 82 | `unitLeft` | 남음 | left |
| 83 | `widgetTooltip` | {name} \| 5시간: {p}% {unit} ({pr}) \| 주간: {w}% {unit} ({wr}) | {name} \| 5H: {p}% {unit} ({pr}) \| Weekly: {w}% {unit} ({wr}) |
| 84 | `widgetTooltipNoWeekly` | {name} \| {p}% {unit} ({pr}) | {name} \| {p}% {unit} ({pr}) |
| 85 | `noAccountTitle` | 연결된 AI 계정 없음 (클릭하여 계정 추가 또는 로컬 앱 감지) | No AI account connected (click to add or auto-detect) |
| 86 | `widgetClickTitle` | 클릭하여 상세 정보 및 설정 열기 | Click for details and settings |

**주의점**: `launchAtLogin`=`trayAutoLaunch` 중복 / en `tabUsage`·`usageLabel` 둘 다 "Usage" / "1 accounts active" 복수형 / "작업표시줄" vs "작업 표시줄" / "리셋: -- 남음"·"리셋: 0m 남음". 사전 밖 한국어 하드코딩(V1-34): tier 접미사 `(로컬 감지)` `(클라우드 세션)` `(실시간 세션)` `(공식 app-server)` `(Orca 직결)` `(로컬 세션)`, 모델명 `Gemini (대표 모델)` `Codex 세션 한도 (5시간)` `Codex 주간 한도 (7일)` `Codex (5시간)` `Codex (1주일)`, §1-4 errorMessage, 배지 `loading`/`ready`/`error`, `Login canceled or failed`, 감지 `description`(M:1890,1916,1941, 미표시). 문구·동작 모순(V1-35): `alphaLabel`은 실제 카드 배경 **불투명도**, `noAccountTitle` 클릭은 감지·계정 추가를 하지 않음, `resetDefaults` "3대"는 실제 4개.

---

## 6. v1 문제 목록 (v2에서 전부 해결)

V1-01~22: 검증 분석 확정 목록(`== RISKS`, `== REFUTED` 제외). V1-23~43 `[추출]`: 명세 추출 중 코드로 확인. 형식 `- [ ] V1-NN [심각도] 제목 — 근거 — v2 해결 방향`.

- [ ] V1-01 [medium] 조회 실패 시 customMock 고정 수치를 `ready`로 표시(Claude·Codex는 tier도 없음, Antigravity만 `Pro (목업 모드)`), 커스텀 계정은 전부 가짜 — M:58-116,189-228,753-776,1084-1106,1668-1690,1739-1761,1809-1813; R:378 — mock 제거, error/unknown + 마지막 실측값·시각(DECISIONS 01:36)
- [ ] V1-02 [medium] 앱 폴더 Authenticated Users 수정 가능 + 로그인 자동 실행 + 미서명 + asar 무결성 퓨즈 꺼짐(OnlyLoadAppFromAsar=0, AsarIntegrity=0, RunAsNode=1) — M:57,1950-1963,1986,2025,2320-2337,2464; exe 퓨즈 — `%LOCALAPPDATA%\Programs\AI Usage Widget` 설치, asar·무결성 퓨즈 ON, RunAsNode·NodeOptions·Inspect OFF(서명은 범위 외)
- [ ] V1-03 [medium] 제3자 자격증명 재사용·공식 클라이언트 사칭(UA `claude-code/0.2.29`, UA `antigravity`·ideType `ANTIGRAVITY`, state.vscdb 토큰 스캔) — M:438,469-481,491-499,830-842,869-878,1010-1017,1051-1062 — 자체 UA `ai-usage-widget/<버전>`, 공식 CLI 로그인 위임, 사칭 없는 경로가 없으면 비활성+보고
- [ ] V1-04 [medium] Gemini CLI 토큰이 공유 계정 객체·상수 `Oe[3]`에 주입 → 평문 저장·렌더러 전송·ANTIGRAVITY 전송, 만료 후 빈 client_id refresh 반복, 새 토큰 재독 안 함 — M:102-115,152,179-181,231,238,246,300-313,442-466,1803-1805,2184,2192 — 기본값·저장소 불변(깊은 복사), 외부 도구 토큰 비보관, 타 도구 자격증명 파일 직접 사용 금지
- [ ] V1-05 [low] OAuth 토큰 평문 저장(safeStorage 없음), `z()`로 tokens를 두 렌더러에 전송 — M:174,179-181,2181-2192,2376-2382,2414-2420; R:139 — `safeStorage`, 렌더러 DTO는 id·name·provider·email·사용량만
- [ ] V1-06 [low] `innerHTML`·`title` 무이스케이프 + CSP 없음 + IPC senderFrame·will-navigate·setWindowOpenHandler 없음 — R:55,94,104-108,138-139,379,477; dist/index.html; M:2403-2459,730-731 — textContent/컴포넌트, CSP `default-src 'self'`, 네비게이션 차단, senderFrame 검증
- [ ] V1-07 [low] `netstat | findstr <pid>` 부분 문자열 매칭으로 무관한 로컬 리스너에 CSRF 토큰 전송 — M:585-591,612-616,648-660 — 경로 유지 시 PID 열 정확 비교+응답 검증, 아니면 제거
- [ ] V1-08 [low] 지원 종료 가능성 높은 Electron 34.5.8/Chromium 132/Node 20.19.1과 기본값 퓨즈 — exe 내장 문자열; M:2232,2275 — 지원 메이저, `@electron/fuses`
- [ ] V1-09 [low] 위젯·트레이로 열면 항상 잠금 → blur 자동 숨김 무력화, 항상 위 팝업이 화면을 가림 — M:2275-2276,2281-2298,2398-2399,2445-2450; R:378,477 — 클릭으로 열 때 잠금 없음, 설정 조작 중에만 lock/unlock 짝
- [ ] V1-10 [low] Antigravity 미실행 시 폴링마다 PowerShell 생성, state.vscdb 경로가 실제 설치와 달라 클라우드 폴백 항상 null — M:576-581,649-650,810-818,898-899 — 미실행도 짧게 캐시, 확인된 공식 경로만 유지
- [ ] V1-11 [low] Claude 조회에 토큰 갱신·401/429 구분·백오프·실패 캐시 없음 — M:1008-1019,1046,1066-1075 — 상태 코드 보존·구분 표시, 지수 백오프
- [ ] V1-12 [low] 오프셋 슬라이더 input(50ms)·change·mouseup마다 config 쓰기 + staytop .NET 프로세스 kill/respawn(투명도는 change 1회만 — R:378 재확인으로 검증 분석 문구 정정) — M:1975-1994,2195,2405; R:378 — 같은 HWND면 재기동 안 함, 드래그 중 미리보기는 비저장, 확정 시 1회 저장
- [ ] V1-13 [low] Codex 3차 폴백이 `node:sqlite`(Node 22.5+) 의존, Node 20에서 import 실패 시 0% `ready` — M:1583,1587,1625,1635-1636 — 실패는 error, 추정 경로 제거(§7)
- [ ] V1-14 [low] 로그인 자동 실행 기본 ON(동의 없음), 등록한 `--hidden` 미사용 — M:57,2231,2320-2337,2464 — 기본 OFF 또는 첫 실행 동의, `--hidden` 처리
- [ ] V1-15 [low] 계정 전부 삭제 시 다음 기동에 기본 4계정(google-gemini 포함) 부활, 문구는 "3대" — M:146-152,102-115,2119,2122 — 빈 배열 존중, 프리셋·문구 일치
- [ ] V1-16 [low] 클라우드 fetch timeout 없음 → 한 요청이 멈추면 전체 갱신 정체(재진입 방지로 다음 폴링도 건너뜀) — M:286,306,469,491,874,903,925,1780,1786,1823 — `AbortSignal.timeout`, 계정별 결과 즉시 notify
- [ ] V1-17 [low] `weeklyQuota`가 실제로는 pro 모델 그룹 잔량인데 "주간"으로 표시, 로컬 요약 실패 시 0% `ready` — M:533,544-551,671-672,724-751,967-972 — 라벨=실제 의미, 실패=error
- [ ] V1-18 [low] 좌/우·자동 숨김 작업표시줄·보조 모니터 미지원(하단 48px·트레이 220 가정), 자동 숨김에서 최대화 창을 전체화면으로 오판 가능 — M:1838-1869,2467; C#:105-138 — `SHAppBarMessage(ABM_GETTASKBARPOS)`, 모니터별 배치, 창 스타일·최대화 반영
- [ ] V1-19 [low] codex.exe를 mtime 최신·서명 미확인으로 상주 실행, stdin `error` 리스너 없음, 재연결마다 리스너 누적 — M:1133-1170,1187-1201,1244 — 경로 우선순위 고정+Authenticode, `stdin.on("error")`, 1회 등록
- [ ] V1-20 [low] 렌더러 입력 무검증: UPDATE_CONFIG 통째 교체(NaN 주기), RESIZE_WIDGET 상한 없음, id 병합으로 provider 덮어쓰기 — M:171,187,1829,2405,2425-2441,2451-2452 — 스키마 검증+기본값 병합, 크기 상한, provider 변경 금지
- [ ] V1-21 [info] 앱 내 OAuth: `Math.random` state, PKCE 없음, 콜백 서버 `error` 리스너 없음·포트 TOCTOU, 콜백 HTML 무이스케이프 — M:263-275,365-377,381-419 — CLI 위임으로 앱 내 OAuth 서버 없음. 둔다면 `randomBytes` state+PKCE+`listen(0)`+`server.on("error")`
- [ ] V1-22 [info] 배포 번들에 개발용 Mock API(가짜 3계정) 잔존, 테마 조건 불일치(1c/1d weekly 조건 무시, 1a mono 분기 없음) — R:378,401,420,454,477 — mock은 테스트 코드에만, 테마 조건 통일
- [ ] V1-23 [low][추출] `isRefreshing` 항상 false → ↻ 회전이 안 보임 — M:2186; CSS `.icon-button.refreshing` — 실제 조회 상태 반영(위젯 막대 새로고침 포함)
- [ ] V1-24 [low][추출] 토큰 없는 google 계정·CloudCode/Antigravity 클라우드 예외를 warn 후 삼켜 영구 `loading`, 원인 미표시 — M:456-457,1793-1798,1803-1813 — error/unknown + 원인 문구
- [ ] V1-25 [low][추출] 팝업이 상태 변경마다 `innerHTML` 전체 재렌더 → 스크롤 초기화·`popupSlideUp` 재생·입력/포커스 소실·옛 state 클로저 — R:55-84,378,477 — 부분 갱신, 애니메이션은 표시 시에만
- [ ] V1-26 [low][추출] 오프셋 슬라이더 키보드 조작 시 `G` 미설정 → 매 input 재렌더로 포커스 소실 — R:378 — 입력 소스 무관하게 조작 중 재렌더 억제
- [ ] V1-27 [low][추출] 팝업이 열린 채 위젯이 이동해도 팝업 고정, 디스플레이 변경 시 팝업 재배치·fswatch 재시작 없음 — M:2236-2254,2281,2403-2405,2469-2472 — bounds·디스플레이 이벤트에서 팝업 재배치+워처 갱신
- [ ] V1-28 [low][추출] floating+`alwaysOnTop:false`여도 2초 `moveTop`으로 맨 위 복귀 — M:2195,2464-2466 — 항상 위 모드에서만
- [ ] V1-29 [low][추출] 상단 작업표시줄+floating이면 `y=bounds.y-h-4`로 화면 밖(코드 추론, 미실측) — M:1845-1849,1862-1863 — top이면 작업표시줄 아래 배치
- [ ] V1-30 [low][추출] 전체화면 해제 복원이 `y.show()`라 포커스 탈취 가능 — M:2467 — `showInactive()`
- [ ] V1-31 [low][추출] 트레이 자동 실행 체크를 등록 인자 없이 `getLoginItemSettings()`로 조회 → 실제 상태와 불일치 가능(Electron 문서 기준, 미검증) — M:2329-2333,2340 — 같은 path·args로 조회
- [ ] V1-32 [low][추출] `second-instance` 핸들러 없음 → 재실행 시 무반응 종료 — M:2175-2176 — 기존 인스턴스가 위젯 표시·팝업 열기
- [ ] V1-33 [low][추출] 모노크롬 범위 불일치: 팝업 모델 %는 무시, 1c 중앙 Codex·Antigravity·Gemini SVG 원색, 1a 게이지·% 색 유지 — R:90,378,420 — mono 규칙 단일 정의·전 요소 적용
- [ ] V1-34 [low][추출] i18n 이원화: 사전 2벌, 로케일 출처 2개, main 치환 미지원, tier·모델명·오류·배지 한국어 하드코딩, 복수형 없음 — R:55,471; M:2070-2169 — 단일 사전 모듈 + main이 정한 로케일 전달, 노출 문자열 전부 사전화
- [ ] V1-35 [low][추출] 문구·동작 모순: `alphaLabel`(실제 카드 불투명도), `noAccountTitle`(클릭해도 감지·계정 탭 이동 없음) — R:360,472,477 — 문구 정정 또는 빈 상태 클릭 시 계정 탭+감지
- [ ] V1-36 [low][추출] 접근성: 탭 `<div>` 키보드 불가, `role`·`aria-*` 없음, 아이콘 버튼 `title`만, 전역 `user-select:none` — R:56-78; CSS `*` — `role=tablist/tab`, 키보드 이동, `aria-label`, 포커스 표시
- [ ] V1-37 [low][추출] 감지 목록 초기값 `H`가 하드코딩된 가짜 running 상태 — R:55,147-170 — 초기 자동 감지 + 감지 중 표시
- [ ] V1-38 [info][추출] `verticalOffsetPx`·`showWeeklyLimit` UI 없음, `--vertical-offset`·`.ai-icon`·`.status-dot`·`.segment*` 죽은 코드 — M:48,51; R:471; CSS — 노출 여부 결정, 죽은 코드 미이식
- [ ] V1-39 [info][추출] refresh 경유 IPC 1회에 브로드캐스트 2회, `lastRefreshedAt`이 스냅샷 시각 — M:2187,2406,2440-2441,2462-2463 — 1회 브로드캐스트, 계정별 실측 시각
- [ ] V1-40 [low][추출] Codex 로컬 추정치(토큰 합 ÷ 임의 분모)를 실측과 구분 없이 `ready` 표시 — M:1552-1666 — 제거, 유지 시 "추정" 상태 명시
- [ ] V1-41 [info][추출] `showCardBackground` 기본값 불일치(main true / 렌더러 fallback false), floating 선택 시 카드 배경 말없이 강제 ON — M:53; R:378,471 — 기본값 단일 정의, 강제 변경은 UI에 표시
- [ ] V1-42 [info][추출] SVG gradient id 고정(`geminiGrad`, `agyArchGrad`) → 여러 개 삽입 시 id 충돌 — R:1-38 — 인스턴스별 고유 id
- [ ] V1-43 [info][추출] 사용자 경로에서 안 쓰는 IPC 4종(`show-popup` `open-settings` `schedule-hide-popup` `cancel-hide-popup`), `OPEN_SETTINGS`는 탭 전환도 안 함 — M:2441-2458; R:477 — 미이식, 필요 시 탭 인자

---

## 7. v2에서 의도적으로 버리는 v1 동작

| # | 버리는 것 | v1 위치 | 이유 / 대체 |
|---|---|---|---|
| 1 | `customMock` 전체: `Oe` 4개 mock, `restoreDetectedAccount` mock, `getFallback` mock 분기(Antigravity `Pro (목업 모드)` 포함), `createInitialUsage` mock 분기, `목업`·`로컬 대기` 판정 | M:58-116,189-229,753-776,1084-1106,1668-1690,1739-1761,1792,1809-1812 | 가짜 수치 금지(V1-01) → error/unknown + 마지막 실측값 |
| 2 | 커스텀 계정 폼, `ADD_CUSTOM_ACCOUNT`, i18n 9키(`addManually` 등) | R:171-216,378; M:2425-2440 | 가짜 수치 입력 전용. **[결정]** 실제 소스 연결 폼으로 대체할지 |
| 3 | 렌더러 Mock API, 하드코딩 감지 목록 `H` | R:55,477 | mock은 테스트에만(CLAUDE.md), 자동 감지 |
| 4 | 사칭 헤더 UA `claude-code/0.2.29`, UA `antigravity`, ideType `ANTIGRAVITY` | M:469-499,830-878,1051-1062 | 자체 UA(DECISIONS 01:36) |
| 5 | 타 도구 자격증명 직접 사용: `state.vscdb` 원시 스캔, `~/.gemini/oauth_creds.json` 주입, `~/.claude/.credentials.json` 토큰 직접 호출, 다른 프로세스 커맨드라인 CSRF 토큰 추출 | M:442-466,571-752,806-1004,1005-1075 | CLI 로그인 위임 + 계정별 격리 폴더, 사칭 없는 공식 경로 확인분만(조사 결과 대기) |
| 6 | 앱 내 Google OAuth(env `ANTIGRAVITY_OAUTH_CLIENT_ID/SECRET`, 루프백 콜백) | M:259-422,2367-2385,2406-2424 | 차용 client ID 금지. **[결정]** 로그인 버튼·트레이 항목 대체 흐름 |
| 7 | Orca 경로 하드코딩: `%APPDATA%\orca\orca-runtime.json` named pipe, `%APPDATA%\orca\codex-runtime-home\home\{auth.json,state_5.sqlite}`, 모델 라벨 `gpt-5.6-terra` | M:1370-1492,1553,1580,1928; 1466,1478,1583 | 개인 환경 전용. 공식 Codex 경로만 |
| 8 | Codex 로컬 sqlite 추정 | M:1532-1666 | 실측 아님(V1-13,V1-40) |
| 9 | `TaskbarDock.exe` 미사용 명령 `dock`(SetParent), `setpos`, `isfgfullscreen`, `gettaskbar` | C#:179-244,270-286 | 호출 0건. staytop·fswatch 기능은 v2 구현 방식 결정 |
| 10 | `Ve.fetchClaudeUsage`, `preload.js` 구버전, 미사용 IPC 4종 | M:1496-1529; preload.js; §1-5 #11,18,20,21 | 죽은 코드(V1-43) |
| 11 | 죽은 CSS·변수(`.ai-icon*`, `.status-dot`, `.segment-meter`, `.segment*`, `--vertical-offset`) | CSS; R:471 | 화면 영향 없음(V1-38) |

- 유지하되 결함은 고침: 테마 4종·수치·색 규칙(§2), 팝업 3탭(§3), docked/floating 좌표(§4-3, V1-18·29 보완), 전체화면 자동 숨김, 단일 인스턴스, 트레이 메뉴.
---

## 8. 추출 누락·불확실 항목

### 8-1. 코드 재확인으로 정정한 모순

| 주제 | 차이 | 확정 (근거) |
|---|---|---|
| 오류 문구 표시 | 추출본 하나는 `Account has no authentication tokens` 등이 refreshAll catch로 표시된다고 적음 | `wt`·`ge` 예외는 M:1796/1806에서 삼켜 `loading`. M:1815 catch는 `ne`·`Se`·`be` 자체 throw만(M:1786-1819) |
| Claude·Codex 실패 표시 | 검증 분석 "tier 없이 ready" vs 추출본 "error" | 둘 다 맞음: customMock 있으면 mock `ready`(tier 없음), 없으면 `error`(weekly 없음)(M:1084-1123,1668-1707). Antigravity mock만 `Pro (목업 모드)`(M:761) |
| mock tier | "(로컬 대기)" | 원결과에 errorMessage가 있을 때만 `목업 (로컬 대기)`(M:1812) |
| 슬라이더 저장 | 검증 분석은 offset·alpha 모두 input 50ms 저장 | alpha는 change에서만(R:378) → V1-12 정정 |
| 기본 계정 mock | 일부만 명시 | `Oe` 4개 모두(grep 4건) |
| i18n 일치 | 검증 분석 GAP "대조 안 함" | 스크립트 86=86, 전용 키 0건 |
| 미사용 명령 행 | 검증 분석 dock C#:179-220만 | grep: setpos 221, isfgfullscreen 239, fswatch 245, gettaskbar 270, Main 287 |
### 8-2. 여전히 불확실하거나 빠진 것

- **렌더 실측 없음**: 창 폭(1c·1d), 1d 높이, 빈 점 hover, 0% round cap은 CSS 계산·추론. v1 기준 캡처는 스크래치패드에만 있어 휘발성(리포 미이관).
- **공급자 조회 절차·응답 파싱**(엔드포인트, 필드 매핑, `formatPlanName`, Orca 응답, app-server·Orca 리셋 원문)은 §1-4 요약과 §7 목록만 있다. v2는 조사 결과(`docs/RESEARCH-auth-quota.md`, 미작성)로 재설계.
- **미검증 동작**: `node:sqlite` import 실패 여부, Antigravity 프로세스명이 `language_server`인지, 좌/우·자동 숨김 작업표시줄·혼합 DPI 좌표, V1-29·V1-31, `setVisibleOnAllWorkspaces({visibleOnFullScreen:true})`와 fswatch 숨김의 상호작용, codex app-server가 `~/.codex/auth.json`을 스스로 갱신하는지, 자동 실행 레지스트리 값(runtime 리더 관찰만).
- **옮기지 않은 바이너리**: 트레이 폴백 PNG(M:2315), `dist/icons/*.png`, `public/tray-icon.*` — v1 폴더 삭제 전에 복사 필요.
- CSS 속성 값은 추출본 인용이다(원문과 속성 단위 대조 안 함).

### 8-3. 자가 감사 (스크립트)

80KB 미만 · BOM 없음 · `V1-NN` 43개(01-43 연속) · §5 표 86행 · CSS 파일의 `.클래스` 토큰 80종과 keyframes 3종 모두 본문에 등장(누락 0) · 코드 펜스 짝 맞음.

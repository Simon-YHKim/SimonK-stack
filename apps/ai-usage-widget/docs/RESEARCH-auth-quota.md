> 생성물. 원본 wq7odxbgd.output(워크플로 wf_1d84ab23-cbf 결과) sha256 88be4ebd0424 · 생성 260915 02:24 KST
> 손으로 고치지 않는다. 사실이 바뀌면 조사를 다시 돌리거나 DECISIONS.md에 결정으로 남긴다.

# AI Usage Widget v2 인증·쿼터·플랫폼 결정용 사실 시트

작성 2026-09-15 02:03 KST · 발행 Claude Code(서브에이전트 종합)
입력: 6개 토픽(grok, claude, codex, gemini, orca, platform)의 연구 결과와 각 토픽의 독립 검증 결과
이번 종합 단계에서는 원격 호출, 로그인, 설정 변경을 하지 않았다. 새 로컬 명령은 시각 확인용 `node` 1회뿐이다.

---

## 0. 출처 약어

| 약어 | 실제 위치 |
|---|---|
| `claude.exe@N` | C:\Users\202502\.local\bin\claude.exe 바이트 오프셋 |
| `orca.asar@N` | C:\Users\202502\AppData\Local\Programs\orca\resources\app.asar 바이트 오프셋. gemini 토픽의 오프셋은 추출본 C:\Users\202502\AppData\Local\Temp\claude\widget-v2-research\orca-main.js 기준이다 |
| `orca.cli/…` | …\orca\resources\app.asar.unpacked\out\cli\ |
| `grok.exe@N` / `grok-docs/…` | C:\Users\202502\.grok\bin\grok.exe / C:\Users\202502\.grok\docs\user-guide\ |
| `codex-schema/…` | C:\Users\202502\AppData\Local\Temp\claude\widget-v2-research\codex-schema (`codex app-server generate-json-schema`, 0.154.0 산출) |
| `codex-docs/…` | 같은 폴더 codex-docs\ (learn.chatgpt.com 사본, openai/codex **main 브랜치** 소스 사본) |
| `gemini-bundle/…` | C:\Users\202502\AppData\Roaming\npm\node_modules\@google\gemini-cli\bundle\ |
| `e44/…` | Electron 44-x-y docs·소스 사본(scratch electron-docs, raw와 대조해 일치) |
| `orca list` | `orca account list --json` 마스킹 출력 |

---

## 1. 결론 요약

1. **구독 쿼터를 공식적으로, 문서화된 방식으로, 비대화형으로 읽을 수 있는 공급자는 Codex 하나뿐이다.** 경로는 `codex app-server`의 `account/rateLimits/read`이다(codex-schema/v2/GetAccountRateLimitsResponse.json). 다만 문서는 app-server 명령 자체를 experimental로, production 워크로드는 미지원으로 적고 있다(codex-docs/learn_app-server.txt).
2. **계정 격리는 다섯 공급자 중 네 곳에서 공식 또는 준공식 수단이 있다.**
   - Claude: `CLAUDE_CONFIG_DIR`. 문서가 여러 계정 용도로 명시한다(env-vars.md:393). 로컬에서 격리를 재현했다.
   - Codex: `CODEX_HOME`. 소스 기준 file·keyring 모두 경로별로 분리된다(storage.rs L235-248). 공식 멀티계정 기능은 아니다(#4432 open).
   - Grok: `GROK_HOME`(grok-docs/05-configuration.md:809).
   - Gemini CLI: `GEMINI_CLI_HOME`(https://geminicli.com/docs/reference/configuration/).
   - Antigravity(agy): 문서화된 수단이 없다. 자격증명이 wincred 단일 대상 `gemini:antigravity`에 있다(cmdkey /list).
3. **Claude·Grok·Gemini·Antigravity의 쿼터는 비공개 내부 엔드포인트나 TUI에만 있다.** Anthropic(legal-and-compliance), Google(Gemini CLI·Antigravity 약관)은 제3자가 구독 자격증명으로 서비스에 직접 접근하는 것을 명시적으로 금지한다. xAI 약관은 이번에 읽지 않았다(§8).
4. **Orca(B)는 주 소스로 부적합하다.** 이유는 네 가지다.
   - `orca account list`는 항상 `refreshUsage:false`로 캐시만 준다(orca.cli/handlers/account.js:222-224). 재측정에서도 claude 값은 24분, codex 값은 57분 묵어 있었다.
   - 백그라운드 폴링은 Orca 창이 보이고 포커스를 가진 동안에만 15분 주기로 돈다(orca.asar@10709573).
   - 멀티계정은 Claude·Codex만 지원한다.
   - 업스트림은 UA·ideType·client secret을 사칭하는 비공식 호출이다.
5. **권장은 C다.** A(위젯 전용 격리 폴더 + 공식 CLI 위임)를 주 경로로 두고, B는 읽기 전용 보조 어댑터로 한정한다. 공급자별로 "측정 불가" 표시를 정상 상태로 허용한다.
6. **플랫폼**: Electron 44.3.0으로 고정하고 45는 stable(2026-10-20) 이후에 올린다. 구성은 electron-vite 5 + Vite 7 + TypeScript, electron-builder 26 NSIS per-user, fuses 적용이다. 테마는 nativeTheme / getAccentColor / prefersReducedTransparency를 쓴다. Mica/Acrylic은 #48031 실측 전까지 옵션으로만 둔다.

---

## 2. 폐기·정정된 주장

| 원 주장 | 판정 | 정정 내용 | 근거 |
|---|---|---|---|
| vibe 스킬·pitfalls.md:14 "`grok usage`는 TUI를 연다" | 틀림 | `grok usage <SESSION_ID> [TURN]`은 세션 토큰·비용 JSON 출력기다. 계정 한도는 TUI 슬래시 명령 `/usage`에만 있다 | `grok usage --help`; grok-docs/17-sessions.md:279-291 |
| GROK-14 "Orca Grok 조회는 GROK_HOME을 무시" | 틀림 | `GROK_HOME?.trim()\|\|~/.grok`를 따른다. 다만 프로세스당 1경로이고 첫 유효 세션만 쓰므로 멀티계정 불가라는 결론은 유지된다 | app.asar.unpacked/out/main/chunks/grok-session-paths-Dapl1QNA.js |
| GROK-11 "공개 클라이언트 근거는 02-authentication.md:61-65" | 인용 오류 | 해당 절은 고객사 SSO 등록 설명이다. auth.x.ai는 `client_secret_basic/post/none`을 모두 지원하므로 공개형이라는 증명이 아니다 | https://auth.x.ai/.well-known/openid-configuration |
| GROK-8 scope에 `conversations:*` 와일드카드 | 정정 | 실제는 `conversations:read conversations:write workspaces:read workspaces:write`이고 `billing:read`는 토큰 scope에 없다 | 로컬 JWT 클레임 디코드(값 마스킹) |
| GROK-6 "5시간 창이 없다고 명시, 리셋은 계정마다 다름" | 부분 | FAQ는 주간 풀만 설명한다(5h 부재를 명시하지 않음). 풀은 API·Build·Chat·Imagine·Voice가 공유하고, 한도 도달이 hard stop은 아니다 | https://docs.x.ai/grok/faq |
| GEM-3 "Gemini OAuth는 기본 키체인 저장이라 GEMINI_CLI_HOME만으로 분리 안 됨" | **반증** | 기본은 평문 `<home>/.gemini/oauth_creds.json`이다. 키체인은 `GEMINI_FORCE_ENCRYPTED_FILE_STORAGE=true`일 때만 쓰인다 | gemini-bundle/chunk-FQCNOBUR.js:278888-278913, 279359-279378 |
| GEM-5 "로컬 패치가 평문 토큰을 되살림" | 부분 | 패치 자체는 있다(2026-09-06 19:30, .bak 존재). 그러나 암호화 모드에서만 호출되므로 현재 경로에서는 비활성이고, 평문은 upstream 기본값이다 | 같은 파일, PowerShell 환경변수 조회 |
| CLAUDE-22 "Orca rateLimits.claude는 활성 계정만" | 틀림 | `rateLimits.inactiveClaudeAccounts[]`로 계정별 값이 나온다(60초 스로틀). 채워지는 시점은 사용 패널 열기, refresh RPC, subscribe 때뿐이다 | orca.asar@10684986, @10712186 |
| CLAUDE-20 "Orca가 관리 계정마다 CLAUDE_CONFIG_DIR 주입" | 틀림(Windows 호스트) | 활성 관리 계정의 자격증명을 `~/.claude/.credentials.json`에 덮어쓰고 되읽는 양방향 동기화 구조다. 현재 두 파일은 sha256이 같다 | orca.asar@10827454, @10828230, @10855032 |
| CLAUDE-19 "토큰 사본 3곳" | 정정 | 실제 토큰 값이 든 사본은 2곳(~/.claude, claude-accounts)이다. system-default-auth.json의 토큰 필드는 비어 있다 | 키 구조 검사 |
| CLAUDE-24 "UA를 claude-code로 줘야 429 회피(#202)" | 근거 없음 | #202는 닫힌 기능 제안이다. 확인된 것은 #30930(429, 직원 답변 없음)과 Orca가 그 UA를 쓴다는 사실뿐이다 | `gh issue view 30930`; orca.asar@10643028 |
| CLAUDE-4 "문서가 평문 저장이라고 명시" | 정정 | 평문 근거는 claude.exe 경고 문자열이다(@191057586). 이 PC의 ACL에는 `CodexSandboxUsers:(RX)`가 추가돼 있다 | `icacls ~/.claude/.credentials.json` |
| CLAUDE-14 claude.exe의 limits[].display_name 파서 | 약화 | 직접 확인한 곳은 Orca 파서(orca.asar@10643226)뿐이다. claude.exe에서는 필드명과 'Current week (' 문자열까지만 확인했다 | claude.exe@97980204 |
| CODEX-2 "production 미지원은 WebSocket만" | 정정 | 문서는 app-server 명령 자체도 experimental·production 미지원이라고 적는다 | codex-docs/learn_app-server.txt |
| CODEX-23 "device code가 두 번째 계정의 쿠키 재사용을 피함" | 추론 | 문서 근거가 없다. device code는 beta이고 ChatGPT 보안 설정에서 사전 활성화가 필요하다 | codex-docs/learn_auth.txt |
| AGY-3 "agy에 비대화형 쿼터 명령 없음" | 미확정 | 2026-09-12 빌드 help에 print 모드 슬래시 확장, `--disable-slash-commands`, `--output-format json`이 있다 | `timeout 20 agy.exe --help` |
| AGY-4 "격리 다중 계정 불가능" | 과장 | 확인된 범위는 "문서화된 분리 수단 없음 + wincred 단일 대상"까지다 | cmdkey /list, 바이너리 문자열 |
| AGY-7 "Antigravity와 Gemini CLI가 쿼터 공유" | 반대 정황 | Antigravity는 5시간 새로고침 + 주간 한도, Gemini CLI는 일 단위 요청 수다. Orca 값은 약 24시간 버킷 1개다 | https://antigravity.google/docs/plans/ ; https://geminicli.com/docs/resources/quota-and-pricing/ |
| ORCA-13 "/billing 폴백은 HTTP 실패 시" | 정정 | credits 응답에서 weekly·monthly 창을 모두 못 찾았을 때만 폴백한다. 401/403은 곧바로 error다 | orca.asar@10666920, @10670419 |
| ORCA-17 "런타임 authToken 전권은 추정" | 확인으로 격상 | 파이프 authToken으로 계정 전환·삭제, Codex 리셋 크레딧 consume까지 호출할 수 있다 | orca.asar@12374721, @8014216 |
| WIN-2 "#39708이 27 백포트, transparent 우회 불가는 공식 결론" | 정정 | 27-x-y 백포트는 #39802다. 해당 문장은 이슈 작성자 코멘트다. `transparent` 미사용 권장은 추론이다 | electron/electron PR #39708, #39802, issue #38532 |
| WIN-3 "#47386이 35~38에 백포트" | 정정 | 36~38만 백포트됐다(35 skipped). #48031은 frameless가 아닌 창에서도 재현된다 | PR #47386, issue #48031 |
| FUSE-2/3 electron-builder scheme 인용 | 정정 | 인용한 scheme은 26.15.3 태그와 다르다. 설정 키는 camelCase이고, 26.15.3에는 `wasmTrapHandlers` 키와 "서명 전 flip" 문구가 없다 | electron-builder@26.15.3 scheme.json raw |
| INST-3 "openAsHidden이 Windows 옵션에서 제거" | 정정 | 원래 macOS 전용 옵션이었다 | e44/api/app.md |
| TASK-3 "koffi asarUnpack은 공식 안내" | 정정 | 서드파티 출처뿐이다 | koffi.dev(해당 문구 없음) |
| SEC-2 CSP를 `<meta>`로 설정 | 정정 | meta CSP에서는 `frame-ancestors`가 무시된다. `protocol.handle` 응답 헤더 방식을 기본으로 한다 | CSP 명세, e44/api/protocol.md:151-190 |
| gemini 연구자 "실행 시각이 2026-09-14" | 오판 | Git Bash에는 tzdata가 없어 `TZ=Asia/Seoul date`가 UTC를 출력한다. KST로는 2026-09-15다 | 실행 출력, scratch mtime |

---

## 3. 공급자별 사실

### 3-0. 한눈 매트릭스

| 공급자 | 계정 격리 수단 | 로그인 위임 명령 | 공식 비대화형 쿼터 | 권장 쿼터 경로 | 권장 경로의 약관 위험 |
|---|---|---|---|---|---|
| Claude | `CLAUDE_CONFIG_DIR`(문서·로컬 재현) | `claude auth login --claudeai` | 없음 | statusline 브리지 + Orca 보조, 둘 다 없으면 측정 불가 | 낮음(Orca 보조는 간접적으로 중간) |
| Codex | `CODEX_HOME`(소스·관행) | app-server `account/login/start{chatgptDeviceCode}` | 있음(experimental) | app-server `account/rateLimits/read` | 낮음 |
| Grok | `GROK_HOME`(문서) | `grok login --device-auth` | 없음(ACP `x.ai/billing` 후보) | ACP 실측, 실패 시 /billing 직접 호출 여부를 결정 | 중간 |
| Gemini CLI | `GEMINI_CLI_HOME`(문서) | 사용자가 `gemini` 실행해 로그인 | 없음 | 로그인 상태만 | 낮음(직접 호출하면 높음) |
| Antigravity | 없음(wincred 단일) | agy 로그인(단일) | 없음(`agy -p "/usage"` 후보) | 실측 전 미표시 | 낮음(상태 확인만) |

### 3-1. Claude

**권장 인증(A)**
1. 위젯 전용 폴더 `%LOCALAPPDATA%\AIUsageWidget\claude\<acctId>`를 먼저 만든다.
2. 자식 프로세스 환경에서 다음 변수를 제거한다. `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN`, `CLAUDE_CODE_USE_BEDROCK/VERTEX/FOUNDRY`, `ANTHROPIC_PROFILE`, `ANTHROPIC_FEDERATION_RULE_ID`, `ANTHROPIC_ORGANIZATION_ID`, `AWS_BEARER_TOKEN_BEDROCK`, `ANTHROPIC_CUSTOM_HEADERS`(authentication 문서의 precedence). Orca가 지우는 목록은 이보다 짧다(orca.asar@5914964).
3. `CLAUDE_CONFIG_DIR=<폴더>`로 `claude.exe auth login --claudeai`를 `shell:false`, 파이프로 실행한다. 이 흐름은 Ink TUI가 아니다. stdout에 URL을 찍고, `Paste code here if prompted > ` 뒤 stdin 한 줄(`code#state`)을 받고, 성공하면 `Login successful.`과 exit 0이다(claude.exe@212727600~212731800).
4. 파이프 처리 주의점:
   - stdout이 TTY일 때만 OSC 8 이스케이프가 붙지만, ANSI/OSC 제거 파서는 넣어 둔다(claude.exe@201268404).
   - `#`이 없는 입력이 들어오면 끝나지 않고 계속 기다리므로 타임아웃과 kill이 필요하다.
5. 계정 레이블은 `claude auth status --json`으로 붙인다. 로그인 안 됐으면 exit 1이고, 이 명령도 대상 폴더에 `.claude.json`과 `backups/`를 만든다. 순수 읽기가 아니다(verify-cfg 재현).

**금지할 것**
- `~/.claude`나 `%APPDATA%\orca\claude-accounts\<uuid>\auth`를 계정 폴더로 쓰지 않는다. Orca가 덮어쓰고, 소유권 마커 검증과도 충돌한다(orca.asar@10652546, @10654746).
- `--console`을 노출하지 않는다. 머신에 저장된 claude.ai 로그인을 로그아웃시킨다(authentication, Sign in without an API key).
- `setup-token`이나 `CLAUDE_CODE_OAUTH_REFRESH_TOKEN` 방식은 위젯이 토큰을 store하게 되므로 쓰지 않는다.

**쿼터 소스**(공식 비대화형 경로 없음, commands.md:156, `claude --help`)

| 순위 | 경로 | 판정 |
|---|---|---|
| 1 | statusline 브리지. 위젯 폴더의 `settings.json` `statusLine.command`가 stdin JSON의 `rate_limits`를 파일로 기록한다 | 문서화돼 있고 토큰을 만지지 않는다(statusline.md:193-195, 293-306, 339). 단 **그 CONFIG_DIR로 대화형 세션이 돌 때만** 갱신되고, 첫 API 응답 이후에만 나오며, 문서상 Pro/Max 한정이다. 사용자가 평소 `~/.claude`로 일하면 위젯 폴더에서는 값이 계속 비어 있다(추론). `-p` 모드 실행 여부는 미확인 |
| 2 | Orca `rateLimits.claude` + `inactiveClaudeAccounts[]` | 계정별 값이 있지만 캐시다. 원천은 사칭 UA(`claude-code/2.1.0`)로 부르는 `/api/oauth/usage`와 Claude Code client_id를 쓴 직접 토큰 갱신이다(orca.asar@10643028, @10650976). "Orca 제공·비공식" 라벨이 필요하다 |
| 금지 | 위젯이 `.credentials.json`을 읽어 `/api/oauth/usage` 호출 | legal-and-compliance의 "collect, store, or intermediate" 금지, Consumer Terms의 "automated or non-human means" 금지, 429 이슈 #30930 |
| 금지 | `anthropic-ratelimit-unified-*` 응답 헤더 | 미문서화이고, 조회할 때마다 추론 1회로 쿼터를 소모하며 토큰을 직접 써야 한다(claude.exe@103168640) |
| 금지 | PTY로 `/usage` 스크래핑 | Orca는 이 경로에서 신뢰 프롬프트에 `y`를 자동 전송하고(orca.asar@10636324), Windows에서는 비활성화했다 |

**표시 가능한 수치**
- 5시간 창·7일 창의 `used_percentage`와 `resets_at`(statusline은 epoch 초, Orca는 ms).
- 모델별 주간(`fableWeekly`)은 Orca 비공식 경로에서만 나온다.
- `spend_limit`는 gateway 전용이다.
- 플랜(`subscriptionType`)과 orgName은 `auth status`로 얻는다.
- **로그인 만료 시각은 공식 CLI로 알 수 없다.** 실패하거나 "Login expired"가 나와야 감지된다(authentication, Renew an expiring login).

**공식성·약관**
- 로그인 A는 위험이 낮다. "수정하지 않은 Claude Code 바이너리에 자기 구독으로 로그인"은 막지 않는다는 조항에 해당한다.
- 같은 문서의 "Pro/Max 한도는 ordinary, individual usage를 전제한다"는 문장은 여러 구독 계정을 다루는 도구와 긴장 관계가 있다. 위젯은 표시만 하므로 직접 해당하지는 않는다고 본다(추론).

**실측 필요**
- 파이프로 실행한 `auth login`이 브라우저 콜백 또는 코드 붙여넣기로 끝까지 완료되는가.
- 같은 계정을 `~/.claude`·Orca·위젯 폴더에 따로 로그인했을 때 서로의 토큰을 무효화하는가.
- `claude -p` 헤드리스에서 statusline이 실행되는가.
- Team/Enterprise 계정에서 `rate_limits`가 나오는가.
- Claude 계정이 2개 이상일 때 Orca `inactiveClaudeAccounts`가 어떤 조건에서 채워지는가.

### 3-2. Codex

**권장 인증(A)**
1. 위젯 전용 `CODEX_HOME` 폴더를 **먼저** 만든다. keyring 키는 `canonicalize(codex_home)`의 sha256이라 폴더가 없으면 원 경로로 해시되어 키가 달라진다(codex-docs storage.rs L238-248).
2. `CODEX_HOME=<폴더>`로 `codex app-server`를 stdio로 실행한다. 참고로 Orca의 인수는 `-c approval_policy=never -s read-only -a never app-server`다(orca.asar@5930919). `--analytics-default-enabled`는 넘기지 않는다.
3. `initialize{clientInfo:{name:'ai-usage-widget',version}}`를 보낸다. `experimentalApi`는 생략해 stable 표면만 쓴다.
4. `initialized` 알림을 보낸다.
5. `account/login/start{type:'chatgptDeviceCode'}` 응답의 `{loginId,userCode,verificationUrl}`을 UI에 표시한다(문서 예시 URL은 https://auth.openai.com/codex/device).
6. `account/login/completed`를 기다린 뒤 `account/read`로 email(마스킹)과 planType을 확인한다.
7. `initialize` 응답의 `codexHome`으로 격리를 검증한다(codex-schema/v1/InitializeResponse.json).

- 대안: `chatgpt`(authUrl, app-server가 localhost 콜백을 받음) 또는 CLI `codex login --device-auth`.
- 전제: device code 로그인은 beta다. 개인은 ChatGPT 보안 설정에서, 워크스페이스는 관리자가 켜야 한다(learn_auth.txt).
- **금지**
  - `chatgptAuthTokens`: 스키마에 "[UNSTABLE] FOR OPENAI INTERNAL USE ONLY - DO NOT USE"라고 적혀 있다.
  - `apiKey`: 플랜 한도와 무관하다.
  - `~/.codex`나 Orca `codex-accounts`·`codex-runtime-home` 공유: 갱신한 토큰을 파일 락 없이 auth.json에 다시 쓰므로 refresh 경합이 생긴다(codex-docs auth_manager.rs L1571-1593, L2062).
  - `account/rateLimitResetCredit/consume`, `account/sendAddCreditsNudgeEmail`: 부작용이 있는 호출이다.
- **Windows 실행**: codex는 npm shim이다(`C:\Users\202502\AppData\Roaming\npm\codex.cmd`). shell 없이 `.cmd`를 spawn하면 EINVAL이 난다(node v24.14.1 실측, CVE-2024-27980). node와 JS 엔트리를 직접 실행하거나 `cmd.exe /d /c`로 엄격하게 인용한다. JS 엔트리의 실제 경로는 미확인이다.

**쿼터 소스**
- `account/rateLimits/read`를 호출하고 결과를 받으면 프로세스를 종료한다. Orca의 주 경로와 같다(host 기준 init 30초 / rpc 10초, orca.asar@10628681).
- `account/rateLimits/updated`는 sparse 갱신이라 직전 read 결과에 병합해야 한다(codex-schema AccountRateLimitsUpdatedNotification.json). 보조 수단으로만 쓴다.
- Orca 폴백 `chatgpt.com/backend-api/wham/usage`는 `User-Agent: codex-cli`, `originator: Codex Desktop`을 사칭하므로 배제한다(orca.asar@10612193).

**표시 가능한 수치**(codex-schema/v2/GetAccountRateLimitsResponse.json)
- `rateLimitsByLimitId`의 각 버킷이 가진 primary/secondary 창: `{usedPercent:int, windowDurationMins, resetsAt(Unix 초)}`. 문서 예시와 Orca 코드로 단위가 초임을 확인했다.
- 창 분류는 `windowDurationMins`로 한다. 300은 5시간, 10080은 주간, 그 밖의 값은 "기타 창"으로 표시한다. 문서 예시에는 15/60분 창과 `codex_other` 버킷이 있는데 Orca는 이를 버린다.
- `planType`: 17종 + unknown. 모르는 값도 허용해야 한다.
- `credits{hasCredits,unlimited,balance}`, `rateLimitReachedType`, `rateLimitResetCredits.availableCount`.
- 현재 Orca 캐시 값: session null, weekly 10080분 88%(`orca list`).

**공식성·약관**
- 약관 위험은 낮다. account 메서드는 모두 stable 스키마에 있다. experimental로 생성해도 account 쪽 추가는 bedrock 2개뿐이다(스키마 차집합 비교).
- 다만 app-server는 experimental이고 스키마는 실행한 버전 전용이다. 따라서 codex-cli 최소 버전을 고정하고, 빌드 시 generate-json-schema 결과를 비교하며, 알 수 없는 필드를 허용해야 한다.

**실측 필요**
- 빈 CODEX_HOME에서 device code 로그인 후 auth.json이 실제로 그 폴더에 생기는가.
- Pro 계정의 실제 버킷 키와 창 길이.
- `rateLimits/read`나 `account/read`가 토큰을 갱신하면서 auth.json을 다시 쓰는가.
- 같은 CODEX_HOME을 동시에 쓸 때 sqlite 잠금 문제가 있는가, daemon 소켓이 CODEX_HOME별로 분리되는가.
- `codex doctor` 출력 형식.

### 3-3. Grok

**권장 인증(A)**
- 계정마다 `GROK_HOME=<위젯 폴더>`를 두고 `grok login --device-auth`로 로그인한다(URL·코드 출력 후 폴링, `grok login --help`, grok-docs/02-authentication.md:245-253).
- 대안 후보: ACP `grok agent stdio`의 `x.ai/auth/get_url`·`submit_code`(grok-docs/15-agent-mode.md:154), `grok agent --reauth`.
- leader 모드는 기본 off다(02-authentication.md:224-225). 켜지 않으면 leader 소켓 충돌은 문제가 되지 않는다.
- 토큰 수명은 exp−iat = 21600초(약 6시간)다. CLI는 만료 300초 전(`GROK_AUTH_EARLY_INVALIDATION_SECS`)이나 401을 받았을 때 스스로 갱신하고, auth.json 변경을 핫리로드한다(02-authentication.md:241, 259-281).
- **금지(A3)**: 위젯이 직접 OIDC refresh_token grant를 수행하는 것. CLI의 OAuth 클라이언트를 가장하는 것이고, grok.exe에 리프레시 토큰 회전을 추적하는 코드(`idp_rotated`, `disk_rt_prefix`, `auth.refresh.sibling_rotation_demoted`)가 있어 CLI 로그인을 깰 위험이 크다.

**쿼터 소스(우선순위)**
1. **ACP `x.ai/billing`**(실측 필요). grok.exe 인라인 상수 `x.ai/bil`+`ling`이 4곳에 있고 'handling billing config request' 문자열도 있다. 계정별 `GROK_HOME=<dir> grok agent stdio`로 로그인·갱신·조회를 모두 공식 바이너리에 맡기면 위젯은 토큰을 만지지 않는다.
2. **A1: /billing 직접 호출.** 위젯 메인이 `<GROK_HOME>\auth.json`의 `https://auth.x.ai::<client_id>` 항목에서 `key`, `expires_at`, `user_id`만 읽는다. 이 파일에는 email, first_name, last_name, profile_image_asset_id 같은 PII가 있으니 나머지는 버린다.
   - 호출: `GET https://cli-chat-proxy.grok.com/v1/billing?format=credits`
   - 헤더: `Authorization: Bearer`, `X-XAI-Token-Auth: xai-grok-cli`, `Accept: application/json`, 선택 `x-userid`
   - 근거: grok.exe@0x82e6252, 내장 헤더 표; orca.asar@10668801
   - `x-grok-client-*`와 `x-email`은 보내지 않는다(CLI 헤더 후보 문자열에 있음). User-Agent는 위젯 고유값으로 둔다.
   - 만료까지 5분 이내면 호출하지 않는다. 갱신 트리거 후보는 `grok models`인데 실측이 필요하다.
   - 위험은 중간이다. 비공개 엔드포인트이고, X-XAI-Token-Auth 헤더 자체가 "CLI 세션 토큰으로 검증하라"는 선택자라 '가장 금지' 원칙상 허용 여부를 결정해야 한다.
3. **B: Orca `rateLimits.grok`.** 단일 계정, 캐시다. 토큰 만료 5분 이내면 `delegated-refresh-required`를 반환하고 갱신하지 않는다(orca.asar@10168311). `authProvenance`에 이메일이 평문으로 들어 있다.
- **부적합**
  - `grok usage`(세션 단위 전용), TUI `/usage`.
  - Management API(`/v1/billing/teams/{team_id}/usage` 등): API 과금용이라 SuperGrok 주간 풀이 없고, 별도 Management Key가 필요하다. base URL 표기도 문서끼리 충돌한다(management-api.x.ai vs api.x.ai).
  - `XAI_API_KEY` 인증: billing 불가(grok.exe billing.rs 문자열).
  - OTEL: 토큰 수만 내보낸다.

**표시 가능한 수치**
- 주간: `creditUsagePercent`, 리셋은 `currentPeriod.end`. Orca는 `currentPeriod.type==='USAGE_PERIOD_TYPE_WEEKLY'`이면서 billingPeriod와 일치할 때만 weekly로 매핑한다.
- 없으면 월간: `used.val / monthlyLimit.val`.
- 보조: `onDemandUsed`/`onDemandCap`, `prepaidBalance`, `subscriptionTier`, `isUnifiedBillingUser`, `on_demand_enabled`.
- 5시간 창은 없다(FAQ에 언급 없음, Orca session null).
- **100%를 차단으로 표시하지 않는다.** 추가 크레딧으로 계속 쓸 수 있다(FAQ). 현재 Orca 캐시도 weekly 100%인데 status가 ok다. 리셋은 2026-09-17T07:51Z(= 16:51 KST)다(`orca list`).

**실측 필요**
- `grok agent stdio` initialize 응답에 `x.ai/billing`이 있는가, 응답 형태는 무엇인가.
- `grok models`가 만료 임박 토큰을 갱신하고 해당 GROK_HOME에 되쓰는가, windowsHide로 창 없이 끝나는가.
- `--device-auth`가 stdout만 쓰고 끝나는가.
- 리프레시 토큰이 실제로 회전하는가.
- 팀·무료·X Basic 계정에서 응답이 어떻게 다른가.
- 429 응답의 형식.
- xAI 약관상 허용 여부.

### 3-4. Gemini CLI

**선결 사항**: 공식 문서에 "Gemini CLI was replaced by Antigravity CLI on June 18th, 2026"이 있고, 대상은 무료 티어와 Google One 사용자다(https://geminicli.com/docs/resources/quota-and-pricing/). 사용자 계정 등급에 따라 Gemini CLI 카드의 전제가 무너질 수 있다. `~/.gemini/oauth_creds.json` mtime(2026-09-14 23:59)은 Orca도 이 파일을 다시 쓰므로 CLI 사용 증거가 아니다.

**권장 인증(A)**
- 계정별 `GEMINI_CLI_HOME=<dir>`만으로 `<dir>\.gemini\oauth_creds.json`이 분리된다(chunk-FQCNOBUR.js:251979-251989. 정적 근거).
- 평문을 피하려면 `GEMINI_FORCE_ENCRYPTED_FILE_STORAGE=true`와 `GEMINI_FORCE_FILE_STORAGE=true`를 함께 준다. 두 변수 모두 공식 설정 문서에 없어 버전이 바뀌면 사라질 수 있고, 실측이 필요하다.
- 격리에 구멍이 있다. gemini.js:42는 `<GEMINI_CLI_HOME>/settings.json`을 `.gemini` 없이 읽고, sandbox 정책 경로는 `os.homedir()`을 직접 쓴다(chunk-MFLFXOVQ.js:257206).
- 위젯은 토큰 값을 읽지 않는다. 파일 존재 여부와 `settings.json`의 `security.auth.selectedType`만 본다.

**쿼터 소스**
- 공식 비대화형 경로가 없다. 내부 API `POST https://cloudcode-pa.googleapis.com/v1internal:retrieveUserQuota`뿐이다(chunk-FQCNOBUR.js:310862-310863, 311086-311091).
- **약관이 직접 금지한다**: "Directly accessing the services powering Gemini CLI … using third-party software … may be grounds for suspension"(https://geminicli.com/docs/resources/tos-privacy/). Google 메인테이너가 2026-02에 정지 사례를 인정했고 이후 일괄 해제와 이의신청 절차가 있었다(google-gemini/gemini-cli discussions #20632).
- Orca B의 문제:
  - 고정 경로 `~/.gemini/oauth_creds.json` 단일 계정이고 GEMINI_CLI_HOME은 0건이다.
  - `ideType:'GEMINI_CLI'`를 붙인다. 실제 CLI는 `IDE_UNSPECIFIED`다(chunk-FQCNOBUR.js:311383-311386).
  - gemini-cli의 OAuth client secret을 정규식으로 추출해 토큰을 갱신한다. 이 설치 레이아웃에는 대상 파일이 없어 성공 여부는 미검증이다.
  - OpenCode auth.json도 읽는데, OpenCode는 금지 하네스로 명시돼 있다.
  - 결론적으로 간접 약관 위험이 중간~높음이다.
- 후보: `gemini -p "/stats model"`. 비대화형 모드도 슬래시 명령을 내장 명령으로 실행한다(gemini-CKAAKWBN.js:10821-10880, 11212). 하지만 비대화형 UI는 text 항목만 출력하므로 stats 표가 나오지 않을 가능성이 높다(정적 추론, 실측 필요).

**표시 가능한 수치**
- 권장: 로그인 상태, 그리고 공식 문서의 플랜별 일일 한도를 참고값으로 표시한다(AI Pro 1,500 요청/일, Ultra 2,000 요청/일, Code Assist Individual 1,000 요청/일).
- Orca 값을 참고로 쓸 경우 `buckets[].usedPercent/resetsAt`만 쓰고 "Orca 제공·비공식·단일 계정" 라벨을 붙인다. `windowMinutes:60`은 고정값이라 틀렸다(실제 약 24시간, orca-main.js Fzi).

**실측 필요**: 테스트 계정 두 개로 GEMINI_CLI_HOME과 FORCE 변수 조합 격리, `gemini -p "/stats model"` 출력, 사용자 계정 등급.

### 3-5. Antigravity(agy)

**인증**
- 멀티계정 수단이 없다. 자격증명은 wincred `LegacyGeneric:target=gemini:antigravity` 단일 대상이다.
- AGY_*/ANTIGRAVITY_* 이름 중 홈·설정 디렉터리 오버라이드는 발견하지 못했다. `ANTIGRAVITY_EXECUTABLE_DATA_DIR`, `AGY_ADC_AUTH`의 의미는 미확인이다.
- 위젯은 대상 이름의 존재 여부만 확인할 수 있다.

**쿼터 소스**
- 공식은 TUI `/usage`(`/quota`)뿐이다(https://antigravity.google/docs/cli/commands/usage/).
- 후보: `agy -p "/usage" --output-format json`. 설치본 help에 print 모드 슬래시 확장이 있다. 확장이 안 되면 AI 프롬프트로 처리되어 요청 1회를 소모할 수 있다.
- **금지**
  - 로컬 language server RPC(`RetrieveUserQuotaSummary`, `GetUserStatus`, `ANTIGRAVITY_CSRF_TOKEN`): Antigravity 약관이 제3자 소프트웨어 접근을 위반으로, Antigravity 및/또는 Gemini CLI 계정의 정지 사유로 명시한다(https://antigravity.google/terms/).
  - Orca `rateLimits.antigravity` 표시: Gemini 결과를 provider 이름만 바꿔 복사한 값이다(orca-main.js eHi. 재실행 비교에서 provider 제외 동일). 표시하면 오표시다.

**표시 가능한 수치**
- 공식 구조: Pro/Ultra는 5시간마다 새로고침되고 주간 한도가 있다. 그 외 플랜은 주간 새로고침이다. AI Credits 잔액이 있다(docs/plans).
- 현재 위젯이 정당하게 얻을 수 있는 수치는 **없다**(실측 전).

---

## 4. A / B / C 비교

| 기준 | A: 공식 CLI 위임 + 위젯 전용 격리 폴더 | B: Orca를 소스로 | C: A 주 + B 보조 |
|---|---|---|---|
| Claude | 계정별 로그인 가능. 수치는 statusline 브리지(해당 폴더로 대화형 사용할 때만)에서만 나와 거의 비어 있음 | 계정별 값(inactive 포함), 캐시, 비공식 원천 | 로그인은 A, 수치는 브리지 우선 + Orca 보조 |
| Codex | 계정별 즉시 조회(stable 메서드) | 계정별 구조는 있으나 이 PC의 관리 계정 0개(systemDefault만) | A |
| Grok | 계정별(ACP 또는 /billing, 결정 필요) | 단일 계정(Orca 프로세스 GROK_HOME) | A, B는 기본 계정 교차검증 |
| Gemini CLI | 계정별 로그인 상태만 | 단일 계정 % (약관 위험 간접 상속) | 상태만. Orca %는 선택적 참고 |
| Antigravity | 실측 전 불가 | 가짜값(Gemini 복사) | 제외 |
| 최신성 | 새로고침 버튼으로 즉시(Codex·Grok) | 항상 캐시. 폴링은 Orca 창이 보이고 포커스일 때만 900초 주기이고 `orca serve`에서는 없음(orca.asar@10709573). 강제 갱신은 전권 authToken RPC가 필요 | 즉시 + 캐시 표시 |
| 토큰 취급 | CLI가 소유. Grok A1만 메인 메모리로 key를 읽음 | 위젯은 토큰을 안 만짐 | 동일 |
| 사칭·약관 | 사칭 없음(Grok 헤더 해석만 결정 필요) | Orca가 UA·ideType·client secret 사칭 → 간접 상속 | A 기준, B 값에 출처 라벨 |
| 외부 의존 | CLI 설치·버전 드리프트 | Orca 실행 필수(`runtime_unavailable`), 무버전 JSON, PII 혼재(email, organizationName, systemDefault.email, authProvenance) | 둘 다, 단 B는 선택 |
| 구현량 | 중~상 | 하 | 중상 |

**권장: C.** Codex·Grok은 A로 계정별 즉시 조회가 가능하다. Claude는 A만으로는 수치 공백이 커서 B 보조의 실익이 있다. Gemini·Antigravity는 A도 B도 정당한 수치를 주지 못한다.

**C의 Orca 어댑터 규칙**(orca 토픽 검증 결과)
1. `orca status --json`으로 헬스체크한다(`result.app.running`, `result.runtime.reachable`).
2. capability를 감지해 `orca resource status --json [--refresh]`를 우선 쓴다. 이 명령은 PR stablyai/orca#19703(2026-09-10 기준 open)으로 추가 중인 식별정보 없는 읽기 전용 계약이고, 로컬 1.4.200에는 없다(`Unknown command: resource`). 없으면 `account list --json`으로 폴백한다.
3. **파이프 RPC와 `orca-runtime.json`의 authToken은 쓰지 않는다.** 이 토큰은 `accounts.removeClaude`, `selectClaude`, `consumeCodexResetCredit`, `terminal.send`까지 부를 수 있는 전권 토큰이다.
4. `ORCA_USER_DATA_PATH` 환경변수를 존중한다(orca.cli/runtime/metadata.js:41-43). Orca가 꺼져 있어도 대신 띄우지 않는다.
5. `resetsAt`(ms)를 쓰고 `resetDescription`(로케일 문자열)은 무시한다. `status==='error'` 값은 최대 30분(rate-limited면 24시간) 전 성공값일 수 있으니 stale로 표시한다(orca.asar@10686824). stale 임계는 5분이다(Orca 자체 기준 3e5 ms, @10710637).
6. `antigravity` 키와 gemini의 `windowMinutes`는 무시한다. 식별정보는 메인 프로세스에서 마스킹한 뒤 renderer로 넘긴다.
7. A 계정과 Orca 계정이 겹치면 org UUID(`claude auth status` orgId ↔ Orca organizationUuid) 또는 이메일 해시로 합친다(추론).

---

## 5. 플랫폼 스택 권장

| 영역 | 권장 | 근거·주의 |
|---|---|---|
| Electron | **44.3.0 정확 고정**(latest, 2026-09-08 게시, M152 / Node 24.18.1, EOL 2027-03-02). 45는 stable(2026-10-20) 이후 패치가 1~2회 나오면 올림 | `npm view electron dist-tags`; https://releases.electronjs.org/schedule. 지원은 최신 stable 3개뿐이라 v34는 지원 범위 밖. 44의 breaking: ia32 제거, **renderer `clipboard` 제거**(IPC나 W3C Clipboard로 대체), 42부터 postinstall 자가 다운로드 없음(e44/breaking-changes.md:100, 113, 473) |
| 스캐폴딩 | electron-vite **5.0.0** + vite **7.3.6** + TypeScript, UI 프레임워크 없이 순수 TS/DOM | peer vite ^5\|\|^6\|\|^7. Vite 8은 6.0.0-beta.1만 지원. Forge Vite 템플릿은 experimental. electron-vite 5.0.0은 2025-12-07 이후 새 stable이 없어 유지보수 위험이 있고, Electron 44와의 공식 호환 표기도 없음(실측) |
| 패키징 | electron-builder 26.x NSIS `oneClick:true`, `perMachine:false` → `%LOCALAPPDATA%\Programs\<app>` | 기본값이 per-user(26.15.3 scheme). 설치 폴더 ACL은 소유자·SYSTEM·Administrators만 전체 권한(icacls). **26.15.3(latest)과 26.16.1(v26 태그) 중 고정 버전 결정 필요.** Squirrel은 앱 이름 공백 경고가 있어 비권장 |
| 기존 설치 | `C:\AI.Usage.Widget-1.0.2-win`에서 이전 후 제거 | `Authenticated Users:(I)(M)`라 로그인한 모든 사용자가 exe·asar를 수정할 수 있음(icacls) |
| Fuses | `electronFuses`: `runAsNode:false`, `enableCookieEncryption:true`, `enableNodeOptionsEnvironmentVariable:false`, `enableNodeCliInspectArguments:false`, `enableEmbeddedAsarIntegrityValidation:true`, `onlyLoadAppFromAsar:true`, `grantFileProtocolExtraPrivileges:false` | 기본값은 e44/tutorial/fuses.md. 26.15.3에는 `wasmTrapHandlers` 키 없음. `runAsNode:false`면 `child_process.fork`가 실패하므로 spawn/execFile 또는 utilityProcess 사용. 검증은 `npx @electron/fuses read --app <exe>`. 무서명이면 퓨즈를 되돌릴 수 있어 심층방어 수준이고, Windows는 AppLocker 같은 정책 없이는 실행 시 변조를 차단하지 않음 |
| 보안 기본 | `app://` 커스텀 프로토콜(`registerSchemesAsPrivileged` + `protocol.handle`, `path.resolve` 후 번들 루트 접두어 비교). CSP는 **응답 헤더**로: `default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'`(개발 빌드만 `ws:`) | 체크리스트 7·13·14·15·17·18·19(e44/tutorial/security.md:96-117). `setWindowOpenHandler`는 deny, navigation 제한, IPC sender 검증. `shell.openExternal`은 메인에서 enum을 받아 고정 https 허용목록만 열기(Windows 2081자 제한, e44/api/shell.md:46-67). renderer에는 마스킹된 수치 DTO만 |
| 비밀 저장 | 원칙적으로 위젯이 토큰을 보관하지 않음. 꼭 필요한 비밀만 `safeStorage.encryptStringAsync` | Windows는 DPAPI라 다른 사용자로부터는 보호하지만 같은 사용자 권한의 앱은 막지 못함(e44/api/safe-storage.md:42). 위젯이 토큰을 안 가져도 CLI·Orca 쪽 평문 파일은 그대로라 줄어드는 것은 **위젯의 노출면**뿐 |
| 자식 프로세스 | `shell:false`, `windowsHide:true`, argv 배열, 타임아웃 + 프로세스 트리 kill, 계정별 env 화이트리스트. `.exe`(claude.exe, grok.exe, agy.exe, orca.exe)는 직접 실행. npm shim(codex, gemini)은 node + JS 엔트리 | `.cmd` spawn EINVAL 실측(node 24.14.1). Orca도 win32에서 `/d /c` 래퍼 사용(orca.asar@10629651) |
| 폴링·백오프 | 메인 프로세스 전용 스케줄러, 지수 백오프 + 지터, Retry-After 준수, 새로고침 버튼 최소 간격, lastUpdated와 stale 표시, mock 값 금지 | 참고로 Orca는 `min(30s·2^(n-1), 15분)`, streak 상한 8(orca.asar@10710637, @10687416) |
| 테마 | `nativeTheme.shouldUseDarkColors` + `'updated'`. 작업표시줄 인접 UI는 `shouldUseDarkColorsForSystemIntegratedUI`. `inForcedColorsMode`면 재질 끄기. `prefersReducedTransparency`가 true면 `backgroundMaterial:'none'` | e44/api/native-theme.md:11-22, 66-86. Chromium이 Personalize 레지스트리를 감시(os_settings_provider_win.cc:163-215). 이 PC는 SystemUsesLightTheme=1, AppsUseLightTheme=1, EnableTransparency=1 |
| 강조색 | `systemPreferences.getAccentColor()`. `'accent-color-changed'`는 트리거로만 쓰고 재조회 | 문서는 macOS 전용이라 적지만 e44 소스에 Windows 구현이 있음(electron_api_system_preferences.cc:91, _win.cc:87-94). 이 PC 기대값은 `0078d4ff`. 이벤트 페이로드는 DWM colorization 값이라 `0078d4c4`처럼 알파가 다름(추정) |
| 재질 | `frame:false` + `backgroundMaterial:'acrylic'\|'mica'`, `transparent` 미사용, `thickFrame:false`. **#48031 실측 전까지 기본은 불투명 토큰 색** | Win11 22H2+ 전용이고 이 PC는 26200(e44/api/base-window.md:1514-1528). #48031은 가려지거나 화면 밖이거나 Energy saver일 때 검정·회색이 되는 버그로 not planned 종료, 일반 창에서도 재현 |
| 작업표시줄 위치 | 기본: 대상 디스플레이의 `bounds`와 `workArea` 차이 + `'display-metrics-changed'`. 자동 숨김 대응이 필요하면 koffi 3.2.1로 `SHAppBarMessage`(`ABM_GETSTATE`→`ABS_AUTOHIDE`, `ABM_GETTASKBARPOS`)를 메인에서만 로드하고 실패 시 폴백 | e44/api/screen.md:91-101. MS Learn ABM_GETTASKBARPOS(기본 작업표시줄만 반환). Win11은 하단 고정(2차 출처). 이 PC의 StuckRects3 해석은 하단, 자동 숨김 아님, 48px @96dpi(비문서 형식 추정). koffi asarUnpack은 서드파티 출처라 패키징 실측 필요 |
| 자동 시작 | `app.setLoginItemSettings({openAtLogin, path, args:['--autostart'], enabled, name})` | e44/api/app.md:1475-1530 |
| 서명·배포 | 본인 PC 전용이면 무서명 로컬 빌드로 충분. 타인 배포 시 OV($150–300/년), SignPath Foundation(OSS 무료), MS Store MSIX 중 선택 | 이 PC Smart App Control은 Off(`VerifiedAndReputablePolicyState=0`, Off는 단방향). 한국 거주 개인은 Azure Artifact Signing 대상이 아님(개인은 미국·캐나다만). EV는 SmartScreen 즉시 통과 이점이 없음(MS Learn code-signing-options, smartscreen-reputation). Electron code-signing 문서 일부는 MS Learn과 불일치하므로 MS Learn 기준 |

---

## 6. 지금 정할 것

| ID | 결정 | 안 정하면 막히는 것 | 권장 |
|---|---|---|---|
| D1 | A / B / C | 공급자 인터페이스와 계정 모델 설계 | C |
| D2 | Claude 수치 소스 | Claude 카드 | statusline 브리지 + Orca 보조, 둘 다 없으면 "측정 불가". `/api/oauth/usage` 직접 호출 금지를 확정 |
| D3 | Grok 쿼터 경로 | Grok 카드, 토큰 접근 여부 | ACP 실측(T4) 후 결정. 실패하면 `X-XAI-Token-Auth` 헤더를 허용해 /billing을 직접 부를지, Orca 단일 계정을 쓸지, "측정 불가"로 둘지 선택 |
| D4 | Gemini 카드 범위 | Gemini 카드 | 계정 등급 확인 후 "로그인 상태 + 문서 한도 참고". Orca %는 기본 숨김 |
| D5 | Antigravity 포함 여부 | 카드 수 | T6 결과가 성공이면 포함, 실패면 제외 |
| D6 | 재질 기본값 | 테마 구현 | T8 전까지 불투명, 재질은 설정 옵션 |
| D7 | 배포 범위와 서명 | 빌드 파이프라인 | 본인 PC 전용이면 무서명 |
| D8 | electron-builder 버전(26.15.3 vs 26.16.1) | 퓨즈 설정 검증 | 26.15.3 고정 후 `@electron/fuses read`로 검증 |
| D9 | 로컬 gemini-cli 패치 원복 | 없음(현재 경로에서 비활성) | 보류 가능 |
| D10 | scratch 원본 `orca_accounts_raw.json` 처리 | PII 잔존 | 삭제 또는 마스킹본으로 교체(사용자 승인 필요) |

---

## 7. 실측 계획(사용자 참관, 영향 명시)

| ID | 테스트 | 부작용·비용 | 결정에 주는 영향 |
|---|---|---|---|
| T1 | 빈 CODEX_HOME에서 app-server device code 로그인 → `codexHome`, auth.json 위치, `rateLimits/read` 실제 버킷·창, 호출 후 auth.json mtime 변화 | 새 로그인 세션 1개, 원격 호출 | Codex A 확정 |
| T2 | 빈 CLAUDE_CONFIG_DIR로 `claude auth login --claudeai` 파이프 실행 → 콜백·코드 붙여넣기 경로, 이후 `~/.claude`·Orca 로그인 유지 여부 | 새 로그인 세션 | Claude A 확정 |
| T3 | 위젯 폴더로 대화형 1회와 `claude -p` 1회 실행 → statusline `rate_limits` 기록 여부 | 쿼터 소모 | D2 |
| T4 | `GROK_HOME=<빈폴더> grok agent stdio` initialize로 메서드 목록 확인 → 로그인 → `x.ai/billing` 응답. 이어서 `grok models`의 갱신·되쓰기와 windowsHide | 새 로그인 세션, 원격 호출 | D3 |
| T5 | CLI가 스스로 갱신하기 전후 refresh_token 접두 비교(마스킹) | 없음(관찰만) | A3 금지 근거 확정, 동시 갱신 안전성 |
| T6 | `agy -p "/usage" --output-format json` | 확장 실패 시 요청 1회 소모 가능 | D5 |
| T7 | 사용자 계정 등급 확인, `gemini -p "/stats model"`, 테스트 계정 2개로 GEMINI_CLI_HOME + FORCE 두 변수 격리 | 로그인 필요 | D4 |
| T8 | Electron 44.3.0 최소 창: backgroundMaterial의 가림·화면 밖·Energy saver 동작, `getAccentColor()` 반환값, 투명도만 토글했을 때 `'updated'` 발생 여부, NSIS 빌드 `@electron/fuses read`, asar 무결성 켠 상태 기동, koffi 패키징, electron-vite 5 빌드 | 로컬 전용 | D6, D8 |
| T9 | Orca 정지 상태에서 `orca account list --json`의 종료코드·stderr. Claude 2계정일 때 `inactiveClaudeAccounts` 채움 조건 | Orca 상태 변경(사용자 판단) | B 어댑터 오류 처리 |

---

## 8. 완결성 비판: 미검증·미열람 항목

**1) 실측이 0건이다.** 원격 동작과 로그인 흐름은 모두 정적 근거(바이너리 문자열, 번들, 스키마, 문서)에 기대고 있다. 결정을 뒤집을 수 있는 핵심 불확실성은 세 가지다.
- Codex `rateLimits/read`의 실제 값
- Grok ACP `x.ai/billing`의 존재
- Claude 파이프 로그인이 끝까지 완료되는지

**2) 버전 고정이 어긋난 근거가 있다.**
- codex 소스(storage.rs, auth_manager.rs, types.rs)는 main 브랜치 사본이고 0.154.0 태그와 대조하지 않았다.
- electron-builder NSIS 템플릿은 master 사본이다.
- Orca 오프셋은 추출본(orca-main.js) 기준과 원본 app.asar 바이트 기준이 섞여 있다.

**3) 읽지 않았거나 추적하지 않은 항목**
- **기존 v1.0.2의 `resources\app\dist-electron\main.js` 자체**는 이번 6개 토픽에서 재분석하지 않았다. mock 값, 사칭 UA·ideType, 평문 토큰, 렌더러 유출, CSP 부재 같은 결함 목록은 배경 전제이지 이번 검증 대상이 아니었다. 기존 설정·계정 데이터를 v2로 옮기는 경로도 조사하지 않았다.
- **xAI 소비자·API 약관 원문을 읽지 않았다.** Anthropic·Google·Antigravity는 약관 원문을 확인했지만 Grok은 "공개 문서 없음"에서 멈췄다. D3 결정 전에 필요하다.
- **API 키 계정용 사용량 경로를 조사하지 않았다.** Anthropic Admin/Usage API, OpenAI usage/costs API, Gemini API(AI Studio) 쿼터 조회가 해당된다. xAI Management API만 조사했다. 위젯이 API 키 계정을 지원할지 정하기 전에 필요하다.
- Orca: `fetchAll` 본문(비활성 계정 포함 여부), `buildInactiveArray`의 실제 모양(이 PC에서는 빈 배열), OpenCode 자격증명 우선순위, Gemini client secret 추출 폴백(bzi/Szi/xzi) 성공 여부, PR #19703의 병합 여부와 탑재 버전, Orca 공식 문서.
- Claude: Consumer Terms 조항 번호, claude.exe의 limits[] 파서, Team/Enterprise의 `rate_limits`, 로그인 만료 시각을 기계적으로 읽는 공식 수단(없음으로 판단했으나 출력 전수 확인은 안 함).
- Codex: community.openai.com 스레드 재조회, daemon의 CODEX_HOME 분리, `codex doctor`, npm shim 뒤 JS 엔트리의 실제 경로.
- Grok: Management API base URL 충돌, auth.json `team_id`와 Management API team_id가 같은지, 팀·무료 계정 응답, 429 형식.
- Gemini·Antigravity: Antigravity CLI 대체 공지와 사용자 등급의 관계, `AGY_ADC_AUTH`, `ANTIGRAVITY_EXECUTABLE_DATA_DIR`, 두 제품의 쿼터 공유 여부(공식 근거 없음), Antigravity IDE 1.107.0 재확인.
- 플랫폼:
  - Win11에서 작업표시줄 영역 위에 창을 띄울 때의 **z-order 유지**(작업표시줄을 클릭하면 가려지는지)와 이 방식의 지속 가능성
  - 보조 모니터 작업표시줄, 혼합 DPI, 자동 숨김 UX
  - pnpm 11에서 Electron 42+ 바이너리 설치 절차
  - Azure Artifact Signing Premium 가격(HN 2차 출처뿐)
  - "Mark-of-the-Web이 없으면 SmartScreen 검사 없음"(추론)
  - "Win11 작업표시줄 이동 불가"(2차 출처)
  - 절전·배터리 상태에서의 폴링 정책

**4) 조사 중 발견한 보안 위생 문제(조치 대상)**
- scratch의 `C:\Users\202502\AppData\Local\Temp\claude\widget-v2-research\orca_accounts_raw.json`(5541바이트)에 이메일 형태 문자열 4개가 남아 있다. 토큰 문자열은 없다.
- `~/.claude/.credentials.json` ACL에 `CodexSandboxUsers:(RX)`가 있다.
- Orca 런타임 websocket이 `ws://0.0.0.0:4348`(모든 인터페이스)에 바인딩돼 있다. device token의 mobile scope 허용목록에 `terminal.send`, `accounts.selectClaude`, `accounts.consumeCodexResetCredit` 등이 들어 있다(orca.asar@12375568).
- 기존 설치 폴더에 `Authenticated Users` 수정 권한이 있다.
- Orca PTY 폴백이 신뢰 프롬프트에 `y`를 자동 전송한다(비Windows 경로).

**5) 시각 기준.** Git Bash `TZ=Asia/Seoul date`는 tzdata가 없어 UTC를 출력한다. 이 문서의 시각은 node `Date` 환산값이다. 위젯 코드는 OS 타임존 API를 써야 하고 셸 TZ 출력을 믿으면 안 된다.

**6) 이번 종합에서 생략한 것.** 입력의 Kimi·MiniMax·OpenCode Go 등 Orca의 다른 공급자 키는 범위 밖이라 다루지 않았다. Grok OTEL과 Codex `account/usage/read`(토큰 사용량 요약)는 한도 표시와 무관해 표에서 뺐다.

---
[AI Usage Widget v2 인증·쿼터·스택 사실 시트 / 26.09.15 / 02:03:31]
#AIUsageWidget #멀티계정인증 #쿼터소스 #Electron44 #Orca #약관위험
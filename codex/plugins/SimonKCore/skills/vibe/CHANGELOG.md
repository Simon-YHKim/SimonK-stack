# Changelog

## 2.17.0 - 2026-10-12

- **D-101: GPT 쪽은 `gpt-6-astra` @xhigh 만 쓰고, 보안 생성물 게이트는 Daybreak 로 되돌렸다**(Simon 지시, 토론 없음,
  허브 DECISIONS D-101). 지시 원문은 셋이다.
  - "gpt 6.1 sol은 너무 느려서 빼기로 결정. 기획단계 gpt astra xhigh와 opus 5.5. 단순작업 sonet 5.5"
  - "보안게이트는 데이브레이크로 할려했는데 그게 안돼면 opus 5.5로 하자."
  - "gpt 쪽은 astra 말고는 쓰지마. gpt 를 넣어야한다면 astra xhigh."
- **철회된 레인 다섯**: `gpt-6.1-sol`, `gpt-6-luna`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`. 레인 키는 원장
  호환용으로 `LANES` 에 남는다(`ledger.py` 가 `LANES` 에 없는 레인의 원장 행을 거부한다). 새 `WITHDRAWN_LANES` 로
  계획에 넣으면 `validate_plan` 이 `LANE_WITHDRAWN`(계획기에서는 `ORCA_LANE_WITHDRAWN`)으로 막고 예외 자리는 없다.
  **결함 때문이 아니다.** `gpt-6-luna` 는 D-91 canary 를, `gpt-6.1-sol` 은 D-67·D-98 canary 를 통과했고 제공사
  lifecycle 은 active 그대로다. 소유자가 뺀 것이다. `FORBIDDEN_LANES`(용도 미검증·은퇴, `LANES` 밖)와
  `DEPRECATED_LANES`(제공사 폐기 표시)가 이 경우에 맞지 않아 집합을 따로 뒀다.
- **`gpt-6-astra` 는 항상 xhigh**: 사다리 std = top = xhigh(옛 std high)이고 새 `EFFORT_PINNED` 로 고정했다.
  `allow_off_ladder` 로도 다른 값은 열리지 않는다(`validate_effort`, 계획기에서는 `ORCA_DISPATCH_UNSUPPORTED`, 계획
  검증에서는 `EFFORT_NOT_ALLOWED`). codex 직행 argv(`codex_exec_argv`)는 `gpt-6-astra` @xhigh 만 만들고 철회·폐기
  표시 레인과 `LANES` 밖 GPT id 를 거부한다. `run_codex_exec` 기본 effort 는 ultra → xhigh 다. 원장은 과거 행
  (astra@high·@medium, 철회 레인)을 계속 읽는다. 반증 질문과 무관하게 xhigh 라 codex 쿼터를 더 쓴다. 80% 초과
  강등은 B·A-verify 2순위 `claude-fable-5-1` 로 간다. effort 를 낮추거나 다른 GPT 레인으로 가는 규칙은 없다.
- **목록**: A = `claude-haiku-5-5` → `claude-sonnet-5-5` → `claude-opus-5-5`(오케스트레이터가 Haiku 를 Sonnet 앞에
  두자고 권했고 Simon 이 반대하지 않았다). C-realtime = `grok-4.6` → `claude-opus-5-5` → `gpt-6-astra`. C-platform =
  `gemini-3.8-flash` → `claude-opus-5-5` → `gpt-6-astra`. B·A-verify·D·코딩은 그대로다. 코디네이터 =
  `gpt-6-astra` @xhigh. A 1순위 산출물 제약(`OUTPUT_RULES`)은 `claude-haiku-5-5` 로 합쳤고 `gpt-6-luna` 규칙은 뺐다.
  - 부작용 둘. A 클래스가 전부 claude 라 claude 가 한도에 닿으면 A 작업은 codex 로 넘어가지 않고 멈춘다. 코디네이터가
    인가 게이트·B 1순위와 같은 모델이라 코딩 라운드와 대부분의 B 라운드에서 `coordinator_conflict()` 가 참이다
    (경고이며 디스패치를 막지 않는다. 규칙은 바꾸지 않았다).
- **보안 생성물 게이트 = `gpt-daybreak-blue-latest` @xhigh**(D-98 의 `gpt-6.1-sol` 이전을 같은 날 뒤집었다).
  제공사의 deprecated 표시, 레지스트리의 `lifecycle: deprecated`, 중앙 계획기의 `MODEL_NOT_ACTIVE` 는 건드리지
  않았다. 바뀐 가드는 `LANE_DEPRECATED` 하나다: 새 `DEPRECATED_LANE_PINS` 의 한 자리, 곧 고정 공정
  `security-artifact-gate` 이고 그 고정 배정이 지금도 이 별칭이며 effort 가 고정값 xhigh(또는 미지정)일 때만
  통과시킨다. 우선순위 목록·코딩·다른 공정·재시도·다른 effort 는 그대로 막힌다. G1·G1_SEC_SAME_MODEL·쿼터/과금
  게이트는 그대로다.
  - **알려진 한계**: packaged registry 를 쓰는 중앙 계획기 경로에서는 게이트 후보가 `MODEL_NOT_ACTIVE` 로 계속
    막힌다. 게이트 자리는 고정이지 동작이 아니다(D-98 이 풀려던 상태로 돌아갔다).
  - `references/security-artifact-gate.md`: 고정 레인과 이유를 Daybreak 로 고쳤다. 루브릭·출력 형식·fail-closed
    규칙은 그대로다. "Before each run" 을 더했다: 코디네이터가 `~/.codex/models_cache.json` 에 별칭이 은퇴·upgrade
    표시 없이 남아 있는지 확인하고, 없거나 게이트 출력이 비거나 차단되면 게이트는 통과가 아니라 실패다(스크립트가
    이 확인을 하지는 않는다). 재승격 절은 대체 규칙으로 바꿨다: 더 새로운 cyber 모델은 같은 canary 와 1단 기록
    뒤에만 별칭을 대체한다. 두 canary 기록(D-98 `gpt-6.1-sol`, D-101 Daybreak)을 모두 남겼다.
  - **미결(Simon 판정 필요)**: Simon 이 말한 폴백 `claude-opus-5-5` 는 구현하지 않았다. 코딩이
    `claude-opus-5-5` 라 같은 모델이 자기 산출물을 검사하게 되어 G1 과 충돌한다. 선택지는 (a) Opus 폴백 + 그
    경우에만 G1 완화(Simon 이 말한 쪽), (b) `gpt-6-astra` 가 두 보안 게이트를 맡고 그 경우에만 G1_SEC_SAME_MODEL
    완화. 판정 전에는 별칭이 없거나 출력이 비거나 차단되면 게이트 실패이고 코딩 라운드가 멈춘다.
  - canary(오케스트레이터가 구현 전에 실행, 2026-10-12 15:19~15:20 KST, Orca run `run_b08adccb4ec8`, dispatch
    `ctx_41243c1a0d26`, 읽기 전용 워커 1개, 도구 금지): `launch.requested` == `launch.effective`
    (`gpt-daybreak-blue-latest`, xhigh), Codex rollout(originator `codex-tui`, CLI 0.162.1) `turn_context` 가 같은 값.
    D-98 과 같은 결함 4개 샘플에 `GATE: BLOCK` + CWE-89·78·22·502 를 정확히 보고했고 안전한 함수 2개에는 발견을
    내지 않았다. 출력은 비거나 차단되지 않았고 약 30초가 걸렸다. 자기보고 모델명 `GPT-5` 는 틀렸다. 워커 정지·터미널
    종료 확인. 심은 샘플 1건이며 별칭은 예고 없이 사라질 수 있다.
  - **canary 를 돌리지 않은 것**: 코디네이터로서의 `gpt-6-astra`, A 클래스 순서 변경. 근거는 앞선 것뿐이다
    (Haiku 5.5 는 D-99 의 정답이 정해진 A 과제 3개, Sonnet 5.5 는 D-91 canary).
- **shadow task-fit 정책 `2026-10-12-shadow.2`**(`checked_at`·`valid_until` 그대로): GPT 행은 `gpt-6-astra` 의 xhigh
  뿐이다. `gpt-6.1-sol`·`gpt-6-sol`·`gpt-6-luna` 행을 네 프로필에서 모두 뺐다. PLAN_ARCHITECTURE = `claude-opus-5-5`
  (high·xhigh)·`gpt-6-astra`(xhigh) 0순위. CODE_COMPLEX = `claude-opus-5-5` medium 0순위·high/xhigh 1순위,
  `gpt-6-astra` xhigh 0순위. CODE_SIMPLE = `claude-haiku-5-5`(low·medium) 0순위, `claude-sonnet-5-5`(medium) 1순위,
  `claude-opus-5-5`(medium) 2순위. WRITING = `claude-opus-5-5`(medium·high) 0순위. Sonnet 5.5 가 CODE_SIMPLE 로
  돌아온 것은 지시 때문이지 D-90 재진입 조건이 충족돼서가 아니다(Artificial Analysis 는 2026-10-12 11:48 KST 까지
  재측정을 올리지 않았다). 다른 세 프로필은 Sonnet 5.5 를 계속 뺀다. 출처 키 `anthropic_haiku`·
  `anthropic_haiku_docs` 를 더했고 쓰지 않게 된 키는 기록으로 남겼다. SKILL.md 의 권고 표도 같이 고쳤다.
- registry `2026-10-12.3`(`checked_at`·`data_as_of`·모델 값 그대로): `legacy_lane_migration` 15건은 `pending-*` 6,
  `held-*` 5, `keep-*` 4 다. 철회 다섯 건은 `held-withdrawn-by-owner` 이고 후보는 일이 간 곳이다
  (`gpt-6.1-sol`·`gpt-5.6-sol`·`gpt-5.6-terra` → `gpt-6-astra`, `gpt-6-luna`·`gpt-5.6-luna` → `claude-haiku-5-5`).
  재개 조건은 Simon 의 명시 지시나 별도 결정 기록, 그리고 같은 canary 의 재통과다. `gpt-daybreak-blue-latest` 는
  후보 자기 자신, `keep-security-pin-resolve-per-run` 으로 돌아갔다. `gpt-5.6-terra` 의 등급 평가는 대상이
  철회돼 더 진행하지 않는다.
- `eval/probes.json`: 문제 18개 중 17개에서 철회 레인을 빼고 그 자리에 `gpt-6-astra` 를 한 번 넣었다(codex 후보는
  astra 하나). `adversarial_eval.load_probes` 는 철회·폐기 표시 레인이 든 문제를 거부한다. `VENDOR_OF` 의 키는 평가
  원장의 과거 행 때문에 남는다. `references/legacy-routing.md` 는 `sync_skill_table.py` 로 다시 만들었다(레인 표의
  기동 칸이 철회·게이트 전용을 적는다).
- 테스트 픽스처: guarded Orca 어댑터·준비·wave 테스트의 공용 픽스처 레인을 철회된 `gpt-5.6-luna` 에서
  `claude-haiku-5-5` @low 로 옮겼다(`test_execute_orca.py`, `tests/test_prepare_state.py`,
  `tests/test_prepare_refresh.py`, `multi-terminal-dispatcher` 의 `test_dispatch_wave.py`). 어댑터는 claude·codex
  표면을 똑같이 다루고, codex 표면은 `gpt-6-astra` @xhigh 와 Daybreak 게이트 테스트가 계속 본다.
- **범위 밖(그대로 둔 것)**: Orca 밖 경로(host·direct CLI)의 후보 선택은 호스트가 준 runtime 후보와 레지스트리
  (제공사 사실)로만 고른다. "GPT 는 astra 만" 은 그 경로에 걸려 있지 않다. 걸려면 계획기에 새 가드가 필요하고
  Codex 호스트 세션에 영향이 있어 별도 결정으로 남겼다.
- 검증: scripts 단위 테스트 436 OK(434→436), `tests/` 157 OK, selftest PASS 265 · FAIL 0(215→265),
  `validate_skill.py` 0 errors / 0 warnings, `sync_skill_table.py --check` 동기 OK, skill CI 141 clean,
  `multi-terminal-dispatcher` 25 OK(skipped 3). 이 변경에서 모델 호출·Orca 명령·worker-start·설치는 0회다(위
  canary 는 오케스트레이터가 구현 전에 돌린 것).

## 2.16.0 - 2026-10-12

- **D-98: 보안 생성물 게이트 레인을 `gpt-6.1-sol` @xhigh 로 옮겼다**(허브 토론 `dbt-261012-124530`, quick,
  PROVISIONAL 3/4, 심판 확신도 91). OpenAI API 문서가 별칭 `gpt-daybreak-blue-latest` 를 deprecated 로 표시했다
  (종료일·대체 ID 미공지). 이 계정 Codex 카탈로그는 아직 그 별칭을 list·cyber 로 싣고 은퇴 표시가 없지만 다른
  cyber 모델도 없다. 레지스트리는 2.15.7 부터 `lifecycle: deprecated` 이고 중앙 계획기는 그 후보를
  `MODEL_NOT_ACTIVE` 로 막는데, 레거시 레인 표만 폐기된 별칭을 가리키고 있었다.
  - `routing.py`: `security-artifact-gate` 고정 레인 `("gpt-6.1-sol", "xhigh")`. 지킨 것은 G1(코딩은 claude 전용,
    게이트는 codex)과 G1_SEC_SAME_MODEL(생성물 게이트 `gpt-6.1-sol` 과 인가 게이트 `gpt-6-astra` 는 다른 모델)이다.
    잃은 것은 cyber 전용성이고, 방어 루브릭으로 보완하지만 동등하다고 증명된 것은 아니다.
  - 옛 키 `gpt-daybreak-blue-latest` 는 원장 호환용으로 `LANES` 에 남는다(`ledger.py` 가 `LANES` 에 없는 레인의
    원장 행을 거부한다). 어떤 우선순위 목록·고정 공정에도 없고, 새 `DEPRECATED_LANES` 로 계획에 넣으면
    `validate_plan` 이 `LANE_DEPRECATED`(계획기에서는 `ORCA_LANE_DEPRECATED`)로 막는다. 레지스트리의 deprecated 와
    `MODEL_NOT_ACTIVE` 는 그대로다. 게이트 산출물 제약(`OUTPUT_RULES`)은 게이트와 함께 `gpt-6.1-sol` 로 옮겼다.
  - 새 참고 문서 `references/security-artifact-gate.md`: 목적, 고정 레인과 이유, 루브릭(CWE-89·78·22·502·798·327·918,
    인증·인가 우회, 안전하지 않은 파일·권한 처리), 출력 형식(첫 줄 `GATE: BLOCK` 또는 `GATE: PASS`, 이어서 발견마다
    한 줄 `CWE-<n> | <location> | <reason>`), fail-closed 규칙(빈 출력, 제공사 차단·거절, 첫 줄 누락, 모호한 판정은
    PASS 가 아니라 FAIL), G1(게이트는 자기 벤더의 산출물을 채점하지 않는다), 재승격 규칙(폐기된 별칭이 아닌 cyber
    모델이 `~/.codex/models_cache.json` 에 나타나면 같은 canary 를 돌리고, 통과하면 1단 DECISIONS 기록과 함께 옮긴다.
    자동 승격 없음), canary 기록.
  - canary(오케스트레이터가 구현 전에 실행, 2026-10-12 12:53~12:55 KST, Orca run `run_8f7a27febc38`, dispatch
    `ctx_ff39c4a979ba`, 읽기 전용 워커 1개, 도구 금지): `launch.requested` == `launch.effective`(`gpt-6.1-sol`, xhigh),
    Codex rollout `turn_context` 가 `gpt-6.1-sol`/xhigh. 결함 4개와 안전한 함수 2개를 심은 Python 생성물에
    `GATE: BLOCK` + CWE-89·78·22·502 를 정확히 보고했고 안전한 함수에는 발견을 내지 않았다. 출력은 비거나 차단되지
    않았다. 자기보고 모델명 `gpt-6` 은 틀렸다(자기보고는 근거가 아니다). 워커 정지·터미널 종료 확인.
  - 한계와 부작용. 심은 샘플 1건이며 루브릭 9개 항목 중 4개만 봤다. fail-closed 규칙은 게이트 출력을 읽는 쪽
    (호스트·코디네이터)이 적용하는 문서 규칙이고 테스트는 문서와 레인을 고정한다. 게이트 출력을 파싱하는 코드는
    없다. 생성물 게이트와 코디네이터가 같은 `gpt-6.1-sol` 이 되어 코딩 라운드마다 `coordinator_conflict()` 가
    참이다(경고이며 디스패치를 막지 않는다). 코디네이터는 바꾸지 않았다.
- **D-99: `claude-haiku-5-5` 를 등록하고 A 클래스의 Claude 쪽 첫 폴백으로 넣었다**(허브 토론 `dbt-261012-124540`,
  quick, PROVISIONAL 3/4, 심판 확신도 82, 조건부 채택의 조건 통과). A 클래스는 `gpt-6-luna` → `claude-haiku-5-5` →
  `claude-sonnet-5-5` → `claude-opus-5-5` 다. 1순위는 그대로이고 Sonnet 5.5 도 남는다. B·A-verify·D·코딩 목록과
  `task-fit-policy.json` 은 바꾸지 않았다.
  - 등록 사실은 2026-10-12 13:01:22~13:01:28 KST 에 공식 페이지 7개(Haiku 5.5 개요·발표문, 가격표, 폐기 페이지,
    모델 개요, effort, Claude Code model-config)를 모델 호출 없이 HTTPS 로 읽어 확인했다(전부 첫 요청 HTTP 200):
    2026-10-07 출시, Active, 은퇴 2027-10-07 이후, 1M 컨텍스트, 128K 출력, effort low~max(API·Claude Code 기본
    medium), adaptive thinking, Claude Code 2.1.293 이상. `haiku` 별칭은 Anthropic API 에서만 Haiku 5.5 라서
    별칭으로 등록하되 레인은 정식 ID 를 보낸다(해석 근거 없는 별칭 요청은 `ALIAS_RESOLUTION_UNVERIFIED`).
  - 가격은 프롬프트 길이로 갈린다. 10만 토큰 이하: 입력 $0.10, 캐시 읽기 $0.01, 출력 $0.50. 10만 토큰 초과: 입력
    $0.50, 캐시 읽기 $0.05, 출력 $2.50. `pricing.tiers` 의 `above_input_tokens: 100000` 으로 담았다. 스키마가 담지
    못한 것 둘은 `pricing.note` 에 적었다: 캐시 쓰기가 구간마다 둘(5분 $0.125/$0.625, 1시간 $0.20/$1)이라
    `cache_write` 는 null 이고, 프롬프트 길이가 캐시 읽기·쓰기를 포함한 모든 입력 토큰이며 요청마다 따로 판정된다.
  - 새 Orca 레인 `claude-haiku-5-5`(flag, Orca low~max, 사다리 std low / top medium, high·xhigh·max 는 off-ladder
    로만, claude 일반 weekly 쿼터). 산출물 제약은 luna 와 같은 싼 레인 규율이다(정형 변환·카운트·분류, 우열 판단
    금지). 2순위가 바뀌어 A 공정의 탐색 슬롯과 표의 2순위 칸은 이제 Haiku 를 본다.
  - canary(같은 Orca run `run_8f7a27febc38`, dispatch `ctx_cd78cf210447`, 12:53~12:54 KST, 읽기 전용 워커 1개, 도구
    금지): `launch.requested` == `launch.effective`(`claude-haiku-5-5`, low), 세션 기록의 두 assistant 메시지 모두
    `message.model` `claude-haiku-5-5`(entrypoint `cli`). 정답이 스크립트로 정해진 A 클래스 과제 3개가 전부 맞았다:
    CSV→JSON 변환 완전 일치, 스키마 위반 id `2,3,5,6,7`, 로그 24줄 레벨 집계 `ERROR=5 WARN=7 INFO=9 DEBUG=3`.
    워커 정지·터미널 종료 확인.
  - 한계. 선두 레인이 아니다. 작은 과제 3개·effort 1개라 큰 입력과 10만 토큰 초과 입력의 근거가 아니다. 쿼터
    절감은 측정하지 않았다(같은 구독에서 Haiku 실패 뒤 Sonnet 을 부르면 총 쿼터가 늘 수 있다). 선두 승격이나
    Sonnet 5.5 제외는 별도 비교 근거가 필요하다.
- registry `2026-10-12.2`: `legacy_lane_migration` 의 `gpt-daybreak-blue-latest` 를
  `keep-security-pin-resolve-per-run` 에서 후보 `gpt-6.1-sol`, `pending-transport-and-certificate` 로 바꾸고,
  `claude-haiku-5-5` 를 자기 후보 `pending-transport-and-certificate` 로 더했다(15건: `pending-*` 12, `keep-*` 3).
  모델 19개(Haiku 5.5 추가), 출처 2개 추가. `checked_at`·`data_as_of` 는 그대로다. Haiku 5.5 를 읽은 시각은
  `checked_at`(가장 이른 근거 11:43:08)보다 늦다. 두 레인 모두 **등록만 됐다**: Orca 런치 계정/과금 인증서
  전까지 동작 레인이 아니며 $0 게이트·G5·런치 인증서가 똑같이 걸린다.
- `adversarial_eval.VENDOR_OF` 에 `claude-haiku-5-5` 를 더했고 `eval/probes.json` 의 A 클래스 문제 11개에 넣었다
  (B 문제 7개에는 넣지 않았다). `references/legacy-routing.md` 는 `sync_skill_table.py` 로 다시 만들었다.
  `model-catalog-map.md` 의 CLI 이름표에서 `claude-haiku-5-5` 행을 뺐다(등록된 ID 는 CLI 전용 이름이 아니다).
- 검증: scripts 단위 테스트 434 OK(426→434), `tests/` 157 OK, selftest PASS 215 · FAIL 0(196→215),
  `validate_skill.py` 0 errors / 0 warnings, `sync_skill_table.py --check` 동기 OK. 이 변경에서 모델 호출·Orca
  명령·worker-start·설치는 0회다(위 canary 두 건은 오케스트레이터가 구현 전에 돌린 것).

## 2.15.7 - 2026-10-12

- 모델 레지스트리 사실을 다시 확인했다(허브 PROTOCOL §35.8 1단, 승인된 절차 반복). 2.15.6 의 사실은
  2026-10-13 12:45:26 KST 에 `REGISTRY_STALE` 이 될 예정이었다. 레지스트리 출처 28개와 task-fit 출처 9개,
  폐기 페이지·모델 목록 6개를 모델 호출 없이 HTTPS 로 다시 읽었고(전부 첫 요청 HTTP 200, 10-06 과 같은 브라우저형
  요청 헤더), 로컬 Codex·Grok·agy·Claude CLI 카탈로그와 메타데이터 전용 `runtime_collect.py` 와 대조했다.
  `model_watch.py scan --force` 는 상태 파일 사본으로 돌려 원본은 읽기만 했다(새 후보 0·오류 0).
  프롬프트·Orca 워커·설치는 0회다.
- **제공사 사실 3개가 바뀌어 레지스트리 값을 고쳤다.** 등록 모델 18개의 사실 필드 232개(10-06 과 같은 정의)는
  고치기 전 일치 227·불일치 3·확인불가 2 였고, 고친 뒤 일치 230·불일치 0·확인불가 2 다.
  - `claude-sonnet-5-5` 의 `pricing.cached_input` 0.2 → 0.1: Anthropic 이 2026-10-07 에 Sonnet 5.5 캐시 읽기를
    $0.20 → $0.10/MTok 으로 내렸다.
  - `gpt-daybreak-blue-latest` 의 `lifecycle` active → deprecated: 모델 페이지에 Deprecated 배지와 "This alias is
    deprecated, please use the latest cyber model available to you" 가 붙었고 모델 목록에서 빠졌다. 종료 일자와
    대체 ID 는 공지되지 않았다. 이제 `constrain_runtime` 이 이 alias 후보를 `MODEL_NOT_ACTIVE` 로 막는다.
  - `gemini-3.8-flash` 의 `source_updated_at` 2026-09-23 → 2026-10-09(latest-model 페이지의 Last updated).

  확인불가 2개는 `gpt-5.6-terra`·`gpt-5.6-luna` 의 장문 cached_input 으로 10-06 과 같다. 근거와 표는
  `references/model-catalog-map.md` 에 있다.
- `checked_at` 은 실제로 쓴 근거 중 가장 이른 시각인 Grok 모델 캐시 수신 2026-10-12 11:43:08 KST 다.
  사실은 2026-10-19 11:43:08 KST 에 `REGISTRY_STALE` 이 된다. shadow task-fit 정책은 2026-10-12 11:48:51 ~
  2026-10-19 11:48:51 KST 에 유효하다. 레지스트리 version 은 2026-10-12.1, 정책은 2026-10-12-shadow.1 이다.
- 관측만 기록했다(등록·레인·라우팅 변경 없음). 새 GA 모델 Claude Haiku 5.5(`claude-haiku-5-5`, 2026-10-07 출시,
  effort low~max, 프롬프트 10만 토큰 기준 가격 구간)와 이미지 모델 `gemini-nano-banana-2.1`(10-06)이 나왔다.
  미등록 `gemini-3.7-flash`·`gemini-3.5-flash` 는 폐기됐고(10-08), Haiku 4.5 는 Legacy 가 됐으며(은퇴 하한 10-15
  그대로), Codex 카탈로그의 `gpt-5.5` 에 10-14 은퇴 표시가 붙었고, `gpt-6.1-sol` 에 Ultrafast 모드가 생겼다.
  Gemini 4 Argon 은 개발자 API 에 없고 Grok 5 는 xAI 문서에 없다. Codex 0.162.1·agy 1.3.3·Claude Code 2.1.296 으로
  올라갔다. Artificial Analysis 는 Sonnet 5.5 재측정을 아직 올리지 않아 D-90 은 그대로다.
- 바꾸지 않은 것: 레인 라우팅·우선순위·`legacy_lane_migration`(Daybreak 의 `keep-security-pin-resolve-per-run`
  포함)·D-90/D-91 노트·task-fit 순위. 폐기된 Daybreak alias 를 쓰는 보안 레인을 어디로 옮길지와 Haiku 5.5 등록
  여부는 별도 결정이 필요하다.
- `test_model_registry.py` 의 기간 테스트는 이번 재확인 창(하한 2026-10-12 11:00, 만료 2026-10-19 11:00 이후)을 본다.
  바뀐 사실 3개와 폐기된 alias 가 `MODEL_NOT_ACTIVE` 로 막히는지 보는 테스트 1개를 더했다.

## 2.15.6 - 2026-10-06

- 모델 레지스트리 사실을 다시 확인했다(허브 PROTOCOL §35.8 1단, 승인된 절차 반복). 2.15.3 의 사실은
  2026-10-12 14:17:43 KST 에 `REGISTRY_STALE` 이 될 예정이었다. 레지스트리 출처 28개와 task-fit 출처 9개,
  폐기 페이지·모델 목록 6개를 모델 호출 없이 HTTPS 로 다시 읽었고(전부 첫 요청 HTTP 200), 로컬 Codex·Grok·agy·
  Claude CLI 카탈로그와 메타데이터 전용 `runtime_collect.py`, model-watch 상태 파일(읽기만)과 대조했다.
  프롬프트·Orca 워커·설치는 0회다. 등록 모델 18개의 사실 필드 232개 중 230개가 일치하고 불일치는 0이다.
  확인불가 2개는 `gpt-5.6-terra`·`gpt-5.6-luna` 의 장문 cached_input 으로, 제공사 페이지에 값이 없어 같은 문구의
  `gpt-5.6-sol` 로 유추해 유지했다. 필드 수 정의(메타데이터 5종 제외, null·빈 값 34개는 규약대로 일치)는
  `references/model-catalog-map.md` 에 적었다. 10-05 의 162필드는 정의가 남아 있지 않아 바로 비교하지 않는다.
  제공사 사실은 바뀌지 않았고 제거·개명된 모델도, 10-05 이후 API GA 신규 모델도 없다.
- `checked_at` 은 실제로 쓴 근거 중 가장 이른 시각인 Grok 모델 캐시 수신 2026-10-06 12:45:26 KST 다.
  사실은 2026-10-13 12:45:26 KST 에 `REGISTRY_STALE` 이 된다. shadow task-fit 정책은 2026-10-06 12:50:44 ~
  2026-10-13 12:50:44 KST 에 유효하다. 레지스트리 version 은 2026-10-06.1, 정책은 2026-10-06-shadow.1 이다.
- 관측만 기록했다: Codex 카탈로그에서 미등록 `gpt-5.5` 가 숨김이 됐다(대응표 메모만 고침). agy 1.2.17·Claude Code
  2.1.290 으로 올라갔다. Haiku 5.5 는 여전히 GA 전이고 미등록 Haiku 4.5 의 은퇴 하한(10-15)이 9일 남았다.
  레인 라우팅·우선순위·`legacy_lane_migration`·D-90/D-91 노트·task-fit 순위는 바꾸지 않았다.
- `test_model_registry.py` 의 기간 테스트는 이번 재확인 창(하한 2026-10-06 12:00, 만료 2026-10-13 12:00 이후)을 본다.

## 2.15.5 - 2026-10-05

- Simon 지시("5.5로 전환해. 최신모델을써야지 왜 구모델을씀?"): A 클래스(bulk-transform·inventory-schema·
  disk-grep·log-history-triage)를 현행 세대 레인으로 옮겼다. 순서는 `gpt-6-luna` → `claude-sonnet-5-5` →
  `claude-opus-5-5` 다. 이전 1·2순위였던 `gpt-5.6-luna`·`claude-sonnet-5` 는 같은 세대가 아니었다.
- D-67 과 같은 ADD_ALONGSIDE_KEEP_LEGACY 패턴이다. 옛 키 옆에 새 Orca 레인 두 개를 넣었다.
  - `claude-sonnet-5-5`: flag, Orca low~max(claude 카탈로그에 없는 정식 id), 정책 std medium(Claude Code·앱 기본값) /
    top high(Artificial Analysis 가 Sonnet 5.5 의 가장 경쟁력 있는 설정으로 보는 값). xhigh·max 는 토큰 폭증
    (max 에서 작업당 출력 약 193k 토큰) 때문에 정책 사다리 밖이라 off-ladder 로만 열린다. 쿼터는 claude 일반 weekly.
  - `gpt-6-luna`: flag, Orca minimal~xhigh(codex 미등록 모델 폴백, max·ultra 거부), 정책 low/medium(5.6-luna 와 같음).
  - 옛 `gpt-5.6-luna`·`claude-sonnet-5` 는 원장 호환용(우선순위 밖)으로만 남긴다. `ledger.py` 가 `LANES` 에 없는
    레인의 원장 행을 거부하기 때문이다. A 1순위 산출물 제약(`OUTPUT_RULES`)도 `gpt-6-luna` 로 옮겼다.
- registry(2026-10-05.3): `claude-sonnet-5` → `claude-sonnet-5-5` 를 `held-until-remeasure` 에서
  `pending-transport-and-canary` 로 되돌렸다. D-90 소수의견대로 이 레인에 대한 Simon 의 명시 지시가 보류보다 앞선다.
  새 레인 `claude-sonnet-5-5`·`gpt-6-luna` 를 자기 후보 항목으로 추가했다. `gpt-5.6-luna` 는 `pending-transport-and-canary`
  그대로다. 제공사 사실·`checked_at` 은 바꾸지 않았다. `references/task-fit-policy.json`(D-90 의 Sonnet 5.5
  shadow 제외)은 별개의 비용 프런티어 결정이라 바꾸지 않았다.
- **등록이지 동작이 아니다.** 두 레인은 읽기 전용 canary(`launch.requested` ↔ `launch.effective`)와 Orca 런치
  계정/과금 인증서 전이다. planner 는 이제 두 모델을 `ORCA_UNREGISTERED_PROCESS_OR_MODEL` 로 막지 않고 G5 에서 멈춘다.
  모델 포함·API 폴백 OFF·G5·런치 인증서 게이트가 옛 레인과 똑같이 걸린다는 테스트를 붙였다
  (`test_orchestrate.py` 2건, `test_execute_orca.py` 1건, `test_model_registry.py` 1건, selftest 8건).
  검증: scripts 단위 테스트 425 OK(421→425), `tests/` 157 OK, selftest PASS 196 · FAIL 0(188→196).
- `adversarial_eval.VENDOR_OF` 와 `eval/probes.json` 에 새 레인을 옛 레인 옆에 더했다(12개 문제에 `gpt-6-luna`).
  `references/legacy-routing.md` 는 `sync_skill_table.py` 로 다시 만들었다. 모델 호출·Orca 명령·worker-start 는 0회다.
- D-91 읽기 전용 Orca canary 를 통과했다(2026-10-05 20:47~20:53 KST, run `run_0a369252175f`, 레인마다 워커 1개).
  `claude-sonnet-5-5`@medium: requested == effective, argv `--model claude-sonnet-5-5 --effort medium`, 세션 기록 model
  `claude-sonnet-5-5`(자기보고 `claude-fable-5-1` 은 틀림). `gpt-6-luna`@low: requested == effective, argv
  `-m gpt-6-luna -c model_reasoning_effort=low`, rollout `turn_context` `gpt-6-luna`/low(자기보고 `gpt-6.1-sol` 은 틀림).
  워커 정지·PID 소멸 확인. 그래서 A 클래스 이전 4건을 `pending-transport-and-certificate` 로 바꿨다(registry 2026-10-05.4).
  여전히 Orca 런치 계정/과금 인증서 전이라 동작 레인이 아니다. `scripts/preview-vibe-candidate.ps1` 기본 모델도 `claude-sonnet-5-5` 다.

## 2.15.4 - 2026-10-05

- 허브 D-90(4벤더 quick 토론 FINAL 4/4, 심판 확신도 76): `claude-sonnet-5-5` 를 shadow task-fit 정책의
  네 프로필(CODE_SIMPLE·WRITING·CODE_COMPLEX·PLAN_ARCHITECTURE)에서 모두 뺐다. Artificial Analysis(독립 측정)는
  Sonnet 5.5 가 모든 effort 에서 지능 대비 작업당 비용 Pareto 프런티어 밖이고, low·medium·high 가 GPT-6 Sol
  high·xhigh·max 보다 적은 토큰으로 낮은 성능이라고 적는다. 구독 환경에서는 작업당 토큰이 실제 비용(쿼터)이다.
- 새 순위: CODE_SIMPLE 0순위 `gpt-6.1-sol`·`gpt-6-sol`(low·medium), 2순위 `gpt-6-luna` 와 `claude-opus-5-5` medium.
  WRITING 0순위 `claude-opus-5-5`. 나머지 상대 순서는 그대로다. 정책 version 2026-10-05-shadow.2.
- registry `legacy_lane_migration` 의 `claude-sonnet-5` → `claude-sonnet-5-5` 는 `held-until-remeasure` 로
  멈췄다(registry version 2026-10-05.2). 재개 조건은 AA 재측정에서 작업당 토큰이 Sonnet 5 이하이거나 A 클래스
  canary 가 Opus 폴백보다 쿼터를 덜 쓰는 것이다. 옛 `claude-sonnet-5` A 클래스 폴백 레인(D-28)은 그대로다.
- 재진입은 AA 공개판 재측정 뒤, 같은 작업 짝 평가에서 품질을 충족하고 대체 모델보다 쿼터 효율이 좋을 때만
  그 프로필에 한해 허용한다(정책 노트). 먼저 볼 자리는 CODE_COMPLEX high 다.

## 2.15.3 - 2026-10-05

- 모델 레지스트리 사실을 다시 확인했다(허브 PROTOCOL §35.8 1단, 승인된 절차 반복). 2.15.2 의 사실은
  2026-10-11 21:46:09 KST 에 `REGISTRY_STALE` 이 될 예정이었다. 레지스트리 출처 28개와 task-fit 출처 9개,
  폐기 페이지·모델 목록 6개를 모델 호출 없이 HTTPS 로 다시 읽었고(전부 첫 요청 HTTP 200), 로컬 Codex·Grok·agy·
  Claude CLI 카탈로그와 메타데이터 전용 `runtime_collect.py`, `model_watch.py status` 와 대조했다. 프롬프트·Orca
  워커·설치는 0회다. 등록 모델 18개의 162필드 중 160개가 일치하고 불일치는 0이다. 확인불가 2개는
  `gpt-5.6-terra`·`gpt-5.6-luna` 의 장문 cached_input 으로, 제공사 페이지에 값이 없어 같은 문구의 `gpt-5.6-sol`
  로 유추해 유지했다. 제공사 사실은 바뀌지 않았고 제거·개명된 모델도, 10-04 이후 API GA 신규 모델도 없다.
- `checked_at` 은 실제로 쓴 근거 중 가장 이른 시각인 Codex 모델 캐시 수신 2026-10-05 14:17:43 KST 다.
  사실은 2026-10-12 14:17:43 KST 에 `REGISTRY_STALE` 이 된다. shadow task-fit 정책은 2026-10-05 14:20:41 ~
  2026-10-12 14:20:41 KST 에 유효하다. 레지스트리 version 은 2026-10-05.1, 정책은 2026-10-05-shadow.1 이다.
- 관측만 기록했다: Haiku 5.5 는 발표만 됐고 GA 전이다. `gpt-5.6-sol` 할인가의 기한(11-21)은 스키마에 필드가 없다.
  AA 의 Sonnet 5.5 비용 프런티어 평가는 CODE_SIMPLE 근거와 긴장이 있어 다음 정책 검토에서 본다. 레인 라우팅·
  우선순위·D-67 `legacy_lane_migration` 상태는 바꾸지 않았다.
- `test_model_registry.py` 의 기간 테스트는 이번 재확인 창(하한 2026-10-05 14:00, 만료 2026-10-12 14:00 이후)을 본다.

## 2.15.2 - 2026-10-04

- 모델 레지스트리 사실을 같은 날 두 번째로 갱신했다(허브 PROTOCOL §35.8 1단, 승인된 절차 반복).
  2.14.1 과 같은 절차로 레지스트리 출처 28개와 task-fit 출처 9개를 모델 호출 없이 HTTPS 로 다시
  읽었고(전부 HTTP 200, openai.com Astra 페이지는 첫 요청 403 뒤 브라우저 요청 헤더로 재시도),
  로컬 Codex·Grok·agy·Claude CLI 카탈로그, 메타데이터 전용 `runtime_collect.py`(Codex app-server
  `model/list`, Grok ACP 과금), OpenAI·Google 폐기 페이지, `model_watch.py status` 와 대조했다.
  프롬프트·Orca 워커·설치는 0회다. 모델 ID·API effort·컨텍스트·가격·장문 구간·은퇴 일자·Daybreak 대상·
  Claude Code 주석이 모두 그대로라 제공사 사실은 바뀌지 않았고, 제거·개명된 모델도 없다.
- `checked_at` 은 실제로 쓴 근거 중 가장 이른 시각인 Codex 모델 캐시 수신 2026-10-04 21:46:09 KST 다.
  그래서 사실은 2026-10-11 13:05:20 KST 대신 2026-10-11 21:46:09 KST 에 `REGISTRY_STALE` 이 된다.
  shadow task-fit 정책은 2026-10-04 21:52:28 ~ 2026-10-11 21:52:28 KST 에 유효하고, 인용 주장과
  순위는 그대로다. 레지스트리 version 은 2026-10-04.4, 정책은 2026-10-04-shadow.2 다.
- Grok 모델 캐시는 처음 볼 때 `fetched_at` 이 20:31:49 KST 였지만 메타데이터만 읽었고,
  `grok --no-auto-update models` 가 같은 etag 로 다시 받아 21:49:58 이 된 사본으로 내용을 대조했다.
  `references/model-catalog-map.md` 의 반복 절차에 이 순서를 적었다.
- 관측만 기록했다: CLI 버전은 1차와 같다(Codex 0.160.0, grok 1.0.46, agy 1.2.16, Claude Code 2.1.289).
  Gemini 4 Argon 은 여전히 신뢰 사용자 대상 단계 배포라 등록하지 않았다. xAI `grok-4.5` 페이지의 API
  별칭 `grok-4.5-latest`·`grok-build-latest` 는 레지스트리가 제공사 별칭을 모으지 않으므로 넣지 않았다.
  레인 라우팅·우선순위·D-67 `legacy_lane_migration` 상태는 바꾸지 않았다.
- `test_model_registry.py` 의 기간 테스트는 2차 재확인 창(하한 2026-10-04 21:00, 만료 2026-10-11 21:00
  이후)을 본다. 오프라인 테스트만 실행했다.

## 2.15.1 - 2026-10-04

- 허브 D-76 1단계: 배포 트리에서 이 PC 절대경로를 뺐다. `scripts/ledger.py` 허브,
  `make_intake.py`·`make_decision_sheet.py` 기본 출력은 `$SIMONK_PROJECT_DIR`(없으면 홈 폴더)
  기준이다. 이 PC는 사용자 환경변수가 이미 같은 값이라 동작이 그대로다. Orca 저장소 목록이 없을 때
  `make_intake.py`는 고정 2nd-B 클론 대신 현재 폴더를 보여 준다. `adversarial_eval.py --repo` 기본값은
  현재 폴더다.
- `references/orchestration.md`의 `/qa` 계약 참조를 `<qa-skill-dir>/references/detail.md`로 바꿨다.
  플러그인 경로 감사가 이것을 vibe 자신의 `references/detail.md`로 읽어 미해결로 냈다.

## 2.15.0 - 2026-10-04

- D-74(Simon 결정): 모든 벤더(Claude·Codex·Grok·Antigravity·Grok Bot)를 포함 사용량으로만 판단한다.
  막는 조건은 사용량 근거 없음·오래됨·85% 이상(`INCLUDED_USAGE_CEILING`), rate limit·spend control
  도달(`USAGE_LIMIT_REACHED`, 최상위·이름 붙은 버킷 모두), API 폴백 미차단, 모델 미포함이다.
- 크레딧 잔액·`has_credits`/`unlimited`·초과 사용(`extra_usage_enabled`)·Grok `on_demand_cap`/`prepaid_balance`·
  `paid_credit_fallback_disabled` 증거 부재는 더 이상 경로를 막거나 사용자에게 되묻는 사유가 아니다.
  계획에는 정보로만 남는다. `PAID_CREDIT_EXPOSURE`·`PAID_CREDIT_FALLBACK_UNVERIFIED`·`OVERAGE_UNVERIFIED`·
  `CODEX_PAID_CREDIT_EXPOSURE` 판정을 없앴다.
- Codex·Grok·일반 CLI 실행 어댑터도 같은 기준이다. Codex 어댑터는 실행 직전 계정 재관측에서
  rate limit·spend control 도달을 확인한다(`CODEX_USAGE_LIMIT_REACHED`).
- 포함 사용량을 다 쓰면 기존 구매 크레딧이 빠질 수 있으므로 85% 상한이 그 보호다. 이미지 경로의
  제공자 USD 0 하드캡은 원자적 어댑터 계약이라 유지했다.
- ai-debate는 이미 같은 규칙이라 바꾸지 않았다(좌석 크레딧은 사유 문구에만, 기준 95%).

## 2.14.2 - 2026-10-04

- D-67 읽기 전용 Orca canary 결과를 반영했다. 2026-10-04 13:19~13:27 KST 에 Orca 1.4.218 로
  레인마다 워커 1개를 띄웠다(run `run_92ff481d8b2f`). 두 레인 모두 `launch.requested` 와
  `launch.effective` 가 같았다. `claude-opus-5-5`@high 는 argv `--model claude-opus-5-5 --effort high`,
  세션 기록 model `claude-opus-5-5`, 응답 `claude-opus-5-5 CANARY-OK` 였다. `gpt-6.1-sol`@xhigh 는 argv
  `-m gpt-6.1-sol -c model_reasoning_effort=xhigh`, 세션 기록 `gpt-6.1-sol`/xhigh, 상태줄
  "GPT-6.1-Sol xhigh fast", 응답 `gpt-6 CANARY-OK` 였다(자기보고는 계열명뿐이고 서버측 모델은 따로
  확인하지 못했다). 두 워커는 정지했고 PID 가 사라진 것을 확인했다. 쿼터는 전후 모두 한도 안이었다.
- registry `legacy_lane_migration` 에서 후보가 두 레인인 항목 4개(`claude-opus-5-5`·`claude-opus-5`·
  `gpt-6.1-sol`·`gpt-5.6-sol`)를 `pending-transport-and-canary` 에서 `pending-transport-and-certificate`
  로 바꿨다. `gpt-5.6-terra` 는 후보가 `gpt-6.1-sol` 이지만 상태가 평가 보류
  (`pending-evaluation-not-equivalent-tier`)라 그대로 두었다. `claude-sonnet-5`·`gpt-5.6-luna` 는
  canary 를 하지 않은 후보라 그대로다. 제공사 사실과 `checked_at` 은 바꾸지 않았고
  레지스트리 version 만 2026-10-04.3 이 됐다.
- **여전히 동작 레인이 아니다.** Orca native send 보류, 준비 브리지 미구현, Orca 런치 계정/과금
  인증서 부재(모델 포함, 초과과금 OFF, API 폴백 OFF, Codex 크레딧 폴백 OFF, `request_identity`,
  plan binding)가 그대로다. 라우팅·우선순위·게이트 동작은 바뀌지 않았다.
- `references/orca-workflow.md` 에 canary 에서 관측한 운영 주의 3건을 적었다. Orca 워커는 전권
  모드(Claude `--dangerously-skip-permissions`, Codex 승인·샌드박스 우회)로 떠서 읽기 전용은
  과제문으로만 지켜진다. Codex 워커는 `service_tier="priority"` 를 물려받는다(사용량 배수 미확인).
  실제 과제문은 `worker_done` CLI 호출을 허용해야 한다(금지하면 Task 가 `blocked` 로 남는다).
- `routing.py` 의 두 레인 주석·`ctx` 와 `legacy-routing.md`(`sync_skill_table.py` 로 재생성),
  `model-catalog-map.md`, SKILL.md 의 상태 문구를 고쳤다. `test_model_registry.py` 의 D-67 테스트는
  새 상태, 상태를 바꾼 항목이 정확히 4개라는 것, terra·luna 상태 유지, 대응표 행의 새 상태를 본다.
  오프라인 테스트만 실행했다.

## 2.14.1 - 2026-10-04

- 7일 창이 닫히기 전에 모델 레지스트리를 다시 갱신했다(허브 PROTOCOL §35.8 1단, 승인된 절차 반복).
  레지스트리 출처 28개와 task-fit 출처 9개를 모델 호출 없이 HTTPS 로 다시 읽었고(전부 HTTP 200,
  openai.com Astra 페이지는 브라우저 요청 헤더로 재시도), 로컬 Codex·Grok·agy·Claude CLI 카탈로그와
  메타데이터 전용 `runtime_collect.py`(Codex app-server `model/list`, Grok ACP 과금) 결과와 대조했다.
  프롬프트·Orca 워커는 0회다. 모델 ID·API effort·컨텍스트·가격·장문 구간·은퇴 일자·Daybreak 대상·
  Claude Code 주석이 모두 그대로라 제공사 사실은 바뀌지 않았고, 제거·개명된 모델도 없다.
- `checked_at` 은 실제로 쓴 근거 중 가장 이른 시각인 Grok 모델 캐시 수신 2026-10-04 13:05:20 KST 다.
  그래서 사실은 2026-10-10 21:42:01 KST 대신 2026-10-11 13:05:20 KST 에 `REGISTRY_STALE` 이 된다.
  shadow task-fit 정책은 2026-10-04 13:13:08 ~ 2026-10-11 13:13:08 KST 에 유효하고, 인용 주장과
  순위는 그대로다. 레지스트리 version 은 2026-10-04.2, 정책은 2026-10-04-shadow.1 이다.
- 관측만 기록했다: Claude Code 2.1.289(전 2.1.288). Google "Gemini 4 Argon"(2026-09-30 공지)은
  Fairwind Program 신뢰 사용자 대상 단계 배포라 API ID·문서·가격·agy 이름이 없어 등록하지 않았다.
  레인 라우팅·우선순위·D-67 `legacy_lane_migration` 상태는 바꾸지 않았다(Orca canary 결과는 따로 반영한다).
- `scripts/adversarial_eval.py` 의 `VENDOR_OF` 가 D-67 새 레인 `claude-opus-5-5`(claude)·`gpt-6.1-sol`(codex)을
  옛 이름 옆에 갖는다. 같은 김에 빠져 있던 `routing.LANES` 키 `claude-fable-5-1`·`claude-sonnet-5`(claude)도
  넣었다. 옛 키는 그대로라 기존 평가 원장 행과 동작은 같다. `eval/probes.json` 은 registry 이전 후보가
  레인인 경우 옛 레인 옆에 새 레인을 둔다(`claude-opus-5` 옆 `claude-opus-5-5` 18곳, `gpt-5.6-terra` 옆
  `gpt-6.1-sol` 11곳). 실호출은 여전히 격리돼 있고 dry 경로만 확인했다.
- `test_model_registry.py` 에 두 테스트를 더했다. `routing.LANES` 키가 `VENDOR_OF` 에 없거나 벤더가 다르면,
  그리고 probe 가 레인이 아닌 이름을 쓰거나 이전 후보 레인을 빠뜨리면 실패한다. main 의 옛 파일로 되돌리면
  두 테스트 모두 실패하는 것을 확인했다. 기간 테스트는 2026-10-04 재확인 창을 본다.

## 2.14.0 - 2026-10-04

- 허브 결정 D-67(토론 `dbt-261004-033902`, ADD_ALONGSIDE_KEEP_LEGACY, 4/4,
  심판 확신도 92)에 따라 현행 세대 Orca 레인 두 개를 옛 레인 옆에 추가했다.
  `claude-opus-5-5` 는 flag 레인(정책 high/max, Orca low~max)이고 `gpt-6.1-sol` 은
  flag 레인(정책 high/xhigh, Orca minimal~xhigh)이다. 근거는 Orca 1.4.218 번들의
  검증 코드(claude 미등록 id → low~max, codex 미등록 모델 → xhigh 상한)이며 모델 호출은 0회다.
- 이 두 레인은 **등록만 됐다.** registry `legacy_lane_migration` 상태는
  `pending-transport-and-canary` 이고, 읽기 전용 canary(`launch.requested` ↔
  `launch.effective`)와 Orca 런치 계정/과금 인증서 전까지 동작 레인이 아니다.
  native send 보류와 준비 브리지 미구현도 그대로다.
- 우선순위 목록(A·B·A-verify·C-realtime·C-platform·D)과 `PROCESS_LANES.coding` 의
  `claude-opus-5` 를 `claude-opus-5-5` 로 바꿨다. 옛 opus 레인은 prompt-keyword 라
  guarded Orca 로 실행되지 않아 코딩 1순위와 종합 고정이 실행 경로가 없었다.
- 종합 고정을 `(claude-opus-5, ultracode)` 에서 `(claude-opus-5-5, max)` 로 옮겼다.
  ultracode 는 프롬프트 키워드라 flag 레인이 받을 수 없고, max 는 opus-5-5 의 Orca
  상한이자 허브 핀이다. 코디네이터는 `gpt-6.1-sol` @xhigh 다(종합과 다른 벤더,
  D-28 #8 의 effort 유지, 6.1-sol 의 Orca 상한). C 클래스 2순위도 `gpt-6.1-sol` 이다.
- 옛 키는 지우지 않았다. `ledger.py` 가 `LANES` 에 없는 레인의 원장 행을 거부하므로
  `claude-opus-5`·`gpt-5.6-sol` 등은 원장 호환용으로 남고, `gpt-5.6-sol` 은 C 클래스
  목록 끝의 폴백이다. sol 후속은 `gpt-6.1-sol` 로 통일했다(registry 의 `gpt-6-sol` 표기 정리).
  레지스트리 version 은 2026-10-04.1 이 됐지만 제공사 사실과 `checked_at` 은 그대로다.
- `claude-sonnet-5-5`·`gpt-6-luna`·`gpt-6-sol`·`grok-4.7` 은 레인을 만들지 않았다.
  sonnet-5-5 는 effort 재보정이 필요하고, 6-luna 는 A 클래스 1순위를 바꾸는 별도 결정이며,
  grok 은 Orca 가 모델을 고정하지 못한다. 이들로의 Orca 발주는 여전히
  `ORCA_UNREGISTERED_PROCESS_OR_MODEL` 이다.
- 소수의견 방어 테스트를 추가했다. 모델 포함·초과과금 OFF 증거가 없으면 새 레인도 기존
  flag 레인과 같은 사유(`MODEL_INCLUSION_UNVERIFIED`·`OVERAGE_UNVERIFIED`)로 막히고,
  쿼터 증거가 없으면 `ORCA_G5` 로, 런치 인증서가 없으면 `TRANSPORT_ACCOUNT_UNVERIFIED`
  로 막힌다. `gpt-6.1-sol` @max·ultra 와 `claude-opus-5-5` @ultracode 는
  `ORCA_DISPATCH_UNSUPPORTED` 다. 오프라인 테스트만 실행했다.

## 2.13.1 - 2026-10-03

- Refresh the model registry before its seven-day window closed: all 28
  registry sources and the nine task-fit sources were re-read over HTTPS
  (HTTP 200), and model IDs/efforts were compared with the local Codex, Grok,
  agy and Claude CLI catalogs, without a model call. No provider fact changed:
  IDs, API efforts, context, prices, long-context tiers, retirement dates, the
  Daybreak alias target and the Claude Code notes all match.
- `checked_at` is the earliest evidence timestamp, the Grok models cache fetch
  at 2026-10-03 21:42:01 KST, so the facts stay fresh until
  2026-10-10 21:42:01 KST instead of becoming `REGISTRY_STALE` on
  2026-10-09 00:39:26 KST. The shadow task-fit policy is valid until
  2026-10-10 21:47:06 KST; its cited claims and ranks are unchanged.
- `gpt-6-sol` stays active: OpenAI's model page points to GPT-6.1 Sol as the
  newer Sol model, but its 2026-10-01 deprecation notice names `gpt-6-sol` as a
  replacement, not a deprecated model. `gemini-3.1-pro-preview` stays preview
  with no shutdown date.
- agy 1.2.16 now lists `claude-opus-5-5-*` and `claude-sonnet-5-5-*` (low,
  medium, high) instead of `claude-sonnet-4-6` and `claude-opus-4-6-thinking`.
  The map in `references/model-catalog-map.md` records them as unregistered,
  because the schema binds the antigravity surface to Google.
- Codex 0.160.0 and Claude Code 2.1.288 were observed; their model and effort
  lists are unchanged. Orca lanes are unchanged.

## 2.13.0 - 2026-10-03

- A run that writes code (a node with `writes`, `proc=coding`, a CODE_* task
  type or the `qa` skill) can no longer complete without a pinned QA binding:
  `run_state.py bind-qa` records the QA contract and target once
  (`QA_BINDING_IMMUTABLE`, absolute paths only, `QA_INTENT_CHANGED` when the
  spec digest moves), and `Store.complete` reruns the QA gate before it marks
  the run done (`QA_BINDING_REQUIRED` otherwise). There is no opt-out, so an
  already open coding run also needs `bind-qa`. `check-qa` runs the gate alone.
- `scripts/qa_acceptance.py` executes the qa skill's `qa_gate.py` only when its
  LF-normalized SHA-256 matches the pinned constant; changing `qa_gate.py`
  needs the same constant change here. The complete event payload carries the
  QA report; the database schema is unchanged.
- Pairs with qa 2.1.0 (contract hash, exact revision/environment and evidence
  file hashes, fail-closed on missing, skipped, failed or stale evidence).
  Installed on 2026-10-03 03:43 from `feat/qa-evidence-261003` before it
  reached main; landed on main through PR #96.

## 2.12.43 - 2026-10-02

- Refresh the model registry before its seven-day window closed: every
  official source was re-read over HTTPS and model IDs/efforts were compared
  with the local Codex, Grok, agy and Claude CLI catalogs, without a model call.
  `checked_at` is now the earliest observation, 2026-10-02 00:39:26 KST, so the
  facts stay fresh until 2026-10-09 00:39:26 KST instead of becoming
  `REGISTRY_STALE` on 2026-10-06 04:03 KST.
- Register `grok-4.5` as a legacy entry with low, medium and high only: xAI's
  reasoning guide says it treats `xhigh` as `high`. Label `claude-sonnet-5`
  legacy, as Anthropic does, while it stays active.
- Leave CLI-only names unregistered and map them in
  `references/model-catalog-map.md`: `grok-4.7-build-fast` (2x token rates,
  Cursor/Grok Build only), agy effort-suffixed Gemini names, and Haiku 4.5,
  which has no effort parameter. Requests for them still fail with
  `MODEL_NOT_REGISTERED`.
- Re-read the nine task-fit sources; claims and ranks are unchanged and the
  shadow policy is valid until 2026-10-09 00:42:30 KST.
- Orca lanes are unchanged. Orca dispatch to current-generation models is still
  rejected until a separate lane-migration decision. The advisory table now
  names GPT-6.1 Sol.
- Offline tests cover the refreshed windows, the new and legacy entries, the
  unregistered CLI names, the Grok 1.0.46 listing and the Orca rejection.
- Make the legacy label count in routing. `constrain_runtime` now copies the
  registry's `generation` onto the candidate and drops any runtime claim. The
  planner and the shadow task-fit score put `generation: legacy` after resource
  rank and the 80% quota guard, before quota percentage. Before this,
  candidate-ID order let `grok-4.5` beat an equally ranked `grok-4.7` on a host
  route. Plans without a legacy candidate keep the same routes and digests.
- CI now runs `test_model_registry.py`, where most of the refresh tests live.
- `references/model-catalog-map.md` no longer says every lane migration is
  pending (four are `keep-*`) or that a registered legacy model never routes.

## 2.12.42 - 2026-10-01

- Give each /vibe run its own Gstack state folder with telemetry, update checks
  and onboarding prompts off. `run_state.py gstack-env --run <id>` creates
  `gstack-runs/<sha256 prefix>` beside the run DB without creating the DB or
  touching the personal `~/.gstack`, and prints the env, an `export` line and a
  PowerShell line. Re-entry reads the config like `gstack-config get` (last
  `key:` line, LF-split lines only, quotes kept, exact `off`/`false`) and fails
  closed otherwise.
- Plans mark Gstack bin tool handoffs when any argv element names a
  `skills/gstack/bin/` script, and Gstack-skill host/Orca nodes. Inventory flags
  a skill `gstack: true` when its SKILL.md bytes (or a shadowed alternative's)
  reference `skills/gstack/bin/` or `~/.gstack`/`$HOME/.gstack`, which catches
  plugin-packaged Gstack skills; the flag stays out of `inventory_digest`.
- The brief names `<vibe skill folder>` instead of an absolute path, so Orca Task
  specs do not depend on the install path. `refresh` rejects a changed Task spec
  on a bound, unfinished Orca node with `TASK_SPEC_CHANGED`. Finalize drafted
  preparations before upgrading; cancel and re-plan registered runs whose Task
  spec changed.
- Isolation is instruction-level: nothing reads `gstack_isolation` at runtime,
  Orca is best-effort, and Gstack-derived skills and some bin scripts still use
  `~/.gstack`/`$HOME` directly (see the orchestration reference).
- Require a PROTOCOL §35 decision record to come from `/ai-debate` >= 0.2.0 with
  all four vendor seats; the five-node debate graph is an execution contract only.
- Offline tests only. No Gstack, model, Orca worker or Bot call was made, and
  `gstack-runs` folders are not cleaned up automatically.

## 2.12.18 - 2026-09-30

- Bind Grok CLI and Grok Bot quota evidence to their distinct surface,
  transport and account, and require a freshly observed state. A reset timestamp
  or the other xAI path's quota cannot reopen a held route. Offline tests cover
  wrong surface, transport, account, missing evidence and unobserved reset.
- Align the `model-router` image-generation contract and Bot fixture with the
  already enforced planner gates. This is source-only: no provider generation,
  Relay delivery, user installation or subscription billing proof is claimed.

## 2.12.8 - 2026-09-30

- Enforce the existing writing-review rule for typed `WRITING` outputs even
  when they do not edit files. Require an independent LLM reviewer in the same
  plan and hold downstream consumers until it passes on either host. Offline
  tests cover the previously ready unreviewed path and reviewed recovery;
  this does not establish live Claude/Codex behavior or permit paid calls.

## 2.12.5 - 2026-09-29

- Admit locally measured Antigravity CLI 1.2.13 for metadata-only `/usage`:
  `/help` and `/usage` both exited successfully with zero turns and zero tokens.
  Unknown versions still stop before the slash command; this does not verify
  account identity, subscription billing, model inclusion or generation.

## 2.12.4 - 2026-09-29

- Clarify that disabling auto-reload is not proof of disabled extra-credit
  consumption for Codex or Grok. Require account/transport-specific overage
  evidence for Claude, Codex, Antigravity, Grok and Grok Bot before treating
  subscription usage as zero additional spend. No payment setting is changed.

## 2.12.3 - 2026-09-29

- Bind default catalog discovery in a Codex compatibility overlay to both
  the original bundle and its exact manual-only `zoom-out` projection.
- Reject altered overlay bytes or forged projection receipts without falling
  back to a different skill root. This is offline discovery validation, not
  host installation or model-routing certification.

## 2.12.2 - 2026-09-28

- Fail closed when legacy plan quota checks are omitted; preserve quarantine of live preflight paths.

## 2.12.1 - 2026-09-28

- Recheck current GPT, Claude, Gemini and Grok provider facts on 2026-09-28
  and refresh the seven-day model-registry evidence window. Public model
  support still does not establish subscription access or permit API billing.
- Explicitly warn that non-interactive Claude Fable can charge usage credits
  without a consent prompt; keep exact-model inclusion and overage gates.

## 2.12.0 - 2026-09-28

- Block pinned Gstack design API-key setup, generation and checks under subscription-only USD 0; require transitive local-command cost evidence.

## 2.11.13 - 2026-09-27

- Make Play Console and other GUI requests discover the `/vibe` coordinator
  even without a slash invocation. Check authorized CLI/API/MCP first and name
  only the actual `vibe-bot` adapter for GUI-only steps.
- Add a natural-language GUI routing evaluation and a description regression
  after a tool-less Claude subscription probe invented a nonexistent specialist.
  This metadata change is not a measured improvement in live selection accuracy.
- Add the exact skill-name question as a second evaluation. A follow-up
  isolated probe with `Skill` available selected the real `/vibe` on both the
  old and revised metadata. The tool-less probe disabled automatic skill use;
  it cannot establish a regression or a metadata-driven improvement.

## 2.11.12 - 2026-09-27

- Admit only locally measured Antigravity CLI 1.2.12 for zero-turn, zero-token
  `/usage` metadata collection. Keep account, model and billing verification
  unavailable; the observed quota buckets do not authorize generation.
- Record the installed CLI's rejection of `agy models --output-format json`;
  do not infer executable model routes from the text-only listing.

## 2.8.0 - 2026-09-23

- Add durable local run/account reservations and dispatch intents in one SQLite
  transaction; keep the authorized grant immutable and default to USD 0.
- Prevent repeated claim sends and unsafe retries after uncertain acceptance;
  require original-job lookup, terminal proof, cost settlement and fresh plans.
- Separate execution success, acceptance/rejection and actual-cost evidence.
  Preserve unknown cost and observed overruns; never release them on timeout.
- Add crash, concurrent-process, local CLI lifecycle and sensitive-payload
  regression tests. Strict embedded JSON parsing rejects duplicate keys and
  non-finite values; exact nanoUSD conversion never rounds approval caps up.
- Document trusted-coordinator and single-local-DB boundaries. No provider
  generation adapter, live five-surface E2E, installation or main promotion is
  implied by these state tests.

## 2.7.0 - 2026-09-23

- Add a central model/effort registry with separate provider and transport facts;
  reject stale alias/access evidence again when work becomes ready.
- Collect explicit one-shot Codex, Claude, Grok and Antigravity CLI metadata.
  Preserve observed quota buckets, credit fields and opaque account references.
- Keep unknown billing, missing identity and unverified generation unavailable;
  do not equate subscription usage or metadata success with zero-cost execution.
- Bound probe I/O and lifetime; contain owned Windows process trees before
  launch and reject server-initiated actions or unknown Antigravity contracts.
- Add offline collector regression tests. Actual metadata observations are not
  five-surface task E2E, cost authorization or deployment-parity evidence.
- Leave legacy Orca defaults unchanged. Persistent execution/budget state,
  all-consumer migration and validated installation remain separate work.

## 2.6.0 - 2026-09-23

- Introduce the umbrella skill entry point, discovered skill composition,
  five execution surfaces, dependency preflight and total-run cost bounds.
- Integrate the vibe-bot handoff and result-verification contract.

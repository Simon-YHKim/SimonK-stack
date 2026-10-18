# Model catalog map — CLI names, registry IDs and the 2026-10-18 refresh

## Contents

- CLI name map
- Registered legacy entries
- Lane migration pending
- Refresh record (2026-10-18)
- Refresh record (2026-10-12)
- Repeating the refresh

`references/model-registry.json` stores provider API IDs only. CLI catalogs can
print a different name, carry an effort inside the name, or offer a CLI-only
serving tier. The names below are documentation, not registry IDs or aliases:
a runtime candidate that requests one fails closed with `MODEL_NOT_REGISTERED`.
The registry schema has no CLI-name alias table, so the IDs stay unchanged.

## CLI name map

agy prints no API ID; its rows are matched by display name, for example
"Gemini 3.8 Flash (High)". `runtime_collect.py` does not collect agy models and
no guarded agy execution adapter exists, so this map grants no route.

| Surface | CLI catalog name | Registry ID | Effort in name | Note |
| --- | --- | --- | --- | --- |
| `antigravity` | `gemini-4-argon-high` | `gemini-4-argon` | `high` | thinking level high; D-104 ai-debate Gemini seat default |
| `antigravity` | `gemini-4-argon-medium` | `gemini-4-argon` | `medium` | API default level |
| `antigravity` | `gemini-4-argon-low` | `gemini-4-argon` | `low` | |
| `antigravity` | `gemini-3.8-flash-high` | `gemini-3.8-flash` | `high` | thinking level high |
| `antigravity` | `gemini-3.8-flash-medium` | `gemini-3.8-flash` | `medium` | API default level |
| `antigravity` | `gemini-3.8-flash-low` | `gemini-3.8-flash` | `low` | |
| `antigravity` | `claude-opus-5-5-low` | `unregistered` | `-` | Anthropic model on the Google surface; the schema binds antigravity to Google |
| `antigravity` | `claude-opus-5-5-medium` | `unregistered` | `-` | same |
| `antigravity` | `claude-opus-5-5-high` | `unregistered` | `-` | same |
| `antigravity` | `claude-sonnet-5-5-low` | `unregistered` | `-` | same |
| `antigravity` | `claude-sonnet-5-5-medium` | `unregistered` | `-` | same |
| `antigravity` | `claude-sonnet-5-5-high` | `unregistered` | `-` | same |
| `antigravity` | `gpt-oss-120b-medium` | `unregistered` | `-` | not a Google model |
| `grok` | `grok-4.7-build-fast` | `unregistered` | `-` | Grok 4.7 on faster serving at 2x standard token rates (1.5x long context), Cursor and Grok Build only, not on the public xAI API. Not for default routing |
| `claude` | `claude-haiku-4-5-20251001` | `unregistered` | `-` | Claude docs: default effort "Not supported", so it cannot satisfy the registry's explicit effort list; Legacy since Haiku 5.5 (2026-10-07), retirement not sooner than 2026-10-15 |
| `codex` | `gpt-5.5` | `unregistered` | `-` | in the Codex models cache with efforts up to xhigh; previous generation. Hidden in the Codex catalog as of 2026-10-06 (public on 2026-10-04). The 2026-10-12 cache says it retires on 2026-10-14 (upgrade target `gpt-6.1-sol`) |
| `codex` | `gpt-reserve` | `unregistered` | `-` | hidden in the Codex catalog |
| `codex` | `codex-auto-review` | `unregistered` | `-` | hidden in the Codex catalog |

`claude-haiku-5-5` 는 D-99(2026-10-12, 2.16.0)로 레지스트리에 **등록**됐다(2.15.7 까지는 이 표의 `unregistered`
행이었다). 등록된 ID 는 CLI 전용 이름이 아니라서 이 표에서 뺐다. 이 표의 이름은 레지스트리 키가 아니어야 한다.
등록 사실, 두 가격 구간, 레인 상태는 아래 "Lane migration pending" 에 있다.

## Registered legacy entries

- `grok-4.5` is a public xAI API model, so it is registered as `generation: legacy`
  with `low`, `medium`, `high`. Its model page lists `xhigh`, but the reasoning
  guide says grok-4.5 treats `xhigh` as `high`, and its release note and grok CLI
  1.0.46 list three levels; the conservative set wins.
- `claude-opus-5` and `claude-sonnet-5` are labelled Legacy on their Claude
  overview pages and Active in the deprecation table, so they keep
  `lifecycle: active` and carry `generation: legacy`, like `gpt-5.6-*` and `grok-4.6`.
- registry 에 등록됐다고 Orca 레인이 생기지는 않는다(D-67 과 2026-10-05 Simon 지시로 추가된 네 레인,
  D-99 의 `claude-haiku-5-5` 는 아래 절).
  shadow task-fit 정책은 현행 Claude/Codex 모델만 든다. 자기 게이트를 통과한
  Orca 밖 경로는 legacy 모델을 고를 수 있다. `constrain_runtime` 이
  `generation: legacy` 를 후보에 복사하고, planner 는 그 값을 resource rank 와
  80% 쿼터 가드 다음, 쿼터 비율 앞에서 본다. 그래서 순위가 같으면 legacy 모델은
  현행 모델에 진다. 현행 모델이 쿼터를 더 썼어도(80% 미만) 마찬가지다.

## Lane migration pending

D-67(2026-10-04, 허브 토론 `dbt-261004-033902`, ADD_ALONGSIDE_KEEP_LEGACY)에 따라
2.14.0 은 Orca 레인 두 개를 옛 레인 **옆에** 추가했다. 근거는 Orca 1.4.218 번들의
검증 코드를 읽은 것이며 모델 호출·worker-start 는 0회다. 2.15.5 는 2026-10-05 Simon 지시로
A 클래스 레인 두 개를 같은 방식으로 더했다(표의 셋째·넷째 줄, 이 변경에서도 모델 호출·worker-start 0회).
2.16.0 은 D-99(2026-10-12)로 `claude-haiku-5-5` 를 더했다(표의 마지막 줄). 이 줄의 canary 는 오케스트레이터가
돌렸고, 구현 변경 자체에서는 모델 호출·worker-start 가 0회다.
2.17.0 은 D-101(2026-10-12, Simon 지시)로 GPT 쪽 레인을 `gpt-6-astra` 하나로 줄였다. 표의 `gpt-6.1-sol`·`gpt-6-luna`
줄은 철회된 레인이다(키는 원장 호환용으로 남는다). 지금 값은 이 절 아래쪽의 D-101 항목이 정본이고, 그 위의 D-67·
2026-10-05·D-99·D-98 항목은 그 시점 기록이다.

| 새 레인 | 전달 | Orca 1.4.218 이 받는 effort | 정책 std / top | registry 상태 |
| --- | --- | --- | --- | --- |
| `claude-opus-5-5` | `--effort` 플래그 | low~max (claude 카탈로그에 없는 정식 id) | high / max | `pending-transport-and-certificate` |
| `gpt-6.1-sol` | `--effort` 플래그 | minimal~xhigh (codex 미등록 모델 폴백, max·ultra 거부) | high / xhigh | `held-withdrawn-by-owner` (D-101 철회, 새 배정은 `LANE_WITHDRAWN`) |
| `claude-sonnet-5-5` | `--effort` 플래그 | low~max (claude 카탈로그에 없는 정식 id) | medium / high (xhigh·max 는 정책 밖) | `pending-transport-and-certificate` |
| `gpt-6-luna` | `--effort` 플래그 | minimal~xhigh (codex 미등록 모델 폴백, max·ultra 거부) | low / medium | `held-withdrawn-by-owner` (D-101 철회, 새 배정은 `LANE_WITHDRAWN`) |
| `claude-haiku-5-5` | `--effort` 플래그 | low~max (claude 카탈로그에 없는 정식 id) | low / medium (high·xhigh·max 는 정책 밖) | `pending-transport-and-certificate` |

- 우선순위 목록·`PROCESS_LANES.coding`·종합 고정·코디네이터를 새 키로 옮겼다.
  종합은 `claude-opus-5-5` @max 다. ultracode 는 프롬프트 키워드라 flag 레인이 받지 못한다.
  코디네이터는 `gpt-6.1-sol` @xhigh 로, 종합(claude)과 벤더가 다르고 xhigh 는 6.1-sol 의 Orca 상한이다.
- 옛 키는 지우지 않는다. `ledger.py` 는 `LANES` 에 없는 레인의 원장 행을 거부하므로
  `claude-opus-5`·`gpt-5.6-sol` 등은 원장 호환용으로 남는다. `claude-opus-5` 는 우선순위 밖이고,
  `gpt-5.6-sol` 은 C 클래스 목록 끝의 폴백이다. sol 의 후속은 `gpt-6.1-sol` 로 통일했다
  (`gpt-5.6-terra` 의 평가 후보도 같다).
- **canary 는 통과했지만 아직 동작 레인이 아니다(2.14.2).** 2026-10-04 13:19~13:27 KST 의 읽기 전용
  canary(Orca 1.4.218, run `run_92ff481d8b2f`, 레인마다 워커 1개)에서 두 레인 모두
  `launch.requested` 와 `launch.effective` 가 같았다. `claude-opus-5-5`@high 는 argv
  `--model claude-opus-5-5 --effort high` 이고 세션 기록의 model 도 `claude-opus-5-5` 였다.
  `gpt-6.1-sol`@xhigh 는 argv `-m gpt-6.1-sol -c model_reasoning_effort=xhigh` 이고 세션 기록은
  `gpt-6.1-sol`/xhigh 였다. 단, 응답의 자기보고는 계열명 `gpt-6` 이고 서버측 모델은 따로 확인하지
  못했다. 두 워커는 정지했고 PID 가 사라진 것을 확인했다.
- 그래서 후보가 두 레인인 registry 항목 4개(`claude-opus-5-5`·`claude-opus-5`·`gpt-6.1-sol`·`gpt-5.6-sol`)를
  `pending-transport-and-certificate` 로 바꿨다. native send 보류, 준비 브리지 미구현, Orca 런치
  계정/과금 인증서 부재(모델 포함, 초과과금 OFF, API 폴백 OFF, Codex 크레딧 폴백 OFF,
  `request_identity`, plan binding)는 그대로라 준비된 경로로 보지 않는다. 모델 포함·초과과금 OFF·
  API 폴백 OFF·G5·런치 인증서 게이트는 기존 flag 레인과 똑같이 걸린다(`test_orchestrate.py`·
  `test_execute_orca.py` 의 D-67 테스트). 운영 주의 3건은 `orca-workflow.md` 에 적었다.
- **2026-10-05 Simon 지시(2.15.5): A 클래스를 현행 세대로 옮겼다** — "5.5로 전환해. 최신모델을써야지
  왜 구모델을씀?". A 클래스는 `gpt-6-luna` → `claude-sonnet-5-5` → `claude-opus-5-5` 이고, 옛
  `gpt-5.6-luna`·`claude-sonnet-5` 는 원장 호환용(우선순위 밖)이다. A 1순위의 산출물 제약(정형 변환·카운트·
  분류, 부재 보고에는 탐색 범위)도 `gpt-6-luna` 로 옮겼다. `claude-sonnet-5-5` 사다리는 Sonnet 5 의
  medium/xhigh 를 물려받지 않고 다시 잡았다: std medium(Claude Code·앱 기본값), top high(Artificial
  Analysis 가 Sonnet 5.5 의 가장 경쟁력 있는 설정으로 보는 값). xhigh·max 는 토큰 폭증(max 에서 작업당
  출력 약 193k 토큰) 때문에 정책 사다리 밖이고 off-ladder 로만 열린다. 쿼터는 claude 일반 weekly 다.
  `gpt-6-luna` 는 `gpt-5.6-luna` 와 같은 low/medium 이고, Orca 상한은 seed 밖 폴백이라 xhigh 다(5.6-luna 는 max).
- **canary 는 통과했지만 아직 동작 레인이 아니다(D-91, 2.15.5).** 2026-10-05 20:47~20:53 KST 의 읽기 전용
  canary(Orca run `run_0a369252175f`, 레인마다 워커 1개, 도구 금지 한 줄 응답, D-67 과 같은 folder worktree)에서
  두 레인 모두 `launch.requested` 와 `launch.effective` 가 같았다. `claude-sonnet-5-5`@medium 은 argv
  `--model claude-sonnet-5-5 --effort medium` 이고 세션 기록의 model 도 `claude-sonnet-5-5` 였다(자기보고는
  `claude-fable-5-1 CANARY-OK` 로 틀렸다). `gpt-6-luna`@low 는 argv `-m gpt-6-luna -c model_reasoning_effort=low`
  이고 rollout `turn_context` 는 `gpt-6-luna`/low 였다(자기보고 `gpt-6.1-sol CANARY-OK`, 서버측 모델은 따로
  확인하지 못했다). 두 워커는 정지했고 PID 가 사라진 것을 확인했다. 그래서 상태는
  `pending-transport-and-certificate` 이고, Orca 런치 계정/과금 인증서가 생기기 전까지 준비된 경로로 보지 않는다.
  모델 포함·초과과금 OFF·API 폴백 OFF·G5·런치 인증서 게이트는 기존 flag 레인과 똑같이 걸린다
  (`test_orchestrate.py`·`test_execute_orca.py` 의 A 클래스 레인 테스트).
- `claude-sonnet-5` → `claude-sonnet-5-5` 는 D-90(2026-10-05)으로 `held-until-remeasure` 였다가, 같은 날
  Simon 지시(D-91)로 전환했고 canary 를 통과해 지금은 `pending-transport-and-certificate` 다. D-90 소수의견대로 이 레인에 대한
  Simon 의 명시 지시가 보류보다 앞선다. D-90 이 든 비용 근거(Artificial Analysis 는 Sonnet 5.5 의 작업당
  비용을 Sonnet 5 보다 약 50% 높게 보고, 모든 effort 가 지능 대비 작업당 비용 프런티어 밖이라고 적는다)는
  별개의 비용 프런티어 판단이라 shadow task-fit 정책의 `claude-sonnet-5-5` 제외(재진입 조건은 그 정책 노트)는
  그대로 두었다.
- **D-99(2026-10-12, 2.16.0): `claude-haiku-5-5` 를 등록하고 A 클래스의 Claude 쪽 첫 폴백으로 넣었다**
  (허브 토론 `dbt-261012-124540`, quick, PROVISIONAL 3/4, 심판 확신도 82). A 클래스는 `gpt-6-luna` →
  `claude-haiku-5-5` → `claude-sonnet-5-5` → `claude-opus-5-5` 다. 1순위는 그대로이고 Sonnet 5.5 도 남는다.
  B·A-verify·D·코딩 목록과 shadow task-fit 정책은 바꾸지 않았다. 사다리는 std low(canary 가 띄운 값), top
  medium(제공사 기본값)이고 high·xhigh·max 는 off-ladder 로만 열린다. Orca 의 low~max 는 D-67 의 1.4.218
  읽기와 `claude-sonnet-5-5` 를 따른 값이며, canary 가 실제로 띄운 effort 는 low 하나다.
  - 등록 사실(2026-10-12 13:01:22~13:01:28 KST 에 공식 페이지 7개를 모델 호출 없이 HTTPS 로 읽음, 전부 첫 요청
    HTTP 200): 2026-10-07 출시, Active, 은퇴 2027-10-07 이후, 1M 컨텍스트, 128K 출력, effort low~max
    (API·Claude Code 기본 medium), adaptive thinking, Claude Code 2.1.293 이상. `haiku` 별칭은 Anthropic API
    에서만 Haiku 5.5 이고 다른 제공사에서는 Haiku 4.5 라서 레인은 정식 ID 를 보낸다.
  - 가격은 프롬프트 길이로 갈린다. 10만 토큰 이하: 입력 $0.10, 캐시 읽기 $0.01, 출력 $0.50. 10만 토큰 초과:
    입력 $0.50, 캐시 읽기 $0.05, 출력 $2.50. 레지스트리는 `pricing.tiers` 의 `above_input_tokens: 100000` 으로
    담았다. 스키마가 담지 못한 것 둘은 `pricing.note` 에 적었다: 캐시 쓰기가 구간마다 둘(5분 $0.125/$0.625,
    1시간 $0.20/$1)이라 `cache_write` 는 null 이고, 프롬프트 길이가 캐시 읽기·쓰기를 포함한 모든 입력 토큰이며
    요청마다 따로 판정된다는 점이다.
  - canary(오케스트레이터 실행, 12:53~12:54 KST, Orca run `run_8f7a27febc38`, dispatch `ctx_cd78cf210447`,
    읽기 전용 워커 1개, 도구 금지): `launch.requested` == `launch.effective`(`claude-haiku-5-5`, low), Claude 세션
    기록의 두 assistant 메시지 모두 `message.model` 이 `claude-haiku-5-5`(entrypoint `cli`)였다. 정답이 스크립트로
    정해진 A 클래스 과제 3개가 전부 맞았다: CSV→JSON 변환 완전 일치, 스키마 위반 id `2,3,5,6,7`, 로그 24줄 레벨
    집계 `ERROR=5 WARN=7 INFO=9 DEBUG=3`. 워커 정지·터미널 종료를 확인했다.
  - 한계: 작은 과제 3개·effort 1개다. 큰 입력, 10만 토큰 초과 입력, 쿼터 절감은 측정하지 않았다. 같은 claude
    구독에서 Haiku 가 실패한 뒤 Sonnet 을 부르면 총 쿼터가 늘 수 있다(D-99 소수의견). 선두 승격이나 Sonnet 5.5
    제외는 별도 비교 근거가 필요하다. 상태는 `pending-transport-and-certificate` 이고 Orca 런치 계정/과금 인증서
    전까지 준비된 경로로 보지 않는다. 모델 포함·초과과금 OFF·API 폴백 OFF·G5·런치 인증서 게이트는 기존 flag
    레인과 똑같이 걸린다(`test_orchestrate.py`·`test_execute_orca.py` 의 D-99 테스트).
- **D-98(2026-10-12, 2.16.0): 보안 생성물 게이트를 `gpt-6.1-sol` @xhigh 로 옮겼다**(허브 토론
  `dbt-261012-124530`, quick, PROVISIONAL 3/4, 심판 확신도 91). OpenAI 가 `gpt-daybreak-blue-latest` 별칭을
  deprecated 로 표시했고(종료일·대체 ID 미공지), 이 계정 Codex 카탈로그는 아직 list·cyber 로 싣지만 다른 cyber
  모델이 없다. 레지스트리의 `lifecycle: deprecated` 와 `constrain_runtime` 의 `MODEL_NOT_ACTIVE` 는 그대로다.
  `legacy_lane_migration` 의 `gpt-daybreak-blue-latest` 는 `keep-security-pin-resolve-per-run` 에서 후보
  `gpt-6.1-sol`, `pending-transport-and-certificate` 로 바뀌었다(후보 레인과 같은 상태). 옛 키는 원장 호환용으로
  `LANES` 에 남고, 새 계획에 넣으면 `validate_plan` 이 `LANE_DEPRECATED` 로 막는다.
  - 지킨 것: G1(코딩은 claude 전용, 게이트는 codex), G1_SEC_SAME_MODEL(생성물 게이트 `gpt-6.1-sol` 과 인가
    게이트 `gpt-6-astra` 는 다른 모델). 잃은 것: cyber 전용성. 방어 루브릭·출력 형식·fail-closed 규칙(빈 출력,
    차단·거절, 첫 줄 누락, 모호한 판정은 FAIL)과 재승격 규칙은 `references/security-artifact-gate.md` 에 있다.
    이 규칙은 게이트 출력을 읽는 쪽이 적용하며 스크립트가 출력을 파싱하지는 않는다.
  - canary(오케스트레이터 실행, 12:53~12:55 KST, 같은 Orca run, dispatch `ctx_ff39c4a979ba`, 읽기 전용 워커 1개,
    도구 금지): `launch.requested` == `launch.effective`(`gpt-6.1-sol`, xhigh), Codex rollout(originator
    `codex-tui`, CLI 0.162.1)의 `turn_context` 가 `gpt-6.1-sol`/xhigh 였다. 결함 4개와 안전한 함수 2개를 심은
    Python 생성물에 `GATE: BLOCK` 으로 답하고 CWE-89·CWE-78·CWE-22·CWE-502 를 정확히 보고했으며 안전한 함수에는
    발견을 내지 않았다. 출력은 비거나 차단되지 않았다. 자기보고 모델명은 `gpt-6` 으로 틀렸다. 워커 정지·터미널
    종료를 확인했다. 심은 샘플 1건이라 cyber 전용 모델과 동등하다는 증명이 아니다.
  - 부작용: 생성물 게이트와 코디네이터가 같은 `gpt-6.1-sol` 이라 코딩 라운드마다 `coordinator_conflict()` 가
    참이다(경고이며 디스패치를 막지 않는다). D-98 은 코디네이터를 바꾸지 않았다.
  - 이 이전은 같은 날 오후 D-101 이 뒤집었다(다음 항목). 루브릭·출력 형식·fail-closed 규칙과 이 canary 기록은 남는다.
- **D-101(2026-10-12, 2.17.0, Simon 지시, 토론 없음): GPT 쪽은 `gpt-6-astra` @xhigh 만 쓰고, 생성물 게이트는
  Daybreak 로 되돌렸다.** 지시 원문: "gpt 6.1 sol은 너무 느려서 빼기로 결정. 기획단계 gpt astra xhigh와 opus 5.5.
  단순작업 sonet 5.5", "보안게이트는 데이브레이크로 할려했는데 그게 안돼면 opus 5.5로 하자.", "gpt 쪽은 astra 말고는
  쓰지마. gpt 를 넣어야한다면 astra xhigh."
  - 철회된 레인 다섯: `gpt-6.1-sol`, `gpt-6-luna`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`. registry 상태는
    `held-withdrawn-by-owner` 다. 후보는 일이 간 곳이다: sol 계열과 terra 는 `gpt-6-astra`, luna 두 건은 A 클래스를
    받은 `claude-haiku-5-5`. 레인 키는 원장 호환용으로 `LANES` 에 남고, 새 계획에 넣으면 `validate_plan` 이
    `LANE_WITHDRAWN`(계획기에서는 `ORCA_LANE_WITHDRAWN`)으로 막는다. 예외 자리는 없다. **결함 때문이 아니다**:
    `gpt-6-luna` 는 D-91 canary 를, `gpt-6.1-sol` 은 D-67·D-98 canary 를 통과했고 다섯 모델의 제공사 lifecycle 은
    active 그대로다. 재개 조건: Simon 의 명시 지시나 별도 결정 기록, 그리고 같은 읽기 전용 canary 의 재통과.
  - `gpt-6-astra` 는 codex 벤더에서 일을 받는 유일한 레인이고 effort 는 xhigh 고정이다(사다리 std = top = xhigh,
    off-ladder 로도 다른 값 불가). 코디네이터도 `gpt-6-astra` @xhigh 다. astra 는 인가 게이트이자 B·A-verify
    1순위라 코딩 라운드와 대부분의 B 라운드에서 `coordinator_conflict()` 가 참이다(경고이며 디스패치를 막지 않는다).
    codex 가 80% 를 넘으면 2순위 `claude-fable-5-1` 로 강등된다. effort 를 낮추거나 다른 GPT 레인으로 가지 않는다.
  - 목록: A = `claude-haiku-5-5` → `claude-sonnet-5-5` → `claude-opus-5-5`(전부 claude 라 claude 가 한도에 닿으면
    A 작업은 멈춘다. codex 폴백이 없다). C-realtime = `grok-4.6` → `claude-opus-5-5` → `gpt-6-astra`. C-platform =
    `gemini-3.8-flash` → `claude-opus-5-5` → `gpt-6-astra`. B·A-verify·D·코딩은 그대로다. Haiku 를 Sonnet 앞에 둔 것은
    오케스트레이터의 권고이고 Simon 이 반대하지 않았다.
  - 생성물 게이트는 `gpt-daybreak-blue-latest` @xhigh 다. `legacy_lane_migration` 의 그 항목은 후보 자기 자신,
    `keep-security-pin-resolve-per-run` 으로 돌아갔다. 제공사의 deprecated 표시, 레지스트리의 `lifecycle: deprecated`,
    `constrain_runtime` 의 `MODEL_NOT_ACTIVE` 는 그대로다. 그래서 이 레지스트리를 쓰는 중앙 계획기 경로에서는 게이트
    후보가 계속 막힌다. 레인 표만 한 자리를 연다: 고정 공정 `security-artifact-gate`, 고정 effort xhigh. 그 밖(우선순위
    목록, 코딩, 다른 공정, 재시도, 다른 effort)은 `LANE_DEPRECATED` 그대로다.
  - canary(오케스트레이터 실행, 15:19~15:20 KST, Orca run `run_b08adccb4ec8`, dispatch `ctx_41243c1a0d26`, 읽기 전용
    워커 1개, 도구 금지): `launch.requested` == `launch.effective`(`gpt-daybreak-blue-latest`, xhigh), Codex rollout
    (originator `codex-tui`, CLI 0.162.1)의 `turn_context` 가 같은 값이었다. D-98 과 같은 결함 4개 샘플에
    `GATE: BLOCK` 으로 답하고 CWE-89·CWE-78·CWE-22·CWE-502 를 정확히 보고했으며 안전한 함수 2개에는 발견을 내지
    않았다. 출력은 비거나 차단되지 않았고 약 30초가 걸렸다. 자기보고 모델명은 `GPT-5` 로 틀렸다. 워커 정지·터미널
    종료를 확인했다. 심은 샘플 1건이다. 별칭은 예고 없이 사라질 수 있다.
  - canary 를 돌리지 않은 것: 코디네이터로서의 `gpt-6-astra`, A 클래스 순서 변경. Haiku 5.5 의 근거는 D-99 의 정답이
    정해진 A 과제 3개, Sonnet 5.5 의 근거는 D-91 canary 가 전부다.
  - (그 시점의 미결) Simon 이 말한 게이트 폴백 `claude-opus-5-5` 는 구현하지 않았다. 코딩이 `claude-opus-5-5` 라 같은 모델이
    자기 산출물을 검사하게 되어 G1 과 충돌한다.
  - **D-102(2026-10-12, 2.18.0, Simon 판정)가 그 미결을 정했다**: 고정 레인이 설 수 없을 때만 `gpt-6-astra` @xhigh 가
    생성물 게이트를 맡는다(`routing.FIXED_FALLBACKS`). 그 상태 하나에서만 `G1_SEC_SAME_MODEL` 을 면제하고 G1 은 그대로다.
    레지스트리 값은 바꾸지 않았다(`gpt-daybreak-blue-latest` 는 `deprecated`, 계획기는 계속 `MODEL_NOT_ACTIVE`). 그 거부가
    곧 폴백 사유가 되어, packaged registry 경로에서는 지금 `gpt-6-astra` 가 게이트를 맡는다. 조건·실행 전 규칙·canary
    (run `run_3607f8833d7e`)는 `references/security-artifact-gate.md` 에 있다.
  - shadow task-fit 정책(`2026-10-12-shadow.2`)도 같은 지시로 바꿨다: GPT 행은 `gpt-6-astra` 의 xhigh 뿐이고,
    CODE_SIMPLE 은 `claude-haiku-5-5` → `claude-sonnet-5-5` → `claude-opus-5-5` 다. Sonnet 5.5 가 돌아온 것은 지시
    때문이지 D-90 재진입 조건(Artificial Analysis 재측정)이 충족돼서가 아니다.
- `legacy_lane_migration` 15건 중 6건이 `pending-*`, 5건이 `held-*`, 4건이 `keep-*` 다. `pending-*` 는
  `claude-opus-5-5`·`claude-opus-5`·`claude-sonnet-5-5`·`claude-sonnet-5`·`claude-haiku-5-5`(인증서 대기)와
  `grok-4.6` → `grok-4.7`(Orca 가 grok 모델을 고정하지 못한다)이다. `held-*` 는 위 D-101 의 철회 다섯 건이다
  (`gpt-5.6-terra` 의 등급 평가는 대상 `gpt-6.1-sol` 이 철회돼 더 진행하지 않는다). `keep-*` 4건은 자기 모델
  그대로다: `claude-fable-5-1`, `gpt-6-astra`, `gemini-3.8-flash`, 그리고 D-101 로 돌아온 `gpt-daybreak-blue-latest`.
- 그래서 planner 는 여전히 `gpt-6-sol`, `grok-4.7`, `grok-4.5` 로의 Orca 발주를
  `ORCA_UNREGISTERED_PROCESS_OR_MODEL` 로 막는다. `claude-sonnet-5-5`·`claude-haiku-5-5` 는 등록된 레인이라
  그 코드가 아니라 다음 게이트(G5·$0·런치 인증서)에서 멈추고, 철회된 `gpt-6-luna`·`gpt-6.1-sol` 은 `ORCA_LANE_WITHDRAWN`
  에서 멈춘다. 레인을 더 바꾸려면 Orca canary 와 `/ai-debate` 를 거친 별도 결정이나 Simon 의 명시 지시가 필요하다.
  Orca 밖 guarded adapter 는 자기 계정·과금·effort 게이트를 그대로 적용한다. D-101 의 "GPT 는 astra 만" 은 레인 표·
  codex 직행 argv·평가 문제·shadow task-fit 에 걸려 있고, Orca 밖 경로(host·direct CLI)의 후보 선택에는 걸려 있지
  않다. 그 경로는 호스트가 준 runtime 후보와 레지스트리(제공사 사실)로만 고른다.

### D-104 (2026-10-18): `gemini-4-argon` 은 등록만, 레인은 없다

`gemini-4-argon` 은 2026-10-13 Gemini API GA 라 2026-10-18.1 레지스트리에 등록했지만 `routing.py` 레인은 없다. 그래서 계획에 넣으면 지금처럼 `ORCA_UNREGISTERED_PROCESS_OR_MODEL` 로 막힌다. 이유는 둘이다. Orca 의 antigravity 에이전트는 기동 때 모델을 고를 수 없고(D-28 #12), agy CLI 직행 실행기도 없다. 실행기를 만들더라도 다른 실행기처럼 코디네이터 인증서(모델 포함·남은 쿼터·초과 과금 OFF·API 폴백 OFF)가 있어야 돌고, Antigravity 초과 과금 여부는 아직 확인하지 못했다. 허브 토론 D-104 를 다시 연 판정이 이 순서(먼저 인증서 경로 확인)를 정했다. 지금 Argon 이 실제로 쓰이는 곳은 ai-debate 의 Gemini 좌석(`gemini-4-argon-high`, ai-debate 0.2.8)이다. 2026-10-18 canary 두 건(화면 녹화 검토, 심어 둔 주장 10개 대조)은 통과했지만 둘 다 n=1 합성 표본이다.

## Refresh record (2026-10-18)

시각은 모두 KST 다. 이 재확인 자체는 모델·Bot·유료 API 호출 0회다(출처 읽기는 하위 에이전트가 curl 로 했고,
CLI 는 목록·버전·도움말만 읽었다). 같은 날 따로 돈 Argon canary(agy 3회, Codex 1회)와 허브 토론 D-104 는 이 기록의 근거가 아니다.

| 근거 | 관측 | 결과 |
| --- | --- | --- |
| Codex `~/.codex/models_cache.json` | `fetched_at` 2026-10-18T00:27:34Z(09:27:34), 클라이언트 0.162.1 | 10개 slug(10-12 11개): 숨김 `gpt-5.5` 가 빠졌다(10-12 캐시의 10-14 19:00Z 은퇴 예고대로). 우선순위 1 `gpt-6.1-sol`, Daybreak alias 는 목록에 그대로(우선순위 11). 등록된 slug 의 effort 는 10-12 와 같다 |
| `~/.grok/models_cache.json`, `grok --no-auto-update models` | `fetched_at` 00:25:29Z(09:25:29), 09:27:57 실행 뒤에도 같다 | 그대로: `grok-4.7`(기본)·`grok-4.7-build-fast`·`grok-4.6`·`grok-4.5`. 목록만 읽었다 |
| `codex --version`, `grok --no-auto-update --version`, `agy --version`, `claude --version` | 09:27:57 | Codex 0.162.1·grok 1.0.46 은 10-12 와 같다. agy 1.4.1(10-12 1.3.3), Claude Code 2.1.302(10-12 2.1.296) |
| `agy models`(`AGY_CLI_DISABLE_AUTO_UPDATE=true`) | 09:11:29, 09:28:05 | 13개 이름(10-12 18개). `gemini-4-argon-low/medium/high` 가 새로 생겼고 `gemini-3.1-pro-*` 2개·`gemini-3.7-flash-*` 3개·`gemini-3.6-flash-*` 3개가 빠졌다. `--model gemini-3.1-pro-high` 는 0턴에 "not recognized as a known model" 로 거부된다 — ai-debate Gemini 좌석 기본값을 `gemini-4-argon-high` 로 바꾼 이유(ai-debate 0.2.8) |
| `claude --help` | 09:28 | `--effort` 는 low, medium, high, xhigh, max 그대로 |
| 레지스트리·task-fit 출처 36개(중복 제거) | 첫 요청 09:19:19 | 32개는 첫 요청 200. `ai.google.dev` 4개는 처음에 `oauth2authorize` 로 302 리다이렉트돼 쿠키를 받은 뒤 200(10-12 에는 전부 첫 요청 200). 불일치 2개: `gg_latest` 페이지가 Gemini 4 Argon 안내로 바뀌었고, task-fit 의 D-90 노트 한 구절이 AA 원문과 방향이 반대다(정책 D-103 노트에서 바로잡음). 확인 불가 2개(`gpt-5.6-terra`·`gpt-5.6-luna` 장문 cached)는 10-12 와 같다. Sonnet 5.5 는 바뀐 것이 없고 AA 는 재측정을 올리지 않았다 |
| Gemini 4 Argon 공식 페이지(모델 페이지·changelog·가격·thinking·Antigravity 글·모델 카드) | 같은 실행 | API ID `gemini-4-argon`(stable, preview ID 없음), 2026-10-13 GA, thinking low·medium·high(기본 medium), 통합 컨텍스트 1,048,576, 기본 출력 65,536(long decode 로 1,048,576 까지), 11-30 까지 $2 / $0.10 / $10 이고 12-01 부터 $4 / $0.20 / $20, 무료 등급 없음, Google Cloud 은퇴 2027-10-13 이후, 지식 기준 2026-03(모델 카드). Antigravity 글은 AI Pro·Ultra, blog.google 글은 Ultra 라고 적어 서로 다르다 |
| `model_watch.py status` | 09:28:25 | 새 후보 0. 대기 후보: Gemini 4 Argon 글 2건(이번에 등록), Claude Haiku 5.5 글 2건(10-12 등록), Grok 4.7, OpenAI 글 3건 |

바뀐 등록 사실.
- 새 모델 `gemini-4-argon`(active). 레인은 없다(위 "D-104" 절).
- `gemini-3.8-flash` 의 출처 `gg_latest` 를 `whats-new-gemini-3.8` 로 옮기고 `source_updated_at` 을 그 페이지의 2026-10-13 으로 고쳤다. effort·가격·GA 상태는 그대로다.
- `gemini-3.1-pro-preview` 는 API 에서 그대로 preview(종료일 공지 없음)라 값을 바꾸지 않았다. agy 목록에서만 빠졌다.

레지스트리 `checked_at` 은 실제로 쓴 근거 중 가장 이른 시각인 출처 첫 요청 2026-10-18 09:19:19 라 사실은
2026-10-25 09:19:19 KST 에 만료된다. task-fit 정책도 같은 실행에서 자기 출처를 읽어 같은 구간이다.

## Refresh record (2026-10-12)

시각은 모두 KST 다. 모델·Bot·유료 API 호출은 0회다(프롬프트를 보내지 않았고 Orca 워커도
띄우지 않았다). 2026-10-06(2.15.6, 12:45~12:58) 표는 커밋 `28fe12a` 의 이 파일에, 10-05(2.15.3,
14:17~14:20) 표는 커밋 `c108714` 의 이 파일에, 10-04 2차(2.15.2, 21:46~21:59) 표는 PR #126 의 이 파일에,
1차(2.14.1, 13:05~13:16) 표는 PR #114 커밋 `e407918` 의 이 파일에, 요약은 각 changelog 항목에 있다.

이번에는 등록된 제공사 사실 3개가 바뀌어 레지스트리 값을 고쳤다(아래 "바뀐 등록 사실").

| 근거 | 관측 | 결과 |
| --- | --- | --- |
| Codex `~/.codex/models_cache.json` | `fetched_at` 2026-10-12T02:44:21Z(11:44:21), 캐시 클라이언트 0.162.0(10-06 은 0.160.0) | 그대로: 11개 slug, 우선순위 1 `gpt-6.1-sol`, 등록된 slug 는 모두 low~max(`ultra` 는 같은 여섯 개), `none` 은 어디에도 없다. 미등록 `gpt-5.5` 는 숨김 그대로이고 `upgrade` 항목에 2026-10-14T19:00Z 은퇴와 대체 `gpt-6.1-sol` 이 적혀 있다. `gpt-daybreak-blue-latest` 는 공개 목록(우선순위 11)에 그대로 있고 은퇴 표시가 없다 |
| `~/.grok/models_cache.json` | 11:47:04·11:47:31 에 본 사본의 `fetched_at` 은 02:43:08Z(11:43:08)다. 아래 `grok models` 는 캐시가 새로워 다시 받지 않았고(11:47:37 에 `fetched_at`·etag 그대로, etag 는 10-06 과도 같다), 내용 대조는 이 사본으로 했다 | 그대로: 4.7·4.7-build-fast·4.6 은 low~xhigh, 4.5 는 low~high, 기본 high, 256K·500K 창 |
| `codex --version`, `grok --no-auto-update --version`, `agy --version`, `claude --version` | 11:47:31 | grok 1.0.46 은 10-06 과 같다. Codex 0.162.1(10-06 0.160.0), agy 1.3.3(10-06 1.2.17), Claude Code 2.1.296(10-06 2.1.290) |
| `grok --no-auto-update models` | 11:47:31 | 그대로: `grok-4.7`(기본), `grok-4.7-build-fast`, `grok-4.6`, `grok-4.5`. 목록만 읽었고 프롬프트는 보내지 않았다 |
| `agy models`, `AGY_CLI_DISABLE_AUTO_UPDATE=1` | 11:47:34 | 그대로: 18개 이름. Gemini API 에서 10-08 에 폐기된 `gemini-3.7-flash` 의 세 이름도 그대로 나온다(위 대응표). agy 1.3.3 은 값 `1` 을 무시하고 `true` 만 인정한다(같은 날 main 의 위젯 수정 `a8fc7d7`). 이번 호출은 agy 로그에 "Last check was less than 15 minutes ago, skipping update" 가 남았고 업데이터는 뜨지 않았다 |
| `claude --help` | 11:47:37 | `--effort` 는 여전히 low, medium, high, xhigh, max |
| `runtime_collect.py --surface codex --surface grok` (메타데이터 전용) | 11:47:53~11:47:57 | 10-06 과 같다: Codex app-server 공개 목록 8개(숨김 `gpt-5.5`·`gpt-reserve`·`codex-auto-review` 제외)의 effort 가 캐시와 같고 Grok 은 모델 4개다. 등록 모델 후보는 Codex 8개·Grok 3개. 둘 다 구독 모드. 턴 0회 |
| 레지스트리 출처 28개 | 11:48:31~11:48:51, 전부 첫 요청에 HTTP 200(10-06 과 같은 브라우저형 User-Agent·Accept 헤더, 재시도 0) | 등록 모델 18개, 사실 필드 232개. 고치기 전: 일치 227, 불일치 3, 확인불가 2. 불일치 3개(아래 "바뀐 등록 사실")를 고친 뒤: 일치 230, 불일치 0, 확인불가 2(`gpt-5.6-terra`·`gpt-5.6-luna` 장문 cached_input — 모델 페이지는 "2x input and 1.5x output"만 적고 가격 페이지에 행이 없다. 같은 문구의 `gpt-5.6-sol` 은 가격 페이지 Cyber models 표에 장문 cached $0.80 이 명시돼 유추로 유지) |
| task-fit 출처 9개 | 11:48:51~11:48:55, 전부 첫 요청에 HTTP 200(openai.com Astra 포함) | 인용 주장 3개 그대로(Opus 5.5 기본 effort 의 FrontierCode 결과, AA 의 medium 프런티어, AA 지수에서 GPT-6.1 Sol 이 Astra 보다 1점 아래). D-90 근거(AA: Sonnet 5.5 는 비용 프런티어 밖, Terminal-Bench 4.0 64%)도 그대로이고, AA 는 재측정을 아직 올리지 않았다("we will be re-running relevant evaluations soon"). 순위·effort 그대로 |
| 폐기 페이지·모델 목록 6개(OpenAI·Google·xAI) | 11:48:55~11:48:59, 전부 첫 요청에 HTTP 200 | OpenAI 모델 목록에서 Daybreak Blue·Red alias 항목이 빠졌다(폐기 페이지의 최신 공지는 10-01 그대로이고 이 alias 의 날짜 공지는 없다). Google changelog 10-08: `gemini-3.7-flash`·`gemini-3.5-flash` 폐기(3.8·3.6 Flash 로 자동 전환). 10-06: `gemini-nano-banana-2.1` GA, `gemini-3.1-flash-image` 폐기. `gemini-3.8-flash`·`gemini-3.1-pro-preview` 는 종료 일자 없음. xAI 릴리스 노트의 최신 항목은 10-02 그대로이고 모델 목록도 같다 |
| 43개 페이지 본문(태그 제거 텍스트) | 10-06 12:50 사본과 줄 단위 비교 | 1개만 같다(openai.com Astra 발표문). 나머지 42개의 차이는 대부분 사이트 메뉴와 미등록 모델 내용이다: OpenAI 문서 메뉴 개편과 사용 등급 5→3단계, Claude 문서의 Haiku 5.5 추가, xAI 문서 제목·메뉴, Google 문서의 3.7·3.5 Flash 삭제와 Last updated 2026-10-09, AA 글 옆의 최근 글 목록. 등록 사실에 닿는 차이는 아래 3개뿐이다 |
| `model_watch.py scan --force` | 11:56:42~11:56:45. 상태 파일의 사본에 `--state` 로 실행해 `%LOCALAPPDATA%\SimonK\vibe\model-watch.json` 은 읽기만 했다(sha256 이 실행 전후 같다) | 새 후보 0·오류 0, 바뀐 출처는 xai(원본의 마지막 스캔 11:21:04 이후). 대기 후보: Claude Haiku 5.5 2건·Gemini 4 Argon·OpenAI 글 3건(공식 검토 대기), GPT-6.1 Sol(모니터링) |
| 후보 확인용 공식 페이지 8개(Anthropic 뉴스·Haiku 5.5 발표문, Claude Haiku 5.5·4.5 개요, Google 모델 블로그·Gemini 4 Argon 글, x.ai 뉴스, OpenAI 뉴스 RSS) | 11:57:08~11:57:13, 전부 첫 요청에 HTTP 200 | Haiku 5.5 는 2026-10-07 출시·Active 로 확인했다. Gemini 4 Argon 은 신뢰 테스터(cyber defenders) 대상 단계 공개라 개발자 API 에 없다. x.ai 뉴스에 Grok 5 가 없다. OpenAI 뉴스에 10-06 이후 새 API 모델 발표가 없다 |

필드 수는 `models` 항목의 모든 값에서 `sources`·`surface`·`vendor`·`id_namespace`·`pricing.scope` 를 빼고
센 것이다. 목록(`api_efforts`·`aliases`)은 한 필드, 장문 구간은 값마다 한 필드다. 이 가운데 34개는 null
또는 빈 값(제공사 별칭 미수집 15, 기본 `cache_write` 10, 장문 `cache_write` 7, Daybreak 의 `api_efforts`·
`pricing` 2)이고 레지스트리 규약대로 일치로 셌다. 10-06 과 같은 정의라 두 번의 수(232개)를 바로 비교할 수 있다.

바뀐 등록 사실 3개(레지스트리 값을 고쳤다).
- `claude-sonnet-5-5` 의 `pricing.cached_input` 0.2 → 0.1. Anthropic 이 2026-10-07 에 Sonnet 5.5 캐시 읽기를
  $0.20 → $0.10/MTok 으로 내렸다. 가격표("Hits and refreshes" $0.10, "0.05x on Claude Opus 5.5 and Claude Sonnet
  5.5"), Sonnet 5.5 개요("Cache read $0.10 / MTok"), Haiku 5.5 발표문("Cache reads now cost 50% less")이 같다.
  입력 $2·출력 $10·캐시 쓰기 $2.50/$4 는 그대로다.
- `gpt-daybreak-blue-latest` 의 `lifecycle` active → deprecated. 모델 페이지에 Deprecated 배지가 붙고 안내문이
  "This alias is deprecated, please use the latest cyber model available to you" 로 바뀌었으며 모델 목록에서 빠졌다.
  종료 일자와 대체 ID 는 공지되지 않았고 스냅샷 표의 대상은 여전히 `gpt-5.6-sol` 이다. `constrain_runtime` 은
  이제 이 alias 후보를 `MODEL_NOT_ACTIVE` 로 막는다. `legacy_lane_migration` 의
  `keep-security-pin-resolve-per-run` 과 `routing.py` 의 보안 레인은 바꾸지 않았다. 보안 게이트를 어느 모델로
  옮길지는 `/ai-debate` 를 거친 별도 결정이나 Simon 의 명시 지시가 필요하다.
  → 같은 날 D-98(2.16.0)이 게이트를 `gpt-6.1-sol` @xhigh 로 옮겼고, 오후에 D-101(2.17.0, Simon 지시)이
  `gpt-daybreak-blue-latest` @xhigh 로 되돌렸다(위 "Lane migration pending"). 제공사 사실(deprecated)은 그대로다.
  이 갱신 기록은 11:43~11:57 시점 그대로 둔다.
- `gemini-3.8-flash` 의 `source_updated_at` 2026-09-23 → 2026-10-09(latest-model 페이지의 Last updated). 가격·
  thinking level·GA 상태는 그대로다.

제거·개명된 등록 모델은 없다. 아래는 관측만 적는다(레지스트리 값·레인·라우팅은 그대로).
- **새 GA 모델 Claude Haiku 5.5(`claude-haiku-5-5`).** 2026-10-07 출시, Active(은퇴는 2027-10-07 이후), effort
  low~max(기본 medium), adaptive thinking, 1M 컨텍스트·128K 출력. 가격은 프롬프트 10만 토큰 이하 $0.10/$0.50,
  초과 $0.50/$2.50(캐시 읽기 $0.01/$0.05)이다. Claude Code 는 2.1.293 이상이 필요하다. 등록하지 않았고 레인도
  없다. 등록하려면 10만 토큰 기준 가격 구간을 어떻게 담을지와 레인 여부를 따로 정해야 한다.
  → 같은 날 D-99(2.16.0)가 등록하고 A 클래스 레인으로 넣었다(위 "Lane migration pending"). 그래서 지금 등록
  모델은 19개다. 위 표의 18개·232개는 11:48 시점의 수이고 Haiku 5.5 의 사실 필드는 그 수에 들어 있지 않다.
- 미등록 `claude-haiku-4-5` 는 Legacy 로 내려갔고 은퇴 하한(2026-10-15)은 그대로다(3일 남음).
- 이미지 모델 `gemini-nano-banana-2.1` 이 10-06 에 GA 가 됐다(task-fit 정책은 이미지 생성을 다루지 않는다).
  Gemini 4 Argon 은 Google 블로그에 발표됐지만 Gemini API 문서(모델 목록·changelog·가격·폐기)에 없다.
  Grok 5 는 xAI 문서·뉴스에 없다.
- `gpt-6.1-sol` 에 Ultrafast 모드(Standard 의 6배, 10-08)가 생겼다. 레지스트리는 Standard 가격만 담아 값은 그대로다.
  OpenAI API 사용 등급은 5단계에서 3단계로 바뀌었고, 가격표 Life sciences 표에 `gpt-rosalind-discovery` 행이 생겼다.
- AA 의 Sonnet 5.5 글은 캐시 읽기를 인하 전 $0.2 로 적는다. 재측정이 올라오면 D-90 재진입 조건을 다시 본다.
- `gpt-5.6-sol` 할인가 기한(11-21)과 장문 구간 `cache_write: null` 은 10-06 과 같다. Gemini 가격표의 3.1 Pro
  200k 구간 값은 이번에도 HTML 원문에서 $4.00·$18.00·$0.40 을 확인했다.

레지스트리 `checked_at` 은 실제로 쓴 근거 중 가장 이른 시각인 Grok 모델 캐시 수신
2026-10-12 11:43:08(초 미만 버림)이라 사실은 2026-10-19 11:43:08 KST 에 만료된다(Codex 캐시 수신 11:44:21 은
그보다 늦다). task-fit 정책은 자기 출처를 처음 읽은 11:48:51 부터 2026-10-19 11:48:51 KST 까지 유효하다.

## Repeating the refresh

1. Codex 모델 캐시와 Grok 모델 캐시의 `fetched_at` 을 읽고, `grok --no-auto-update models` 와
   자동 업데이트를 끈 `agy models`(`AGY_CLI_DISABLE_AUTO_UPDATE=true`. agy 1.3.3 은 값 `1` 을 무시한다)를
   실행하고, `claude --help` 를 읽는다. `grok models` 가 Grok
   캐시를 다시 받아 `fetched_at` 을 바꿀 수 있으니 캐시 내용 대조는 그 뒤 사본으로 하고, 쓴
   사본의 `fetched_at` 을 적는다. 원하면
   `runtime_collect.py --surface codex --surface grok` 로 app-server `model/list` 와 Grok ACP
   과금을 메타데이터만 읽는다. 프롬프트는 보내지 않는다.
2. 레지스트리·task-fit 출처를 모두 HTTPS 로 다시 읽고 ID·effort·가격·구간·은퇴 일자를 JSON 과
   대조한다. 폐기 페이지와 `model_watch.py status` 의 대기 후보도 본다.
3. `checked_at` 은 실제로 쓴 관측 중 가장 이른 시각으로 둔다(캐시라면 그 `fetched_at`). 더 늦은
   시각은 쓰지 않는다. 그다음 `test_model_registry.py`, `test_runtime_collect.py`,
   `test_orchestrate.py` 를 돌린다.

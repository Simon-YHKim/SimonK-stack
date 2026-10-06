# Model catalog map — CLI names, registry IDs and the 2026-10-06 refresh

## Contents

- CLI name map
- Registered legacy entries
- Lane migration pending
- Refresh record (2026-10-06)
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
| `antigravity` | `gemini-3.8-flash-high` | `gemini-3.8-flash` | `high` | thinking level high |
| `antigravity` | `gemini-3.8-flash-medium` | `gemini-3.8-flash` | `medium` | API default level |
| `antigravity` | `gemini-3.8-flash-low` | `gemini-3.8-flash` | `low` | |
| `antigravity` | `gemini-3.1-pro-high` | `gemini-3.1-pro-preview` | `high` | preview, so `MODEL_NOT_ACTIVE` |
| `antigravity` | `gemini-3.1-pro-low` | `gemini-3.1-pro-preview` | `low` | agy lists no medium |
| `antigravity` | `gemini-3.7-flash-high` | `unregistered` | `-` | older Flash |
| `antigravity` | `gemini-3.7-flash-medium` | `unregistered` | `-` | older Flash |
| `antigravity` | `gemini-3.7-flash-low` | `unregistered` | `-` | older Flash |
| `antigravity` | `gemini-3.6-flash-high` | `unregistered` | `-` | older Flash |
| `antigravity` | `gemini-3.6-flash-medium` | `unregistered` | `-` | older Flash |
| `antigravity` | `gemini-3.6-flash-low` | `unregistered` | `-` | older Flash |
| `antigravity` | `claude-opus-5-5-low` | `unregistered` | `-` | Anthropic model on the Google surface; the schema binds antigravity to Google |
| `antigravity` | `claude-opus-5-5-medium` | `unregistered` | `-` | same |
| `antigravity` | `claude-opus-5-5-high` | `unregistered` | `-` | same |
| `antigravity` | `claude-sonnet-5-5-low` | `unregistered` | `-` | same |
| `antigravity` | `claude-sonnet-5-5-medium` | `unregistered` | `-` | same |
| `antigravity` | `claude-sonnet-5-5-high` | `unregistered` | `-` | same |
| `antigravity` | `gpt-oss-120b-medium` | `unregistered` | `-` | not a Google model |
| `grok` | `grok-4.7-build-fast` | `unregistered` | `-` | Grok 4.7 on faster serving at 2x standard token rates (1.5x long context), Cursor and Grok Build only, not on the public xAI API. Not for default routing |
| `claude` | `claude-haiku-4-5-20251001` | `unregistered` | `-` | Claude docs: default effort "Not supported", so it cannot satisfy the registry's explicit effort list; retirement not sooner than 2026-10-15 |
| `codex` | `gpt-5.5` | `unregistered` | `-` | in the Codex models cache with efforts up to xhigh; previous generation. Hidden in the Codex catalog as of 2026-10-06 (public on 2026-10-04) |
| `codex` | `gpt-reserve` | `unregistered` | `-` | hidden in the Codex catalog |
| `codex` | `codex-auto-review` | `unregistered` | `-` | hidden in the Codex catalog |

## Registered legacy entries

- `grok-4.5` is a public xAI API model, so it is registered as `generation: legacy`
  with `low`, `medium`, `high`. Its model page lists `xhigh`, but the reasoning
  guide says grok-4.5 treats `xhigh` as `high`, and its release note and grok CLI
  1.0.46 list three levels; the conservative set wins.
- `claude-opus-5` and `claude-sonnet-5` are labelled Legacy on their Claude
  overview pages and Active in the deprecation table, so they keep
  `lifecycle: active` and carry `generation: legacy`, like `gpt-5.6-*` and `grok-4.6`.
- registry 에 등록됐다고 Orca 레인이 생기지는 않는다(D-67 과 2026-10-05 Simon 지시로 추가된 네 레인은 아래 절).
  shadow task-fit 정책은 현행 Claude/Codex 모델만 든다. 자기 게이트를 통과한
  Orca 밖 경로는 legacy 모델을 고를 수 있다. `constrain_runtime` 이
  `generation: legacy` 를 후보에 복사하고, planner 는 그 값을 resource rank 와
  80% 쿼터 가드 다음, 쿼터 비율 앞에서 본다. 그래서 순위가 같으면 legacy 모델은
  현행 모델에 진다. 현행 모델이 쿼터를 더 썼어도(80% 미만) 마찬가지다.

## Lane migration pending

D-67(2026-10-04, 허브 토론 `dbt-261004-033902`, ADD_ALONGSIDE_KEEP_LEGACY)에 따라
2.14.0 은 Orca 레인 두 개를 옛 레인 **옆에** 추가했다. 근거는 Orca 1.4.218 번들의
검증 코드를 읽은 것이며 모델 호출·worker-start 는 0회다. 2.15.5 는 2026-10-05 Simon 지시로
A 클래스 레인 두 개를 같은 방식으로 더했다(표의 아래 두 줄, 이 변경에서도 모델 호출·worker-start 0회).

| 새 레인 | 전달 | Orca 1.4.218 이 받는 effort | 정책 std / top | registry 상태 |
| --- | --- | --- | --- | --- |
| `claude-opus-5-5` | `--effort` 플래그 | low~max (claude 카탈로그에 없는 정식 id) | high / max | `pending-transport-and-certificate` |
| `gpt-6.1-sol` | `--effort` 플래그 | minimal~xhigh (codex 미등록 모델 폴백, max·ultra 거부) | high / xhigh | `pending-transport-and-certificate` |
| `claude-sonnet-5-5` | `--effort` 플래그 | low~max (claude 카탈로그에 없는 정식 id) | medium / high (xhigh·max 는 정책 밖) | `pending-transport-and-certificate` |
| `gpt-6-luna` | `--effort` 플래그 | minimal~xhigh (codex 미등록 모델 폴백, max·ultra 거부) | low / medium | `pending-transport-and-certificate` |

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
- `legacy_lane_migration` 14건 중 10건이 `pending-*` 이고 `held-*` 는 없다. 아직 레인을 옮기지 않은 이전
  대상은 `grok-4.6` → `grok-4.7`(Orca 가 grok 모델을 고정하지 못한다)이고, `gpt-5.6-terra` → `gpt-6.1-sol` 은
  같은 등급이 아니라 평가 보류다. `keep-*` 4건은 자기 모델 그대로다: `claude-fable-5-1`, `gpt-6-astra`,
  `gpt-daybreak-blue-latest`, `gemini-3.8-flash`.
- 그래서 planner 는 여전히 `gpt-6-sol`, `grok-4.7`, `grok-4.5` 로의 Orca 발주를
  `ORCA_UNREGISTERED_PROCESS_OR_MODEL` 로 막는다. `claude-sonnet-5-5`·`gpt-6-luna` 는 이제 등록된 레인이라
  그 코드가 아니라 다음 게이트(G5·$0·런치 인증서)에서 멈춘다. 레인을 더 바꾸려면 Orca canary 와
  `/ai-debate` 를 거친 별도 결정이나 Simon 의 명시 지시가 필요하다. Orca 밖 guarded adapter 는 자기
  계정·과금·effort 게이트를 그대로 적용한다.

## Refresh record (2026-10-06)

시각은 모두 KST 다. 모델·Bot·유료 API 호출은 0회다(프롬프트를 보내지 않았고 Orca 워커도
띄우지 않았다). 2026-10-05(2.15.3, 14:17~14:20) 표는 커밋 `c108714` 의 이 파일에, 10-04 2차(2.15.2,
21:46~21:59) 표는 PR #126 의 이 파일에, 1차(2.14.1, 13:05~13:16) 표는 PR #114 커밋 `e407918` 의
이 파일에, 요약은 각 changelog 항목에 있다.

| 근거 | 관측 | 결과 |
| --- | --- | --- |
| Codex `~/.codex/models_cache.json` | `fetched_at` 2026-10-06T03:46:47Z(12:46:47), 캐시 클라이언트 0.160.0(10-05 는 0.159.0) | 그대로: 11개 slug, 우선순위 1 `gpt-6.1-sol`, 등록된 slug 는 모두 low~max(`ultra` 는 같은 여섯 개), `none` 은 어디에도 없다. 바뀐 것은 미등록 `gpt-5.5` 가 `visibility: hide` 가 된 것뿐이다(위 대응표) |
| `~/.grok/models_cache.json` | 12:48:07 에 본 사본의 `fetched_at` 은 03:45:26Z(12:45:26)다. 아래 `grok models` 는 캐시가 새로워 다시 받지 않았고(12:49:01 에 `fetched_at`·etag 그대로), 내용 대조는 이 사본으로 했다 | 그대로: 4.7·4.7-build-fast·4.6 은 low~xhigh, 4.5 는 low~high, 기본 high, 256K·500K 창 |
| `codex --version`, `grok --no-auto-update --version`, `agy --version`, `claude --version` | 12:48:57 | Codex 0.160.0, grok 1.0.46 은 10-05 와 같다. agy 1.2.17(10-05 1.2.16), Claude Code 2.1.290(10-05 2.1.289) |
| `grok --no-auto-update models` | 12:48:57 | 그대로: `grok-4.7`(기본), `grok-4.7-build-fast`, `grok-4.6`, `grok-4.5` |
| `agy models`, `AGY_CLI_DISABLE_AUTO_UPDATE=1` | 12:48:58 | 그대로: 18개 이름(위 대응표와 같다) |
| `claude --help` | 12:49:01 | `--effort` 는 여전히 low, medium, high, xhigh, max |
| `runtime_collect.py --surface codex --surface grok` (메타데이터 전용) | 12:49:33~12:49:36 | Codex app-server 공개 목록 8개(숨김 `gpt-5.5`·`gpt-reserve`·`codex-auto-review` 제외)와 Grok 4개의 effort 가 캐시와 같다. 등록 모델 후보는 Codex 8개·Grok 3개. 둘 다 구독 모드. 턴 0회 |
| 레지스트리 출처 28개 | 12:50:25~12:50:44, 전부 첫 요청에 HTTP 200 | 등록 모델 18개, 사실 필드 232개: 일치 230, 불일치 0, 확인불가 2(`gpt-5.6-terra`·`gpt-5.6-luna` 장문 cached_input — 모델 페이지는 "2x input and 1.5x output"만 적고 가격 페이지에 행이 없다. 같은 문구의 `gpt-5.6-sol` 은 가격 페이지 Cyber models 표에 장문 cached $0.80 이 명시돼 유추로 유지). 레지스트리 값 변경 0 |
| task-fit 출처 9개 | 12:50:44~12:50:49, 전부 첫 요청에 HTTP 200(openai.com Astra 포함) | 인용 주장 3개 그대로(Opus 5.5 기본 effort 의 FrontierCode 결과, AA 의 medium 프런티어, AA 지수에서 GPT-6.1 Sol 이 Astra 보다 1점 아래). D-90 근거(AA: Sonnet 5.5 는 비용 프런티어 밖, Terminal-Bench 4.0 64%)도 그대로. 순위·effort 그대로 |
| 폐기 페이지·모델 목록 6개(OpenAI·Google·xAI) | 12:50:50~12:50:53, 전부 첫 요청에 HTTP 200 | 등록 모델 중 폐기·개명·제거 0, 10-05 이후 API GA 신규 0. OpenAI 최신 폐기 공지 10-01, Google changelog 09-22, xAI 릴리스 노트 10-02. `gemini-3.8-flash`·`gemini-3.1-pro-preview` 는 종료 일자 없음 |
| 43개 페이지 본문(태그 제거 텍스트) | 10-05 14:20 사본과 줄 단위 비교 | 39개 같다. 다른 4개는 등록 사실과 무관하다: Claude 모델 개요(Models API `line` 필드 설명 1줄), OpenAI changelog(10-05 HIPAA BAA 설정 항목), Anthropic Opus 5.5·Sonnet 5.5 발표문(사이트 메뉴) |
| model-watch 상태 파일(`%LOCALAPPDATA%\SimonK\vibe\model-watch.json`, 읽기만) | 12:58:11 | 마지막 스캔 09:00:01 은 새 후보 0·오류 0. 대기 후보 그대로: Gemini 4 Argon·GPT-6 가이드(공식 검토 대기), GPT-6.1 Sol(모니터링) |

필드 수는 `models` 항목의 모든 값에서 `sources`·`surface`·`vendor`·`id_namespace`·`pricing.scope` 를 빼고
센 것이다. 목록(`api_efforts`·`aliases`)은 한 필드, 장문 구간은 값마다 한 필드다. 이 가운데 34개는 null
또는 빈 값(제공사 별칭 미수집 15, 기본 `cache_write` 10, 장문 `cache_write` 7, Daybreak 의 `api_efforts`·
`pricing` 2)이고 레지스트리 규약대로 일치로 셌다. 10-05 의 162필드는 집계 정의가 남아 있지 않아 이번 수와
바로 비교할 수 없다.

제거·개명된 모델은 없다. 관측만 적는다(레지스트리 값은 그대로).
- Codex 카탈로그에서 미등록 `gpt-5.5` 가 숨김이 됐다. 등록 모델이 아니라 레지스트리와 라우팅은 그대로다.
- Sonnet 5.5 발표문은 여전히 Haiku 5.5 가 "coming weeks"에 온다고 적고, Claude 모델 개요에도 없다. GA 전이라
  등록하지 않는다. 미등록 `claude-haiku-4-5` 의 은퇴 하한(2026-10-15)은 9일 남았다.
- `gpt-5.6-sol` 할인가 기한(11-21)과 장문 구간 `cache_write: null` 은 10-05 와 같다.
- Gemini 가격표의 3.1 Pro 200k 구간 값은 `<=`·`>` 기호 때문에 태그 제거식 텍스트 추출에서 빠진다. HTML
  원문에서 $4.00·$18.00·$0.40 을 확인했다.

레지스트리 `checked_at` 은 실제로 쓴 근거 중 가장 이른 시각인 Grok 모델 캐시 수신
2026-10-06 12:45:26(초 미만 버림)이라 사실은 2026-10-13 12:45:26 KST 에 만료된다(Codex 캐시 수신 12:46:47 은
그보다 늦다). task-fit 정책은 자기 출처를 처음 읽은 12:50:44 부터 2026-10-13 12:50:44 KST 까지 유효하다.

## Repeating the refresh

1. Codex 모델 캐시와 Grok 모델 캐시의 `fetched_at` 을 읽고, `grok --no-auto-update models` 와
   자동 업데이트를 끈 `agy models` 를 실행하고, `claude --help` 를 읽는다. `grok models` 가 Grok
   캐시를 다시 받아 `fetched_at` 을 바꿀 수 있으니 캐시 내용 대조는 그 뒤 사본으로 하고, 쓴
   사본의 `fetched_at` 을 적는다. 원하면
   `runtime_collect.py --surface codex --surface grok` 로 app-server `model/list` 와 Grok ACP
   과금을 메타데이터만 읽는다. 프롬프트는 보내지 않는다.
2. 레지스트리·task-fit 출처를 모두 HTTPS 로 다시 읽고 ID·effort·가격·구간·은퇴 일자를 JSON 과
   대조한다. 폐기 페이지와 `model_watch.py status` 의 대기 후보도 본다.
3. `checked_at` 은 실제로 쓴 관측 중 가장 이른 시각으로 둔다(캐시라면 그 `fetched_at`). 더 늦은
   시각은 쓰지 않는다. 그다음 `test_model_registry.py`, `test_runtime_collect.py`,
   `test_orchestrate.py` 를 돌린다.

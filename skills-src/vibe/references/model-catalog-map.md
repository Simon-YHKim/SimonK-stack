# Model catalog map — CLI names, registry IDs and the 2026-10-04 refresh

## Contents

- CLI name map
- Registered legacy entries
- Lane migration pending
- Refresh record (2026-10-04, 2차)
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
| `codex` | `gpt-5.5` | `unregistered` | `-` | listed in the Codex models cache with efforts up to xhigh; previous generation |
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
- registry 에 등록됐다고 Orca 레인이 생기지는 않는다(D-67 로 추가된 두 레인은 아래 절).
  shadow task-fit 정책은 현행 Claude/Codex 모델만 든다. 자기 게이트를 통과한
  Orca 밖 경로는 legacy 모델을 고를 수 있다. `constrain_runtime` 이
  `generation: legacy` 를 후보에 복사하고, planner 는 그 값을 resource rank 와
  80% 쿼터 가드 다음, 쿼터 비율 앞에서 본다. 그래서 순위가 같으면 legacy 모델은
  현행 모델에 진다. 현행 모델이 쿼터를 더 썼어도(80% 미만) 마찬가지다.

## Lane migration pending

D-67(2026-10-04, 허브 토론 `dbt-261004-033902`, ADD_ALONGSIDE_KEEP_LEGACY)에 따라
2.14.0 은 Orca 레인 두 개를 옛 레인 **옆에** 추가했다. 근거는 Orca 1.4.218 번들의
검증 코드를 읽은 것이며 모델 호출·worker-start 는 0회다.

| 새 레인 | 전달 | Orca 1.4.218 이 받는 effort | 정책 std / top | registry 상태 |
| --- | --- | --- | --- | --- |
| `claude-opus-5-5` | `--effort` 플래그 | low~max (claude 카탈로그에 없는 정식 id) | high / max | `pending-transport-and-certificate` |
| `gpt-6.1-sol` | `--effort` 플래그 | minimal~xhigh (codex 미등록 모델 폴백, max·ultra 거부) | high / xhigh | `pending-transport-and-certificate` |

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
- `legacy_lane_migration` 12건 중 8건이 `pending-*` 다. 남은 이전 대상은
  `claude-sonnet-5` → `claude-sonnet-5-5`(effort 재보정 필요), `gpt-5.6-luna` → `gpt-6-luna`
  (A 클래스 1순위 변경이라 별도 결정), `grok-4.6` → `grok-4.7`(Orca 가 grok 모델을 고정하지 못한다)이다.
  `keep-*` 4건은 자기 모델 그대로다: `claude-fable-5-1`, `gpt-6-astra`,
  `gpt-daybreak-blue-latest`, `gemini-3.8-flash`.
- 그래서 planner 는 여전히 `claude-sonnet-5-5`, `gpt-6-sol`, `gpt-6-luna`, `grok-4.7`,
  `grok-4.5` 로의 Orca 발주를 `ORCA_UNREGISTERED_PROCESS_OR_MODEL` 로 막는다. 레인을 더
  바꾸려면 Orca canary 와 `/ai-debate` 를 거친 별도 결정이 필요하다. Orca 밖 guarded adapter 는
  자기 계정·과금·effort 게이트를 그대로 적용한다.

## Refresh record (2026-10-04, 2차)

시각은 모두 KST 다. 모델·Bot·유료 API 호출은 0회다(프롬프트를 보내지 않았고 Orca 워커도
띄우지 않았다). 같은 날 1차(2.14.1, 13:05~13:16) 표는 PR #114 커밋 `e407918` 의 이 파일에,
요약은 2.14.1 changelog 항목에 있다. 2026-10-03 기록은 2.13.1 항목에, 2026-10-02 기록은 2.12.43
항목에 있다.

| 근거 | 관측 | 결과 |
| --- | --- | --- |
| Codex `~/.codex/models_cache.json` | `fetched_at` 2026-10-04T12:46:09Z(21:46:09), 캐시 클라이언트 0.159.0. 21:59:41 에 다시 받았지만 etag 가 같다 | 그대로: 11개 slug, 우선순위 1 `gpt-6.1-sol`, 등록된 slug 는 모두 low~max(`ultra` 는 같은 여섯 개), `none` 은 어디에도 없다 |
| `~/.grok/models_cache.json` | 21:49:20 에 처음 본 사본은 `fetched_at` 11:31:49Z(20:31:49)였고 메타데이터만 읽었다. 아래 `grok models` 가 캐시를 다시 받아 `fetched_at` 12:49:58Z(21:49:58)가 됐고 etag 는 같다. 내용 대조는 이 사본으로 했다 | 그대로: 4.7·4.7-build-fast·4.6 은 low~xhigh, 4.5 는 low~high, 기본 high, 256K·500K 창 |
| `codex --version`, `grok --version`, `agy --version`, `claude --version` | 21:49:47~49 | Codex 0.160.0, grok 1.0.46, agy 1.2.16, Claude Code 2.1.289 — 1차와 같다 |
| `grok --no-auto-update models` | 21:49:57 | 그대로: `grok-4.7`(기본), `grok-4.7-build-fast`, `grok-4.6`, `grok-4.5` |
| `agy models`, `AGY_CLI_DISABLE_AUTO_UPDATE=1` | 21:49:59 | 그대로: 18개 이름(위 대응표와 같다) |
| `claude --help` | 21:50:03 | `--effort` 는 여전히 low, medium, high, xhigh, max. 로컬 모델 목록은 없다 |
| `runtime_collect.py --surface codex --surface grok` (메타데이터 전용) | Codex app-server `model/list` 21:50:42, Grok ACP 과금+모델 21:50:44 | Codex 공개 목록 9개(숨김 `gpt-reserve`·`codex-auto-review` 제외)와 effort 가 캐시와 같다. Grok 4개. 둘 다 구독 모드. 턴 0회 |
| 레지스트리 출처 28개 | 21:52:09~21:52:27, 전부 첫 요청에 HTTP 200(쿠키 유지 클라이언트) | ID·API effort·컨텍스트·가격·장문 구간·은퇴 일자·Daybreak 대상(`gpt-5.6-sol`)·Claude Code 주석이 모두 맞다. 레지스트리 값 변경 0 |
| task-fit 출처 9개 | 21:52:28~21:52:31, 전부 HTTP 200(openai.com Astra 는 첫 시도 403 → 브라우저 요청 헤더로 21:52:29 재시도) | 인용 주장 그대로(Opus 5.5 기본 effort medium 의 FrontierCode 최고점, AA 의 medium 프런티어, AA 지수에서 GPT-6.1 Sol 이 Astra 보다 1점 아래 등). 순위·effort 그대로 |
| OpenAI·Google 폐기 페이지, Google·xAI 모델 목록 | 21:52:31~21:52:33 | 등록 모델 중 폐기 대상 0. OpenAI 최신 공지는 그대로 2026-10-01(`gpt-6-sol`·`gpt-6-luna` 가 대체 모델). `gemini-3.8-flash`·`gemini-3.1-pro-preview` 는 종료 일자 없음. xAI 최신 릴리스 노트(10-02)는 미등록 `grok-voice-transcribe-1.0` 종료다 |
| `model_watch.py status` (읽기 전용) | 21:59:13 | 대기 후보 그대로: Google "Gemini 4 Argon"(2026-09-30 블로그) · OpenAI GPT-6 가이드. 최근 스캔(09:00)은 anthropic 출처 TimeoutError |
| Gemini 4 Argon 공지 | 21:59:27 | 여전히 Fairwind Program 의 신뢰 사용자 대상 단계 배포다. API 모델 ID·Google 문서·가격 행·agy 이름이 없어 등록하지 않는다 |

제거·개명된 모델은 없다. xAI 가격표의 `grok-build-0.1` 은 grok CLI 카탈로그에 없어 이번에도
등록하지 않았다. Claude Haiku 4.5 의 은퇴 하한(2026-10-15)이 다가오지만 미등록 이름이라
레지스트리 값은 그대로다. 관측만 적는다: xAI `grok-4.5` 모델 페이지는 API 별칭
`grok-4.5-latest`·`grok-build-latest` 를 적는다. 레지스트리 `aliases` 는 제공사 API 별칭을 모으지
않으므로(`gpt-5.6-sol` 의 `gpt-5.6` 별칭도 없다) 그대로 두었고, 런타임이 이 이름을 쓰면
`MODEL_NOT_REGISTERED` 로 막힌다.

레지스트리 `checked_at` 은 실제로 쓴 근거 중 가장 이른 시각인 Codex 모델 캐시 수신
2026-10-04 21:46:09(초 미만 버림)이라 사실은 2026-10-11 21:46:09 KST 에 만료된다. task-fit 정책은
자기 출처를 처음 읽은 21:52:28 부터 2026-10-11 21:52:28 KST 까지 유효하다.

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

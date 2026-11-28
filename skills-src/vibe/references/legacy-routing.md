# Legacy Orca routing table

Read this table only when inspecting historical Orca lane policy. The current
model registry, observed runtime, account/quota evidence and guarded adapters
govern present-day execution. The region below is generated from
`scripts/routing.py`; run `python -B scripts/sync_skill_table.py` from the skill
root to refresh it, then `--check` to verify. Paths inside the generated table
are relative to the `/vibe` skill root.

## Contents

- [Lane catalog](#레인-카탈로그)
- [Process map](#공정--클래스--레인)
- [Effort ladder](#effort-결정--클래스가-아니라-태스크-속성)
- [Output constraints](#레인별-산출물-제약)
- [Guards](#가드)

<!-- ROUTING:BEGIN — scripts/routing.py 가 생성한다. 손으로 고치지 말 것 -->

### 레인 카탈로그

| 레인 | CLI | 최상위 | 표준 | Orca 실측 허용 | effort 전달 | 오르카 기동 | 정격 |
|---|---|---|---|---|---|---|---|
| `claude-opus-5-5` | claude | `max` | `high` | `low` · `medium` · `high` · `xhigh` · `max` | `--effort` | ✅ `--model`·`--effort` 가능 | canary 통과 · 인증서 전 · Orca 미등록 id → low~max |
| `claude-opus-5` | claude | `ultracode` | `standard` | `standard` · `ultracode` (와이어는 항상 `--effort max`) | 프롬프트 키워드 | ✅ `--model`·`--effort` 가능 | 1M · D-67 원장 호환용(우선순위 밖) |
| `claude-fable-5-1` | claude | `max` | `high` | `low` · `medium` · `high` · `xhigh` · `max` | `--effort` | ✅ `--model`·`--effort` 가능 | 1M · 쿼터 fableWeekly 별도 · D-125 원장 호환용(우선순위 밖) |
| `claude-fable-5-2` | claude | `max` | `high` | `low` · `medium` · `high` · `xhigh` · `max` | `--effort` | ✅ `--model`·`--effort` 가능 | 1M · 쿼터 fableWeekly 별도 · API 단가 $8/$40 · canary 통과 · 인증서 전 |
| `claude-sonnet-5-5` | claude | `high` | `medium` | `low` · `medium` · `high` · `xhigh` · `max` | `--effort` | ✅ `--model`·`--effort` 가능 | canary 통과 · 인증서 전 · Orca 미등록 id → low~max · xhigh·max 정책 밖 |
| `claude-sonnet-5` | claude | `xhigh` | `medium` | `low` · `medium` · `high` · `xhigh` · `max` | `--effort` | ✅ `--model`·`--effort` 가능 | 1M · API 단가 Opus 5의 0.4배 · 원장 호환용(우선순위 밖) |
| `claude-haiku-5-5` | claude | `medium` | `low` | `low` · `medium` · `high` · `xhigh` · `max` | `--effort` | ✅ `--model`·`--effort` 가능 | canary 통과 · 인증서 전 · Orca 미등록 id → low~max · high 이상 정책 밖 · 10만 토큰 초과 입력 미측정 |
| `gpt-6.2-astra` | codex | `xhigh` | `xhigh` | `low` · `medium` · `high` · `xhigh` — 정책은 **`xhigh` 고정** (off-ladder 불가) | `--effort` | ✅ `--model`·`--effort` 가능 | D-131 · 계획·최종 리뷰 · Orca 실행 인증 대기 |
| `gpt-6.2-sol` | codex | `xhigh` | `medium` | `low` · `medium` · `high` · `xhigh` | `--effort` | ✅ `--model`·`--effort` 가능 | D-131 · 구현·1차 리뷰 · Orca 실행 인증 대기 |
| `gpt-6.1-terra` | codex | `xhigh` | `medium` | — **지정 불가** (그 CLI 기본값) | `--effort` | ⛔ **철회** (D-101) — 새 배정은 `LANE_WITHDRAWN` · 원장 호환용 키 | 원장 호환용(우선순위 밖) |
| `gemini-4-neon` | antigravity | `xhigh` | `medium` | — **지정 불가** (그 CLI 기본값) | **슬러그 내장** | ❌ **Orca 워커 불가** (agent 미등록·과제 전달 실패 — CLI 직행만) | D-131 · agy 초안·설계 보조 |
| `gemini-4-argon` | antigravity | `high` | `high` | — **지정 불가** (그 CLI 기본값) | **슬러그 내장** | ❌ **Orca 워커 불가** (agent 미등록·과제 전달 실패 — CLI 직행만) | D-132 · 2026-11-30 Antigravity 퇴장 · 원장 호환용(우선순위 밖) |
| `gemini-4-carbon` | antigravity | `high` | `high` | — **지정 불가** (그 CLI 기본값) | **슬러그 내장** | ❌ **Orca 워커 불가** (agent 미등록·과제 전달 실패 — CLI 직행만) | D-132 · agy 추론 2차 의견·최종 리뷰·설계 보조 |
| `gpt-6-astra` | codex | `xhigh` | `xhigh` | `minimal` · `low` · `medium` · `high` · `xhigh` — 정책은 **`xhigh` 고정** (off-ladder 불가) | `--effort` | ⛔ **철회** (D-101) — 새 배정은 `LANE_WITHDRAWN` · 원장 호환용 키 | 원장 호환용(우선순위 밖) |
| `gpt-6.1-sol` | codex | `xhigh` | `xhigh` | `minimal` · `low` · `medium` · `high` · `xhigh` — 정책은 **`xhigh` 고정** (off-ladder 불가) | `--effort` | ⛔ **철회** (D-101) — 새 배정은 `LANE_WITHDRAWN` · 원장 호환용 키 | D-130 research-deep·terminal-ci-git 공정 한정(그 밖은 철회) · 원장 호환용(우선순위 밖) · xhigh 고정 · Orca 상한 xhigh |
| `gpt-5.6-sol` | codex | `ultra` | `high` | `minimal` · `low` · `medium` · `high` · `xhigh` · `max` · `ultra` | `--effort` | ⛔ **철회** (D-101) — 새 배정은 `LANE_WITHDRAWN` · 원장 호환용 키 | 272K(최대 872K) · D-101 철회 · 원장 호환용(우선순위 밖) |
| `gpt-5.6-terra` | codex | `max` | `medium` | `minimal` · `low` · `medium` · `high` · `xhigh` · `max` · `ultra` | `--effort` | ⛔ **철회** (D-101) — 새 배정은 `LANE_WITHDRAWN` · 원장 호환용 키 | 272K(최대 872K) · D-101 철회 · 원장 호환용(우선순위 밖) |
| `gpt-6-luna` | codex | `medium` | `low` | `minimal` · `low` · `medium` · `high` · `xhigh` | `--effort` | ⛔ **철회** (D-101) — 새 배정은 `LANE_WITHDRAWN` · 원장 호환용 키 | D-101 철회(결함 아님 · D-91 canary 통과) · 원장 호환용(우선순위 밖) · Orca 상한 xhigh |
| `gpt-5.6-luna` | codex | `medium` | `low` | `minimal` · `low` · `medium` · `high` · `xhigh` · `max` | `--effort` | ⛔ **철회** (D-101) — 새 배정은 `LANE_WITHDRAWN` · 원장 호환용 키 | 272K(최대 872K) · 최저가 · 원장 호환용(우선순위 밖) |
| `gpt-daybreak-blue-latest` | codex | `xhigh` | `high` | `minimal` · `low` · `medium` · `high` · `xhigh` | `--effort` | ⚠ 폐기 표시 — 고정 공정 `security-artifact-gate` 자리만 (그 밖은 `LANE_DEPRECATED`) | 폐기 표시(deprecated) 별칭 · D-101 생성물 게이트 고정 전용(그 밖은 LANE_DEPRECATED) · Orca 상한 xhigh |
| `gemini-3.8-flash` | antigravity | `high` | `medium` | — **지정 불가** (그 CLI 기본값) | **슬러그 내장** | ❌ **Orca 워커 불가** (agent 미등록·과제 전달 실패 — CLI 직행만) | Gemini Flash 계열 |
| `gemini-4-hydrogen` | antigravity | `xhigh` | `high` | — **지정 불가** (그 CLI 기본값) | **슬러그 내장** | ❌ **Orca 워커 불가** (agent 미등록·과제 전달 실패 — CLI 직행만) | Gemini 4 Hydrogen · 1M 통합 · API 단가 $1.50/$7.50 · D-125 |
| `grok-4.6` | grok | `xhigh` | `high` | — **지정 불가** (그 CLI 기본값) | `--effort` | ⚠ `--agent` 만 — `--model` 거부 | 500K · 200K초과 2배 과금 · D-125 원장 호환용(우선순위 밖) |
| `grok-4.7` | grok | `xhigh` | `high` | — **지정 불가** (그 CLI 기본값) | `--effort` | ⚠ `--agent` 만 — `--model` 거부 | 500K · 200K초과 2배 과금 · CLI 기본 모델 · D-125 |

**과거 Orca 정책표이며 현재 실행·가격·계정 증거가 아니다.** `--probe-efforts`는 worker-start를 사용하므로 차단됐다. 중앙 registry/runtime과 guarded adapter로 재검증한다. `allow_off_ladder=True`는 오프라인 argv 검증 옵션일 뿐 실행 허가가 아니다.

**오르카 기동은 2026-09-04 실측이다.** `--model` 은 Claude·Codex·Cursor 만 받는다 (orca help) — grok·gemini 는 `--agent` 만 주고 모델은 그 CLI 의 기본값이 쓰인다. ⚠ **agent id 는 CLI 이름이 아니라 좌석 이름이다**: `--agent agy` 는 `agent_unconfigured` 로 거부되고 `--agent antigravity` 가 정본이다. (CLI 바이너리는 `agy`, Orca 등록명은 `antigravity`.)

**배정 금지**: `codex-auto-review` · `gpt-5.3-codex-spark` · `gpt-5.4-mini` · `gpt-reserve` — 용도 미검증 / R&R 미확정 (발주 §3) · **D-28**: 코딩은 공정 전용 목록 `PROCESS_LANES` (claude 전용 · codex 폴백 없음 · #5 · 파일을 바꾸는 `writes` 공정도 같음 · Q-09) · fable·sonnet 은 M1 통과(2026-09-16) 뒤 2순위 편입 · A-verify = astra → fable → opus(읽기 전용 · `writes` 면 A_VERIFY_WRITES) · 반증 "예"인 A 작업은 A-verify 로 승격 · gemini `unavailable`(M6) → `references/d28-routing.md`

**D-67 (2026-10-04)**: `claude-opus-5-5`(flag · low~max)·`gpt-6.1-sol`(flag · minimal~xhigh)을 옛 레인 옆에 **등록만** 했다 — 우선순위·코딩·종합 고정·코디네이터가 새 키로 옮겨졌다. 읽기 전용 canary(`launch.requested` ↔ `launch.effective` 대조)는 2026-10-04 에 두 레인 모두 통과했지만, native send 와 계정/과금 인증서 전까지는 동작 레인이 아니며 $0 게이트·G5·Orca 인증서가 똑같이 걸린다. 옛 키(`claude-opus-5` 등)는 원장 호환용으로 남고 `gpt-5.6-sol` 은 C 클래스 끝 폴백이었다. grok 은 Orca 가 모델을 고정하지 못해 그대로다. (그 시점 기록 — `gpt-6.1-sol`·`gpt-5.6-sol` 은 D-101 로 철회됐다. 아래.)

**2026-10-05 Simon 지시 (2.15.5)**: A 클래스를 현행 세대로 옮겼다 — `gpt-6-luna`(flag · minimal~xhigh · 사다리 low/medium) → `claude-sonnet-5-5`(flag · low~max · 사다리 medium/high, xhigh·max 는 토큰 폭증이라 정책 밖) → `claude-opus-5-5`. 옛 `gpt-5.6-luna`·`claude-sonnet-5` 는 원장 호환용(우선순위 밖)이다. 두 새 레인은 **등록만** 됐다 — 읽기 전용 canary 와 계정/과금 인증서 전까지 동작 레인이 아니며 $0 게이트·G5·Orca 인증서가 똑같이 걸린다. (그 시점 기록 — `gpt-6-luna` 는 D-101 로 철회됐다. 아래.)

**D-98 (2026-10-12 오전 · 2.16.0 · 같은 날 D-101 이 뒤집었다)**: 보안 생성물 게이트를 `gpt-daybreak-blue-latest` → `gpt-6.1-sol` @xhigh 로 옮겼었다. OpenAI 가 그 별칭을 deprecated 로 표시했고(종료일·대체 ID 미공지) 중앙 계획기는 `MODEL_NOT_ACTIVE` 로 막는다 — 이 두 사실은 지금도 그대로다. 그때 만든 방어 루브릭과 fail-closed 규칙(빈 출력·차단·첫 줄 누락·모호한 판정 = FAIL)은 `references/security-artifact-gate.md` 에 남아 지금 게이트에도 쓴다.

**D-99 (2026-10-12 오전 · 2.16.0)**: `claude-haiku-5-5`(flag · low~max · 사다리 low/medium, high 이상은 정책 밖)를 A 클래스의 Claude 쪽 첫 폴백(2순위)으로 넣었다. 읽기 전용 canary(run `run_8f7a27febc38` · @low · 정답이 정해진 A 과제 3/3)는 통과했지만 계정/과금 인증서 전까지 동작 레인이 아니며 $0 게이트·G5·Orca 인증서가 똑같이 걸린다. 큰 입력·10만 토큰 초과 입력·쿼터 절감은 미측정이다. 같은 날 D-101 로 1순위가 됐다(아래).

**D-101 / D-102 당시 기록**: GPT-6 Astra @xhigh 단일 레인, Daybreak 고정 및 조건부 Astra 폴백. D-130에서 6.1 Sol을 연구·에이전트에 한시 허용했다. 당시 canary는 6.2 모델을 시험하지 않았다.

**D-131 (2026-11-24)**: D-130의 6.1 Sol 예외를 종료했다. GPT-6.2 Sol과 Astra는 독립 단계에서 병렬로 쓴다. 레거시 Orca 코딩 라운드의 고정 보안 게이트와 G1 독립성 검사는 계속 적용한다. Gemini 4 세 모델은 agy 경로를 쓴다.

**D-132 (2026-11-28)**: Antigravity가 11월 30일 Gemini 4 Argon을 뺀다. Argon이 맡던 agy 추론 2차 의견·최종 리뷰·설계 보조는 Carbon high, 한국어 초안 대체는 Carbon medium으로 옮겼다.

### 공정 → 클래스 → 레인

| 공정 | 클래스 | 1순위 | 2순위 | 3후보 (이후 폴백) |
|---|---|---|---|---|
| 대량 정형 변환 · 카운트 | A | `claude-haiku-5-5` | `claude-sonnet-5-5` | `claude-opus-5-5` |
| 인벤토리 · 스키마 검증 | A | `claude-haiku-5-5` | `claude-sonnet-5-5` | `claude-opus-5-5` |
| 디스크 스캔 · grep | A | `claude-haiku-5-5` | `claude-sonnet-5-5` | `claude-opus-5-5` |
| 장문 로그 · 커밋히스토리 분류 집계 | A | `claude-haiku-5-5` | `claude-sonnet-5-5` | `claude-opus-5-5` |
| 기록↔사실 대조 · 주장 판정 (읽기 전용) | A-verify | `gpt-6.2-astra` | `claude-fable-5-2` | `claude-opus-5-5` |
| 웹 리서치 — 정독 · 모순 종합 | B | `gpt-6.2-astra` | `claude-fable-5-2` | `claude-opus-5-5` |
| 코딩 — 구현 · 대규모 리팩터링 **(공정 전용 목록)** | B | `claude-opus-5-5` | `claude-fable-5-2` | `claude-sonnet-5-5` |
| 터미널 · CI · git (판단 섞인 경우) | B | `gpt-6.2-astra` | `claude-fable-5-2` | `claude-opus-5-5` |
| 보안 — 생성물 안전성 게이트 | B | **`gpt-daybreak-blue-latest` @xhigh 고정** | 폴백 `gpt-6.2-astra` @xhigh (고정 레인이 설 수 없을 때만 · D-102) | — |
| 보안 — 비즈니스 로직 · 인가 | B | **`gpt-6.2-astra` @xhigh 고정** | — | — |
| 트렌드 · 실시간 | C-realtime | `grok-4.7` | `claude-opus-5-5` | `gpt-6.2-astra` |
| 웹 리서치 — 수집 | C-realtime | `grok-4.7` | `claude-opus-5-5` | `gpt-6.2-astra` |
| Google 플랫폼 (BigQuery/Firebase/Workspace) | C-platform | `gemini-4-hydrogen` | `claude-opus-5-5` | `gpt-6.2-astra` |
| UI 시각 검증 | C-platform | `gemini-4-hydrogen` | `claude-opus-5-5` | `gpt-6.2-astra` |
| 다레인 산출물 조립 | D | **`claude-opus-5-5` @max 고정** | — | — |
| 워크트리 · run 관리 (orca CLI) | N | — | — | — |

### effort 결정 — 클래스가 아니라 태스크 속성

> **반증 가능한 전제가 있나?** ("X는 죽었다"를 확인 / "A가 B보다 낫다"를 판정 / 원인 규명)

| | `claude-opus-5-5` | `claude-opus-5` | `claude-fable-5-1` | `claude-fable-5-2` | `claude-sonnet-5-5` | `claude-sonnet-5` | `claude-haiku-5-5` | `gpt-6.2-astra` | `gpt-6.2-sol` | `gpt-6.1-terra` | `gemini-4-neon` | `gemini-4-argon` | `gemini-4-carbon` | `gpt-6-astra` | `gpt-6.1-sol` | `gpt-5.6-sol` | `gpt-5.6-terra` | `gpt-6-luna` | `gpt-5.6-luna` | `gpt-daybreak-blue-latest` | `gemini-3.8-flash` | `gemini-4-hydrogen` | `grok-4.6` | `grok-4.7` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **YES** 최상위 | `max` | `ultracode` | `max` | `max` | `high` | `xhigh` | `medium` | `xhigh` | `xhigh` | `xhigh` | `xhigh` | `high` | `high` | `xhigh` | `xhigh` | `ultra` | `max` | `medium` | `medium` | `xhigh` | `high` | `xhigh` | `xhigh` | `xhigh` |
| **NO** 표준 | `high` | `standard` | `high` | `high` | `medium` | `medium` | `low` | `xhigh` | `medium` | `medium` | `medium` | `high` | `high` | `xhigh` | `xhigh` | `high` | `medium` | `low` | `low` | `high` | `medium` | `high` | `high` | `high` |
| 사다리 밖 상한 (`allow_off_ladder`) | `max` | `ultracode` | `max` | `max` | `max` | `max` | `max` | `xhigh` | `xhigh` | — (지정 불가) | — (지정 불가) | — (지정 불가) | — (지정 불가) | `xhigh` | `xhigh` | `ultra` | `ultra` | `xhigh` | `max` | `xhigh` | — (지정 불가) | — (지정 불가) | — (지정 불가) | — (지정 불가) |

이 사다리는 과거 transport 제약이다. 현재 모델/effort는 중앙 registry와 fresh runtime의 교집합으로 정한다. `run_codex_exec` 실호출은 차단됐으며 상한 초과를 direct CLI로 우회하지 않는다.

코디네이터 레인 = **`gpt-6.2-astra` @xhigh** — 종합(D)과 벤더가 달라야 한다. 워커 겸임은 클래스와 무관하게 경고한다(D-28 #6).

### 레인별 산출물 제약

| 레인 | 허용 | 금지 | 사유 |
|---|---|---|---|
| `grok-4.7` | CSV · 카운트 · 분류 라벨만 | 서술 결론 · 인과 추정 · 200K 초과 입력(과금 2배) | 사실 신뢰도가 4레인 중 최약. 합계는 D 레인이 산술 재검산한다 |
| `gemini-4-hydrogen` | 발견 목록 + 탐색 드라이브 · 제외 경로 · 스캔 파일 수 | 범위 없는 '0건' 반환 · 무인 장기 루프 단독 배치 | 부재 보고 오류가 직전 라운드 오류 5건 중 3건의 원인 |
| `claude-opus-5-5` | 항목별 확신도 표기 필수 (강=기계검증 / 약=판단) | 리포트만 내고 끝내기 — 사람이 읽는 것은 결정 시트 1장이다 | 종합 레인이므로 사람의 결정으로 이어져야 한다 |
| `gpt-6.2-astra` | 계획·설계·복합 디버깅·최종 리뷰. 파일·실행 결과로 요구사항을 대조한다. | stub, 확인하지 않은 주장, 요청 밖 변경을 완료 근거로 삼기 | D-131 · 다른 벤더 리뷰 또는 시험 증거가 필요하다. |
| `gpt-6.2-sol` | 일상 구현·문서·1차 리뷰. 독립 작업은 Astra와 같은 라운드에 둔다. | 같은 벤더로 자기 산출물의 독립 리뷰를 대체하기 | D-131 · 요구사항별 시험 증거나 다른 벤더의 결과를 기록한다. |
| `claude-haiku-5-5` | 정형 변환 · 카운트 · 분류 · **부재 보고에는 탐색 범위 명시** | 우열 판단 (필요하면 sonnet-5-5 이상으로 올린다) · 범위 없는 '0건' | A 클래스 1순위 레인(D-101) — 판단을 맡기지 않는다. 범위 요구는 Simon 결정(2026-09-04, luna03 채택)으로 A 클래스 전체에 적용된다. canary 는 작은 과제 3개 · effort low 1회만 봤다(D-99 · 1순위로 옮긴 뒤의 canary 는 없다): 큰 입력 · 10만 토큰 초과 입력(API 단가 5배 구간) · 쿼터 절감은 미측정이다 |
| `gpt-daybreak-blue-latest` | **생성물 게이트로만 쓴다**: 첫 줄 `GATE: BLOCK` 또는 `GATE: PASS` · 이어서 발견마다 한 줄 (CWE 번호 · 위치 · 사유) · 그 뒤에 발견별 재현 경로 · 심각도 · 최소 패치(옛 게이트 규칙 그대로) · 형식과 루브릭은 `references/security-artifact-gate.md` | 빈 출력 · 차단/거절 · 첫 줄 누락 · 모호한 판정을 PASS 로 읽기 (전부 FAIL) · 방어 목적 밖의 공격 코드 생성 · 범위 없는 '취약점 0건' · 게이트 밖 공정에 배정 (`LANE_DEPRECATED`) | 제공사가 폐기 표시한 cyber 별칭을 Simon 지시(D-101)로 게이트에만 쓴다 — 근거 없는 통과는 게이트를 무력화하고, 별칭은 예고 없이 사라질 수 있다. 실행 전마다 Codex 카탈로그를 확인하고, 없거나 출력이 비거나 차단되면 FAIL 이다(canary 는 심은 샘플 1건) |

### 가드

| | 내용 | 자동 검출 |
|---|---|---|
| G1 | 짠 레인이 자기 코드를 보안 리뷰하지 않는다 | ✅ 원장 기록 |
| G2 | 자기 결론 재검증에 서브에이전트를 쓰지 않는다 — 반증은 리포트 '§X 반증 시도' 섹션 | — (오검출 방지) |
| G3 | 워커당 spawn 상한 8 | ✅ 원장 기록 |
| G4 | 쿼터 게이트는 디스패치 시점에만. 실행 중 중단 근거로 쓰지 않는다 — 한도 도달로 **실패·정지한** 워커만 여유 레인의 새 task 로 인수인계한다(`handoff_spec` + `revalidate_for_retry`, Q-260913-05). 상시 모니터링 데몬·실행 중 선제 교체는 하지 않는다 | — (오검출 방지) |
| G5 | 쿼터는 4벤더 각각 확인한다 | ✅ 원장 기록 |
| G6 | 부재 보고에는 탐색 범위를 붙인다. 범위 없는 '0건'은 반환값 불인정 — gemini 뿐 아니라 **A 클래스 전체**에 적용 (Simon 결정 2026-09-04) | — (오검출 방지) |
| G7 | 최상위 effort 는 반증질문 YES 인 태스크에만 | — (오검출 방지) |
| G8 | 쓰기 라운드 전 검증된 종료 절차가 필요하다. legacy `kill_worker.py --kill --fence`는 handle/dispatch 결속 미검증으로 사용 금지이며 raw `worker-stop`도 차단된다. 별도 승인·정확한 대상 검증 없이 종료하거나 재발주하지 않는다 | — (오검출 방지) |
| G9 | Move-Item 배치는 매니페스트 + 역방향 스크립트 선행 | — (오검출 방지) |
| G10 | 적대적 평가에서 채점자는 두 생산자와 **벤더가 달라야** 한다. 벤더 3개를 못 채우면 그 문제는 건너뛴다 — 자기 벤더가 자기 답을 채점하느니 관측을 포기한다 (`adversarial_eval.py`) | — (오검출 방지) |
| G11 | Codex 워커 기동 전에 PATH 실행본과 인접 npm 패키지를 로컬에서 비교한다. `python -B scripts/check_tooling.py --local-codex` (종료 0만 진행, 1=뒤처짐, 2=미확인). 전체 도구 보고서는 npm 원격·Orca 조회가 있어 이 게이트를 대체하지 못한다 | — (오검출 방지) |
| G12 | 쿼터·metadata는 생성 성공이나 무료 사용 증거가 아니다. legacy `adversarial_eval.py --preflight` 실호출은 차단됐다. 실측도 중앙 계획·예산 예약·fresh 계정/비용 증명 뒤에만 가능하다. 과거 Grok HOLD는 영구 금지가 아니며 복구 시에도 최신 쿼터·선택 모델의 구독 포함·초과 과금 차단을 다시 확인한다 | — (오검출 방지) |
| G13 | 재시도·대체도 중앙 planner/Store/guarded adapter를 거친다. 수락 불명은 lookup-only이며 raw `worker-start --retry-of`로 우회하지 않는다 | — (오검출 방지) |
| G14 | 결정 시트(`make_decision_sheet.py`)를 만들지 않은 라운드는 **끝난 것으로 치지 않는다** — 손으로 조립한 시트는 `decisions_run_*.json` 을 내지 않아 채택률이 비고 스왑 규칙이 돌지 않는다 (D-28 #15) | — (오검출 방지) |

쿼터: 80% 초과 → **모든 순위에서** 강등(ok 레인이 없으면 첫 강등 레인) · 100% 도달 → 사용 금지(Q-05) · 읽기 실패 = **미확인**(0%로 간주 금지) · 실호출(G12) 실패 = 사용 금지 · 실호출 결과가 24시간 넘으면 미확인 · `quota_bucket` 이 있는 레인(fable)은 그 버킷으로 판정 (D-28 #13)

<!-- ROUTING:END -->

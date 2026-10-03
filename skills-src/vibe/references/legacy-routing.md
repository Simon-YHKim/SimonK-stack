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
| `claude-opus-5-5` | claude | `max` | `high` | `low` · `medium` · `high` · `xhigh` · `max` | `--effort` | ✅ `--model`·`--effort` 가능 | canary 전 · Orca 미등록 id → low~max |
| `claude-opus-5` | claude | `ultracode` | `standard` | `standard` · `ultracode` (와이어는 항상 `--effort max`) | 프롬프트 키워드 | ✅ `--model`·`--effort` 가능 | 1M · D-67 원장 호환용(우선순위 밖) |
| `claude-fable-5-1` | claude | `max` | `high` | `low` · `medium` · `high` · `xhigh` · `max` | `--effort` | ✅ `--model`·`--effort` 가능 | 1M · 쿼터 fableWeekly 별도 · API 단가 Opus 5의 2배 |
| `claude-sonnet-5` | claude | `xhigh` | `medium` | `low` · `medium` · `high` · `xhigh` · `max` | `--effort` | ✅ `--model`·`--effort` 가능 | 1M · API 단가 Opus 5의 0.4배 |
| `gpt-6-astra` | codex | `xhigh` | `high` | `minimal` · `low` · `medium` · `high` · `xhigh` | `--effort` | ✅ `--model`·`--effort` 가능 | 272K(최대 872K) · Orca 상한 xhigh |
| `gpt-6.1-sol` | codex | `xhigh` | `high` | `minimal` · `low` · `medium` · `high` · `xhigh` | `--effort` | ✅ `--model`·`--effort` 가능 | canary 전 · Orca 상한 xhigh |
| `gpt-5.6-sol` | codex | `ultra` | `high` | `minimal` · `low` · `medium` · `high` · `xhigh` · `max` · `ultra` | `--effort` | ✅ `--model`·`--effort` 가능 | 272K(최대 872K) · D-67 6.1-sol 뒤 폴백 |
| `gpt-5.6-terra` | codex | `max` | `medium` | `minimal` · `low` · `medium` · `high` · `xhigh` · `max` · `ultra` | `--effort` | ✅ `--model`·`--effort` 가능 | 272K(최대 872K) |
| `gpt-5.6-luna` | codex | `medium` | `low` | `minimal` · `low` · `medium` · `high` · `xhigh` · `max` | `--effort` | ✅ `--model`·`--effort` 가능 | 272K(최대 872K) · 최저가 |
| `gpt-daybreak-blue-latest` | codex | `xhigh` | `high` | `minimal` · `low` · `medium` · `high` · `xhigh` | `--effort` | ✅ `--model`·`--effort` 가능 | 보안 전용 · 기본 low · Orca 상한 xhigh |
| `gemini-3.8-flash` | antigravity | `high` | `medium` | — **지정 불가** (그 CLI 기본값) | **슬러그 내장** | ❌ **Orca 워커 불가** (agent 미등록·과제 전달 실패 — CLI 직행만) | Gemini Flash 계열 |
| `grok-4.6` | grok | `xhigh` | `high` | — **지정 불가** (그 CLI 기본값) | `--effort` | ⚠ `--agent` 만 — `--model` 거부 | 500K · 200K초과 2배 과금 |

**과거 Orca 정책표이며 현재 실행·가격·계정 증거가 아니다.** `--probe-efforts`는 worker-start를 사용하므로 차단됐다. 중앙 registry/runtime과 guarded adapter로 재검증한다. `allow_off_ladder=True`는 오프라인 argv 검증 옵션일 뿐 실행 허가가 아니다.

**오르카 기동은 2026-09-04 실측이다.** `--model` 은 Claude·Codex·Cursor 만 받는다 (orca help) — grok·gemini 는 `--agent` 만 주고 모델은 그 CLI 의 기본값이 쓰인다. ⚠ **agent id 는 CLI 이름이 아니라 좌석 이름이다**: `--agent agy` 는 `agent_unconfigured` 로 거부되고 `--agent antigravity` 가 정본이다. (CLI 바이너리는 `agy`, Orca 등록명은 `antigravity`.)

**배정 금지**: `codex-auto-review` · `gpt-5.3-codex-spark` · `gpt-5.4-mini` · `gpt-reserve` — 용도 미검증 / R&R 미확정 (발주 §3) · **D-28**: 코딩은 공정 전용 목록 `PROCESS_LANES` (claude 전용 · codex 폴백 없음 · #5 · 파일을 바꾸는 `writes` 공정도 같음 · Q-09) · fable·sonnet 은 M1 통과(2026-09-16) 뒤 2순위 편입 · A-verify = astra → fable → opus(읽기 전용 · `writes` 면 A_VERIFY_WRITES) · 반증 "예"인 A 작업은 A-verify 로 승격 · gemini `unavailable`(M6) → `references/d28-routing.md`

**D-67 (2026-10-04)**: `claude-opus-5-5`(flag · low~max)·`gpt-6.1-sol`(flag · minimal~xhigh)을 옛 레인 옆에 **등록만** 했다 — 우선순위·코딩·종합 고정·코디네이터가 새 키로 옮겨졌다. 읽기 전용 canary(`launch.requested` ↔ `launch.effective` 대조)와 계정/과금 인증서 전까지는 동작 레인이 아니며 $0 게이트·G5·Orca 인증서가 똑같이 걸린다. 옛 키(`claude-opus-5` 등)는 원장 호환용으로 남고 `gpt-5.6-sol` 은 C 클래스 끝 폴백이다. grok 은 Orca 가 모델을 고정하지 못해 그대로다.

### 공정 → 클래스 → 레인

| 공정 | 클래스 | 1순위 | 2순위 | 3후보 (이후 폴백) |
|---|---|---|---|---|
| 대량 정형 변환 · 카운트 | A | `gpt-5.6-luna` | `claude-sonnet-5` | `claude-opus-5-5` |
| 인벤토리 · 스키마 검증 | A | `gpt-5.6-luna` | `claude-sonnet-5` | `claude-opus-5-5` |
| 디스크 스캔 · grep | A | `gpt-5.6-luna` | `claude-sonnet-5` | `claude-opus-5-5` |
| 장문 로그 · 커밋히스토리 분류 집계 | A | `gpt-5.6-luna` | `claude-sonnet-5` | `claude-opus-5-5` |
| 기록↔사실 대조 · 주장 판정 (읽기 전용) | A-verify | `gpt-6-astra` | `claude-fable-5-1` | `claude-opus-5-5` |
| 웹 리서치 — 정독 · 모순 종합 | B | `gpt-6-astra` | `claude-fable-5-1` | `claude-opus-5-5` |
| 코딩 — 구현 · 대규모 리팩터링 **(공정 전용 목록)** | B | `claude-opus-5-5` | `claude-fable-5-1` | — |
| 터미널 · CI · git (판단 섞인 경우) | B | `gpt-6-astra` | `claude-fable-5-1` | `claude-opus-5-5` |
| 보안 — 생성물 안전성 게이트 | B | **`gpt-daybreak-blue-latest` @xhigh 고정** | — | — |
| 보안 — 비즈니스 로직 · 인가 | B | **`gpt-6-astra` @xhigh 고정** | — | — |
| 트렌드 · 실시간 | C-realtime | `grok-4.6` | `gpt-6.1-sol` | `claude-opus-5-5` → `gpt-5.6-sol` |
| 웹 리서치 — 수집 | C-realtime | `grok-4.6` | `gpt-6.1-sol` | `claude-opus-5-5` → `gpt-5.6-sol` |
| Google 플랫폼 (BigQuery/Firebase/Workspace) | C-platform | `gemini-3.8-flash` | `gpt-6.1-sol` | `claude-opus-5-5` → `gpt-5.6-sol` |
| UI 시각 검증 | C-platform | `gemini-3.8-flash` | `gpt-6.1-sol` | `claude-opus-5-5` → `gpt-5.6-sol` |
| 다레인 산출물 조립 | D | **`claude-opus-5-5` @max 고정** | — | — |
| 워크트리 · run 관리 (orca CLI) | N | — | — | — |

### effort 결정 — 클래스가 아니라 태스크 속성

> **반증 가능한 전제가 있나?** ("X는 죽었다"를 확인 / "A가 B보다 낫다"를 판정 / 원인 규명)

| | `claude-opus-5-5` | `claude-opus-5` | `claude-fable-5-1` | `claude-sonnet-5` | `gpt-6-astra` | `gpt-6.1-sol` | `gpt-5.6-sol` | `gpt-5.6-terra` | `gpt-5.6-luna` | `gpt-daybreak-blue-latest` | `gemini-3.8-flash` | `grok-4.6` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **YES** 최상위 | `max` | `ultracode` | `max` | `xhigh` | `xhigh` | `xhigh` | `ultra` | `max` | `medium` | `xhigh` | `high` | `xhigh` |
| **NO** 표준 | `high` | `standard` | `high` | `medium` | `high` | `high` | `high` | `medium` | `low` | `high` | `medium` | `high` |
| 사다리 밖 상한 (`allow_off_ladder`) | `max` | `ultracode` | `max` | `max` | `xhigh` | `xhigh` | `ultra` | `ultra` | `max` | `xhigh` | — (지정 불가) | — (지정 불가) |

이 사다리는 과거 transport 제약이다. 현재 모델/effort는 중앙 registry와 fresh runtime의 교집합으로 정한다. `run_codex_exec` 실호출은 차단됐으며 상한 초과를 direct CLI로 우회하지 않는다.

코디네이터 레인 = **`gpt-6.1-sol` @xhigh** — 종합(D)과 벤더가 달라야 한다. 워커 겸임은 클래스와 무관하게 경고한다(D-28 #6).

### 레인별 산출물 제약

| 레인 | 허용 | 금지 | 사유 |
|---|---|---|---|
| `grok-4.6` | CSV · 카운트 · 분류 라벨만 | 서술 결론 · 인과 추정 · 200K 초과 입력(과금 2배) | 사실 신뢰도가 4레인 중 최약. 합계는 D 레인이 산술 재검산한다 |
| `gemini-3.8-flash` | 발견 목록 + 탐색 드라이브 · 제외 경로 · 스캔 파일 수 | 범위 없는 '0건' 반환 · 무인 장기 루프 단독 배치 | 부재 보고 오류가 직전 라운드 오류 5건 중 3건의 원인 |
| `gpt-5.6-luna` | 정형 변환 · 카운트 · 분류 · **부재 보고에는 탐색 범위 명시** | 우열 판단 (필요하면 terra 이상으로 올린다) · 범위 없는 '0건' | 최저가 레인 — 판단을 맡기면 싼 값에 틀린다. 범위 요구는 Simon 결정(2026-09-04, luna03 채택)으로 A 클래스 전체에 적용된다 |
| `claude-opus-5-5` | 항목별 확신도 표기 필수 (강=기계검증 / 약=판단) | 리포트만 내고 끝내기 — 사람이 읽는 것은 결정 시트 1장이다 | 종합 레인이므로 사람의 결정으로 이어져야 한다 |
| `gpt-6-astra` | 판단마다 근거(파일·행·명령 출력) 첨부 · 반증 시도 1건 이상 명시 | 대량 정형 변환에 배치 (A 클래스는 luna 로 내린다) · `ultra`/`max` 로 Orca 디스패치 (거부된다 — 상한 xhigh) | codex 계열 최상위 좌석이다. 싼 일에 태우면 쿼터만 태우고, 정책 밖 effort 로 부르면 워커가 아예 안 뜬다 |
| `gpt-daybreak-blue-latest` | 취약점 발견마다 file:line · 재현 경로 · 심각도 · 최소 패치 | 방어 목적 밖의 공격 코드 생성 · 범위 없는 '취약점 0건' | 보안 전용 레인 — 근거 없는 발견은 게이트를 무력화한다. 출력이 차단되면 Trusted Access 미승인이므로 terminal read 로 확인한다 |

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

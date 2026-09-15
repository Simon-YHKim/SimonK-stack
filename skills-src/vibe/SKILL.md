---
name: vibe
description: "Use when, and proactively whenever, work should be fanned out to Orca workers across four vendors instead of one session—triggers \"/vibe\", \"바이브 코딩\", \"오르카로 돌려\", \"파이프라인 돌려\", \"워커 붙여서\", \"orca pipeline\", \"fan out this task\", or a pasted \"/vibe 실행\" block. Produces: an HTML intake form (vibe-intake.html) with live 4-vendor quota and prefilled class lanes; then Orca workers routed by process class (A mechanical / B judgment / C external / D synthesis) across claude-opus-5, gpt-6-astra, gpt-5.6-sol/terra/luna, gpt-daybreak-blue-latest (cyber), gemini-3.8-flash (agent antigravity) and grok-4.6, with effort forced into every codex dispatch and checked against Orca's measured allowlist (astra/daybreak cap at xhigh); a decision sheet; and one routing-ledger row per worker. NOT for small single-session edits (dev-orchestrator) or new apps (app-dev-orchestrator)."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 2.3.0
author: simon-stack
---

# vibe — 4벤더 분산 파이프라인

**Simon은 명령어를 외우지 않는다.** `/vibe` 한 마디면 폼이 뜨고, 거기서 만들어진 프롬프트를 붙여넣으면 실행된다.

```
A. /vibe                      → 인테이크 폼 생성 → 브라우저로 염 → 멈춤
B. (폼에서 복사한 "/vibe 실행 …" 블록 붙여넣기)  → 파이프라인 실행
C. /vibe <과제를 직접 서술>    → 폼 건너뛰고 바로 분류·실행
```

## 호스트 — Claude Code · codex CLI 둘 다

실체는 `SKILL_ROOT` 아래의 python 스크립트와 `orca` CLI 뿐이라 **어느 호스트에서든 같게 돈다.**
아래 문서의 `<skill>` 은 전부 이 경로로 읽는다.

```bash
SKILL_ROOT="$HOME/.claude/skills/vibe"     # codex 에서도 같은 실체다(아래 참조)
python "$SKILL_ROOT/scripts/routing.py"    # 레인·상한 요약
```

- **Claude Code**: `~/.claude/skills/vibe` (정본 실체)
- **codex CLI**: `~/.codex/skills/vibe` — 위 디렉터리로 가는 **디렉터리 정션**이다(2026-09-06 설치).
  복사본이 아니라서 표·스크립트가 갈라지지 않는다. 이 스킬의 규율 자체가 "정본은 하나"이므로 사본을 두지 않는다.
  ⚠ 걷어낼 때는 **정션만** 지운다: `cmd /c rmdir "%USERPROFILE%\.codex\skills\vibe"`.
  `rm -rf` 로 지우면 정션을 따라가 **정본까지 지운다.**
- codex 는 스킬 설명이 길면 컨텍스트 예산에 맞춰 **줄여서** 싣는다("descriptions were shortened").
  본문은 온전히 읽히므로 동작에는 영향이 없지만, codex 쪽 자동 발동은 Claude 보다 둔할 수 있다 —
  안 걸리면 `/vibe` 를 이름으로 부르면 된다.

## v2.1이 푸는 문제

직전 라운드에서 읽기전용 워커 4개를 **전부 한 벤더(Claude)에** 배정했다 → 쿼터 63%에서 게이트 → 축소 → 79% 착지. 한 달 전에는 파일 허브가 Gemini 쿼터 소진 후 아무도 재기동하지 않아 죽었다. **30일 간격의 같은 실패 모드다.**

목표는 성능이 아니라 **가용성**이다. 단일 벤더 쿼터가 라운드 전체를 죽이는 구조를 없애고, 어느 배정이 나았는지를 라운드마다 기록해 축적한다.

## v2.2 — `gpt-6-astra` 편입 (2026-09-06)

B 2순위가 `gpt-6-astra` 로, 인가 게이트가 `gpt-6-astra @xhigh` 로 올랐고 effort 를 **정책(최상위/표준)** 과 **Orca 물리적 상한**으로 쪼갰다.
astra·daybreak 은 Orca 워커로 `xhigh` 가 끝이다(Orca 앱의 codex 카탈로그 다섯 줄 밖이라 `unknownModelOptions` 로 떨어진다, 1.4.200 에서도 같다). `ultra` 는 sol 로 내리거나 codex 직행(3-2)뿐이다.
원인 규명 전문 · 측정법(`routing.py --probe-efforts`) → **`references/v2.2-astra-effort-cap.md`** · **v2.3 (2026-09-16) — D-28 1단계**: 코딩 claude 전용(`PROCESS_LANES`) · 강등을 전 순위에·실호출·fable 버킷 · gemini `unavailable` · 코디네이터 sol@xhigh → **`references/d28-routing.md`**

---

## 라우팅 — 정본은 `scripts/routing.py`

아래 표는 `python scripts/routing.py --emit-md` 가 생성한다. **손으로 고치지 말 것** — 고치려면 `routing.py`를 고치고 다시 생성한다. 폼(모드 A)과 실행(모드 B/C)이 이 한 표를 같이 본다.

<!-- ROUTING:BEGIN — scripts/routing.py 가 생성한다. 손으로 고치지 말 것 -->

### 레인 카탈로그

| 레인 | CLI | 최상위 | 표준 | Orca 실측 허용 | effort 전달 | 오르카 기동 | 정격 |
|---|---|---|---|---|---|---|---|
| `claude-opus-5` | claude | `ultracode` | `standard` | `standard` · `ultracode` (와이어는 항상 `--effort max`) | 프롬프트 키워드 | ✅ `--model`·`--effort` 가능 | 1M |
| `claude-fable-5-1` | claude | `max` | `high` | `low` · `medium` · `high` · `xhigh` · `max` | `--effort` | ✅ `--model`·`--effort` 가능 | 1M · 쿼터 fableWeekly 별도 · API 단가 Opus 5의 2배 |
| `gpt-6-astra` | codex | `xhigh` | `high` | `minimal` · `low` · `medium` · `high` · `xhigh` | `--effort` | ✅ `--model`·`--effort` 가능 | 272K(최대 872K) · Orca 상한 xhigh |
| `gpt-5.6-sol` | codex | `ultra` | `high` | `minimal` · `low` · `medium` · `high` · `xhigh` · `max` · `ultra` | `--effort` | ✅ `--model`·`--effort` 가능 | 272K(최대 872K) |
| `gpt-5.6-terra` | codex | `max` | `medium` | `minimal` · `low` · `medium` · `high` · `xhigh` · `max` · `ultra` | `--effort` | ✅ `--model`·`--effort` 가능 | 272K(최대 872K) |
| `gpt-5.6-luna` | codex | `medium` | `low` | `minimal` · `low` · `medium` · `high` · `xhigh` · `max` | `--effort` | ✅ `--model`·`--effort` 가능 | 272K(최대 872K) · 최저가 |
| `gpt-daybreak-blue-latest` | codex | `xhigh` | `high` | `minimal` · `low` · `medium` · `high` · `xhigh` | `--effort` | ✅ `--model`·`--effort` 가능 | 보안 전용 · 기본 low · Orca 상한 xhigh |
| `gemini-3.8-flash` | antigravity | `high` | `medium` | — **지정 불가** (그 CLI 기본값) | **슬러그 내장** | ❌ **Orca 워커 불가** (agent 미등록·과제 전달 실패 — CLI 직행만) | Gemini Flash 계열 |
| `grok-4.6` | grok | `xhigh` | `high` | — **지정 불가** (그 CLI 기본값) | `--effort` | ⚠ `--agent` 만 — `--model` 거부 | 500K · 200K초과 2배 과금 |

**「Orca 실측 허용」은 2026-09-06 에 전수 측정한 값이다** — `python scripts/routing.py --probe-efforts --task <실재 task_id>` 로 언제든 다시 잰다(워커가 안 뜨므로 비용 0). `models_cache.json` 이 지원한다고 적는 값과 **다르다**: astra·daybreak 은 CLI 에서는 `ultra`·`max` 가 돌지만 Orca 워커로는 `xhigh` 가 상한이다. 정책 두 단(최상위/표준) 밖의 값을 쓰려면 `allow_off_ladder=True` 를 명시한다.

⚠ **Orca 는 `--model` 문자열을 검증하지 않는다** — 존재하지 않는 슬러그도 `high`·`xhigh` 면 통과하고, 워커가 뜬 뒤 codex 가 죽는다. 이 표의 레인 키가 사실상 유일한 오타 방어선이다.

**오르카 기동은 2026-09-04 실측이다.** `--model` 은 Claude·Codex·Cursor 만 받는다 (orca help) — grok·gemini 는 `--agent` 만 주고 모델은 그 CLI 의 기본값이 쓰인다. ⚠ **agent id 는 CLI 이름이 아니라 좌석 이름이다**: `--agent agy` 는 `agent_unconfigured` 로 거부되고 `--agent antigravity` 가 정본이다. (CLI 바이너리는 `agy`, Orca 등록명은 `antigravity`.)

**배정 금지**: `codex-auto-review` · `gpt-5.3-codex-spark` · `gpt-5.4-mini` · `gpt-reserve` — 용도 미검증 / R&R 미확정 (발주 §3) · **D-28**: 코딩은 공정 전용 목록 `PROCESS_LANES` (claude 전용 · codex 폴백 없음 · #5) · 반증 "예"인 A 작업은 B 비코딩 목록으로 승격(#11) · `claude-fable-5-1`·`claude-sonnet-5` 는 실워커 1회(M1) 전까지 목록 밖 · gemini `unavailable`(M6) → `references/d28-routing.md`

### 공정 → 클래스 → 레인

| 공정 | 클래스 | 1순위 | 2순위 | 3후보 |
|---|---|---|---|---|
| 대량 정형 변환 · 카운트 | A | `gpt-5.6-luna` | `claude-opus-5` | — |
| 인벤토리 · 스키마 검증 | A | `gpt-5.6-luna` | `claude-opus-5` | — |
| 디스크 스캔 · grep | A | `gpt-5.6-luna` | `claude-opus-5` | — |
| 장문 로그 · 커밋히스토리 분류 집계 | A | `gpt-5.6-luna` | `claude-opus-5` | — |
| 웹 리서치 — 정독 · 모순 종합 | B | `gpt-6-astra` | `claude-opus-5` | — |
| 코딩 — 구현 · 대규모 리팩터링 **(공정 전용 목록)** | B | `claude-opus-5` | — | — |
| 터미널 · CI · git (판단 섞인 경우) | B | `gpt-6-astra` | `claude-opus-5` | — |
| 보안 — 생성물 안전성 게이트 | B | **`gpt-daybreak-blue-latest` @xhigh 고정** | — | — |
| 보안 — 비즈니스 로직 · 인가 | B | **`gpt-6-astra` @xhigh 고정** | — | — |
| 트렌드 · 실시간 | C-realtime | `grok-4.6` | `gpt-5.6-sol` | `claude-opus-5` |
| 웹 리서치 — 수집 | C-realtime | `grok-4.6` | `gpt-5.6-sol` | `claude-opus-5` |
| Google 플랫폼 (BigQuery/Firebase/Workspace) | C-platform | `gemini-3.8-flash` | `gpt-5.6-sol` | `claude-opus-5` |
| UI 시각 검증 | C-platform | `gemini-3.8-flash` | `gpt-5.6-sol` | `claude-opus-5` |
| 다레인 산출물 조립 | D | **`claude-opus-5` @ultracode 고정** | — | — |
| 워크트리 · run 관리 (orca CLI) | N | — | — | — |

### effort 결정 — 클래스가 아니라 태스크 속성

> **반증 가능한 전제가 있나?** ("X는 죽었다"를 확인 / "A가 B보다 낫다"를 판정 / 원인 규명)

| | `claude-opus-5` | `claude-fable-5-1` | `gpt-6-astra` | `gpt-5.6-sol` | `gpt-5.6-terra` | `gpt-5.6-luna` | `gpt-daybreak-blue-latest` | `gemini-3.8-flash` | `grok-4.6` |
|---|---|---|---|---|---|---|---|---|---|
| **YES** 최상위 | `ultracode` | `max` | `xhigh` | `ultra` | `max` | `medium` | `xhigh` | `high` | `xhigh` |
| **NO** 표준 | `standard` | `high` | `high` | `high` | `medium` | `low` | `high` | `medium` | `high` |
| 사다리 밖 상한 (`allow_off_ladder`) | `ultracode` | `max` | `xhigh` | `ultra` | `ultra` | `max` | `xhigh` | — (지정 불가) | — (지정 불가) |

셋째 줄이 **물리적 상한**이다. 둘째 줄까지가 기본 경로고, 셋째 줄까지는 `allow_off_ladder=True` 를 명시해야 열린다 — 원장에 `off_ladder` 로 남는다. 그 위(`ultra`·`max` on astra/daybreak)는 Orca 가 거부하므로 **없는 값**이다. 거기가 정말 필요하면 워커가 아니라 codex 직행이다 (`run_codex_exec`).

코디네이터 레인 = **`gpt-5.6-sol` @xhigh** — 종합(D)과 벤더가 달라야 한다. 워커 겸임은 클래스와 무관하게 경고한다(D-28 #6).

### 레인별 산출물 제약

| 레인 | 허용 | 금지 | 사유 |
|---|---|---|---|
| `grok-4.6` | CSV · 카운트 · 분류 라벨만 | 서술 결론 · 인과 추정 · 200K 초과 입력(과금 2배) | 사실 신뢰도가 4레인 중 최약. 합계는 D 레인이 산술 재검산한다 |
| `gemini-3.8-flash` | 발견 목록 + 탐색 드라이브 · 제외 경로 · 스캔 파일 수 | 범위 없는 '0건' 반환 · 무인 장기 루프 단독 배치 | 부재 보고 오류가 직전 라운드 오류 5건 중 3건의 원인 |
| `gpt-5.6-luna` | 정형 변환 · 카운트 · 분류 · **부재 보고에는 탐색 범위 명시** | 우열 판단 (필요하면 terra 이상으로 올린다) · 범위 없는 '0건' | 최저가 레인 — 판단을 맡기면 싼 값에 틀린다. 범위 요구는 Simon 결정(2026-09-04, luna03 채택)으로 A 클래스 전체에 적용된다 |
| `claude-opus-5` | 항목별 확신도 표기 필수 (강=기계검증 / 약=판단) | 리포트만 내고 끝내기 — 사람이 읽는 것은 결정 시트 1장이다 | 종합 레인이므로 사람의 결정으로 이어져야 한다 |
| `gpt-6-astra` | 판단마다 근거(파일·행·명령 출력) 첨부 · 반증 시도 1건 이상 명시 | 대량 정형 변환에 배치 (A 클래스는 luna 로 내린다) · `ultra`/`max` 로 Orca 디스패치 (거부된다 — 상한 xhigh) | codex 계열 최상위 좌석이다. 싼 일에 태우면 쿼터만 태우고, 정책 밖 effort 로 부르면 워커가 아예 안 뜬다 |
| `gpt-daybreak-blue-latest` | 취약점 발견마다 file:line · 재현 경로 · 심각도 · 최소 패치 | 방어 목적 밖의 공격 코드 생성 · 범위 없는 '취약점 0건' | 보안 전용 레인 — 근거 없는 발견은 게이트를 무력화한다. 출력이 차단되면 Trusted Access 미승인이므로 terminal read 로 확인한다 |

### 가드

| | 내용 | 자동 검출 |
|---|---|---|
| G1 | 짠 레인이 자기 코드를 보안 리뷰하지 않는다 | ✅ 원장 기록 |
| G2 | 자기 결론 재검증에 서브에이전트를 쓰지 않는다 — 반증은 리포트 '§X 반증 시도' 섹션 | — (오검출 방지) |
| G3 | 워커당 spawn 상한 8 | ✅ 원장 기록 |
| G4 | 쿼터 게이트는 디스패치 시점에만. 실행 중 중단 근거로 쓰지 않는다 | — (오검출 방지) |
| G5 | 쿼터는 4벤더 각각 확인한다 | ✅ 원장 기록 |
| G6 | 부재 보고에는 탐색 범위를 붙인다. 범위 없는 '0건'은 반환값 불인정 — gemini 뿐 아니라 **A 클래스 전체**에 적용 (Simon 결정 2026-09-04) | — (오검출 방지) |
| G7 | 최상위 effort 는 반증질문 YES 인 태스크에만 | — (오검출 방지) |
| G8 | 쓰기 라운드는 **워커 강제종료 절차가 선 상태에서만** 띄운다 — `python scripts/kill_worker.py --dispatch <ctx_…>` (기본은 목록만, `--kill --fence` 로 트리 종료 → 재스캔 0 확인 → worker-stop). worker-stop 은 프로세스 사망을 약속하지 않는다. 원래 문구 '문서화 전까지 착수 금지'는 2026-09-13 문서화·실측 1회로 충족 — SKILL.md '워커 강제종료 (G8)' | — (오검출 방지) |
| G9 | Move-Item 배치는 매니페스트 + 역방향 스크립트 선행 | — (오검출 방지) |
| G10 | 적대적 평가에서 채점자는 두 생산자와 **벤더가 달라야** 한다. 벤더 3개를 못 채우면 그 문제는 건너뛴다 — 자기 벤더가 자기 답을 채점하느니 관측을 포기한다 (`adversarial_eval.py`) | — (오검출 방지) |
| G11 | 디스패치 전에 툴체인 최신화를 확인한다 — codex 가 한 버전만 뒤처져도 `Agent startup blocked: codex-update-prompt` 로 **전 워커가 안 뜨는데 에러가 프롬프트 문제처럼 보인다** (2026-09-12 실사고). `python scripts/check_tooling.py` | — (오검출 방지) |
| G12 | **벤더 가용성은 쿼터로 판정하지 않는다 — 실호출로 확인한다.** 2026-09-13 실측: grok 은 402(잔액 소진), gemini 단독 CLI 는 IneligibleTierError 였는데 **쿼터 %로는 둘 다 여유 있어 보였다** — 못 쓰는 이유가 쿼터가 아니었기 때문이다. 쿼터 게이트(G5)는 '얼마나 썼나'를 보고, 이건 '지금 답이 나오나'를 본다. 다른 질문이다. `python scripts/adversarial_eval.py --preflight` | — (오검출 방지) |
| G13 | 재시도(`worker-start --retry-of`)·수동 재배정도 계획 검증을 다시 통과해야 한다 — `routing.revalidate_for_retry(plan, proc, new_lane, ...)` 가 (ok, 위반, 메모, 새 계획)을 준다. `--retry-of` 는 orca CLI 를 직접 부르므로 routing 의 계획 검증을 거치지 않는다 (D-28 #14) | — (오검출 방지) |
| G14 | 결정 시트(`make_decision_sheet.py`)를 만들지 않은 라운드는 **끝난 것으로 치지 않는다** — 손으로 조립한 시트는 `decisions_run_*.json` 을 내지 않아 채택률이 비고 스왑 규칙이 돌지 않는다 (D-28 #15) | — (오검출 방지) |

쿼터: 60% 초과 → **모든 순위에서** 강등(ok 레인이 없으면 첫 강등 레인) · 85% 초과 → 사용 금지 · 읽기 실패 = **미확인**(0%로 간주 금지) · 실호출(G12) 실패 = 사용 금지 · 실호출 결과가 24시간 넘으면 미확인 · `quota_bucket` 이 있는 레인(fable)은 그 버킷으로 판정 (D-28 #13)

<!-- ROUTING:END -->

---

## 모드 A — 인테이크 폼 (인자 없이 `/vibe`)

```bash
python "<skill>/scripts/make_intake.py"
```

출력 경로(`E:\Coding Infra\reports\vibe-intake.html`)를 브라우저로 열고 **거기서 멈춘다.**

폼이 실행될 때마다 하는 일:
1. **4벤더 쿼터**를 각각 읽는다 (`orca account list --json` 하나로 claude/codex/gemini/grok 전부 나온다)
2. 쿼터를 반영해 **클래스별 기본 레인을 미리 채운다** — 안 건드리면 그대로 간다
3. **다운로드 폴더의 `decisions_run_*.json`을 자동 회수**해 원장에 합치고 파일을 소비한다
4. 미회수 run이 3개 이상이면 **"학습 정지 상태"** 경고를 띄운다

폼을 연 뒤 한 줄만 말한다: *"폼에서 고르고 [복사] 눌러 붙여넣어 주세요."* **추측으로 먼저 시작하지 않는다.**

## 모드 B/C — 실행

### 0-A. 툴체인 최신화 — 쿼터보다 먼저 본다

```bash
python "<skill>/scripts/check_tooling.py"     # 뒤처졌으면 종료코드 1
```

**codex 가 한 버전만 뒤처져도 전 워커가 안 뜬다.** 그런데 에러가 프롬프트 문제처럼 보인다:

```
dispatch 실패 → lastError: agent_prompt_blocked          ← 내용 탓으로 오독하기 쉽다
최소 프롬프트로 갈라보면 → Agent startup blocked: codex-update-prompt
```

2026-09-12 에 이걸로 스펙을 두 번 다시 썼다. 원인은 codex-cli 0.153.4 / 최신 0.154.0 이었고,
올리니 세 워커가 그대로 떴다. **갈라보는 방법은 최소 프롬프트 한 줄을 같은 레인에 던지는 것**이다 —
그래도 막히면 내용이 아니라 툴이다.

이 스크립트는 **자동으로 설치하지 않는다.** 전역 npm 패키지는 같은 머신의 다른 세션에 영향을 준다.
올리기 전에 실행 중인 codex 프로세스를 보고, **CPU 0초로 멈춰 있으면 그것도 이 프롬프트에 걸린
워커다**(죽여도 된다). 일하는 중이면 기다린다.

`orca skills list` 스냅샷도 같이 대조해 추가·삭제·설명 변경을 알린다
(`state/orca-skills.json`). 변경이 보이면 그 스킬 문서를 다시 읽는다 — 오르카의 명령 정본은
이 문서가 아니라 `orca skills get <이름>` 이다.

### 0. 프리플라이트 — 건너뛰지 않는다

```python
import sys; sys.path.insert(0, "<skill>/scripts")
import routing
ok, status = routing.run_orca_json("status")
ok, acct  = routing.run_orca_json("account", "list")   # 4벤더 각각
```

- 어느 벤더 60% 초과 → **그 레인을 쓰는 태스크만** 2순위로 강등
- 어느 벤더 85% 초과 → 그 레인 사용 금지. 후보가 없으면 **축소안을 제시**하고 승인받는다
- 읽기 실패 → **"미확인"**으로 표시하고 1순위 유지. **0%로 간주하지 않는다**
- `claude.fableWeekly` 100%면 fable을 워커로 쓰지 않는다

### 1. 공정 분류 → 클래스 → 레인

과제를 공정으로 쪼개고 각 공정을 위 표의 클래스에 넣는다. **디스패치 결정과 학습 집계는 클래스 단위로만 한다.**

태스크마다 **반증질문**에 예/아니오를 정한다(폼 답이 있으면 그대로, 없으면 **아니오**):
> 반증 가능한 전제가 있나? — "X는 죽었다"를 확인 / "A가 B보다 낫다"를 판정 / 원인 규명

**착수 전 한 줄로 알린다**: 분류 결과 · 예상 워커 수 · 어느 태스크가 탐색 슬롯인지.

### 2. Run + 작업 DAG

```python
ok, run  = routing.run_orca_json("orchestration", "run-create",
                                 "--objective", objective)          # 인용 불필요
ok, task = routing.run_orca_json("orchestration", "task-create",
                                 "--run", run["run"]["id"],
                                 "--spec", spec)                    # 인용 불필요
```

`objective`·`spec` 은 사람이 쓴 자유 문자열이다. `run_orca_json()` 은 셸을 거치지 않으므로
`$(...)`·`;`·백틱이 확장되지 않는다. **셸 문자열로 조립해 실행하지 말 것.**

추가 조건에 **"먼저 계획만"**이 있으면 여기서 `task-list --brief --json`을 보여주고 **종료한다**(비용 0).

### 3. 워커 기동 — effort를 반드시 박는다

디스패치는 **`routing.validate_and_dispatch()`로만 한다.** 계획 검증을 통과해야 실행된다 — 필수 보안 게이트 부재 · 4벤더 쿼터 미확인 · 금지 레인 · 고정 레인 오버라이드를 코드가 막는다.

```python
import sys; sys.path.insert(0, "<skill>/scripts")
import routing

plan = [
    {"proc": "coding",                 "lane": "claude-opus-5", "class": "B", "falsifiable": True},
    {"proc": "security-artifact-gate", "lane": "gpt-5.6-sol",   "class": "B"},
    {"proc": "security-bizlogic-2nd",  "lane": "gpt-5.6-terra", "class": "B"},
]
ok, results, violations, notes = routing.validate_and_dispatch(
    plan,
    task_of={"coding": task_a, "security-artifact-gate": task_b, "security-bizlogic-2nd": task_c},
    spec_of={"coding": spec_a, ...},          # claude 최상위는 spec 이 **필수**다
    worktree="current",                       # 필수 — 외부 셸에서는 보통 current
    quota_checked_vendors=["claude", "codex", "gemini", "grok"],
)
if not ok:
    # 아무것도 실행되지 않았다. violations 를 보고 계획을 고친다.
    raise SystemExit(f"계획 검증 실패: {violations} {notes}")
```

낱개로 부를 때도 서명을 지킨다 — **`worktree` 는 필수**이고 반환은 **4개**다:

```python
rc, out, err, meta = routing.run_dispatch(
    "claude-opus-5", "ultracode", task_id, worker_name, "current", spec=spec)
# meta["spec"] 을 그대로 task-create --spec 으로 넣어야 ultracode 가 실제로 발동한다.
# spec 없이 최상위 claude 를 부르면 ValueError 로 막힌다 — meta 에만 남고
# 워커에는 전달되지 않아 조용히 표준 effort 로 도는 것을 방지한다.
```

⚠ **배열을 문자열로 다시 합치지 말 것 (감사 HIGH-6, 2026-09-04).**
argv 배열을 문자열로 이어 붙여 셸에 넘기면 안전성이 사라진다 — 워커 이름이
`safe; Write-Output X`면 배열에서는 한 인자지만, 이어 붙인 문자열을 셸이 읽으면
두 명령으로 갈라진다. `dispatch_argv()`는 **표시·검토용**이고 실행은
`run_dispatch()`가 `shell=False`로 한다. 확인만 하려면 `dry=True`가 argv 를 JSON 으로 돌려준다.

**orca 호출은 전부 `routing.run_orca()` / `run_orca_json()` 하나로 한다.**
timeout·returncode·stderr redaction 이 그 안에 있다. 자유 문자열은 그냥 인자로 넘기면 된다 —
셸을 거치지 않으므로 인용이 필요 없고, 인용으로 막으려 하지도 말아야 한다.

⚠ **"PowerShell 로 부르면 안전하다"는 생각은 틀렸다.** PowerShell 도 큰따옴표 안의
`$(...)`를 확장한다. Git Bash 는 거기에 더해 `/`로 시작하는 인자를 경로로 바꾼다
(`/vibe …` → `C:/Program Files/Git/vibe …` 로 실제 오염된 적이 있다).
**어느 셸이든 자유 문자열을 명령 문자열에 넣지 않는 것이 유일한 방어다.**

| 레인 | 나오는 형태 |
|---|---|
| codex | `--model <slug> --effort <값>` — **빼면 sol·astra·daybreak 이 조용히 기본값(low/medium)로 돈다** |
| grok · agy | `--agent` 만. **`--model` 을 주면 거부**되고, `--effort` 는 `--model` 을 요구하므로 **effort 지정 자체가 불가능**하다 — 그 CLI 의 기본값이 쓰인다 |
| claude | `--model claude-opus-5 --effort max` + **프롬프트 첫 줄에 `ultracode`** |

**정책 밖 effort 를 쓰려면 명시한다.** 기본 경로는 `top`/`std` 두 단이고, 그 밖의 값(예: 라운드가 가벼워서 `astra@medium` 으로 내리고 싶을 때)은 `allow_off_ladder=True` 를 붙여야 열린다. 원장에 `off_ladder` 로 남는다.

```python
plan = [{"proc": "research-deep", "lane": "gpt-6-astra", "class": "B",
         "effort": "medium", "off_ladder": True}]   # 의도한 하향임을 명시
```

`ultra`·`max` 를 astra·daybreak 에 주면 **계획 검증에서 `EFFORT_NOT_ALLOWED` 로 막힌다** — 한 건도 디스패치되지 않는다. Orca 가 안 받는 값이기 때문이고, 이건 정책이 아니라 물리적 사실이다.

워커 과제 서술에 반드시 넣는다: 검증 가능한 완료조건 · 건드리지 말 것 · **레인별 산출물 제약**(위 표) · 끝나면 `worker_done` 보고.

**배정 검증** — 디스패치 전에 돌린다:
```python
routing.check_guards(assignments, quota_checked_vendors, spawn_counts)   # G1·G3·G5·탐색오배정
routing.coordinator_conflict(assignments)   # 코디네이터 레인이 워커를 겸임(클래스 무관, D-28 #6) · 재시도 전엔 revalidate_for_retry()(G13)
```

✅ **D-260904-01 — 보안 검사 배정 (Simon 결정, 2026-09-04)**

판단이 가능한 벤더는 **claude·codex 둘뿐**인데 역할은 셋(구현·생성물검사·인가검사)이다. 셋을 모두 다른 벤더에 두는 배치는 **존재하지 않는다**(비둘기집). 그래서 우선순위가 낮은 제약을 양보했다.

| | 배정 | 벤더 |
|---|---|---|
| 코딩 (공정 전용 목록 `PROCESS_LANES`, D-28 #5) | `claude-opus-5` | claude |
| 생성물 안전성 게이트 | `gpt-daybreak-blue-latest` @xhigh | codex |
| 비즈로직·인가 게이트 | `gpt-6-astra` @xhigh  *(2026-09-06, 직전 `gpt-5.6-terra` @high)* | codex |

- **지킨 것** — 코딩 ≠ 두 게이트 모두. **자기채점 0.** G1을 HARD로 승격했고 `G1_BIZLOGIC` 임시 분기는 없앴다
- **양보한 것** — 두 게이트가 같은 codex 벤더가 되는 것(발주 §5 한 줄). 대신 **다른 모델**을 강제한다: `daybreak@xhigh` vs `astra@xhigh`. 같은 모델이 두 축을 겸하면 `G1_SEC_SAME_MODEL`로 잡는다
- ⚠ **2026-09-06 로 구분자가 바뀌었다.** 예전에는 "모델도 effort 상한도 다르다"였는데 astra 와 daybreak 은 **상한도 effort 도 둘 다 xhigh** 다(둘 다 Orca 의 `unknownModelOptions` 로 떨어지기 때문이다). 지금 두 게이트를 가르는 것은 **모델 성격**이다 — daybreak 은 `model_specialty="cyber"` 전용, astra 는 범용 프론티어. "상한이 달라서 안전하다"를 근거로 인용하지 말 것

> **2026-09-04 갱신 — 생성물 게이트를 `gpt-5.6-sol` → `gpt-daybreak-blue-latest` 로 옮겼다.**
> Simon 이 codex 모델 선택지에서 찾아냈다. 정본은 `~/.codex/models_cache.json`:
> display_name **"Daybreak Blue"**, *"Latest frontier agentic coding model for
> broad defensive cybersecurity work."* — **보안 전용 프론티어 모델**이다.
> sol 은 범용 워크호스("Reliable agentic workhorse")였으니, 보안 자리에 보안 모델을 놓는다. *(D-28 #16: 2026-09-13 models_cache 에서 sol 은 priority 1 "Latest frontier agentic coding model." 로 바뀌었다 — 이 문장은 09-04 기록이다)*
> 벤더는 여전히 codex 라 위 양보는 그대로고, 개선된 것은 **모델 적합성**뿐이다.
> 부수 효과로 sol 이 게이트에서 풀려 **코디네이터 겸임 충돌이 사라졌다.**
> ⚠ daybreak 도 **기본 effort 가 low** 다 — sol 과 같은 함정. effort 명시는 코드가 강제한다.

> **⚠ 전제 — codex 보안 게이트는 Trusted Access 승인이 있어야 작동한다 (2026-09-04 실측).**
> 승인이 없으면 codex는 감사를 **수행하고도 결과 출력만 차단**한다:
> `This content can't be shown / We take extra caution with cybersecurity requests`.
> 이건 **조용한 실패**다 — `worker_done`이 안 오고 산출 파일도 안 쓰이며 태스크가
> `dispatched`에 멈춘 것처럼 보인다. 진단은 `orca terminal read` 로 터미널 실물을 읽는 것뿐이다.
> 신청처는 `https://openai.com/daybreak/` (= Trusted Access). Simon 계정은 2026-09-04 승인 완료.
> **승인이 없는 계정·머신에서는 이 배정을 쓰지 말 것** — 게이트를 claude 로 돌리되
> 구현자와 벤더가 겹치지 않는지 반드시 확인한다.

> 지시는 "두 게이트가 같은 codex가 되면 생성물게이트를 claude로 맞바꿔라"였으나, 그렇게 하면 코딩과 생성물게이트가 모두 claude가 되어 **짠 쪽이 자기 산출물을 검사하는 HARD G1**이 된다. 옮기려던 문제보다 나쁘다. `selftest.py`의 "정본 기본 배정이 가드를 통과한다" 케이스가 이걸 잡는다 — 표를 고칠 때마다 여기서 걸린다.

### 3-2. codex 직행 — Orca 상한을 넘어야 할 때만

Orca 워커로는 astra·daybreak 에서 `xhigh` 가 끝이다. 그 위가 필요하면 codex CLI 를 직접 부른다.

```python
rc, out, err = routing.run_codex_exec(
    prompt,                       # stdin 으로 들어간다 — 인자로 넣지 않는다
    model="gpt-6-astra", effort="ultra",
    sandbox="read-only",          # 기본값. 격리가 없으니 쓰기는 워커로 보낸다
    cwd=worktree_path, timeout=1800)
```

**이건 워커가 아니다.** 차이를 알고 쓴다:

| | Orca 워커 | codex 직행 |
|---|---|---|
| 워크트리 격리 | 있다 | **없다** — 이 셸의 cwd 에서 돈다 |
| `worker_done` · 게이트 · `worker-release` | 있다 | **없다** — 동기 블로킹 호출 |
| 원장 dispatch 행 | 자동 | **직접 넣어야 한다** |
| 도달 가능한 effort | astra `xhigh` 까지 | `max` · `ultra` 까지 |

- 쓸 자리: 워커 하나를 통째로 띄울 값어치는 없는데 **최상단 추론이 필요한 단발 판정**
- **G1 은 그대로다** — 짠 쪽을 이 경로로 우회시켜 자기 산출물을 검사하게 하지 말 것
- 기본 `sandbox="read-only"` 를 올리기 전에 "워커로 보내면 되는 일 아닌가"를 먼저 본다

## 4. 탐색 슬롯 — 라운드당 1개

A 클래스 태스크 하나(없으면 B의 비고정 공정)를 **2순위 레인**으로 강제 배정하고 `explore:true`로 기록한다.
- 후보 중 **무작위**로 고른다 — 항상 첫 태스크를 고르면 난이도 편향이 생긴다
- **제외**: D · 보안 게이트 2종 · 코딩(공정 전용 목록 — 2순위 없음) · 되돌릴 수 없는 태스크 · 2순위가 Orca 로 안 뜨거나 실호출에 실패한 공정 — 후보는 `routing.explore_candidates()` 결과만 (D-28 #12)
- 추가 조건에 "탐색 슬롯 끄기"가 있으면 건너뛴다

### 5. 디자인 게이트 — 로컬호스트 컨펌

`화면 확인`이 "로컬호스트"면 디자인 워커 과제 서술 끝에 못박는다:
*"끝나면 `npx expo start --web --port <할당포트>`로 서버를 **띄운 채로 두고** worker_done을 보고할 것."*

```python
routing.run_orca_json("tab", "create", "--url", f"http://localhost:{port}")
routing.run_orca_json("screenshot", "--format", "png")        # 내가 먼저 픽셀 확인
routing.run_orca_json("orchestration", "gate-create", "--task", task_id,
                      "--question", f"localhost:{port} 컨펌?",
                      "--options", '["통과","재작업"]')
```

포트는 워크트리마다 `8090`부터. **명백히 깨진 화면은 올리지 않는다.** 대기 중에도 다른 단계는 계속 돌린다.

### 6. 수확 · 정리

```python
ok, res = routing.run_orca_json("orchestration", "check", "--run", run_id, "--wait",
                                "--types", "worker_done,escalation,question",
                                "--timeout-ms", 900000, timeout=960)
routing.run_orca_json("orchestration", "worker-release", "--dispatch", dispatch_id)
routing.run_orca_json("worktree", "set", "--worktree", "active",
                      "--comment", comment,                  # 자유 문자열
                      "--workspace-status", "in-progress")
```

`worker_done`은 **성공·실패 모두** release 대상. 타임아웃·유휴·질문은 release 사유가 **아니다**.

⚠ **G4** — 쿼터를 근거로 **실행 중인 워커를 중단시키지 않는다.** 직전 라운드에서 이 오판으로 최고 품질 워커를 죽였다(고아로 1h17m 더 살아 완성했다). 03:00에 쿼터 읽기가 0%로 실패한 실적도 있다.

### 6-2. 워커 강제종료 (G8) — 2026-09-13 문서화 · 실측

`worker-stop` 은 **Dispatch 를 fence 하고 터미널을 멈춘다**까지만 약속한다 — 프로세스가 죽었다는 약속이 아니다(help 원문). `worker-abandon` 은 프로세스에 손대지 않고, `worker-release` 는 끝난 워커의 터미널만 닫는다. `terminal show` 는 PID 를 주지 않는다(ptyId 만).

대신 **워커 셸과 에이전트가 전부 환경변수 `ORCA_TERMINAL_HANDLE=<handle>` 을 갖는다.** 구조는 `Orca.exe(터미널 호스트) → pwsh(터미널마다) → claude.exe · agy.exe · codex → 도구 하위 프로세스` 이고, 코디네이터 세션은 **다른 handle** 이다. 그래서 dispatch → handle → 환경변수로 정확히 그 워커 트리만 고른다. handle 은 `worker-list --json` 의 `agentTerminalHandle` 이다.

```bash
python "<skill>/scripts/kill_worker.py" --dispatch ctx_…               # 목록만 (기본)
python "<skill>/scripts/kill_worker.py" --dispatch ctx_… --kill --fence
#   terminate → 8초 대기 → kill → 재스캔. left_after 가 [] 이고 verified 가 true 여야 끝난 것이다
#   종료코드: 0 확인됨 · 1 잔존 · 2 handle 못 찾음 · 3 자기 자신/조상이 대상에 섞임(거부)
```

- 대상은 **handle 이 같은 프로세스 + 그 자손**이다. 워커가 띄운 에뮬레이터 · adb 도 환경변수를 물려받으므로 같이 내려간다
- 자기 터미널 handle 이거나 **이 스크립트의 조상 PID** 가 섞이면 아무것도 하지 않고 3 으로 끝난다 — 코디네이터가 자기 세션을 죽이는 사고를 막는다
- 실측(2026-09-13 21:16): 폴더 신뢰 프롬프트에 걸려 과제를 못 받은 agy 워커 → 대상 2개(agy.exe · pwsh.exe) terminate 로 전부 종료 · 재스캔 0 · worker-stop ok · 터미널 목록에서 사라짐. 코디네이터 트리는 건드리지 않았다
- 강제종료한 task 는 `failed` 가 되어 재디스패치가 안 된다 — 같은 spec 으로 **새 task** 를 만든다
- 쓰기 워커를 죽였으면 그 워크트리의 미커밋 변경을 **지우기 전에 본다**(`git --no-optional-locks status`). 워커 산출물을 버릴지는 사람이 정한다

⚠ **워커에 과제가 안 들어가는 증상 — 2026-09-13 에 다섯 번 봤다(agy 2 · claude 2 · codex 1).** 겉모습이 같다: 워커 TUI 는 떴는데 입력창이 비어 있고, `worker-show` 의 stage 가 `input_accepted` 또는 `turn_start_unobserved` 에 머문다. 그대로 두면 계속 논다.
- **claude 1건은 고쳐졌다.** 첫 `worker-start` 가 rc=1 로 끝났고(출력은 못 잡았다) task 가 `blocked` 가 됐는데 워커 터미널은 살아 있었다. `--worktree id:<repoId>::<경로>` + `--timeout-ms 300000` 으로 **새 task** 를 띄우자 응답에 `turnStart: observed` 가 오고 과제가 들어갔다. "기본 대기 시간 안에 에이전트 턴이 시작되지 않으면 CLI 가 먼저 끝나고 과제 입력이 사라진다"는 **추론**이다 — 재현 1회로 고쳐진 것만 확인했다
- **claude 2번째(22:16)는 `id:` + `--timeout-ms 300000` 을 처음부터 줬는데도 났다.** 방금 `git worktree add` 한 **새 워크트리의 첫 기동**이었다. `worker-start` 는 `cli_failed rc=1`(stderr 빈 값), `worker-show` 는 `start_unknown` · "input was written and submitted, but turn start could not be verified (up to 30s)", `terminal read` 의 `draft:` 에는 과제 전문이 있는데 **화면 입력창은 빈 `❯`** 였다. 복구: `kill_worker.py --kill --fence`(7프로세스 · 재스캔 0) → `task-update --status failed` → **같은 task 에 `worker-start --retry-of <죽인 dispatch>`** 를 같은 워크트리 · agent 로 다시 → `turnStart: observed`. 두 번째 기동은 그 폴더를 이미 한 번 연 뒤라 빨랐다는 것은 **추론**이다. 새 워크트리로 보낼 때는 첫 시도가 이렇게 날 수 있다고 보고, 응답의 `turnStart` 부터 본다
- **agy 2건은 원인 미확정이다.** 한 번은 처음 여는 폴더의 `Do you trust the contents of this project?`(`agentWait.reason = codex-trust-workspace`)에 막혔고, Enter 로 기본값을 주는 사이 과제가 사라졌다. 두 번째는 신뢰가 끝난 폴더에서도 입력창이 5분 넘게 비었다 — 위 claude 와 같은 타임아웃이었을 수 있는데 **agy 를 `--timeout-ms` 로 다시 띄워 보지는 않았다.** 손으로 과제를 보내면 dispatch 별 `--dispatch-capability` 토큰이 없어 `worker_done` 을 못 보낸다
- **codex 1건(astra, 22:32)은 `turnStart: observed` 가 거짓이었다.** 응답은 observed 였는데 50분 뒤 보니 `worker-show` 단계가 `input_accepted` · 하트비트 0 · codex 프로세스 CPU 15초였고, 화면 입력창에 `[Pasted Content 3026 chars][Pasted Content 4125 chars]` 가 **전송 안 된 채** 걸려 있었다. 복구: `orca terminal send --terminal <handle> --enter` 한 번 → 곧바로 `Working` 으로 바뀌었다. **dispatch 가 그대로라 `worker_done` 토큰도 산다**(죽이고 재발주하는 것보다 싸다). ⚠ `--wait-submit` 은 `--text` 없이 쓰면 `invalid_argument` 다 — Enter 만 보낼 때는 빼고, 확인은 화면(`terminal read --screen`)으로 한다
- → 디스패치 응답의 `turnStart` 가 `observed` 여도 **몇 분 뒤 한 번 더** 본다 — 하트비트가 없고 화면에 붙여넣은 과제가 남아 있으면 먼저 `terminal send --enter`, 입력창이 비어 있으면 아래 절차다. `observed` 가 아니면 `kill_worker.py --kill --fence` 로 내리고 **새 task** 를 `--timeout-ms` 를 늘려 띄운다. gemini 레인은 `--timeout-ms` 로 한 번 재확인하기 전까지 Orca 워커 배정을 피하고, 꼭 필요하면 CLI 직행(`agy --print`)이다 — D-28 #12 로 routing.py 에서 `dispatch: unavailable`(해제 조건 M6)

⚠ **`--worktree current` 는 cwd 가 아니라 코디네이터 터미널의 워크트리다 (2026-09-13).** Orca 터미널 안에서 도는 세션은 환경변수 `ORCA_WORKTREE_ID` 를 갖고 `worker-start --worktree current` 는 그걸 쓴다. 전용 워크트리로 `cd` 한 뒤 불렀는데도 워커는 **코디네이터 워크트리**에서 떴다 — `orca worktree current` 명령만 cwd 를 본다(둘이 다르다). 쓰기 워커를 다른 워크트리로 보내려면 `--worktree id:<repoId>::<절대경로>` 를 쓰고, `orca worktree show --worktree id:…` 로 먼저 풀리는지 본다. 옛 기록("Orca 터미널 밖 셸에서는 `current` 만 통과")과 결과가 다른 이유는 코디네이터가 Orca 터미널 안에 있느냐로 보인다(추론)

⚠ **코디네이터 터미널 하나는 run 하나에만 묶인다.** `run-create` 가 새 run 으로 **다시 묶는다.** 그 뒤 옛 run 에 `check` · `task-update` · `worker-release` 를 부르면 `consumer_fenced`(`bound to <새 run>, not <옛 run>`)로 거부된다 — `task-list` 같은 읽기는 된다. 두 라운드를 겹쳐 돌리면 결과는 `task-list` 의 `result`(worker_done 본문이 들어 있다)로 읽고, 옛 run 을 정리할 때만 `orchestration run-use` 로 다시 묶는다

### 7. 결정 시트 → 채택률

```bash
python "<skill>/scripts/make_decision_sheet.py" <items.json> [출력.html]
```

항목마다 **어느 레인이 냈는지** 배지로 표시된다. Simon이 체크하고 **[결과 저장]**을 누르면 `decisions_<run_id>.json`이 다운로드되고, **다음 `/vibe` 실행 때 자동으로 원장에 합쳐진다.** Simon이 외울 새 명령은 없다. **이 시트 없이는 라운드가 끝나지 않는다(G14 · D-28 #15)** — 손으로 조립한 시트는 회수 경로가 없다.

### 8. 원장 append — 마지막 단계

```python
import ledger

# ⚠ orca 응답 객체를 그대로 넘기지 말 것 — ID 문자열을 꺼내서 넣는다.
#   run["run"]["id"] 같은 dict 를 넘기면 strict schema 가 거부한다.
run_id = run_result["run"]["id"]            # "run_26ad3eb182a7"
recs = [ledger.new_record(
    run_id,                                  # str
    "security-artifact-gate",                # task = 공정 ID (비식별, 영숫자·_·-·. 64자)
    "B",                                     # class ∈ A / B / C-realtime / C-platform / D / N
    "gpt-5.6-sol", "ultra",                  # lane·effort 는 routing 정본의 허용 쌍
    falsifiable=True, explore=False, status="done",
    sec=2100, retries=0, quota_delta={"codex": 1}, guard_violations=[])]
n, note = ledger.append_records(recs)        # 시크릿 스캔 → CAS 커밋
```

`note` 를 반드시 읽는다. `commit 완료(CAS)` 가 아니면 **커밋되지 않았거나 부분 성공**이다 —
`partial` 은 입력을 소비하지 않고 `.vibe-pending/journal.jsonl` 에 복구 정보를 남긴다.

- 워커 1개 = 1줄. 집계 키는 **(class, lane, effort)** — task로 집계하면 arm당 관측이 1이라 영원히 수렴하지 않는다
- **산출물 본문을 넣지 않는다.** 메트릭만
- `quota_delta`는 보조 신호다. 부정확하므로 스왑 판정의 주 근거로 쓰지 않는다
- **데몬·상시 폴링을 만들지 않는다** — 허브가 정확히 그 SPOF로 죽었다

### 9. 보고

§6 규격 HTML 1개. **실패·건너뛴 항목을 성공한 것보다 먼저.** 워커별 소모 · 만들어진 워크트리와 되돌리는 법 · 다음 1개.

---

## 집계 · 스왑 제안

```bash
python "<skill>/scripts/aggregate_ledger.py"        # 사람용 표
python "<skill>/scripts/aggregate_ledger.py" --json # 기계용
```

(class, lane, effort)별 채택률 · 중위 소요 · 실패율 · 재실행률. `explore:true` 관측은 **별도 컬럼**.

**스왑 제안 조건**: 같은 클래스에서 2순위 채택률이 1순위보다 **15%p 이상** 높고 **양쪽 관측이 각 5회 이상**.

- 제안은 **출력만** 한다. **표를 자동 수정하지 않는다**
- 승인은 Simon이 폼에서 누른다. **모델이 라우팅 표를 스스로 고치는 경로를 만들지 않는다**
- 관측이 부족하면 `관측 부족(n=N, 필요 5)`을 **명시 출력**한다. 침묵하지 않는다

## 가드레일

- **자동 머지 금지.** PR까지만
- **비용·파괴·시크릿**은 워커에게 위임하지 않는다
- 워커가 워커를 띄우려 하면 `nested_worker_depth_exceeded` — 우회하지 않는다
- 워커 산출물을 검증 없이 신뢰하지 않는다. **리뷰는 생략 가능한 단계가 아니다**
- 과제가 워커를 띄울 만큼 크지 않으면 `dev-orchestrator`로 넘기거나 인라인 처리한다
- **§7 가드를 학습 파라미터로 만들지 않는다** — 불변이다

## 주기 적대평가 — 영역별 최적 레인을 데이터로 정한다

라운드는 1순위만 태워 2순위 이하 관측이 안 쌓인다. 정답이 기계로 나오는 문항을 두 레인이 풀고 **벤더가 다른 제3 레인이 채점**한다(G10).
순서: `adversarial_eval.py --validate` → `--plan` → `--run --dry` → `--preflight`(G12 실호출) → `--run` → `--report`. 표는 자동으로 안 고친다 — 제안만.
규율 표 · 실행 경로(Orca 워커가 아니라 벤더 CLI 직행) · 문항 추가 규칙 → **`references/adversarial-eval.md`**

## 알려진 함정

Orca effort 상한 · 실패 task 재디스패치(`--retry-of`) · Windows `.cmd` 셔임 · codex 기본 effort · `check` 응답 모양 · Git Bash 경로 오염 등 20여 건 → **`references/pitfalls.md`**. 워커에 과제가 안 들어가는 증상과 G8 강제종료는 위 6-2 절에 있다.

## 관련 스킬

`dev-orchestrator`(단일 세션) · `simon-worktree`(격리 규칙) · `ai-debate`(결정 지점) · `simon-design-first`(디자인 방향) · `orca-cli`(오르카 명령 정본 — 버전 불일치 시 `orca skills get <이름>`이 우선)

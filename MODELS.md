# MODELS.md — 허브 AI 모델·effort 정본 (always-best)

> **목적**: 4-AI 허브의 모든 AI가 **항상 가장 높은 벤치마크 모델 + 최대 reasoning effort**를 쓰도록 강제한다.
> **기계 판독 정본 = `tools/models.json`** (hub-daemon.ps1이 읽어 spawn 플래그를 만든다). 이 문서는 사람용 요약.
> **갱신**: `model-benchmark-refresh` 일일 cloud schedule이 제공사별 최신 최고모델을 재조사해 둘 다 갱신한다(§ 갱신 절차).
> **마지막 점검**: 2026-06-14 (hub-upgrade-research workflow — 제공사별 병렬 웹검색 + 적대적 교차검증) · **2026-07-03 Claude fable-5 재핀**(재가용 확인, 세션 실구동 검증).

---

## 정본 표 (2026-06-14)

| AI | CLI | 최고모델 | effort 최대 | 선택/플래그 |
|---|---|---|---|---|
| **Claude** | `claude` | `claude-fable-5` (2026-07-03 재핀) | `max` | `--model fable` 또는 `/model` → Fable 5 → `/effort max` (영속: env `CLAUDE_CODE_EFFORT_LEVEL=max`) |
| **Codex** | `codex` | `gpt-5.5` | `medium` (Simon 핀) | `-m gpt-5.5 -c model_reasoning_effort="medium"` |
| **Grok** | `grok` | `grok-build` | `high` | `-m grok-build` + env `GROK_MODEL=grok-build` (grok-4.3 not in this CLI build) |
| **Antigravity** | `agy` (gemini sunset 06-18) | `gemini-3.1-pro-preview` | `high`(=max) | 인-윈도우 agy `"Gemini 3.1 Pro (High)"` / 데몬 헤드리스 `node tools/agy-pty/agy-headless.js` |

---

## usage 소진 시 자동 모델 폴백 (always-up)

> **목적**: 어떤 AI가 자기 최고모델의 **usage/quota를 다 쓰면**(429·QUOTA_EXHAUSTED·TerminalQuotaError·"usage limit") 멍하니 수 시간 쉬는 대신 **검증된 대체 모델로 갈아타 계속 일한다.**

| AI | primary | 소진 시 fallback | 근거(검증 2026-06-15) |
|---|---|---|---|
| **Claude** | `claude-fable-5` @ max (2026-07-03 재핀) | `claude-opus-4-8` @ max | fable 재가용 + Simon이 /model Fable 5 기본 설정(세션 검증). opus는 06-17~07-03 실사용 검증된 직전 핀. 인터랙티브는 정액이라 사실상 무한 |
| **Codex** | `gpt-5.5` @ medium (Simon 핀) | `gpt-5.5` @ **low** | Codex CLI가 노출하는 OpenAI 모델은 gpt-5.5뿐 → **같은 모델·낮은 effort**로 호출당 소비 절감. 진짜 저가 모델 id 생기면 교체 |
| **Grok** | `grok-build` @ high | `grok-composer-2.5-fast` @ high | `grok models`가 노출하는 유일한 대체(=CLI 기본). 호출 검증됨 |
| **Antigravity** | `gemini-3.1-pro-preview` @ high | `gemini-2.5-flash` @ high | FLASHOK 프로브로 호출 검증. ⚠ `gemini-3.5-flash`는 404(미존재)라 **금지** |

**동작 (hub-daemon.ps1)**: primary가 quota를 뱉으면 → 같은 사이클에서 fallback 모델로 **1회 재시도** → 이후 `$PrimaryReprobeAfter`(=6사이클 ≈ 1h)동안 fallback 유지 → 그 뒤 primary 재프로브(한도 리셋 가능성). fallback마저 소진이면 기존 quota-backoff(지수 백오프)로 인계.

**불변 원칙(중요)**: `fallback_model`은 **그 CLI가 실제 호출 가능한 진짜 모델 id**여야 한다. 환각/오타 id는 spawn을 조용히 죽인다(= grok-4.3 사건). 위 4개는 모두 프로브로 검증됨. 새 id 핀 전 반드시 `grok models`/FLASHOK류 프로브로 확인.

**인터랙티브(인-윈도우) AI**: 데몬이 아닌 창에서 도는 AI는 자기 활성화 프롬프트의 "한도 도달 시 fallback_model 전환" 지침을 따른다(prompts/*-activate.md).

---

## AI별 근거·주의 (검증됨)

### Claude — `claude-fable-5` @ max (2026-07-03 재핀)
- **2026-07-03 변경**: fable **재가용** 확인(Simon이 `/model` → Fable 5를 기본으로 저장, 세션이 `claude-fable-5`로 실구동 검증) → 06-17의 "fable 재가용 시에만 재핀" 조건 충족으로 재핀. Fable 5 = Claude 5 패밀리, Opus 위 Mythos급 티어.
- **주의**: `max`의 세션 간 영속은 env `CLAUDE_CODE_EFFORT_LEVEL=max`로만 가능. 인터랙티브 Claude Code는 정액(토큰 미과금). fable이 다시 불가해지면 opus-4-8로 롤백 핀(그 폴백은 sonnet-4-6@high).
- **폴백**: `claude-opus-4-8` @ `max` (직전 핀, 06-17~07-03 실사용 검증).

### Codex — `gpt-5.5` @ medium (Simon 핀, 2026-06-17)
- GPT-5.5(2026-04-23) = OpenAI 최신 프런티어, Codex CLI 기본. **`gpt-5.5-codex` 변종 없음 → `-m gpt-5.5`**. `xhigh`가 최대지만 **Simon이 `medium`으로 핀**(Pro Lite 프리미엄 풀 소비를 줄여 한도 도달 지연). 폴백 `low`.
- **주의**: 검증자 교정 — GPT-5.5 SWE-bench Verified ~82.6%(Claude Opus 4.8 88.6%보다 낮음). 그러나 *Codex 레인에서 쓸 수 있는 최고 OpenAI 모델*. gpt-5.6 루머(공식 id 미정) 주시.

### Grok — `grok-build` @ high
- **2026-06-14 교정**: 설치된 grok CLI(grok.com 로그인)는 `grok models`에서 **grok-build(default) + grok-composer-2.5-fast만** 노출. `grok-4.3`은 이 빌드에 없어 매 spawn에서 거부(`Couldn't set model grok-4.3: Invalid params: unknown`)되어 **grok 데몬이 조용히 죽고 있었음**(monitor에서 3h stale). 정본 원칙(=그 CLI가 실제 호출 가능한 최고 모델)대로 **grok-build**로 핀.
- **주의**: 미래 빌드가 grok-4.x를 노출하면 `grok models` 확인 후 재핀. reasoning_effort 노출은 빌드마다 다름 — `GROK_REASONING_EFFORT`는 grok-build가 무시할 수 있음(블로커는 effort가 아니라 모델 id였음).

### Antigravity — `gemini-3.1-pro-preview` @ high(=max)
- Gemini 3.1 Pro(2026-02-19) = Google 종합 1위(SWE-bench Verified 80.6%, ARC-AGI-2 77.1%, 16개 중 13개 벤치 선두). **thinkingLevel HIGH가 최대이자 3.1 Pro 기본값**.
- **주의**: Gemini CLI는 **2026-06-18 폐기 → agy(Antigravity CLI)로 이관**. agy 모델 라벨 `"Gemini 3.1 Pro (High)"`의 `(High)`가 최대 thinking(agy 기본은 `Gemini 3.5 Flash (High)`이라 override 필요).
- **데몬 헤드리스 수정 (2026-06-17)**: `agy -p`/`gemini -p`는 stdout 리다이렉트 시 ~0바이트만 뱉어 **AG 좌석이 조용히 no-op**(exit 0·빈 transcript·STATUS 수시간 stale)됐다. hub-daemon.ps1 AG 레인을 **ConPTY 래퍼 `tools/agy-pty/agy-headless.js`로 교체**(node + node-pty 필요, `npm install` 1회). 인-윈도우 agy(실제 터미널)는 정상이므로 데몬 대신 인-윈도우로 돌려도 됨.
- Gemini 3.5 Flash가 일부 에이전트-코딩 벤치에서 3.1 Pro를 더 낮은 비용에 상회(방어가능한 대안).

---

## 갱신 절차 (일일 로컬 예약작업 — 제안+게이트)

- **예약작업** `HubModelBenchmarkRefresh` (Windows Scheduled Task, 매일 09:00 KST) → `tools/refresh-models.ps1` 실행.
  - cloud schedule이 아닌 **로컬 작업**인 이유: Anthropic 클라우드 에이전트는 로컬 `E:\...\models.json`을 못 건드림. 갱신은 로컬에서만 가능.
- 동작: 웹 가능 헤드리스 AI(gemini→grok 폴백)로 제공사별 최신 최고모델·effort 재조사 → **`tools/models.json`을 자동 덮어쓰지 않고** `tools/models.proposed.json`에 제안 + `agents/claude/inbox`에 변동 노트 + `tools/models-refresh.log` 기록.
  - **게이트(중요)**: 환각/오타 모델 id가 데몬 spawn을 깨뜨릴 수 있어 **Claude(또는 Simon)가 제안을 검토 후 적용**(`models.json` 반영 + 이 표 last_checked 갱신 + `commit.ps1 -As claude`). hub-health의 `models.json best-model contract` 체크로 무결성 확인.
- 수동: `powershell -File tools/refresh-models.ps1` (즉시 제안) · 정밀 재조사는 hub-upgrade-research workflow 재실행.
- **불변 원칙**: 항상 *그 CLI에서 실제 호출 가능한* 최고 벤치마크 모델 + 최대 effort. 비용 게이트(§11-5)는 구독 CLI라 해당 없음(헤드리스 `claude -p`만 과금).

# BACKLOG.md — Cross-Domain Improvement Backlog

> Synthesized from a 4-domain adversarial audit (2nd-B fn/ux, hub, skills, stack) via Workflow `wnc60iphn` (11 agents). Only REAL/sharpened findings retained. Deduped, ranked by leverage. Within each tier, Claude-autonomous items lead. Claude's /loop chews this queue.
> Generated 2026-06-14. Owner: claude (merge gate).

## Status legend
`[ ]` todo · `[~]` in progress · `[x]` done · `[-]` dismissed (with reason)

---

## P0 — Correctness / Safety / Blocks-Autonomy

### Claude-autonomous (do in loop)
- `[x]` **commit.ps1 index.lock retry** — landed (concurrent-writer safety). + **mutex + `exit 1` on failure** (retry alone still races; failed commit must not look fresh). `tools/commit.ps1`
- `[x]` **No per-AI-invocation timeout** — LANDED 2026-06-14 (Start-Job+Wait-Job 1200s, see the pass below). — one hung CLI stalls the sequential daemon cycle forever. Wrap each CLI in `Start-Job`+`Wait-Job -Timeout`; on timeout kill + log TIMEOUT + continue. `tools/hub-daemon.ps1` Invoke-AI/loop. (S)
- `[x]` **Set-Heartbeat fakes freshness + violates single-writer + reverts paused** — LANDED 2026-06-14 (fake Set-Heartbeat removed; monitor uses live-log mtime + PID-gated green, see the pass below). — daemon writes other AIs' STATUS, forces `state: running`, masks a `paused` hub. Fix: stop writing STATUS; age daemon-AIs by `tools/live/<ai>.log` mtime in monitor.ps1; only when CONTROL.state==running. (S)
- `[ ]` **Crash-restart / liveness supervision** — monitor DAEMON-green is a stale-log illusion; verify a live PID + next-cycle-due, not just log mtime. (S–M)
- `[ ]` **Destructive-action PreToolUse hook + permissions.deny** under intentional `bypassPermissions` — hard-block `rm -rf`/`reset --hard`/`push -f`/`--no-verify`/`DROP TABLE` + writes to `.env*`/`credentials*`. Encodes §6/§11-5 in the harness. (S)

### Needs a runtime owner (Claude sets up)
- `[ ]` **Durable scheduler (SPOF)** — whole loop dies when the Claude session closes. `Register-ScheduledTask` (AtLogOn + restart), gated on CONTROL.state, PID lockfile keyed on AI-set so the 300s codex/grok + 1800s AG loops coexist but identical sets can't stack. (S)

---

## P1 — High-Leverage

### 2nd-B core product loop (Claude coding; coordinate with codex)
- `[ ]` **Stale core-loop screens after capture (no shared data/cache) — COUPLED with NavGraph rebuild.** Fixed order: (a) stabilize `dataNodes` ref (id-set/content hash); (b) `React.memo` NavGraph w/ node-id comparator; THEN (c) focus-refetch across index/records/core-brain/insights/trinity/record[id]. Don't ship (c) alone. `src/app/index.tsx`, `NavGraph.tsx`. (M)
- `[ ]` **NavGraph (2689 ln) rebuilds all animation loops on every data-identity change** — same fix as above (memo upstream array). `useNativeDriver:false` at NavGraph:950. (M)
- `[ ]` **Capture = 2 serial, un-abortable, double-billed LLM calls** — thread one AbortController keyed to focus/unmount; evaluate collapsing classify+ingest into one proxy round-trip. Preserve C3/C9 order. `capture.tsx:793-846`. (M)
- `[ ]` **~13 fire-and-forget audit/crisis writes → silent C3/C9 gaps on Supabase outage** — one `enqueueAuditWrite` (AsyncStorage outbox + flush-on-reconnect); tighten `isProxyCrisisRejection` so unreadable 422 isn't auto-crisis. `lib/llm/gemini.ts`. (S–M)
- `[ ]` **Disabled PremiumButton drops out of focus/press tree + sub-3:1 disabled contrast** — keep Pressable w/ `disabled`, raise BTN_DISABLED_FG ≥3:1, add accessibilityHint. `surfaces.tsx:163-165,258-271`. (S)
- `[ ]` **Home CTAs bypass design system (no press feedback, dup visuals)** — use PremiumButton/PremiumCTA; shared pressable w/ 80ms opacity-0.8 feedback. `index.tsx:522-675`. (M)

### Hub autonomy charter (Claude)
- `[ ]` **No merge-gate backpressure** — §12.2 "8 unmerged" is prose-only. Before discovery, count AI's open outbox items; if ≥8, skip discovery + dispatch throttle-redirect; cap worktrees/AI. `hub-daemon.ps1`. (M)
- `[x]` **AG lane headless** — RESOLVED: agy-pty ConPTY wrapper (2026-06-17) + `AGY_USE_CONPTY=0` winpty fix for console-less hosts (2026-07-03, PONG-verified under Start-Job). The 06-14 "agy -p non-functional" premise is obsolete.

### Skills/stack hygiene (Claude)
- `[ ]` **§21 routing misses dominant workflows + 3 configs out of sync** — add native-UI/store-submit/LLM-feature/deploy routing rows; re-sync CLAUDE/AGENTS/GEMINI verbatim (§18). (M)
- `[x]` **Config drift — AGENTS.md/GEMINI.md §18** — done (see line "3 root config §17/§18 정렬" below; both entries were the same work).
- `[ ]` **cp949 crash half-fixed** — set `PYTHONUTF8=1` at session start; patch doc one-liners to `encoding='utf-8'`. (S)
- `[~]` **Hub guardrails prose-only** — LANE GUARD (agents/<As>/ 밖 거부) + encoding/size guard + BRANCH GUARD(2026-07-03) landed in commit.ps1; remaining: staged secret-scan. (S)

---

## P2 — Nice-to-Have
- `[ ]` **Zero integration coverage on records↔sources data-shape contract** — one Supabase-mock round-trip test (createRecord/captureFromMarkdown → mergeEvidence → exportUserWiki field parity). Cheapest high-value win. (M, codex test-only)
- `[ ]` **Profile hub chips 14px caption-only, color-only signal** — add glyph + body(16px) label + muted hint line. `profile.tsx:177-196`. (M)
- `[ ]` **Tab active-state + secondary-button edge contrast unverified post-palette-pivot** — non-color active cue; bump labels; raise `gameboy.border` alpha; re-run contrast matrix. (S→M)
- `[ ]` **Asset version sprawl (~16MB dead weight)** — delete v45/v49 dirs + require maps + variant prop; resolve rhythm_core PLACEHOLDER. CLAUDE.md §20.4. (L)
- `[ ]` **INDEX.md stale vs 5-plugin source-of-truth** — regenerate from manifests + CI drift-guard; verify sibling-repo cutover install actually clones. (M)
- `[ ]` **Hardcoded skill counts contradict across 6 docs** — drop exact counts or CI-generate. (S)
- `[ ]` **Three skill trees diverged (13 orphans, triple-copy spec)** — pick canonical tree. **§35.1 ai-debate decision (source-of-truth = irreversible)** before mechanical migration. (L)

---

## Cross-cutting notes
1. **2nd-B P1 coupling:** stale-screens + NavGraph rebuild are ONE change in fixed order (stabilize array → memo → focus-refetch). Don't ship focus-refetch alone.
2. **Hub monitoring blind spot is systemic:** per-AI-timeout + Set-Heartbeat fake-freshness + stale-log green together let all monitor surfaces show "healthy" while the daemon is hung. Land the PID-liveness probe in the same pass as the heartbeat fix.
3. **Root cause (hub/stack P0s):** critical rules live in markdown prose while enforcement points (scheduled task, deny-list, commit hook) are empty — `design-first-gate.sh` proves the PreToolUse pattern works. Port the highest-risk prose rules into that hook/task layer.
4. **Do NOT re-do:** commit.ps1 retry (landed); the "§28.4 hang" claim (false — preconditions avoided); "bypassPermissions = banned" rhetoric (intentional §18 grant).

## Dismissed / unconfirmed (merge-gate verdicts)
- `[-]` **AG: Sign-in unauthenticated nav (Link) + deep link broken (P1/P2)** — DISMISSED as false positive (2026-06-14, Claude framework-aware). `_layout.tsx:249` renders the full Stack for `!userId` (unauth nav to /manual + /sign-up is allowed by design); Links use standard `Link asChild`+Pressable wiring. AG's headless-gemini emulator interaction is unreliable (tap-miss) and deep-links to genuinely auth-gated routes bouncing to /sign-in is the intended auth model, not a bug. Re-open only if a real interactive emulator session reproduces a dead /manual link.

---

## 2026-06-14 허브 개선 패스 (landed — Simon "허브 전부 개선·업데이트")
> 역할분석(wf w4gxhs3bw, 15갭) + 미성년 enablement(wf wvx2pd0f6) 산출을 **허브 거버넌스**에 반영. 2nd-B 제품코드는 별도 라이브-머지 사이클(범위 외).
- `[x]` **DECISIONS 원장 스튜어드(#14)** — frontmatter 06-06→06-14, Resolved 인덱스 신설, 만료투표 D-01/02/07 표기, D-18~20 enablement 안건 큐.
- `[x]` **release-gate.ps1(#3)** — author-독립 머지 GO/NO-GO + 롤백 SHA 기록(§8/§11.1). #222류 자기인증 머지사고 방지.
- `[x]` **RUNBOOK.md + INCIDENTS.md(#5)** — FAIL→복구 룩업표 + 인시던트 원장. monitor/hub-health의 신호에 'responder' 연결.
- `[x]` **PROTOCOL §35.6**(코어레인 독립반론, Claude 최종권 불변) · **§31.8**(좌석 용량게이트) · **§36**(미성년 ENABLEMENT 학습자 면허).
- `[x]` **ROUTING §1.5** 좌석 재정의 — Gemini 감사·심판 / Grok 와치독 / Codex 테스트저자·verify:safety / Claude 최소화(SPOF 회피).
- `[x]` **HUB-STARTUP.html** 모델·effort 정확화(fable-5 max 등) + 역할 갱신 + release-gate 도구 카드 + 신규자산 푸터.
- `[x]` **hub-daemon.ps1 P0 3종 landed**: per-AI 타임아웃(Start-Job+Wait-Job 1200s) · CONTROL.state 게이트(§13) · 가짜 Set-Heartbeat 제거(monitor가 실 live-log mtime + PID-gated green). 3 데몬 재기동 검증. 커밋됨. + HUB-STARTUP 경로-공백 launch 버그 수정.
- `[x]` **🔴 P1 (D-20 발견, 라이브-머지 사이클): 2nd-B `recommendations` 런타임 ungated** — SHIPPED 2026-06-14 (#369 미성년 게이트 배선, main 2dececf; DECISIONS RATIFY 참조). 미성년 누출은 더 이상 라이브 아님. — `ops.tsx:104-129 runRecommend`가 pref 미참조 → 미성년 포함 전원 실행, `0038` clamp는 읽는 게이트 없어 명목적. 픽스=runRecommend에 pref 게이트 배선(미성년 default OFF=clamp 값 사용)+미성년-lock 회귀테스트+승격은 ops_push promotable 패턴. 안전강화(더 보수적)지만 미성년 consent 경로 → **Claude 리뷰 게이트+live verify 경유**(자동 데몬 X). 법무 무관·즉시 가능.
- `[x]` **/goal 빌드루프 — 2nd-B 라이브 머지 3건**(verify green + CI green 후 머지): **#369** D-20 recommendations 미성년 게이트(ungated 누출 차단, main 2dececf) · **#370** D-19 anti-anthropomorphism CI 게이트(companion 카피 차단, locales 5135 클린, a47a6e8) · **#371** long_term_memory 동의 카피 de-companion(utility 프레이밍 + 회귀 가드, bd1e4d3).
- `[x]` **3 root config §17/§18 정렬**(AGENTS/GEMINI에 §17 외부자산 추가 + 동시작업 §17→§18, cross-file "§18" 포인터 복구).
- `[x]` **D-19 de-personification 감사 완료**(read-only): 주장=PARTIALLY-TRUE. 깨끗(스프라이트 얼굴無·persona=거울·crisis 인간핸드오프·streak 중립) / **실 COMPANION-RISK 2** = ①SceneHero 1인칭 순찰 speech(코드임베드라 게이트 미스) ②memory 동의 카피(→#371로 수정). 게이트는 locales만 스캔 = 코드 speech 커버 갭.
- `[ ]` **🟡 Simon 결정 필요(의인화 감사)**: ①**마스코트 1인칭 보이스**(SceneHero "I gathered the patterns…" `secondb.tsx:353`/`persona.tsx:216` + personas.ts "warm relationship guide") 유지 vs mirror-voice로 de-voice — named-mascot은 Simon 2026-05-31 지시라 자동변경 안 함, §35 ai-debate 후보 ②**anti-anthro 게이트를 코드(personas.ts·monologues.ts·SceneHero)까지 확장**(확장 시 기존 마스코트 speech가 게이트 fail → ①과 묶임) ③마스코트 "쉬고 있어요"/idle float·blink(KIDS-MODE 눈·표정 과잉금지 원칙을 14+에 적용할지).
- `[ ]` **후속(미착수·게이트)**: §36 enablement **빌드=Simon 법무** · **K12 아동 DPIA(초안 작성중 wf wkr380gtr)** · export 경로(GDPR Art.20) · Lane 7/8 egress audit · counsel 사인오프(Art.5·SB243·Std12·韓 §13).

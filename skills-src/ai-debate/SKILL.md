---
name: ai-debate
description: Use when a decision is important, contested, or irreversible and you want structured multi-AI debate instead of a solo call — triggers "토론 붙여", "다관점으로 결정", "이거 합의 보자", "찬반 검토", "AI들끼리 토론", "여러 의견 모아줘", "debate this", "get multiple positions", "structured decision", "consensus on", or /ai-debate. Also the MANDATORY mechanism for PROTOCOL §35.1 triggers (design/architecture/naming, conflicting findings, irreversible changes, low-confidence high-impact). Runs a multi-position panel → adversarial cross-examination → a SEPARATE judge (proposer is never judge) → consensus or Claude tiebreak, and records the verdict to the hub DECISIONS.md (D-code) with positions, rationale, and the preserved minority view. Produces a decision record, not just an opinion.
version: 0.1.0
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Agent
compatibility:
  - claude-code
---

# AI Debate — structured multi-perspective decision

Turn an important/contested/irreversible decision into a recorded debate instead of a solo guess. This is the runnable form of PROTOCOL **§35 (구조적 토론 게이트)** and unifies §14 (consensus), §19–23 (review), and §34.4 (separate-judge cross-review).

## When to use (and when it is MANDATORY)

Invoke proactively whenever a decision is worth more than one viewpoint. It is **required** (PROTOCOL §35.1) — do not proceed without a debate record — for:

| Trigger | Examples |
|---|---|
| ① 설계·아키텍처·네이밍 | UI 방향, 스택/DB 선택, 앱·기능·마스코트 명명, 정보위계 |
| ② AI·에이전트 충돌 | findings/verdict가 엇갈림, 공유-전제 위양성 의심 |
| ③ 중요·비가역 | main 머지, 스키마, 수익화/가격, 권한 모델, 대량 삭제, 라이브 배포 |
| ④ 저신뢰·고영향 | 불확실 + 영향 큼 (보안·법무·임상 표현 — 최종 게이트는 §11-5 Simon) |

Do **not** use for trivial, reversible, or single-obvious-answer work — that is solo or a plain `/review`.

## Workflow

1. **Frame** the decision as one sharp question + the options on the table + the decision criteria (what would make one option win). Pull any real evidence (read the relevant files/specs) so positions argue facts, not vibes.
2. **Panel (divergent positions).** Spawn N independent positions that each argue a *distinct* stance — not N copies. Two execution modes:
   - **Headless / solo session → Workflow panel** (default, immediate): one `agent()` per position, each told to make the strongest case for ITS stance and name the strongest objection to it.
   - **4-AI hub available → real AIs**: dispatch a `type: debate` request to codex/antigravity/grok outboxes (each argues from its lane: Codex=UI/UX, AG=native/perf, Grok=consumer/market), collect responses.
   - Lenses to assign (pick what fits): proponent, skeptic/refuter, the user's-interest, future-self/maintenance, cost/risk, and at least one "alternative nobody proposed".
3. **Adversarial cross-examination.** Each position must rebut the others' strongest point (§14: up to 5 rounds). Surface hidden shared assumptions (the framework-misunderstanding false-positive trap, [[tool_workflow_verify_shared_premise]]).
4. **Separate judge.** A judge agent that authored NONE of the positions scores them against the stated criteria (proposer ≠ judge, §34.4). It must pick or synthesize, and explicitly say why the losers lost.
5. **Resolve.** Consensus if it emerges; otherwise **Claude tiebreak** (§14) with written rationale. Safety-rail decisions (§11-5: destructive/cost/secrets/clinical/legal) still escalate to Simon — debate informs, Simon decides.
6. **Record** to the hub `DECISIONS.md` as one D-code entry (format below) and link it from whatever the decision gates (PR, spec, merge). The merge gate (§11.1) checks this record exists for §35.1 triggers.

## Panel skeleton (Workflow)

```js
// inside a Workflow script
const POSITIONS = [
  {k:'proponent', p:'Argue FOR option A. Strongest case + the one objection that could sink it.'},
  {k:'skeptic',   p:'Refute A; argue the status quo or B. Default to skepticism.'},
  {k:'alt',       p:'Propose an option neither side raised; argue it beats both.'},
  {k:'user',      p:'Argue purely from the end-user / Simon interest, ignore implementation ego.'},
]
const args = await parallel(POSITIONS.map(x => () =>
  agent(`Decision: ${QUESTION}\nCriteria: ${CRITERIA}\nEvidence: ${EVIDENCE}\n\n${x.p}`,
        {label:'debate:'+x.k, schema: POSITION_SCHEMA})))
const verdict = await agent(
  `You judged NONE of these. Score against criteria, pick or synthesize, say why losers lost:\n${JSON.stringify(args)}`,
  {label:'debate:judge', schema: VERDICT_SCHEMA})   // separate judge, no schema-less abstain trap
```

Keep the judge a *different* call than any position. Recover raw and synthesize yourself if a structured judge abstains ([[tool_workflow_structuredoutput_fail]]).

## DECISIONS.md entry format

```
### D-<n> — <decision title> (YYYY-MM-DD)
- 안건: <one-sentence question + options>
- 입장: A) <who/what/why> · B) <...> · alt) <...>
- 심판 근거: <criteria-based reasoning, why losers lost>
- 판정: <chosen/synthesized> (consensus | Claude tiebreak | →Simon §11-5)
- 소수의견: <preserved dissent — do not delete>
- 후속: <action / what this gates>
```

## Verification

- A debate is "done" only when DECISIONS.md has the D-code entry AND the judge ≠ any proposer AND the minority view is preserved.
- For §35.1 triggers, the thing being decided (PR/merge/spec) must link the D-code; the merge gate (§11.1) rejects trigger-changes without it.

## Anti-patterns

- N identical positions (no real divergence) — assign distinct stances/lenses.
- Proposer self-judging — always a separate judge.
- Debating trivial/reversible calls — wastes cycles; reserve for §35.1 + genuinely contested.
- Treating "0 objections" from a structured-output failure as agreement — verify the judge actually ran.

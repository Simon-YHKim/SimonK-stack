# SimonK-Stack

> A skill library that makes Claude Code **follow the right procedure automatically** — from product planning to development, monetization, growth, and exit. Plus **simonK unified autonomous harness**.

**[simonk-stack.pages.dev](https://simonk-stack.pages.dev)** · [![validator](https://img.shields.io/badge/skill--validator-98%20skills-brightgreen)]() [![harness](https://img.shields.io/badge/simonK-autonomous-blueviolet)]() [![license](https://img.shields.io/badge/license-MIT-blue)]()

🇰🇷 **한국어 README**: [README.md](README.md) (full version)

---

## What is this?

**Problem**: AI coding assistants work in a different order every time you give them a large task, and they repeat the same mistakes.

**Solution**: 98 skills (work manuals) + **simonK unified autonomous harness** (single entry point → 6-phase autonomous execution). Combined with [SimonKWiki](https://github.com/Simon-YHKim/SimonKWiki) (private) for cross-session learning accumulation — no more re-reasoning from scratch every session.

```
"build a new app"      → app-dev-orchestrator    → 21-stage pipeline
"analyze PMF"          → pmf-analyzer            → 3-case scenario prediction
"add payment"          → payment-integrator      → Stripe/PortOne + webhook + tests
"test monetization"    → revenue-scenario-tester → 7 specialized agents, 80+ scenarios
"release notes"        → release-notes           → separate dev (README) and user (store) outputs
"go viral"             → viral-launch            → 4-channel playbook
"remove AI tone"       → human-voice-guard       → LLM-tell detection + human-tone rewriting
"pick a stack"         → tech-preference-tracker → consistency advice based on accumulated preferences
"exit strategy"        → exit-strategy-planner   → IPO/M&A roadmap

simonK <goal>          → unified autonomous harness → Ambiguity check → Sprint plan
                                                    → parallel Task agents → Verify → Full Auto push
```

---

## 🤖 simonK Unified Autonomous Harness (★ v2 core)

**Single entry point — invokable from anywhere:**

```powershell
# PowerShell — profile persisted (works in any folder)
simonK <task>

# Inside Claude Code interactive session — slash
/simonK <task>
```

Both execute the same `skills-src/simonk/SKILL.md`. **Case-insensitive** (`simonk`, `SIMONK`, `SimonK` all equivalent).

### 6-Phase autonomous flow

| Phase | Action | User input? |
|---|---|---|
| **1** Ambiguity Score | Evaluate 4 dimensions (Goal/Scope/Success/Risk) 0-10 | If score<6 → Socratic 3-5 Q&A once |
| **2** Sprint Plan | Break into `≤5` sub-tasks + dependency graph → `.simonk/plan.md` | default proceed |
| **3** Parallel Execution | Independent sub-tasks → Task tool parallel calls (general-purpose / Explore / Plan agents) | none |
| **4** Verification | Task-specific (`validate_skill.py` / `wiki-lint` / `bash -n` / test) | none (report on 2nd failure) |
| **5** Persistence | `git add -A && commit && push` both repos (Full Auto) | none |
| **6** Final Report | Structured summary of work · verification · git status · next steps | none |

### Auto-push policy (Full Auto, user-agreed)

- ✅ All repos (private + public) auto commit + push
- ❌ **PR creation/merge** — NEVER automated (global CLAUDE.md policy)
- ❌ **Destructive ops** (`rm -rf`, `git reset --hard`, force push to main of multi-collab, DB drop) STOP
- ❌ **.env / credentials** exposure/modification immediate STOP

---

## 🔁 Auto-update — which sources stay current?

`session-start.sh` hook applies per-source policy on every session start:

| Source | Mechanism | Auto? |
|---|---|---|
| **SimonK-stack itself** | session-start hook `git fetch + pull --ff-only` (clean+main only) | ✅ Auto |
| **SimonKWiki** (PRIVATE) | Same mechanism | ✅ Auto |
| **Gstack upstream** (`garrytan/gstack`) | Hook detects ahead-count → LLM advised to `/gstack-upgrade` | 🟡 Semi-auto |
| **kepano/obsidian-skills** (5 vendored) | Vendored snapshot — manual update needed | ❌ Manual |
| **external/** (OMC · OMO · OpenHarness · TradingAgents · anthropics-skills) | Shallow clone, reference only | ❌ Manual |
| **Graphify** | `uv tool upgrade graphifyy` manual | ❌ Manual |

---

## Install

### Claude Code Web (easiest)
1. Go to https://claude.ai/code → Open `Simon-YHKim/SimonK-stack` → Done

### Local CLI
```bash
git clone https://github.com/Simon-YHKim/SimonK-stack.git
cd SimonK-stack && ./scripts/install.sh
```

### Vendoring into other projects
```bash
/path/to/SimonK-stack/scripts/setup-repo.sh /path/to/your-project
```

Details: [docs/USING-IN-OTHER-REPOS.md](docs/USING-IN-OTHER-REPOS.md)

---

## 🎯 Quick Start — 18 Curated Skills

For first-time users, **`simonK <goal>` is the single entry point**. The rest of the curated 18 main skills:

| Priority | Skills |
|---|---|
| ★ Entry | `simonK <task>` |
| ★ Pipelines | `app-dev-orchestrator` · `dev-orchestrator` · `security-orchestrator` |
| ★ Methodology base | `karpathy-guidelines` · `simon-tdd` · `simon-worktree` · `simon-instincts` |
| ★ Pre-launch | `payment-integrator` · `human-voice-guard` · `release-notes` · `viral-launch` |
| ★ Research/Design | `simon-research` · `simon-design-first` |
| ★ Wiki ops | `wiki-ingest` · `wiki-query` · `wiki-lint` |
| ★ Daily | `commit` |

The remaining 83 (domain-specific + 36 Gstack vendored + 5 kepano vendored) → see [docs/CURATED-SKILLS.md](docs/CURATED-SKILLS.md) or [full catalog](README.md#skill-카탈로그--98개) (Korean).

---

## 📊 Phase 3 pre-entry (planned 6/15~6/30 → actual 5/23~24)

Three Phase 3 core tools entered *3 weeks early*:

| # | Tool | Install | Result |
|---|---|---|---|
| **A13** | [Graphify](https://graphify.net) v0.8.16 (Safi Shamsi · YC S26) | `uv tool install graphifyy` | SimonKWiki **894 nodes** · SimonK-stack **4645 nodes** · Claude Code PreToolUse hook |
| **C02** | [OpenHarness](https://github.com/HKUDS/OpenHarness) v0.1.9 (HKUDS) | `uv tool install openharness-ai` | 4 CLIs (`oh`/`ohmo`/`openh`/`openharness`) · Phase 6 ohmo signature reference |
| **VS Code** | extensions + settings | `code --install-extension ...` | 5 ext (claude-code · Korean lang pack · python+pylance+debugpy · markdown-all-in-one · yaml) |

### MCP integrations (active 2026-05-25)

- **A11 Zotero MCP** ✓ Connected (`zotero-mcp --transport stdio`)
- **A12 NotebookLM** ✓ login (`/notebooklm` slash + CLI)
- **A14 MCP integration bundle** — A11+A12+A13+C02 working together at Phase 3 full entry

---

## Test results

| Test | Result |
|---|---|
| Native skills (SimonK) | **62/62 PASS** (validator 0 errors / 0 warnings) |
| Vendored skills (Gstack + kepano) | **36 + 5 vendored** (original format preserved) |
| Full validator (lenient + **strict YAML E013**) | **98/98 PASS** |
| simonk autonomous harness | **0 errors / 0 warnings · score 0.80** |
| simon-design-first (W013 fix) | **0 errors / 0 warnings** |
| Bash syntax (hooks + scripts) | **all PASS** |
| PowerShell scripts | **all PASS** |
| Graphify graph (SimonKWiki) | **894 nodes · 813 edges · 86 communities** |
| Graphify graph (SimonK-stack) | **4645 nodes · 4538 edges · 404 communities** |

---

## Credits

| Source | Contribution |
|---|---|
| [Gstack](https://github.com/garrytan/gstack) — garrytan | 36 execution-pipeline skills |
| [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) | 5 Obsidian ops skills (defuddle / json-canvas / obsidian-bases / obsidian-cli / obsidian-markdown) |
| [Karpathy](https://x.com/karpathy) | 4 principles + llm-wiki pattern |
| [Superpowers](https://github.com/obra/superpowers) — obra | TDD, worktree, verification loop |
| [everything-claude-code](https://github.com/affaan-m/everything-claude-code) | Instincts learning, research-first |
| [Skill-Agent](https://github.com/Simon-YHKim/Skill-Gen-Agent) | validate_skill.py |
| [Impeccable](https://github.com/pbakaus/impeccable) | AI Slop prevention design principles |
| [Graphify](https://graphify.net) — Safi Shamsi (YC S26) | Knowledge graph extraction/visualization (Phase 3 integration) |
| [TradingAgents](https://github.com/TauricResearch/TradingAgents) — UCLA TauricResearch | Multi-agent reference for Phase 4-6 closed-network signature agent |

## Show HN draft (Stage 3 사전, 11월~)

> **2026 Stage 3 글로벌 노출 사전 draft** — 사용자 본인이 *11월 6개월 ROI 회고 후* 실제 post 결정.

### Title candidates

1. *"SimonK-stack: 6-month case study of a single Korean engineer running 100 Claude Code skills + autonomous harness"*
2. *"Show HN: I built a personal AI OS with 100 skills, MCP integration, and a closed-network signature agent roadmap"*
3. *"Show HN: simonK — autonomous 6-phase harness for Claude Code (one-command → Plan + parallel Task agents + auto-push)"*

### Pitch (140 chars)

> Korean dev's 6-month single-user case study: 100 curated Claude Code skills + simonK autonomous harness + MCP integration (Zotero/NotebookLM/Graphify/OpenHarness) + closed-network signature agent roadmap (27Y Q1+).

### Core proof points

- **Real production use** — not a demo. Used daily for Android app launch (5/30), AI career pivot, Korean wiki accumulation.
- **Open source MIT** — fork friendly, vendoring documented.
- **Sister repo SimonKWiki** (private) — 6 months Karpathy-model wiki + 17 NotebookLM workspaces + 926-article external blog mirror = real knowledge base, not a toy.
- **Autonomous harness** — 6-phase (Ambiguity → Plan → parallel Task → Verify → Push → Report) with Boundary Check (security audit auto-detection).
- **3-layer auto-update** — SessionStart hook + Wiki-Lint cron + Graphify PreToolUse — system gets *better while you're not looking*.

### Anti-pitch (Korean wisdom)

> "이건 *내 운영체제*다. 누가 써도 자유. 본인 워크플로우 맞게 fork → 큐레이션 권장."

= *not a product, a personal OS share*. Authentic > polished.

### Posting checklist (Stage 3)

- [ ] Stage 2 (6/15~6/30) 메인 18 큐레이션 6개월 실사용 데이터 누적 완료
- [ ] 본인 Android app 5/30 출시 + 6개월 metric (downloads · revenue · churn)
- [ ] CSO audit 완료 (PII + 사내 식별 reference 완전 마스킹 확인)
- [ ] Korean → English 핵심 docs 번역
- [ ] r/ClaudeAI · HN Show HN · GeekNews 동시 post

## License

[MIT](LICENSE). Commercial use, modification, distribution free.

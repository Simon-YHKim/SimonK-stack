# SimonK-Stack

> A toolbox of 182 Claude Code skills in five plugins. It covers idea validation, planning, building, testing, security, shipping, design, AI features and marketing. Describe what you want done, and it hands the work to the right skill and model.

![license](https://img.shields.io/badge/license-MIT-green) [![validate](https://github.com/Simon-YHKim/SimonK-stack/actions/workflows/validate-plugin.yml/badge.svg)](https://github.com/Simon-YHKim/SimonK-stack/actions/workflows/validate-plugin.yml) ![plugins](https://img.shields.io/badge/plugins-5-5b8cff) ![skills](https://img.shields.io/badge/skills-182-brightgreen)

**Site**: [simonk-stack.pages.dev](https://simonk-stack.pages.dev) · **한국어**: [README.md](README.md) · **Changes**: [CHANGELOG.md](CHANGELOG.md)

## Contents

1. [What SimonK-Stack is](#1-what-simonk-stack-is)
2. [The five plugins](#2-the-five-plugins)
3. [Install](#3-install)
4. [First steps](#4-first-steps)
5. [Find a skill by task](#5-find-a-skill-by-task)
6. [Safety mode: careful, freeze, guard, unfreeze](#6-safety-mode-careful-freeze-guard-unfreeze)
7. [Update, roll back, remove](#7-update-roll-back-remove)
8. [Moving from the old `simonk-stack` 0.1.0](#8-moving-from-the-old-simonk-stack-010)
9. [Troubleshooting](#9-troubleshooting)
10. [Bundled app: AI Usage Widget](#10-bundled-app-ai-usage-widget)
11. [For developers](#11-for-developers)
12. [License](#12-license)

---

## 1. What SimonK-Stack is

A skill is a packaged procedure that tells Claude how to do a kind of work, along with any tools it needs. SimonK-Stack collects the working methods a solo product builder uses most, so you don't have to repeat the same instructions every session.

How it works:

1. Say what you want. For example: "Check whether this idea has a market" or "Build a login feature and take it to deployment."
2. Each plugin's entry skill (`vibe`, `skstack`, `skdesign`, `skaihub`, `skmarket`) works out the intent and hands off to the right sub-skills. A plain-language request also works: Claude reads the skill descriptions and picks one.
3. Results are verified before they are reported. Without test or measurement evidence, nothing is called "done".

Principles:

- **You set the goal and the authority.** Merges, deployments, deletions, payments and anything else that is hard to undo or costs money run only within the authority you gave.
- **No extra billing by default.** `/vibe` uses models only within your subscription's included usage. If billing or usage can't be confirmed, it doesn't run.
- **Only verified claims.** Anything not measured is reported as "unverified".

## 2. The five plugins

| Plugin | What it does | Skills | Entry point |
| --- | --- | ---: | --- |
| `simonk-core` | Shared base: work coordination (`vibe`), sprints (`simonk`), model assignment, AI debate, memory and wiki, reports, session handoff, safety (`careful`, `unfreeze`) | 61 | `/simonk-core:vibe` |
| `simonk-stack` | Building the product: planning and specs, development and refactoring, debugging, QA, security, deployment and release, safety (`freeze`, `guard`) | 60 | `/simonk-stack:skstack` |
| `simonk-aihub` | Building AI features: model choice, prompts, agents, RAG, LLM and safety evaluation | 7 | `/simonk-aihub:skaihub` |
| `simonk-design` | Design: UI direction, design systems, logos and social graphics, slides, accessibility checks | 22 | `/simonk-design:skdesign` |
| `simonk-market` | Market and revenue: idea validation, PMF, growth and retention, ads, payments and subscriptions, launch | 32 | `/simonk-market:skmarket` |

To call a plugin skill by slash command, the `/<plugin>:<skill>` form always works (for example `/simonk-core:careful`). The full skill list per plugin is at the [end of section 5](#full-skill-list).

## 3. Install

### Requirements

- Claude Code with plugin support. Install, update and rollback were measured on 2.1.289.
- Git.
- For safety mode (section 6): Windows, Git for Windows (Git Bash), and Python 3.7 or later on PATH.

### Install commands

Inside a Claude Code session:

```
/plugin marketplace add Simon-YHKim/SimonK-stack
/plugin install simonk-core@simonk-stack
/plugin install simonk-stack@simonk-stack
/plugin install simonk-aihub@simonk-stack
/plugin install simonk-design@simonk-stack
/plugin install simonk-market@simonk-stack
```

From a terminal, use `claude plugin marketplace add Simon-YHKim/SimonK-stack` and `claude plugin install <id>@simonk-stack`. If you installed inside a session, run `/reload-plugins` to apply it now, or open a new session.

You can install only some plugins, but entry skills often hand work to skills in other plugins, so installing all five is recommended.

### Check the install

Five lines means it worked.

```powershell
(claude plugin list --json | Out-String | ConvertFrom-Json) | Where-Object id -like 'simonk-*@simonk-stack' | Select-Object id, version, enabled
```

In a POSIX shell: `claude plugin list --json | grep -o 'simonk-[a-z]*@simonk-stack'`.

> **Don't combine with a flat install.** If you already copied the same skills into `~/.claude/skills`, enabling the plugins shows every skill twice. A 2026-10-05 measurement saw 563 skills and over 30,000 characters of descriptions, so the list was truncated, which lowers the accuracy of automatic skill selection. Use either the plugins or the flat install, not both.

> **Codex CLI is not supported yet.** Running `codex plugin marketplace add Simon-YHKim/SimonK-stack` in Codex finds no plugins to install (hub D-88). A Codex build (177 skills, without the safety skills) will be published after its own verification. If you installed through Codex before 2026-10-05, check with `codex plugin list` and remove each one, for example `codex plugin remove simonk-core@simonk-stack`. That build carries Claude Code-only safety skills, so their protection is not guaranteed in Codex.

## 4. First steps

Ask in plain words. The skill in parentheses is the one usually picked.

```
Would people pay for this idea? How do I validate it before launch?   (idea-validation)
Let's build an MVP of a to-do app                                     (app-dev-orchestrator, skstack)
Login returns a 500 error. Find the cause and fix it                  (investigate)
Run QA on this page                                                   (qa)
Set the design direction for a landing page first                     (simon-design-first)
I want a RAG chatbot that answers customer questions                  (skaihub, rag-builder)
Add payments and design subscription plans                            (skmarket, paywall-designer)
```

To hand over several steps at once, call the coordinator:

```
/simonk-core:vibe Build a web app with sign-up through payment and verify it right up to deployment
```

`vibe` puts the needed skills, models, usage and verification steps into one plan and runs it within the approved scope. `/simonk-core:simonk` runs a six-phase sprint under the same coordinator: clarify → plan → execute → verify and recover → scoped Git persistence → report.

Not sure a skill exists? Search with `/simonk-core:find-skill receipt OCR`.

## 5. Find a skill by task

| Task | Skills | Plugin |
| --- | --- | --- |
| Validate an idea, test demand | `idea-validation`, `pmf-analyzer` | market |
| Write requirements and specs | `spec`, `office-hours` | stack, core |
| Start a new app from scratch | `app-dev-orchestrator`, `skstack` | stack |
| Choose a tech stack or database | `stack-architect`, `db-selector`, `app-platform-selector` | stack |
| Test-driven development | `simon-tdd`, `test-gen` | stack |
| Find a bug's root cause | `investigate`, `debug` | stack |
| Web QA and fixes | `qa`, `qa-only` | stack |
| Security review | `cso`, `security-checklist`, `security-orchestrator` | stack |
| PRs, deployment, release | `ship`, `land-and-deploy`, `release-notes` | stack |
| Design direction and systems | `simon-design-first`, `design-consultation`, `design-system-keeper` | design |
| Slides, logos, social images | `slides`, `logo-generator`, `social-graphic` | design |
| Accessibility checks | `accessibility-audit`, `inclusive-ux` | design |
| AI models, prompts, agents | `ai-model-selector`, `prompt-engineering`, `agent-builder` | aihub |
| RAG, LLM evaluation | `rag-builder`, `llm-eval`, `ai-safety-eval` | aihub |
| Growth and retention | `growth-engine`, `aarrr-growth-planner`, `cohort-retention-analyzer` | market |
| Monetization, payments, subscriptions | `monetization-planner`, `payment-integrator`, `paywall-designer` | market |
| Debate a major decision across AIs | `ai-debate` | core |
| Pick the right model for a task | `model-router` | core |
| Session handoff | `simon-handoff` | core |
| HTML result report | `completion-report` | core |
| Work that truly needs a GUI | `vibe-bot` | core |

### Full skill list

<details>
<summary><code>simonk-core</code>: 61</summary>

agent-delegate, ai-debate, ai-usage-widget-install, careful, caveman, checkpoint, completion-report, defuddle, designmd-upgrade, domain-glossary, find-skill, founder-context, gcloud-helper, grill-me, gstack-upgrade, html-default-output, human-voice-guard, json-canvas, keepass-helper, learn, llm-wiki-builder, model-router, multi-terminal-dispatcher, notebooklm-import, obsidian-bases, obsidian-cli, obsidian-markdown, office-docs, office-hours, omc-upgrade, omo-upgrade, open-gstack-browser, opencowork-upgrade, openharness-upgrade, pair-agent, persona-validate, perspectives, plan-ceo-review, project-context-md, semantic-recall, session-context-export, session-context-tracker, session-start-hook, setup-browser-cookies, simon-handoff, simon-instincts, simon-ohmo, simon-research, simon-worktree, simonk, simonk-report, sprint-optimizer, stack-update, tech-preference-tracker, unfreeze, vibe, vibe-bot, web-publisher, wiki-ingest, wiki-lint, wiki-query
</details>

<details>
<summary><code>simonk-stack</code>: 60</summary>

analytics-ad-wiring, app-dev-orchestrator, app-platform-selector, auth-builder, authz-designer, autoplan, benchmark, browse, building-native-ui, canary, code-health-guard, codex, consent-manager, cso, data-flow-mapper, data-retention-planner, db-selector, debug, deeplink-integrator, deploy-configurator, dev-orchestrator, devex-review, document-release, explain, freeze, guard, health, i18n-localizer, iap-product-configurator, incident-runbook, investigate, karpathy-guidelines, land-and-deploy, minor-consent-compliance, nextjs-optimizer, offline-first, paid-api-guard, phase4-game-orchestrator, plan-devex-review, plan-eng-review, qa, qa-only, refactor, release-health-guard, release-notes, retro, security-checklist, security-orchestrator, setup-deploy, ship, simon-tdd, simple-static-site, skstack, spec, stack-architect, store-privacy-disclosure, test-gen, vercel-react, vue-best-practices, zoom-out
</details>

<details>
<summary><code>simonk-aihub</code>: 7</summary>

agent-builder, ai-model-selector, ai-safety-eval, llm-eval, prompt-engineering, rag-builder, skaihub
</details>

<details>
<summary><code>simonk-design</code>: 22</summary>

accessibility-audit, coloring-art, consistency-guard, dashboard-review, design-consultation, design-html, design-review, design-shotgun, design-system-keeper, design-system-page, inclusive-ux, logo-generator, persona-simulation, photo-album, plan-design-review, remotion-best-practices, scientific-paper, simon-design-first, skdesign, slides, social-graphic, stitch-design-flow
</details>

<details>
<summary><code>simonk-market</code>: 32</summary>

aarrr-growth-planner, ad-monetization, aha-moment-optimizer, analytics-integrator, churn-recovery-planner, cohort-retention-analyzer, community-marketing, exit-strategy-planner, experiment-analyzer, export-channel, feedback-and-review-collector, global-payment-planner, growth-engine, idea-validation, lifecycle-campaign-designer, mobile-attribution-integrator, monetization-planner, nocode-monetization, onboarding-flow-builder, paid-ads-campaign, payment-integrator, paywall-designer, pink-tax-advisor, pmf-analyzer, referral-program-builder, revenue-scenario-tester, skmarket, store-launcher, subscription-manager-selector, tag-manager-integrator, unit-economics-modeler, viral-launch
</details>

## 6. Safety mode: careful, freeze, guard, unfreeze

These guard against mistakes on a production server or a shared machine. Once turned on, Claude checks every command or file edit for the rest of that session before it runs.

| Skill | What it does |
| --- | --- |
| `careful` (core) | Checks risky commands. HIGH commands such as a recursive delete of a root, drive root or home, or a force push to the default branch, are blocked (deny). MEDIUM Bash commands such as `rm -r`, `git reset --hard` or `DROP` ask first (ask). PowerShell commands are only blocked when the shape is dangerous; they never ask. If the check itself fails, the command is blocked. |
| `freeze` (stack) | Limits edits to one folder. Edits outside it, or to paths it can't resolve, are blocked. |
| `guard` (stack) | Turns on `careful` and `freeze` together. |
| `unfreeze` (core) | Removes the `freeze` or `guard` edit boundary. Success prints a `FREEZE_CLEARED` line. |

> **The safety hooks are Windows-only.** The hooks of `careful`, `freeze`, `guard` and `investigate` only judge commands on Windows. On other systems, from the moment the skill is turned on, they **deliberately block all** matching commands or edits (fail-closed). The same happens when Python is missing. To get out, start a new session without the skill, or run `/plugin disable simonk-core@simonk-stack` (careful) or `/plugin disable simonk-stack@simonk-stack` (freeze, guard, investigate) and open a new session. On non-Windows systems `/unfreeze` does not release it. Rationale and measurements: [INSTALL.md, non-Windows safety hooks](docs/INSTALL.md#비windows-안전-훅--인터프리터-가드-d-76-4단계) (Korean).

## 7. Update, roll back, remove

### Update

Auto-update is off by default for third-party marketplaces. Get a new version like this:

```
claude plugin marketplace update simonk-stack
claude plugin update simonk-core@simonk-stack
claude plugin update simonk-stack@simonk-stack
claude plugin update simonk-aihub@simonk-stack
claude plugin update simonk-design@simonk-stack
claude plugin update simonk-market@simonk-stack
```

Versions look like `1.<number>.0`, and the number grows with each release. After updating, open a new session or run `/reload-plugins`.

### When a bad release is rolled back

Nothing extra on your side. A bad release is rolled back by shipping the previous content again under a **higher version**. Just run the update commands above again (measured 2026-10-05: 1.766.0 → 1.767.0 restored the previous content).

### Remove

```
claude plugin uninstall simonk-core@simonk-stack
```

The other plugins work the same way. To switch one off for a while, use `claude plugin disable <id>@simonk-stack`, and `enable` to turn it back on. To remove the marketplace too, run `claude plugin marketplace remove simonk-stack`.

## 8. Moving from the old `simonk-stack` 0.1.0

This applies if you used this marketplace before 2026-10-05, when it had a single plugin, `simonk-stack` 0.1.0. Running `/plugin update` (or `claude plugin update simonk-stack@simonk-stack`) now swaps that ID for the new `simonk-stack`, but **the other four are not installed automatically.** Ten of the old skills then disappear: nine moved to `simonk-market` and `consistency-guard` moved to `simonk-design`. After the update, run these four lines:

```
claude plugin install simonk-core@simonk-stack
claude plugin install simonk-market@simonk-stack
claude plugin install simonk-design@simonk-stack
claude plugin install simonk-aihub@simonk-stack
```

Then use the [install check in section 3](#check-the-install) to confirm all five are present. The `dependencies` field in plugin.json is only followed on a fresh install, not on an update. Measurements: [INSTALL.md, legacy migration](docs/INSTALL.md#레거시-simonk-stack-010-사용자-이전-d-76-4단계) (Korean).

## 9. Troubleshooting

| Symptom | What to check |
| --- | --- |
| Installed, but the skills don't show | Run `/reload-plugins` or open a new session. Check that `enabled` is true in `claude plugin list`. |
| A new version doesn't arrive | Auto-update is off. Run `marketplace update` and then `plugin update`, as in section 7. |
| Skills appear twice and the list is cut off | A flat install (`~/.claude/skills`) and the plugins are both on. Use only one. |
| Every command is blocked on macOS or Linux | `careful`, `freeze` or `guard` is on. The safety hooks are Windows-only. Follow the way out in section 6. |
| On Windows, the safety hooks block every command | Check that Git for Windows and Python 3.7+ are on PATH. If the checker can't run, it blocks on purpose. |
| `/vibe` says "blocked" instead of running | Included subscription usage couldn't be confirmed, or is near its limit. This prevents extra billing; the report says what blocked it. |
| Old skills disappeared | Run the four lines in section 8. |
| Codex says "No marketplace plugins found" | Expected. The Codex build is not published yet (see the Codex note in section 3). |

## 10. Bundled app: AI Usage Widget

`apps/ai-usage-widget/` is an Electron app that shows subscription usage for Claude, Codex, Grok and Antigravity next to the Windows taskbar: 5-hour and weekly limits, and the time left until reset.

- It uses only each provider's official CLI path. If a lookup fails, it shows "unverified" and the last measured time instead of a made-up number.
- When a limit's usage climbs faster than usual, it highlights that account and briefly shows a speech bubble.
- When a new model release is confirmed in official documentation, it shows a badge.

In Claude Code, run `/simonk-core:ai-usage-widget-install` or say "install the AI usage widget". It builds from source, verifies, then installs (needs node, pnpm and git). You sign in yourself, in the widget window. Design details are in the [app design document](apps/ai-usage-widget/docs/DESIGN.md); rights to third-party logos follow [NOTICE](NOTICE).

## 11. For developers

### Repository layout

```
skills-src/        137 shipped skill sources (SKILL.md, evals/, scripts/, references/)
.claude/skills/    4 development skills used in this repo
scripts/           build and verification tools (skill_release, plugin_bundle, codex_overlay, codex_safe_subset, dist_release)
scripts/windows/   Windows user-home installer (update-local.ps1)
distribution/      release inputs and gates (plugin-inputs, dist-publish.allow, hold files)
apps/              AI Usage Widget
docs/              install records (INSTALL.md), handoff (HANDOFF.md) and more
```

The five plugins are built by combining `skills-src/` with each plugin's source repository, pinned by commit in `distribution/plugin-inputs.v1.json`.

### Adding or changing a skill

1. Create new skills with `skill-gen-agent`, which checks description format, naming and length.
2. Validate after every change. Errors and warnings must both be 0.

   ```bash
   python3 .claude/skills/skill-gen-agent/scripts/validate_skill.py skills-src/<name>
   python3 .github/skill-ci/run_ci.py
   ```

3. Keep at least two test cases in `evals/cases.json`.
4. Bump the skill version (`SKILL.md`, `evals/cases.json`, and any test that pins the version) and add a line to the CHANGELOG.
5. Use Conventional Commits (`feat(skills):`, `fix(...)`, `docs:` …).

Common tests:

```bash
python3 -B -m unittest discover -s scripts/tests -p 'test_*.py'
(cd skills-src/vibe/scripts && python3 -B -m unittest discover -s . -p 'test_*.py' -q)
```

### How a release reaches users

1. On every push to main, `five-plugin-dist.yml` rebuilds the five plugins on a Windows runner from public inputs only. The path audit and the safety runtime tests run against the built tree; the bundle, Codex and safety hook unit tests run in a separate job.
2. The publish job adds a new commit to the `dist` branch only when both of these exist: the repository variable `SIMONK_DIST_PUBLISH`, and a committed `distribution/dist-publish.allow` (decision code, source commit, content digest). Identical content is skipped, a version not newer than what is already published is refused, and nothing is force-pushed.
3. The marketplace catalog (`.claude-plugin/marketplace.json`) points to the five folders on the `dist` branch.

To ship new content, merge the feature, then merge a PR that sets the approval file's digest to that build's value. To roll back, revert the offending commit on main; the previous content then ships again under a higher version. **Never revert the catalog commit.** Users who already installed would get "not found" for their plugins. Full procedure and evidence: [docs/INSTALL.md](docs/INSTALL.md) (Korean).

### Managing a flat install on Windows

This is the maintainer path that installs straight into `~/.claude/skills` instead of using the plugins.

```powershell
pwsh -NoProfile -NonInteractive -File scripts/windows/update-local.ps1            # preview
pwsh -NoProfile -NonInteractive -File scripts/windows/update-local.ps1 -Apply -Selftest
```

It builds a candidate, swaps the links, replaces only the changed skills, then verifies itself, and rolls everything back if verification fails. Don't enable the plugins on a machine that uses this (see section 3). The older git-clone install scripts (`scripts/install.sh`, `scripts/setup-repo.sh`) are no longer recommended.

### More

| Document | Contents |
| --- | --- |
| [docs/INSTALL.md](docs/INSTALL.md) | Install and release procedure with verification records (Korean) |
| [docs/HANDOFF.md](docs/HANDOFF.md) | Latest work status and next steps (Korean) |
| [CLAUDE.md](CLAUDE.md) | Rules and verification commands for working in this repo |
| [.claude/skills/INDEX.md](.claude/skills/INDEX.md) | Map of source and development skills |
| [skills-src/vibe/references/orchestration.md](skills-src/vibe/references/orchestration.md) | The `vibe` execution contract (plan, budget, gates) |
| [docs/skill-selection-validation.md](docs/skill-selection-validation.md) | How automatic skill selection accuracy is validated |

## 12. License

MIT. Details and upstream credits (gstack by garrytan, mattpocock skills and others) are in [LICENSE](LICENSE) and [NOTICE](NOTICE).

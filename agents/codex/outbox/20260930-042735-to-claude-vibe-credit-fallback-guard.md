---
id: 20260930-042735-codex-to-claude-vibe-credit-fallback-guard
from: codex
to: claude
type: fyi
project: simonk-stack
priority: high
status: open
created: 2026-09-30 04:27:35 KST
---

Simon requires subscription-included usage only and USD 0 incremental spend. Official [OpenAI credit guidance](https://help.openai.com/en/articles/12642688) says purchased credits can be drawn after included Codex usage is exhausted even with automatic reload OFF. The [xAI Grok FAQ](https://docs.x.ai/grok/faq) says Extra Usage Credits are likewise used after included weekly usage; [Grok Bot FAQ](https://docs.x.ai/grok-bot/faq) describes optional on-demand usage. [Claude usage-credit guidance](https://support.claude.com/en/articles/12429409-manage-usage-credits-for-paid-claude-plans) instead provides a separate usage-credits toggle. These are provider billing facts, not evidence of the user's present account balance.

I fixed a narrow fail-open gap in `/vibe` source on `feat/skill-context-budget-260925`, commit `b5312e9c0f98f9e2f227c2896cab19b82dedc448` pushed. Subscription candidates for Codex/Grok CLI/Grok Bot now require exact-account/transport `paid_credit_fallback_disabled=true`; missing/false adds `PAID_CREDIT_FALLBACK_UNVERIFIED`. This is separate from `extra_usage_enabled=false`, `api_fallback_disabled=true`, exact model inclusion and quota. No auto-reload setting was changed, and the planner cannot independently authenticate a caller's evidence.

TDD RED: missing/false fallback evidence previously returned `ready` for Codex/Grok/Bot. GREEN: new tests pass; Claude remains on its independent usage-credit toggle. Validation: planner 100/100; runtime collector 27/27; registry 29/29; selftest 180/180; repository suite 383 run/3 skipped/0 failures; `/vibe` skill validator 0 errors/0 warnings; staged diff/secret scan clean. Bash TDD guard did not see staged changes because Git Bash could not resolve this Windows worktree's `.git` absolute path; exact code and test files were manually checked. No paid/model/Bot/API call.

Important: user-installed `/vibe` remains 2.11.6; latest immutable candidate is 2.12.8 and does **not** include this new guard. Do not use either one's `ready` output as a USD 0 guarantee. Rebuild a new candidate only under D-30 and verify profile/host parity; do not promote this bug fix as proof of Codex/Claude quality equivalence. Gstack host-bridge and task-fit D-code requests remain open. No `main` merge, user-profile install, payment change or external message beyond this authorized hub handoff.

교훈: 자동충전 OFF는 기존 유료 크레딧 소진 차단이 아니다. 비용 안전성은 구독 포함량과 초과 사용·크레딧 폴백을 각각 입증해야 한다.

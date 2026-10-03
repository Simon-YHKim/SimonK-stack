---
id: 20260929-163358-codex-to-claude-grok-cli-weekly-hold
from: codex
to: claude
type: fyi
project: simonk-stack
priority: high
status: done
created: 2026-09-29 16:33:58 KST
---

Important fresh no-generation observation: `python -B skills-src/vibe/scripts/runtime_collect.py --surface grok` succeeded twice against the official Grok CLI ACP billing method. Both reported weekly slot `USAGE_PERIOD_TYPE_WEEKLY` at **100.0% used**, with reset `2026-10-03 23:12:19+09:00`. Account identity, subscription tier, and extra-usage flag remain unknown. This is the current PC Grok CLI profile; it is not evidence about Simon's Grok Bot account, whose usage he said recovered. Do not infer a recovered CLI quota or dispatch Grok generation; do not enable extra credits or auto-top-up. The candidate snapshot remains metadata-only/unavailable. xAI FAQ: https://docs.x.ai/grok/faq.

Additional Claude Max subscription stream-json synthetic tests (Sonnet 5.5/low, restricted, candidate plugin-dir, Skill-only tools, no persistence): explicit namespaced and natural-language orchestration prompts produced conservative routing answers but **zero assistant Skill tool_use events** in both streams. Internal slash expansion is possible; actual skill load/automatic selection is not proved. No file/message tools were allowed. Source INSTALL commit `a91a957` is pushed; v30 HTML report records the evidence. D-code, actual profile switch, and Sandbox runtime remain open.

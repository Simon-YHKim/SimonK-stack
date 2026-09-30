import type { ExternalLinkKey } from '../../shared/ipc';

/**
 * Fixed install-guide URLs opened by key. Only https addresses confirmed in
 * official documentation belong here; keys without a verified URL answer
 * `not-found` instead of guessing.
 *
 * Verified 26.09.19 (DECISIONS 26.09.19 11:20):
 * - claude: Anthropic "Advanced setup" page, lists the Windows PowerShell/CMD/WinGet installs.
 * - codex: OpenAI developer docs entry; answers 308 to learn.chatgpt.com/docs/codex/cli.
 * - grok: xAI "Getting Started - Grok Build", lists `irm https://x.ai/cli/install.ps1 | iex`.
 * - antigravity: Google "Getting Started" CLI tab (`/docs/cli/` redirects here), lists
 *   `irm https://antigravity.google/cli/install.ps1 | iex`; the query selects that tab.
 * - grok-bot-usage (26.09.30): Cursor's Spending tab, linked from cursor.com/help/account-and-billing/spend-limits.
 *   It shows on-demand charges and the Monthly Limit set for Grok Bot's on-demand usage.
 * - grok-usage (26.09.30): grok.com Settings → Usage, the address the user's own browser showed. It lists the
 *   SuperGrok weekly limit (what the Grok card reads through the CLI) and, separately, "Weekly Grok Bot Limit"
 *   with its exact reset time.
 */
export const EXTERNAL_LINKS: Readonly<Partial<Record<ExternalLinkKey, string>>> = Object.freeze({
  'claude-cli-install': 'https://code.claude.com/docs/en/setup',
  'codex-cli-install': 'https://developers.openai.com/codex/cli',
  'codex-usage': 'https://chatgpt.com/codex/settings/usage',
  'grok-cli-install': 'https://docs.x.ai/build/overview',
  'grok-bot-usage': 'https://cursor.com/dashboard/spending',
  'grok-usage': 'https://grok.com/?_s=usage',
  'antigravity-cli-install': 'https://antigravity.google/docs/getting-started?tab=cli',
});

/** Hosts an install-guide link may point at; each belongs to the provider that ships the CLI. */
export const EXTERNAL_LINK_HOSTS: Readonly<Record<ExternalLinkKey, readonly string[]>> = Object.freeze({
  'claude-cli-install': ['code.claude.com'],
  'codex-cli-install': ['developers.openai.com'],
  'codex-usage': ['chatgpt.com'],
  'grok-cli-install': ['docs.x.ai'],
  'grok-bot-usage': ['cursor.com'],
  'grok-usage': ['grok.com'],
  'antigravity-cli-install': ['antigravity.google'],
});

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
 */
export const EXTERNAL_LINKS: Readonly<Partial<Record<ExternalLinkKey, string>>> = Object.freeze({
  'claude-cli-install': 'https://code.claude.com/docs/en/setup',
  'codex-cli-install': 'https://developers.openai.com/codex/cli',
  'grok-cli-install': 'https://docs.x.ai/build/overview',
  'antigravity-cli-install': 'https://antigravity.google/docs/getting-started?tab=cli',
});

/** Hosts an install-guide link may point at; each belongs to the provider that ships the CLI. */
export const EXTERNAL_LINK_HOSTS: Readonly<Record<ExternalLinkKey, readonly string[]>> = Object.freeze({
  'claude-cli-install': ['code.claude.com'],
  'codex-cli-install': ['developers.openai.com'],
  'grok-cli-install': ['docs.x.ai'],
  'antigravity-cli-install': ['antigravity.google'],
});

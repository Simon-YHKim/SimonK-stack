import { BASE_ENV_ALLOW, type EnvPolicy } from '../../cli/spawn';

/**
 * Credential/routing overrides removed from every widget-run claude
 * (RESEARCH 3-1 step 2), plus the alternate login inputs read by
 * `claude auth login` in claude.exe 2.1.270.
 */
export const CLAUDE_ENV_REMOVE: readonly string[] = [
  'ANTHROPIC_API_KEY',
  'ANTHROPIC_AUTH_TOKEN',
  'CLAUDE_CODE_OAUTH_TOKEN',
  'CLAUDE_CODE_USE_BEDROCK',
  'CLAUDE_CODE_USE_VERTEX',
  'CLAUDE_CODE_USE_FOUNDRY',
  'ANTHROPIC_PROFILE',
  'ANTHROPIC_FEDERATION_RULE_ID',
  'ANTHROPIC_ORGANIZATION_ID',
  'AWS_BEARER_TOKEN_BEDROCK',
  'ANTHROPIC_CUSTOM_HEADERS',
  'CLAUDE_CODE_OAUTH_REFRESH_TOKEN',
  'CLAUDE_CODE_OAUTH_SCOPES',
  'CLAUDE_CODE_OAUTH_CLIENT_ID',
  'CLAUDE_CODE_CUSTOM_OAUTH_URL',
  'CLAUDE_CONFIG_DIR',
];

/** Non-credential variables claude needs behind proxies or with a custom Git Bash. */
export const CLAUDE_ENV_EXTRA_ALLOW: readonly string[] = [
  'HTTPS_PROXY',
  'HTTP_PROXY',
  'NO_PROXY',
  'NODE_EXTRA_CA_CERTS',
  'CLAUDE_CODE_GIT_BASH_PATH',
];

export function claudeEnvPolicy(configDir: string): EnvPolicy {
  return {
    allow: [...BASE_ENV_ALLOW, ...CLAUDE_ENV_EXTRA_ALLOW],
    remove: CLAUDE_ENV_REMOVE,
    set: { CLAUDE_CONFIG_DIR: configDir },
  };
}

import { maskEmail } from '../../../shared/mask';
import { isPlainObject } from '../../../shared/validate';
import { stripAnsi } from '../../cli/text';
import type { ProviderIdentity } from '../types';

export type AuthStatusParse = { ok: true; identity: ProviderIdentity } | { ok: false };

const PLAN_RE = /^[A-Za-z0-9_-]{1,32}$/;

/**
 * Parses `claude auth status --json`. Field names (loggedIn, authMethod, email,
 * subscriptionType) come from claude.exe 2.1.270 and a probe in an empty
 * CLAUDE_CONFIG_DIR (loggedIn:false, exit 1). The raw e-mail never leaves this function.
 */
export function parseAuthStatus(stdout: string): AuthStatusParse {
  const text = stripAnsi(stdout);
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start === -1 || end <= start) return { ok: false };
  let value: unknown;
  try {
    value = JSON.parse(text.slice(start, end + 1));
  } catch {
    return { ok: false };
  }
  if (!isPlainObject(value) || typeof value.loggedIn !== 'boolean') return { ok: false };
  if (!value.loggedIn) return { ok: true, identity: { loggedIn: false } };
  const identity: ProviderIdentity = { loggedIn: true };
  if (typeof value.email === 'string' && value.email.includes('@')) identity.emailMasked = maskEmail(value.email);
  if (typeof value.subscriptionType === 'string' && PLAN_RE.test(value.subscriptionType)) {
    identity.plan = value.subscriptionType.toLowerCase();
  }
  return { ok: true, identity };
}

const VERSION_RE = /(\d+\.\d+\.\d+)/;

/** `2.1.270 (Claude Code)` -> `2.1.270`. */
export function parseClaudeVersion(stdout: string): string | undefined {
  return VERSION_RE.exec(stripAnsi(stdout))?.[1];
}

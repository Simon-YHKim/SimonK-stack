import type { ExternalLinkKey } from '../../shared/ipc';

/**
 * Fixed install-guide URLs opened by key. Only https addresses confirmed in
 * official documentation belong here; keys without a verified URL answer
 * `not-found` instead of guessing (docs/RESEARCH-auth-quota.md lists none yet).
 */
export const EXTERNAL_LINKS: Readonly<Partial<Record<ExternalLinkKey, string>>> = Object.freeze({});

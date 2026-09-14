import { describe, expect, it } from 'vitest';
import { parseAuthStatus, parseClaudeVersion } from './identity';

// Probe 2026-09-15: CLAUDE_CONFIG_DIR=<new empty temp dir> `claude auth status --json` (2.1.270), exit 1.
const LOGGED_OUT = `{
  "loggedIn": false,
  "authMethod": "none",
  "apiProvider": "firstParty",
  "analyticsDisabled": false,
  "projectsDirectory": "C:\\\\probe\\\\projects",
  "configDirectory": "C:\\\\probe"
}
`;

// Shape from claude.exe 2.1.270 auth status (email, orgId, orgName, subscriptionType when authMethod is claude.ai).
const LOGGED_IN = JSON.stringify(
  {
    loggedIn: true,
    authMethod: 'claude.ai',
    apiProvider: 'firstParty',
    email: 'someone.long@example.org',
    orgId: '00000000-0000-0000-0000-000000000000',
    orgName: "Someone's Organization",
    subscriptionType: 'max',
  },
  null,
  2,
);

describe('parseAuthStatus', () => {
  it('reports a logged-out profile', () => {
    expect(parseAuthStatus(LOGGED_OUT)).toEqual({ ok: true, identity: { loggedIn: false } });
  });

  it('masks the e-mail and keeps the plan', () => {
    const parsed = parseAuthStatus(LOGGED_IN);
    expect(parsed).toEqual({ ok: true, identity: { loggedIn: true, emailMasked: 's***@e***.org', plan: 'max' } });
    expect(JSON.stringify(parsed)).not.toContain('someone');
    expect(JSON.stringify(parsed)).not.toContain('Organization');
  });

  it('tolerates ANSI noise and drops implausible plan values', () => {
    const noisy = `\u001b[2m${LOGGED_IN.replace('"max"', '"<script>"')}\u001b[0m`;
    expect(parseAuthStatus(noisy)).toEqual({ ok: true, identity: { loggedIn: true, emailMasked: 's***@e***.org' } });
  });

  it('rejects output that is not the status object', () => {
    expect(parseAuthStatus('')).toEqual({ ok: false });
    expect(parseAuthStatus('Not logged in')).toEqual({ ok: false });
    expect(parseAuthStatus('{"authMethod":"none"}')).toEqual({ ok: false });
    expect(parseAuthStatus('[1,2]')).toEqual({ ok: false });
  });
});

describe('parseClaudeVersion', () => {
  it('extracts the semver from `claude --version`', () => {
    expect(parseClaudeVersion('2.1.270 (Claude Code)\n')).toBe('2.1.270');
    expect(parseClaudeVersion('unknown')).toBeUndefined();
  });
});

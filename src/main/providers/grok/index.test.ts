// Adapter tests against test-fixtures/fake-grok.cjs (a fake grok binary run with node).
// No real grok.exe, GROK_HOME or credentials are involved.
import { mkdir, mkdtemp, readFile, rm, stat, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import type { Account, LoginEvent } from '../../../shared/types';
import { createLogger } from '../../log';
import { profileDirFor } from '../../paths';
import { ProviderError, type ProviderDeps } from '../types';
import { createGrokAdapter, parseGrokVersion, resolveGrokCli, type GrokAdapterOptions } from './index';

const FIXTURE = fileURLToPath(new URL('./test-fixtures/fake-grok.cjs', import.meta.url));
const NOW = Date.parse('2026-09-15T00:00:00Z');
const LEAK_KEY = 'xai-test-key-must-not-leak-0000000000';
const TEST_TIMEOUT = 30_000;

let root: string;
let logLines: string[];

beforeEach(async () => {
  root = await mkdtemp(path.join(os.tmpdir(), 'grok-adapter-test-'));
  logLines = [];
});

afterEach(async () => {
  await rm(root, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 });
});

function makeDeps(): ProviderDeps {
  const localDataRoot = path.join(root, 'local');
  return {
    logger: createLogger({ sinks: [{ write: (line) => logLines.push(line) }], minLevel: 'debug', scope: 'test' }),
    now: () => NOW,
    appVersion: '2.0.0-test',
    localDataRoot,
    profilesRoot: path.join(localDataRoot, 'profiles'),
    bridgeRoot: path.join(localDataRoot, 'bridge'),
    resourcesDir: path.join(root, 'resources'),
    homeDir: path.join(root, 'home'),
    env: { ...process.env, XAI_API_KEY: LEAK_KEY, GROK_HOME: path.join(root, 'must-not-be-used') },
  };
}

function makeAccount(deps: ProviderDeps, id = 'acct-1'): Account {
  return {
    id,
    provider: 'grok',
    label: 'Grok test',
    enabled: true,
    order: 0,
    profileDir: profileDirFor(deps.profilesRoot, 'grok', id),
    createdAt: NOW,
  };
}

function setup(scenario: string, options: GrokAdapterOptions = {}) {
  const deps = makeDeps();
  const account = makeAccount(deps);
  const adapter = createGrokAdapter(deps, {
    resolveCli: () => ({
      ok: true,
      command: { file: process.execPath, prefixArgs: [FIXTURE, `--scenario=${scenario}`, `--expect-home=${account.profileDir}`] },
      source: FIXTURE,
    }),
    ...options,
  });
  return { deps, account, adapter };
}

async function recordedCalls(account: Account): Promise<string[]> {
  try {
    return (await readFile(path.join(account.profileDir, 'calls.log'), 'utf8')).split('\n').filter((line) => line.length > 0);
  } catch {
    return [];
  }
}

const signal = (): AbortSignal => new AbortController().signal;

describe('resolveGrokCli', () => {
  const home = 'C:\\Users\\tester';
  const managed = path.win32.join(home, '.grok', 'bin', 'grok.exe');
  const baseDeps = { platform: 'win32' as const, readText: () => '' };

  it('prefers grok on PATH', () => {
    const onPath = 'C:\\tools\\grok.exe';
    const result = resolveGrokCli(home, {
      ...baseDeps,
      env: { PATH: 'C:\\tools', PATHEXT: '.EXE;.CMD' },
      isFile: (file) => file.toLowerCase() === onPath.toLowerCase() || file.toLowerCase() === managed.toLowerCase(),
    });
    expect(result).toEqual({ ok: true, command: { file: onPath, prefixArgs: [] }, source: onPath });
  });

  it('falls back to the managed install under the home dir', () => {
    const result = resolveGrokCli(home, {
      ...baseDeps,
      env: { PATH: 'C:\\Windows', PATHEXT: '.EXE;.CMD' },
      isFile: (file) => file.toLowerCase() === managed.toLowerCase(),
    });
    expect(result).toEqual({ ok: true, command: { file: managed, prefixArgs: [] }, source: managed });
  });

  it('reports cli-not-found when neither exists', () => {
    expect(resolveGrokCli(home, { ...baseDeps, env: { PATH: '' }, isFile: () => false })).toEqual({ ok: false, code: 'cli-not-found' });
  });
});

describe('parseGrokVersion', () => {
  it('reads the version from grok --version output', () => {
    expect(parseGrokVersion('grok 1.0.30 (04b7ffed98c6) [stable]\n')).toBe('1.0.30');
    expect(parseGrokVersion('no version here')).toBeUndefined();
  });
});

describe('grok adapter: detectCli', () => {
  it('reports the version of a found CLI', async () => {
    const { adapter } = setup('weekly');
    await expect(adapter.detectCli(signal())).resolves.toEqual({ found: true, path: FIXTURE, version: '1.0.30' });
  }, TEST_TIMEOUT);

  it('reports a missing CLI', async () => {
    const deps = makeDeps();
    const adapter = createGrokAdapter(deps, { resolveCli: () => ({ ok: false, code: 'cli-not-found' }) });
    await expect(adapter.detectCli()).resolves.toEqual({ found: false, errorCode: 'cli-not-found' });
  });
});

describe('grok adapter: fetchUsage', () => {
  it('maps weekly billing from ACP and isolates the child environment', async () => {
    const { adapter, account } = setup('weekly');
    const snapshot = await adapter.fetchUsage(account, signal());
    expect(snapshot).toEqual({
      accountId: 'acct-1',
      provider: 'grok',
      state: 'ok',
      windows: [
        {
          kind: 'weekly',
          usedPercent: 42.5,
          resetsAt: Date.parse('2026-09-17T07:51:00Z'),
          windowMinutes: 10_080,
          label: 'credits',
        },
      ],
      plan: 'Super Grok',
      measuredAt: NOW,
      lastSuccessAt: NOW,
      source: 'grok-acp',
    });
    // Only the handshake and billing: no session/new, session/prompt or auth/* methods.
    expect(await recordedCalls(account)).toEqual(['initialize', '_x.ai/billing']);
    expect(logLines.join('\n')).not.toContain(LEAK_KEY);
  }, TEST_TIMEOUT);

  it('maps monthly billing to an other window', async () => {
    const { adapter, account } = setup('monthly');
    const snapshot = await adapter.fetchUsage(account, signal());
    expect(snapshot.state).toBe('ok');
    expect(snapshot.windows).toEqual([
      { kind: 'other', usedPercent: 30, resetsAt: Date.parse('2026-10-01T00:00:00Z'), windowMinutes: 43_200, label: 'monthly' },
    ]);
  }, TEST_TIMEOUT);

  it('keeps 100% usage as ok, not blocked', async () => {
    const { adapter, account } = setup('full');
    const snapshot = await adapter.fetchUsage(account, signal());
    expect(snapshot.state).toBe('ok');
    expect(snapshot.windows[0]?.usedPercent).toBe(100);
    expect(snapshot.errorCode).toBeUndefined();
  }, TEST_TIMEOUT);

  it('uses the unprefixed method name when only that one exists', async () => {
    const { adapter, account } = setup('legacy-name');
    const snapshot = await adapter.fetchUsage(account, signal());
    expect(snapshot.state).toBe('ok');
    expect(await recordedCalls(account)).toEqual(['initialize', '_x.ai/billing', 'x.ai/billing']);
  }, TEST_TIMEOUT);

  const failures: Array<[string, string, string]> = [
    ['logged-out', 'logged-out', 'not-logged-in'],
    ['no-billing', 'unavailable', 'quota-unavailable'],
    ['empty', 'unavailable', 'quota-unavailable'],
    ['rate-limited', 'error', 'rate-limited'],
    ['garbage', 'error', 'parse-error'],
    ['crash', 'error', 'protocol-error'],
    ['bad-version', 'error', 'cli-unsupported-version'],
  ];
  it.each(failures)('scenario %s -> state %s / %s with no windows', async (scenario, state, code) => {
    const { adapter, account } = setup(scenario);
    const snapshot = await adapter.fetchUsage(account, signal());
    expect(snapshot).toMatchObject({ state, errorCode: code, windows: [], measuredAt: null, lastSuccessAt: null, source: 'grok-acp' });
  }, TEST_TIMEOUT);

  it('times out a hanging billing request', async () => {
    const { adapter, account } = setup('hang', { timeouts: { acpRequestMs: 800 } });
    const started = Date.now();
    const snapshot = await adapter.fetchUsage(account, signal());
    expect(snapshot).toMatchObject({ state: 'error', errorCode: 'timeout' });
    expect(Date.now() - started).toBeLessThan(15_000);
  }, TEST_TIMEOUT);

  it('returns cancelled when aborted', async () => {
    const { adapter, account } = setup('hang');
    const controller = new AbortController();
    setTimeout(() => controller.abort(), 700);
    const snapshot = await adapter.fetchUsage(account, controller.signal);
    expect(snapshot).toMatchObject({ state: 'error', errorCode: 'cancelled' });
  }, TEST_TIMEOUT);

  it('reports a missing CLI as data', async () => {
    const deps = makeDeps();
    const adapter = createGrokAdapter(deps, { resolveCli: () => ({ ok: false, code: 'cli-not-found' }) });
    const snapshot = await adapter.fetchUsage(makeAccount(deps), signal());
    expect(snapshot).toMatchObject({ state: 'error', errorCode: 'cli-not-found' });
  });

  it('refuses a profile dir outside the grok profiles root', async () => {
    const { adapter, account } = setup('weekly');
    const snapshot = await adapter.fetchUsage({ ...account, profileDir: path.join(root, 'elsewhere') }, signal());
    expect(snapshot).toMatchObject({ state: 'error', errorCode: 'internal' });
  });
});

describe('grok adapter: getIdentity', () => {
  it('infers login from billing and reuses the result for the next fetchUsage', async () => {
    const { adapter, account } = setup('weekly');
    await expect(adapter.getIdentity(account, signal())).resolves.toEqual({ loggedIn: true, plan: 'Super Grok' });
    const snapshot = await adapter.fetchUsage(account, signal());
    expect(snapshot.state).toBe('ok');
    expect(await recordedCalls(account)).toEqual(['initialize', '_x.ai/billing']);
  }, TEST_TIMEOUT);

  it('reports logged out on the authentication error', async () => {
    const { adapter, account } = setup('logged-out');
    await expect(adapter.getIdentity(account, signal())).resolves.toEqual({ loggedIn: false });
  }, TEST_TIMEOUT);

  it('throws when the login state cannot be determined', async () => {
    const { adapter, account } = setup('no-billing');
    const identity = adapter.getIdentity(account, signal());
    await expect(identity).rejects.toBeInstanceOf(ProviderError);
    await expect(identity).rejects.toMatchObject({ code: 'quota-unavailable' });
  }, TEST_TIMEOUT);
});

describe('grok adapter: startLogin', () => {
  it('emits the device code, waits for exit 0 and verifies via billing', async () => {
    const { adapter, account } = setup('after-login');
    const events: LoginEvent[] = [];
    await adapter.startLogin(account, (event) => events.push(event), signal());
    expect(events).toEqual([
      { type: 'progress', stage: 'starting' },
      {
        type: 'device-code',
        userCode: 'WXYZ-2345',
        verificationUrl: 'https://accounts.x.ai/device',
        expiresAt: NOW + 15 * 60_000,
      },
      { type: 'progress', stage: 'waiting-device-code' },
      { type: 'progress', stage: 'verifying' },
      { type: 'success', plan: 'Super Grok' },
    ]);
    const logs = logLines.join('\n');
    expect(logs).not.toContain('WXYZ-2345');
    expect(logs).not.toContain('accounts.x.ai');
    expect(logs).not.toContain(LEAK_KEY);

    const snapshot = await adapter.fetchUsage(account, signal());
    expect(snapshot.state).toBe('ok');
    expect(await recordedCalls(account)).toEqual(['login --device-auth', 'initialize', '_x.ai/billing']);
  }, TEST_TIMEOUT);

  it('maps an expired device code', async () => {
    const { adapter, account } = setup('login-expired');
    const events: LoginEvent[] = [];
    await adapter.startLogin(account, (event) => events.push(event), signal());
    expect(events.at(-1)).toEqual({ type: 'error', code: 'login-expired' });
  }, TEST_TIMEOUT);

  it('kills the login and reports cancelled on abort', async () => {
    const { adapter, account } = setup('login-hang');
    const controller = new AbortController();
    const events: LoginEvent[] = [];
    await adapter.startLogin(
      account,
      (event) => {
        events.push(event);
        if (event.type === 'device-code') setTimeout(() => controller.abort(), 50);
      },
      controller.signal,
    );
    expect(events.some((event) => event.type === 'device-code')).toBe(true);
    expect(events.at(-1)).toEqual({ type: 'error', code: 'cancelled' });
  }, TEST_TIMEOUT);

  it('times out a login that never finishes', async () => {
    const { adapter, account } = setup('login-hang', { timeouts: { loginMs: 1500 } });
    const events: LoginEvent[] = [];
    await adapter.startLogin(account, (event) => events.push(event), signal());
    expect(events.at(-1)).toEqual({ type: 'error', code: 'timeout' });
  }, TEST_TIMEOUT);

  it('reports a missing CLI', async () => {
    const deps = makeDeps();
    const adapter = createGrokAdapter(deps, { resolveCli: () => ({ ok: false, code: 'cli-not-found' }) });
    const events: LoginEvent[] = [];
    await adapter.startLogin(makeAccount(deps), (event) => events.push(event), signal());
    expect(events).toEqual([
      { type: 'progress', stage: 'starting' },
      { type: 'error', code: 'cli-not-found' },
    ]);
  });
});

describe('grok adapter: profile dirs', () => {
  it('creates and removes the account profile dir', async () => {
    const { adapter, account } = setup('weekly');
    await adapter.ensureProfileDir(account);
    await adapter.ensureProfileDir(account);
    await writeFile(path.join(account.profileDir, 'auth.json'), '{}');
    expect((await stat(account.profileDir)).isDirectory()).toBe(true);
    await adapter.removeProfile(account);
    await expect(stat(account.profileDir)).rejects.toMatchObject({ code: 'ENOENT' });
  });

  it('refuses paths outside the grok profiles root', async () => {
    const { adapter, account, deps } = setup('weekly');
    const outside = path.join(root, 'outside');
    await mkdir(outside, { recursive: true });
    await expect(adapter.removeProfile({ ...account, profileDir: outside })).rejects.toBeInstanceOf(ProviderError);
    await expect(adapter.ensureProfileDir({ ...account, profileDir: deps.profilesRoot })).rejects.toBeInstanceOf(ProviderError);
    await expect(
      adapter.removeProfile({ ...account, profileDir: profileDirFor(deps.profilesRoot, 'codex', account.id) }),
    ).rejects.toBeInstanceOf(ProviderError);
    expect((await stat(outside)).isDirectory()).toBe(true);
  });
});

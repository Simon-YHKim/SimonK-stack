// Adapter tests against test-fixtures/fake-agy.cjs (a fake agy binary run with node).
// No real agy.exe, Windows credential store or Google account is involved.
import { mkdtemp, readFile, rm, stat } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import type { Account, LoginEvent } from '../../../shared/types';
import { createLogger } from '../../log';
import { profileDirFor } from '../../paths';
import { ProviderError, type ProviderDeps } from '../types';
import { createAntigravityAdapter, parseAgyVersion, resolveAgyCli, type AntigravityAdapterOptions } from './index';

const FIXTURE = fileURLToPath(new URL('./test-fixtures/fake-agy.cjs', import.meta.url));
const NOW = Date.parse('2026-09-19T03:00:00Z');
const LEAK_KEY = 'gemini-test-key-must-not-leak-000000';
const TEST_TIMEOUT = 30_000;

let root: string;
let logLines: string[];
let clock: number;

beforeEach(async () => {
  root = await mkdtemp(path.join(os.tmpdir(), 'agy-adapter-test-'));
  logLines = [];
  clock = NOW;
});

afterEach(async () => {
  await rm(root, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 });
});

function makeDeps(): ProviderDeps {
  const localDataRoot = path.join(root, 'local');
  return {
    logger: createLogger({ sinks: [{ write: (line) => logLines.push(line) }], minLevel: 'debug', scope: 'test' }),
    now: () => clock,
    appVersion: '2.0.0-test',
    localDataRoot,
    profilesRoot: path.join(localDataRoot, 'profiles'),
    bridgeRoot: path.join(localDataRoot, 'bridge'),
    resourcesDir: path.join(root, 'resources'),
    homeDir: path.join(root, 'home'),
    env: { ...process.env, GEMINI_API_KEY: LEAK_KEY },
  };
}

function makeAccount(deps: ProviderDeps, id = 'acct-1'): Account {
  return {
    id,
    provider: 'antigravity',
    label: 'Antigravity test',
    enabled: true,
    order: 0,
    profileDir: profileDirFor(deps.profilesRoot, 'antigravity', id),
    createdAt: NOW,
  };
}

interface Call {
  args: string[];
  cwd: string;
  autoUpdateOff: string | null;
  leakedKey: string | null;
}

function setup(scenario: string, options: AntigravityAdapterOptions = {}) {
  const deps = makeDeps();
  const account = makeAccount(deps);
  const callLog = path.join(root, 'calls.jsonl');
  const adapter = createAntigravityAdapter(deps, {
    resolveCli: () => ({ ok: true, command: { file: process.execPath, prefixArgs: [FIXTURE, scenario, callLog] }, source: 'fake-agy' }),
    ...options,
  });
  const calls = async (): Promise<Call[]> => {
    const text = await readFile(callLog, 'utf8').catch(() => '');
    return text
      .split('\n')
      .filter((line) => line !== '')
      .map((line) => JSON.parse(line) as Call);
  };
  return { deps, account, adapter, calls };
}

const never = new AbortController().signal;

describe('antigravity adapter', () => {
  it(
    'reads usage through `agy -p /usage` in its own empty folder with the updater off',
    async () => {
      const { adapter, account, calls } = setup('ok');
      const snapshot = await adapter.fetchUsage(account, never);

      expect(snapshot).toMatchObject({
        accountId: account.id,
        provider: 'antigravity',
        source: 'antigravity-cli-usage',
        state: 'ok',
        measuredAt: NOW,
        lastSuccessAt: NOW,
      });
      expect(snapshot.windows.map((w) => `${w.label}:${w.kind}`)).toEqual([
        'Gemini Models:session',
        'Gemini Models:weekly',
        'Claude and GPT models:session',
        'Claude and GPT models:weekly',
      ]);

      const [call] = await calls();
      expect(call?.args).toEqual(['-p', '/usage', '--output-format', 'json', '--print-timeout', '30s']);
      expect(path.resolve(call?.cwd ?? '')).toBe(path.resolve(account.profileDir));
      expect(call?.autoUpdateOff).toBe('1');
      expect(call?.leakedKey).toBeNull();
      expect(logLines.join('\n')).not.toContain(LEAK_KEY);
    },
    TEST_TIMEOUT,
  );

  it(
    'shares one agy run between getIdentity and the following fetchUsage',
    async () => {
      const { adapter, account, calls } = setup('ok');
      await expect(adapter.getIdentity(account, never)).resolves.toEqual({ loggedIn: true });
      const snapshot = await adapter.fetchUsage(account, never);
      expect(snapshot.state).toBe('ok');
      expect(await calls()).toHaveLength(1);

      clock += 60_000;
      await adapter.fetchUsage(account, never);
      expect(await calls()).toHaveLength(2);
    },
    TEST_TIMEOUT,
  );

  it(
    'stops calling agy for the rest of the run once /usage is answered as an AI prompt',
    async () => {
      const { adapter, account, calls } = setup('prompt');
      const first = await adapter.fetchUsage(account, never);
      expect(first).toMatchObject({ state: 'unavailable', errorCode: 'cli-unsupported-version', windows: [] });

      clock += 60_000;
      const second = await adapter.fetchUsage(account, never);
      expect(second).toMatchObject({ state: 'unavailable', errorCode: 'cli-unsupported-version' });
      await expect(adapter.getIdentity(account, never)).rejects.toMatchObject({ code: 'cli-unsupported-version' });
      // One spent request at most: the later refreshes never reached the CLI.
      expect(await calls()).toHaveLength(1);
    },
    TEST_TIMEOUT,
  );

  it(
    'reports a signed-out CLI as logged-out and unparseable output as an error with no values',
    async () => {
      const signedOut = setup('signed-out');
      await expect(signedOut.adapter.getIdentity(signedOut.account, never)).resolves.toEqual({ loggedIn: false });
      clock += 60_000;
      expect(await signedOut.adapter.fetchUsage(signedOut.account, never)).toMatchObject({
        state: 'logged-out',
        errorCode: 'not-logged-in',
        windows: [],
        measuredAt: null,
      });

      const garbage = setup('garbage');
      expect(await garbage.adapter.fetchUsage(garbage.account, never)).toMatchObject({ state: 'error', errorCode: 'parse-error', windows: [] });
      clock += 60_000;
      const identity = garbage.adapter.getIdentity(garbage.account, never);
      await expect(identity).rejects.toBeInstanceOf(ProviderError);
      await expect(identity).rejects.toMatchObject({ code: 'parse-error' });
    },
    TEST_TIMEOUT,
  );

  it(
    'kills a hanging agy at the timeout and honours abort',
    async () => {
      const slow = setup('hang', { timeouts: { usageMs: 1_500 } });
      expect(await slow.adapter.fetchUsage(slow.account, never)).toMatchObject({ state: 'error', errorCode: 'timeout' });

      const aborted = setup('hang');
      const controller = new AbortController();
      const pending = aborted.adapter.fetchUsage(aborted.account, controller.signal);
      setTimeout(() => controller.abort(), 300);
      expect(await pending).toMatchObject({ state: 'error', errorCode: 'cancelled' });
    },
    TEST_TIMEOUT,
  );

  it(
    'has no widget login: startLogin answers not-implemented without starting agy',
    async () => {
      const { adapter, account, calls } = setup('ok');
      const events: LoginEvent[] = [];
      await adapter.startLogin(account, (event) => events.push(event), never);
      expect(events).toEqual([{ type: 'error', code: 'not-implemented' }]);
      expect(adapter.loginUrlHosts).toEqual([]);
      expect(await calls()).toHaveLength(0);
    },
    TEST_TIMEOUT,
  );

  it(
    'detects the CLI version and reports a missing CLI without throwing',
    async () => {
      const found = setup('ok');
      await expect(found.adapter.detectCli()).resolves.toMatchObject({ found: true, version: '1.2.6', path: 'fake-agy' });

      const missing = setup('ok', { resolveCli: () => ({ ok: false, code: 'cli-not-found' }) });
      await expect(missing.adapter.detectCli()).resolves.toEqual({ found: false, errorCode: 'cli-not-found' });
      expect(await missing.adapter.fetchUsage(missing.account, never)).toMatchObject({ state: 'error', errorCode: 'cli-not-found' });
    },
    TEST_TIMEOUT,
  );

  it(
    'creates and removes only the widget-owned folder and refuses paths outside the profiles root',
    async () => {
      const { adapter, account, deps } = setup('ok');
      await adapter.ensureProfileDir(account);
      expect((await stat(account.profileDir)).isDirectory()).toBe(true);
      await adapter.removeProfile(account);
      await expect(stat(account.profileDir)).rejects.toMatchObject({ code: 'ENOENT' });

      const outside: Account = { ...account, profileDir: path.join(deps.homeDir, '.gemini') };
      await expect(adapter.ensureProfileDir(outside)).rejects.toBeInstanceOf(ProviderError);
      await expect(adapter.removeProfile(outside)).rejects.toBeInstanceOf(ProviderError);
      const wrongProvider: Account = { ...account, provider: 'grok' };
      await expect(adapter.removeProfile(wrongProvider)).rejects.toBeInstanceOf(ProviderError);
    },
    TEST_TIMEOUT,
  );
});

describe('parseAgyVersion', () => {
  it('accepts the bare and the prefixed form', () => {
    expect(parseAgyVersion('1.2.6\n')).toBe('1.2.6');
    expect(parseAgyVersion('agy 1.3.0-beta.1')).toBe('1.3.0-beta.1');
    expect(parseAgyVersion('no version here')).toBeUndefined();
  });
});

describe('resolveAgyCli', () => {
  const managed = 'C:\\Users\\u\\AppData\\Local\\agy\\bin\\agy.exe';
  const env = { PATH: 'C:\\nowhere', PATHEXT: '.EXE', LOCALAPPDATA: 'C:\\Users\\u\\AppData\\Local' };

  it('falls back to the managed install folder when agy is not on PATH', () => {
    const result = resolveAgyCli(env, { platform: 'win32', env, isFile: (file) => file === managed, readText: () => '' });
    expect(result).toMatchObject({ ok: true, command: { file: managed, prefixArgs: [] } });
  });

  it('reports cli-not-found when agy is neither on PATH nor in the managed install folder', () => {
    const result = resolveAgyCli(env, { platform: 'win32', env, isFile: () => false, readText: () => '' });
    expect(result).toEqual({ ok: false, code: 'cli-not-found' });
  });
});

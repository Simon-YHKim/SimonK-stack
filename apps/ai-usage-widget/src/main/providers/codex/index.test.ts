// Adapter tests against a fake line-delimited JSON-RPC child (test-only fixture).
// The fake reads its scenario from <CODEX_HOME>/fake-scenario.json, which also proves
// CODEX_HOME is passed, and logs what it received to <CODEX_HOME>/fake-log.jsonl.
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { afterAll, describe, expect, it } from 'vitest';
import type { Account, LoginEvent } from '../../../shared/types';
import type { ResolveResult } from '../../cli/resolve';
import { nullLogger } from '../../log';
import { profileDirFor } from '../../paths';
import type { ProviderDeps } from '../types';
import { createCodexAdapter, type CodexAdapterOptions } from './index';
import { CODEX_ENV_ALLOW } from './session';

const FAKE_APP_SERVER = `'use strict';
const fs = require('fs');
const path = require('path');
const home = process.env.CODEX_HOME || '';
const args = process.argv.slice(2);
function log(entry) { if (home) fs.appendFileSync(path.join(home, 'fake-log.jsonl'), JSON.stringify(entry) + '\\n'); }
if (args[0] === '--version') {
  log({ kind: 'version', envKeys: Object.keys(process.env), cwd: process.cwd() });
  process.stderr.write('WARNING: fake warning\\n');
  process.stdout.write('codex-cli 9.8.7\\n');
  process.exit(0);
}
if (args[0] !== 'app-server') process.exit(2);
const scenario = JSON.parse(fs.readFileSync(path.join(home, 'fake-scenario.json'), 'utf8'));
const responses = scenario.responses || {};
const calls = {};
function alivePeers() {
  try {
    return fs.readFileSync(path.join(home, 'fake-log.jsonl'), 'utf8').split('\\n').filter(Boolean)
      .map(function (line) { return JSON.parse(line); })
      .filter(function (entry) { return entry.kind === 'start'; })
      .map(function (entry) { return entry.pid; })
      .filter(function (pid) { try { process.kill(pid, 0); return true; } catch (e) { return false; } });
  } catch (e) { return []; }
}
log({ kind: 'start', pid: process.pid, alivePeers: alivePeers(), args: args, envKeys: Object.keys(process.env), cwd: process.cwd() });
if (scenario.grandchild) {
  const child = require('child_process').spawn(process.execPath, ['-e', 'setInterval(function(){},1000)'], { stdio: 'ignore', windowsHide: true });
  log({ kind: 'grandchild', pid: child.pid });
}
if (scenario.ignoreStdinClose) setInterval(function () {}, 1000);
process.stderr.write('WARNING: fake app-server warning\\n');
function send(message) { process.stdout.write(JSON.stringify(message) + '\\n'); }
let buffer = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', function (chunk) {
  buffer += chunk;
  let index;
  while ((index = buffer.indexOf('\\n')) >= 0) {
    const line = buffer.slice(0, index);
    buffer = buffer.slice(index + 1);
    if (line.trim().length > 0) handle(JSON.parse(line));
  }
});
process.stdin.on('end', function () { log({ kind: 'stdin-end' }); if (!scenario.ignoreStdinClose) process.exit(0); });
function handle(message) {
  log({ kind: 'recv', message: message });
  if (message.id === undefined) return;
  let spec = responses[message.method];
  // { sequence: [specA, specB] }: one spec per call, the last one repeats.
  if (spec !== undefined && Array.isArray(spec.sequence)) {
    calls[message.method] = (calls[message.method] || 0) + 1;
    spec = spec.sequence[Math.min(calls[message.method], spec.sequence.length) - 1];
  }
  if (spec === undefined && message.method === 'initialize') {
    spec = {
      result: { userAgent: 'fake/1', codexHome: scenario.codexHome || home, platformFamily: 'windows', platformOs: 'windows', futureField: true },
      then: [{ method: 'remoteControl/status/changed', params: {}, emittedAtMs: 1 }],
    };
  }
  if (spec === undefined) {
    send({ id: message.id, error: { code: -32600, message: 'Invalid request: unknown variant ' + message.method } });
    return;
  }
  if (spec.hang) return;
  setTimeout(function () {
    if (spec.error) send({ id: message.id, error: spec.error });
    else send({ id: message.id, result: spec.result });
    (spec.then || []).forEach(function (note) { setTimeout(function () { send(note); }, note.delayMs || 10); });
  }, spec.delayMs || 0);
}
`;

interface LogEntry {
  kind: string;
  pid?: number;
  /** Earlier app-server processes of the same CODEX_HOME that were still running at start. */
  alivePeers?: number[];
  envKeys?: string[];
  cwd?: string;
  message?: { id?: number; method?: string; params?: unknown };
}

const root = mkdtempSync(path.join(os.tmpdir(), 'codex-adapter-test-'));
const script = path.join(root, 'fake-codex.cjs');
writeFileSync(script, FAKE_APP_SERVER);

afterAll(() => {
  rmSync(root, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 });
});

const fakeCli = (): ResolveResult => ({
  ok: true,
  command: { file: process.execPath, prefixArgs: [script] },
  kind: 'node-script',
  source: script,
});

const NOW = 1_800_000_000_000;
const TIMEOUTS: NonNullable<CodexAdapterOptions['timeouts']> = {
  initMs: 10_000,
  rpcMs: 5_000,
  loginStartMs: 5_000,
  loginMs: 10_000,
  loginCancelMs: 2_000,
  exitGraceMs: 1_000,
  versionMs: 10_000,
  verifyAttempts: 4,
  verifyDelayMs: 50,
};
const TEST_TIMEOUT = 30_000;

let counter = 0;

function setup(options: CodexAdapterOptions = {}) {
  counter += 1;
  const caseRoot = path.join(root, `case${counter}`);
  const profilesRoot = path.join(caseRoot, 'profiles');
  const deps: ProviderDeps = {
    logger: nullLogger,
    now: () => NOW,
    appVersion: '2.0.0-test',
    localDataRoot: caseRoot,
    profilesRoot,
    bridgeRoot: path.join(caseRoot, 'bridge'),
    resourcesDir: path.join(caseRoot, 'resources'),
    homeDir: path.join(caseRoot, 'home'),
    env: {
      ...process.env,
      OPENAI_API_KEY: 'sk-test-must-not-leak-0000000000',
      CODEX_API_KEY: 'must-not-leak',
      SECRET_TOKEN: 'must-not-leak',
    },
  };
  const id = `acct${counter}`;
  const account: Account = {
    id,
    provider: 'codex',
    label: 'Test',
    enabled: true,
    order: 0,
    profileDir: profileDirFor(profilesRoot, 'codex', id),
    createdAt: 0,
  };
  const adapter = createCodexAdapter(deps, {
    resolveCli: fakeCli,
    ...options,
    timeouts: { ...TIMEOUTS, ...options.timeouts },
  });
  return { deps, account, adapter };
}

function writeScenario(account: Account, scenario: Record<string, unknown>): void {
  mkdirSync(account.profileDir, { recursive: true });
  writeFileSync(path.join(account.profileDir, 'fake-scenario.json'), JSON.stringify(scenario));
}

function readLog(dir: string): LogEntry[] {
  const file = path.join(dir, 'fake-log.jsonl');
  if (!existsSync(file)) return [];
  return readFileSync(file, 'utf8')
    .split('\n')
    .filter((line) => line.trim().length > 0)
    .map((line) => JSON.parse(line) as LogEntry);
}

function received(dir: string): Array<NonNullable<LogEntry['message']>> {
  return readLog(dir).flatMap((entry) => (entry.kind === 'recv' && entry.message !== undefined ? [entry.message] : []));
}

function isAlive(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

async function waitUntil(predicate: () => boolean, timeoutMs: number): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (predicate()) return true;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  return predicate();
}

const signal = (): AbortSignal => new AbortController().signal;

const ACCOUNT_PRO = {
  result: { account: { type: 'chatgpt', email: 'john.doe@example.com', planType: 'pro' }, requiresOpenaiAuth: true },
};
const ACCOUNT_NONE = { result: { account: null, requiresOpenaiAuth: true } };
const CODEX_BUCKET = {
  limitId: 'codex',
  limitName: null,
  primary: { usedPercent: 42, windowDurationMins: 300, resetsAt: 1_800_003_600 },
  secondary: { usedPercent: 88, windowDurationMins: 10_080, resetsAt: 1_800_400_000 },
  credits: { hasCredits: false, unlimited: false, balance: null },
  planType: 'pro',
  rateLimitReachedType: null,
};
const RATE_LIMITS = {
  result: {
    rateLimits: CODEX_BUCKET,
    rateLimitsByLimitId: {
      codex: CODEX_BUCKET,
      codex_other: { limitId: 'codex_other', primary: { usedPercent: 5, windowDurationMins: 60, resetsAt: 1_800_001_000 } },
    },
    rateLimitResetCredits: { availableCount: 0, credits: null },
    futureTopLevel: 'ignored',
  },
};
const AUTH_REQUIRED = {
  error: { code: -32600, message: 'codex account authentication required to read rate limits' },
};
const FORBIDDEN_METHODS = [
  'account/rateLimitResetCredit/consume',
  'account/sendAddCreditsNudgeEmail',
  'account/logout',
  'thread/start',
  'turn/start',
];

describe('codex adapter: fetchUsage', () => {
  it(
    'reads identity and rate limits, then shuts the app-server down',
    async () => {
      const { account, adapter } = setup();
      writeScenario(account, { responses: { 'account/read': ACCOUNT_PRO, 'account/rateLimits/read': RATE_LIMITS } });

      const snapshot = await adapter.fetchUsage(account, signal());

      expect(snapshot).toEqual({
        accountId: account.id,
        provider: 'codex',
        state: 'ok',
        windows: [
          { kind: 'session', usedPercent: 42, resetsAt: 1_800_003_600_000, windowMinutes: 300 },
          { kind: 'weekly', usedPercent: 88, resetsAt: 1_800_400_000_000, windowMinutes: 10_080 },
          { kind: 'other', usedPercent: 5, resetsAt: 1_800_001_000_000, windowMinutes: 60, label: 'codex_other' },
        ],
        measuredAt: NOW,
        lastSuccessAt: NOW,
        source: 'codex-app-server',
        plan: 'pro',
      });

      const messages = received(account.profileDir);
      expect(messages.map((m) => m.method)).toEqual(['initialize', 'initialized', 'account/read', 'account/rateLimits/read']);
      expect(messages[0]?.params).toEqual({ clientInfo: { name: 'ai-usage-widget', version: '2.0.0-test' } });
      expect(messages[1]?.id).toBeUndefined();
      expect(messages[2]?.params).toEqual({});
      expect(messages[3]?.params).toEqual({ excludeResetCreditDetails: true });
      expect(messages.some((m) => FORBIDDEN_METHODS.includes(m.method ?? ''))).toBe(false);

      const start = readLog(account.profileDir).find((entry) => entry.kind === 'start');
      const envKeys = (start?.envKeys ?? []).filter((key) => !key.startsWith('=')).map((key) => key.toUpperCase());
      // libuv re-adds these from the parent on Windows even when omitted (uv_spawn required_vars).
      const libuvRequired = ['HOMEDRIVE', 'HOMEPATH', 'LOGONSERVER', 'SYSTEMDRIVE', 'USERDOMAIN', 'USERNAME'];
      const allowed = new Set([...CODEX_ENV_ALLOW.map((key) => key.toUpperCase()), ...libuvRequired, 'CODEX_HOME']);
      expect(envKeys).toContain('CODEX_HOME');
      expect(envKeys.filter((key) => !allowed.has(key))).toEqual([]);
      expect(envKeys).not.toContain('OPENAI_API_KEY');
      expect(envKeys).not.toContain('CODEX_API_KEY');
      expect(start?.cwd?.toLowerCase()).toBe(account.profileDir.toLowerCase());
      expect(await waitUntil(() => !isAlive(start?.pid ?? 0), 5000)).toBe(true);
    },
    TEST_TIMEOUT,
  );

  it(
    'reports logged-out without reading limits when the profile has no account',
    async () => {
      const { account, adapter } = setup();
      writeScenario(account, { responses: { 'account/read': ACCOUNT_NONE, 'account/rateLimits/read': AUTH_REQUIRED } });
      const snapshot = await adapter.fetchUsage(account, signal());
      expect(snapshot).toMatchObject({ state: 'logged-out', errorCode: 'not-logged-in', windows: [], measuredAt: null });
      expect(received(account.profileDir).map((m) => m.method)).not.toContain('account/rateLimits/read');
    },
    TEST_TIMEOUT,
  );

  it(
    'maps an authentication error from rateLimits/read to logged-out',
    async () => {
      const { account, adapter } = setup();
      writeScenario(account, { responses: { 'account/read': ACCOUNT_PRO, 'account/rateLimits/read': AUTH_REQUIRED } });
      expect(await adapter.fetchUsage(account, signal())).toMatchObject({ state: 'logged-out', errorCode: 'not-logged-in' });
    },
    TEST_TIMEOUT,
  );

  it('does not spawn or create folders when the profile dir is missing', async () => {
    const { account, adapter } = setup({ resolveCli: () => ({ ok: false, code: 'cli-not-found' }) });
    expect(await adapter.fetchUsage(account, signal())).toMatchObject({ state: 'logged-out', errorCode: 'not-logged-in' });
    expect(existsSync(account.profileDir)).toBe(false);
  });

  it('reports unavailable when the CLI cannot be resolved or started', async () => {
    const missing = setup({ resolveCli: () => ({ ok: false, code: 'cli-not-found' }) });
    writeScenario(missing.account, {});
    expect(await missing.adapter.fetchUsage(missing.account, signal())).toMatchObject({
      state: 'unavailable',
      errorCode: 'cli-not-found',
    });

    const noNode = setup({ resolveCli: () => ({ ok: false, code: 'node-not-found' }) });
    writeScenario(noNode.account, {});
    expect(await noNode.adapter.fetchUsage(noNode.account, signal())).toMatchObject({
      state: 'unavailable',
      errorCode: 'node-not-found',
    });

    const broken = setup({
      resolveCli: () => ({
        ok: true,
        command: { file: path.join(root, 'definitely-missing', 'codex.exe'), prefixArgs: [] },
        kind: 'exe',
        source: 'x',
      }),
    });
    writeScenario(broken.account, {});
    expect(await broken.adapter.fetchUsage(broken.account, signal())).toMatchObject({
      state: 'unavailable',
      errorCode: 'cli-not-found',
    });
  });

  it(
    'maps rpc and initialize timeouts to error/timeout',
    async () => {
      const rpc = setup({ timeouts: { rpcMs: 300 } });
      writeScenario(rpc.account, { responses: { 'account/read': ACCOUNT_PRO, 'account/rateLimits/read': { hang: true } } });
      expect(await rpc.adapter.fetchUsage(rpc.account, signal())).toMatchObject({ state: 'error', errorCode: 'timeout' });

      const init = setup({ timeouts: { initMs: 300 } });
      writeScenario(init.account, { responses: { initialize: { hang: true } } });
      expect(await init.adapter.fetchUsage(init.account, signal())).toMatchObject({ state: 'error', errorCode: 'timeout' });
    },
    TEST_TIMEOUT,
  );

  it(
    'refuses an app-server that reports a different CODEX_HOME',
    async () => {
      const { account, adapter } = setup();
      writeScenario(account, { codexHome: path.join(root, 'elsewhere'), responses: { 'account/read': ACCOUNT_PRO } });
      expect(await adapter.fetchUsage(account, signal())).toMatchObject({ state: 'error', errorCode: 'protocol-error' });
      expect(received(account.profileDir).map((m) => m.method)).toEqual(['initialize']);
    },
    TEST_TIMEOUT,
  );

  it(
    'flags CLIs without the rate-limit method as unsupported',
    async () => {
      const { account, adapter } = setup();
      writeScenario(account, { responses: { 'account/read': ACCOUNT_PRO } });
      expect(await adapter.fetchUsage(account, signal())).toMatchObject({
        state: 'unavailable',
        errorCode: 'cli-unsupported-version',
      });
    },
    TEST_TIMEOUT,
  );

  it(
    'reports quota-unavailable when no window is present, keeping the plan',
    async () => {
      const { account, adapter } = setup();
      writeScenario(account, {
        responses: {
          'account/read': ACCOUNT_PRO,
          'account/rateLimits/read': { result: { rateLimits: { limitId: 'codex', primary: null, secondary: null } } },
        },
      });
      expect(await adapter.fetchUsage(account, signal())).toMatchObject({
        state: 'unavailable',
        errorCode: 'quota-unavailable',
        plan: 'pro',
        windows: [],
      });
    },
    TEST_TIMEOUT,
  );

  it(
    'maps malformed responses to parse-error',
    async () => {
      const { account, adapter } = setup();
      writeScenario(account, { responses: { 'account/read': ACCOUNT_PRO, 'account/rateLimits/read': { result: 'nope' } } });
      expect(await adapter.fetchUsage(account, signal())).toMatchObject({ state: 'error', errorCode: 'parse-error' });
    },
    TEST_TIMEOUT,
  );

  it(
    'kills the whole process tree when the app-server ignores stdin close',
    async () => {
      const { account, adapter } = setup({ timeouts: { exitGraceMs: 300 } });
      writeScenario(account, {
        grandchild: true,
        ignoreStdinClose: true,
        responses: { 'account/read': ACCOUNT_PRO, 'account/rateLimits/read': RATE_LIMITS },
      });
      expect(await adapter.fetchUsage(account, signal())).toMatchObject({ state: 'ok' });
      const log = readLog(account.profileDir);
      const pid = log.find((entry) => entry.kind === 'start')?.pid ?? 0;
      const grandchild = log.find((entry) => entry.kind === 'grandchild')?.pid ?? 0;
      expect(pid).toBeGreaterThan(0);
      expect(grandchild).toBeGreaterThan(0);
      expect(await waitUntil(() => !isAlive(pid) && !isAlive(grandchild), 8000)).toBe(true);
    },
    TEST_TIMEOUT,
  );

  it(
    'stops on abort and reports cancelled',
    async () => {
      const { account, adapter } = setup();
      writeScenario(account, { responses: { 'account/read': ACCOUNT_PRO, 'account/rateLimits/read': { hang: true } } });
      const controller = new AbortController();
      setTimeout(() => controller.abort(), 1500);
      const started = Date.now();
      expect(await adapter.fetchUsage(account, controller.signal)).toMatchObject({ state: 'error', errorCode: 'cancelled' });
      expect(Date.now() - started).toBeLessThan(10_000);
      const pid = readLog(account.profileDir).find((entry) => entry.kind === 'start')?.pid ?? 0;
      expect(await waitUntil(() => !isAlive(pid), 5000)).toBe(true);
    },
    TEST_TIMEOUT,
  );

  it('rejects accounts whose profile dir is not the widget-owned folder', async () => {
    const { account, adapter, deps } = setup();
    const foreign: Account = { ...account, profileDir: path.join(deps.homeDir, '.codex') };
    expect(await adapter.fetchUsage(foreign, signal())).toMatchObject({ state: 'error', errorCode: 'internal' });
    await expect(adapter.ensureProfileDir(foreign)).rejects.toMatchObject({ code: 'internal' });
    await expect(adapter.getIdentity(foreign, signal())).rejects.toMatchObject({ code: 'internal' });
    await expect(adapter.removeProfile(foreign)).rejects.toMatchObject({ code: 'internal' });
    expect(existsSync(foreign.profileDir)).toBe(false);
    await expect(adapter.ensureProfileDir({ ...account, provider: 'grok' })).rejects.toMatchObject({ code: 'internal' });
  });
});

describe('codex adapter: identity and profile', () => {
  it(
    'returns masked identity and plan',
    async () => {
      const { account, adapter } = setup();
      writeScenario(account, {
        responses: {
          'account/read': { result: { account: { type: 'chatgpt', email: 'jane@example.org', planType: 'plus' } } },
        },
      });
      const identity = await adapter.getIdentity(account, signal());
      expect(identity).toEqual({ loggedIn: true, emailMasked: 'j***@e***.org', plan: 'plus' });
    },
    TEST_TIMEOUT,
  );

  it(
    'reports logged-out identities and throws coded errors for other failures',
    async () => {
      const out = setup();
      writeScenario(out.account, { responses: { 'account/read': ACCOUNT_NONE } });
      expect(await out.adapter.getIdentity(out.account, signal())).toEqual({ loggedIn: false });

      const missing = setup();
      expect(await missing.adapter.getIdentity(missing.account, signal())).toEqual({ loggedIn: false });

      const slow = setup({ timeouts: { rpcMs: 300 } });
      writeScenario(slow.account, { responses: { 'account/read': { hang: true } } });
      await expect(slow.adapter.getIdentity(slow.account, signal())).rejects.toMatchObject({
        name: 'ProviderError',
        code: 'timeout',
      });
    },
    TEST_TIMEOUT,
  );

  it('creates and removes the profile dir', async () => {
    const { account, adapter } = setup();
    await adapter.ensureProfileDir(account);
    await adapter.ensureProfileDir(account);
    expect(existsSync(account.profileDir)).toBe(true);
    writeFileSync(path.join(account.profileDir, 'auth.json'), '{}');
    await adapter.removeProfile(account);
    expect(existsSync(account.profileDir)).toBe(false);
  });

  it(
    'detects the CLI version using a widget-owned CODEX_HOME',
    async () => {
      const { adapter, deps } = setup();
      const info = await adapter.detectCli();
      expect(info).toEqual({ found: true, path: script, version: '9.8.7' });
      const detectHome = path.join(deps.localDataRoot, 'cli-detect', 'codex');
      const entry = readLog(detectHome).find((e) => e.kind === 'version');
      expect(entry?.cwd?.toLowerCase()).toBe(detectHome.toLowerCase());
      expect((entry?.envKeys ?? []).map((k) => k.toUpperCase())).not.toContain('OPENAI_API_KEY');

      const missing = setup({ resolveCli: () => ({ ok: false, code: 'cli-not-found' }) });
      expect(await missing.adapter.detectCli()).toEqual({ found: false, errorCode: 'cli-not-found' });
    },
    TEST_TIMEOUT,
  );
});

describe('codex adapter: device-code login', () => {
  const START_OK = {
    result: {
      type: 'chatgptDeviceCode',
      loginId: 'login-1',
      userCode: 'ABCD-EFGH',
      verificationUrl: 'https://auth.openai.com/codex/device',
    },
  };

  it(
    'emits the device code, waits for completion and reports the masked identity',
    async () => {
      const { account, adapter } = setup();
      writeScenario(account, {
        responses: {
          'account/login/start': {
            ...START_OK,
            then: [
              { method: 'account/login/completed', params: { loginId: 'other', success: false, error: 'x' }, delayMs: 50 },
              { method: 'account/login/completed', params: { loginId: 'login-1', success: true, error: null }, delayMs: 150 },
            ],
          },
          'account/read': ACCOUNT_PRO,
        },
      });
      const events: LoginEvent[] = [];
      await adapter.startLogin(account, (event) => events.push(event), signal());
      expect(events).toEqual([
        { type: 'progress', stage: 'starting' },
        { type: 'device-code', userCode: 'ABCD-EFGH', verificationUrl: 'https://auth.openai.com/codex/device' },
        { type: 'progress', stage: 'waiting-device-code' },
        { type: 'progress', stage: 'verifying' },
        { type: 'success', emailMasked: 'j***@e***.com', plan: 'pro' },
      ]);
      const messages = received(account.profileDir);
      expect(messages.map((m) => m.method)).toEqual(['initialize', 'initialized', 'account/login/start', 'account/read']);
      expect(messages[2]?.params).toEqual({ type: 'chatgptDeviceCode' });
      const pid = readLog(account.profileDir).find((entry) => entry.kind === 'start')?.pid ?? 0;
      expect(await waitUntil(() => !isAlive(pid), 5000)).toBe(true);
    },
    TEST_TIMEOUT,
  );

  it(
    'keeps reading the account after a successful login until the app-server has reloaded auth',
    async () => {
      const { account, adapter } = setup();
      writeScenario(account, {
        responses: {
          'account/login/start': {
            ...START_OK,
            then: [{ method: 'account/login/completed', params: { loginId: 'login-1', success: true, error: null }, delayMs: 50 }],
          },
          // Right after the login the app-server still answers "no account" twice.
          'account/read': { sequence: [ACCOUNT_NONE, ACCOUNT_NONE, ACCOUNT_PRO] },
        },
      });
      const events: LoginEvent[] = [];
      await adapter.startLogin(account, (event) => events.push(event), signal());
      expect(events.at(-1)).toEqual({ type: 'success', emailMasked: 'j***@e***.com', plan: 'pro' });
      expect(received(account.profileDir).filter((m) => m.method === 'account/read')).toHaveLength(3);
    },
    TEST_TIMEOUT,
  );

  it(
    'trusts the completed login when the account view never catches up, instead of reporting a failure',
    async () => {
      const { account, adapter } = setup();
      writeScenario(account, {
        responses: {
          'account/login/start': {
            ...START_OK,
            then: [{ method: 'account/login/completed', params: { loginId: 'login-1', success: true, error: null }, delayMs: 50 }],
          },
          'account/read': ACCOUNT_NONE,
        },
      });
      const events: LoginEvent[] = [];
      await adapter.startLogin(account, (event) => events.push(event), signal());
      expect(events.at(-1)).toEqual({ type: 'success' });
      expect(received(account.profileDir).filter((m) => m.method === 'account/read')).toHaveLength(4);
    },
    TEST_TIMEOUT,
  );

  it(
    'waits for a cancelled identity read to exit before its own app-server starts in the same CODEX_HOME',
    async () => {
      const { account, adapter } = setup();
      // ignoreStdinClose: the first process only goes away through the tree kill, like a real one mid-initialisation.
      writeScenario(account, {
        ignoreStdinClose: true,
        responses: { 'account/read': { hang: true }, 'account/login/start': START_OK },
      });
      const identityAbort = new AbortController();
      const identity = adapter.getIdentity(account, identityAbort.signal).catch((error: unknown) => error);
      expect(await waitUntil(() => received(account.profileDir).some((m) => m.method === 'account/read'), 10_000)).toBe(true);

      // What the controller does when the user presses Login: cancel the fetch, start the login at once.
      identityAbort.abort();
      const loginAbort = new AbortController();
      const events: LoginEvent[] = [];
      const login = adapter.startLogin(account, (event) => events.push(event), loginAbort.signal);
      expect(await waitUntil(() => events.some((event) => event.type === 'device-code'), 15_000)).toBe(true);

      const starts = readLog(account.profileDir).filter((entry) => entry.kind === 'start');
      expect(starts).toHaveLength(2);
      expect(starts[1]?.alivePeers).toEqual([]);
      expect(await identity).toMatchObject({ code: 'cancelled' });

      loginAbort.abort();
      await login;
      expect(events.at(-1)).toEqual({ type: 'error', code: 'cancelled' });
    },
    TEST_TIMEOUT,
  );

  it(
    'fails fast without touching the profile dir when the CLI is missing',
    async () => {
      const { account, adapter } = setup({ resolveCli: () => ({ ok: false, code: 'cli-not-found' }) });
      const events: LoginEvent[] = [];
      await adapter.startLogin(account, (event) => events.push(event), signal());
      expect(events.at(-1)).toEqual({ type: 'error', code: 'cli-not-found' });
      expect(existsSync(account.profileDir)).toBe(false);
    },
  );

  it(
    'maps a failed completion to device-auth-disabled',
    async () => {
      const { account, adapter } = setup();
      writeScenario(account, {
        responses: {
          'account/login/start': {
            ...START_OK,
            then: [
              {
                method: 'account/login/completed',
                params: { loginId: 'login-1', success: false, error: 'Device code authorization is disabled for this workspace' },
              },
            ],
          },
        },
      });
      const events: LoginEvent[] = [];
      await adapter.startLogin(account, (event) => events.push(event), signal());
      expect(events.at(-1)).toEqual({ type: 'error', code: 'device-auth-disabled' });
    },
    TEST_TIMEOUT,
  );

  it(
    'cancels the pending login on abort',
    async () => {
      const { account, adapter } = setup();
      writeScenario(account, {
        responses: { 'account/login/start': START_OK, 'account/login/cancel': { result: { status: 'canceled' } } },
      });
      const controller = new AbortController();
      const events: LoginEvent[] = [];
      await adapter.startLogin(
        account,
        (event) => {
          events.push(event);
          if (event.type === 'device-code') setTimeout(() => controller.abort(), 100);
        },
        controller.signal,
      );
      expect(events.at(-1)).toEqual({ type: 'error', code: 'cancelled' });
      const cancel = received(account.profileDir).find((m) => m.method === 'account/login/cancel');
      expect(cancel?.params).toEqual({ loginId: 'login-1' });
    },
    TEST_TIMEOUT,
  );

  it(
    'times out and cancels when the user never completes sign-in',
    async () => {
      const { account, adapter } = setup({ timeouts: { loginMs: 400 } });
      writeScenario(account, {
        responses: { 'account/login/start': START_OK, 'account/login/cancel': { result: { status: 'canceled' } } },
      });
      const events: LoginEvent[] = [];
      await adapter.startLogin(account, (event) => events.push(event), signal());
      expect(events.at(-1)).toEqual({ type: 'error', code: 'timeout' });
      expect(received(account.profileDir).map((m) => m.method)).toContain('account/login/cancel');
    },
    TEST_TIMEOUT,
  );

  it(
    'rejects unsafe verification URLs and failed starts',
    async () => {
      const unsafe = setup();
      writeScenario(unsafe.account, {
        responses: { 'account/login/start': { result: { ...START_OK.result, verificationUrl: 'http://evil.example/' } } },
      });
      const unsafeEvents: LoginEvent[] = [];
      await unsafe.adapter.startLogin(unsafe.account, (event) => unsafeEvents.push(event), signal());
      expect(unsafeEvents).toEqual([
        { type: 'progress', stage: 'starting' },
        { type: 'error', code: 'protocol-error' },
      ]);

      const failed = setup();
      writeScenario(failed.account, {
        responses: { 'account/login/start': { error: { code: -32603, message: 'failed to request device code' } } },
      });
      const failedEvents: LoginEvent[] = [];
      await failed.adapter.startLogin(failed.account, (event) => failedEvents.push(event), signal());
      expect(failedEvents.at(-1)).toEqual({ type: 'error', code: 'login-failed' });
    },
    TEST_TIMEOUT,
  );
});

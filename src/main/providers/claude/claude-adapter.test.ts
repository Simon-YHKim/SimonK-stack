// Adapter + bridge installer against temp dirs only. homeDir is a temp folder: the real ~/.claude is never touched.

import { existsSync } from 'node:fs';
import { mkdir, mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import type { Account } from '../../../shared/types';
import type { ResolveResult } from '../../cli/resolve';
import type { RunOptions, RunResult, run as runProcess } from '../../cli/spawn';
import { nullLogger } from '../../log';
import { profileDirFor } from '../../paths';
import type { ProviderDeps } from '../types';
import { bridgeKeyFor } from './bridge-data';
import { claudeBridgeLayout } from './bridge-files';
import { resolveDefaultProfile } from './bridge-service';
import { createClaudeAdapter, type ClaudeAdapterOverrides } from './index';

const NOW = Date.UTC(2026, 8, 15, 3, 0, 0);
const RESOURCES = path.resolve('resources');

let root: string;
let deps: ProviderDeps;

beforeEach(async () => {
  root = await mkdtemp(path.join(os.tmpdir(), 'aiuw-claude-'));
  deps = {
    logger: nullLogger,
    now: () => NOW,
    appVersion: '0.0.0-test',
    localDataRoot: root,
    profilesRoot: path.join(root, 'profiles'),
    bridgeRoot: path.join(root, 'bridge'),
    resourcesDir: RESOURCES,
    homeDir: path.join(root, 'home'),
    env: {},
  };
});

afterEach(async () => {
  await rm(root, { recursive: true, force: true });
});

function account(id = 'acc1'): Account {
  return {
    id,
    provider: 'claude',
    label: 'Work',
    enabled: true,
    order: 0,
    profileDir: profileDirFor(deps.profilesRoot, 'claude', id),
    createdAt: NOW,
  };
}

const exe = (file: string): ResolveResult => ({ ok: true, command: { file, prefixArgs: [] }, kind: 'exe', source: file });

function overrides(options: { node?: boolean; claude?: boolean; run?: typeof runProcess } = {}): ClaudeAdapterOverrides {
  return {
    resolve: (name) => {
      if (name === 'node') return options.node === false ? { ok: false, code: 'cli-not-found' } : exe('C:\\nodejs\\node.exe');
      if (name === 'claude') return options.claude === false ? { ok: false, code: 'cli-not-found' } : exe('C:\\cli\\claude.exe');
      return { ok: false, code: 'cli-not-found' };
    },
    run: options.run ?? (() => Promise.reject(new Error('run not expected'))),
    spawnLongLived: () => Promise.reject(new Error('spawn not expected')),
  };
}

async function readJson(file: string): Promise<Record<string, unknown>> {
  return JSON.parse(await readFile(file, 'utf8')) as Record<string, unknown>;
}

const USER_SETTINGS = `{
  "model": "opus",
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh",
    "padding": 1
  },
  "permissions": {
    "allow": []
  }
}
`;

describe('default profile bridge', () => {
  it('backs up, wraps the existing command and restores it on uninstall', async () => {
    const claudeDir = path.join(deps.homeDir, '.claude');
    const settingsPath = path.join(claudeDir, 'settings.json');
    await mkdir(claudeDir, { recursive: true });
    await writeFile(settingsPath, USER_SETTINGS);
    const adapter = createClaudeAdapter(deps, overrides());
    const layout = claudeBridgeLayout(deps.bridgeRoot);
    const key = bridgeKeyFor(null);

    const installed = await adapter.bridge.installDefault(account());
    expect(installed).toEqual({ installed: true, wrapsExistingCommand: true, targetAccountId: 'acc1', lastDataAt: null });

    const files = await readdir(claudeDir);
    const backups = files.filter((name) => name.startsWith('settings.json.aiuw-backup-'));
    expect(backups).toEqual(['settings.json.aiuw-backup-20260915T030000000Z']);
    expect(await readFile(path.join(claudeDir, backups[0]!), 'utf8')).toBe(USER_SETTINGS);

    const settings = await readJson(settingsPath);
    expect(Object.keys(settings)).toEqual(['model', 'statusLine', 'permissions']);
    expect(settings.model).toBe('opus');
    expect(settings.permissions).toEqual({ allow: [] });
    const statusLine = settings.statusLine as Record<string, unknown>;
    expect(statusLine.padding).toBe(1);
    const expectedScript = path.join(layout.binDir, 'aiuw-claude-bridge.cjs').replace(/\\/g, '/');
    expect(statusLine.command).toBe(`node '${expectedScript}' --key ${key} --out '${layout.dir.replace(/\\/g, '/')}'`);
    expect(existsSync(path.join(layout.binDir, 'aiuw-claude-bridge.cjs'))).toBe(true);
    expect(existsSync(path.join(layout.binDir, 'aiuw-claude-bridge.ps1'))).toBe(true);
    expect(await readJson(layout.wrapPath(key))).toEqual({
      v: 1,
      previous: { present: true, value: { type: 'command', command: '~/.claude/statusline.sh', padding: 1 } },
    });

    const again = await adapter.bridge.installDefault(account());
    expect(again.installed).toBe(true);
    expect((await readdir(claudeDir)).filter((name) => name.includes('aiuw-backup'))).toHaveLength(1);

    const removed = await adapter.bridge.uninstallDefault();
    expect(removed).toEqual({ installed: false, wrapsExistingCommand: false, targetAccountId: null, lastDataAt: null });
    expect(await readFile(settingsPath, 'utf8')).toBe(USER_SETTINGS);
    expect(existsSync(layout.wrapPath(key))).toBe(false);
    expect(existsSync(layout.defaultStatePath)).toBe(false);
  });

  it('refuses to touch settings.json that is not valid JSON', async () => {
    const claudeDir = path.join(deps.homeDir, '.claude');
    const broken = '{ "model": "opus", }';
    await mkdir(claudeDir, { recursive: true });
    await writeFile(path.join(claudeDir, 'settings.json'), broken);
    const adapter = createClaudeAdapter(deps, overrides());

    const status = await adapter.bridge.installDefault(account());
    expect(status).toMatchObject({ installed: false, errorCode: 'parse-error' });
    expect(await readFile(path.join(claudeDir, 'settings.json'), 'utf8')).toBe(broken);
    expect(await readdir(claudeDir)).toEqual(['settings.json']);
    expect(await adapter.bridge.uninstallDefault()).toMatchObject({ errorCode: 'parse-error' });
    expect(await readFile(path.join(claudeDir, 'settings.json'), 'utf8')).toBe(broken);
  });

  it('creates settings.json when missing and removes only its own key on uninstall', async () => {
    const adapter = createClaudeAdapter(deps, overrides({ node: false }));
    const status = await adapter.bridge.installDefault(account());
    expect(status).toMatchObject({ installed: true, wrapsExistingCommand: false });
    const settingsPath = path.join(deps.homeDir, '.claude', 'settings.json');
    const command = ((await readJson(settingsPath)).statusLine as Record<string, unknown>).command as string;
    expect(command.startsWith('powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File ')).toBe(true);
    expect(command).toContain(`aiuw-claude-bridge.ps1' -Key ${bridgeKeyFor(null)} -Out '`);
    await adapter.bridge.uninstallDefault();
    expect(await readJson(settingsPath)).toEqual({});
  });

  it('never treats a widget profile as the default profile', () => {
    const inside = { ...deps, env: { CLAUDE_CONFIG_DIR: path.join(deps.profilesRoot, 'claude', 'acc1') } };
    expect(resolveDefaultProfile(inside)).toEqual({ configDir: path.join(deps.homeDir, '.claude'), key: bridgeKeyFor(null) });
    const custom = path.join(root, 'custom-claude');
    expect(resolveDefaultProfile({ ...deps, env: { CLAUDE_CONFIG_DIR: custom } })).toEqual({
      configDir: custom,
      key: bridgeKeyFor(custom),
    });
  });

  it('refuses non-claude targets', async () => {
    const adapter = createClaudeAdapter(deps, overrides());
    await expect(adapter.bridge.installDefault({ ...account(), provider: 'codex' })).rejects.toMatchObject({ code: 'internal' });
  });
});

describe('widget profile', () => {
  it('installs the bridge into the profile settings automatically and idempotently', async () => {
    const adapter = createClaudeAdapter(deps, overrides());
    const acc = account();
    await adapter.ensureProfileDir(acc);
    await adapter.ensureProfileDir(acc);
    const settings = await readJson(path.join(acc.profileDir, 'settings.json'));
    const command = (settings.statusLine as Record<string, unknown>).command as string;
    expect(command).toContain(`--key ${bridgeKeyFor(acc.profileDir)}`);
    expect(await readdir(acc.profileDir)).toEqual(['settings.json']);
  });

  it('reads usage from the bridge record of the profile and of the default profile target', async () => {
    const adapter = createClaudeAdapter(deps, overrides());
    const acc = account();
    const signal = new AbortController().signal;
    expect(await adapter.fetchUsage(acc, signal)).toMatchObject({
      state: 'unavailable',
      errorCode: 'bridge-no-data',
      windows: [],
    });

    const layout = claudeBridgeLayout(deps.bridgeRoot);
    const resetsAt = Math.floor((NOW + 3_600_000) / 1000);
    const writeRecord = async (key: string, used: number, capturedAt: number): Promise<void> => {
      await mkdir(layout.dir, { recursive: true });
      await writeFile(
        layout.recordPath(key),
        JSON.stringify({
          v: 1,
          configDirHash: key,
          seenAt: capturedAt,
          capturedAt,
          rate_limits: { five_hour: { used_percentage: used, resets_at: resetsAt, captured_at: capturedAt } },
        }),
      );
    };
    await writeRecord(bridgeKeyFor(acc.profileDir), 20, NOW - 60_000);
    expect(await adapter.fetchUsage(acc, signal)).toMatchObject({
      state: 'ok',
      windows: [{ kind: 'session', usedPercent: 20, resetsAt: resetsAt * 1000, windowMinutes: 300 }],
    });

    await writeRecord(bridgeKeyFor(null), 55, NOW - 1000);
    expect((await adapter.fetchUsage(acc, signal)).windows[0]?.usedPercent).toBe(20);
    await adapter.bridge.installDefault(acc);
    expect((await adapter.fetchUsage(acc, signal)).windows[0]?.usedPercent).toBe(55);
    expect((await adapter.bridge.status()).lastDataAt).toBe(NOW - 1000);

    await writeFile(layout.recordPath(bridgeKeyFor(acc.profileDir)), '{broken');
    await rm(layout.recordPath(bridgeKeyFor(null)));
    expect(await adapter.fetchUsage(acc, signal)).toMatchObject({ state: 'error', errorCode: 'parse-error' });
  });

  it('removes only profiles inside the claude profiles root', async () => {
    const adapter = createClaudeAdapter(deps, overrides());
    const acc = account();
    await adapter.ensureProfileDir(acc);
    await adapter.removeProfile(acc);
    expect(existsSync(acc.profileDir)).toBe(false);
    const outside = { ...acc, profileDir: path.join(root, 'home', '.claude') };
    await expect(adapter.removeProfile(outside)).rejects.toMatchObject({ code: 'internal' });
    await expect(adapter.removeProfile({ ...acc, profileDir: deps.profilesRoot })).rejects.toMatchObject({ code: 'internal' });
  });
});

describe('CLI calls', () => {
  function fakeRun(result: Partial<RunResult>, calls: Array<{ args: readonly string[]; options: RunOptions }>): typeof runProcess {
    return (_command, args, options) => {
      calls.push({ args, options });
      return Promise.resolve({
        exitCode: 0,
        signal: null,
        stdout: '',
        stderr: '',
        timedOut: false,
        aborted: false,
        truncated: false,
        durationMs: 1,
        ...result,
      });
    };
  }

  it('detects the CLI version with a widget-owned scratch config dir', async () => {
    const calls: Array<{ args: readonly string[]; options: RunOptions }> = [];
    const adapter = createClaudeAdapter(deps, overrides({ run: fakeRun({ stdout: '2.1.270 (Claude Code)\n' }, calls) }));
    expect(await adapter.detectCli()).toEqual({ found: true, version: '2.1.270', path: 'C:\\cli\\claude.exe' });
    expect(calls[0]?.args).toEqual(['--version']);
    expect(calls[0]?.options.env.set?.CLAUDE_CONFIG_DIR).toBe(path.join(root, 'tmp', 'claude-detect'));
  });

  it('falls back to %USERPROFILE%\\.local\\bin\\claude.exe and reports a missing CLI', async () => {
    const seen: string[] = [];
    const adapter = createClaudeAdapter(deps, {
      ...overrides(),
      resolve: (name) => {
        seen.push(name);
        return { ok: false, code: 'cli-not-found' };
      },
    });
    expect(await adapter.detectCli()).toEqual({ found: false, errorCode: 'cli-not-found' });
    expect(seen).toContain(path.join(deps.homeDir, '.local', 'bin', 'claude.exe'));
  });

  it('reads identity with CLAUDE_CONFIG_DIR set to the profile and scrubbed credentials', async () => {
    const calls: Array<{ args: readonly string[]; options: RunOptions }> = [];
    const stdout = JSON.stringify({ loggedIn: true, authMethod: 'claude.ai', email: 'person@example.com', subscriptionType: 'pro' });
    const adapter = createClaudeAdapter(
      { ...deps, env: { ANTHROPIC_API_KEY: 'x', PATH: 'C:\\Windows' } },
      overrides({ run: fakeRun({ stdout }, calls) }),
    );
    const acc = account();
    expect(await adapter.getIdentity(acc, new AbortController().signal)).toEqual({
      loggedIn: true,
      emailMasked: 'p***@e***.com',
      plan: 'pro',
    });
    expect(calls[0]?.args).toEqual(['auth', 'status', '--json']);
    expect(calls[0]?.options.cwd).toBe(acc.profileDir);
    expect(calls[0]?.options.env.set).toEqual({ CLAUDE_CONFIG_DIR: acc.profileDir });
    expect(calls[0]?.options.env.remove).toEqual(expect.arrayContaining(['ANTHROPIC_API_KEY', 'CLAUDE_CODE_OAUTH_TOKEN']));
    expect(calls[0]?.options.env.allow).not.toContain('ANTHROPIC_API_KEY');
  });

  it('maps identity failures to provider errors', async () => {
    const timedOut = createClaudeAdapter(deps, overrides({ run: fakeRun({ timedOut: true, exitCode: null }, []) }));
    await expect(timedOut.getIdentity(account(), new AbortController().signal)).rejects.toMatchObject({ code: 'timeout' });
    const garbage = createClaudeAdapter(deps, overrides({ run: fakeRun({ stdout: 'oops', exitCode: 1 }, []) }));
    await expect(garbage.getIdentity(account(), new AbortController().signal)).rejects.toMatchObject({ code: 'parse-error' });
    const missing = createClaudeAdapter(deps, overrides({ claude: false }));
    await expect(missing.getIdentity(account(), new AbortController().signal)).rejects.toMatchObject({ code: 'cli-not-found' });
  });

  it('emits cli-not-found at login when the CLI is missing', async () => {
    const adapter = createClaudeAdapter(deps, overrides({ claude: false }));
    const events: unknown[] = [];
    await adapter.startLogin(account(), (event) => events.push(event), new AbortController().signal);
    expect(events).toEqual([{ type: 'error', code: 'cli-not-found' }]);
  });
});

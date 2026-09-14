// Adapter + bridge installer against temp dirs only. homeDir is a temp folder: the real ~/.claude is never touched.

import { createHash } from 'node:crypto';
import { existsSync } from 'node:fs';
import { appendFile, copyFile, mkdir, mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
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
import {
  BRIDGE_SCRIPT_FILES,
  BRIDGE_SCRIPT_SHA256,
  claudeBridgeLayout,
  ensureBridgeScripts,
  type BridgeRuntime,
} from './bridge-files';
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

/** The default profile is keyed by its folder, whether it came from CLAUDE_CONFIG_DIR or the home default. */
const defaultKey = (): string => bridgeKeyFor(path.join(deps.homeDir, '.claude'));

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
    const key = defaultKey();

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
    expect(command).toContain(`aiuw-claude-bridge.ps1' -Key ${defaultKey()} -Out '`);
    await adapter.bridge.uninstallDefault();
    expect(await readJson(settingsPath)).toEqual({});
  });

  it('never treats a widget profile as the default profile', () => {
    const inside = { ...deps, env: { CLAUDE_CONFIG_DIR: path.join(deps.profilesRoot, 'claude', 'acc1') } };
    expect(resolveDefaultProfile(inside)).toEqual({ configDir: path.join(deps.homeDir, '.claude'), key: defaultKey() });
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

    await writeRecord(defaultKey(), 55, NOW - 1000);
    expect((await adapter.fetchUsage(acc, signal)).windows[0]?.usedPercent).toBe(20);
    await adapter.bridge.installDefault(acc);
    expect((await adapter.fetchUsage(acc, signal)).windows[0]?.usedPercent).toBe(55);
    expect((await adapter.bridge.status()).lastDataAt).toBe(NOW - 1000);

    await writeFile(layout.recordPath(bridgeKeyFor(acc.profileDir)), '{broken');
    await rm(layout.recordPath(defaultKey()));
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

describe('default profile bridge: recovery and hygiene', () => {
  const ORIGINAL_STATUS_LINE = { type: 'command', command: '~/.claude/statusline.sh', padding: 1 };
  const ORIGINAL_SIDECAR = JSON.stringify({ v: 1, previous: { present: true, value: ORIGINAL_STATUS_LINE } });

  /** settings.json with the bridge already installed under `key`, plus an optional raw sidecar. */
  async function installedUnderKey(key: string, sidecar: string | null): Promise<string> {
    const layout = claudeBridgeLayout(deps.bridgeRoot);
    const claudeDir = path.join(deps.homeDir, '.claude');
    const script = path.join(layout.binDir, 'aiuw-claude-bridge.cjs').replace(/\\/g, '/');
    const command = `node '${script}' --key ${key} --out '${layout.dir.replace(/\\/g, '/')}'`;
    await mkdir(claudeDir, { recursive: true });
    const settingsPath = path.join(claudeDir, 'settings.json');
    await writeFile(settingsPath, `${JSON.stringify({ model: 'opus', statusLine: { ...ORIGINAL_STATUS_LINE, command } }, null, 2)}\n`);
    await mkdir(layout.dir, { recursive: true });
    if (sidecar !== null) await writeFile(layout.wrapPath(key), sidecar);
    return settingsPath;
  }

  it('reinstalling over a bridge installed under another key keeps the original statusLine (SEC-01)', async () => {
    const legacyKey = bridgeKeyFor(null);
    const settingsPath = await installedUnderKey(legacyKey, ORIGINAL_SIDECAR);
    const adapter = createClaudeAdapter(deps, overrides());
    expect(await adapter.bridge.status()).toMatchObject({ installed: true, wrapsExistingCommand: true });

    expect(await adapter.bridge.installDefault(account())).toMatchObject({
      installed: true,
      wrapsExistingCommand: true,
      targetAccountId: 'acc1',
    });
    const layout = claudeBridgeLayout(deps.bridgeRoot);
    const command = ((await readJson(settingsPath)).statusLine as Record<string, unknown>).command as string;
    expect(command).toContain(`--key ${defaultKey()} `);
    expect(await readJson(layout.wrapPath(defaultKey()))).toEqual(JSON.parse(ORIGINAL_SIDECAR));
    // Re-pointing an installed bridge is not a takeover: no new copy of settings.json.
    expect((await readdir(path.dirname(settingsPath))).filter((name) => name.includes('aiuw-backup'))).toEqual([]);

    await adapter.bridge.uninstallDefault();
    expect(await readJson(settingsPath)).toEqual({ model: 'opus', statusLine: ORIGINAL_STATUS_LINE });
  });

  it('uninstalls a bridge installed under another key directly', async () => {
    const legacyKey = bridgeKeyFor(null);
    const settingsPath = await installedUnderKey(legacyKey, ORIGINAL_SIDECAR);
    const adapter = createClaudeAdapter(deps, overrides());
    expect(await adapter.bridge.uninstallDefault()).toMatchObject({ installed: false });
    expect(await readJson(settingsPath)).toEqual({ model: 'opus', statusLine: ORIGINAL_STATUS_LINE });
    expect(existsSync(claudeBridgeLayout(deps.bridgeRoot).wrapPath(legacyKey))).toBe(false);
  });

  it('refuses to reinstall or uninstall while the recorded original is unreadable (CR-12)', async () => {
    const broken = '{"v":1,"previous":';
    const settingsPath = await installedUnderKey(defaultKey(), broken);
    const before = await readFile(settingsPath, 'utf8');
    const adapter = createClaudeAdapter(deps, overrides());
    expect(await adapter.bridge.installDefault(account())).toMatchObject({ errorCode: 'parse-error' });
    expect(await adapter.bridge.uninstallDefault()).toMatchObject({ errorCode: 'parse-error' });
    expect(await readFile(settingsPath, 'utf8')).toBe(before);
    expect(await readFile(claudeBridgeLayout(deps.bridgeRoot).wrapPath(defaultKey()), 'utf8')).toBe(broken);
  });

  it('keeps only the newest three settings backups (SEC-02)', async () => {
    const claudeDir = path.join(deps.homeDir, '.claude');
    await mkdir(claudeDir, { recursive: true });
    await writeFile(path.join(claudeDir, 'settings.json'), USER_SETTINGS);
    const adapter = createClaudeAdapter(deps, overrides());
    for (let cycle = 0; cycle < 4; cycle += 1) {
      expect((await adapter.bridge.installDefault(account())).installed).toBe(true);
      expect((await adapter.bridge.uninstallDefault()).installed).toBe(false);
    }
    const base = 'settings.json.aiuw-backup-20260915T030000000Z';
    expect((await readdir(claudeDir)).filter((name) => name.includes('aiuw-backup')).sort()).toEqual([
      `${base}-5`,
      `${base}-6`,
      `${base}-7`,
    ]);
    expect(await readFile(path.join(claudeDir, 'settings.json'), 'utf8')).toBe(USER_SETTINGS);
  });
});

describe('bridge script integrity (SEC-04)', () => {
  it('embeds the hashes of the shipped scripts', async () => {
    for (const [runtime, name] of Object.entries(BRIDGE_SCRIPT_FILES) as [BridgeRuntime, string][]) {
      const bytes = await readFile(path.join(RESOURCES, 'claude-bridge', name));
      expect(BRIDGE_SCRIPT_SHA256?.[runtime]).toBe(createHash('sha256').update(bytes).digest('hex'));
    }
  });

  it('refuses modified scripts and installs nothing', async () => {
    const tampered = path.join(root, 'tampered-resources');
    await mkdir(path.join(tampered, 'claude-bridge'), { recursive: true });
    for (const name of Object.values(BRIDGE_SCRIPT_FILES)) {
      await copyFile(path.join(RESOURCES, 'claude-bridge', name), path.join(tampered, 'claude-bridge', name));
    }
    await appendFile(path.join(tampered, 'claude-bridge', BRIDGE_SCRIPT_FILES.node), '\n// changed\n');
    const layout = claudeBridgeLayout(deps.bridgeRoot);
    await expect(ensureBridgeScripts(tampered, layout)).rejects.toMatchObject({ code: 'internal' });
    expect(existsSync(path.join(layout.binDir, BRIDGE_SCRIPT_FILES.node))).toBe(false);

    const adapter = createClaudeAdapter({ ...deps, resourcesDir: tampered }, overrides());
    expect(await adapter.bridge.installDefault(account())).toMatchObject({ installed: false, errorCode: 'internal' });
    expect(existsSync(path.join(deps.homeDir, '.claude', 'settings.json'))).toBe(false);
    await expect(ensureBridgeScripts(RESOURCES, layout, null)).rejects.toMatchObject({ code: 'internal' });
  });
});

describe('profile removal', () => {
  it('aborts and waits for a running auth status before deleting the profile (CR-03)', async () => {
    const order: string[] = [];
    const aborted: RunResult = {
      exitCode: null,
      signal: null,
      stdout: '',
      stderr: '',
      timedOut: false,
      aborted: true,
      truncated: false,
      durationMs: 1,
    };
    let started = false;
    const slowRun: typeof runProcess = (_command, _args, options) =>
      new Promise<RunResult>((resolve) => {
        started = true;
        const exit = (): void => {
          // The child needs a moment to exit after the tree kill.
          setTimeout(() => {
            order.push('child-exited');
            resolve(aborted);
          }, 30);
        };
        if (options.signal?.aborted === true) exit();
        else options.signal?.addEventListener('abort', exit, { once: true });
      });
    const adapter = createClaudeAdapter(deps, overrides({ run: slowRun }));
    const acc = account();
    await adapter.ensureProfileDir(acc);
    const identity = adapter.getIdentity(acc, new AbortController().signal);
    const rejected = expect(identity).rejects.toMatchObject({ code: 'cancelled' });
    while (!started) await new Promise((resolve) => setTimeout(resolve, 1));
    await adapter.removeProfile(acc);
    order.push('removed');
    expect(order).toEqual(['child-exited', 'removed']);
    await rejected;
    expect(existsSync(acc.profileDir)).toBe(false);
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

import { mkdtemp, readFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';
import type { EventChannel, EventContract, PlacementPreview, ResizeWidgetRequest } from '../../shared/ipc';
import type { Settings } from '../../shared/settings';
import type {
  Account,
  AppStateSnapshot,
  LoginEvent,
  LoginEventMessage,
  ProviderId,
  ThemeTokens,
  UsageSnapshot,
} from '../../shared/types';
import { nullLogger } from '../log';
import { profileDirFor } from '../paths';
import { createAutostart, type LoginItemApi } from '../platform/autostart';
import { createProviderRegistry } from '../providers/registry';
import { ProviderError, type ClaudeProviderAdapter, type ProviderAdapter } from '../providers/types';
import { SOURCE_BY_PROVIDER } from '../scheduler';
import { openStore } from '../store';
import { createAppController, type WindowsPort } from './controller';
import { sanitizeSnapshot } from './sanitize';

const THEME: ThemeTokens = {
  scheme: 'light',
  taskbarScheme: 'dark',
  highContrast: false,
  accent: '#0078d4',
  reducedTransparency: false,
  effectiveMaterial: 'none',
};

interface FakeOptions {
  found?: boolean;
  loggedIn?: boolean;
  usage?: (account: Account, call: number) => UsageSnapshot;
  removeFails?: boolean;
  loginHosts?: string[];
}

interface Harness {
  controller: ReturnType<typeof createAppController>;
  windows: ReturnType<typeof fakeWindows>;
  calls: string[];
  logins: { emit: (event: LoginEvent) => void; signal: AbortSignal }[];
  opened: string[];
  writes: unknown[];
  profilesRoot: string;
  dir: string;
  store: Awaited<ReturnType<typeof openStore>>;
}

const dirs: string[] = [];
const controllers: Harness['controller'][] = [];

afterEach(async () => {
  for (const controller of controllers.splice(0)) controller.stop();
  await Promise.all(dirs.splice(0).map((dir) => rm(dir, { recursive: true, force: true })));
});

function okUsage(account: Account, at = Date.now()): UsageSnapshot {
  return {
    accountId: account.id,
    provider: account.provider,
    state: 'ok',
    windows: [{ kind: 'session', usedPercent: 42, resetsAt: at + 3_600_000, windowMinutes: 300 }],
    plan: 'pro',
    measuredAt: at,
    lastSuccessAt: at,
    source: SOURCE_BY_PROVIDER[account.provider],
  };
}

function fakeWindows() {
  const events: { channel: EventChannel; payload: unknown }[] = [];
  const applied: { settings: Settings; theme: ThemeTokens }[] = [];
  const resized: ResizeWidgetRequest[] = [];
  const previews: (PlacementPreview | null)[] = [];
  const port: WindowsPort = {
    togglePopup: () => undefined,
    showPopup: () => undefined,
    hidePopup: () => undefined,
    setPopupLock: () => undefined,
    resizeWidget: (size) => resized.push(size),
    previewPlacement: (patch) => previews.push(patch),
    showWidget: () => undefined,
    applySettings: (settings, theme) => applied.push({ settings, theme }),
    broadcast: <E extends EventChannel>(channel: E, payload: EventContract[E]) => events.push({ channel, payload }),
  };
  const states = (): AppStateSnapshot[] =>
    events.filter((e) => e.channel === 'state:changed').map((e) => e.payload as AppStateSnapshot);
  return { port, events, applied, resized, previews, states, last: () => states().at(-1) };
}

function fakeAdapter(id: ProviderId, calls: string[], logins: Harness['logins'], options: FakeOptions): ProviderAdapter {
  let usageCalls = 0;
  const adapter: ProviderAdapter = {
    id,
    loginUrlHosts: options.loginHosts ?? [],
    detectCli: () =>
      Promise.resolve(options.found === false ? { found: false, errorCode: 'cli-not-found' } : { found: true, version: '1.2.3', path: 'C:\\secret\\cli.exe' }),
    ensureProfileDir: (account) => {
      calls.push(`${id}:ensure:${account.id}:${account.profileDir}`);
      return Promise.resolve();
    },
    startLogin: (_account, emit, signal) =>
      new Promise<void>((resolve) => {
        logins.push({ emit, signal });
        signal.addEventListener('abort', () => resolve());
        const wrapped = (event: LoginEvent): void => {
          emit(event);
          if (event.type === 'success' || event.type === 'error') resolve();
        };
        logins[logins.length - 1]!.emit = wrapped;
      }),
    getIdentity: (account) => {
      calls.push(`${id}:identity:${account.id}`);
      if (options.loggedIn === false) return Promise.resolve({ loggedIn: false });
      // A raw address from a misbehaving adapter must still reach the renderer masked.
      const emailMasked = account.id === 'raw1' ? 'someone@example.com' : 'a***@b***.com';
      return Promise.resolve({ loggedIn: true, emailMasked, plan: 'pro' });
    },
    fetchUsage: (account) => {
      calls.push(`${id}:usage:${account.id}`);
      usageCalls += 1;
      return Promise.resolve(options.usage ? options.usage(account, usageCalls) : okUsage(account));
    },
    removeProfile: (account) => {
      calls.push(`${id}:remove:${account.id}`);
      return options.removeFails === true ? Promise.reject(new ProviderError('internal')) : Promise.resolve();
    },
  };
  return adapter;
}

async function until(condition: () => boolean, timeoutMs = 2_000): Promise<void> {
  const started = Date.now();
  while (!condition()) {
    if (Date.now() - started > timeoutMs) throw new Error('condition not met in time');
    await new Promise((resolve) => setTimeout(resolve, 5));
  }
}

async function setup(
  config: {
    accounts?: { id: string; provider: ProviderId; enabled?: boolean }[];
    adapters?: Partial<Record<ProviderId, FakeOptions>>;
    loginItems?: { name: string; enabled: boolean }[];
    autostartSupported?: boolean;
  } = {},
): Promise<Harness> {
  const dir = await mkdtemp(path.join(os.tmpdir(), 'aiuw-ctrl-'));
  dirs.push(dir);
  const profilesRoot = path.join(dir, 'local', 'profiles');
  const store = await openStore({ dir, profilesRoot, logger: nullLogger });
  if (config.accounts !== undefined) {
    await store.saveAccounts(
      config.accounts.map((a, order) => ({
        id: a.id,
        provider: a.provider,
        label: a.id.toUpperCase(),
        enabled: a.enabled ?? true,
        order,
        profileDir: profileDirFor(profilesRoot, a.provider, a.id),
        createdAt: 1,
      })),
    );
  }
  const calls: string[] = [];
  const logins: Harness['logins'] = [];
  const bridgeCalls: string[] = [];
  const registry = createProviderRegistry(
    {
      logger: nullLogger,
      now: Date.now,
      appVersion: '0.0.0-test',
      localDataRoot: path.join(dir, 'local'),
      profilesRoot,
      bridgeRoot: path.join(dir, 'local', 'bridge'),
      resourcesDir: dir,
      homeDir: dir,
      env: {},
    },
    {
      claude: (): ClaudeProviderAdapter => ({
        ...fakeAdapter('claude', calls, logins, config.adapters?.claude ?? {}),
        id: 'claude',
        bridge: {
          status: () => Promise.resolve({ installed: false, wrapsExistingCommand: false, targetAccountId: null, lastDataAt: null }),
          installDefault: (target) => {
            bridgeCalls.push(target.id);
            calls.push(`claude:bridge-install:${target.id}`);
            return Promise.resolve({ installed: true, wrapsExistingCommand: false, targetAccountId: target.id, lastDataAt: null });
          },
          uninstallDefault: () => Promise.reject(new ProviderError('bridge-not-installed')),
        },
      }),
      codex: () => fakeAdapter('codex', calls, logins, config.adapters?.codex ?? {}),
      grok: () => fakeAdapter('grok', calls, logins, config.adapters?.grok ?? {}),
      antigravity: () => fakeAdapter('antigravity', calls, logins, config.adapters?.antigravity ?? {}),
    },
  );
  const writes: unknown[] = [];
  const api: LoginItemApi = {
    setLoginItemSettings: (settings) => writes.push(settings),
    getLoginItemSettings: () => ({ openAtLogin: false, launchItems: config.loginItems ?? [] }),
  };
  const windows = fakeWindows();
  const opened: string[] = [];
  let counter = 0;
  const controller = createAppController({
    store,
    registry,
    windows: windows.port,
    theme: { current: () => THEME, setMaterial: (material) => ({ ...THEME, effectiveMaterial: material }) },
    autostart: createAutostart({ api, execPath: 'C:\\app.exe', supported: config.autostartSupported ?? false, logger: nullLogger }),
    openExternal: (url) => {
      opened.push(url);
      return Promise.resolve();
    },
    systemLocale: 'ko-KR',
    profilesRoot,
    logger: nullLogger,
    externalLinks: {},
    newAccountId: () => `n${(counter += 1)}`,
    scheduler: { manualMinIntervalMs: 0, random: () => 0.5, timeoutMs: 2_000 },
  });
  controllers.push(controller);
  return { controller, windows, calls, logins, opened, writes, profilesRoot, dir, store };
}

describe('sanitizeSnapshot', () => {
  const account: Account = { id: 'a1', provider: 'grok', label: 'x', enabled: true, order: 0, profileDir: 'C:\\p', createdAt: 1 };

  it('rebuilds snapshots from contract fields only and keeps unknown values null', () => {
    const dirty = {
      accountId: 'other',
      provider: 'codex',
      state: 'ok',
      windows: [
        { kind: 'weekly', usedPercent: null, resetsAt: 'soon', windowMinutes: 10_080, token: 'secret' },
        { kind: 'bogus', usedPercent: 140, resetsAt: 5, windowMinutes: -1, label: 'bucket\u202e' },
        'junk',
      ],
      measuredAt: 10,
      lastSuccessAt: 10,
      source: 'grok-acp',
      profileDir: 'C:\\Users\\x',
      accessToken: 'eyJ...',
    } as unknown as UsageSnapshot;
    expect(sanitizeSnapshot(account, dirty)).toEqual({
      accountId: 'a1',
      provider: 'grok',
      state: 'ok',
      windows: [
        { kind: 'weekly', usedPercent: null, resetsAt: null, windowMinutes: 10_080 },
        { kind: 'other', usedPercent: 100, resetsAt: 5, windowMinutes: null, label: 'bucket' },
      ],
      measuredAt: 10,
      lastSuccessAt: 10,
      source: 'grok-acp',
    });
  });

  it('turns unknown states into error with a code', () => {
    const bad = { state: 'ready', windows: 'nope', source: 'mock' } as unknown as UsageSnapshot;
    expect(sanitizeSnapshot(account, bad)).toMatchObject({ state: 'error', errorCode: 'internal', windows: [], source: 'grok-acp' });
  });
});

describe('app controller', () => {
  it('starts: detects CLIs, resolves identity, fetches usage and broadcasts renderer-safe state', async () => {
    const h = await setup({ accounts: [{ id: 'a1', provider: 'codex' }, { id: 'g1', provider: 'grok', enabled: false }] });
    await h.controller.start();
    await until(() => h.windows.last()?.usage.find((u) => u.accountId === 'a1')?.state === 'ok');
    const state = h.windows.last()!;
    expect(state.locale).toBe('ko');
    expect(state.accounts).toEqual([
      { id: 'a1', provider: 'codex', label: 'A1', enabled: true, order: 0, loginState: 'logged-in', emailMasked: 'a***@b***.com', plan: 'pro' },
      { id: 'g1', provider: 'grok', label: 'G1', enabled: false, order: 1, loginState: 'unknown' },
    ]);
    expect(state.cli.codex).toEqual({ state: 'found', version: '1.2.3' });
    expect(JSON.stringify(state)).not.toMatch(/profile|secret|cli\.exe/i);
    expect(h.calls.filter((c) => c.includes(':usage:'))).toEqual(['codex:usage:a1']);
    expect(h.calls).toContain(`codex:ensure:a1:${path.resolve(h.profilesRoot, 'codex', 'a1')}`);
  });

  it('re-masks identity strings before they reach the renderer', async () => {
    const h = await setup({ accounts: [{ id: 'raw1', provider: 'grok' }] });
    await h.controller.start();
    await until(() => h.windows.last()?.accounts[0]?.loginState === 'logged-in');
    expect(h.windows.last()?.accounts[0]?.emailMasked).toBe('s***@e***.com');
    expect(JSON.stringify(h.windows.states())).not.toContain('someone@example.com');
  });

  it('reports a missing CLI without spawning fetches and refuses login', async () => {
    const h = await setup({ accounts: [{ id: 'a1', provider: 'codex' }], adapters: { codex: { found: false } } });
    await h.controller.start();
    await until(() => h.windows.last()?.usage[0]?.state === 'unavailable');
    expect(h.windows.last()?.usage[0]).toMatchObject({ errorCode: 'cli-not-found', windows: [] });
    expect(h.windows.last()?.accounts[0]?.loginState).toBe('cli-missing');
    expect(h.calls.some((c) => c.includes(':usage:') || c.includes(':identity:'))).toBe(false);
    expect(() => h.controller.startLogin('a1')).toThrow(expect.objectContaining({ code: 'conflict', detail: 'cli-not-found' }));
  });

  it('keeps the last measured values when a fetch fails (no fake numbers)', async () => {
    const h = await setup({
      accounts: [{ id: 'a1', provider: 'grok' }],
      adapters: {
        grok: {
          usage: (account, call) =>
            call === 1
              ? okUsage(account)
              : { ...okUsage(account), state: 'error', windows: [], measuredAt: null, lastSuccessAt: null, errorCode: 'network' },
        },
      },
    });
    await h.controller.start();
    await until(() => h.windows.last()?.usage[0]?.state === 'ok');
    await h.controller.refreshNow('a1');
    await until(() => h.windows.last()?.usage[0]?.state === 'error');
    const failed = h.windows.last()!.usage[0]!;
    expect(failed.errorCode).toBe('network');
    expect(failed.windows[0]?.usedPercent).toBe(42);
    expect(failed.lastSuccessAt).not.toBeNull();
  });

  it('skips usage for logged-out accounts and marks old successes stale', async () => {
    const h = await setup({
      accounts: [{ id: 'c1', provider: 'claude' }, { id: 'x1', provider: 'codex' }],
      adapters: {
        claude: { loggedIn: false },
        codex: { usage: (account) => okUsage(account, Date.now() - 10 * 60_000) },
      },
    });
    await h.controller.start();
    await until(() => h.windows.last()?.usage.length === 2 && h.windows.last()!.usage.every((u) => u.state !== 'loading'));
    expect(h.windows.last()?.usage[0]).toMatchObject({ accountId: 'c1', state: 'logged-out', errorCode: 'not-logged-in' });
    expect(h.calls).not.toContain('claude:usage:c1');
    h.controller.markStale();
    await until(() => h.windows.last()?.usage[1]?.state === 'stale');
  });

  it('adds and removes accounts through the adapters, persisting without profile paths', async () => {
    const h = await setup();
    await h.controller.start();
    const dto = await h.controller.addAccount('grok', 'Home');
    expect(dto).toEqual({ id: 'n1', provider: 'grok', label: 'Home', enabled: true, order: 0, loginState: 'unknown' });
    expect(h.calls).toContain(`grok:ensure:n1:${path.resolve(h.profilesRoot, 'grok', 'n1')}`);
    expect(await readFile(path.join(h.dir, 'accounts.json'), 'utf8')).not.toContain('profile');
    await until(() => h.windows.last()?.usage[0]?.state === 'ok');

    await h.controller.removeAccount('n1');
    expect(h.calls).toContain('grok:remove:n1');
    await until(() => h.windows.last()?.accounts.length === 0);
    expect(h.windows.last()?.usage).toEqual([]);
    await expect(h.controller.removeAccount('n1')).rejects.toMatchObject({ code: 'not-found' });
  });

  it('accepts one Antigravity account only, while other providers stay unlimited', async () => {
    const h = await setup();
    await h.controller.start();
    await h.controller.addAccount('antigravity', 'Main');
    await expect(h.controller.addAccount('antigravity', 'Second')).rejects.toMatchObject({ code: 'conflict' });
    expect(h.calls.filter((call) => call.startsWith('antigravity:ensure:'))).toHaveLength(1);
    await h.controller.addAccount('grok', 'G1');
    await h.controller.addAccount('grok', 'G2');
    expect(h.store.getAccounts().map((a) => a.provider)).toEqual(['antigravity', 'grok', 'grok']);

    // Removing it frees the slot again.
    const [first] = h.store.getAccounts();
    await h.controller.removeAccount(first!.id);
    await expect(h.controller.addAccount('antigravity', 'Again')).resolves.toMatchObject({ provider: 'antigravity' });
  });

  it('keeps an account when its profile cannot be removed', async () => {
    const h = await setup({ accounts: [{ id: 'a1', provider: 'codex' }], adapters: { codex: { removeFails: true } } });
    await h.controller.start();
    await expect(h.controller.removeAccount('a1')).rejects.toMatchObject({ code: 'internal', detail: 'internal' });
    expect(h.controller.listAccounts().map((a) => a.id)).toEqual(['a1']);
  });

  it('renames, toggles and reorders accounts (within the same provider)', async () => {
    const h = await setup({
      accounts: [{ id: 'a1', provider: 'codex' }, { id: 'a2', provider: 'grok' }, { id: 'a3', provider: 'codex' }],
    });
    await h.controller.start();
    expect((await h.controller.reorderAccount('a2', 'up')).map((a) => a.id)).toEqual(['a1', 'a2', 'a3']);
    expect((await h.controller.reorderAccount('a3', 'up')).map((a) => a.id)).toEqual(['a3', 'a2', 'a1']);
    expect((await h.controller.renameAccount('a1', 'Renamed')).label).toBe('Renamed');
    expect((await h.controller.toggleAccount('a2', false)).enabled).toBe(false);
    await expect(h.controller.reorderAccount('zz', 'up')).rejects.toMatchObject({ code: 'not-found' });
  });

  it('runs a login session, opens only its URLs and updates identity on success', async () => {
    const h = await setup({ accounts: [{ id: 'a1', provider: 'codex' }], adapters: { codex: { loginHosts: ['openai.com'] } } });
    await h.controller.start();
    const { sessionId } = h.controller.startLogin('a1');
    await until(() => h.windows.last()?.accounts[0]?.loginState === 'logging-in');
    await expect(Promise.resolve().then(() => h.controller.startLogin('a1'))).rejects.toMatchObject({ code: 'busy' });

    const login = h.logins[0]!;
    login.emit({ type: 'device-code', userCode: 'WXYZ-1234', verificationUrl: 'https://auth.openai.com/codex/device' });
    login.emit({ type: 'url', url: 'https://evil.test/phish' });
    const loginEvents = h.windows.events.filter((e) => e.channel === 'login:event').map((e) => e.payload as LoginEventMessage);
    expect(loginEvents.map((m) => [m.sessionId, m.event.type])).toEqual([
      [sessionId, 'device-code'],
      [sessionId, 'url'],
    ]);
    await h.controller.openExternal({ kind: 'login', sessionId, url: 'https://auth.openai.com/codex/device' });
    await expect(h.controller.openExternal({ kind: 'login', sessionId, url: 'https://evil.test/phish' })).rejects.toMatchObject({
      code: 'invalid-request',
    });
    await expect(h.controller.openExternal({ kind: 'link', key: 'codex-cli-install' })).rejects.toMatchObject({ code: 'not-found' });
    expect(h.opened).toEqual(['https://auth.openai.com/codex/device']);

    login.emit({ type: 'success', emailMasked: 'n***@e***.com', plan: 'plus' });
    await until(() => h.windows.last()?.accounts[0]?.loginState === 'logged-in');
    // Identity is re-read from the CLI after login; the adapter stays authoritative.
    await until(() => h.calls.filter((c) => c === 'codex:identity:a1').length >= 2);
    await expect(h.controller.openExternal({ kind: 'login', sessionId, url: 'https://auth.openai.com/codex/device' })).rejects.toMatchObject({
      code: 'invalid-request',
    });
  });

  it('applies settings: persistence, autostart registration, locale, windows and material', async () => {
    const h = await setup({ autostartSupported: true });
    await h.controller.start();
    const next = await h.controller.updateSettings({ openAtLogin: true, language: 'en', material: 'mica', offsetPx: 40 });
    expect(next).toMatchObject({ openAtLogin: true, language: 'en', material: 'mica', offsetPx: 40 });
    expect(h.writes).toEqual([
      { openAtLogin: true, path: 'C:\\app.exe', args: ['--autostart'], name: 'AIUsageWidgetV2', enabled: true },
    ]);
    expect(h.windows.applied.at(-1)?.settings.offsetPx).toBe(40);
    expect(h.windows.applied.at(-1)?.theme.effectiveMaterial).toBe('mica');
    await until(() => h.windows.last()?.locale === 'en');
    const saved = JSON.parse(await readFile(path.join(h.dir, 'settings.json'), 'utf8')) as Settings;
    expect(saved.offsetPx).toBe(40);

    h.controller.resizeWidget({ width: 5000, height: 1 });
    expect(h.windows.resized).toEqual([{ width: 3840, height: 24 }]);

    h.controller.previewPlacement({ offsetPx: 20 });
    h.controller.previewPlacement(null);
    expect(h.windows.previews).toEqual([{ offsetPx: 20 }, null]);
    h.controller.setEffectivePlacementMode('floating');
    await until(() => h.windows.last()?.effectivePlacementMode === 'floating');
  });

  it('serializes settings updates so back-to-back changes all persist (RR-02)', async () => {
    const h = await setup({ autostartSupported: true });
    await h.controller.start();
    const [first, second] = await Promise.all([
      h.controller.updateSettings({ openAtLogin: true }),
      h.controller.updateSettings({ language: 'en' }),
    ]);
    expect(first).toMatchObject({ openAtLogin: true, language: 'auto' });
    expect(second).toMatchObject({ openAtLogin: true, language: 'en' });
    expect(h.controller.getSettings()).toMatchObject({ openAtLogin: true, language: 'en' });
    expect(h.writes).toHaveLength(1);
    const saved = JSON.parse(await readFile(path.join(h.dir, 'settings.json'), 'utf8')) as Settings;
    expect(saved).toMatchObject({ openAtLogin: true, language: 'en' });
  });

  it('rolls the autostart registration back when settings cannot be saved', async () => {
    const h = await setup({ autostartSupported: true });
    await h.controller.start();
    const save = h.store.saveSettings.bind(h.store);
    h.store.saveSettings = () => Promise.reject(new Error('disk full'));
    await expect(h.controller.updateSettings({ openAtLogin: true })).rejects.toMatchObject({ code: 'internal' });
    expect(h.writes.map((w) => (w as { openAtLogin: boolean }).openAtLogin)).toEqual([true, false]);
    expect(h.controller.getSettings().openAtLogin).toBe(false);
    // The queue keeps working after a failed change.
    h.store.saveSettings = save;
    await expect(h.controller.updateSettings({ language: 'en' })).resolves.toMatchObject({ language: 'en', openAtLogin: false });
  });

  it('keeps a confirmed logged-out account logged-out even when usage would read ok (CR-02)', async () => {
    const h = await setup({ accounts: [{ id: 'c1', provider: 'claude' }], adapters: { claude: { loggedIn: false } } });
    await h.controller.start();
    await until(() => h.windows.last()?.usage[0]?.state === 'logged-out');
    for (let round = 2; round <= 4; round += 1) {
      await h.controller.refreshNow('c1');
      await until(() => h.calls.filter((c) => c === 'claude:identity:c1').length >= round);
      await until(() => h.windows.last()?.refresh.inFlight === false);
    }
    expect(h.calls).not.toContain('claude:usage:c1');
    expect(h.windows.states().some((s) => s.usage[0]?.state === 'ok')).toBe(false);
    expect(h.windows.last()?.usage[0]?.state).toBe('logged-out');
  });

  it('serializes account changes so concurrent adds and renames all persist (CR-04)', async () => {
    const h = await setup({ accounts: [{ id: 'a1', provider: 'codex' }] });
    await h.controller.start();
    await Promise.all([
      h.controller.addAccount('grok', 'G'),
      h.controller.addAccount('claude', 'C'),
      h.controller.renameAccount('a1', 'Renamed'),
    ]);
    expect(h.controller.listAccounts().map((a) => [a.id, a.label, a.order])).toEqual([
      ['a1', 'Renamed', 0],
      ['n1', 'G', 1],
      ['n2', 'C', 2],
    ]);
    const saved = JSON.parse(await readFile(path.join(h.dir, 'accounts.json'), 'utf8')) as { accounts: { id: string }[] };
    expect(saved.accounts.map((a) => a.id)).toEqual(['a1', 'n1', 'n2']);
  });

  it('does not start the scheduler when stopped while start() is pending (CR-05)', async () => {
    const h = await setup({ accounts: [{ id: 'a1', provider: 'codex' }] });
    const starting = h.controller.start();
    h.controller.stop();
    await starting;
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(h.calls.filter((c) => c.includes(':usage:') || c.includes(':identity:'))).toEqual([]);
  });

  it('re-detects a CLI on request and reports detection in progress (P-06)', async () => {
    const h = await setup({ adapters: { grok: { found: false } } });
    await h.controller.start();
    await until(() => h.windows.last()?.cli.grok.state === 'missing');
    const before = h.windows.states().length;
    h.controller.redetectCli('grok');
    await until(() => h.windows.states().length > before + 1);
    expect(h.windows.states().slice(before).map((s) => s.cli.grok.state)).toEqual(['unknown', 'missing']);
    expect(h.windows.last()?.cli.codex.state).toBe('found');
  });

  it('adopts an externally changed autostart registration without re-registering', async () => {
    const h = await setup({ autostartSupported: true, loginItems: [{ name: 'AIUsageWidgetV2', enabled: true }] });
    await h.controller.start();
    expect(h.controller.getSettings().openAtLogin).toBe(true);
    expect(h.writes).toEqual([]);
  });

  it('routes the Claude bridge only for Claude accounts', async () => {
    const h = await setup({ accounts: [{ id: 'c1', provider: 'claude' }, { id: 'x1', provider: 'codex' }] });
    await h.controller.start();
    await expect(h.controller.bridgeInstallDefault('x1')).rejects.toMatchObject({ code: 'invalid-request' });
    await expect(h.controller.bridgeInstallDefault('c1')).resolves.toMatchObject({ installed: true, targetAccountId: 'c1' });
    await expect(h.controller.bridgeUninstallDefault()).rejects.toMatchObject({ code: 'internal', detail: 'bridge-not-installed' });
  });
});

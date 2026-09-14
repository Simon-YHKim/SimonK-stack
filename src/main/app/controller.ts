import { randomBytes } from 'node:crypto';
import { resolveLocale } from '../../shared/i18n';
import {
  clampWidgetSize,
  type EventChannel,
  type EventContract,
  type ExternalLinkKey,
  type OpenExternalRequest,
  type RendererReadyRequest,
  type ResizeWidgetRequest,
} from '../../shared/ipc';
import { applySettingsPatch, type Material, type Settings } from '../../shared/settings';
import {
  PROVIDER_IDS,
  toAccountDTO,
  type Account,
  type AccountDTO,
  type AccountIdentityInfo,
  type AppStateSnapshot,
  type ClaudeBridgeStatus,
  type CliStatusDTO,
  type ErrorCode,
  type Locale,
  type LoginState,
  type PopupTab,
  type ProviderId,
  type RefreshStatus,
  type ThemeTokens,
  type UsageSnapshot,
} from '../../shared/types';
import { maskSecrets } from '../../shared/mask';
import { applyFetchFailure, createEmptySnapshot, staleAfterMs } from '../../shared/usage';
import { IpcHandlerError } from '../ipc/dispatch';
import type { Logger } from '../log';
import { createLoginManager, type LoginManager } from '../login';
import { profileDirFor } from '../paths';
import type { Autostart } from '../platform/autostart';
import type { ProviderRegistry } from '../providers/registry';
import { ProviderError, type CliInfo, type ProviderAdapter } from '../providers/types';
import { SOURCE_BY_PROVIDER, createScheduler, type FetchOutcome, type Scheduler, type SchedulerOptions } from '../scheduler';
import type { AppStore } from '../store';
import { moveAccount, renumberAccounts } from '../store/accounts';
import { sanitizeSnapshot } from './sanitize';

export const MAX_ACCOUNTS = 24;
export const CLI_DETECT_TIMEOUT_MS = 15_000;
export const REDETECT_MIN_INTERVAL_MS = 30_000;
export const IDENTITY_MAX_AGE_MS = 30 * 60_000;
export const STALE_CHECK_INTERVAL_MS = 30_000;

export interface WindowsPort {
  togglePopup(): void;
  showPopup(tab: PopupTab | null, focus: boolean): void;
  hidePopup(): void;
  setPopupLock(locked: boolean): void;
  resizeWidget(size: ResizeWidgetRequest): void;
  showWidget(): void;
  applySettings(settings: Settings, theme: ThemeTokens): void;
  broadcast<E extends EventChannel>(channel: E, payload: EventContract[E]): void;
}

export interface ThemePort {
  current(): ThemeTokens;
  setMaterial(material: Material): ThemeTokens;
}

export interface AppControllerDeps {
  store: AppStore;
  registry: ProviderRegistry;
  windows: WindowsPort;
  theme: ThemePort;
  autostart: Autostart;
  openExternal(url: string): Promise<void>;
  systemLocale: string;
  profilesRoot: string;
  logger: Logger;
  externalLinks: Readonly<Partial<Record<ExternalLinkKey, string>>>;
  now?: () => number;
  newAccountId?: () => string;
  onRendererReady?(request: RendererReadyRequest): void;
  onSnapshot?(snapshot: AppStateSnapshot): void;
  scheduler?: Partial<Pick<SchedulerOptions, 'timeoutMs' | 'manualMinIntervalMs' | 'resumeDelayMs' | 'random'>>;
  loginTimeoutMs?: number;
}

export interface CliSummary {
  found: boolean;
  version?: string;
  errorCode?: ErrorCode;
}

export type AppController = ReturnType<typeof createAppController>;

function errorCodeOf(error: unknown): ErrorCode {
  return error instanceof ProviderError ? error.code : 'internal';
}

function adapterLoginHosts(adapter: ProviderAdapter): readonly string[] | null {
  // Optional adapter extension until the contract carries it (see contract change requests).
  const hosts = (adapter as { loginUrlHosts?: unknown }).loginUrlHosts;
  return Array.isArray(hosts) && hosts.length > 0 && hosts.every((h) => typeof h === 'string') ? hosts : null;
}

export function createAppController(deps: AppControllerDeps) {
  const { store, registry, windows, logger } = deps;
  const now = deps.now ?? Date.now;
  const newAccountId = deps.newAccountId ?? (() => randomBytes(9).toString('base64url'));

  let settings: Settings = store.getSettings();
  let locale: Locale = resolveLocale(settings.language, deps.systemLocale);
  let theme: ThemeTokens = deps.theme.current();
  let refresh: RefreshStatus = { inFlight: false, accountIds: [], lastRunAt: null, nextRunAt: null };
  const usage = new Map<string, UsageSnapshot>();
  const identities = new Map<string, AccountIdentityInfo & { at: number }>();
  const needsIdentity = new Set<string>();
  const cli: Record<ProviderId, CliInfo | null> = { claude: null, codex: null, grok: null };
  const lastDetectAt: Record<ProviderId, number> = { claude: 0, codex: 0, grok: 0 };
  let broadcastPending = false;
  let stopped = false;
  let staleTimer: ReturnType<typeof setInterval> | null = null;

  // -------------------------------------------------------------------------
  // Snapshot + broadcast

  const loginStateFor = (account: Account): LoginState => {
    if (login.isActive(account.id)) return 'logging-in';
    const info = cli[account.provider];
    if (info !== null && !info.found) return 'cli-missing';
    return identities.get(account.id)?.loginState ?? 'unknown';
  };

  const dtoFor = (account: Account): AccountDTO => {
    const identity = identities.get(account.id);
    const info: AccountIdentityInfo = { loginState: loginStateFor(account) };
    if (identity?.emailMasked !== undefined) info.emailMasked = identity.emailMasked;
    if (identity?.plan !== undefined) info.plan = identity.plan;
    return toAccountDTO(account, info);
  };

  const cliDto = (provider: ProviderId): CliStatusDTO => {
    const info = cli[provider];
    if (info === null) return { state: 'unknown' };
    if (!info.found) return { state: 'missing' };
    return info.version === undefined ? { state: 'found' } : { state: 'found', version: info.version };
  };

  const snapshot = (): AppStateSnapshot => {
    const accounts = store.getAccounts();
    return {
      locale,
      settings: { ...settings },
      accounts: accounts.map(dtoFor),
      usage: accounts
        .map((account) => usage.get(account.id))
        .filter((entry): entry is UsageSnapshot => entry !== undefined)
        .map((entry) => ({ ...entry, windows: entry.windows.map((w) => ({ ...w })) })),
      refresh: { ...refresh, accountIds: [...refresh.accountIds] },
      theme: { ...theme },
      cli: { claude: cliDto('claude'), codex: cliDto('codex'), grok: cliDto('grok') },
    };
  };

  /** Coalesces changes made in the same tick into one state:changed (V1-39). */
  const scheduleBroadcast = (): void => {
    if (broadcastPending || stopped) return;
    broadcastPending = true;
    queueMicrotask(() => {
      broadcastPending = false;
      if (stopped) return;
      const snap = snapshot();
      windows.broadcast('state:changed', snap);
      deps.onSnapshot?.(snap);
    });
  };

  // -------------------------------------------------------------------------
  // CLI detection, identity, usage

  const detectProvider = async (provider: ProviderId): Promise<void> => {
    lastDetectAt[provider] = now();
    try {
      const info = await registry.get(provider).detectCli(AbortSignal.timeout(CLI_DETECT_TIMEOUT_MS));
      const clean: CliInfo = { found: info.found === true };
      if (typeof info.version === 'string') clean.version = info.version.slice(0, 64);
      if (info.errorCode !== undefined) clean.errorCode = info.errorCode;
      cli[provider] = clean;
    } catch (error) {
      logger.warn('detectCli failed', { provider, error });
      cli[provider] = { found: false, errorCode: errorCodeOf(error) };
    }
  };

  const redetectMissing = async (providers: readonly ProviderId[]): Promise<void> => {
    const due = providers.filter(
      (provider) => cli[provider]?.found !== true && now() - lastDetectAt[provider] >= REDETECT_MIN_INTERVAL_MS,
    );
    if (due.length === 0) return;
    await Promise.all(due.map(detectProvider));
    scheduleBroadcast();
  };

  /** Adapters already mask; masking again is a cheap guard against a raw address slipping through. */
  const setIdentity = (accountId: string, info: AccountIdentityInfo): void => {
    const safe: AccountIdentityInfo = { loginState: info.loginState };
    if (typeof info.emailMasked === 'string') safe.emailMasked = maskSecrets(info.emailMasked).slice(0, 128);
    if (typeof info.plan === 'string') safe.plan = maskSecrets(info.plan).slice(0, 64);
    identities.set(accountId, { ...safe, at: now() });
  };

  const fetchFor = async (account: Account, signal: AbortSignal): Promise<FetchOutcome> => {
    const info = cli[account.provider];
    const base = { accountId: account.id, provider: account.provider, source: SOURCE_BY_PROVIDER[account.provider] };
    // A running login owns the profile; never start a second CLI process against it.
    if (login.isActive(account.id)) {
      return { snapshot: createEmptySnapshot({ ...base, state: 'loading' }), skipped: true };
    }
    if (info !== null && !info.found) {
      return { snapshot: createEmptySnapshot({ ...base, state: 'unavailable', errorCode: info.errorCode ?? 'cli-not-found' }) };
    }
    const adapter = registry.get(account.provider);
    const identity = identities.get(account.id);
    // Identity runs inside the scheduler slot so a provider never has two CLI processes at once.
    if (needsIdentity.has(account.id) || identity === undefined || now() - identity.at > IDENTITY_MAX_AGE_MS) {
      try {
        const result = await adapter.getIdentity({ ...account }, signal);
        const next: AccountIdentityInfo = { loginState: result.loggedIn ? 'logged-in' : 'logged-out' };
        if (result.emailMasked !== undefined) next.emailMasked = result.emailMasked;
        if (result.plan !== undefined) next.plan = result.plan;
        setIdentity(account.id, next);
        needsIdentity.delete(account.id);
        scheduleBroadcast();
      } catch (error) {
        if (signal.aborted) throw error;
        logger.warn('getIdentity failed', { provider: account.provider, error });
        setIdentity(account.id, { loginState: 'unknown' });
      }
      if (identities.get(account.id)?.loginState === 'logged-out') {
        return { snapshot: createEmptySnapshot({ ...base, state: 'logged-out', errorCode: 'not-logged-in' }) };
      }
    }
    return { snapshot: await adapter.fetchUsage({ ...account }, signal) };
  };

  const onResult = (account: Account, raw: UsageSnapshot): void => {
    if (store.getAccount(account.id) === undefined) return;
    const clean = sanitizeSnapshot(account, raw);
    const merged = clean.state === 'error' ? applyFetchFailure(usage.get(account.id), clean) : clean;
    usage.set(account.id, merged);
    const identity = identities.get(account.id);
    if (clean.state === 'logged-out' && identity?.loginState !== 'logged-out') {
      setIdentity(account.id, { loginState: 'logged-out' });
    } else if (clean.state === 'ok' && identity?.loginState !== 'logged-in') {
      needsIdentity.add(account.id);
    }
    scheduleBroadcast();
  };

  const markStale = (): void => {
    const threshold = staleAfterMs(settings.refreshIntervalSec);
    const at = now();
    let changed = false;
    for (const [id, entry] of usage) {
      if (entry.state === 'ok' && entry.lastSuccessAt !== null && at - entry.lastSuccessAt > threshold) {
        usage.set(id, { ...entry, state: 'stale' });
        changed = true;
      }
    }
    if (changed) scheduleBroadcast();
  };

  const scheduler: Scheduler = createScheduler({
    listAccounts: () => store.getAccounts(),
    intervalSec: () => settings.refreshIntervalSec,
    fetch: fetchFor,
    onResult,
    onStatus: (status) => {
      refresh = status;
      scheduleBroadcast();
    },
    logger: logger.child('scheduler'),
    now,
    ...deps.scheduler,
  });

  const login: LoginManager = createLoginManager({
    getAccount: (id) => store.getAccount(id),
    adapterFor: (provider) => registry.get(provider),
    emit: (message) => windows.broadcast('login:event', message),
    onStarted: () => scheduleBroadcast(),
    onSettled: ({ accountId, event }) => {
      if (event.type === 'success') {
        const info: AccountIdentityInfo = { loginState: 'logged-in' };
        if (event.emailMasked !== undefined) info.emailMasked = event.emailMasked;
        if (event.plan !== undefined) info.plan = event.plan;
        setIdentity(accountId, info);
        needsIdentity.add(accountId);
        void scheduler.refreshNow(accountId);
      }
      scheduleBroadcast();
    },
    allowedHosts: (provider) => adapterLoginHosts(registry.get(provider)),
    logger: logger.child('login'),
    now,
    ...(deps.loginTimeoutMs === undefined ? {} : { timeoutMs: deps.loginTimeoutMs }),
  });

  // -------------------------------------------------------------------------
  // Helpers for handlers

  const requireAccount = (accountId: string): Account => {
    const account = store.getAccount(accountId);
    if (account === undefined) throw new IpcHandlerError('not-found');
    return account;
  };

  const persistAccounts = async (next: readonly Account[]): Promise<void> => {
    try {
      await store.saveAccounts(next);
    } catch (error) {
      logger.error('saving accounts failed', { error });
      throw new IpcHandlerError('internal');
    }
  };

  const applySettings = async (next: Settings): Promise<Settings> => {
    const previous = settings;
    if (next.openAtLogin !== previous.openAtLogin) {
      try {
        deps.autostart.setEnabled(next.openAtLogin);
      } catch (error) {
        logger.error('autostart registration failed', { error });
        throw new IpcHandlerError('internal');
      }
    }
    try {
      await store.saveSettings(next);
    } catch (error) {
      logger.error('saving settings failed', { error });
      throw new IpcHandlerError('internal');
    }
    settings = store.getSettings();
    locale = resolveLocale(settings.language, deps.systemLocale);
    if (settings.material !== previous.material) theme = deps.theme.setMaterial(settings.material);
    if (settings.refreshIntervalSec !== previous.refreshIntervalSec) scheduler.reschedule();
    windows.applySettings(settings, theme);
    scheduleBroadcast();
    return { ...settings };
  };

  const bridgeCall = async (run: () => Promise<ClaudeBridgeStatus>): Promise<ClaudeBridgeStatus> => {
    try {
      return await run();
    } catch (error) {
      logger.warn('claude bridge call failed', { error });
      throw new IpcHandlerError('internal', errorCodeOf(error));
    }
  };

  // -------------------------------------------------------------------------
  // Public surface

  return {
    async start(): Promise<void> {
      const accounts = store.getAccounts();
      await Promise.all(
        accounts.map(async (account) => {
          try {
            await registry.get(account.provider).ensureProfileDir({ ...account });
          } catch (error) {
            logger.warn('ensureProfileDir failed', { provider: account.provider, error });
          }
        }),
      );
      await Promise.all(PROVIDER_IDS.map(detectProvider));
      for (const account of accounts) {
        if (account.enabled && !usage.has(account.id)) {
          usage.set(
            account.id,
            createEmptySnapshot({
              accountId: account.id,
              provider: account.provider,
              source: SOURCE_BY_PROVIDER[account.provider],
              state: 'loading',
            }),
          );
        }
      }
      if (deps.autostart.supported) {
        const registered = deps.autostart.isEnabled();
        if (registered !== null && registered !== settings.openAtLogin) {
          // The registry (e.g. Task Manager) is the truth; never re-register silently.
          settings = { ...settings, openAtLogin: registered };
          await store.saveSettings(settings).catch((error: unknown) => logger.warn('saving settings failed', { error }));
        }
      }
      stopped = false;
      scheduler.start();
      staleTimer = setInterval(markStale, STALE_CHECK_INTERVAL_MS);
      scheduleBroadcast();
    },

    stop(): void {
      stopped = true;
      login.cancelAll();
      scheduler.stop();
      if (staleTimer !== null) clearInterval(staleTimer);
      staleTimer = null;
    },

    snapshot,
    markStale,
    getSettings: (): Settings => ({ ...settings }),
    getLocale: (): Locale => locale,
    cliSummary: (): Record<ProviderId, CliSummary | null> => ({
      claude: cli.claude === null ? null : { ...cli.claude },
      codex: cli.codex === null ? null : { ...cli.codex },
      grok: cli.grok === null ? null : { ...cli.grok },
    }),

    suspend: (): void => scheduler.suspend(),
    resume: (): void => scheduler.resume(),
    setOnBattery: (onBattery: boolean): void => scheduler.setOnBattery(onBattery),

    onThemeChanged(tokens: ThemeTokens): void {
      const materialChanged = tokens.effectiveMaterial !== theme.effectiveMaterial;
      theme = tokens;
      if (materialChanged) windows.applySettings(settings, theme);
      windows.broadcast('theme:changed', { ...tokens });
    },

    onRendererReady(request: RendererReadyRequest): null {
      deps.onRendererReady?.(request);
      return null;
    },

    updateSettings(patch: Partial<Settings>): Promise<Settings> {
      return applySettings(applySettingsPatch(settings, patch));
    },

    listAccounts: (): AccountDTO[] => store.getAccounts().map(dtoFor),

    async addAccount(provider: ProviderId, label: string): Promise<AccountDTO> {
      const accounts = store.getAccounts();
      if (accounts.length >= MAX_ACCOUNTS) throw new IpcHandlerError('conflict');
      const id = newAccountId();
      if (accounts.some((account) => account.id === id)) throw new IpcHandlerError('conflict');
      let profileDir: string;
      try {
        profileDir = profileDirFor(deps.profilesRoot, provider, id);
      } catch {
        throw new IpcHandlerError('internal');
      }
      const account: Account = { id, provider, label, enabled: true, order: accounts.length, profileDir, createdAt: now() };
      try {
        await registry.get(provider).ensureProfileDir({ ...account });
      } catch (error) {
        logger.error('ensureProfileDir failed', { provider, error });
        throw new IpcHandlerError('internal', errorCodeOf(error));
      }
      await persistAccounts(renumberAccounts([...accounts, account]));
      needsIdentity.add(id);
      usage.set(id, createEmptySnapshot({ accountId: id, provider, source: SOURCE_BY_PROVIDER[provider], state: 'loading' }));
      scheduler.sync();
      scheduleBroadcast();
      return dtoFor(requireAccount(id));
    },

    async removeAccount(accountId: string): Promise<null> {
      const account = requireAccount(accountId);
      login.cancelForAccount(accountId);
      scheduler.cancel(accountId);
      try {
        await registry.get(account.provider).removeProfile({ ...account });
      } catch (error) {
        logger.error('removeProfile failed', { provider: account.provider, error });
        throw new IpcHandlerError('internal', errorCodeOf(error));
      }
      await persistAccounts(renumberAccounts(store.getAccounts().filter((a) => a.id !== accountId)));
      usage.delete(accountId);
      identities.delete(accountId);
      needsIdentity.delete(accountId);
      scheduler.sync();
      scheduleBroadcast();
      return null;
    },

    async renameAccount(accountId: string, label: string): Promise<AccountDTO> {
      requireAccount(accountId);
      await persistAccounts(store.getAccounts().map((a) => (a.id === accountId ? { ...a, label } : a)));
      scheduleBroadcast();
      return dtoFor(requireAccount(accountId));
    },

    async toggleAccount(accountId: string, enabled: boolean): Promise<AccountDTO> {
      const account = requireAccount(accountId);
      if (account.enabled !== enabled) {
        if (!enabled) scheduler.cancel(accountId);
        await persistAccounts(store.getAccounts().map((a) => (a.id === accountId ? { ...a, enabled } : a)));
        if (enabled && !usage.has(accountId)) {
          usage.set(
            accountId,
            createEmptySnapshot({ accountId, provider: account.provider, source: SOURCE_BY_PROVIDER[account.provider], state: 'loading' }),
          );
        }
        scheduler.sync();
        scheduleBroadcast();
      }
      return dtoFor(requireAccount(accountId));
    },

    async reorderAccount(accountId: string, direction: 'up' | 'down'): Promise<AccountDTO[]> {
      const moved = moveAccount(store.getAccounts(), accountId, direction);
      if (moved === null) throw new IpcHandlerError('not-found');
      await persistAccounts(moved);
      scheduleBroadcast();
      return store.getAccounts().map(dtoFor);
    },

    startLogin(accountId: string): { sessionId: string } {
      const account = requireAccount(accountId);
      const info = cli[account.provider];
      if (info !== null && !info.found) throw new IpcHandlerError('conflict', info.errorCode ?? 'cli-not-found');
      scheduler.cancel(accountId);
      return login.start(accountId);
    },

    cancelLogin(sessionId: string): null {
      if (!login.cancel(sessionId)) throw new IpcHandlerError('not-found');
      return null;
    },

    async submitLoginPaste(sessionId: string, text: string): Promise<null> {
      try {
        await login.submitPaste(sessionId, text);
      } catch (error) {
        if (error instanceof IpcHandlerError) throw error;
        logger.warn('submitPaste failed', { error });
        throw new IpcHandlerError('internal', errorCodeOf(error));
      }
      return null;
    },

    refreshNow(accountId: string | null): Promise<null> {
      const accounts = store.getAccounts();
      if (accountId !== null && !accounts.some((a) => a.id === accountId)) {
        return Promise.reject(new IpcHandlerError('not-found'));
      }
      const providers = [
        ...new Set(accounts.filter((a) => a.enabled && (accountId === null || a.id === accountId)).map((a) => a.provider)),
      ];
      // Respond immediately; progress shows through refresh status in state:changed.
      void redetectMissing(providers)
        .catch((error: unknown) => logger.warn('redetect failed', { error }))
        .then(() => scheduler.refreshNow(accountId));
      return Promise.resolve(null);
    },

    async openExternal(request: OpenExternalRequest): Promise<null> {
      let url: string | undefined;
      if (request.kind === 'link') {
        url = deps.externalLinks[request.key];
        if (url === undefined) throw new IpcHandlerError('not-found');
      } else {
        if (!login.isOpenableUrl(request.sessionId, request.url)) throw new IpcHandlerError('invalid-request');
        url = request.url;
      }
      try {
        await deps.openExternal(url);
      } catch (error) {
        logger.warn('openExternal failed', { error });
        throw new IpcHandlerError('internal');
      }
      return null;
    },

    togglePopup: (): null => (windows.togglePopup(), null),
    showPopup: (tab: PopupTab | null): null => (windows.showPopup(tab, true), null),
    hidePopup: (): null => (windows.hidePopup(), null),
    setPopupLock: (locked: boolean): null => (windows.setPopupLock(locked), null),
    resizeWidget: (request: ResizeWidgetRequest): null => (windows.resizeWidget(clampWidgetSize(request)), null),

    bridgeStatus: (): Promise<ClaudeBridgeStatus> => bridgeCall(() => registry.claude.bridge.status()),
    async bridgeInstallDefault(accountId: string): Promise<ClaudeBridgeStatus> {
      const account = requireAccount(accountId);
      if (account.provider !== 'claude') throw new IpcHandlerError('invalid-request');
      const status = await bridgeCall(() => registry.claude.bridge.installDefault({ ...account }));
      void scheduler.refreshNow(accountId);
      return status;
    },
    bridgeUninstallDefault: (): Promise<ClaudeBridgeStatus> => bridgeCall(() => registry.claude.bridge.uninstallDefault()),

    /** Tray / second-instance helpers. */
    revealFromSecondInstance(): void {
      windows.showWidget();
      windows.showPopup(null, true);
    },
    isLoginActive: (accountId: string): boolean => login.isActive(accountId),
  };
}

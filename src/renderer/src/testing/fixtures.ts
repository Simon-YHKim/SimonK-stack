// Test-only fixtures. Never imported by application code.

import type {
  EventChannel,
  EventContract,
  InvokeChannel,
  InvokeRequest,
  InvokeResponse,
  IpcResult,
  PreloadApi,
} from '../../../shared/ipc';
import { DEFAULT_SETTINGS, type Settings } from '../../../shared/settings';
import type {
  AccountDTO,
  AppStateSnapshot,
  QuotaWindow,
  QuotaWindowKind,
  ThemeTokens,
  UsageSnapshot,
} from '../../../shared/types';

export const NOW = Date.UTC(2026, 8, 15, 3, 0, 0);
export const HOUR = 3_600_000;

export function themeTokens(overrides: Partial<ThemeTokens> = {}): ThemeTokens {
  return {
    scheme: 'dark',
    taskbarScheme: 'dark',
    highContrast: false,
    accent: '#0078d4',
    reducedTransparency: false,
    effectiveMaterial: 'none',
    ...overrides,
  };
}

export function account(overrides: Partial<AccountDTO> & Pick<AccountDTO, 'id'>): AccountDTO {
  return { provider: 'codex', label: overrides.id, enabled: true, order: 0, loginState: 'logged-in', ...overrides };
}

export function quotaWindow(kind: QuotaWindowKind, usedPercent: number | null, resetInMs: number | null): QuotaWindow {
  return {
    kind,
    usedPercent,
    resetsAt: resetInMs === null ? null : NOW + resetInMs,
    windowMinutes: kind === 'session' ? 300 : kind === 'weekly' ? 10_080 : 60,
  };
}

export function usage(
  accountId: string,
  overrides: Partial<UsageSnapshot> = {},
): UsageSnapshot {
  return {
    accountId,
    provider: 'codex',
    state: 'ok',
    windows: [quotaWindow('session', 25, 2 * HOUR + 7 * 60_000), quotaWindow('weekly', 90, 4 * 24 * HOUR)],
    measuredAt: NOW - 30_000,
    lastSuccessAt: NOW - 30_000,
    source: 'codex-app-server',
    ...overrides,
  };
}

export type AppStateOverrides = Omit<Partial<AppStateSnapshot>, 'settings'> & { settings?: Partial<Settings> };

export function appState(overrides: AppStateOverrides = {}): AppStateSnapshot {
  const { settings, ...rest } = overrides;
  return {
    locale: 'en',
    accounts: [],
    usage: [],
    refresh: { inFlight: false, accountIds: [], lastRunAt: null, nextRunAt: null },
    theme: themeTokens(),
    cli: { claude: { state: 'found', version: '2.1.270' }, codex: { state: 'found' }, grok: { state: 'missing' } },
    effectivePlacementMode: null,
    ...rest,
    settings: { ...DEFAULT_SETTINGS, ...settings },
  };
}

type Handler = (request: unknown) => IpcResult<unknown> | Promise<IpcResult<unknown>>;

/** Records invokes; replies with configured handlers or `{ok:true,value:null}`. */
export class FakeApi implements PreloadApi {
  readonly calls: { channel: InvokeChannel; request: unknown }[] = [];
  private readonly handlers = new Map<InvokeChannel, Handler>();
  private readonly listeners = new Map<EventChannel, Set<(payload: unknown) => void>>();

  reply<C extends InvokeChannel>(channel: C, handler: (request: InvokeRequest<C>) => IpcResult<InvokeResponse<C>> | Promise<IpcResult<InvokeResponse<C>>>): this {
    this.handlers.set(channel, handler as Handler);
    return this;
  }

  invoke<C extends InvokeChannel>(channel: C, request: InvokeRequest<C>): Promise<IpcResult<InvokeResponse<C>>> {
    this.calls.push({ channel, request });
    const handler = this.handlers.get(channel);
    const result = handler === undefined ? { ok: true as const, value: null } : handler(request);
    return Promise.resolve(result) as Promise<IpcResult<InvokeResponse<C>>>;
  }

  on<E extends EventChannel>(channel: E, listener: (payload: EventContract[E]) => void): () => void {
    const set = this.listeners.get(channel) ?? new Set();
    const wrapped = listener as (payload: unknown) => void;
    set.add(wrapped);
    this.listeners.set(channel, set);
    return () => set.delete(wrapped);
  }

  emit<E extends EventChannel>(channel: E, payload: EventContract[E]): void {
    for (const listener of this.listeners.get(channel) ?? []) listener(payload);
  }

  callsTo(channel: InvokeChannel): unknown[] {
    return this.calls.filter((call) => call.channel === channel).map((call) => call.request);
  }
}

/** Lets pending promise callbacks run. */
export async function flush(): Promise<void> {
  for (let i = 0; i < 5; i += 1) await Promise.resolve();
}

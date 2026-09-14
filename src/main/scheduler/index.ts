import {
  isErrorCode,
  type Account,
  type ErrorCode,
  type ProviderId,
  type RefreshStatus,
  type UsageSnapshot,
  type UsageSource,
} from '../../shared/types';
import { createEmptySnapshot } from '../../shared/usage';
import type { Logger } from '../log';
import { ProviderError } from '../providers/types';
import { computeBackoffMs } from './backoff';

export const SOURCE_BY_PROVIDER: Readonly<Record<ProviderId, UsageSource>> = {
  claude: 'claude-statusline',
  codex: 'codex-app-server',
  grok: 'grok-acp',
};

export const DEFAULT_FETCH_TIMEOUT_MS = 45_000;
export const MANUAL_MIN_INTERVAL_MS = 5_000;
export const RESUME_DELAY_MS = 3_000;
export const BATTERY_INTERVAL_MULTIPLIER = 2;
const MAX_TIMER_MS = 2_147_483_647;

export interface FetchOutcome {
  snapshot: UsageSnapshot;
  /** Provider hint for the next attempt after a failure (e.g. rate limit). */
  retryAfterMs?: number;
  /** Nothing was fetched (e.g. a login owns the profile): no result, no failure, next run at the interval. */
  skipped?: boolean;
}

export interface SchedulerOptions {
  /** Every account; only enabled ones are scheduled. */
  listAccounts(): readonly Account[];
  intervalSec(): number;
  fetch(account: Account, signal: AbortSignal): Promise<FetchOutcome>;
  /** Called once per finished fetch, as soon as it finishes (not batched). */
  onResult(account: Account, snapshot: UsageSnapshot): void;
  onStatus(status: RefreshStatus): void;
  logger: Logger;
  now?: () => number;
  random?: () => number;
  timeoutMs?: number;
  manualMinIntervalMs?: number;
  resumeDelayMs?: number;
}

export interface Scheduler {
  start(): void;
  stop(): void;
  /** Reconciles scheduled entries with the account list (added, removed, toggled). */
  sync(): void;
  /**
   * Manual refresh. Joins an in-flight fetch instead of starting another and
   * ignores repeats within the minimum interval. `null` = every enabled account.
   */
  refreshNow(accountId: string | null): Promise<void>;
  /** Aborts an account's in-flight fetch and discards its result. */
  cancel(accountId: string): void;
  /** Applies a changed refresh interval. */
  reschedule(): void;
  suspend(): void;
  resume(): void;
  setOnBattery(onBattery: boolean): void;
  status(): RefreshStatus;
}

interface Entry {
  account: Account;
  failures: number;
  dueAt: number;
  queued: boolean;
  run: Promise<void> | null;
  controller: AbortController | null;
  generation: number;
  lastStartedAt: number | null;
  waiters: (() => void)[];
}

function errorCodeOf(error: unknown): ErrorCode {
  if (error instanceof ProviderError) return error.code;
  const code = (error as { code?: unknown } | null)?.code;
  return isErrorCode(code) ? code : 'internal';
}

export function failureSnapshot(account: Account, errorCode: ErrorCode): UsageSnapshot {
  return createEmptySnapshot({
    accountId: account.id,
    provider: account.provider,
    source: SOURCE_BY_PROVIDER[account.provider],
    state: 'error',
    errorCode,
  });
}

export function createScheduler(options: SchedulerOptions): Scheduler {
  const now = options.now ?? Date.now;
  const random = options.random ?? Math.random;
  const timeoutMs = options.timeoutMs ?? DEFAULT_FETCH_TIMEOUT_MS;
  const manualMinIntervalMs = options.manualMinIntervalMs ?? MANUAL_MIN_INTERVAL_MS;
  const resumeDelayMs = options.resumeDelayMs ?? RESUME_DELAY_MS;
  const logger = options.logger;

  const entries = new Map<string, Entry>();
  let running = false;
  let paused = false;
  let onBattery = false;
  let timer: ReturnType<typeof setTimeout> | null = null;
  let lastRunAt: number | null = null;
  let lastStatusJson = '';

  const intervalMs = (): number =>
    options.intervalSec() * 1000 * (onBattery ? BATTERY_INTERVAL_MULTIPLIER : 1);

  const wakeWaiters = (entry: Entry): void => {
    const waiters = entry.waiters;
    entry.waiters = [];
    for (const wake of waiters) wake();
  };

  const computeStatus = (): RefreshStatus => {
    const active = [...entries.values()].filter((entry) => entry.run !== null || entry.queued);
    let nextRunAt: number | null = null;
    if (running && !paused) {
      for (const entry of entries.values()) {
        if (entry.run === null && (nextRunAt === null || entry.dueAt < nextRunAt)) nextRunAt = entry.dueAt;
      }
    }
    return {
      inFlight: active.length > 0,
      accountIds: active.map((entry) => entry.account.id),
      lastRunAt,
      nextRunAt,
    };
  };

  const emitStatus = (): void => {
    const status = computeStatus();
    const json = JSON.stringify(status);
    if (json === lastStatusJson) return;
    lastStatusJson = json;
    options.onStatus(status);
  };

  const clearTimer = (): void => {
    if (timer !== null) clearTimeout(timer);
    timer = null;
  };

  const arm = (): void => {
    clearTimer();
    if (!running || paused) return;
    let earliest: number | null = null;
    for (const entry of entries.values()) {
      if (entry.run === null && !entry.queued && (earliest === null || entry.dueAt < earliest)) earliest = entry.dueAt;
    }
    if (earliest === null) return;
    const delay = Math.min(MAX_TIMER_MS, Math.max(0, earliest - now()));
    timer = setTimeout(pump, delay);
  };

  const runFetch = async (account: Account, controller: AbortController): Promise<FetchOutcome> => {
    let timeoutHandle: ReturnType<typeof setTimeout> | undefined;
    const timedOut = new Promise<null>((resolve) => {
      timeoutHandle = setTimeout(() => {
        controller.abort();
        resolve(null);
      }, timeoutMs);
    });
    try {
      const fetching = options.fetch(account, controller.signal);
      fetching.catch(() => undefined);
      const result = await Promise.race([fetching, timedOut]);
      if (result === null) return { snapshot: failureSnapshot(account, 'timeout') };
      return result;
    } catch (error) {
      if (controller.signal.aborted) return { snapshot: failureSnapshot(account, 'cancelled') };
      logger.warn('fetch threw', { provider: account.provider, error });
      return { snapshot: failureSnapshot(account, errorCodeOf(error)) };
    } finally {
      clearTimeout(timeoutHandle);
    }
  };

  const startRun = (entry: Entry): void => {
    entry.queued = false;
    entry.generation += 1;
    const generation = entry.generation;
    const controller = new AbortController();
    entry.controller = controller;
    entry.lastStartedAt = now();
    const account = { ...entry.account };

    const holder: { promise: Promise<void> | null } = { promise: null };
    const promise = (async () => {
      const outcome = await runFetch(account, controller);
      if (entry.generation !== generation || entries.get(account.id) !== entry) return;
      if (outcome.skipped === true) {
        entry.dueAt = now() + intervalMs();
        return;
      }
      const snapshot = outcome.snapshot;
      let delay: number;
      if (snapshot.state === 'error') {
        entry.failures += 1;
        delay = computeBackoffMs({
          failures: entry.failures,
          rateLimited: snapshot.errorCode === 'rate-limited',
          retryAfterMs: outcome.retryAfterMs,
          random,
        });
      } else {
        entry.failures = 0;
        delay = intervalMs();
      }
      entry.dueAt = now() + delay;
      try {
        options.onResult(account, snapshot);
      } catch (error) {
        logger.error('onResult failed', { error });
      }
    })().finally(() => {
      if (entry.run === holder.promise) {
        entry.run = null;
        entry.controller = null;
      }
      lastRunAt = now();
      wakeWaiters(entry);
      pump();
    });
    holder.promise = promise;
    entry.run = promise;
  };

  function pump(): void {
    timer = null;
    if (!running || paused) {
      emitStatus();
      return;
    }
    const at = now();
    const ordered = [...entries.values()].sort((a, b) => a.dueAt - b.dueAt);
    for (const entry of ordered) {
      if (entry.run === null && !entry.queued && entry.dueAt <= at) entry.queued = true;
    }
    // One fetch per provider at a time.
    const busy = new Set<ProviderId>();
    for (const entry of ordered) if (entry.run !== null) busy.add(entry.account.provider);
    for (const entry of ordered) {
      if (!entry.queued || busy.has(entry.account.provider)) continue;
      busy.add(entry.account.provider);
      startRun(entry);
    }
    arm();
    emitStatus();
  }

  const cancelEntry = (entry: Entry): void => {
    entry.generation += 1;
    entry.controller?.abort();
    entry.controller = null;
    entry.run = null;
    entry.queued = false;
    wakeWaiters(entry);
  };

  const waitFor = (entry: Entry): Promise<void> =>
    new Promise<void>((resolve) => {
      entry.waiters.push(resolve);
    });

  return {
    start() {
      running = true;
      paused = false;
      this.sync();
    },
    stop() {
      running = false;
      clearTimer();
      for (const entry of entries.values()) cancelEntry(entry);
      emitStatus();
    },
    sync() {
      const enabled = options.listAccounts().filter((account) => account.enabled);
      const ids = new Set(enabled.map((account) => account.id));
      for (const [id, entry] of entries) {
        if (!ids.has(id) || entry.account.provider !== enabled.find((a) => a.id === id)?.provider) {
          cancelEntry(entry);
          entries.delete(id);
        }
      }
      for (const account of enabled) {
        const existing = entries.get(account.id);
        if (existing !== undefined) {
          existing.account = { ...account };
          continue;
        }
        entries.set(account.id, {
          account: { ...account },
          failures: 0,
          dueAt: now(),
          queued: false,
          run: null,
          controller: null,
          generation: 0,
          lastStartedAt: null,
          waiters: [],
        });
      }
      pump();
    },
    refreshNow(accountId) {
      if (!running || paused) return Promise.resolve();
      const targets =
        accountId === null
          ? [...entries.values()]
          : [entries.get(accountId)].filter((entry): entry is Entry => entry !== undefined);
      const at = now();
      const waits = targets.map((entry) => {
        if (entry.run !== null) return entry.run;
        if (entry.queued) return waitFor(entry);
        if (entry.lastStartedAt !== null && at - entry.lastStartedAt < manualMinIntervalMs) return Promise.resolve();
        entry.dueAt = at;
        return waitFor(entry);
      });
      pump();
      return Promise.all(waits).then(() => undefined);
    },
    cancel(accountId) {
      const entry = entries.get(accountId);
      if (entry === undefined) return;
      cancelEntry(entry);
      entry.dueAt = now() + intervalMs();
      pump();
    },
    reschedule() {
      const next = now() + intervalMs();
      for (const entry of entries.values()) {
        if (entry.run === null && entry.failures === 0) entry.dueAt = Math.min(entry.dueAt, next);
      }
      arm();
      emitStatus();
    },
    suspend() {
      if (paused) return;
      paused = true;
      clearTimer();
      for (const entry of entries.values()) cancelEntry(entry);
      emitStatus();
    },
    resume() {
      if (!paused) return;
      paused = false;
      const due = now() + resumeDelayMs;
      for (const entry of entries.values()) entry.dueAt = due;
      arm();
      emitStatus();
    },
    setOnBattery(value) {
      onBattery = value;
    },
    status: computeStatus,
  };
}

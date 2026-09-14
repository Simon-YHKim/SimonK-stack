import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Account, RefreshStatus, UsageSnapshot } from '../../shared/types';
import { nullLogger } from '../log';
import { ProviderError } from '../providers/types';
import { BACKOFF_BASE_MS, BACKOFF_MAX_MS, RATE_LIMITED_MIN_MS, computeBackoffMs } from './backoff';
import { SOURCE_BY_PROVIDER, createScheduler, type FetchOutcome, type SchedulerOptions } from '.';

const account = (id: string, provider: Account['provider'] = 'codex', enabled = true): Account => ({
  id,
  provider,
  label: id,
  enabled,
  order: 0,
  profileDir: `C:\\p\\${id}`,
  createdAt: 1,
});

const snap = (a: Account, state: UsageSnapshot['state'], errorCode?: UsageSnapshot['errorCode']): UsageSnapshot => ({
  accountId: a.id,
  provider: a.provider,
  state,
  windows: [],
  measuredAt: state === 'ok' ? Date.now() : null,
  lastSuccessAt: state === 'ok' ? Date.now() : null,
  source: SOURCE_BY_PROVIDER[a.provider],
  ...(errorCode === undefined ? {} : { errorCode }),
});

interface Deferred {
  account: Account;
  signal: AbortSignal;
  resolve(outcome: FetchOutcome): void;
  reject(error: unknown): void;
}

function harness(accounts: Account[], overrides: Partial<SchedulerOptions> = {}) {
  const calls: Deferred[] = [];
  const results: { id: string; snapshot: UsageSnapshot }[] = [];
  const statuses: RefreshStatus[] = [];
  const scheduler = createScheduler({
    listAccounts: () => accounts,
    intervalSec: () => 60,
    fetch: (a, signal) =>
      new Promise<FetchOutcome>((resolve, reject) => {
        calls.push({ account: a, signal, resolve, reject });
      }),
    onResult: (a, snapshot) => results.push({ id: a.id, snapshot }),
    onStatus: (status) => statuses.push(status),
    logger: nullLogger,
    random: () => 0.5,
    timeoutMs: 10_000,
    ...overrides,
  });
  return { scheduler, calls, results, statuses };
}

describe('computeBackoffMs', () => {
  it('doubles from 30s up to 15min with jitter', () => {
    const mid = () => 0.5;
    expect(computeBackoffMs({ failures: 1, rateLimited: false, random: mid })).toBe(BACKOFF_BASE_MS);
    expect(computeBackoffMs({ failures: 2, rateLimited: false, random: mid })).toBe(60_000);
    expect(computeBackoffMs({ failures: 30, rateLimited: false, random: mid })).toBe(BACKOFF_MAX_MS);
    expect(computeBackoffMs({ failures: 1, rateLimited: false, random: () => 0 })).toBe(24_000);
    expect(computeBackoffMs({ failures: 1, rateLimited: false, random: () => 1 })).toBe(36_000);
  });

  it('waits at least 5 minutes when rate limited and honours retry-after', () => {
    expect(computeBackoffMs({ failures: 1, rateLimited: true, random: () => 0.5 })).toBe(RATE_LIMITED_MIN_MS);
    expect(computeBackoffMs({ failures: 1, rateLimited: false, retryAfterMs: 120_000, random: () => 0.5 })).toBe(120_000);
    expect(computeBackoffMs({ failures: 1, rateLimited: false, retryAfterMs: 1e12, random: () => 0.5 })).toBe(3_600_000);
  });
});

describe('scheduler', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(1_000_000);
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('fetches enabled accounts, one per provider, reporting each result as it arrives', async () => {
    const accounts = [account('c1'), account('c2'), account('g1', 'grok'), account('off', 'claude', false)];
    const { scheduler, calls, results, statuses } = harness(accounts);
    scheduler.start();
    await vi.advanceTimersByTimeAsync(0);
    expect(calls.map((c) => c.account.id)).toEqual(['c1', 'g1']);
    expect(statuses.at(-1)).toMatchObject({ inFlight: true });
    expect(statuses.at(-1)?.accountIds.sort()).toEqual(['c1', 'c2', 'g1']);

    calls[1]!.resolve({ snapshot: snap(accounts[2]!, 'ok') });
    await vi.advanceTimersByTimeAsync(0);
    expect(results.map((r) => r.id)).toEqual(['g1']);

    calls[0]!.resolve({ snapshot: snap(accounts[0]!, 'ok') });
    await vi.advanceTimersByTimeAsync(0);
    expect(results.map((r) => r.id)).toEqual(['g1', 'c1']);
    expect(calls.map((c) => c.account.id)).toEqual(['c1', 'g1', 'c2']);

    calls[2]!.resolve({ snapshot: snap(accounts[1]!, 'ok') });
    await vi.advanceTimersByTimeAsync(0);
    expect(statuses.at(-1)).toMatchObject({ inFlight: false, accountIds: [] });
    scheduler.stop();
  });

  it('polls at the interval after success and backs off after errors', async () => {
    const a = account('a');
    const { scheduler, calls } = harness([a]);
    scheduler.start();
    await vi.advanceTimersByTimeAsync(0);
    calls[0]!.resolve({ snapshot: snap(a, 'ok') });
    await vi.advanceTimersByTimeAsync(59_999);
    expect(calls).toHaveLength(1);
    await vi.advanceTimersByTimeAsync(1);
    expect(calls).toHaveLength(2);

    calls[1]!.resolve({ snapshot: snap(a, 'error', 'network') });
    await vi.advanceTimersByTimeAsync(29_999);
    expect(calls).toHaveLength(2);
    await vi.advanceTimersByTimeAsync(1);
    expect(calls).toHaveLength(3);

    calls[2]!.resolve({ snapshot: snap(a, 'error', 'rate-limited') });
    await vi.advanceTimersByTimeAsync(RATE_LIMITED_MIN_MS - 1);
    expect(calls).toHaveLength(3);
    await vi.advanceTimersByTimeAsync(1);
    expect(calls).toHaveLength(4);

    calls[3]!.resolve({ snapshot: snap(a, 'error', 'provider-error'), retryAfterMs: 20 * 60_000 });
    await vi.advanceTimersByTimeAsync(20 * 60_000 - 1);
    expect(calls).toHaveLength(4);
    await vi.advanceTimersByTimeAsync(1);
    expect(calls).toHaveLength(5);
    scheduler.stop();
  });

  it('coalesces manual refreshes: joins in-flight work and ignores repeats within 5s', async () => {
    const a = account('a');
    const { scheduler, calls } = harness([a]);
    scheduler.start();
    await vi.advanceTimersByTimeAsync(0);
    const joined = scheduler.refreshNow('a');
    void scheduler.refreshNow(null);
    expect(calls).toHaveLength(1);
    calls[0]!.resolve({ snapshot: snap(a, 'ok') });
    await joined;

    await vi.advanceTimersByTimeAsync(1_000);
    await scheduler.refreshNow('a');
    expect(calls).toHaveLength(1);

    await vi.advanceTimersByTimeAsync(4_000);
    const manual = scheduler.refreshNow('a');
    await vi.advanceTimersByTimeAsync(0);
    expect(calls).toHaveLength(2);
    calls[1]!.resolve({ snapshot: snap(a, 'ok') });
    await manual;
    scheduler.stop();
  });

  it('times out a hung fetch, aborts its signal and reports timeout', async () => {
    const a = account('a');
    const { scheduler, calls, results } = harness([a], { timeoutMs: 5_000 });
    scheduler.start();
    await vi.advanceTimersByTimeAsync(5_000);
    expect(calls[0]!.signal.aborted).toBe(true);
    expect(results[0]?.snapshot).toMatchObject({ state: 'error', errorCode: 'timeout', windows: [] });
    scheduler.stop();
  });

  it('maps thrown errors to error snapshots', async () => {
    const a = account('a');
    const { scheduler, calls, results } = harness([a]);
    scheduler.start();
    await vi.advanceTimersByTimeAsync(0);
    calls[0]!.reject(new ProviderError('parse-error'));
    await vi.advanceTimersByTimeAsync(0);
    expect(results[0]?.snapshot).toMatchObject({ state: 'error', errorCode: 'parse-error' });
    scheduler.stop();
  });

  it('discards results of removed accounts and of fetches aborted by suspend', async () => {
    const accounts = [account('a'), account('b', 'grok')];
    const { scheduler, calls, results } = harness(accounts);
    scheduler.start();
    await vi.advanceTimersByTimeAsync(0);

    accounts.splice(0, 1);
    scheduler.sync();
    expect(calls[0]!.signal.aborted).toBe(true);
    calls[0]!.resolve({ snapshot: snap(account('a'), 'ok') });

    scheduler.suspend();
    expect(calls[1]!.signal.aborted).toBe(true);
    calls[1]!.resolve({ snapshot: snap(accounts[0]!, 'ok') });
    await vi.advanceTimersByTimeAsync(120_000);
    expect(results).toEqual([]);
    expect(calls).toHaveLength(2);

    scheduler.resume();
    await vi.advanceTimersByTimeAsync(2_999);
    expect(calls).toHaveLength(2);
    await vi.advanceTimersByTimeAsync(1);
    expect(calls.map((c) => c.account.id)).toEqual(['a', 'b', 'b']);
    scheduler.stop();
  });

  it('keeps a single wake-up timer armed however often pump runs (CR-08)', async () => {
    const accounts = [account('a'), account('b', 'grok')];
    const { scheduler, calls } = harness(accounts);
    scheduler.start();
    await vi.advanceTimersByTimeAsync(0);
    calls[0]!.resolve({ snapshot: snap(accounts[0]!, 'ok') });
    await vi.advanceTimersByTimeAsync(0);
    calls[1]!.resolve({ snapshot: snap(accounts[1]!, 'ok') });
    await vi.advanceTimersByTimeAsync(0);
    for (let i = 0; i < 5; i += 1) scheduler.sync();
    // Both idle: exactly one wake-up timer, however many times pump ran.
    expect(vi.getTimerCount()).toBe(1);
    await vi.advanceTimersByTimeAsync(60_000);
    expect(calls).toHaveLength(4);
    // Both running: only their two fetch timeouts, no leftover wake-up.
    expect(vi.getTimerCount()).toBe(2);
    scheduler.stop();
  });

  it('treats skipped fetches as neither result nor failure', async () => {
    const a = account('a');
    const { scheduler, calls, results } = harness([a]);
    scheduler.start();
    await vi.advanceTimersByTimeAsync(0);
    calls[0]!.resolve({ snapshot: snap(a, 'loading'), skipped: true });
    await vi.advanceTimersByTimeAsync(59_999);
    expect(results).toEqual([]);
    expect(calls).toHaveLength(1);
    await vi.advanceTimersByTimeAsync(1);
    expect(calls).toHaveLength(2);
    scheduler.stop();
  });

  it('stretches the interval on battery and applies a shorter interval immediately', async () => {
    const a = account('a');
    let interval = 300;
    const { scheduler, calls } = harness([a], { intervalSec: () => interval });
    scheduler.setOnBattery(true);
    scheduler.start();
    await vi.advanceTimersByTimeAsync(0);
    calls[0]!.resolve({ snapshot: snap(a, 'ok') });
    await vi.advanceTimersByTimeAsync(0);
    expect(scheduler.status().nextRunAt).toBe(Date.now() + 600_000);

    scheduler.setOnBattery(false);
    interval = 15;
    scheduler.reschedule();
    await vi.advanceTimersByTimeAsync(15_000);
    expect(calls).toHaveLength(2);
    scheduler.stop();
  });
});

import { createHash } from 'node:crypto';
import { describe, expect, it } from 'vitest';
import { bridgeKeyFor, normalizeConfigDir, parseBridgeRecord, snapshotFromBridge, type BridgeRecord } from './bridge-data';

const NOW = Date.UTC(2026, 8, 15, 3, 0, 0);
const HOUR = 3_600_000;

function record(partial: Partial<BridgeRecord> = {}): BridgeRecord {
  return {
    configDirHash: 'aaaaaaaaaaaaaaaa',
    seenAt: NOW,
    capturedAt: NOW - 1000,
    fiveHour: { usedPercentage: 23.5, resetsAtSec: (NOW + 2 * HOUR) / 1000, capturedAt: NOW - 1000 },
    sevenDay: { usedPercentage: 41.2, resetsAtSec: (NOW + 72 * HOUR) / 1000, capturedAt: NOW - 1000 },
    ...partial,
  };
}

describe('bridge keys', () => {
  it('normalizes separators, case and trailing slashes', () => {
    const a = 'C:\\Users\\Me\\AppData\\Local\\AIUsageWidget\\profiles\\claude\\acc1';
    expect(normalizeConfigDir('c:/users/me/appdata/local/aiusagewidget/profiles/claude/acc1/')).toBe(a.toLowerCase());
    expect(bridgeKeyFor(a)).toBe(bridgeKeyFor('c:/users/me/appdata/local/aiusagewidget/profiles/claude/acc1\\'));
    expect(bridgeKeyFor(a)).not.toBe(bridgeKeyFor(`${a}2`));
    expect(bridgeKeyFor(a)).toMatch(/^[0-9a-f]{16}$/);
  });

  it('hashes the documented marker for the default profile', () => {
    expect(bridgeKeyFor(null)).toBe(createHash('sha256').update('~/.claude default').digest('hex').slice(0, 16));
  });
});

describe('parseBridgeRecord', () => {
  const text = JSON.stringify({
    v: 1,
    configDirHash: 'aaaaaaaaaaaaaaaa',
    seenAt: NOW,
    capturedAt: NOW,
    rate_limits: {
      five_hour: { used_percentage: 23.5, resets_at: 1789500000, captured_at: NOW },
      seven_day: { used_percentage: null, resets_at: 1789900000, captured_at: NOW },
    },
    model: { id: 'claude-opus-5', display_name: 'Opus' },
    runtime: 'node',
  });

  it('parses a valid record', () => {
    expect(parseBridgeRecord(text, 'aaaaaaaaaaaaaaaa')).toEqual({
      configDirHash: 'aaaaaaaaaaaaaaaa',
      seenAt: NOW,
      capturedAt: NOW,
      fiveHour: { usedPercentage: 23.5, resetsAtSec: 1789500000, capturedAt: NOW },
      sevenDay: { usedPercentage: null, resetsAtSec: 1789900000, capturedAt: NOW },
    });
  });

  it('accepts a record without windows (bridge ran before the first API response)', () => {
    const empty = JSON.stringify({ v: 1, configDirHash: 'aaaaaaaaaaaaaaaa', seenAt: NOW, capturedAt: null, rate_limits: {} });
    expect(parseBridgeRecord(empty, 'aaaaaaaaaaaaaaaa')).toMatchObject({ capturedAt: null, fiveHour: null, sevenDay: null });
  });

  it.each([
    ['another key', text, 'bbbbbbbbbbbbbbbb'],
    ['invalid JSON', '{', 'aaaaaaaaaaaaaaaa'],
    ['wrong version', text.replace('"v":1', '"v":2'), 'aaaaaaaaaaaaaaaa'],
    ['window without captured_at', text.replace(',"captured_at":' + String(NOW) + '}', '}'), 'aaaaaaaaaaaaaaaa'],
    ['rate_limits not an object', text.replace(/"rate_limits":\{.*\},"model"/, '"rate_limits":[],"model"'), 'aaaaaaaaaaaaaaaa'],
  ])('rejects %s', (_name, input, key) => {
    expect(parseBridgeRecord(input, key)).toBeNull();
  });
});

describe('snapshotFromBridge', () => {
  it('maps fresh readings to session and weekly windows', () => {
    const snapshot = snapshotFromBridge({ accountId: 'acc1', records: [record()], now: NOW });
    expect(snapshot).toEqual({
      accountId: 'acc1',
      provider: 'claude',
      state: 'ok',
      windows: [
        { kind: 'session', usedPercent: 23.5, resetsAt: NOW + 2 * HOUR, windowMinutes: 300 },
        { kind: 'weekly', usedPercent: 41.2, resetsAt: NOW + 72 * HOUR, windowMinutes: 10080 },
      ],
      measuredAt: NOW - 1000,
      lastSuccessAt: NOW,
      source: 'claude-statusline',
    });
  });

  it('shows an expired window as unknown instead of the old percentage', () => {
    const snapshot = snapshotFromBridge({
      accountId: 'acc1',
      records: [record({ fiveHour: { usedPercentage: 99, resetsAtSec: (NOW - 60_000) / 1000, capturedAt: NOW - HOUR } })],
      now: NOW,
    });
    expect(snapshot.state).toBe('ok');
    expect(snapshot.windows[0]).toEqual({ kind: 'session', usedPercent: null, resetsAt: NOW - 60_000, windowMinutes: 300 });
    expect(snapshot.windows[1]?.usedPercent).toBe(41.2);
  });

  it('is reset when every window has passed its reset time', () => {
    const snapshot = snapshotFromBridge({
      accountId: 'acc1',
      records: [
        record({
          fiveHour: { usedPercentage: 80, resetsAtSec: (NOW - 1000) / 1000, capturedAt: NOW - 6 * HOUR },
          sevenDay: { usedPercentage: 90, resetsAtSec: (NOW - 1000) / 1000, capturedAt: NOW - 6 * HOUR },
        }),
      ],
      now: NOW,
    });
    expect(snapshot.state).toBe('reset');
    expect(snapshot.windows.map((window) => window.usedPercent)).toEqual([null, null]);
  });

  it('is stale when the newest reading is old', () => {
    const old = NOW - 10 * 60_000;
    const snapshot = snapshotFromBridge({
      accountId: 'acc1',
      records: [record({ fiveHour: { usedPercentage: 10, resetsAtSec: (NOW + HOUR) / 1000, capturedAt: old }, sevenDay: null })],
      now: NOW,
    });
    expect(snapshot).toMatchObject({ state: 'stale', measuredAt: old });
    expect(snapshot.windows).toHaveLength(1);
  });

  it('reports bridge-no-data without windows', () => {
    const expected = { state: 'unavailable', errorCode: 'bridge-no-data', windows: [], measuredAt: null };
    expect(snapshotFromBridge({ accountId: 'acc1', records: [], now: NOW })).toMatchObject(expected);
    expect(snapshotFromBridge({ accountId: 'acc1', records: [record({ fiveHour: null, sevenDay: null })], now: NOW })).toMatchObject(
      expected,
    );
  });

  it('takes the newest reading per window across profiles and ignores future stamps', () => {
    const own = record({
      fiveHour: { usedPercentage: 5, resetsAtSec: (NOW + HOUR) / 1000, capturedAt: NOW - 30_000 },
      sevenDay: { usedPercentage: 70, resetsAtSec: (NOW + 50 * HOUR) / 1000, capturedAt: NOW - 20_000 },
    });
    const defaultProfile = record({
      fiveHour: { usedPercentage: 12, resetsAtSec: (NOW + HOUR) / 1000, capturedAt: NOW - 10_000 },
      sevenDay: { usedPercentage: 1, resetsAtSec: (NOW + 50 * HOUR) / 1000, capturedAt: NOW + 10 * 60_000 },
    });
    const snapshot = snapshotFromBridge({ accountId: 'acc1', records: [own, defaultProfile], now: NOW });
    expect(snapshot.windows.map((window) => window.usedPercent)).toEqual([12, 70]);
    expect(snapshot.measuredAt).toBe(NOW - 10_000);
  });

  it('clamps percentages and drops implausible reset times', () => {
    const snapshot = snapshotFromBridge({
      accountId: 'acc1',
      records: [
        record({
          fiveHour: { usedPercentage: 140, resetsAtSec: (NOW + 400 * 24 * HOUR) / 1000, capturedAt: NOW },
          sevenDay: null,
        }),
      ],
      now: NOW,
    });
    expect(snapshot.windows).toEqual([{ kind: 'session', usedPercent: 100, resetsAt: null, windowMinutes: 300 }]);
  });
});

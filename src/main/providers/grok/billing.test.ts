// Fixtures follow field names found in grok.exe 1.0.30 (extensions/billing.rs serde strings)
// and RESEARCH-auth-quota §3-3; the real `_x.ai/billing` payload is still pending live test T4.
import { describe, expect, it } from 'vitest';
import { normalizeTier, parseAmount, parseBillingResponse, parsePeriodType, parseTimestamp } from './billing';

const WEEKLY_END = '2026-09-17T07:51:00Z';

describe('parseAmount', () => {
  it('accepts numbers, numeric strings and val wrappers', () => {
    expect(parseAmount(12.5)).toBe(12.5);
    expect(parseAmount(' 4250 ')).toBe(4250);
    expect(parseAmount({ val: '10000' })).toBe(10000);
    expect(parseAmount({ value: 7 })).toBe(7);
  });

  it('returns null for anything else', () => {
    expect(parseAmount(undefined)).toBeNull();
    expect(parseAmount('12%')).toBeNull();
    expect(parseAmount(Number.NaN)).toBeNull();
    expect(parseAmount({ amount: 3 })).toBeNull();
    expect(parseAmount({ val: { val: { val: 1 } } })).toBeNull();
  });
});

describe('parseTimestamp', () => {
  it('parses ISO strings, epoch seconds, epoch ms and {seconds}', () => {
    const ms = Date.parse(WEEKLY_END);
    expect(parseTimestamp(WEEKLY_END)).toBe(ms);
    expect(parseTimestamp(ms / 1000)).toBe(ms);
    expect(parseTimestamp(ms)).toBe(ms);
    expect(parseTimestamp(String(ms / 1000))).toBe(ms);
    expect(parseTimestamp({ seconds: String(ms / 1000), nanos: 0 })).toBe(ms);
  });

  it('rejects small numbers and junk', () => {
    expect(parseTimestamp(5)).toBeNull();
    expect(parseTimestamp('soon')).toBeNull();
    expect(parseTimestamp('')).toBeNull();
    expect(parseTimestamp(null)).toBeNull();
  });
});

describe('parsePeriodType', () => {
  it('recognizes enum and short spellings', () => {
    expect(parsePeriodType('USAGE_PERIOD_TYPE_WEEKLY')).toBe('weekly');
    expect(parsePeriodType('weekly')).toBe('weekly');
    expect(parsePeriodType('MONTHLY')).toBe('monthly');
    expect(parsePeriodType('USAGE_PERIOD_TYPE_UNSPECIFIED')).toBe('unknown');
    expect(parsePeriodType(3)).toBe('unknown');
  });
});

describe('normalizeTier', () => {
  it('turns enum names into readable plan names', () => {
    expect(normalizeTier('SUBSCRIPTION_TIER_SUPER_GROK')).toBe('Super Grok');
    expect(normalizeTier('X_BASIC')).toBe('X Basic');
    expect(normalizeTier('SuperGrok Heavy')).toBe('SuperGrok Heavy');
  });

  it('drops empty, unspecified or suspicious values', () => {
    expect(normalizeTier('SUBSCRIPTION_TIER_UNSPECIFIED')).toBeUndefined();
    expect(normalizeTier('')).toBeUndefined();
    expect(normalizeTier('<script>')).toBeUndefined();
    expect(normalizeTier('x'.repeat(65))).toBeUndefined();
    expect(normalizeTier(1)).toBeUndefined();
  });
});

describe('parseBillingResponse', () => {
  it('maps a weekly period to a weekly window reset at currentPeriod.end', () => {
    const billing = parseBillingResponse({
      creditUsagePercent: 42.5,
      currentPeriod: { type: 'USAGE_PERIOD_TYPE_WEEKLY', end: WEEKLY_END },
      monthlyLimit: { val: '10000' },
      used: { val: '9000' },
      subscriptionTier: 'SUBSCRIPTION_TIER_SUPER_GROK',
      somethingNew: { deeply: ['ignored'] },
    });
    expect(billing).toEqual({
      windows: [
        { kind: 'weekly', usedPercent: 42.5, resetsAt: Date.parse(WEEKLY_END), windowMinutes: 10_080, label: 'credits' },
      ],
      periodType: 'weekly',
      overageAvailable: null,
      plan: 'Super Grok',
    });
  });

  it('falls back to used/monthlyLimit as an other window when the period is not weekly', () => {
    const billing = parseBillingResponse({
      currentPeriod: { type: 'MONTHLY', end: '2026-10-01T00:00:00Z' },
      monthlyLimit: { val: 2000 },
      used: { val: 600 },
      billingPeriodStart: '2026-09-01T00:00:00Z',
      billingPeriodEnd: '2026-10-01T00:00:00Z',
    });
    expect(billing?.windows).toEqual([
      {
        kind: 'other',
        usedPercent: 30,
        resetsAt: Date.parse('2026-10-01T00:00:00Z'),
        windowMinutes: 30 * 24 * 60,
        label: 'monthly',
      },
    ]);
    expect(billing?.periodType).toBe('monthly');
  });

  it('does not treat a weekly percent without a weekly period type as weekly', () => {
    const billing = parseBillingResponse({ creditUsagePercent: 10, currentPeriod: { end: WEEKLY_END } });
    expect(billing?.windows).toEqual([
      { kind: 'other', usedPercent: 10, resetsAt: Date.parse(WEEKLY_END), windowMinutes: null, label: 'credits' },
    ]);
  });

  it('keeps 100% as a value and flags on-demand credits instead of blocking', () => {
    const billing = parseBillingResponse({
      creditUsagePercent: 100,
      currentPeriod: { type: 'WEEKLY', end: WEEKLY_END },
      on_demand_enabled: true,
      onDemandCap: { val: '5000' },
      onDemandUsed: { val: '120' },
    });
    expect(billing?.windows[0]?.usedPercent).toBe(100);
    expect(billing?.overageAvailable).toBe(true);
  });

  it('detects prepaid balance and explicit on-demand off', () => {
    expect(parseBillingResponse({ prepaidBalance: { val: '250' } })?.overageAvailable).toBe(true);
    expect(parseBillingResponse({ on_demand_enabled: false, prepaidBalance: { val: '0' } })?.overageAvailable).toBe(false);
  });

  it('clamps out-of-range percentages and never invents values', () => {
    const over = parseBillingResponse({ creditUsagePercent: 180, currentPeriod: { type: 'WEEKLY' } });
    expect(over?.windows[0]).toEqual({ kind: 'weekly', usedPercent: 100, resetsAt: null, windowMinutes: 10_080, label: 'credits' });
    const unknown = parseBillingResponse({ creditUsagePercent: 'n/a', currentPeriod: { type: 'WEEKLY' } });
    expect(unknown?.windows).toEqual([]);
    expect(parseBillingResponse({ monthlyLimit: { val: 0 }, used: { val: 5 } })?.windows).toEqual([]);
  });

  it('finds billing data wrapped one level deep', () => {
    const billing = parseBillingResponse({ credits: { creditUsagePercent: 5, currentPeriod: { type: 'WEEKLY', end: WEEKLY_END } } });
    expect(billing?.windows[0]?.usedPercent).toBe(5);
  });

  it('returns an empty result for objects without quota fields and null for non-objects', () => {
    expect(parseBillingResponse({})).toEqual({ windows: [], periodType: 'unknown', overageAvailable: null });
    expect(parseBillingResponse(42)).toBeNull();
    expect(parseBillingResponse(null)).toBeNull();
    expect(parseBillingResponse([{ creditUsagePercent: 1 }])).toBeNull();
  });
});

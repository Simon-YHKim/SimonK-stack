// Fixture shapes follow `codex app-server generate-json-schema` output of codex-cli 0.154.0:
// v1/InitializeResponse.json, v2/LoginAccountResponse.json, v2/AccountLoginCompletedNotification.json,
// v2/GetAccountResponse.json, v2/GetAccountRateLimitsResponse.json.
import { describe, expect, it } from 'vitest';
import {
  isSafeHttpsUrl,
  parseAccountRead,
  parseInitializeResult,
  parseLoginCompleted,
  parseLoginStartResult,
  parseConsumeResetOutcome,
  parseRateLimits,
  parseResetOffer,
  samePath,
  sanitizeIdentifier,
} from './protocol';

describe('parseInitializeResult', () => {
  it('reads codexHome and ignores unknown fields', () => {
    expect(
      parseInitializeResult({
        codexHome: 'C:\\p',
        platformFamily: 'windows',
        platformOs: 'windows',
        userAgent: 'x',
        future: { nested: 1 },
      }),
    ).toEqual({ codexHome: 'C:\\p', platformOs: 'windows' });
  });

  it('rejects responses without a codexHome string', () => {
    expect(parseInitializeResult({})).toBeNull();
    expect(parseInitializeResult(null)).toBeNull();
    expect(parseInitializeResult({ codexHome: 5 })).toBeNull();
    expect(parseInitializeResult({ codexHome: '' })).toBeNull();
  });
});

describe('samePath', () => {
  it('compares Windows paths case-insensitively, ignoring the verbatim prefix and trailing separators', () => {
    expect(samePath('C:\\Users\\A\\profiles\\codex\\x', 'c:\\users\\a\\PROFILES\\codex\\x\\')).toBe(true);
    expect(samePath('\\\\?\\C:\\Users\\A\\p', 'C:\\Users\\A\\p')).toBe(true);
    expect(samePath('C:\\Users\\A\\p', 'C:\\Users\\A\\p2')).toBe(false);
    expect(samePath('C:\\Users\\A\\.codex', 'C:\\Users\\A\\profiles\\codex\\a')).toBe(false);
  });
});

describe('isSafeHttpsUrl', () => {
  it('accepts plain https URLs only', () => {
    expect(isSafeHttpsUrl('https://auth.openai.com/codex/device')).toBe(true);
    expect(isSafeHttpsUrl('http://auth.openai.com/codex/device')).toBe(false);
    expect(isSafeHttpsUrl('https://user:pw@auth.openai.com/')).toBe(false);
    expect(isSafeHttpsUrl('javascript:alert(1)')).toBe(false);
    expect(isSafeHttpsUrl(`https://a.example/${'x'.repeat(2100)}`)).toBe(false);
    expect(isSafeHttpsUrl('https://a.example/\u202etxt')).toBe(false);
    expect(isSafeHttpsUrl(42)).toBe(false);
  });
});

describe('sanitizeIdentifier', () => {
  it('passes identifier-like strings including unknown values and drops the rest', () => {
    expect(sanitizeIdentifier('pro')).toBe('pro');
    expect(sanitizeIdentifier('future_plan.v2')).toBe('future_plan.v2');
    expect(sanitizeIdentifier('unknown')).toBe('unknown');
    expect(sanitizeIdentifier('has space')).toBeUndefined();
    expect(sanitizeIdentifier('')).toBeUndefined();
    expect(sanitizeIdentifier(7)).toBeUndefined();
    expect(sanitizeIdentifier('x'.repeat(65))).toBeUndefined();
  });
});

describe('parseLoginStartResult', () => {
  const valid = {
    type: 'chatgptDeviceCode',
    loginId: 'login-1',
    userCode: 'ABCD-EFGH',
    verificationUrl: 'https://auth.openai.com/codex/device',
  };

  it('parses the device-code variant and tolerates extra fields', () => {
    expect(parseLoginStartResult({ ...valid, extra: true })).toEqual({
      loginId: 'login-1',
      userCode: 'ABCD-EFGH',
      verificationUrl: 'https://auth.openai.com/codex/device',
    });
  });

  it('rejects other variants and unsafe values', () => {
    expect(parseLoginStartResult({ ...valid, type: 'chatgpt' })).toBeNull();
    expect(parseLoginStartResult({ ...valid, userCode: undefined })).toBeNull();
    expect(parseLoginStartResult({ ...valid, userCode: 'AB\nCD' })).toBeNull();
    expect(parseLoginStartResult({ ...valid, verificationUrl: 'http://evil.example/' })).toBeNull();
    expect(parseLoginStartResult({ ...valid, loginId: '' })).toBeNull();
    expect(parseLoginStartResult('nope')).toBeNull();
  });
});

describe('parseLoginCompleted', () => {
  it('reads success, loginId and error text', () => {
    expect(parseLoginCompleted({ loginId: 'l', success: true, error: null, onboardingEntrypoint: null })).toEqual({
      loginId: 'l',
      success: true,
      error: null,
    });
    expect(parseLoginCompleted({ success: false, error: 'denied' })).toEqual({
      loginId: null,
      success: false,
      error: 'denied',
    });
  });

  it('rejects payloads without a boolean success', () => {
    expect(parseLoginCompleted({ loginId: 'l' })).toBeNull();
    expect(parseLoginCompleted(null)).toBeNull();
  });
});

describe('parseAccountRead', () => {
  it('reports no account when account is null or missing (observed on an empty CODEX_HOME)', () => {
    expect(parseAccountRead({ account: null, requiresOpenaiAuth: true })).toEqual({ kind: 'none' });
    expect(parseAccountRead({ requiresOpenaiAuth: true })).toEqual({ kind: 'none' });
  });

  it('masks the e-mail and passes plan types through, including unknown ones', () => {
    const info = parseAccountRead({
      account: { type: 'chatgpt', email: 'john.doe@example.com', planType: 'future_plan' },
      requiresOpenaiAuth: true,
    });
    expect(info).toEqual({ kind: 'chatgpt', emailMasked: 'j***@e***.com', planType: 'future_plan' });
    expect(JSON.stringify(info)).not.toContain('john.doe');
    expect(parseAccountRead({ account: { type: 'chatgpt', email: null, planType: 'unknown' } })).toEqual({
      kind: 'chatgpt',
      planType: 'unknown',
    });
  });

  it('treats non-ChatGPT accounts as signed in without subscription limits', () => {
    expect(parseAccountRead({ account: { type: 'apiKey' } })).toEqual({ kind: 'other' });
    expect(parseAccountRead({ account: { type: 'amazonBedrock', usesCodexManagedCredentials: false } })).toEqual({
      kind: 'other',
    });
  });

  it('rejects malformed payloads', () => {
    expect(parseAccountRead('x')).toBeNull();
    expect(parseAccountRead({ account: { email: 'a@b.co' } })).toBeNull();
    expect(parseAccountRead({ account: [] })).toBeNull();
  });
});

describe('parseRateLimits', () => {
  const codexBucket = {
    limitId: 'codex',
    limitName: null,
    primary: { usedPercent: 42, windowDurationMins: 300, resetsAt: 1_800_003_600 },
    secondary: { usedPercent: 88, windowDurationMins: 10_080, resetsAt: 1_800_400_000 },
    credits: { hasCredits: true, unlimited: false, balance: '12.50' },
    planType: 'pro',
    rateLimitReachedType: null,
  };

  it('maps every bucket, primary first, classifying windows by length', () => {
    const parsed = parseRateLimits({
      rateLimits: codexBucket,
      rateLimitsByLimitId: {
        codex_other: {
          limitId: 'codex_other',
          primary: { usedPercent: 5, windowDurationMins: 60, resetsAt: 1_800_001_000 },
          secondary: { usedPercent: 9, windowDurationMins: 300, resetsAt: 1_800_002_000 },
        },
        codex: codexBucket,
      },
      rateLimitResetCredits: { availableCount: 0, credits: null },
      ordinaryUsageAllowed: true,
      futureField: { anything: 1 },
    });
    expect(parsed).toEqual({
      windows: [
        { kind: 'session', usedPercent: 42, resetsAt: 1_800_003_600_000, windowMinutes: 300 },
        { kind: 'weekly', usedPercent: 88, resetsAt: 1_800_400_000_000, windowMinutes: 10_080 },
        { kind: 'other', usedPercent: 5, resetsAt: 1_800_001_000_000, windowMinutes: 60, label: 'codex_other' },
        { kind: 'session', usedPercent: 9, resetsAt: 1_800_002_000_000, windowMinutes: 300, label: 'codex_other' },
      ],
      planType: 'pro',
      credits: { hasCredits: true, unlimited: false, balance: '12.50' },
      resetCreditCount: 0,
    });
  });

  it('reads the measured Pro response, which carries a weekly window only (T1, codex 0.155.1, 26.09.20)', () => {
    const bucket = {
      limitId: 'codex',
      limitName: null,
      normalModelSlug: null,
      primary: { usedPercent: 18, windowDurationMins: 10_080, resetsAt: 1_790_420_068 },
      secondary: null,
      credits: { hasCredits: false, unlimited: false, balance: '0' },
      individualLimit: null,
      spendControlReached: false,
      planType: 'pro',
      rateLimitReachedType: null,
    };
    const parsed = parseRateLimits({
      ordinaryUsageAllowed: true,
      rateLimits: bucket,
      rateLimitsByLimitId: { codex: bucket },
      rateLimitResetCredits: { availableCount: 0, credits: null },
      accountId: '00000000-0000-4000-8000-000000000000',
      rateLimitUpsell: null,
    });
    // The server sends no 5-hour window for this plan, so the widget shows the weekly row alone.
    expect(parsed?.windows).toEqual([{ kind: 'weekly', usedPercent: 18, resetsAt: 1_790_420_068_000, windowMinutes: 10_080 }]);
    expect(parsed?.planType).toBe('pro');
  });

  it('falls back to the legacy single-bucket view', () => {
    expect(
      parseRateLimits({
        rateLimits: { limitId: null, primary: null, secondary: { usedPercent: 10, windowDurationMins: 10_080, resetsAt: null } },
        rateLimitsByLimitId: null,
      }),
    ).toEqual({ windows: [{ kind: 'weekly', usedPercent: 10, resetsAt: null, windowMinutes: 10_080 }] });
  });

  it('keeps the legacy bucket when the multi-bucket map lacks it', () => {
    const parsed = parseRateLimits({
      rateLimits: codexBucket,
      rateLimitsByLimitId: { extra: { primary: { usedPercent: 1, windowDurationMins: 15, resetsAt: null } } },
    });
    expect(parsed?.windows.map((w) => [w.kind, w.label])).toEqual([
      ['session', undefined],
      ['weekly', undefined],
      ['other', 'extra'],
    ]);
  });

  it('keeps unknown values as null instead of 0 and skips empty windows', () => {
    const parsed = parseRateLimits({
      rateLimits: {
        primary: { windowDurationMins: 300, resetsAt: 1_800_000_000 },
        secondary: { usedPercent: 150, windowDurationMins: null, resetsAt: 'soon' },
      },
      rateLimitsByLimitId: { codex: { primary: { usedPercent: null }, secondary: {} } },
    });
    expect(parsed?.windows).toEqual([]);
    const legacyOnly = parseRateLimits({
      rateLimits: {
        primary: { windowDurationMins: 300, resetsAt: 1_800_000_000 },
        secondary: { usedPercent: 150, windowDurationMins: null, resetsAt: 'soon' },
      },
    });
    expect(legacyOnly?.windows).toEqual([
      { kind: 'session', usedPercent: null, resetsAt: 1_800_000_000_000, windowMinutes: 300 },
      { kind: 'other', usedPercent: 100, resetsAt: null, windowMinutes: null, label: 'codex' },
    ]);
  });

  it('ignores bucket ids that are not identifier-like and invalid credits', () => {
    const parsed = parseRateLimits({
      rateLimitsByLimitId: {
        'bad id <script>': { primary: { usedPercent: 1, windowDurationMins: 300, resetsAt: null } },
        codex: { primary: { usedPercent: 2, windowDurationMins: 300, resetsAt: null }, credits: { hasCredits: 'yes' } },
      },
    });
    expect(parsed).toEqual({ windows: [{ kind: 'session', usedPercent: 2, resetsAt: null, windowMinutes: 300 }] });
  });

  it('rejects payloads without any rate-limit view', () => {
    expect(parseRateLimits(null)).toBeNull();
    expect(parseRateLimits({})).toBeNull();
    expect(parseRateLimits({ rateLimits: 'x', rateLimitsByLimitId: [] })).toBeNull();
  });
});

describe('banked reset parsing', () => {
  const now = 1_800_000_000_000;
  const base = { rateLimits: { primary: { usedPercent: 80, windowDurationMins: 10_080, resetsAt: 1_800_400_000 } } };

  it('reads a real available count without confusing it with purchased usage credits', () => {
    expect(parseRateLimits({ ...base, rateLimitResetCredits: { availableCount: 2, credits: null } })?.resetCreditCount).toBe(2);
    expect(parseRateLimits({ ...base, rateLimitResetCredits: { availableCount: -1 } })?.resetCreditCount).toBeUndefined();
    expect(parseRateLimits({ ...base, rateLimitResetCredits: { availableCount: '2' } })?.resetCreditCount).toBeUndefined();
  });

  it('selects the earliest unexpired Codex reset only when the backend account is known', () => {
    const credits = [
      { id: 'credit-later', resetType: 'codexRateLimits', status: 'available', expiresAt: 1_800_200_000 },
      { id: 'credit-sooner', resetType: 'codexRateLimits', status: 'available', expiresAt: 1_800_100_000 },
      { id: 'credit-expired', resetType: 'codexRateLimits', status: 'available', expiresAt: 1_799_999_999 },
      { id: 'credit-other', resetType: 'futureReset', status: 'available', expiresAt: 1_800_050_000 },
    ];
    expect(parseResetOffer({ ...base, accountId: 'workspace_1', rateLimitResetCredits: { availableCount: 3, credits } }, now))
      .toEqual({ backendAccountId: 'workspace_1', creditId: 'credit-sooner', availableCount: 3, expiresAt: 1_800_100_000_000 });
    expect(parseResetOffer({ ...base, rateLimitResetCredits: { availableCount: 3, credits } }, now)).toBeNull();
    expect(parseResetOffer({ ...base, accountId: 'workspace_1', rateLimitResetCredits: { availableCount: 3, credits: null } }, now)).toBeNull();
  });

  it('accepts only documented redemption outcomes', () => {
    for (const outcome of ['reset', 'nothingToReset', 'noCredit', 'alreadyRedeemed'] as const) {
      expect(parseConsumeResetOutcome({ outcome })).toBe(outcome);
    }
    expect(parseConsumeResetOutcome({ outcome: 'charged' })).toBeNull();
    expect(parseConsumeResetOutcome(null)).toBeNull();
  });
});

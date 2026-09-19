import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { MAX_GROUP_LABEL_LENGTH, parseAgyUsage, sanitizeGroupLabel } from './usage';

// Captured from `agy -p "/usage" --output-format json` (agy 1.2.6, 26.09.19); holds no account data.
const MEASURED = readFileSync(fileURLToPath(new URL('./test-fixtures/usage-1.2.6.json', import.meta.url)), 'utf8');

function withBuckets(buckets: unknown[], extra: Record<string, unknown> = {}): string {
  return JSON.stringify({
    status: 'SUCCESS',
    num_turns: 0,
    command: { name: 'usage', data: { groups: [{ name: 'G', buckets }] } },
    ...extra,
  });
}

describe('parseAgyUsage', () => {
  it('reads the measured 1.2.6 output: two groups, session before weekly, labelled by group', () => {
    const parsed = parseAgyUsage(MEASURED);
    expect(parsed.kind).toBe('ok');
    if (parsed.kind !== 'ok') return;
    expect(parsed.windows.map((w) => [w.label, w.kind, w.windowMinutes])).toEqual([
      ['Gemini Models', 'session', 300],
      ['Gemini Models', 'weekly', 10_080],
      ['Claude and GPT models', 'session', 300],
      ['Claude and GPT models', 'weekly', 10_080],
    ]);
    const [geminiSession, , , thirdPartyWeekly] = parsed.windows;
    expect(geminiSession?.usedPercent).toBeCloseTo(0.0678, 3);
    expect(geminiSession?.resetsAt).toBe(Date.parse('2026-09-19T05:48:24Z'));
    expect(thirdPartyWeekly?.usedPercent).toBe(0);
    expect(thirdPartyWeekly?.resetsAt).toBe(Date.parse('2026-09-26T02:40:37Z'));
  });

  it('turns remaining_fraction into used percent', () => {
    const parsed = parseAgyUsage(withBuckets([{ window: '5h', remaining_fraction: 0.25, reset_time: '2026-09-19T05:00:00Z' }]));
    expect(parsed).toMatchObject({ kind: 'ok', windows: [{ kind: 'session', usedPercent: 75 }] });
  });

  it('keeps an unknown fraction unknown instead of 0 % or 100 %', () => {
    for (const remaining of [undefined, null, 'half', Number.NaN, -0.1, 1.5]) {
      const parsed = parseAgyUsage(withBuckets([{ window: 'weekly', remaining_fraction: remaining, reset_time: '2026-09-26T00:00:00Z' }]));
      expect(parsed).toMatchObject({ kind: 'ok', windows: [{ kind: 'weekly', usedPercent: null }] });
    }
  });

  it('drops a bucket with neither a fraction nor a reset time', () => {
    expect(parseAgyUsage(withBuckets([{ window: '5h' }, 'text', null]))).toEqual({ kind: 'ok', windows: [] });
  });

  it('files an unrecognised window under "other" with unknown length', () => {
    const parsed = parseAgyUsage(withBuckets([{ window: 'monthly', remaining_fraction: 0.5, reset_time: 'not a date' }]));
    expect(parsed).toMatchObject({ kind: 'ok', windows: [{ kind: 'other', windowMinutes: null, usedPercent: 50, resetsAt: null }] });
  });

  it('reports a prompt-style answer as not-usage-command', () => {
    expect(parseAgyUsage(JSON.stringify({ status: 'SUCCESS', num_turns: 1, response: 'hello' }))).toEqual({ kind: 'not-usage-command' });
    expect(parseAgyUsage(withBuckets([], { num_turns: 2 }))).toEqual({ kind: 'not-usage-command' });
    expect(parseAgyUsage(JSON.stringify({ status: 'SUCCESS', num_turns: 0, command: { name: 'help', data: {} } }))).toEqual({
      kind: 'not-usage-command',
    });
  });

  it('reports a non-success status as failed and bad shapes as malformed', () => {
    expect(parseAgyUsage(JSON.stringify({ status: 'ERROR' }))).toEqual({ kind: 'failed', status: 'ERROR' });
    expect(parseAgyUsage('<<not json>>')).toEqual({ kind: 'malformed' });
    expect(parseAgyUsage('[]')).toEqual({ kind: 'malformed' });
    expect(parseAgyUsage(JSON.stringify({ status: 'SUCCESS', num_turns: 0, command: { name: 'usage', data: { groups: 'x' } } }))).toEqual({
      kind: 'malformed',
    });
  });
});

describe('sanitizeGroupLabel', () => {
  it('collapses whitespace and control characters and caps the length', () => {
    expect(sanitizeGroupLabel('  Gemini\u0000\tModels\n')).toBe('Gemini Models');
    expect(sanitizeGroupLabel('x'.repeat(200))).toHaveLength(MAX_GROUP_LABEL_LENGTH);
    expect(sanitizeGroupLabel('   ')).toBeUndefined();
    expect(sanitizeGroupLabel(42)).toBeUndefined();
  });
});

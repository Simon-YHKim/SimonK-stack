import { describe, expect, it } from 'vitest';
import { DEFAULT_SETTINGS } from '../../shared/settings';
import { relativeTimeText } from './format';
import { pickLocale } from './locale';
import { createTranslator } from '../../shared/i18n';
import { buildAccountView, extraUsageParts, itemTooltip, selectWidgetRows, tagForWindow, toRow } from './model';
import { HOUR, NOW, account, quotaWindow, themeTokens, usage } from './testing/fixtures';
import { accentForeground, safeAccent } from './theme';

describe('view model', () => {
  it('missing snapshot is loading, logged-out or cli error by login state', () => {
    const settings = { ...DEFAULT_SETTINGS };
    expect(buildAccountView(account({ id: 'a' }), null, settings, NOW).state).toBe('loading');
    expect(buildAccountView(account({ id: 'a', loginState: 'logged-out' }), null, settings, NOW).state).toBe('logged-out');
    const cli = buildAccountView(account({ id: 'a', loginState: 'cli-missing' }), null, settings, NOW);
    expect([cli.state, cli.errorCode]).toEqual(['error', 'cli-not-found']);
  });

  it('tooltip names a weekly-only window as weekly', () => {
    const snapshot = usage('g', { provider: 'grok', source: 'grok-acp', windows: [quotaWindow('weekly', 40, 2 * HOUR)] });
    const view = buildAccountView(account({ id: 'g', provider: 'grok', label: 'G' }), snapshot, DEFAULT_SETTINGS, NOW);
    const ctx = { t: createTranslator('en'), locale: 'en' as const, settings: DEFAULT_SETTINGS, theme: themeTokens(), now: NOW };
    expect(itemTooltip(view, ctx)).toContain('G | Weekly: 60% left (');
  });

  it('ok snapshot without windows is shown as unavailable', () => {
    const view = buildAccountView(account({ id: 'a' }), usage('a', { windows: [] }), DEFAULT_SETTINGS, NOW);
    expect([view.state, view.errorCode]).toEqual(['unavailable', 'quota-unavailable']);
  });

  it('rows: unknown stays null, expired windows are reset', () => {
    expect(toRow(quotaWindow('session', null, HOUR), NOW, false)).toMatchObject({ status: 'unknown', shownPercent: null, level: 'unknown' });
    expect(toRow(quotaWindow('session', 50, -1), NOW, false)).toMatchObject({ status: 'reset', shownPercent: null, countdown: '--' });
    expect(toRow(quotaWindow('weekly', 30, null), NOW, false)).toMatchObject({ status: 'value', shownPercent: 70, countdown: '--' });
  });

  it('selects session then weekly, falling back to other windows', () => {
    const rows = [quotaWindow('other', 5, HOUR), quotaWindow('weekly', 10, HOUR), quotaWindow('session', 20, HOUR)].map((w) => toRow(w, NOW, true));
    expect(selectWidgetRows(rows, true).map((r) => r.kind)).toEqual(['session', 'weekly']);
    expect(selectWidgetRows(rows, false).map((r) => r.kind)).toEqual(['session']);
    expect(selectWidgetRows(rows.slice(0, 1), false).map((r) => r.tag)).toEqual(['1H']);
    expect(tagForWindow('other', 30)).toBe('30m');
    expect(tagForWindow('other', 1440)).toBe('1D');
    expect(tagForWindow('other', null)).toBe('--');
  });

  it('agy: the Argon weekly limit leads the popup and takes the first taskbar row (agy 1.4.7, 26.10.25)', () => {
    const labelled = (kind: 'session' | 'weekly', used: number, label: string) => ({ ...quotaWindow(kind, used, HOUR), label });
    const snapshot = usage('ag', { provider: 'antigravity', source: 'antigravity-cli-usage', windows: [
      labelled('session', 0, 'Gemini Models'), labelled('weekly', 0, 'Gemini Models'),
      labelled('session', 0, 'Claude and GPT models'), labelled('weekly', 0, 'Claude and GPT models'),
      labelled('weekly', 20.34, 'Gemini 4 Argon'),
    ] });
    const view = buildAccountView(account({ id: 'ag', provider: 'antigravity', label: 'AG' }), snapshot, DEFAULT_SETTINGS, NOW);
    expect(view.windows[0]?.label).toBe('Gemini 4 Argon');
    expect(view.rows.map((row) => [row.tag, row.label])).toEqual([['AR', 'Gemini 4 Argon'], ['5H', 'Gemini Models']]);
    const ctx = { t: createTranslator('en'), locale: 'en' as const, settings: DEFAULT_SETTINGS, theme: themeTokens(), now: NOW };
    expect(itemTooltip(view, ctx)).toContain('AG | Weekly Limit (Gemini 4 Argon): 80% left');
    // Without an Argon group (older agy, Ultra plans) nothing changes.
    const plain = buildAccountView(account({ id: 'ag', provider: 'antigravity' }),
      usage('ag', { provider: 'antigravity', windows: [labelled('session', 0, 'Gemini Models'), labelled('weekly', 0, 'Gemini Models')] }),
      DEFAULT_SETTINGS, NOW);
    expect(plain.rows.map((row) => row.tag)).toEqual(['5H', 'WK']);
  });

  it('extra usage: purchased credits and on-demand in dollars, Codex credits as a count, nothing invented', () => {
    const t = createTranslator('en');
    expect(extraUsageParts(t, { prepaidCents: 4638 })).toEqual(['Purchased credits $46.38 left']);
    expect(extraUsageParts(t, { prepaidCents: 0, onDemandUsedCents: 0, onDemandCapCents: 0 }))
      .toEqual(['Purchased credits $0.00 left', 'On-demand off']);
    expect(extraUsageParts(t, { onDemandUsedCents: 120, onDemandCapCents: 5000 })).toEqual(['On-demand $1.20 of $50.00']);
    expect(extraUsageParts(t, { credits: { balance: 12.5, unlimited: false } })).toEqual(['12.5 credits']);
    expect(extraUsageParts(t, { credits: { balance: null, unlimited: true } })).toEqual(['Unlimited credits']);
    expect(extraUsageParts(t, undefined)).toEqual([]);
    const snapshot = usage('g', { provider: 'grok', source: 'grok-acp', windows: [quotaWindow('weekly', 100, HOUR)],
      extraUsage: { prepaidCents: 4638 } });
    const view = buildAccountView(account({ id: 'g', provider: 'grok', label: 'G' }), snapshot, DEFAULT_SETTINGS, NOW);
    const ctx = { t, locale: 'en' as const, settings: DEFAULT_SETTINGS, theme: themeTokens(), now: NOW };
    expect(itemTooltip(view, ctx)).toContain('Purchased credits $46.38 left');
  });
});

describe('helpers', () => {
  it('pickLocale: explicit wins, auto uses main then navigator', () => {
    expect(pickLocale('en', 'ko', 'ko-KR')).toBe('en');
    expect(pickLocale('auto', 'ko', 'en-US')).toBe('ko');
    expect(pickLocale('auto', undefined, 'ko-KR')).toBe('ko');
    expect(pickLocale('auto', 'xx', 'fr-FR')).toBe('en');
  });

  it('relative time uses Intl in both locales', () => {
    expect(relativeTimeText('en', NOW - 5 * 60_000, NOW)).toBe('5 minutes ago');
    expect(relativeTimeText('ko', NOW - 5 * 60_000, NOW)).toBe('5분 전');
    expect(relativeTimeText('en', NOW - 10_000, NOW)).toBe('now');
  });

  it('accent is validated and gets a readable foreground', () => {
    expect(safeAccent('red; background:url(x)')).toBe('#0078d4');
    expect(accentForeground('#0078d4')).toBe('#ffffff');
    expect(accentForeground('#ffb900')).toBe('#000000');
  });
});

import { describe, expect, it } from 'vitest';
import { DEFAULT_SETTINGS } from '../../shared/settings';
import { relativeTimeText } from './format';
import { pickLocale } from './locale';
import { buildAccountView, selectWidgetRows, tagForWindow, toRow } from './model';
import { HOUR, NOW, account, quotaWindow, usage } from './testing/fixtures';
import { accentForeground, safeAccent } from './theme';

describe('view model', () => {
  it('missing snapshot is loading, logged-out or cli error by login state', () => {
    const settings = { ...DEFAULT_SETTINGS };
    expect(buildAccountView(account({ id: 'a' }), null, settings, NOW).state).toBe('loading');
    expect(buildAccountView(account({ id: 'a', loginState: 'logged-out' }), null, settings, NOW).state).toBe('logged-out');
    const cli = buildAccountView(account({ id: 'a', loginState: 'cli-missing' }), null, settings, NOW);
    expect([cli.state, cli.errorCode]).toEqual(['error', 'cli-not-found']);
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

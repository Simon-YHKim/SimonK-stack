import { describe, expect, it } from 'vitest';
import { createTranslator } from '../../../shared/i18n';
import { THEME_IDS, type Settings, type ThemeId } from '../../../shared/settings';
import type { AccountDTO, UsageSnapshot, UsageState } from '../../../shared/types';
import { buildAccountView, type RenderContext } from '../model';
import { HOUR, NOW, account, appState, quotaWindow, usage } from '../testing/fixtures';
import { ROW_GLYPHS, STATUS_GLYPHS, renderWidgetItem } from './themes';

function ctx(theme: ThemeId, settings: Partial<Settings> = {}): RenderContext {
  const state = appState({ settings: { theme, ...settings } });
  return { t: createTranslator('en'), locale: 'en', settings: state.settings, theme: state.theme, now: NOW };
}

function render(theme: ThemeId, snapshot: UsageSnapshot | null, settings: Partial<Settings> = {}, dto?: AccountDTO): HTMLElement {
  const c = ctx(theme, settings);
  const acc = dto ?? account({ id: 'a1', label: 'Work' });
  return renderWidgetItem(buildAccountView(acc, snapshot, c.settings, NOW), c);
}

const PERCENT_SELECTOR = '.percent, .percent-mono, .quota-val, .quota-val-sub, .w-pct';

const STATE_SNAPSHOTS: Record<UsageState, UsageSnapshot> = {
  ok: usage('a1'),
  stale: usage('a1', { measuredAt: NOW - 20 * 60_000, lastSuccessAt: NOW - 20 * 60_000 }),
  loading: usage('a1', { state: 'loading', windows: [], measuredAt: null, lastSuccessAt: null }),
  // Error keeps last measured windows (applyFetchFailure); the widget must still not show them as current.
  error: usage('a1', { state: 'error', errorCode: 'timeout', measuredAt: NOW - 10 * 60_000 }),
  unavailable: usage('a1', { state: 'unavailable', windows: [], errorCode: 'quota-unavailable', measuredAt: null }),
  'logged-out': usage('a1', { state: 'logged-out', windows: [], measuredAt: null }),
  reset: usage('a1', {
    windows: [quotaWindow('session', 40, -60_000), quotaWindow('weekly', 70, -1000)],
  }),
};

describe.each(THEME_IDS)('widget theme %s', (theme) => {
  it('ok: shows measured left% and countdown', () => {
    const item = render(theme, STATE_SNAPSHOTS.ok);
    expect(item.dataset.state).toBe('ok');
    const values = [...item.querySelectorAll(PERCENT_SELECTOR)].map((el) => el.textContent);
    expect(values).toEqual(['75%', '10%']);
    expect(item.textContent).toContain('2h 07m');
    expect(item.getAttribute('title')).toBe('Work | 5H: 75% left (2h 07m) | Weekly: 10% left (4d 0h)');
  });

  it('ok with showUsedPercent shows used%', () => {
    const item = render(theme, STATE_SNAPSHOTS.ok, { showUsedPercent: true });
    expect([...item.querySelectorAll(PERCENT_SELECTOR)].map((el) => el.textContent)).toEqual(['25%', '90%']);
  });

  it('stale: values dimmed and tooltip names the last measurement', () => {
    const item = render(theme, STATE_SNAPSHOTS.stale);
    expect(item.dataset.state).toBe('stale');
    expect(item.classList.contains('is-stale')).toBe(true);
    expect(item.getAttribute('title')).toContain('Stale | Last measured 20 minutes ago');
  });

  it.each(['loading', 'unavailable', 'logged-out'] as const)('%s: marker only, never a number', (state) => {
    const item = render(theme, STATE_SNAPSHOTS[state]);
    expect(item.dataset.state).toBe(state);
    expect(item.classList.contains('is-status')).toBe(true);
    expect(item.textContent).not.toMatch(/\d/);
    expect(item.querySelectorAll(PERCENT_SELECTOR)).toHaveLength(0);
    expect(item.querySelector('.state-mark')?.textContent).toBe(STATUS_GLYPHS[state]);
  });

  it('error keeps the last measured values, dimmed, with the failure marker (P-02)', () => {
    const item = render(theme, STATE_SNAPSHOTS.error);
    expect(item.dataset.state).toBe('error');
    expect(item.classList.contains('is-error')).toBe(true);
    expect(item.classList.contains('is-status')).toBe(false);
    expect([...item.querySelectorAll(PERCENT_SELECTOR)].map((el) => el.textContent)).toEqual(['75%', '10%']);
    expect(item.querySelector('.state-mark')?.textContent).toBe(STATUS_GLYPHS.error);
  });

  it('error without an earlier measurement is a marker only', () => {
    const item = render(theme, usage('a1', { state: 'error', errorCode: 'timeout', windows: [], measuredAt: null, lastSuccessAt: null }));
    expect(item.classList.contains('is-status')).toBe(true);
    expect(item.textContent).not.toMatch(/\d/);
    expect(item.querySelector('.state-mark')?.textContent).toBe(STATUS_GLYPHS.error);
  });

  it('error and unavailable tooltips give the reason', () => {
    expect(render(theme, STATE_SNAPSHOTS.error).getAttribute('title')).toBe(
      'Work | Failed | Timed out | Last measured 10 minutes ago',
    );
    expect(render(theme, STATE_SNAPSHOTS.unavailable).getAttribute('title')).toBe(
      'Work | Unavailable | This account does not report usage limits',
    );
    expect(render(theme, STATE_SNAPSHOTS['logged-out']).getAttribute('title')).toBe('Work | Sign-in required');
  });

  it('reset: windows started fresh show a reset marker, no percentage', () => {
    const item = render(theme, STATE_SNAPSHOTS.reset);
    expect(item.dataset.state).toBe('reset');
    const values = [...item.querySelectorAll(PERCENT_SELECTOR)].map((el) => el.textContent);
    expect(values.length).toBeGreaterThan(0);
    expect(values.every((v) => v === ROW_GLYPHS.reset)).toBe(true);
    expect(item.textContent).not.toContain('%');
    expect(item.getAttribute('title')).toContain('Reset (awaiting new reading)');
  });

  it('renders every state distinctly', () => {
    const signatures = (Object.keys(STATE_SNAPSHOTS) as UsageState[]).map((state) => {
      const item = render(theme, STATE_SNAPSHOTS[state]);
      return `${item.dataset.state}|${item.className}|${item.querySelector('.state-mark')?.textContent ?? ''}`;
    });
    expect(new Set(signatures).size).toBe(signatures.length);
  });

  it('unknown percent inside an ok snapshot is a dash, not 0%', () => {
    const item = render(theme, usage('a1', { windows: [quotaWindow('session', null, HOUR)] }));
    const values = [...item.querySelectorAll(PERCENT_SELECTOR)].map((el) => el.textContent);
    expect(values).toEqual([ROW_GLYPHS.unknown]);
    expect(item.textContent).not.toMatch(/\d%/);
    expect(item.querySelector('.ring-arc')).toBeNull();
    expect(item.getAttribute('title')).toContain('Unknown');
  });

  it('respects showWeeklyLimit', () => {
    const item = render(theme, STATE_SNAPSHOTS.ok, { showWeeklyLimit: false });
    expect(item.querySelectorAll(PERCENT_SELECTOR)).toHaveLength(1);
    expect(item.getAttribute('title')).toBe('Work | 75% left (2h 07m)');
    if (theme === '1c') expect(item.querySelectorAll('circle')).toHaveLength(2);
    if (theme === '1d') expect(item.querySelector('.sub-line')).toBeNull();
  });

  it('keeps a weekly-only limit visible even when weekly display is off', () => {
    const grok = account({ id: 'g1', provider: 'grok', label: 'Home' });
    const item = render(
      theme,
      usage('g1', { provider: 'grok', source: 'grok-acp', windows: [quotaWindow('weekly', 40, 3 * 24 * HOUR)] }),
      { showWeeklyLimit: false },
      grok,
    );
    expect([...item.querySelectorAll(PERCENT_SELECTOR)].map((el) => el.textContent)).toEqual(['60%']);
  });

  it('monochrome applies to icons and value colors', () => {
    const item = render(theme, STATE_SNAPSHOTS.ok, { iconStyle: 'monochrome' });
    const mono = item.querySelector('.ai-brand-icon, .ring-center-icon');
    expect(mono?.classList.contains('is-mono')).toBe(true);
    if (theme === 'windows') {
      expect([...item.querySelectorAll('.w-row')].map((row) => row.getAttribute('data-level'))).toEqual(['mono', 'mono']);
    } else {
      const first = item.querySelector<HTMLElement>(PERCENT_SELECTOR);
      expect(first?.style.color.toLowerCase()).toMatch(/d1d5db|209, 213, 219/);
    }
  });

  it('renders an untrusted label as text', () => {
    const evil = '<img src=x onerror=alert(1)>';
    const item = render(theme, STATE_SNAPSHOTS.ok, {}, account({ id: 'a1', label: evil }));
    expect(item.querySelector('[onerror]')).toBeNull();
    expect(item.querySelector('img[src="x"]')).toBeNull();
    expect(item.getAttribute('title')).toContain(evil);
  });
});

describe('v1 color thresholds', () => {
  it('uses 85/60 on used percent regardless of display mode', () => {
    const item = render('1b', usage('a1', { windows: [quotaWindow('session', 85, HOUR), quotaWindow('weekly', 60, HOUR)] }));
    const [first, second] = [...item.querySelectorAll<HTMLElement>('.percent-mono')];
    expect(first?.style.color.toLowerCase()).toMatch(/f43f5e|244, 63, 94/);
    expect(second?.style.color.toLowerCase()).toMatch(/f97316|249, 115, 22/);
    const low = render('1b', usage('a1', { windows: [quotaWindow('session', 59, HOUR)] }));
    expect(low.querySelector<HTMLElement>('.percent-mono')?.style.color.toLowerCase()).toMatch(/10b981|16, 185, 129/);
  });

  it('1b segments follow the displayed value (v1 z())', () => {
    const item = render('1b', usage('a1', { windows: [quotaWindow('session', 25, HOUR)] }));
    expect(item.querySelectorAll('.segment-rect[data-on="1"]')).toHaveLength(8);
  });

  it('colorByUsage off uses the provider brand for the first row', () => {
    const item = render('1a', STATE_SNAPSHOTS.ok, { colorByUsage: false });
    expect(item.querySelector<HTMLElement>('.percent')?.style.color.toLowerCase()).toMatch(/6366f1|99, 102, 241/);
  });
});

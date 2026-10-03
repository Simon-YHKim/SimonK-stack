import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { AppStateSnapshot } from '../../../shared/types';
import { FakeApi, NOW, account, appState, flush, quotaWindow, usage, type AppStateOverrides } from '../testing/fixtures';
import { REFRESH_COOLDOWN_MS, TOGGLE_DEBOUNCE_MS, WidgetApp } from './widget-app';

function withAccounts(overrides: AppStateOverrides = {}): AppStateSnapshot {
  return appState({
    accounts: [account({ id: 'a1', label: 'Work', order: 0 }), account({ id: 'a2', label: 'Home', order: 1, provider: 'claude' })],
    usage: [usage('a1'), usage('a2', { provider: 'claude', source: 'claude-statusline' })],
    ...overrides,
  });
}

function setup(state: AppStateSnapshot, size = { width: 200, height: 30 }) {
  const api = new FakeApi();
  const root = document.createElement('div');
  document.body.replaceChildren(root);
  const app = new WidgetApp({
    api,
    root,
    measure: () => size,
    schedule: (fn) => fn(),
    navigatorLanguage: 'en-US',
  });
  const rendered = app.update(state);
  return { api, root, app, rendered };
}

describe('WidgetApp', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(NOW);
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('empty state: dot opens the accounts tab and hides the refresh button', () => {
    const { api, app, rendered } = setup(appState());
    expect(rendered).toBe('empty');
    expect(app.bar.classList.contains('is-empty')).toBe(true);
    expect(app.refreshButton.hidden).toBe(true);
    expect(app.main.getAttribute('aria-label')).toBe('No AI account connected (click to open Accounts)');
    app.main.click();
    expect(api.callsTo('window:show-popup')).toEqual([{ tab: 'accounts' }]);
  });

  it.each(['windows', '1a', '1b', '1c', '1d'] as const)(
    'flashes only the changed displayed percentage in the %s theme', (theme) => {
      const state = (sessionUsed: number, weeklyUsed = 90) => appState({
        accounts: [account({ id: 'a1' })],
        usage: [usage('a1', { windows: [quotaWindow('session', sessionUsed, 2 * 3_600_000),
          quotaWindow('weekly', weeklyUsed, 4 * 86_400_000)] })],
        settings: { theme },
      });
      const { app } = setup(state(25));
      expect(app.main.querySelectorAll('[data-value-flash]')).toHaveLength(0);

      app.update(state(26));
      const rows = app.main.querySelectorAll('.account-item [data-status]');
      const firstTone = rows[0]?.getAttribute('data-value-flash');
      expect(firstTone).toMatch(/^(sky|mint|violet)$/);
      expect(rows[1]?.hasAttribute('data-value-flash')).toBe(false);

      app.update(state(26));
      expect(app.main.querySelector('.account-item [data-status]')).toBe(rows[0]);
      expect(rows[0]?.getAttribute('data-value-flash')).toBe(firstTone);
      app.update(state(27));
      const secondTone = app.main.querySelector('.account-item [data-status]')?.getAttribute('data-value-flash');
      expect(secondTone).toMatch(/^(sky|mint|violet)$/);
      expect(secondTone).not.toBe(firstTone);
      vi.advanceTimersByTime(1_500);
      expect(app.main.querySelectorAll('[data-value-flash]')).toHaveLength(0);
    },
  );

  it('does not flash for a smaller-than-displayed change, view-mode switch, or failed fetch', () => {
    const state = (used: number, showUsedPercent = false, status: 'ok' | 'error' = 'ok') => appState({
      accounts: [account({ id: 'a1' })],
      usage: [usage('a1', { state: status, windows: [quotaWindow('session', used, 2 * 3_600_000)] })],
      settings: { showUsedPercent },
    });
    const { app } = setup(state(25));
    app.update(state(25.1));
    expect(app.main.querySelectorAll('[data-value-flash]')).toHaveLength(0);
    app.update(state(25.1, true));
    expect(app.main.querySelectorAll('[data-value-flash]')).toHaveLength(0);
    app.update(state(25.1, true, 'error'));
    expect(app.main.querySelectorAll('[data-value-flash]')).toHaveLength(0);
  });

  it('shows a separately labelled manual Grok Bot balance and opens its usage card', () => {
    const { api, app } = setup(appState({ settings: { grokBotUsedPercent: 68, grokBotRecordedAt: NOW } }));
    const item = app.main.querySelector('.grok-bot-item') as HTMLElement;
    expect(item.textContent).toContain('32% left');
    expect(item.textContent).toContain('Manual entry');
    expect(app.refreshButton.hidden).toBe(true);
    app.main.click();
    expect(api.callsTo('window:show-popup')).toEqual([{ tab: 'usage' }]);
  });

  it('adds the Grok Bot reset countdown and marks a used-up weekly allowance', () => {
    const resetAt = NOW + (26 * 60 + 5) * 60_000;
    const { app } = setup(appState({ settings: { grokBotUsedPercent: 100, grokBotRecordedAt: NOW, grokBotResetAt: resetAt } }));
    const item = app.main.querySelector('.grok-bot-item') as HTMLElement;
    expect(item.querySelector('.grok-bot-widget-reset')?.textContent).toBe('1d 2h');
    expect(item.classList.contains('is-exhausted')).toBe(true);
    expect(item.getAttribute('title')).toContain('Resets in 1d 2h');
    expect(item.getAttribute('title')).toContain('on-demand');
  });

  it('shows a signed-in Grok Bot weekly balance without any manual entry', () => {
    const { app, api } = setup(appState({ grokBotAuto: { state: 'ok', usedPercent: 41, resetsAt: NOW + 2 * 86_400_000,
      measuredAt: NOW } }));
    const item = app.main.querySelector('.grok-bot-item') as HTMLElement;
    expect(item.textContent).toContain('59% left');
    expect(item.textContent).toContain('Unofficial auto');
    expect(item.title).toContain('Reset');
    expect(app.refreshButton.hidden).toBe(false);
    app.refreshButton.click();
    expect(api.callsTo('usage:refresh-now')).toEqual([{ accountId: null }]);
  });

  it('flashes a standalone Grok Bot percentage when its weekly reading changes', () => {
    const state = (usedPercent: number) => appState({ grokBotAuto: { state: 'ok', usedPercent,
      resetsAt: NOW + 2 * 86_400_000, measuredAt: NOW } });
    const { app } = setup(state(41));
    expect(app.main.querySelectorAll('[data-value-flash]')).toHaveLength(0);
    app.update(state(42));
    expect(app.main.querySelector('.grok-bot-widget-value')?.getAttribute('data-value-flash'))
      .toMatch(/^(sky|mint|violet)$/);
  });

  it('keeps a Bot-only widget visible when an automatic session expires or disappears', () => {
    const { app } = setup(appState({ grokBotAuto: { state: 'ok', usedPercent: 41,
      resetsAt: NOW + 2 * 86_400_000, measuredAt: NOW } }));
    app.update(appState({ grokBotAuto: { state: 'login-expired', usedPercent: null,
      resetsAt: null, measuredAt: NOW + 1_000 } }));
    expect(app.main.querySelector('.grok-bot-item')?.textContent).toContain('Sign in again in the Grok Bot app');
    expect(app.main.querySelector('.grok-bot-item')?.textContent).toContain('—');
    expect(app.refreshButton.hidden).toBe(false);

    app.update(appState({ grokBotAuto: { state: 'unavailable', usedPercent: null,
      resetsAt: null, measuredAt: NOW + 2_000 } }));
    expect(app.main.querySelector('.grok-bot-item')?.textContent).toContain('Grok Bot sign-in was not found');
    expect(app.bar.classList.contains('is-empty')).toBe(false);
    expect(app.refreshButton.hidden).toBe(false);
  });

  it('does not show a Bot row for a first-time user without a Grok Bot session', () => {
    const { app, rendered } = setup(appState({ grokBotAuto: { state: 'unavailable', usedPercent: null,
      resetsAt: null, measuredAt: NOW } }));
    expect(rendered).toBe('empty');
    expect(app.main.querySelector('.grok-bot-item')).toBeNull();
  });

  it.each(['windows', '1a', '1b', '1c', '1d'] as const)('stacks Grok WK and Bot rows in one %s item', (theme) => {
    const grok = account({ id: 'g1', provider: 'grok', label: 'Grok' });
    const base = { accounts: [grok], usage: [usage('g1', { provider: 'grok', source: 'grok-acp',
      windows: [quotaWindow('weekly', 37, 3 * 86_400_000)] })], settings: { theme } };
    const { app } = setup(appState({ ...base, grokBotAuto: { state: 'ok', usedPercent: 41,
      resetsAt: NOW + 2 * 86_400_000, measuredAt: NOW } }));
    const grokItem = app.main.querySelector('.account-item[data-provider="grok"]') as HTMLElement;
    expect(app.main.querySelectorAll(':scope > .account-item')).toHaveLength(1);
    expect(grokItem.querySelectorAll('[data-status]')).toHaveLength(2);
    expect(grokItem.textContent).toContain('WK');
    expect(grokItem.textContent).toContain('Bot');
    expect(grokItem.textContent).toContain('63% left');
    expect(grokItem.textContent).toContain('59% left');
    expect(grokItem.title).toContain('Grok Bot');
    expect(app.main.querySelector('.grok-bot-item')).toBeNull();
    app.update(appState({ ...base, grokBotAuto: { state: 'ok', usedPercent: 50,
      resetsAt: NOW + 2 * 86_400_000, measuredAt: NOW + 1000 } }));
    expect(app.main.querySelector('.account-item[data-provider="grok"]')?.textContent).toContain('50% left');
  });

  it('flashes only Bot when its percentage changes in a grouped Grok item', () => {
    const grok = account({ id: 'g1', provider: 'grok', label: 'Grok' });
    const state = (usedPercent: number) => appState({ accounts: [grok], usage: [usage('g1', {
      provider: 'grok', source: 'grok-acp', windows: [quotaWindow('weekly', 37, 3 * 86_400_000)],
    })], grokBotAuto: { state: 'ok', usedPercent, resetsAt: NOW + 2 * 86_400_000, measuredAt: NOW } });
    const { app } = setup(state(41));
    app.update(state(42));
    const rows = app.main.querySelectorAll('.account-item[data-provider="grok"] [data-status]');
    expect(rows).toHaveLength(2);
    expect(rows[0]?.hasAttribute('data-value-flash')).toBe(false);
    expect(rows[1]?.getAttribute('data-value-flash')).toMatch(/^(sky|mint|violet)$/);
  });

  it('keeps the grouped WK/Bot item and explains a failed Bot refresh', () => {
    const grok = account({ id: 'g1', provider: 'grok', label: 'Grok' });
    const base = { accounts: [grok], usage: [usage('g1', { provider: 'grok', source: 'grok-acp',
      windows: [quotaWindow('weekly', 37, 3 * 86_400_000)] })] };
    const { app } = setup(appState({ ...base, grokBotAuto: { state: 'ok', usedPercent: 41,
      resetsAt: NOW + 2 * 86_400_000, measuredAt: NOW } }));
    app.update(appState({ ...base, grokBotAuto: { state: 'error', usedPercent: null,
      resetsAt: null, measuredAt: NOW + 1_000 } }));
    const item = app.main.querySelector('.account-item[data-provider="grok"]') as HTMLElement;
    const rows = item.querySelectorAll('.w-row');
    expect(app.main.querySelectorAll(':scope > .account-item')).toHaveLength(1);
    expect(rows).toHaveLength(2);
    expect(rows[1]?.textContent).toContain('Bot');
    expect(rows[1]?.textContent).toContain('—');
    expect(item.title).toContain('Automatic refresh failed');
  });

  it('keeps Bot readable when the Grok CLI is signed out, and marks only a stale manual Bot row', () => {
    const grok = account({ id: 'g1', provider: 'grok', label: 'Grok', loginState: 'logged-out' });
    const { app } = setup(appState({ accounts: [grok], settings: {
      grokBotUsedPercent: 41, grokBotRecordedAt: NOW - 2 * 86_400_000,
    } }));
    const grokItem = app.main.querySelector('.account-item[data-provider="grok"]') as HTMLElement;
    const rows = grokItem.querySelectorAll('.w-row');
    expect(rows).toHaveLength(2);
    expect(rows[0]?.textContent).toContain('WK');
    expect(rows[0]?.textContent).toContain('—');
    expect(rows[1]?.textContent).toContain('Bot');
    expect(rows[1]?.textContent).toContain('59% left');
    expect(rows[0]?.getAttribute('data-stale')).toBeNull();
    expect(rows[1]?.getAttribute('data-stale')).toBe('true');
    expect(grokItem.title).toContain('Sign-in required');
  });

  it('shows Grok WK with Bot even when the global weekly-row setting is off', () => {
    const grok = account({ id: 'g1', provider: 'grok', label: 'Grok' });
    const { app } = setup(appState({ accounts: [grok], usage: [usage('g1', { provider: 'grok',
      windows: [quotaWindow('session', 20, 2 * 3_600_000), quotaWindow('weekly', 37, 3 * 86_400_000)],
    })], settings: { showWeeklyLimit: false }, grokBotAuto: {
      state: 'ok', usedPercent: 41, resetsAt: NOW + 2 * 86_400_000, measuredAt: NOW,
    } }));
    const rows = app.main.querySelectorAll('.account-item[data-provider="grok"] .w-row');
    expect([...rows].map((row) => row.querySelector('.w-tag')?.textContent)).toEqual(['WK', 'Bot']);
    expect(rows[0]?.textContent).toContain('63% left');
  });

  it('keeps the manual Bot reset and on-demand warning when grouped with Grok', () => {
    const grok = account({ id: 'g1', provider: 'grok', label: 'Grok' });
    const resetAt = NOW + (26 * 60 + 5) * 60_000;
    const { app } = setup(appState({ accounts: [grok], usage: [usage('g1', { provider: 'grok',
      windows: [quotaWindow('weekly', 37, 3 * 86_400_000)],
    })], settings: { grokBotUsedPercent: 100, grokBotRecordedAt: NOW, grokBotResetAt: resetAt } }));
    const grokItem = app.main.querySelector('.account-item[data-provider="grok"]') as HTMLElement;
    const botRow = grokItem.querySelectorAll('.w-row')[1];
    expect(botRow?.querySelector('.w-tag')?.textContent).toBe('Bot');
    expect(botRow?.textContent).toContain('0% left');
    expect(botRow?.textContent).toContain('1d 2h');
    expect(grokItem.title).toContain('on-demand');
  });

  it('clicking the bar toggles the popup with a 300ms debounce', () => {
    const { api, app } = setup(withAccounts());
    app.main.click();
    app.bar.click();
    expect(api.callsTo('window:toggle-popup')).toHaveLength(1);
    vi.advanceTimersByTime(TOGGLE_DEBOUNCE_MS);
    app.main.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    expect(api.callsTo('window:toggle-popup')).toHaveLength(2);
  });

  it('refresh button refreshes without toggling the popup and coalesces repeated clicks', async () => {
    const { api, app } = setup(withAccounts());
    const button = app.refreshButton;
    expect(button.tagName).toBe('BUTTON');
    expect(button.getAttribute('type')).toBe('button');
    expect(button.getAttribute('aria-label')).toBe('Refresh now');
    expect(button.getAttribute('aria-disabled')).toBe('false');

    button.click();
    expect(api.callsTo('usage:refresh-now')).toEqual([{ accountId: null }]);
    expect(api.callsTo('window:toggle-popup')).toHaveLength(0);
    expect(button.getAttribute('aria-disabled')).toBe('true');
    expect(button.classList.contains('is-spinning')).toBe(true);

    await flush();
    expect(button.classList.contains('is-spinning')).toBe(false);
    button.click();
    expect(api.callsTo('usage:refresh-now')).toHaveLength(1);
    expect(button.getAttribute('aria-disabled')).toBe('true');

    vi.advanceTimersByTime(REFRESH_COOLDOWN_MS);
    expect(button.getAttribute('aria-disabled')).toBe('false');
    button.click();
    expect(api.callsTo('usage:refresh-now')).toHaveLength(2);
  });

  it('spins and is inert while the scheduler reports a refresh in flight', () => {
    const { api, app } = setup(withAccounts({ refresh: { inFlight: true, accountIds: ['a1'], lastRunAt: null, nextRunAt: null } }));
    expect(app.refreshButton.classList.contains('is-spinning')).toBe(true);
    expect(app.refreshButton.getAttribute('aria-busy')).toBe('true');
    expect(app.refreshButton.getAttribute('aria-label')).toBe('Refreshing...');
    app.refreshButton.click();
    expect(api.callsTo('usage:refresh-now')).toHaveLength(0);
    app.update(withAccounts());
    expect(app.refreshButton.classList.contains('is-spinning')).toBe(false);
  });

  it('keeps the refresh button element (and its focus) across state updates', () => {
    const { app } = setup(withAccounts());
    const button = app.refreshButton;
    button.focus();
    app.update(withAccounts({ usage: [usage('a1', { windows: [] , state: 'unavailable' })] }));
    expect(app.bar.contains(button)).toBe(true);
    expect(document.activeElement).toBe(button);
  });

  it('puts an actionable model notice only on its vendor icon', () => {
    const state = withAccounts({ modelNotices: [{
      id: 'released:codex:gpt7sol', provider: 'codex', model: 'GPT-7 Sol', status: 'released',
      releaseDate: null, url: 'https://openai.com/index/gpt-7-sol', observedAt: NOW,
    }] });
    const { api, app } = setup(state);
    const codexBadge = app.main.querySelector('.account-item[data-provider="codex"] .model-notice-badge');
    expect(codexBadge?.getAttribute('title')).toContain('Try it');
    expect(app.main.querySelector('.account-item[data-provider="claude"] .model-notice-badge')).toBeNull();
    (codexBadge as HTMLButtonElement).click();
    expect(api.callsTo('model-notice:open')).toEqual([{ provider: 'codex' }]);
    expect(api.callsTo('window:toggle-popup')).toHaveLength(0);
    codexBadge?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    expect(api.callsTo('window:toggle-popup')).toHaveLength(0);
  });

  it('requests a resize only when the measured size changes', () => {
    const { api, app } = setup(withAccounts());
    expect(api.callsTo('window:resize-widget')).toEqual([{ width: 204, height: 34 }]);
    app.update(withAccounts());
    expect(api.callsTo('window:resize-widget')).toHaveLength(1);
  });

  it('asks for the width the items need when the window clips them (CR-06)', () => {
    const api = new FakeApi();
    const root = document.createElement('div');
    document.body.replaceChildren(root);
    const app = new WidgetApp({ api, root, measure: () => ({ width: 300, height: 30 }), schedule: (fn) => fn(), navigatorLanguage: 'en-US' });
    Object.defineProperty(app.main, 'scrollWidth', { configurable: true, value: 700 });
    Object.defineProperty(app.main, 'clientWidth', { configurable: true, value: 260 });
    app.update(withAccounts());
    expect(api.callsTo('window:resize-widget')).toEqual([{ width: 300 + 440 + 4, height: 34 }]);
    expect(app.bar.lastElementChild?.previousElementSibling).toBe(app.refreshButton);
  });

  it('renders enabled accounts in order with unique ids', () => {
    const state = withAccounts({
      accounts: [
        account({ id: 'a2', label: 'Home', order: 1, provider: 'claude' }),
        account({ id: 'a1', label: 'Work', order: 0 }),
        account({ id: 'a3', label: 'Off', order: 2, enabled: false }),
      ],
    });
    const { root } = setup({ ...state, settings: { ...state.settings, theme: '1c' } });
    expect([...root.querySelectorAll('.account-item')].map((el) => el.getAttribute('data-account-id'))).toEqual(['a1', 'a2']);
    const ids = [...document.querySelectorAll('[id]')].map((el) => el.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('applies taskbar scheme, skin and card alpha', () => {
    const state = withAccounts({ settings: { alphaPercent: 40, showCardBackground: false } });
    const { app } = setup({ ...state, theme: { ...state.theme, scheme: 'light', taskbarScheme: 'dark', accent: '#FFB900' } });
    const html = document.documentElement;
    expect(html.dataset.scheme).toBe('dark');
    expect(html.dataset.skin).toBe('windows');
    expect(html.style.getPropertyValue('--accent')).toBe('#ffb900');
    expect(html.style.getPropertyValue('--accent-fg')).toBe('#000000');
    expect(app.bar.classList.contains('no-card-bg')).toBe(true);
    expect(app.bar.style.getPropertyValue('--bg-alpha')).toBe('0.4');
  });

  it('highlights only the account whose recent quota pace exceeds its earlier pace', () => {
    const { app, root } = setup(appState());
    const feed = (minute: number, used: number, otherUsed = 5) => {
      const at = NOW + minute * 60_000;
      vi.setSystemTime(at);
      app.update(appState({
        accounts: [account({ id: 'a1' }), account({ id: 'a2', order: 1 })],
        usage: [
          usage('a1', { windows: [quotaWindow('session', used, 5 * 3_600_000)], measuredAt: at, lastSuccessAt: at }),
          usage('a2', { windows: [quotaWindow('session', otherUsed, 5 * 3_600_000)], measuredAt: at, lastSuccessAt: at }),
        ],
      }));
    };
    for (const [minute, used] of [[0, 0], [15, 1], [30, 2], [45, 3], [60, 4], [65, 6]] as const) {
      feed(minute, used);
      expect(root.querySelector('.account-item.is-fast')).toBeNull();
    }
    feed(70, 8);
    expect(root.querySelectorAll('.account-item.is-fast')).toHaveLength(1);
    // The warning carries a shape cue of its own, not only a colour; the calm account has none.
    const mark = root.querySelector('.account-item[data-account-id="a1"] > .pace-mark');
    expect(mark?.getAttribute('aria-hidden')).toBe('true');
    expect(root.querySelectorAll('.pace-mark')).toHaveLength(1);
    feed(75, 10);
    expect(root.querySelectorAll('.account-item.is-fast')).toHaveLength(1);
    expect(root.querySelector('.account-item.is-fast')?.getAttribute('data-account-id')).toBe('a1');
    expect(root.querySelector('.account-item.is-fast')?.getAttribute('title')).toContain('Quota usage is rising faster');
    expect(app.main.getAttribute('aria-describedby')).toBe(app.bar.querySelector('.sr-only')?.id);
    expect(app.bar.querySelector('.sr-only')?.textContent).toContain('Quota usage is rising faster');

    feed(80, 1); // quota reset: old history must not trigger an alert
    expect(root.querySelector('.account-item.is-fast')).toBeNull();
    expect(root.querySelector('.pace-mark')).toBeNull();
  });

  it('keeps the fast-pace mark and the value-change cue on different elements', () => {
    const { app, root } = setup(appState());
    const feed = (minute: number, used: number, otherUsed: number) => {
      const at = NOW + minute * 60_000;
      vi.setSystemTime(at);
      app.update(appState({
        accounts: [account({ id: 'a1' }), account({ id: 'a2', order: 1 })],
        usage: [
          usage('a1', { windows: [quotaWindow('session', used, 5 * 3_600_000)], measuredAt: at, lastSuccessAt: at }),
          usage('a2', { windows: [quotaWindow('session', otherUsed, 5 * 3_600_000)], measuredAt: at, lastSuccessAt: at }),
        ],
      }));
    };
    feed(0, 2, 5);
    feed(5, 18, 6); // a1 bursts (fast + changed value), a2 only changes its value
    const fast = root.querySelector<HTMLElement>('.account-item[data-account-id="a1"]');
    const calm = root.querySelector<HTMLElement>('.account-item[data-account-id="a2"]');
    expect(fast?.classList.contains('is-fast')).toBe(true);
    expect(fast?.querySelectorAll(':scope > .pace-mark')).toHaveLength(1);
    expect(calm?.classList.contains('is-fast')).toBe(false);
    expect(calm?.querySelector('.pace-mark')).toBeNull();
    expect(calm?.querySelector('[data-status]')?.getAttribute('data-value-flash')).toMatch(/^(sky|mint|violet)$/);
    // The value cue lives on the row; the mark is a direct child of the item, outside every row.
    for (const row of root.querySelectorAll('[data-value-flash]')) expect(row.querySelector('.pace-mark')).toBeNull();
    vi.advanceTimersByTime(1_500);
    expect(root.querySelectorAll('[data-value-flash]')).toHaveLength(0);
    expect(fast?.querySelectorAll(':scope > .pace-mark')).toHaveLength(1);
  });

  it('does not infer a fast pace from stale or unknown quota readings', () => {
    const { app, root } = setup(appState());
    for (const minute of [0, 15, 30, 45, 60, 65, 70, 75]) {
      const at = NOW + minute * 60_000;
      vi.setSystemTime(at);
      app.update(appState({
        accounts: [account({ id: 'a1' })],
        usage: [usage('a1', {
          state: minute === 75 ? 'error' : 'ok',
          windows: [quotaWindow('session', minute === 75 ? 30 : null, 5 * 3_600_000)],
          measuredAt: at,
          lastSuccessAt: at,
        })],
      }));
    }
    expect(root.querySelector('.account-item.is-fast')).toBeNull();
  });

  it('ignores one delayed quota jump without a sustained increase', () => {
    const { app, root } = setup(appState());
    for (const [minute, used] of [[0, 0], [15, 1], [30, 2], [45, 3], [60, 4], [65, 12], [70, 12], [75, 12]] as const) {
      const at = NOW + minute * 60_000;
      vi.setSystemTime(at);
      app.update(appState({
        accounts: [account({ id: 'a1' })],
        usage: [usage('a1', {
          windows: [quotaWindow('session', used, 5 * 3_600_000)],
          measuredAt: at,
          lastSuccessAt: at,
        })],
      }));
      expect(root.querySelector('.account-item.is-fast')).toBeNull();
    }
  });

  it('alerts once for a rapid Grok weekly-credit burst and clears on reset', () => {
    const { app, root, api } = setup(appState());
    const feed = (minute: number, used: number) => {
      const at = NOW + minute * 60_000;
      vi.setSystemTime(at);
      app.update(appState({
        accounts: [account({ id: 'g1', provider: 'grok', label: 'Grok work' })],
        usage: [usage('g1', { provider: 'grok', source: 'grok-acp',
          windows: [quotaWindow('weekly', used, 7 * 24 * 3_600_000)], measuredAt: at, lastSuccessAt: at })],
      }));
    };
    feed(0, 2);
    expect(api.callsTo('window:show-pace-bubble')).toHaveLength(0);
    feed(5, 18);
    expect(root.querySelector('.account-item[data-account-id="g1"]')?.classList.contains('is-fast')).toBe(true);
    expect(api.callsTo('window:show-pace-bubble')).toEqual([{ accountId: 'g1', recent: 192, usual: null, locale: 'en' }]);
    feed(6, 18);
    expect(api.callsTo('window:show-pace-bubble')).toHaveLength(1);
    feed(8, 0);
    expect(root.querySelector('.account-item.is-fast')).toBeNull();
  });

  it('catches a Grok burst after a long idle history', () => {
    const { app, root, api } = setup(appState());
    for (let minute = 0; minute <= 31; minute += 1) {
      const at = NOW + minute * 60_000;
      vi.setSystemTime(at);
      app.update(appState({
        accounts: [account({ id: 'g1', provider: 'grok' })],
        usage: [usage('g1', { provider: 'grok', source: 'grok-acp',
          windows: [quotaWindow('weekly', minute === 31 ? 18 : 2, 7 * 24 * 3_600_000)], measuredAt: at, lastSuccessAt: at })],
      }));
    }
    expect(root.querySelector('.account-item[data-account-id="g1"]')?.classList.contains('is-fast')).toBe(true);
    expect(api.callsTo('window:show-pace-bubble')).toHaveLength(1);
  });
});

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
    feed(75, 10);
    expect(root.querySelectorAll('.account-item.is-fast')).toHaveLength(1);
    expect(root.querySelector('.account-item.is-fast')?.getAttribute('data-account-id')).toBe('a1');
    expect(root.querySelector('.account-item.is-fast')?.getAttribute('title')).toContain('Quota usage is rising faster');
    expect(app.main.getAttribute('aria-describedby')).toBe(app.bar.querySelector('.sr-only')?.id);
    expect(app.bar.querySelector('.sr-only')?.textContent).toContain('Quota usage is rising faster');

    feed(80, 1); // quota reset: old history must not trigger an alert
    expect(root.querySelector('.account-item.is-fast')).toBeNull();
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
});

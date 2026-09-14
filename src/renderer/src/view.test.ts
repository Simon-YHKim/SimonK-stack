import { describe, expect, it } from 'vitest';
import { DEFAULT_SETTINGS } from '../../shared/settings';
import type { AppStateSnapshot } from '../../shared/types';
import { parseViewFromSearch, renderView } from './view';

function snapshot(overrides: Partial<AppStateSnapshot> = {}): AppStateSnapshot {
  return {
    locale: 'en',
    settings: { ...DEFAULT_SETTINGS },
    accounts: [],
    usage: [],
    refresh: { inFlight: false, accountIds: [], lastRunAt: null, nextRunAt: null },
    theme: {
      scheme: 'light',
      taskbarScheme: 'dark',
      highContrast: false,
      accent: '#0078d4',
      reducedTransparency: false,
      effectiveMaterial: 'none',
    },
    cli: { claude: { state: 'unknown' }, codex: { state: 'unknown' }, grok: { state: 'unknown' } },
    ...overrides,
  };
}

describe('view', () => {
  it('parses the view query', () => {
    expect(parseViewFromSearch('?view=popup')).toBe('popup');
    expect(parseViewFromSearch('?view=admin')).toBe('widget');
    expect(parseViewFromSearch('')).toBe('widget');
  });

  it('widget empty state opens the accounts tab on click', () => {
    const root = document.createElement('div');
    let opened = 0;
    const kind = renderView(root, 'widget', snapshot(), { openAccounts: () => (opened += 1) });
    expect(kind).toBe('empty');
    const button = root.querySelector('button');
    expect(button?.textContent).toBe('No active accounts.');
    button?.click();
    expect(opened).toBe(1);
    expect(document.documentElement.dataset.scheme).toBe('dark');
  });

  it('popup lists enabled accounts in order using the locale', () => {
    const root = document.createElement('div');
    const state = snapshot({
      locale: 'ko',
      accounts: [
        { id: 'b', provider: 'grok', label: '<b>Home</b>', enabled: true, order: 2, loginState: 'logged-in' },
        { id: 'a', provider: 'codex', label: 'Work', enabled: true, order: 1, loginState: 'unknown' },
        { id: 'c', provider: 'claude', label: 'Off', enabled: false, order: 0, loginState: 'logged-out' },
      ],
    });
    expect(renderView(root, 'popup', state, { openAccounts: () => undefined })).toBe('accounts');
    const items = [...root.querySelectorAll('li')].map((li) => li.textContent);
    expect(items).toEqual(['Codex · Work', 'Grok · <b>Home</b>']);
    expect(root.querySelector('h1')?.textContent).toBe('AI 사용량');
    expect(document.documentElement.lang).toBe('ko');
  });
});

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { en } from '../../../shared/i18n/en';
import type { AppStateSnapshot, LoginEvent } from '../../../shared/types';
import { FakeApi, NOW, account, appState, flush, quotaWindow, usage } from '../testing/fixtures';
import { isValidPaste } from './login-panel';
import { PopupApp } from './popup-app';
import { PREVIEW_THROTTLE_MS, RANGE_COMMIT_DELAY_MS } from './settings-tab';

describe('isValidPaste', () => {
  it('requires one non-empty line within the IPC limit', () => {
    expect(isValidPaste(' abc#def ')).toBe(true);
    expect(isValidPaste('   ')).toBe(false);
    expect(isValidPaste('a\nb')).toBe(false);
    expect(isValidPaste('a\rb')).toBe(false);
    expect(isValidPaste('x'.repeat(4097))).toBe(false);
  });
});

function setup(state: AppStateSnapshot, api = new FakeApi()) {
  const root = document.createElement('div');
  document.body.replaceChildren(root);
  const app = new PopupApp({ api, root, now: () => NOW, navigatorLanguage: 'en-US' });
  app.update(state);
  return { api, root, app };
}

function loginEvent(api: FakeApi, accountId: string, sessionId: string, event: LoginEvent): void {
  api.emit('login:event', { accountId, sessionId, at: NOW, event });
}

function typeInto(input: HTMLInputElement, value: string): void {
  input.value = value;
  input.dispatchEvent(new Event('input', { bubbles: true }));
}

function submit(form: HTMLFormElement): void {
  form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
}

describe('PopupApp shell', () => {
  it('Esc hides the popup', () => {
    const { api } = setup(appState());
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    expect(api.callsTo('window:hide-popup').length).toBeGreaterThan(0);
  });

  it('popup:show from main selects the requested tab; null keeps the current one', () => {
    const { api, app } = setup(appState({ accounts: [account({ id: 'a1' })] }));
    api.emit('popup:show', { tab: 'accounts' });
    expect(app.getActiveTab()).toBe('accounts');
    api.emit('popup:show', { tab: null });
    expect(app.getActiveTab()).toBe('accounts');
  });

  it('every popup:show replays the entry animation and refreshes a visible accounts tab (P-01)', () => {
    const api = new FakeApi().reply('claude-bridge:status', () => ({
      ok: true,
      value: { installed: false, wrapsExistingCommand: false, targetAccountId: null, lastDataAt: null },
    }));
    const { app } = setup(appState({ accounts: [account({ id: 'a1' })] }), api);
    expect(app.popupRoot.classList.contains('is-entering')).toBe(false);
    api.emit('popup:show', { tab: 'accounts' });
    expect(app.popupRoot.classList.contains('is-entering')).toBe(true);
    expect(api.callsTo('claude-bridge:status')).toHaveLength(1);
    api.emit('popup:show', { tab: null });
    expect(app.getActiveTab()).toBe('accounts');
    expect(api.callsTo('claude-bridge:status')).toHaveLength(2);
  });

  it('popup:show without a tab opens the accounts tab while there are no accounts', () => {
    const { api, app } = setup(appState());
    api.emit('popup:show', { tab: null });
    expect(app.getActiveTab()).toBe('accounts');
    api.emit('popup:show', { tab: 'settings' });
    expect(app.getActiveTab()).toBe('settings');
  });

  it('tabs follow the ARIA tab pattern with arrow keys', () => {
    const { app } = setup(appState());
    expect(app.tabs.usage.getAttribute('aria-selected')).toBe('true');
    app.tabs.usage.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
    expect(app.getActiveTab()).toBe('accounts');
    expect(app.tabs.accounts.getAttribute('aria-selected')).toBe('true');
    expect(app.panels.accounts.hidden).toBe(false);
    expect(app.panels.usage.hidden).toBe(true);
    app.tabs.accounts.dispatchEvent(new KeyboardEvent('keydown', { key: 'End', bubbles: true }));
    expect(app.getActiveTab()).toBe('settings');
    app.tabs.settings.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
    expect(app.getActiveTab()).toBe('usage');
  });

  it('header badge counts enabled accounts; locale follows explicit language', () => {
    const state = appState({
      accounts: [account({ id: 'a1' }), account({ id: 'a2', enabled: false })],
      settings: { language: 'ko' },
    });
    const { root } = setup(state);
    expect(root.querySelector('.popup-title-badge')?.textContent).toBe('활성 계정 1개');
    expect(document.documentElement.lang).toBe('ko');
  });
});

describe('Usage tab', () => {
  it('offers one Codex reset only for a fresh measured count and routes use through main', async () => {
    const api = new FakeApi().reply('usage:redeem-reset-credit', () => ({ ok: true, value: 'cancelled' }));
    const state = appState({ accounts: [account({ id: 'a1', provider: 'codex' })],
      usage: [usage('a1', { resetCreditsAvailable: 2 })] });
    const { root, app } = setup(state, api);
    expect(root.querySelector('.reset-credit-row')?.textContent).toContain('2 Codex banked resets');
    (root.querySelector('.reset-credit-button') as HTMLButtonElement).click();
    await flush();
    expect(api.callsTo('usage:redeem-reset-credit')).toEqual([{ accountId: 'a1' }]);
    expect(root.textContent).toContain('Reset use cancelled.');
    (root.querySelector('.reset-credit-link') as HTMLButtonElement).click();
    expect(api.callsTo('shell:open-external')).toContainEqual({ kind: 'link', key: 'codex-usage' });
    app.update(appState({ accounts: [account({ id: 'a1', provider: 'codex' })],
      usage: [usage('a1', { state: 'error', resetCreditsAvailable: 2, errorCode: 'network' })] }));
    expect(root.querySelector('.reset-credit-row')).toBeNull();
  });

  it('shows used %, reset countdown, measured time and source per account', () => {
    const state = appState({
      accounts: [account({ id: 'a1', label: 'Work', emailMasked: 'j***@e***.com' })],
      usage: [usage('a1', { plan: 'plus' })],
    });
    const { root } = setup(state);
    const card = root.querySelector('.usage-card');
    expect(card?.querySelector('.card-account-name')?.textContent).toBe('Work');
    expect(card?.querySelector('.card-account-email')?.textContent).toBe('j***@e***.com');
    expect([...(card?.querySelectorAll('.quota-box-percent') ?? [])].map((el) => el.textContent)).toEqual(['25% used', '90% used']);
    expect(card?.querySelector('.quota-box-reset')?.textContent).toBe('Resets in 2h 07m');
    expect(card?.querySelector('.card-measured')?.textContent).toBe('Last measured now');
    expect(card?.querySelector('.card-source')?.textContent).toBe('Source: Official Codex app-server');
    expect([...(card?.querySelectorAll('.card-badge') ?? [])].map((el) => el.textContent)).toEqual(['plus', 'OK']);
  });

  it('unavailable and loading show the reason without any percentage', () => {
    const state = appState({
      accounts: [account({ id: 'a1' }), account({ id: 'a2', order: 1 })],
      usage: [usage('a1', { state: 'unavailable', windows: [], errorCode: 'bridge-no-data', measuredAt: null })],
    });
    const { root } = setup(state);
    const [unavailable, loading] = [...root.querySelectorAll('.usage-card')];
    expect(unavailable?.querySelector('.quota-box')).toBeNull();
    expect(unavailable?.textContent).not.toMatch(/\d+%/);
    expect(unavailable?.querySelector('.card-reason')?.textContent).toBe(`Error: ${en.error_bridgeNoData}`);
    expect(loading?.getAttribute('data-state')).toBe('loading');
    expect(loading?.textContent).not.toMatch(/\d+%/);
    expect(loading?.querySelector('.card-measured')?.textContent).toBe('Not measured yet');
  });

  it('error keeps last measured values dimmed with their time; unknown window says Unknown', () => {
    const state = appState({
      accounts: [account({ id: 'a1' })],
      usage: [
        usage('a1', {
          state: 'error',
          errorCode: 'network',
          measuredAt: NOW - 10 * 60_000,
          windows: [quotaWindow('session', 30, 3_600_000), quotaWindow('weekly', null, null)],
        }),
      ],
    });
    const { root } = setup(state);
    expect(root.querySelector('.card-quota-grid')?.classList.contains('is-dim')).toBe(true);
    expect([...root.querySelectorAll('.quota-box-percent')].map((el) => el.textContent)).toEqual(['30% used', 'Unknown']);
    expect(root.querySelector('.card-measured')?.textContent).toBe('Last measured 10 minutes ago');
    expect(root.querySelector('.card-reason')?.textContent).toBe('Error: Network error');
  });

  it('tells same-kind windows apart by their provider label, rendered as text', () => {
    const evil = '<b>Claude</b> and GPT models';
    const state = appState({
      accounts: [account({ id: 'ag1', provider: 'antigravity' })],
      usage: [
        usage('ag1', {
          provider: 'antigravity',
          source: 'antigravity-cli-usage',
          windows: [
            { ...quotaWindow('session', 10, 3_600_000), label: 'Gemini Models' },
            { ...quotaWindow('weekly', 20, 4 * 24 * 3_600_000), label: 'Gemini Models' },
            { ...quotaWindow('session', 30, 3_600_000), label: evil },
            quotaWindow('weekly', 40, 4 * 24 * 3_600_000),
          ],
        }),
      ],
    });
    const { root } = setup(state);
    const boxes = [...root.querySelectorAll('.quota-box')];
    expect(boxes.map((box) => box.querySelector('.quota-box-label')?.textContent ?? null)).toEqual([
      'Gemini Models',
      'Gemini Models',
      evil,
      null,
    ]);
    expect(root.querySelector('.quota-box-label b')).toBeNull();
    expect(root.querySelector('.card-source')?.textContent).toBe(`Source: ${en.source_antigravityCliUsage}`);
  });

  it('keeps card elements across updates and renders labels as text', () => {
    const evil = '<img src=x onerror=alert(1)>';
    const state = appState({ accounts: [account({ id: 'a1', label: evil })], usage: [usage('a1')] });
    const { root, app } = setup(state);
    const card = root.querySelector('.usage-card');
    app.update(state);
    expect(root.querySelector('.usage-card')).toBe(card);
    expect(root.querySelector('[onerror]')).toBeNull();
    expect(root.querySelector('img[src="x"]')).toBeNull();
    expect(card?.querySelector('.card-account-name')?.textContent).toBe(evil);
  });
});

describe('Accounts tab', () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('adopts a login started from a Windows notification without starting another session', () => {
    const api = new FakeApi();
    const state = appState({ accounts: [account({ id: 'a1', provider: 'codex', loginState: 'logged-out' })] });
    const { app } = setup(state, api);
    app.selectTab('accounts', false);

    loginEvent(api, 'a1', 'notification-session', {
      type: 'device-code',
      userCode: 'WXYZ-9876',
      verificationUrl: 'https://auth.openai.com/codex/device',
    });

    const panel = app.accounts.sections.codex.el.querySelector<HTMLElement>('.login-panel[data-account-id="a1"]');
    expect(panel?.hidden).toBe(false);
    expect(panel?.querySelector('.login-code')?.textContent).toBe('WXYZ-9876');
    expect(api.callsTo('login:start')).toEqual([]);
  });

  it('add account -> label -> login with device code, copy target and open login page', async () => {
    const api = new FakeApi()
      .reply('accounts:add', (req) => ({ ok: true, value: account({ id: 'new1', provider: req.provider, label: req.label, loginState: 'logged-out' }) }))
      .reply('login:start', () => ({ ok: true, value: { sessionId: 'sess1' } }));
    const { app } = setup(appState(), api);
    app.selectTab('accounts', false);
    const section = app.accounts.sections.codex;
    section.addButton.click();
    expect(section.addForm.hidden).toBe(false);

    typeInto(section.addInput, '   ');
    submit(section.addForm);
    expect(section.addInput.getAttribute('aria-invalid')).toBe('true');
    expect(api.callsTo('accounts:add')).toHaveLength(0);

    typeInto(section.addInput, 'Work <b>');
    submit(section.addForm);
    await flush();
    expect(api.callsTo('accounts:add')).toEqual([{ provider: 'codex', label: 'Work <b>' }]);
    expect(api.callsTo('login:start')).toEqual([{ accountId: 'new1' }]);

    loginEvent(api, 'new1', 'sess1', { type: 'device-code', userCode: 'WXYZ-9876', verificationUrl: 'https://auth.openai.com/codex/device' });
    const panel = section.el.querySelector<HTMLElement>('.login-panel[data-account-id="new1"]');
    expect(panel?.hidden).toBe(false);
    expect(panel?.querySelector('.login-code')?.textContent).toBe('WXYZ-9876');
    expect(panel?.querySelector('.login-copy')?.getAttribute('aria-label')).toBe('Copy');
    expect(panel?.querySelector('.login-code')?.getAttribute('aria-label')).toBe('Code: WXYZ-9876');
    expect(panel?.querySelector('.login-paste-form')?.hasAttribute('hidden')).toBe(true);
    panel?.querySelector<HTMLButtonElement>('.login-open')?.click();
    expect(api.callsTo('shell:open-external')).toEqual([
      { kind: 'login', sessionId: 'sess1', url: 'https://auth.openai.com/codex/device' },
    ]);

    // Row arrives with the next snapshot; the same panel moves under it.
    app.update(appState({ accounts: [account({ id: 'new1', provider: 'codex', label: 'Work <b>', loginState: 'logging-in' })] }));
    const row = section.el.querySelector('.account-row[data-account-id="new1"]');
    expect(row?.querySelector('.login-panel')).toBe(panel);
    expect(row?.querySelector('.account-name')?.textContent).toBe('Work <b>');

    loginEvent(api, 'new1', 'sess1', { type: 'success', emailMasked: 'w***@e***.com' });
    expect(panel?.querySelector('.login-status')?.textContent).toBe('Signed in · w***@e***.com');
  });

  it('Antigravity: one account, no widget login, and a hint pointing at the CLI sign-in', async () => {
    const api = new FakeApi().reply('accounts:add', (req) => ({
      ok: true,
      value: account({ id: 'ag1', provider: req.provider, label: req.label, loginState: 'unknown' }),
    }));
    const { app } = setup(appState(), api);
    app.selectTab('accounts', false);
    const section = app.accounts.sections.antigravity;
    expect(section.loginHintEl.hidden).toBe(false);
    expect(section.loginHintEl.textContent).toBe(en.externalLoginHint.replace('{provider}', 'Antigravity'));
    expect(app.accounts.sections.codex.loginHintEl.hidden).toBe(true);

    section.addButton.click();
    typeInto(section.addInput, 'Main');
    submit(section.addForm);
    await flush();
    expect(api.callsTo('accounts:add')).toEqual([{ provider: 'antigravity', label: 'Main' }]);
    // No login panel and no login:start for a provider without a widget login.
    expect(api.callsTo('login:start')).toHaveLength(0);
    expect(section.el.querySelector('.login-panel')).toBeNull();

    app.update(appState({ accounts: [account({ id: 'ag1', provider: 'antigravity', label: 'Main', loginState: 'logged-out' })] }));
    const row = section.el.querySelector('.account-row[data-account-id="ag1"]');
    expect(row?.querySelector<HTMLButtonElement>('.btn-login')?.hidden).toBe(true);
    expect(section.addButton.hidden).toBe(true);
    // Providers without a limit keep their add button.
    expect(app.accounts.sections.codex.addButton.hidden).toBe(false);
  });

  it('Claude login: open page, paste code#state, submit', async () => {
    const api = new FakeApi().reply('login:start', () => ({ ok: true, value: { sessionId: 'c1' } }));
    const state = appState({ accounts: [account({ id: 'cl1', provider: 'claude', label: 'Claude A', loginState: 'logged-out' })] });
    const { app } = setup(state, api);
    const row = app.accounts.sections.claude.el.querySelector('.account-row[data-account-id="cl1"]');
    row?.querySelector<HTMLButtonElement>('.btn-login')?.click();
    await flush();
    loginEvent(api, 'cl1', 'c1', { type: 'url', url: 'https://claude.ai/oauth/authorize?x=1' });
    const panel = row?.querySelector<HTMLElement>('.login-panel');
    expect(panel?.querySelector('.login-hint')?.textContent).toBe('Sign in in your browser, then paste the code it shows below.');
    const form = panel?.querySelector<HTMLFormElement>('.login-paste-form');
    expect(form?.hidden).toBe(false);
    const input = panel?.querySelector<HTMLInputElement>('.login-paste');
    if (input === null || input === undefined || form === null || form === undefined) throw new Error('missing paste form');
    // <input type=text> drops newlines itself; the newline rule is covered by isValidPaste below.
    typeInto(input, '    ');
    submit(form);
    expect(api.callsTo('login:submit-paste')).toHaveLength(0);
    expect(input.getAttribute('aria-invalid')).toBe('true');
    typeInto(input, '  abc#def  ');
    submit(form);
    await flush();
    expect(api.callsTo('login:submit-paste')).toEqual([{ sessionId: 'c1', text: 'abc#def' }]);
    expect(input.value).toBe('');
    expect(panel?.querySelector('.login-status')?.textContent).toBe('Verifying...');
    panel?.querySelector<HTMLButtonElement>('.login-cancel')?.click();
    expect(api.callsTo('login:cancel')).toEqual([{ sessionId: 'c1' }]);
    expect(panel?.hidden).toBe(true);
  });

  it('login error shows the i18n reason and offers retry', async () => {
    const api = new FakeApi().reply('login:start', () => ({ ok: false, error: { code: 'internal', detail: 'cli-not-found' } }));
    const state = appState({ accounts: [account({ id: 'g1', provider: 'grok', loginState: 'logged-out' })] });
    const { app } = setup(state, api);
    app.accounts.startLogin('g1', 'grok');
    await flush();
    const panel = app.accounts.el.querySelector<HTMLElement>('.login-panel[data-account-id="g1"]');
    expect(panel?.querySelector('.login-status')?.textContent).toBe('Sign-in failed: CLI not found');
    expect(panel?.querySelector<HTMLButtonElement>('.login-retry')?.hidden).toBe(false);
  });

  it('remove asks for confirmation first; rename, toggle and reorder call IPC', async () => {
    const state = appState({
      accounts: [account({ id: 'a1', label: 'One', order: 0 }), account({ id: 'a2', label: 'Two', order: 1 })],
    });
    const api = new FakeApi().reply('accounts:rename', (req) => ({ ok: true, value: account({ id: req.accountId, label: req.label }) }));
    const { app } = setup(state, api);
    const rows = app.accounts.sections.codex.el.querySelectorAll('.account-row');
    const first = rows[0];
    const second = rows[1];
    if (first === undefined || second === undefined) throw new Error('rows missing');

    expect(first.querySelector<HTMLButtonElement>('.btn-move-up')?.disabled).toBe(true);
    expect(second.querySelector<HTMLButtonElement>('.btn-move-down')?.disabled).toBe(true);
    second.querySelector<HTMLButtonElement>('.btn-move-up')?.click();
    expect(api.callsTo('accounts:reorder')).toEqual([{ accountId: 'a2', direction: 'up' }]);

    first.querySelector<HTMLButtonElement>('.btn-delete-account')?.click();
    const confirmBox = first.querySelector<HTMLElement>('.confirm-box');
    expect(confirmBox?.hidden).toBe(false);
    expect(confirmBox?.textContent).toContain('Remove this account from the widget?');
    expect(api.callsTo('accounts:remove')).toHaveLength(0);
    first.querySelector<HTMLButtonElement>('.btn-confirm-delete')?.click();
    expect(api.callsTo('accounts:remove')).toEqual([{ accountId: 'a1' }]);

    const checkbox = first.querySelector<HTMLInputElement>('.chk-account');
    if (checkbox === null) throw new Error('checkbox missing');
    checkbox.checked = false;
    checkbox.dispatchEvent(new Event('change', { bubbles: true }));
    expect(api.callsTo('accounts:toggle')).toEqual([{ accountId: 'a1', enabled: false }]);

    first.querySelector<HTMLButtonElement>('.btn-rename')?.click();
    const renameInput = first.querySelector<HTMLInputElement>('.rename-form input');
    const renameForm = first.querySelector<HTMLFormElement>('.rename-form');
    if (renameInput === null || renameForm === null) throw new Error('rename form missing');
    expect(renameInput.value).toBe('One');
    typeInto(renameInput, 'Uno');
    submit(renameForm);
    await flush();
    expect(api.callsTo('accounts:rename')).toEqual([{ accountId: 'a1', label: 'Uno' }]);
    expect(renameForm.hidden).toBe(true);
  });

  it('shows CLI detection state and the install guide only when missing', () => {
    const { app } = setup(appState());
    const grok = app.accounts.sections.grok;
    expect(grok.el.querySelector('.provider-cli')?.textContent).toBe('CLI not found');
    expect(grok.installGuideButton.hidden).toBe(false);
    grok.installGuideButton.click();
    expect(app.accounts.sections.claude.el.querySelector('.provider-cli')?.textContent).toBe('CLI detected (2.1.270)');
    expect(app.accounts.sections.claude.installGuideButton.hidden).toBe(true);
  });

  it('re-scan button asks main to detect a missing CLI and is inert while detecting (P-06)', async () => {
    const { api, app } = setup(appState());
    const grok = app.accounts.sections.grok;
    expect(grok.redetectButton.hidden).toBe(false);
    expect(grok.redetectButton.textContent).toBe('Re-scan');
    grok.redetectButton.click();
    await flush();
    expect(api.callsTo('cli:redetect')).toEqual([{ provider: 'grok' }]);
    expect(app.accounts.sections.codex.redetectButton.hidden).toBe(true);

    const base = appState();
    app.update({ ...base, cli: { ...base.cli, grok: { state: 'unknown' } } });
    expect(grok.el.querySelector('.provider-cli')?.textContent).toBe('Checking installed CLIs...');
    expect(grok.redetectButton.disabled).toBe(true);
    grok.redetectButton.click();
    expect(api.callsTo('cli:redetect')).toHaveLength(1);
  });

  it('order buttons follow the list shown in each provider section (P-05)', () => {
    const state = appState({
      accounts: [
        account({ id: 'c1', provider: 'claude', order: 0 }),
        account({ id: 'x1', provider: 'codex', order: 1 }),
        account({ id: 'x2', provider: 'codex', order: 2 }),
      ],
    });
    const { app } = setup(state);
    const codexRows = app.accounts.sections.codex.el.querySelectorAll('.account-row');
    expect(codexRows[0]?.querySelector<HTMLButtonElement>('.btn-move-up')?.disabled).toBe(true);
    expect(codexRows[0]?.querySelector<HTMLButtonElement>('.btn-move-down')?.disabled).toBe(false);
    expect(codexRows[1]?.querySelector<HTMLButtonElement>('.btn-move-down')?.disabled).toBe(true);
    const claudeRow = app.accounts.sections.claude.el.querySelector('.account-row');
    expect(claudeRow?.querySelector<HTMLButtonElement>('.btn-move-up')?.disabled).toBe(true);
    expect(claudeRow?.querySelector<HTMLButtonElement>('.btn-move-down')?.disabled).toBe(true);
  });

  it('Claude bridge: status, confirmed install for the only account, uninstall', async () => {
    const api = new FakeApi()
      .reply('claude-bridge:status', () => ({ ok: true, value: { installed: false, wrapsExistingCommand: false, targetAccountId: null, lastDataAt: null } }))
      .reply('claude-bridge:install-default', (req) => ({
        ok: true,
        value: { installed: true, wrapsExistingCommand: true, targetAccountId: req.accountId, lastDataAt: NOW - 120_000 },
      }));
    const state = appState({ accounts: [account({ id: 'cl1', provider: 'claude', label: 'Claude A' })] });
    const { app, root } = setup(state, api);
    app.selectTab('accounts', false);
    await flush();
    const bridge = root.querySelector('.bridge-card');
    expect(bridge?.querySelector('.bridge-status')?.textContent).toBe('Not installed');
    bridge?.querySelector<HTMLButtonElement>('.bridge-install')?.click();
    expect(api.callsTo('claude-bridge:install-default')).toHaveLength(0);
    expect(bridge?.querySelector<HTMLElement>('.confirm-box')?.hidden).toBe(false);
    bridge?.querySelector<HTMLButtonElement>('.bridge-confirm')?.click();
    await flush();
    expect(api.callsTo('claude-bridge:install-default')).toEqual([{ accountId: 'cl1' }]);
    expect(bridge?.querySelector('.bridge-status')?.textContent).toBe('Installed in default profile');
    expect(bridge?.querySelector('.bridge-detail')?.textContent).toBe(
      'Wraps and keeps your existing statusline command · Last record 2 minutes ago · Receiving account: Claude A · ' +
        en.bridgeRemoveBeforeUninstall,
    );
    bridge?.querySelector<HTMLButtonElement>('.bridge-uninstall')?.click();
    expect(api.callsTo('claude-bridge:uninstall-default')).toEqual([null]);
  });

  it('reports IPC failures with the translated error', async () => {
    const api = new FakeApi().reply('accounts:reorder', () => ({ ok: false, error: { code: 'not-implemented' } }));
    const state = appState({ accounts: [account({ id: 'a1', order: 0 }), account({ id: 'a2', order: 1 })] });
    const { app } = setup(state, api);
    app.accounts.reorder('a2', 'up');
    await flush();
    expect(app.statusEl.hidden).toBe(false);
    expect(app.statusEl.textContent).toBe('Error: Not implemented yet');
  });
});

describe('Settings tab', () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('exposes every setting and saves choices as single-key patches', () => {
    const { api, app } = setup(appState());
    const el = app.settings.el;
    const themeButtons = [...el.querySelectorAll<HTMLButtonElement>('.choice-button')].filter((b) =>
      ['windows', '1a', '1b', '1c', '1d'].includes(b.dataset.value ?? ''),
    );
    expect(themeButtons.map((b) => b.textContent)).toEqual([
      'Windows (system theme)',
      '1a. Bar Gauge',
      '1b. Segments',
      '1c. Dual Ring',
      '1d. Ultra Compact',
    ]);
    expect(themeButtons[0]?.getAttribute('aria-pressed')).toBe('true');
    themeButtons[2]?.click();
    expect(api.callsTo('settings:update')).toEqual([{ patch: { theme: '1b' } }]);

    const settingKeys = new Set(
      [...el.querySelectorAll<HTMLElement>('[data-setting]')].map((node) => node.dataset.setting),
    );
    for (const key of ['showUsedPercent', 'showWeeklyLimit', 'colorByUsage', 'showCardBackground', 'alwaysOnTop', 'openAtLogin', 'offsetPx', 'verticalOffsetPx', 'alphaPercent', 'refreshIntervalSec', 'language']) {
      expect(settingKeys.has(key), key).toBe(true);
    }
    expect(el.textContent).toContain('Mica');
    expect(el.textContent).toContain('Shown opaque when transparency effects are off or high contrast is on.');

    const weekly = el.querySelector<HTMLInputElement>('[data-setting="showWeeklyLimit"]');
    if (weekly === null) throw new Error('switch missing');
    expect(weekly.getAttribute('role')).toBe('switch');
    weekly.checked = false;
    weekly.dispatchEvent(new Event('change', { bubbles: true }));
    expect(api.callsTo('settings:update')).toContainEqual({ patch: { showWeeklyLimit: false } });

    const select = el.querySelector<HTMLSelectElement>('[data-setting="refreshIntervalSec"]');
    if (select === null) throw new Error('select missing');
    select.value = '120';
    select.dispatchEvent(new Event('change', { bubbles: true }));
    expect(api.callsTo('settings:update')).toContainEqual({ patch: { refreshIntervalSec: 120 } });
  });

  it('always-on-top is shown whenever the widget floats, including the docked fallback (P-04)', () => {
    const { app } = setup(appState());
    const wrap = app.settings.el.querySelector('[data-setting="alwaysOnTop"]')?.closest<HTMLElement>('.form-group');
    const hint = app.settings.el.querySelector<HTMLElement>('.placement-fallback');
    expect(wrap?.hidden).toBe(true);
    expect(hint?.hidden).toBe(true);
    app.update(appState({ settings: { placementMode: 'floating' }, effectivePlacementMode: 'floating' }));
    expect(wrap?.hidden).toBe(false);
    expect(hint?.hidden).toBe(true);
    // Docked chosen, but a side or auto-hide taskbar makes it float.
    app.update(appState({ effectivePlacementMode: 'floating' }));
    expect(wrap?.hidden).toBe(false);
    expect(hint?.hidden).toBe(false);
    expect(hint?.textContent).toBe(en.placementFallbackHint);
    app.update(appState({ effectivePlacementMode: 'docked' }));
    expect(wrap?.hidden).toBe(true);
  });

  it('range input moves the widget without saving and commits once after change (P-03)', () => {
    const { api, app } = setup(appState());
    const slider = app.settings.el.querySelector<HTMLInputElement>('[data-setting="offsetPx"]');
    if (slider === null) throw new Error('slider missing');
    slider.value = '120';
    slider.dispatchEvent(new Event('input', { bubbles: true }));
    expect(slider.parentElement?.querySelector('.range-value')?.textContent).toBe('120px');
    expect(api.callsTo('settings:update')).toHaveLength(0);
    vi.advanceTimersByTime(PREVIEW_THROTTLE_MS);
    expect(api.callsTo('window:preview-placement')).toEqual([{ patch: { offsetPx: 120 } }]);
    slider.dispatchEvent(new Event('change', { bubbles: true }));
    slider.value = '121';
    slider.dispatchEvent(new Event('change', { bubbles: true }));
    expect(api.callsTo('settings:update')).toHaveLength(0);
    vi.advanceTimersByTime(RANGE_COMMIT_DELAY_MS);
    expect(api.callsTo('settings:update')).toEqual([{ patch: { offsetPx: 121 } }]);
  });

  it('a drag that ends on the saved value drops the preview instead of saving', () => {
    const { api, app } = setup(appState());
    const slider = app.settings.el.querySelector<HTMLInputElement>('[data-setting="verticalOffsetPx"]');
    if (slider === null) throw new Error('slider missing');
    const saved = slider.value;
    slider.dispatchEvent(new Event('pointerdown', { bubbles: true }));
    slider.value = '12';
    slider.dispatchEvent(new Event('input', { bubbles: true }));
    vi.advanceTimersByTime(PREVIEW_THROTTLE_MS);
    slider.value = saved;
    slider.dispatchEvent(new Event('input', { bubbles: true }));
    slider.dispatchEvent(new Event('pointerup', { bubbles: true }));
    expect(api.callsTo('window:preview-placement')).toEqual([{ patch: { verticalOffsetPx: 12 } }, { patch: null }]);
    expect(api.callsTo('settings:update')).toHaveLength(0);
  });

  it('dragging locks the popup and releases the lock on pointerup', () => {
    const { api, app } = setup(appState());
    const slider = app.settings.el.querySelector<HTMLInputElement>('[data-setting="alphaPercent"]');
    if (slider === null) throw new Error('slider missing');
    slider.dispatchEvent(new Event('pointerdown', { bubbles: true }));
    slider.value = '50';
    slider.dispatchEvent(new Event('input', { bubbles: true }));
    slider.dispatchEvent(new Event('pointerup', { bubbles: true }));
    expect(api.callsTo('window:set-popup-lock')).toEqual([{ locked: true }, { locked: false }]);
    expect(api.callsTo('settings:update')).toEqual([{ patch: { alphaPercent: 50 } }]);
    expect(api.callsTo('window:preview-placement')).toHaveLength(0);
  });

  it('reverts the control when saving fails', async () => {
    const api = new FakeApi().reply('settings:update', () => ({ ok: false, error: { code: 'invalid-request' } }));
    const { app } = setup(appState(), api);
    const toggle = app.settings.el.querySelector<HTMLInputElement>('[data-setting="colorByUsage"]');
    if (toggle === null) throw new Error('switch missing');
    toggle.checked = false;
    toggle.dispatchEvent(new Event('change', { bubbles: true }));
    await flush();
    expect(toggle.checked).toBe(true);
    expect(app.statusEl.textContent).toBe('Error: Internal error');
  });
});

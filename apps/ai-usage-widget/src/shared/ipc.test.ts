import { describe, expect, it } from 'vitest';
import {
  EVENT_CHANNELS,
  INVOKE_CHANNELS,
  INVOKE_VALIDATORS,
  WIDGET_SIZE_LIMITS,
  clampWidgetSize,
  isAllowedExternalUrl,
  isEventChannel,
  isInvokeChannel,
  validateInvokeRequest,
} from './ipc';
import { toAccountDTO, type Account } from './types';

describe('ipc contract', () => {
  it('has a validator for every invoke channel and no extras', () => {
    expect(Object.keys(INVOKE_VALIDATORS).sort()).toEqual([...INVOKE_CHANNELS].sort());
    expect(new Set(INVOKE_CHANNELS).size).toBe(INVOKE_CHANNELS.length);
    expect(new Set(EVENT_CHANNELS).size).toBe(EVENT_CHANNELS.length);
  });

  it('channel guards', () => {
    expect(isInvokeChannel('settings:update')).toBe(true);
    expect(isInvokeChannel('account:add-custom-account')).toBe(false);
    expect(isEventChannel('state:changed')).toBe(true);
    expect(isEventChannel('settings:update')).toBe(false);
  });

  it('no-payload channels reject payloads', () => {
    expect(validateInvokeRequest('app:get-state', null).ok).toBe(true);
    expect(validateInvokeRequest('app:get-state', { x: 1 }).ok).toBe(false);
  });

  it('settings:update validates the patch', () => {
    expect(validateInvokeRequest('settings:update', { patch: { theme: '1c' } }).ok).toBe(true);
    expect(validateInvokeRequest('settings:update', { patch: { refreshIntervalSec: Number.NaN } }).ok).toBe(false);
    expect(validateInvokeRequest('settings:update', { theme: '1c' }).ok).toBe(false);
  });

  it('accounts:add requires a known provider and a sane label', () => {
    expect(validateInvokeRequest('accounts:add', { provider: 'grok', label: ' Home ' })).toEqual({
      ok: true,
      value: { provider: 'grok', label: 'Home' },
    });
    expect(validateInvokeRequest('accounts:add', { provider: 'google', label: 'x' }).ok).toBe(false);
    expect(validateInvokeRequest('accounts:add', { provider: 'claude', label: 'x'.repeat(65) }).ok).toBe(false);
    expect(validateInvokeRequest('accounts:add', { provider: 'claude', label: 'x', id: 'custom-1' }).ok).toBe(false);
  });

  it('account ids must match the id pattern', () => {
    expect(validateInvokeRequest('accounts:remove', { accountId: 'abc-123' }).ok).toBe(true);
    expect(validateInvokeRequest('accounts:remove', { accountId: '..\\..\\x' }).ok).toBe(false);
    expect(validateInvokeRequest('accounts:reorder', { accountId: 'a', direction: 'left' }).ok).toBe(false);
    expect(validateInvokeRequest('accounts:toggle', { accountId: 'a', enabled: 'yes' }).ok).toBe(false);
  });

  it('login:submit-paste bounds text', () => {
    expect(validateInvokeRequest('login:submit-paste', { sessionId: 's1', text: ' code#state ' })).toEqual({
      ok: true,
      value: { sessionId: 's1', text: 'code#state' },
    });
    expect(validateInvokeRequest('login:submit-paste', { sessionId: 's1', text: '' }).ok).toBe(false);
    expect(validateInvokeRequest('login:submit-paste', { sessionId: 's1', text: 'a\nb' }).ok).toBe(false);
    expect(validateInvokeRequest('login:submit-paste', { sessionId: 's1', text: 'x'.repeat(5000) }).ok).toBe(false);
  });

  it('usage:refresh-now accepts all or one account', () => {
    expect(validateInvokeRequest('usage:refresh-now', null)).toEqual({ ok: true, value: { accountId: null } });
    expect(validateInvokeRequest('usage:refresh-now', { accountId: 'a1' })).toEqual({
      ok: true,
      value: { accountId: 'a1' },
    });
    expect(validateInvokeRequest('usage:refresh-now', { accountId: 5 }).ok).toBe(false);
  });

  it('shell:open-external only allows keys or https login URLs', () => {
    expect(validateInvokeRequest('shell:open-external', { kind: 'link', key: 'codex-cli-install' }).ok).toBe(true);
    expect(validateInvokeRequest('shell:open-external', { kind: 'link', key: 'evil' }).ok).toBe(false);
    expect(
      validateInvokeRequest('shell:open-external', {
        kind: 'login',
        sessionId: 's1',
        url: 'https://auth.openai.com/codex/device',
      }).ok,
    ).toBe(true);
    for (const url of ['http://example.com', 'javascript:alert(1)', 'file:///C:/x', 'https://u:p@example.com', 'https://' + 'a'.repeat(2100)]) {
      expect(validateInvokeRequest('shell:open-external', { kind: 'login', sessionId: 's1', url }).ok, url).toBe(false);
    }
    expect(validateInvokeRequest('shell:open-external', { kind: 'link', key: 'codex-cli-install', url: 'https://x.y' }).ok).toBe(
      false,
    );
  });

  it('isAllowedExternalUrl', () => {
    expect(isAllowedExternalUrl('https://claude.ai/oauth/authorize?x=1')).toBe(true);
    expect(isAllowedExternalUrl('not a url')).toBe(false);
  });

  it('window:resize-widget rejects non-finite sizes and main clamps', () => {
    expect(validateInvokeRequest('window:resize-widget', { width: Number.POSITIVE_INFINITY, height: 30 }).ok).toBe(false);
    expect(validateInvokeRequest('window:resize-widget', { width: -1, height: 30 }).ok).toBe(false);
    expect(clampWidgetSize({ width: 99999, height: 1 })).toEqual({
      width: WIDGET_SIZE_LIMITS.maxWidth,
      height: WIDGET_SIZE_LIMITS.minHeight,
    });
  });

  it('window:preview-placement accepts only placement offsets, or null', () => {
    expect(validateInvokeRequest('window:preview-placement', { patch: null })).toEqual({ ok: true, value: { patch: null } });
    expect(validateInvokeRequest('window:preview-placement', { patch: { offsetPx: 40, verticalOffsetPx: -3 } })).toEqual({
      ok: true,
      value: { patch: { offsetPx: 40, verticalOffsetPx: -3 } },
    });
    expect(validateInvokeRequest('window:preview-placement', { patch: { theme: '1c' } }).ok).toBe(false);
    expect(validateInvokeRequest('window:preview-placement', { patch: { offsetPx: 9999 } }).ok).toBe(false);
    expect(validateInvokeRequest('window:preview-placement', { patch: {} }).ok).toBe(false);
    expect(validateInvokeRequest('window:preview-placement', null).ok).toBe(false);
  });

  it('cli:redetect takes a provider or null', () => {
    expect(validateInvokeRequest('cli:redetect', { provider: null })).toEqual({ ok: true, value: { provider: null } });
    expect(validateInvokeRequest('cli:redetect', { provider: 'codex' })).toEqual({ ok: true, value: { provider: 'codex' } });
    expect(validateInvokeRequest('cli:redetect', { provider: 'gemini' }).ok).toBe(false);
  });

  it('widget size limit leaves room for many accounts', () => {
    expect(WIDGET_SIZE_LIMITS.maxWidth).toBeGreaterThanOrEqual(24 * 150);
  });

  it('window:show-popup accepts an optional tab', () => {
    expect(validateInvokeRequest('window:show-popup', null)).toEqual({ ok: true, value: { tab: null } });
    expect(validateInvokeRequest('window:show-popup', { tab: 'accounts' })).toEqual({ ok: true, value: { tab: 'accounts' } });
    expect(validateInvokeRequest('window:show-popup', { tab: 'debug' }).ok).toBe(false);
  });

  it('toAccountDTO never includes profileDir', () => {
    const account: Account = {
      id: 'a1',
      provider: 'claude',
      label: 'Work',
      enabled: true,
      order: 0,
      profileDir: 'C:\\Users\\x\\AppData\\Local\\AIUsageWidget\\profiles\\claude\\a1',
      createdAt: 1,
    };
    const dto = toAccountDTO(account, { loginState: 'logged-in', emailMasked: 'w***@e***.com' });
    expect(dto).not.toHaveProperty('profileDir');
    expect(dto).not.toHaveProperty('createdAt');
    expect(dto.emailMasked).toBe('w***@e***.com');
  });
});

import { describe, expect, it } from 'vitest';
import { DEFAULT_SETTINGS } from '../../shared/settings';
import { nullLogger } from '../log';
import { IpcHandlerError, dispatchInvoke, type InvokeHandlers } from './dispatch';

const TRUSTED = { senderUrl: 'app://bundle/index.html?view=popup', view: 'popup' as const };
const deps = { isTrustedSender: (url: string) => url.startsWith('app://bundle/'), logger: nullLogger };

describe('dispatchInvoke', () => {
  it('rejects untrusted senders before validation', async () => {
    const result = await dispatchInvoke('settings:get', null, { senderUrl: 'https://evil.test/', view: null }, {}, deps);
    expect(result).toEqual({ ok: false, error: { code: 'forbidden-sender' } });
  });

  it('rejects invalid payloads', async () => {
    const handlers: InvokeHandlers = { 'settings:update': () => DEFAULT_SETTINGS };
    const result = await dispatchInvoke('settings:update', { patch: { refreshIntervalSec: 7 } }, TRUSTED, handlers, deps);
    expect(result).toEqual({ ok: false, error: { code: 'invalid-request' } });
  });

  it('reports missing handlers as not-implemented', async () => {
    const result = await dispatchInvoke('accounts:list', null, TRUSTED, {}, deps);
    expect(result).toEqual({ ok: false, error: { code: 'not-implemented' } });
  });

  it('passes validated requests and returns values', async () => {
    const handlers: InvokeHandlers = {
      'settings:update': (request) => ({ ...DEFAULT_SETTINGS, ...request.patch }),
    };
    const result = await dispatchInvoke('settings:update', { patch: { theme: '1d' } }, TRUSTED, handlers, deps);
    expect(result.ok && result.value.theme).toBe('1d');
  });

  it('maps IpcHandlerError and hides other errors', async () => {
    const handlers: InvokeHandlers = {
      'accounts:remove': () => {
        throw new IpcHandlerError('not-found');
      },
      'login:start': () => {
        throw new IpcHandlerError('busy', 'cli-not-found');
      },
      'accounts:list': () => {
        throw new Error('C:\\secret\\path exploded');
      },
    };
    await expect(dispatchInvoke('accounts:remove', { accountId: 'a' }, TRUSTED, handlers, deps)).resolves.toEqual({
      ok: false,
      error: { code: 'not-found' },
    });
    await expect(dispatchInvoke('login:start', { accountId: 'a' }, TRUSTED, handlers, deps)).resolves.toEqual({
      ok: false,
      error: { code: 'busy', detail: 'cli-not-found' },
    });
    await expect(dispatchInvoke('accounts:list', null, TRUSTED, handlers, deps)).resolves.toEqual({
      ok: false,
      error: { code: 'internal' },
    });
  });
});

import { describe, expect, it } from 'vitest';
import { INVOKE_CHANNELS } from '../../shared/ipc';
import type { AppController } from '../app/controller';
import { nullLogger } from '../log';
import { dispatchInvoke } from './dispatch';
import { createInvokeHandlers } from './handlers';

function recordingController() {
  const calls: { method: string; args: unknown[] }[] = [];
  const controller = new Proxy(
    {},
    {
      get: (_target, method: string) =>
        (...args: unknown[]) => {
          calls.push({ method, args });
          return null;
        },
    },
  ) as unknown as AppController;
  return { controller, calls };
}

const deps = { isTrustedSender: (url: string) => url.startsWith('app://bundle/'), logger: nullLogger };
const WIDGET = { senderUrl: 'app://bundle/index.html?view=widget', view: 'widget' as const };
const POPUP = { senderUrl: 'app://bundle/index.html?view=popup', view: 'popup' as const };

describe('createInvokeHandlers', () => {
  it('covers every contract channel', () => {
    const { controller } = recordingController();
    expect(Object.keys(createInvokeHandlers(controller)).sort()).toEqual([...INVOKE_CHANNELS].sort());
  });

  it('routes validated payloads to the controller', async () => {
    const { controller, calls } = recordingController();
    const handlers = createInvokeHandlers(controller);
    await dispatchInvoke('accounts:add', { provider: 'grok', label: '  Home ' }, POPUP, handlers, deps);
    await dispatchInvoke('usage:refresh-now', null, WIDGET, handlers, deps);
    await dispatchInvoke('window:show-popup', { tab: 'accounts' }, WIDGET, handlers, deps);
    expect(calls).toEqual([
      { method: 'addAccount', args: ['grok', 'Home'] },
      { method: 'refreshNow', args: [null] },
      { method: 'showPopup', args: ['accounts'] },
    ]);
  });

  it('restricts window operations to the view that owns them', async () => {
    const { controller, calls } = recordingController();
    const handlers = createInvokeHandlers(controller);
    await expect(
      dispatchInvoke('window:resize-widget', { width: 300, height: 40 }, POPUP, handlers, deps),
    ).resolves.toEqual({ ok: false, error: { code: 'forbidden-sender' } });
    await expect(dispatchInvoke('window:set-popup-lock', { locked: true }, WIDGET, handlers, deps)).resolves.toEqual({
      ok: false,
      error: { code: 'forbidden-sender' },
    });
    await expect(
      dispatchInvoke('window:resize-widget', { width: 300, height: 40 }, WIDGET, handlers, deps),
    ).resolves.toEqual({ ok: true, value: null });
    expect(calls).toEqual([{ method: 'resizeWidget', args: [{ width: 300, height: 40 }] }]);
  });
});

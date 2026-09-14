import { describe, expect, it } from 'vitest';
import type { InvokeChannel } from '../shared/ipc';
import { createPreloadApi, type IpcRendererLike } from './bridge';

type Listener = (event: unknown, ...args: unknown[]) => void;

function fakeIpc(reply: (channel: string, payload: unknown) => Promise<unknown>) {
  const sent: { channel: string; payload: unknown }[] = [];
  const listeners = new Map<string, Set<Listener>>();
  const ipc: IpcRendererLike = {
    invoke: (channel, ...args) => {
      sent.push({ channel, payload: args[0] });
      return reply(channel, args[0]);
    },
    on: (channel, listener) => {
      const set = listeners.get(channel) ?? new Set<Listener>();
      set.add(listener);
      listeners.set(channel, set);
    },
    removeListener: (channel, listener) => {
      listeners.get(channel)?.delete(listener);
    },
  };
  const emit = (channel: string, payload: unknown): void => {
    for (const listener of listeners.get(channel) ?? []) listener({ sender: 'x' }, payload);
  };
  return { ipc, sent, listeners, emit };
}

describe('createPreloadApi', () => {
  it('forwards validated requests on allowlisted channels', async () => {
    const { ipc, sent } = fakeIpc(() => Promise.resolve({ ok: true, value: null }));
    const api = createPreloadApi(ipc);
    await expect(api.invoke('usage:refresh-now', { accountId: null })).resolves.toEqual({ ok: true, value: null });
    await api.invoke('login:submit-paste', { sessionId: 's1', text: '  code#state  ' });
    expect(sent).toEqual([
      { channel: 'usage:refresh-now', payload: { accountId: null } },
      { channel: 'login:submit-paste', payload: { sessionId: 's1', text: 'code#state' } },
    ]);
  });

  it('rejects unknown channels and invalid payloads without touching IPC', async () => {
    const { ipc, sent } = fakeIpc(() => Promise.resolve({ ok: true, value: null }));
    const api = createPreloadApi(ipc);
    const bogus = 'fs:read' as unknown as InvokeChannel;
    await expect(api.invoke(bogus, null)).resolves.toEqual({ ok: false, error: { code: 'invalid-request' } });
    await expect(
      api.invoke('shell:open-external', { kind: 'login', sessionId: 's1', url: 'javascript:alert(1)' }),
    ).resolves.toEqual({ ok: false, error: { code: 'invalid-request' } });
    await expect(api.invoke('window:resize-widget', { width: Number.NaN, height: 10 })).resolves.toMatchObject({ ok: false });
    expect(sent).toEqual([]);
  });

  it('maps a rejected invoke (no handler) to an internal error instead of throwing', async () => {
    const { ipc } = fakeIpc(() => Promise.reject(new Error('No handler registered')));
    const api = createPreloadApi(ipc);
    await expect(api.invoke('app:get-state', null)).resolves.toEqual({ ok: false, error: { code: 'internal' } });
  });

  it('subscribes only to known events, strips the IPC event object and unsubscribes once', () => {
    const { ipc, listeners, emit } = fakeIpc(() => Promise.resolve(null));
    const api = createPreloadApi(ipc);
    const received: unknown[] = [];
    const off = api.on('theme:changed', (payload) => received.push(payload));
    emit('theme:changed', { scheme: 'dark' });
    expect(received).toEqual([{ scheme: 'dark' }]);
    off();
    off();
    expect(listeners.get('theme:changed')?.size).toBe(0);
    const offBogus = api.on('secret:event' as never, () => undefined);
    expect(listeners.has('secret:event')).toBe(false);
    offBogus();
  });

  it('is frozen', () => {
    const { ipc } = fakeIpc(() => Promise.resolve(null));
    expect(Object.isFrozen(createPreloadApi(ipc))).toBe(true);
  });
});

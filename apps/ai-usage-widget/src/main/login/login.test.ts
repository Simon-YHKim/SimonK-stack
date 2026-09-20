import { describe, expect, it, vi } from 'vitest';
import type { Account, LoginEvent, LoginEventMessage } from '../../shared/types';
import { IpcHandlerError } from '../ipc/dispatch';
import { nullLogger } from '../log';
import type { ProviderAdapter } from '../providers/types';
import { createLoginManager, hostAllowed, type LoginSettled } from '.';

const ACCOUNT: Account = {
  id: 'acc1',
  provider: 'codex',
  label: 'Work',
  enabled: true,
  order: 0,
  profileDir: 'C:\\p',
  createdAt: 1,
};

interface Controls {
  emit: (event: LoginEvent) => void;
  signal: AbortSignal;
  finish: () => void;
  fail: (error: unknown) => void;
}

function setup(options: { hosts?: readonly string[] | null; timeoutMs?: number; paste?: boolean } = {}) {
  const messages: LoginEventMessage[] = [];
  const settled: LoginSettled[] = [];
  const controls: Controls[] = [];
  const pasted: string[] = [];
  const adapter = {
    id: 'codex',
    startLogin: (_account: Account, emit: (event: LoginEvent) => void, signal: AbortSignal) =>
      new Promise<void>((resolve, reject) => {
        controls.push({ emit, signal, finish: resolve, fail: reject });
      }),
    ...(options.paste === false
      ? {}
      : {
          submitPaste: (_account: Account, text: string) => {
            pasted.push(text);
            return Promise.resolve();
          },
        }),
  } as unknown as ProviderAdapter;
  let counter = 0;
  const manager = createLoginManager({
    getAccount: (id) => (id === ACCOUNT.id ? { ...ACCOUNT } : undefined),
    adapterFor: () => adapter,
    emit: (message) => messages.push(message),
    onSettled: (result) => settled.push(result),
    logger: nullLogger,
    newSessionId: () => `s${(counter += 1)}`,
    timeoutMs: options.timeoutMs ?? 60_000,
    allowedHosts: () => options.hosts ?? null,
  });
  return { manager, messages, settled, controls, pasted };
}

const tick = () => new Promise((resolve) => setTimeout(resolve, 0));

describe('login manager', () => {
  it('relays events and only opens https URLs the active session emitted', async () => {
    const { manager, messages, settled, controls } = setup({ hosts: ['openai.com'] });
    const { sessionId } = manager.start('acc1');
    expect(manager.isActive('acc1')).toBe(true);
    controls[0]!.emit({ type: 'device-code', userCode: 'ABCD-EFGH', verificationUrl: 'https://auth.openai.com/codex/device' });
    controls[0]!.emit({ type: 'url', url: 'http://auth.openai.com/insecure' });
    expect(messages.map((m) => [m.sessionId, m.accountId, m.event.type])).toEqual([
      ['s1', 'acc1', 'device-code'],
      ['s1', 'acc1', 'url'],
    ]);
    expect(manager.isOpenableUrl(sessionId, 'https://auth.openai.com/codex/device')).toBe(true);
    expect(manager.isOpenableUrl(sessionId, 'https://auth.openai.com/other')).toBe(false);
    expect(manager.isOpenableUrl(sessionId, 'http://auth.openai.com/insecure')).toBe(false);
    expect(manager.isOpenableUrl('s999', 'https://auth.openai.com/codex/device')).toBe(false);

    controls[0]!.emit({ type: 'success', emailMasked: 'a***@b***.com' });
    controls[0]!.emit({ type: 'progress', stage: 'verifying' });
    controls[0]!.finish();
    await tick();
    expect(settled).toEqual([{ accountId: 'acc1', sessionId: 's1', event: { type: 'success', emailMasked: 'a***@b***.com' } }]);
    expect(messages).toHaveLength(3);
    expect(manager.isActive('acc1')).toBe(false);
    expect(manager.isOpenableUrl(sessionId, 'https://auth.openai.com/codex/device')).toBe(false);
  });

  it('enforces the provider host allowlist', () => {
    const { manager, controls } = setup({ hosts: ['openai.com'] });
    const { sessionId } = manager.start('acc1');
    controls[0]!.emit({ type: 'url', url: 'https://openai.com.evil.test/login' });
    expect(manager.isOpenableUrl(sessionId, 'https://openai.com.evil.test/login')).toBe(false);
    expect(hostAllowed('https://auth.openai.com/x', ['openai.com'])).toBe(true);
    expect(hostAllowed('https://notopenai.com/x', ['openai.com'])).toBe(false);
    expect(hostAllowed('https://anything.test/', null)).toBe(true);
    manager.cancelAll();
  });

  it('allows one session per account and rejects unknown accounts', () => {
    const { manager } = setup();
    manager.start('acc1');
    expect(() => manager.start('acc1')).toThrow(IpcHandlerError);
    try {
      manager.start('nope');
    } catch (error) {
      expect((error as IpcHandlerError).code).toBe('not-found');
    }
    manager.cancelAll();
  });

  it('cancel aborts the adapter and emits cancelled once', async () => {
    const { manager, messages, controls, settled } = setup();
    const { sessionId } = manager.start('acc1');
    expect(manager.cancel(sessionId)).toBe(true);
    expect(controls[0]!.signal.aborted).toBe(true);
    expect(manager.cancel(sessionId)).toBe(false);
    controls[0]!.emit({ type: 'error', code: 'login-failed' });
    controls[0]!.finish();
    await tick();
    expect(messages.map((m) => m.event)).toEqual([{ type: 'error', code: 'cancelled' }]);
    expect(settled).toHaveLength(1);
  });

  it('times out, and reports adapters that end without a result or reject', async () => {
    vi.useFakeTimers();
    try {
      const timed = setup({ timeoutMs: 1_000 });
      timed.manager.start('acc1');
      await vi.advanceTimersByTimeAsync(1_000);
      expect(timed.controls[0]!.signal.aborted).toBe(true);
      expect(timed.messages.at(-1)?.event).toEqual({ type: 'error', code: 'timeout' });
    } finally {
      vi.useRealTimers();
    }

    const silent = setup();
    silent.manager.start('acc1');
    silent.controls[0]!.finish();
    await tick();
    expect(silent.messages.at(-1)?.event).toEqual({ type: 'error', code: 'login-failed' });

    const broken = setup();
    broken.manager.start('acc1');
    broken.controls[0]!.fail(new Error('boom'));
    await tick();
    expect(broken.messages.at(-1)?.event).toEqual({ type: 'error', code: 'internal' });
  });

  it('routes pasted codes to the adapter', async () => {
    const withPaste = setup();
    const { sessionId } = withPaste.manager.start('acc1');
    await withPaste.manager.submitPaste(sessionId, 'code#state');
    expect(withPaste.pasted).toEqual(['code#state']);
    await expect(withPaste.manager.submitPaste('missing', 'x')).rejects.toMatchObject({ code: 'not-found' });
    withPaste.manager.cancelAll();

    const noPaste = setup({ paste: false });
    const started = noPaste.manager.start('acc1');
    await expect(noPaste.manager.submitPaste(started.sessionId, 'x')).rejects.toMatchObject({ code: 'not-implemented' });
    noPaste.manager.cancelAll();
  });
});

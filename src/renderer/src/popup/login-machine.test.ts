import { describe, expect, it } from 'vitest';
import type { LoginEvent } from '../../../shared/types';
import { IDLE, isLoginBusy, reduceLogin, type LoginAction, type LoginFlow } from './login-machine';

const ACCOUNT = 'acc1';
const START: LoginAction = { type: 'start', at: 1_000 };

function event(e: LoginEvent, sessionId = 's1', accountId = ACCOUNT, at = 1_000): LoginAction {
  return { type: 'event', message: { sessionId, accountId, at, event: e } };
}

function run(actions: LoginAction[], from: LoginFlow = IDLE): LoginFlow {
  return actions.reduce((flow, action) => reduceLogin(flow, action, ACCOUNT), from);
}

describe('login machine', () => {
  it('device code flow: start -> started -> code -> success', () => {
    const flow = run([
      START,
      { type: 'started', sessionId: 's1' },
      event({ type: 'device-code', userCode: 'ABCD-1234', verificationUrl: 'https://auth.example/device' }),
    ]);
    expect(flow).toMatchObject({
      phase: 'active',
      sessionId: 's1',
      stage: 'waiting-device-code',
      deviceCode: { userCode: 'ABCD-1234', verificationUrl: 'https://auth.example/device', expiresAt: null },
    });
    expect(isLoginBusy(flow)).toBe(true);
    const done = run([event({ type: 'success', emailMasked: 'j***@e***.com', plan: 'plus' })], flow);
    expect(done).toEqual({ phase: 'success', emailMasked: 'j***@e***.com', plan: 'plus' });
    expect(run([{ type: 'dismiss' }], done)).toEqual(IDLE);
  });

  it('paste flow: url -> needs-paste -> submit -> verifying -> error', () => {
    let flow = run([
      START,
      { type: 'started', sessionId: 's1' },
      event({ type: 'url', url: 'https://claude.ai/oauth' }),
      event({ type: 'needs-paste' }),
    ]);
    expect(flow).toMatchObject({ phase: 'active', url: 'https://claude.ai/oauth', needsPaste: true, stage: 'waiting-paste' });
    flow = run([{ type: 'submit' }], flow);
    expect(flow).toMatchObject({ submitting: true });
    expect(run([{ type: 'submit' }], flow)).toBe(flow);
    flow = run([{ type: 'submit-done' }], flow);
    expect(flow).toMatchObject({ submitting: false, stage: 'verifying' });
    flow = run([event({ type: 'error', code: 'login-failed' })], flow);
    expect(flow).toEqual({ phase: 'error', code: 'login-failed', sessionId: 's1' });
    expect(run([{ type: 'start', at: 2_000 }], flow)).toEqual({ phase: 'starting', since: 2_000 });
  });

  it('adopts the session of events that arrive before login:start resolves', () => {
    const flow = run([START, event({ type: 'progress', stage: 'waiting-browser' }, 's9')]);
    expect(flow).toMatchObject({ phase: 'active', sessionId: 's9', stage: 'waiting-browser' });
    expect(run([{ type: 'started', sessionId: 's9' }], flow)).toBe(flow);
  });

  it('ignores a late event from a session cancelled before this start (CR-11)', () => {
    // Cancel emits 'error cancelled' at 900; the user clicked Login again at 1000 before it arrived.
    const starting = run([START]);
    expect(run([event({ type: 'error', code: 'cancelled' }, 'old', ACCOUNT, 900)], starting)).toBe(starting);
    expect(run([event({ type: 'error', code: 'cancelled' }, 'old', ACCOUNT, 900), { type: 'started', sessionId: 'new' }], starting)).toMatchObject({
      phase: 'active',
      sessionId: 'new',
    });
    // A quick failure of the new session itself is still shown.
    expect(run([event({ type: 'error', code: 'cli-not-found' }, 'new', ACCOUNT, 1_001)], starting)).toEqual({
      phase: 'error',
      code: 'cli-not-found',
      sessionId: 'new',
    });
  });

  it('lets the session main started replace an error adopted from another session', () => {
    const adoptedError: LoginFlow = { phase: 'error', code: 'cancelled', sessionId: 'old' };
    expect(run([{ type: 'started', sessionId: 'new' }], adoptedError)).toMatchObject({ phase: 'active', sessionId: 'new' });
    const ownError: LoginFlow = { phase: 'error', code: 'login-failed', sessionId: 'new' };
    expect(run([{ type: 'started', sessionId: 'new' }], ownError)).toBe(ownError);
  });

  it('ignores events for other accounts or sessions', () => {
    const active = run([START, { type: 'started', sessionId: 's1' }]);
    expect(run([event({ type: 'success' }, 's2')], active)).toBe(active);
    expect(run([event({ type: 'success' }, 's1', 'other')], active)).toBe(active);
    expect(run([event({ type: 'success' })], IDLE)).toBe(IDLE);
  });

  it('start failure, submit failure and cancel', () => {
    expect(run([START, { type: 'start-failed', code: 'cli-not-found' }])).toEqual({
      phase: 'error',
      code: 'cli-not-found',
      sessionId: null,
    });
    const submitting = run([START, { type: 'started', sessionId: 's1' }, { type: 'submit' }]);
    expect(run([{ type: 'submit-failed', code: 'internal' }], submitting)).toMatchObject({ submitting: false, pasteError: 'internal' });
    expect(run([{ type: 'cancel' }], submitting)).toEqual(IDLE);
    expect(run([{ type: 'cancel' }, { type: 'started', sessionId: 's1' }], { phase: 'starting', since: 0 })).toEqual(IDLE);
    expect(run([START], submitting)).toBe(submitting);
  });
});

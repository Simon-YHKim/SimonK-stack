// Pure login-flow state machine for one account. The DOM panel renders whatever state it returns.

import type { ErrorCode, LoginEventMessage, LoginStage } from '../../../shared/types';

export interface DeviceCodeInfo {
  userCode: string;
  verificationUrl: string;
  expiresAt: number | null;
}

export type LoginFlow =
  | { phase: 'idle' }
  /** `since`: when the user started this flow (epoch ms, same clock as LoginEventMessage.at). */
  | { phase: 'starting'; since: number }
  | {
      phase: 'active';
      sessionId: string;
      stage: LoginStage | null;
      url: string | null;
      deviceCode: DeviceCodeInfo | null;
      needsPaste: boolean;
      submitting: boolean;
      pasteError: ErrorCode | null;
    }
  | { phase: 'success'; emailMasked: string | null; plan: string | null }
  | { phase: 'error'; code: ErrorCode; sessionId: string | null };

export type LoginAction =
  | { type: 'start'; at: number }
  | { type: 'started'; sessionId: string }
  | { type: 'start-failed'; code: ErrorCode }
  | { type: 'event'; message: LoginEventMessage }
  | { type: 'submit' }
  | { type: 'submit-done' }
  | { type: 'submit-failed'; code: ErrorCode }
  | { type: 'cancel' }
  | { type: 'dismiss' };

export const IDLE: LoginFlow = { phase: 'idle' };

export function isLoginBusy(flow: LoginFlow): boolean {
  return flow.phase === 'starting' || flow.phase === 'active';
}

function activeFor(sessionId: string): Extract<LoginFlow, { phase: 'active' }> {
  return {
    phase: 'active',
    sessionId,
    stage: 'starting',
    url: null,
    deviceCode: null,
    needsPaste: false,
    submitting: false,
    pasteError: null,
  };
}

function applyEvent(flow: Extract<LoginFlow, { phase: 'active' }>, message: LoginEventMessage): LoginFlow {
  const { event } = message;
  switch (event.type) {
    case 'url':
      return { ...flow, url: event.url, stage: flow.needsPaste ? flow.stage : 'waiting-browser' };
    case 'device-code':
      return {
        ...flow,
        deviceCode: {
          userCode: event.userCode,
          verificationUrl: event.verificationUrl,
          expiresAt: event.expiresAt ?? null,
        },
        stage: 'waiting-device-code',
      };
    case 'needs-paste':
      return { ...flow, needsPaste: true, stage: 'waiting-paste' };
    case 'progress':
      return { ...flow, stage: event.stage };
    case 'success':
      return { phase: 'success', emailMasked: event.emailMasked ?? null, plan: event.plan ?? null };
    case 'error':
      return { phase: 'error', code: event.code, sessionId: flow.sessionId };
  }
}

export function reduceLogin(flow: LoginFlow, action: LoginAction, accountId: string): LoginFlow {
  switch (action.type) {
    case 'start':
      return isLoginBusy(flow) ? flow : { phase: 'starting', since: action.at };
    case 'started':
      if (flow.phase === 'starting') return activeFor(action.sessionId);
      if (flow.phase === 'active' && flow.sessionId !== action.sessionId) return { ...flow, sessionId: action.sessionId };
      // An error adopted from an older session must not hide the session main just started.
      if (flow.phase === 'error' && flow.sessionId !== null && flow.sessionId !== action.sessionId) {
        return activeFor(action.sessionId);
      }
      return flow;
    case 'start-failed':
      return flow.phase === 'starting' ? { phase: 'error', code: action.code, sessionId: null } : flow;
    case 'event': {
      const { message } = action;
      if (message.accountId !== accountId) return flow;
      // Events may arrive before login:start resolves; adopt their session, but never one emitted
      // before this start (e.g. the 'cancelled' of a session the user just cancelled).
      if (flow.phase === 'starting') {
        return message.at < flow.since ? flow : applyEvent(activeFor(message.sessionId), message);
      }
      if (flow.phase === 'active' && flow.sessionId === message.sessionId) return applyEvent(flow, message);
      return flow;
    }
    case 'submit':
      return flow.phase === 'active' && !flow.submitting ? { ...flow, submitting: true, pasteError: null } : flow;
    case 'submit-done':
      return flow.phase === 'active' ? { ...flow, submitting: false, stage: 'verifying' } : flow;
    case 'submit-failed':
      return flow.phase === 'active' ? { ...flow, submitting: false, pasteError: action.code } : flow;
    case 'cancel':
      return isLoginBusy(flow) ? IDLE : flow;
    case 'dismiss':
      return flow.phase === 'success' || flow.phase === 'error' ? IDLE : flow;
  }
}

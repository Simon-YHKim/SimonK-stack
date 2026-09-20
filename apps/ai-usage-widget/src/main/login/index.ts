import { randomUUID } from 'node:crypto';
import { isAllowedExternalUrl } from '../../shared/ipc';
import type { Account, LoginEvent, LoginEventMessage, ProviderId } from '../../shared/types';
import { IpcHandlerError } from '../ipc/dispatch';
import type { Logger } from '../log';
import type { ProviderAdapter } from '../providers/types';

export const LOGIN_TIMEOUT_MS = 10 * 60_000;

export interface LoginSettled {
  accountId: string;
  sessionId: string;
  event: Extract<LoginEvent, { type: 'success' } | { type: 'error' }>;
}

export interface LoginManagerOptions {
  getAccount(accountId: string): Account | undefined;
  adapterFor(provider: ProviderId): ProviderAdapter;
  emit(message: LoginEventMessage): void;
  onStarted?(accountId: string): void;
  onSettled?(result: LoginSettled): void;
  logger: Logger;
  now?: () => number;
  newSessionId?: () => string;
  timeoutMs?: number;
  /** Host allowlist for opening login URLs; null means any https host the session emitted. */
  allowedHosts?(provider: ProviderId): readonly string[] | null;
}

export interface LoginManager {
  /** Throws IpcHandlerError: not-found (account) or busy (a login is already running for it). */
  start(accountId: string): { sessionId: string };
  cancel(sessionId: string): boolean;
  cancelForAccount(accountId: string): void;
  cancelAll(): void;
  submitPaste(sessionId: string, text: string): Promise<void>;
  /** True only for an https URL emitted by this still-active session (and allowed host). */
  isOpenableUrl(sessionId: string, url: string): boolean;
  isActive(accountId: string): boolean;
  activeCount(): number;
}

interface Session {
  id: string;
  account: Account;
  controller: AbortController;
  urls: Set<string>;
  timer: ReturnType<typeof setTimeout>;
  done: boolean;
}

export function hostAllowed(url: string, hosts: readonly string[] | null): boolean {
  if (hosts === null) return true;
  let host: string;
  try {
    host = new URL(url).hostname.toLowerCase();
  } catch {
    return false;
  }
  return hosts.some((allowed) => {
    const h = allowed.toLowerCase();
    return host === h || host.endsWith(`.${h}`);
  });
}

export function createLoginManager(options: LoginManagerOptions): LoginManager {
  const now = options.now ?? Date.now;
  const newSessionId = options.newSessionId ?? randomUUID;
  const timeoutMs = options.timeoutMs ?? LOGIN_TIMEOUT_MS;
  const logger = options.logger;
  const sessions = new Map<string, Session>();

  const send = (session: Session, event: LoginEvent): void => {
    try {
      options.emit({ sessionId: session.id, accountId: session.account.id, at: now(), event });
    } catch (error) {
      logger.error('login emit failed', { error });
    }
  };

  const finish = (session: Session, event: LoginSettled['event'], emit: boolean): void => {
    if (session.done) return;
    session.done = true;
    clearTimeout(session.timer);
    sessions.delete(session.id);
    session.urls.clear();
    if (emit) send(session, event);
    try {
      options.onSettled?.({ accountId: session.account.id, sessionId: session.id, event });
    } catch (error) {
      logger.error('login onSettled failed', { error });
    }
  };

  const findByAccount = (accountId: string): Session | undefined =>
    [...sessions.values()].find((session) => session.account.id === accountId);

  const abortSession = (session: Session, code: 'cancelled' | 'timeout'): void => {
    finish(session, { type: 'error', code }, true);
    session.controller.abort();
  };

  return {
    start(accountId) {
      const account = options.getAccount(accountId);
      if (account === undefined) throw new IpcHandlerError('not-found');
      if (findByAccount(accountId) !== undefined) throw new IpcHandlerError('busy');
      const adapter = options.adapterFor(account.provider);
      const session: Session = {
        id: newSessionId(),
        account: { ...account },
        controller: new AbortController(),
        urls: new Set(),
        timer: setTimeout(() => {
          logger.warn('login timed out', { provider: account.provider });
          abortSession(session, 'timeout');
        }, timeoutMs),
        done: false,
      };
      sessions.set(session.id, session);
      options.onStarted?.(accountId);

      const emit = (event: LoginEvent): void => {
        if (session.done) return;
        if (event.type === 'url' && isAllowedExternalUrl(event.url)) session.urls.add(event.url);
        if (event.type === 'device-code' && isAllowedExternalUrl(event.verificationUrl)) {
          session.urls.add(event.verificationUrl);
        }
        if (event.type === 'success' || event.type === 'error') {
          finish(session, event, true);
          return;
        }
        send(session, event);
      };

      adapter.startLogin({ ...session.account }, emit, session.controller.signal).then(
        () => {
          if (!session.done) finish(session, { type: 'error', code: 'login-failed' }, true);
        },
        (error: unknown) => {
          logger.error('startLogin rejected', { provider: account.provider, error });
          if (!session.done) finish(session, { type: 'error', code: 'internal' }, true);
        },
      );
      return { sessionId: session.id };
    },

    cancel(sessionId) {
      const session = sessions.get(sessionId);
      if (session === undefined) return false;
      abortSession(session, 'cancelled');
      return true;
    },

    cancelForAccount(accountId) {
      const session = findByAccount(accountId);
      if (session !== undefined) abortSession(session, 'cancelled');
    },

    cancelAll() {
      for (const session of [...sessions.values()]) abortSession(session, 'cancelled');
    },

    async submitPaste(sessionId, text) {
      const session = sessions.get(sessionId);
      if (session === undefined) throw new IpcHandlerError('not-found');
      const adapter = options.adapterFor(session.account.provider);
      if (adapter.submitPaste === undefined) throw new IpcHandlerError('not-implemented');
      await adapter.submitPaste({ ...session.account }, text);
    },

    isOpenableUrl(sessionId, url) {
      const session = sessions.get(sessionId);
      if (session === undefined || session.done) return false;
      if (!isAllowedExternalUrl(url) || !session.urls.has(url)) return false;
      return hostAllowed(url, options.allowedHosts?.(session.account.provider) ?? null);
    },

    isActive: (accountId) => findByAccount(accountId) !== undefined,
    activeCount: () => sessions.size,
  };
}

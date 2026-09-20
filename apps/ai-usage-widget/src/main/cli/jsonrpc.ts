// JSON-RPC over line-delimited stdio. Codex app-server omits the "jsonrpc"
// member ('codex' dialect); ACP (grok agent stdio) uses standard JSON-RPC 2.0.

import type { Logger } from '../log';
import type { LongLivedProcess } from './spawn';

export type JsonRpcDialect = 'jsonrpc2' | 'codex';

export interface JsonRpcTransport {
  writeLine(line: string): boolean;
  onLine(listener: (line: string, truncated: boolean) => void): () => void;
  /** Resolves when the underlying stream is gone. */
  readonly closed: Promise<unknown>;
}

export function transportFromProcess(proc: LongLivedProcess): JsonRpcTransport {
  return { writeLine: (line) => proc.writeLine(line), onLine: (listener) => proc.onStdoutLine(listener), closed: proc.exited };
}

export class JsonRpcError extends Error {
  readonly code: number;
  readonly data: unknown;
  constructor(code: number, message: string, data?: unknown) {
    super(message);
    this.name = 'JsonRpcError';
    this.code = code;
    this.data = data;
  }
}

export class JsonRpcTimeoutError extends Error {
  readonly method: string;
  constructor(method: string) {
    super(`request timed out: ${method}`);
    this.name = 'JsonRpcTimeoutError';
    this.method = method;
  }
}

export class JsonRpcClosedError extends Error {
  constructor(reason: string) {
    super(`connection closed: ${reason}`);
    this.name = 'JsonRpcClosedError';
  }
}

export class JsonRpcAbortedError extends Error {
  constructor(method: string) {
    super(`request aborted: ${method}`);
    this.name = 'JsonRpcAbortedError';
  }
}

export type JsonRpcId = number | string;

export type JsonRpcMessage =
  | { kind: 'response'; id: JsonRpcId; result: unknown }
  | { kind: 'error-response'; id: JsonRpcId | null; error: { code: number; message: string; data?: unknown } }
  | { kind: 'request'; id: JsonRpcId; method: string; params: unknown }
  | { kind: 'notification'; method: string; params: unknown };

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isId(value: unknown): value is JsonRpcId {
  return (typeof value === 'number' && Number.isFinite(value)) || typeof value === 'string';
}

/** Classifies one decoded line; returns null for non-JSON or non-RPC lines. */
export function parseJsonRpcLine(line: string): JsonRpcMessage | null {
  const trimmed = line.trim();
  if (!trimmed.startsWith('{')) return null;
  let value: unknown;
  try {
    value = JSON.parse(trimmed) as unknown;
  } catch {
    return null;
  }
  if (!isObject(value)) return null;
  const { id, method } = value;
  if (typeof method === 'string') {
    if (isId(id)) return { kind: 'request', id, method, params: value.params };
    if (id === undefined) return { kind: 'notification', method, params: value.params };
    return null;
  }
  if ('error' in value && isObject(value.error)) {
    const err = value.error;
    const code = typeof err.code === 'number' ? err.code : -32603;
    const message = typeof err.message === 'string' ? err.message : 'unknown error';
    return { kind: 'error-response', id: isId(id) ? id : null, error: { code, message, data: err.data } };
  }
  if (isId(id) && 'result' in value) return { kind: 'response', id, result: value.result };
  return null;
}

export interface RequestOptions {
  timeoutMs?: number;
  signal?: AbortSignal;
}

export interface JsonRpcClient {
  request<T = unknown>(method: string, params?: unknown, options?: RequestOptions): Promise<T>;
  notify(method: string, params?: unknown): void;
  onNotification(method: string, listener: (params: unknown) => void): () => void;
  /** Handles server-to-client requests. Unhandled methods get -32601. */
  onRequest(method: string, handler: (params: unknown) => unknown): () => void;
  close(reason?: string): void;
  readonly isClosed: boolean;
}

export interface JsonRpcClientOptions {
  dialect: JsonRpcDialect;
  defaultTimeoutMs: number;
  logger?: Logger;
}

interface Pending {
  method: string;
  resolve: (value: unknown) => void;
  reject: (error: Error) => void;
  timer: ReturnType<typeof setTimeout>;
  cleanupAbort: () => void;
}

export function createJsonRpcClient(transport: JsonRpcTransport, options: JsonRpcClientOptions): JsonRpcClient {
  const pending = new Map<JsonRpcId, Pending>();
  const notificationListeners = new Map<string, Set<(params: unknown) => void>>();
  const requestHandlers = new Map<string, (params: unknown) => unknown>();
  let nextId = 1;
  let closed = false;

  const envelope = (body: Record<string, unknown>): Record<string, unknown> =>
    options.dialect === 'jsonrpc2' ? { jsonrpc: '2.0', ...body } : body;

  const send = (body: Record<string, unknown>): boolean => {
    if (closed) return false;
    return transport.writeLine(JSON.stringify(envelope(body)));
  };

  const settle = (id: JsonRpcId, outcome: { value?: unknown; error?: Error }): void => {
    const entry = pending.get(id);
    if (entry === undefined) return;
    pending.delete(id);
    clearTimeout(entry.timer);
    entry.cleanupAbort();
    if (outcome.error !== undefined) entry.reject(outcome.error);
    else entry.resolve(outcome.value);
  };

  const handleIncomingRequest = async (id: JsonRpcId, method: string, params: unknown): Promise<void> => {
    const handler = requestHandlers.get(method);
    if (handler === undefined) {
      send({ id, error: { code: -32601, message: 'Method not found' } });
      return;
    }
    try {
      const result = await handler(params);
      send({ id, result: result ?? null });
    } catch (error) {
      const code = error instanceof JsonRpcError ? error.code : -32603;
      const message = error instanceof JsonRpcError ? error.message : 'Internal error';
      send({ id, error: { code, message } });
    }
  };

  const unsubscribeLines = transport.onLine((line, truncated) => {
    if (truncated) {
      options.logger?.warn('jsonrpc: dropped oversized line');
      return;
    }
    const message = parseJsonRpcLine(line);
    if (message === null) {
      if (line.trim().length > 0) options.logger?.debug('jsonrpc: ignored non-rpc line');
      return;
    }
    switch (message.kind) {
      case 'response':
        settle(message.id, { value: message.result });
        break;
      case 'error-response':
        if (message.id !== null) {
          settle(message.id, {
            error: new JsonRpcError(message.error.code, message.error.message, message.error.data),
          });
        }
        break;
      case 'request':
        void handleIncomingRequest(message.id, message.method, message.params);
        break;
      case 'notification':
        for (const listener of notificationListeners.get(message.method) ?? []) {
          try {
            listener(message.params);
          } catch (error) {
            options.logger?.warn('jsonrpc: notification listener threw', error);
          }
        }
        break;
    }
  });

  const client: JsonRpcClient = {
    get isClosed() {
      return closed;
    },
    request<T>(method: string, params?: unknown, requestOptions: RequestOptions = {}): Promise<T> {
      if (closed) return Promise.reject(new JsonRpcClosedError('client closed'));
      if (requestOptions.signal?.aborted === true) return Promise.reject(new JsonRpcAbortedError(method));
      const id = nextId;
      nextId += 1;
      return new Promise<T>((resolve, reject) => {
        const timeoutMs = requestOptions.timeoutMs ?? options.defaultTimeoutMs;
        const timer = setTimeout(() => settle(id, { error: new JsonRpcTimeoutError(method) }), timeoutMs);
        const onAbort = (): void => settle(id, { error: new JsonRpcAbortedError(method) });
        requestOptions.signal?.addEventListener('abort', onAbort, { once: true });
        pending.set(id, {
          method,
          resolve: (value) => resolve(value as T),
          reject,
          timer,
          cleanupAbort: () => requestOptions.signal?.removeEventListener('abort', onAbort),
        });
        const body: Record<string, unknown> = { id, method };
        if (params !== undefined) body.params = params;
        if (!send(body)) settle(id, { error: new JsonRpcClosedError('write failed') });
      });
    },
    notify(method, params) {
      const body: Record<string, unknown> = { method };
      if (params !== undefined) body.params = params;
      send(body);
    },
    onNotification(method, listener) {
      let set = notificationListeners.get(method);
      if (set === undefined) {
        set = new Set();
        notificationListeners.set(method, set);
      }
      set.add(listener);
      return () => set.delete(listener);
    },
    onRequest(method, handler) {
      requestHandlers.set(method, handler);
      return () => {
        if (requestHandlers.get(method) === handler) requestHandlers.delete(method);
      };
    },
    close(reason = 'closed by client') {
      if (closed) return;
      closed = true;
      unsubscribeLines();
      for (const id of [...pending.keys()]) settle(id, { error: new JsonRpcClosedError(reason) });
    },
  };

  void transport.closed.then(() => client.close('transport closed'));
  return client;
}

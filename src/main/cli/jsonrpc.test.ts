import { describe, expect, it } from 'vitest';
import {
  JsonRpcAbortedError,
  JsonRpcClosedError,
  JsonRpcError,
  JsonRpcTimeoutError,
  createJsonRpcClient,
  parseJsonRpcLine,
  type JsonRpcTransport,
} from './jsonrpc';

function fakeTransport(): {
  transport: JsonRpcTransport;
  written: Record<string, unknown>[];
  emit: (message: unknown) => void;
  close: () => void;
} {
  const written: Record<string, unknown>[] = [];
  const listeners = new Set<(line: string, truncated: boolean) => void>();
  let resolveClosed: () => void = () => undefined;
  const closed = new Promise<void>((resolve) => {
    resolveClosed = resolve;
  });
  return {
    transport: {
      writeLine: (line) => {
        written.push(JSON.parse(line) as Record<string, unknown>);
        return true;
      },
      onLine: (listener) => {
        listeners.add(listener);
        return () => listeners.delete(listener);
      },
      closed,
    },
    written,
    emit: (message) => {
      const line = typeof message === 'string' ? message : JSON.stringify(message);
      for (const listener of listeners) listener(line, false);
    },
    close: () => resolveClosed(),
  };
}

const tick = (): Promise<void> => new Promise((resolve) => setTimeout(resolve, 0));

describe('parseJsonRpcLine', () => {
  it('classifies messages', () => {
    expect(parseJsonRpcLine('{"id":1,"result":{}}')).toEqual({ kind: 'response', id: 1, result: {} });
    expect(parseJsonRpcLine('{"id":2,"error":{"code":-1,"message":"x"}}')).toMatchObject({ kind: 'error-response', id: 2 });
    expect(parseJsonRpcLine('{"id":"a","method":"m","params":1}')).toEqual({ kind: 'request', id: 'a', method: 'm', params: 1 });
    expect(parseJsonRpcLine('{"method":"n"}')).toEqual({ kind: 'notification', method: 'n', params: undefined });
    expect(parseJsonRpcLine('Starting server...')).toBeNull();
    expect(parseJsonRpcLine('{broken')).toBeNull();
    expect(parseJsonRpcLine('[1,2]')).toBeNull();
  });
});

describe('createJsonRpcClient', () => {
  it('matches responses by id and omits "jsonrpc" in codex dialect', async () => {
    const fake = fakeTransport();
    const client = createJsonRpcClient(fake.transport, { dialect: 'codex', defaultTimeoutMs: 1000 });
    const first = client.request('initialize', { clientInfo: { name: 'ai-usage-widget' } });
    const second = client.request('account/read');
    expect(fake.written[0]).toEqual({ id: 1, method: 'initialize', params: { clientInfo: { name: 'ai-usage-widget' } } });
    expect(fake.written[1]).toEqual({ id: 2, method: 'account/read' });
    fake.emit({ id: 2, result: 'b' });
    fake.emit({ id: 1, result: 'a' });
    await expect(first).resolves.toBe('a');
    await expect(second).resolves.toBe('b');
  });

  it('adds "jsonrpc":"2.0" in jsonrpc2 dialect', () => {
    const fake = fakeTransport();
    const client = createJsonRpcClient(fake.transport, { dialect: 'jsonrpc2', defaultTimeoutMs: 1000 });
    client.notify('initialized');
    expect(fake.written[0]).toEqual({ jsonrpc: '2.0', method: 'initialized' });
  });

  it('rejects with JsonRpcError on error responses', async () => {
    const fake = fakeTransport();
    const client = createJsonRpcClient(fake.transport, { dialect: 'jsonrpc2', defaultTimeoutMs: 1000 });
    const pending = client.request('x');
    fake.emit({ jsonrpc: '2.0', id: 1, error: { code: -32601, message: 'Method not found' } });
    await expect(pending).rejects.toBeInstanceOf(JsonRpcError);
  });

  it('times out and aborts', async () => {
    const fake = fakeTransport();
    const client = createJsonRpcClient(fake.transport, { dialect: 'codex', defaultTimeoutMs: 1000 });
    await expect(client.request('slow', undefined, { timeoutMs: 20 })).rejects.toBeInstanceOf(JsonRpcTimeoutError);
    const controller = new AbortController();
    const pending = client.request('slow', undefined, { signal: controller.signal });
    controller.abort();
    await expect(pending).rejects.toBeInstanceOf(JsonRpcAbortedError);
  });

  it('dispatches notifications and answers server requests', async () => {
    const fake = fakeTransport();
    const client = createJsonRpcClient(fake.transport, { dialect: 'jsonrpc2', defaultTimeoutMs: 1000 });
    const seen: unknown[] = [];
    client.onNotification('account/rateLimits/updated', (params) => seen.push(params));
    client.onRequest('session/request_permission', () => ({ outcome: 'cancelled' }));
    fake.emit({ method: 'account/rateLimits/updated', params: { a: 1 } });
    fake.emit({ jsonrpc: '2.0', id: 7, method: 'session/request_permission', params: {} });
    fake.emit({ jsonrpc: '2.0', id: 8, method: 'fs/write_text_file', params: {} });
    await tick();
    expect(seen).toEqual([{ a: 1 }]);
    expect(fake.written).toContainEqual({ jsonrpc: '2.0', id: 7, result: { outcome: 'cancelled' } });
    expect(fake.written).toContainEqual({ jsonrpc: '2.0', id: 8, error: { code: -32601, message: 'Method not found' } });
  });

  it('rejects pending requests when the transport closes', async () => {
    const fake = fakeTransport();
    const client = createJsonRpcClient(fake.transport, { dialect: 'codex', defaultTimeoutMs: 5000 });
    const pending = client.request('never');
    fake.close();
    await expect(pending).rejects.toBeInstanceOf(JsonRpcClosedError);
    expect(client.isClosed).toBe(true);
    await expect(client.request('after')).rejects.toBeInstanceOf(JsonRpcClosedError);
  });
});

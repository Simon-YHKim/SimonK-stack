import {
  validateInvokeRequest,
  type InvokeChannel,
  type InvokeRequest,
  type InvokeResponse,
  type IpcError,
  type IpcErrorCode,
  type IpcResult,
} from '../../shared/ipc';
import type { ErrorCode, ViewId } from '../../shared/types';
import type { Logger } from '../log';

export interface InvokeContext {
  senderUrl: string;
  view: ViewId | null;
}

export type InvokeHandler<C extends InvokeChannel> = (
  request: InvokeRequest<C>,
  context: InvokeContext,
) => InvokeResponse<C> | Promise<InvokeResponse<C>>;

export type InvokeHandlers = { [C in InvokeChannel]?: InvokeHandler<C> };

/** Throw from a handler to return a specific envelope error instead of 'internal'. */
export class IpcHandlerError extends Error {
  readonly code: IpcErrorCode;
  readonly detail: ErrorCode | undefined;
  constructor(code: IpcErrorCode, detail?: ErrorCode) {
    super(code);
    this.name = 'IpcHandlerError';
    this.code = code;
    this.detail = detail;
  }
}

export interface DispatchDeps {
  isTrustedSender(url: string): boolean;
  logger: Logger;
}

/** Sender check -> payload validation -> handler, always resolving to an IpcResult. */
export async function dispatchInvoke<C extends InvokeChannel>(
  channel: C,
  payload: unknown,
  context: InvokeContext,
  handlers: InvokeHandlers,
  deps: DispatchDeps,
): Promise<IpcResult<InvokeResponse<C>>> {
  if (!deps.isTrustedSender(context.senderUrl)) {
    deps.logger.warn('ipc: rejected untrusted sender', { channel });
    return { ok: false, error: { code: 'forbidden-sender' } };
  }
  const parsed = validateInvokeRequest(channel, payload);
  if (!parsed.ok) {
    deps.logger.warn('ipc: invalid request', { channel, reason: parsed.error });
    return { ok: false, error: { code: 'invalid-request' } };
  }
  const handler = handlers[channel];
  if (handler === undefined) return { ok: false, error: { code: 'not-implemented' } };
  try {
    const value = await handler(parsed.value, context);
    return { ok: true, value };
  } catch (error) {
    if (error instanceof IpcHandlerError) {
      const envelope: IpcError = { code: error.code };
      if (error.detail !== undefined) envelope.detail = error.detail;
      return { ok: false, error: envelope };
    }
    deps.logger.error('ipc: handler failed', { channel, error });
    return { ok: false, error: { code: 'internal' } };
  }
}

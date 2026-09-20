import {
  isEventChannel,
  isInvokeChannel,
  validateInvokeRequest,
  type EventChannel,
  type EventContract,
  type InvokeChannel,
  type InvokeRequest,
  type InvokeResponse,
  type IpcResult,
  type PreloadApi,
} from '../shared/ipc';

/** The subset of Electron's ipcRenderer the bridge needs (injectable for tests). */
export interface IpcRendererLike {
  invoke(channel: string, ...args: unknown[]): Promise<unknown>;
  on(channel: string, listener: (event: unknown, ...args: unknown[]) => void): unknown;
  removeListener(channel: string, listener: (event: unknown, ...args: unknown[]) => void): unknown;
}

const INVALID: IpcResult<never> = { ok: false, error: { code: 'invalid-request' } };
const INTERNAL: IpcResult<never> = { ok: false, error: { code: 'internal' } };

/**
 * Typed, allowlisted API. Requests are validated here as well as in main so a
 * malformed call never reaches IPC; ipcRenderer itself is never exposed.
 */
export function createPreloadApi(ipc: IpcRendererLike): PreloadApi {
  const api: PreloadApi = {
    invoke<C extends InvokeChannel>(channel: C, request: InvokeRequest<C>): Promise<IpcResult<InvokeResponse<C>>> {
      if (!isInvokeChannel(channel)) return Promise.resolve(INVALID);
      const parsed = validateInvokeRequest(channel, request);
      if (!parsed.ok) return Promise.resolve(INVALID);
      return ipc.invoke(channel, parsed.value).then(
        (result) => result as IpcResult<InvokeResponse<C>>,
        () => INTERNAL,
      );
    },
    on<E extends EventChannel>(channel: E, listener: (payload: EventContract[E]) => void): () => void {
      if (!isEventChannel(channel) || typeof listener !== 'function') return () => undefined;
      const wrapped = (_event: unknown, payload: unknown): void => listener(payload as EventContract[E]);
      ipc.on(channel, wrapped);
      let subscribed = true;
      return () => {
        if (!subscribed) return;
        subscribed = false;
        ipc.removeListener(channel, wrapped);
      };
    },
  };
  return Object.freeze(api);
}

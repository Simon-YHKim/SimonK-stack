import { contextBridge, ipcRenderer, type IpcRendererEvent } from 'electron';
import {
  PRELOAD_GLOBAL,
  isEventChannel,
  isInvokeChannel,
  type EventChannel,
  type EventContract,
  type InvokeChannel,
  type InvokeRequest,
  type InvokeResponse,
  type IpcResult,
  type PreloadApi,
} from '../shared/ipc';

// Only allowlisted channels cross the bridge; ipcRenderer itself is never exposed.
const api: PreloadApi = {
  invoke<C extends InvokeChannel>(channel: C, request: InvokeRequest<C>): Promise<IpcResult<InvokeResponse<C>>> {
    if (!isInvokeChannel(channel)) {
      return Promise.resolve({ ok: false, error: { code: 'invalid-request' } });
    }
    return ipcRenderer.invoke(channel, request) as Promise<IpcResult<InvokeResponse<C>>>;
  },
  on<E extends EventChannel>(channel: E, listener: (payload: EventContract[E]) => void): () => void {
    if (!isEventChannel(channel)) return () => undefined;
    const wrapped = (_event: IpcRendererEvent, payload: EventContract[E]): void => listener(payload);
    ipcRenderer.on(channel, wrapped);
    return () => {
      ipcRenderer.removeListener(channel, wrapped);
    };
  },
};

contextBridge.exposeInMainWorld(PRELOAD_GLOBAL, api);

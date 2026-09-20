import type { IpcMain, IpcMainInvokeEvent, WebContents } from 'electron';
import { INVOKE_CHANNELS, type EventChannel, type EventContract } from '../../shared/ipc';
import { viewFromUrl } from '../protocol/urls';
import { dispatchInvoke, type DispatchDeps, type InvokeHandlers } from './dispatch';

/** URL of the sending top-level frame; subframes are treated as untrusted (empty URL). */
function senderUrlOf(event: IpcMainInvokeEvent): string {
  const frame = event.senderFrame;
  if (frame === null || frame.parent !== null) return '';
  return frame.url;
}

export function registerInvokeHandlers(ipcMain: IpcMain, handlers: InvokeHandlers, deps: DispatchDeps): () => void {
  for (const channel of INVOKE_CHANNELS) {
    ipcMain.handle(channel, (event, payload: unknown) => {
      const senderUrl = senderUrlOf(event);
      return dispatchInvoke(channel, payload, { senderUrl, view: viewFromUrl(senderUrl) }, handlers, deps);
    });
  }
  return () => {
    for (const channel of INVOKE_CHANNELS) ipcMain.removeHandler(channel);
  };
}

export function sendEvent<E extends EventChannel>(
  target: WebContents | null | undefined,
  channel: E,
  payload: EventContract[E],
): void {
  if (target === null || target === undefined || target.isDestroyed()) return;
  target.send(channel, payload);
}

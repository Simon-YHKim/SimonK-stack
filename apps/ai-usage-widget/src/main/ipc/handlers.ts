import type { InvokeChannel } from '../../shared/ipc';
import type { AppController } from '../app/controller';
import { IpcHandlerError, type InvokeContext, type InvokeHandler } from './dispatch';

export type AllInvokeHandlers = { [C in InvokeChannel]: InvokeHandler<C> };

function requireView(context: InvokeContext, view: 'widget' | 'popup'): void {
  if (context.view !== view) throw new IpcHandlerError('forbidden-sender');
}

/** Wraps a handler so only the given view may call it (defence in depth; both views load the same bundle). */
function only<C extends InvokeChannel>(view: 'widget' | 'popup', handler: InvokeHandler<C>): InvokeHandler<C> {
  return (request, context) => {
    requireView(context, view);
    return handler(request, context);
  };
}

/**
 * Maps every contract channel to the controller; the mapped type fails typecheck if one is missing.
 * State-changing channels are limited to the view whose UI uses them: the widget only reads
 * state, refreshes, opens the popup and reports its size.
 */
export function createInvokeHandlers(controller: AppController): AllInvokeHandlers {
  return {
    'app:get-state': () => controller.snapshot(),
    'app:renderer-ready': (request) => controller.onRendererReady(request),
    'settings:get': () => controller.getSettings(),
    'settings:update': only('popup', (request) => controller.updateSettings(request.patch)),
    'accounts:list': () => controller.listAccounts(),
    'accounts:add': only('popup', (request) => controller.addAccount(request.provider, request.label)),
    'accounts:remove': only('popup', (request) => controller.removeAccount(request.accountId)),
    'accounts:rename': only('popup', (request) => controller.renameAccount(request.accountId, request.label)),
    'accounts:toggle': only('popup', (request) => controller.toggleAccount(request.accountId, request.enabled)),
    'accounts:reorder': only('popup', (request) => controller.reorderAccount(request.accountId, request.direction)),
    'login:start': only('popup', (request) => controller.startLogin(request.accountId)),
    'login:cancel': only('popup', (request) => controller.cancelLogin(request.sessionId)),
    'login:submit-paste': only('popup', (request) => controller.submitLoginPaste(request.sessionId, request.text)),
    'usage:refresh-now': (request) => controller.refreshNow(request.accountId),
    'shell:open-external': only('popup', (request) => controller.openExternal(request)),
    'window:toggle-popup': () => controller.togglePopup(),
    'window:show-popup': (request) => controller.showPopup(request.tab),
    'window:hide-popup': only('popup', () => controller.hidePopup()),
    'window:set-popup-lock': only('popup', (request) => controller.setPopupLock(request.locked)),
    'window:resize-widget': only('widget', (request) => controller.resizeWidget(request)),
    'window:preview-placement': only('popup', (request) => controller.previewPlacement(request.patch)),
    'cli:redetect': only('popup', (request) => controller.redetectCli(request.provider)),
    'claude-bridge:status': () => controller.bridgeStatus(),
    'claude-bridge:install-default': only('popup', (request) => controller.bridgeInstallDefault(request.accountId)),
    'claude-bridge:uninstall-default': only('popup', () => controller.bridgeUninstallDefault()),
  };
}

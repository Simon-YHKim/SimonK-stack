import type { InvokeChannel } from '../../shared/ipc';
import type { AppController } from '../app/controller';
import { IpcHandlerError, type InvokeContext, type InvokeHandler } from './dispatch';

export type AllInvokeHandlers = { [C in InvokeChannel]: InvokeHandler<C> };

function requireView(context: InvokeContext, view: 'widget' | 'popup'): void {
  if (context.view !== view) throw new IpcHandlerError('forbidden-sender');
}

/** Maps every contract channel to the controller; the mapped type fails typecheck if one is missing. */
export function createInvokeHandlers(controller: AppController): AllInvokeHandlers {
  return {
    'app:get-state': () => controller.snapshot(),
    'app:renderer-ready': (request) => controller.onRendererReady(request),
    'settings:get': () => controller.getSettings(),
    'settings:update': (request) => controller.updateSettings(request.patch),
    'accounts:list': () => controller.listAccounts(),
    'accounts:add': (request) => controller.addAccount(request.provider, request.label),
    'accounts:remove': (request) => controller.removeAccount(request.accountId),
    'accounts:rename': (request) => controller.renameAccount(request.accountId, request.label),
    'accounts:toggle': (request) => controller.toggleAccount(request.accountId, request.enabled),
    'accounts:reorder': (request) => controller.reorderAccount(request.accountId, request.direction),
    'login:start': (request) => controller.startLogin(request.accountId),
    'login:cancel': (request) => controller.cancelLogin(request.sessionId),
    'login:submit-paste': (request) => controller.submitLoginPaste(request.sessionId, request.text),
    'usage:refresh-now': (request) => controller.refreshNow(request.accountId),
    'shell:open-external': (request) => controller.openExternal(request),
    'window:toggle-popup': () => controller.togglePopup(),
    'window:show-popup': (request) => controller.showPopup(request.tab),
    'window:hide-popup': () => controller.hidePopup(),
    'window:set-popup-lock': (request, context) => {
      requireView(context, 'popup');
      return controller.setPopupLock(request.locked);
    },
    'window:resize-widget': (request, context) => {
      requireView(context, 'widget');
      return controller.resizeWidget(request);
    },
    'claude-bridge:status': () => controller.bridgeStatus(),
    'claude-bridge:install-default': (request) => controller.bridgeInstallDefault(request.accountId),
    'claude-bridge:uninstall-default': () => controller.bridgeUninstallDefault(),
  };
}

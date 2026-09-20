import { app, type Session } from 'electron';
import type { Logger } from '../log';

/** Denies window.open, foreign navigation and webviews for every WebContents. Call before ready. */
export function hardenApp(isTrustedUrl: (url: string) => boolean, logger: Logger): void {
  app.on('web-contents-created', (_event, contents) => {
    contents.setWindowOpenHandler(() => {
      logger.warn('blocked window.open');
      return { action: 'deny' };
    });
    contents.on('will-navigate', (event) => {
      if (!isTrustedUrl(event.url)) {
        event.preventDefault();
        logger.warn('blocked navigation');
      }
    });
    contents.on('will-redirect', (event) => {
      if (!isTrustedUrl(event.url)) {
        event.preventDefault();
        logger.warn('blocked redirect');
      }
    });
    contents.on('will-attach-webview', (event) => {
      event.preventDefault();
    });
  });
}

/** Denies all permission requests; injects CSP for dev-server responses when given. */
export function hardenSession(target: Session, devCspValue: string | undefined): void {
  target.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
  target.setPermissionCheckHandler(() => false);
  if (devCspValue !== undefined) {
    target.webRequest.onHeadersReceived((details, callback) => {
      callback({
        responseHeaders: { ...details.responseHeaders, 'Content-Security-Policy': [devCspValue] },
      });
    });
  }
}

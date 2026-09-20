import { readFile } from 'node:fs/promises';
import { protocol } from 'electron';
import type { Logger } from '../log';
import { APP_SCHEME, PROD_CSP, contentTypeFor, resolveBundlePath } from './urls';

/** Must run before `app.whenReady()`. */
export function registerAppSchemePrivileges(): void {
  protocol.registerSchemesAsPrivileged([
    {
      scheme: APP_SCHEME,
      privileges: { standard: true, secure: true, supportFetchAPI: false, corsEnabled: false, stream: false },
    },
  ]);
}

/** Serves the built renderer from `rendererRoot` with CSP and nosniff headers. */
export function handleAppProtocol(rendererRoot: string, logger: Logger): void {
  protocol.handle(APP_SCHEME, async (request) => {
    if (request.method !== 'GET') return new Response(null, { status: 405 });
    const file = resolveBundlePath(rendererRoot, request.url);
    if (file === null) {
      logger.warn('app protocol: rejected path');
      return new Response(null, { status: 404 });
    }
    try {
      const body = await readFile(file);
      return new Response(body, {
        status: 200,
        headers: {
          'Content-Type': contentTypeFor(file),
          'Content-Security-Policy': PROD_CSP,
          'X-Content-Type-Options': 'nosniff',
          'Referrer-Policy': 'no-referrer',
        },
      });
    } catch {
      return new Response(null, { status: 404 });
    }
  });
}

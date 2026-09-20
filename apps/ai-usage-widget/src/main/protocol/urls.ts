import path from 'node:path';
import { VIEW_IDS, type ViewId } from '../../shared/types';
import { isPathInside } from '../paths';

export const APP_SCHEME = 'app';
export const APP_HOST = 'bundle';
export const APP_ORIGIN = `${APP_SCHEME}://${APP_HOST}`;

/** Production CSP sent as a response header (meta CSP ignores frame-ancestors, RESEARCH §2). */
export const PROD_CSP = [
  "default-src 'none'",
  "script-src 'self'",
  "style-src 'self'",
  "img-src 'self' data:",
  "font-src 'self'",
  "connect-src 'none'",
  "object-src 'none'",
  "base-uri 'none'",
  "form-action 'none'",
  "frame-ancestors 'none'",
].join('; ');

/** Development CSP: Vite dev server origin, HMR websocket and injected styles. */
export function devCsp(devServerUrl: string): string {
  const url = new URL(devServerUrl);
  const ws = `ws://${url.host}`;
  return [
    "default-src 'none'",
    `script-src 'self' ${url.origin}`,
    `style-src 'self' 'unsafe-inline' ${url.origin}`,
    `img-src 'self' data: ${url.origin}`,
    `font-src 'self' ${url.origin}`,
    `connect-src ${url.origin} ${ws}`,
    "object-src 'none'",
    "base-uri 'none'",
    "form-action 'none'",
    "frame-ancestors 'none'",
  ].join('; ');
}

export function rendererEntryUrl(view: ViewId, devServerUrl: string | undefined): string {
  if (devServerUrl !== undefined) {
    const url = new URL('index.html', devServerUrl.endsWith('/') ? devServerUrl : `${devServerUrl}/`);
    url.searchParams.set('view', view);
    return url.toString();
  }
  return `${APP_ORIGIN}/index.html?view=${view}`;
}

export function viewFromUrl(value: string): ViewId | null {
  try {
    const view = new URL(value).searchParams.get('view');
    return VIEW_IDS.find((id) => id === view) ?? null;
  } catch {
    return null;
  }
}

/** Renderer pages we trust for IPC and navigation: app://bundle, or the dev server when unpackaged. */
export function isTrustedRendererUrl(value: string, devServerUrl: string | undefined): boolean {
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    return false;
  }
  if (url.protocol === `${APP_SCHEME}:` && url.host === APP_HOST) return true;
  if (devServerUrl === undefined) return false;
  try {
    return url.origin === new URL(devServerUrl).origin;
  } catch {
    return false;
  }
}

/** Maps an app:// request to a file under `rendererRoot`, or null (wrong host, traversal, NUL). */
export function resolveBundlePath(rendererRoot: string, requestUrl: string): string | null {
  let url: URL;
  try {
    url = new URL(requestUrl);
  } catch {
    return null;
  }
  if (url.protocol !== `${APP_SCHEME}:` || url.host !== APP_HOST) return null;
  let pathname: string;
  try {
    pathname = decodeURIComponent(url.pathname);
  } catch {
    return null;
  }
  if (pathname.includes('\0') || pathname.includes('\\')) return null;
  if (pathname === '/' || pathname === '') pathname = '/index.html';
  const root = path.resolve(rendererRoot);
  const file = path.resolve(root, `.${pathname}`);
  return isPathInside(root, file) ? file : null;
}

const CONTENT_TYPES: Readonly<Record<string, string>> = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
};

export function contentTypeFor(filePath: string): string {
  return CONTENT_TYPES[path.extname(filePath).toLowerCase()] ?? 'application/octet-stream';
}

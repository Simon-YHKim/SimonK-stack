import path from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  PROD_CSP,
  contentTypeFor,
  devCsp,
  isTrustedRendererUrl,
  rendererEntryUrl,
  resolveBundlePath,
  viewFromUrl,
} from './urls';

const ROOT = path.resolve('/app/out/renderer');

describe('protocol urls', () => {
  it('maps app://bundle paths inside the renderer root', () => {
    expect(resolveBundlePath(ROOT, 'app://bundle/index.html?view=widget')).toBe(path.join(ROOT, 'index.html'));
    expect(resolveBundlePath(ROOT, 'app://bundle/')).toBe(path.join(ROOT, 'index.html'));
    expect(resolveBundlePath(ROOT, 'app://bundle/assets/index-abc.js')).toBe(path.join(ROOT, 'assets', 'index-abc.js'));
  });

  it('rejects traversal, other hosts and schemes', () => {
    // The URL parser folds literal dot segments at the root, so this stays inside the bundle.
    expect(resolveBundlePath(ROOT, 'app://bundle/../main/index.js')).toBe(path.join(ROOT, 'main', 'index.js'));
    // Percent-encoded dot segments are folded the same way (WHATWG URL), so they cannot escape.
    expect(resolveBundlePath(ROOT, 'app://bundle/%2e%2e/%2e%2e/secret')).toBe(path.join(ROOT, 'secret'));
    expect(resolveBundlePath(ROOT, 'app://bundle/..%5c..%5csecret')).toBeNull();
    expect(resolveBundlePath(ROOT, 'app://bundle/a%00b')).toBeNull();
    expect(resolveBundlePath(ROOT, 'app://other/index.html')).toBeNull();
    expect(resolveBundlePath(ROOT, 'file:///C:/Windows/win.ini')).toBeNull();
    expect(resolveBundlePath(ROOT, 'app://bundle/%E0%A4%A')).toBeNull();
  });

  it('trusts only the bundle origin or the dev server', () => {
    expect(isTrustedRendererUrl('app://bundle/index.html?view=popup', undefined)).toBe(true);
    expect(isTrustedRendererUrl('app://evil/index.html', undefined)).toBe(false);
    expect(isTrustedRendererUrl('http://localhost:5173/index.html', undefined)).toBe(false);
    expect(isTrustedRendererUrl('http://localhost:5173/index.html', 'http://localhost:5173')).toBe(true);
    expect(isTrustedRendererUrl('https://example.com/', 'http://localhost:5173')).toBe(false);
    expect(isTrustedRendererUrl('', undefined)).toBe(false);
  });

  it('builds entry URLs and reads the view back', () => {
    expect(rendererEntryUrl('widget', undefined)).toBe('app://bundle/index.html?view=widget');
    expect(rendererEntryUrl('popup', 'http://localhost:5173')).toBe('http://localhost:5173/index.html?view=popup');
    expect(viewFromUrl('app://bundle/index.html?view=popup')).toBe('popup');
    expect(viewFromUrl('app://bundle/index.html?view=admin')).toBeNull();
    expect(viewFromUrl('nonsense')).toBeNull();
  });

  it('CSP policies', () => {
    expect(PROD_CSP).toContain("default-src 'none'");
    expect(PROD_CSP).toContain("frame-ancestors 'none'");
    expect(PROD_CSP).not.toContain('unsafe');
    expect(devCsp('http://localhost:5173')).toContain('ws://localhost:5173');
  });

  it('content types', () => {
    expect(contentTypeFor('a/index.html')).toBe('text/html; charset=utf-8');
    expect(contentTypeFor('a/x.JS')).toBe('text/javascript; charset=utf-8');
    expect(contentTypeFor('a/x.bin')).toBe('application/octet-stream');
  });
});

import type { ProviderId } from '../../shared/types';
import claudeIconUrl from '../../../resources/icons/claude_64.png';
import antigravityIconUrl from '../../../resources/icons/antigravity_64.png';
import codexIconUrl from '../../../resources/icons/codex_64.png';
import { h, s, setStyles } from './dom';

// Bundled at build time; Vite may inline small files as data:image/png URIs (allowed by img-src).
const PNG_ICONS: Readonly<Partial<Record<ProviderId, string>>> = {
  claude: claudeIconUrl,
  codex: codexIconUrl,
  antigravity: antigravityIconUrl,
};

function isBundledAssetUrl(url: string): boolean {
  return url.startsWith('data:image/png;base64,') || !/^[a-z][a-z0-9+.-]*:/i.test(url) || url.startsWith('app:');
}

// v1 SVG glyphs (SPEC §2-2) plus a neutral Grok mark.
const CLAUDE_PATH =
  'M12 2l1.2 5.5L18 4l-3 4.8 5.8.5-5 3 4.2 4-5.4.3 2 5.4-4.8-3-1 5.8-1.5-5.5-4.5 3.5 1.5-5.5-5.5-1 5-3.2-4-4.5 5.5 1L10.5 2z';
const CODEX_CLOUD_PATH =
  'M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z';
const CODEX_PROMPT_PATH = 'M7.5 11.5l2.5 2.5-2.5 2.5M12.5 16.5h3';

/** Inline SVG glyph. Mono draws everything in currentColor (V1-33). */
export function providerGlyph(provider: ProviderId, size: number, mono: boolean): SVGSVGElement {
  const attrs = { viewBox: '0 0 24 24', width: size, height: size, 'aria-hidden': 'true', focusable: 'false' };
  if (provider === 'claude') {
    return s('svg', attrs, [s('path', { d: CLAUDE_PATH, fill: 'currentColor' })]);
  }
  if (provider === 'codex') {
    return s('svg', attrs, [
      s('path', { d: CODEX_CLOUD_PATH, fill: mono ? 'currentColor' : '#6366F1' }),
      s('path', {
        d: CODEX_PROMPT_PATH,
        fill: 'none',
        stroke: mono ? '#16161a' : '#FFFFFF',
        'stroke-width': 1.6,
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
      }),
    ]);
  }
  if (provider === 'antigravity') {
    // Neutral arch mark; the brand PNG is used whenever it is bundled.
    return s('svg', attrs, [
      s('path', { d: 'M4 20L12 4l8 16', fill: 'none', stroke: 'currentColor', 'stroke-width': 2.2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }),
    ]);
  }
  return s('svg', attrs, [
    s('circle', { cx: 11, cy: 13, r: 7, fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }),
    s('path', { d: 'M4 21L21 4', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round' }),
  ]);
}

/** v1 `U()` equivalent: brand PNG when bundled, SVG otherwise. Decorative; callers provide text. */
export function providerIcon(provider: ProviderId, size: number, mono: boolean, title?: string): HTMLElement {
  const wrap = h('span', {
    class: `ai-brand-icon ${mono ? 'is-mono' : 'is-color'}`,
    'data-provider': provider,
    title,
    'aria-hidden': 'true',
  });
  setStyles(wrap, { width: `${size}px`, height: `${size}px`, 'min-width': `${size}px` });
  const png = PNG_ICONS[provider];
  if (png !== undefined && isBundledAssetUrl(png)) {
    const img = h('img', { alt: '', width: size, height: size, draggable: 'false' });
    img.src = png;
    wrap.append(img);
  } else {
    wrap.append(providerGlyph(provider, size, mono));
  }
  return wrap;
}

export function refreshGlyph(size = 14): SVGSVGElement {
  const stroke = { fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' };
  return s('svg', { viewBox: '0 0 24 24', width: size, height: size, 'aria-hidden': 'true', focusable: 'false', class: 'refresh-glyph' }, [
    s('path', { d: 'M20 12a8 8 0 1 1-2.34-5.66', ...stroke }),
    s('path', { d: 'M20 4v5h-5', ...stroke }),
  ]);
}

export function copyGlyph(size = 14): SVGSVGElement {
  const stroke = { fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linejoin': 'round' };
  return s('svg', { viewBox: '0 0 24 24', width: size, height: size, 'aria-hidden': 'true', focusable: 'false' }, [
    s('rect', { x: 8, y: 8, width: 12, height: 12, rx: 2, ...stroke }),
    s('path', { d: 'M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3', ...stroke }),
  ]);
}

export function checkGlyph(size = 14): SVGSVGElement {
  return s('svg', { viewBox: '0 0 24 24', width: size, height: size, 'aria-hidden': 'true', focusable: 'false' }, [
    s('path', { d: 'M5 12.5l4.5 4.5L19 7.5', fill: 'none', stroke: 'currentColor', 'stroke-width': 2.2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }),
  ]);
}

import type { ProviderId } from '../../shared/types';
import claudeIconUrl from '../../../resources/icons/claude_64.png';
import antigravityIconUrl from '../../../resources/icons/antigravity_64.png';
import codexIconUrl from '../../../resources/icons/codex_64.png';
import grokIconUrl from '../../../resources/icons/grok_64.png';
import { GROK_MARK_PATHS, GROK_MARK_VIEWBOX, OPENAI_BLOSSOM_PATH, OPENAI_BLOSSOM_VIEWBOX } from './brand-marks';
import { h, s, setStyles } from './dom';

// Bundled at build time; Vite may inline small files as data:image/png URIs (allowed by img-src).
// codex and grok are the vendors' own dark app tiles (white mark on black), so they read on
// light and dark widgets alike; styles.css rounds their corners (DECISIONS 26.09.20 08:57).
const PNG_ICONS: Readonly<Record<ProviderId, string>> = {
  claude: claudeIconUrl,
  codex: codexIconUrl,
  grok: grokIconUrl,
  antigravity: antigravityIconUrl,
};

function isBundledAssetUrl(url: string): boolean {
  return url.startsWith('data:image/png;base64,') || !/^[a-z][a-z0-9+.-]*:/i.test(url) || url.startsWith('app:');
}

// v1 SVG glyph for Claude (SPEC §2-2); Codex and Grok use the vendors' own marks (brand-marks.ts).
const CLAUDE_PATH =
  'M12 2l1.2 5.5L18 4l-3 4.8 5.8.5-5 3 4.2 4-5.4.3 2 5.4-4.8-3-1 5.8-1.5-5.5-4.5 3.5 1.5-5.5-5.5-1 5-3.2-4-4.5 5.5 1L10.5 2z';

/** Inline SVG glyph drawn in currentColor (V1-33); colour comes from `.ai-brand-icon` or the caller. */
export function providerGlyph(provider: ProviderId, size: number): SVGSVGElement {
  const attrs = { viewBox: '0 0 24 24', width: size, height: size, 'aria-hidden': 'true', focusable: 'false' };
  if (provider === 'claude') {
    return s('svg', attrs, [s('path', { d: CLAUDE_PATH, fill: 'currentColor' })]);
  }
  if (provider === 'codex') {
    return s('svg', { ...attrs, viewBox: OPENAI_BLOSSOM_VIEWBOX }, [s('path', { d: OPENAI_BLOSSOM_PATH, fill: 'currentColor' })]);
  }
  if (provider === 'grok') {
    return s(
      'svg',
      { ...attrs, viewBox: GROK_MARK_VIEWBOX },
      GROK_MARK_PATHS.map((d) => s('path', { d, fill: 'currentColor' })),
    );
  }
  // antigravity: neutral arch mark; the brand PNG is used wherever a PNG can be shown.
  return s('svg', attrs, [
    s('path', { d: 'M4 20L12 4l8 16', fill: 'none', stroke: 'currentColor', 'stroke-width': 2.2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }),
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
  if (isBundledAssetUrl(png)) {
    const img = h('img', { alt: '', width: size, height: size, draggable: 'false' });
    img.src = png;
    wrap.append(img);
  } else {
    wrap.append(providerGlyph(provider, size));
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

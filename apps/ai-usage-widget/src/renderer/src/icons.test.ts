import { describe, expect, it } from 'vitest';
import { PROVIDER_IDS } from '../../shared/types';
import { GROK_MARK_PATHS, GROK_MARK_VIEWBOX, OPENAI_BLOSSOM_PATH, OPENAI_BLOSSOM_VIEWBOX } from './brand-marks';
import { providerGlyph, providerIcon } from './icons';

describe('providerIcon', () => {
  it('draws single-colour brands as theme-coloured vectors and multi-colour brands as images', () => {
    const vector = new Set(['codex', 'grok']);
    for (const provider of PROVIDER_IDS) {
      const icon = providerIcon(provider, 24, false, 'name');
      expect(icon.getAttribute('data-provider')).toBe(provider);
      expect(icon.getAttribute('aria-hidden')).toBe('true');
      if (vector.has(provider)) {
        // No image and no fixed fill: the mark sits on a transparent background in currentColor.
        expect(icon.querySelector('img'), provider).toBeNull();
        const paths = [...icon.querySelectorAll('svg path')];
        expect(paths.length, provider).toBeGreaterThan(0);
        for (const path of paths) expect(path.getAttribute('fill')).toBe('currentColor');
        expect(icon.querySelector('svg rect, svg circle'), provider).toBeNull();
      } else {
        expect(icon.querySelector('img')?.getAttribute('src') ?? '', provider).not.toBe('');
        expect(icon.querySelector('svg'), provider).toBeNull();
      }
    }
  });

  it('marks monochrome icons so CSS can desaturate them', () => {
    expect(providerIcon('grok', 18, true).classList.contains('is-mono')).toBe(true);
    expect(providerIcon('grok', 18, false).classList.contains('is-color')).toBe(true);
  });
});

describe('providerGlyph', () => {
  it('draws Codex with the OpenAI blossom and Grok with the Grok mark, in currentColor', () => {
    const codex = providerGlyph('codex', 16);
    expect(codex.getAttribute('viewBox')).toBe(OPENAI_BLOSSOM_VIEWBOX);
    expect([...codex.querySelectorAll('path')].map((p) => p.getAttribute('d'))).toEqual([OPENAI_BLOSSOM_PATH]);

    const grok = providerGlyph('grok', 16);
    expect(grok.getAttribute('viewBox')).toBe(GROK_MARK_VIEWBOX);
    expect([...grok.querySelectorAll('path')].map((p) => p.getAttribute('d'))).toEqual([...GROK_MARK_PATHS]);

    for (const svg of [codex, grok]) {
      for (const path of svg.querySelectorAll('path')) expect(path.getAttribute('fill')).toBe('currentColor');
      expect(svg.getAttribute('width')).toBe('16');
    }
  });

  it('keeps vendor paths free of anything but path data', () => {
    for (const d of [OPENAI_BLOSSOM_PATH, ...GROK_MARK_PATHS]) expect(d).toMatch(/^[MLCVHZmlcvhz0-9 .,-]+$/);
  });
});

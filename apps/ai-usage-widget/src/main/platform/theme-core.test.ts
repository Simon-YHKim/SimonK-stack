import { describe, expect, it } from 'vitest';
import { DEFAULT_ACCENT, computeThemeTokens, normalizeAccentColor } from './theme-core';

describe('theme-core', () => {
  it('normalizes accent colors', () => {
    expect(normalizeAccentColor('0078d4ff')).toBe('#0078d4');
    expect(normalizeAccentColor('#FF8800')).toBe('#ff8800');
    expect(normalizeAccentColor('red')).toBe(DEFAULT_ACCENT);
    expect(normalizeAccentColor(false)).toBe(DEFAULT_ACCENT);
  });

  const base = {
    shouldUseDarkColors: false,
    shouldUseDarkColorsForSystemIntegratedUI: true,
    inForcedColorsMode: false,
    prefersReducedTransparency: false,
    accentRaw: '0078d4ff',
    material: 'mica' as const,
  };

  it('separates app and taskbar schemes', () => {
    expect(computeThemeTokens(base)).toEqual({
      scheme: 'light',
      taskbarScheme: 'dark',
      highContrast: false,
      accent: '#0078d4',
      reducedTransparency: false,
      effectiveMaterial: 'mica',
    });
  });

  it('forces opaque material in high contrast or reduced transparency', () => {
    expect(computeThemeTokens({ ...base, inForcedColorsMode: true }).effectiveMaterial).toBe('none');
    expect(computeThemeTokens({ ...base, prefersReducedTransparency: true }).effectiveMaterial).toBe('none');
  });
});

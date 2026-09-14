import { nativeTheme, systemPreferences } from 'electron';
import type { Material } from '../../shared/settings';
import type { ThemeTokens } from '../../shared/types';
import { computeThemeTokens } from './theme-core';

export function readThemeTokens(material: Material): ThemeTokens {
  let accentRaw: unknown = null;
  try {
    accentRaw = systemPreferences.getAccentColor();
  } catch {
    accentRaw = null;
  }
  return computeThemeTokens({
    shouldUseDarkColors: nativeTheme.shouldUseDarkColors,
    shouldUseDarkColorsForSystemIntegratedUI: nativeTheme.shouldUseDarkColorsForSystemIntegratedUI,
    inForcedColorsMode: nativeTheme.inForcedColorsMode,
    prefersReducedTransparency: nativeTheme.prefersReducedTransparency,
    accentRaw,
    material,
  });
}

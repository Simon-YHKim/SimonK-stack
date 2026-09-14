import { nativeTheme, systemPreferences } from 'electron';
import type { Material } from '../../shared/settings';
import type { ThemeTokens } from '../../shared/types';
import { computeThemeTokens, type ThemeSource } from './theme-core';

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

/** nativeTheme 'updated' + systemPreferences 'accent-color-changed' as re-read triggers. */
export const systemThemeSource: ThemeSource = {
  read: readThemeTokens,
  subscribe(onSystemChange) {
    const listener = (): void => onSystemChange();
    nativeTheme.on('updated', listener);
    systemPreferences.on('accent-color-changed', listener);
    return () => {
      nativeTheme.removeListener('updated', listener);
      systemPreferences.removeListener('accent-color-changed', listener);
    };
  },
};

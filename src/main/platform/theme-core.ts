import type { Material } from '../../shared/settings';
import type { ThemeTokens } from '../../shared/types';

export const DEFAULT_ACCENT = '#0078d4';

/** `0078d4ff` / `#0078D4` -> `#0078d4`; anything else falls back to the Windows default blue. */
export function normalizeAccentColor(raw: unknown): string {
  if (typeof raw !== 'string') return DEFAULT_ACCENT;
  const hex = raw.trim().replace(/^#/, '').toLowerCase();
  return /^[0-9a-f]{6}(?:[0-9a-f]{2})?$/.test(hex) ? `#${hex.slice(0, 6)}` : DEFAULT_ACCENT;
}

export interface ThemeInputs {
  shouldUseDarkColors: boolean;
  shouldUseDarkColorsForSystemIntegratedUI: boolean;
  inForcedColorsMode: boolean;
  prefersReducedTransparency: boolean;
  accentRaw: unknown;
  material: Material;
}

export function computeThemeTokens(input: ThemeInputs): ThemeTokens {
  const forceOpaque = input.inForcedColorsMode || input.prefersReducedTransparency;
  return {
    scheme: input.shouldUseDarkColors ? 'dark' : 'light',
    taskbarScheme: input.shouldUseDarkColorsForSystemIntegratedUI ? 'dark' : 'light',
    highContrast: input.inForcedColorsMode,
    accent: normalizeAccentColor(input.accentRaw),
    reducedTransparency: input.prefersReducedTransparency,
    effectiveMaterial: forceOpaque ? 'none' : input.material,
  };
}

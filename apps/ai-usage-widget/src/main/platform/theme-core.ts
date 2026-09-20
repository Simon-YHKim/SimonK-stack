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

export function themeTokensEqual(a: ThemeTokens, b: ThemeTokens): boolean {
  return (
    a.scheme === b.scheme &&
    a.taskbarScheme === b.taskbarScheme &&
    a.highContrast === b.highContrast &&
    a.accent === b.accent &&
    a.reducedTransparency === b.reducedTransparency &&
    a.effectiveMaterial === b.effectiveMaterial
  );
}

export interface ThemeSource {
  read(material: Material): ThemeTokens;
  /** System change notifications are triggers only; tokens are re-read each time. */
  subscribe(onSystemChange: () => void): () => void;
}

/** Holds current tokens and notifies listeners only when a value actually changed. */
export class ThemeService {
  private tokens: ThemeTokens;
  private readonly listeners = new Set<(tokens: ThemeTokens) => void>();
  private readonly unsubscribe: () => void;

  constructor(
    private readonly source: ThemeSource,
    private material: Material,
  ) {
    this.tokens = source.read(material);
    this.unsubscribe = source.subscribe(() => this.refresh());
  }

  current(): ThemeTokens {
    return { ...this.tokens };
  }

  setMaterial(material: Material): ThemeTokens {
    this.material = material;
    this.refresh();
    return this.current();
  }

  onChange(listener: (tokens: ThemeTokens) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  refresh(): void {
    const next = this.source.read(this.material);
    if (themeTokensEqual(next, this.tokens)) return;
    this.tokens = next;
    for (const listener of this.listeners) listener(this.current());
  }

  dispose(): void {
    this.unsubscribe();
    this.listeners.clear();
  }
}

/** Opaque window background used when a material is requested but not applied. */
export function opaqueBackground(scheme: ThemeTokens['scheme']): string {
  return scheme === 'dark' ? '#202020' : '#f3f3f3';
}

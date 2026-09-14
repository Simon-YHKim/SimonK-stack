import type { AppStateSnapshot, Locale, ViewId } from '../../shared/types';

export const FALLBACK_ACCENT = '#0078d4';

export function safeAccent(value: string): string {
  return /^#[0-9a-f]{6}$/i.test(value) ? value.toLowerCase() : FALLBACK_ACCENT;
}

/**
 * Text color on the accent. Windows puts white text on accent buttons, so white
 * wins whenever it reaches WCAG AA (4.5:1); otherwise the higher-contrast color.
 */
export function accentForeground(accent: string): '#000000' | '#ffffff' {
  const hex = safeAccent(accent).slice(1);
  const channel = (offset: number): number => {
    const c = parseInt(hex.slice(offset, offset + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  };
  const luminance = 0.2126 * channel(0) + 0.7152 * channel(2) + 0.0722 * channel(4);
  const withWhite = 1.05 / (luminance + 0.05);
  const withBlack = (luminance + 0.05) / 0.05;
  return withWhite >= 4.5 || withWhite >= withBlack ? '#ffffff' : '#000000';
}

export type Skin = 'windows' | 'v1';

export function skinFor(state: AppStateSnapshot): Skin {
  return state.settings.theme === 'windows' ? 'windows' : 'v1';
}

/** Root attributes consumed by CSS. The widget sits on the taskbar, so it follows taskbarScheme. */
export function applyDocumentTheme(doc: Document, view: ViewId, state: AppStateSnapshot, locale: Locale): void {
  const html = doc.documentElement;
  const { theme } = state;
  html.lang = locale;
  html.dataset.view = view;
  html.dataset.skin = skinFor(state);
  html.dataset.scheme = view === 'widget' ? theme.taskbarScheme : theme.scheme;
  html.dataset.highContrast = String(theme.highContrast);
  html.dataset.reducedTransparency = String(theme.reducedTransparency);
  html.dataset.material = theme.effectiveMaterial;
  const accent = safeAccent(theme.accent);
  html.style.setProperty('--accent', accent);
  html.style.setProperty('--accent-fg', accentForeground(accent));
}

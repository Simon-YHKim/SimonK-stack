import { resolveLocale } from '../../shared/i18n';
import type { Language } from '../../shared/settings';
import { LOCALES, type Locale } from '../../shared/types';
import { isOneOf } from '../../shared/validate';

/**
 * Explicit language wins. For `auto`, main's resolved locale is the single source
 * (same rule as the tray, V1-34); navigator.language is only a fallback.
 */
export function pickLocale(language: Language, mainLocale: unknown, navigatorLanguage: string): Locale {
  if (language === 'ko' || language === 'en') return language;
  if (isOneOf(LOCALES, mainLocale)) return mainLocale;
  return resolveLocale('auto', navigatorLanguage);
}

export function currentNavigatorLanguage(): string {
  return typeof navigator === 'undefined' ? '' : navigator.language;
}

import type { Locale } from '../../shared/types';
import { formatCountdown } from '../../shared/usage';

export function clampPercent(value: number): number {
  return Math.min(100, Math.max(0, value));
}

export function percentText(value: number): string {
  return `${Math.round(clampPercent(value))}%`;
}

export function countdownText(resetsAt: number | null, now: number): string {
  return resetsAt === null ? '--' : formatCountdown(resetsAt - now);
}

/** Locale-aware "5 minutes ago" via Intl (no hand-written strings). */
export function relativeTimeText(locale: Locale, at: number, now: number): string {
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });
  const diffSec = Math.round((at - now) / 1000);
  const abs = Math.abs(diffSec);
  if (abs < 60) return rtf.format(0, 'second');
  if (abs < 3600) return rtf.format(Math.trunc(diffSec / 60), 'minute');
  if (abs < 86_400) return rtf.format(Math.trunc(diffSec / 3600), 'hour');
  return rtf.format(Math.trunc(diffSec / 86_400), 'day');
}

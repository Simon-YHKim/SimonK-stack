import type { Locale, ModelNotice } from './types';

/** Announcement dates have no time zone; show whole calendar days, not an invented clock. */
export function modelNoticeText(notice: Pick<ModelNotice, 'model' | 'status' | 'releaseDate'>, locale: Locale, now: number): string {
  const model = notice.model;
  if (notice.status === 'released') {
    return locale === 'ko' ? `${model} 출시됨 · 사용해보세요` : `${model} released · Try it`;
  }
  const date = notice.releaseDate;
  if (date === null) return locale === 'ko' ? `${model} 출시 예정 · 날짜 미정` : `${model} announced · Date TBA`;
  const [year, month, day] = date.split('-').map(Number);
  const today = new Date(now);
  const dayIndex = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate());
  const target = Date.UTC(year ?? 0, (month ?? 1) - 1, day ?? 1);
  const remaining = Math.round((target - dayIndex) / 86_400_000);
  if (remaining < 0) return locale === 'ko' ? `${model} · 발표된 출시일 경과, 공식 출시 확인 중` : `${model} · Announced date passed; checking official release`;
  const countdown = remaining === 0 ? 'D-day' : `D-${remaining}`;
  return locale === 'ko' ? `${model} 출시 예정 · ${date} (${countdown})` : `${model} upcoming · ${date} (${countdown})`;
}

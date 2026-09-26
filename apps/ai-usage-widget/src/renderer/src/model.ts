// View model: turns the snapshot into per-account rows. Never invents a number:
// unknown percentages stay null and are rendered as markers, not as 0%.

import {
  ERROR_MESSAGE_KEYS,
  USAGE_STATE_KEYS,
  type MessageKey,
  type Translator,
} from '../../shared/i18n';
import type { Settings } from '../../shared/settings';
import type {
  AccountDTO,
  AppStateSnapshot,
  ErrorCode,
  Locale,
  ProviderId,
  QuotaWindow,
  QuotaWindowKind,
  ThemeTokens,
  UsageSnapshot,
  UsageSource,
  UsageState,
} from '../../shared/types';
import { deriveDisplayState, displayPercent, isWindowExpired, usageLevel, type UsageLevel } from '../../shared/usage';
import { countdownText, percentText, relativeTimeText } from './format';

export interface RenderContext {
  t: Translator;
  locale: Locale;
  settings: Settings;
  theme: ThemeTokens;
  now: number;
}

export type RowStatus = 'value' | 'unknown' | 'reset';

export interface RowView {
  kind: QuotaWindowKind;
  /** Compact widget tag (v1 '5H' / 'WK'); not a translated string. */
  tag: string;
  status: RowStatus;
  usedPercent: number | null;
  /** used% or left% per settings; null unless status is 'value'. */
  shownPercent: number | null;
  level: UsageLevel;
  countdown: string;
  resetsAt: number | null;
  windowMinutes: number | null;
  /** Provider qualifier (bucket id or model group) that tells same-kind windows apart; popup only. */
  label: string | null;
}

export interface AccountView {
  account: AccountDTO;
  state: UsageState;
  errorCode?: ErrorCode;
  /** Every window in provider order (popup). */
  windows: RowView[];
  /** At most two rows for the widget bar. */
  rows: RowView[];
  measuredAt: number | null;
  source: UsageSource | null;
  plan?: string;
  resetCreditsAvailable?: number;
}

/** States whose windows hold current (or dimmed recent) measurements. */
export function isMeasuredState(state: UsageState): state is 'ok' | 'stale' | 'reset' {
  return state === 'ok' || state === 'stale' || state === 'reset';
}

export function tagForWindow(kind: QuotaWindowKind, windowMinutes: number | null): string {
  if (kind === 'session') return '5H';
  if (kind === 'weekly') return 'WK';
  if (windowMinutes === null || windowMinutes <= 0) return '--';
  if (windowMinutes < 60) return `${windowMinutes}m`;
  if (windowMinutes < 1440) return `${Math.round(windowMinutes / 60)}H`;
  return `${Math.round(windowMinutes / 1440)}D`;
}

export function toRow(window: QuotaWindow, now: number, showUsed: boolean): RowView {
  const expired = isWindowExpired(window, now);
  const known = window.usedPercent !== null && Number.isFinite(window.usedPercent);
  const status: RowStatus = expired ? 'reset' : known ? 'value' : 'unknown';
  const used = status === 'value' ? window.usedPercent : null;
  return {
    kind: window.kind,
    tag: tagForWindow(window.kind, window.windowMinutes),
    status,
    usedPercent: used,
    shownPercent: displayPercent(used, showUsed),
    level: usageLevel(used),
    countdown: status === 'reset' ? '--' : countdownText(window.resetsAt, now),
    resetsAt: window.resetsAt,
    windowMinutes: window.windowMinutes,
    label: window.label ?? null,
  };
}

/** Session first, then weekly (hidden by showWeeklyLimit unless it is the only limit), else the first other window. */
export function selectWidgetRows(windows: readonly RowView[], showWeeklyLimit: boolean): RowView[] {
  const session = windows.find((w) => w.kind === 'session');
  const weekly = windows.find((w) => w.kind === 'weekly');
  const rows: RowView[] = [];
  if (session !== undefined) rows.push(session);
  if (weekly !== undefined && (showWeeklyLimit || session === undefined)) rows.push(weekly);
  if (rows.length === 0) {
    const other = windows.find((w) => w.kind === 'other');
    if (other !== undefined) rows.push(other);
  }
  return rows;
}

export function buildAccountView(
  account: AccountDTO,
  snapshot: UsageSnapshot | null,
  settings: Settings,
  now: number,
): AccountView {
  if (snapshot === null) {
    const view: AccountView = { account, state: 'loading', windows: [], rows: [], measuredAt: null, source: null };
    if (account.loginState === 'logged-out') view.state = 'logged-out';
    if (account.loginState === 'cli-missing') {
      view.state = 'error';
      view.errorCode = 'cli-not-found';
    }
    if (account.plan !== undefined) view.plan = account.plan;
    return view;
  }
  let state = deriveDisplayState(snapshot, now, settings.refreshIntervalSec);
  const windows = snapshot.windows.map((w) => toRow(w, now, settings.showUsedPercent));
  // A failed fetch keeps the last measured windows (DECISIONS 01:36); the widget shows them dimmed.
  const keepsLastValues = state === 'error' && snapshot.measuredAt !== null;
  let rows = isMeasuredState(state) || keepsLastValues ? selectWidgetRows(windows, settings.showWeeklyLimit) : [];
  let errorCode = snapshot.errorCode;
  if (isMeasuredState(state) && rows.length === 0) {
    state = 'unavailable';
    errorCode = errorCode ?? 'quota-unavailable';
    rows = [];
  }
  const view: AccountView = {
    account,
    state,
    windows,
    rows,
    measuredAt: snapshot.measuredAt,
    source: snapshot.source,
  };
  if (errorCode !== undefined) view.errorCode = errorCode;
  const plan = snapshot.plan ?? account.plan;
  if (plan !== undefined) view.plan = plan;
  if (state === 'ok' && account.provider === 'codex' && snapshot.resetCreditsAvailable !== undefined) {
    view.resetCreditsAvailable = snapshot.resetCreditsAvailable;
  }
  return view;
}

export function sortedAccounts(accounts: readonly AccountDTO[]): AccountDTO[] {
  return [...accounts].sort((a, b) => a.order - b.order);
}

export function buildEnabledViews(state: AppStateSnapshot, now: number): AccountView[] {
  return sortedAccounts(state.accounts)
    .filter((account) => account.enabled)
    .map((account) => {
      const snapshot =
        state.usage.find((u) => u.accountId === account.id && u.provider === account.provider) ?? null;
      return buildAccountView(account, snapshot, state.settings, now);
    });
}

// ---------------------------------------------------------------------------
// Colors (single monochrome / threshold rule for every theme, V1-22 / V1-33)

export const V1_COLORS = {
  critical: '#F43F5E',
  warn: '#F97316',
  normal: '#10B981',
  monoPrimary: '#D1D5DB',
  monoSecondary: '#9CA3AF',
  secondaryFallback: '#9CA3AF',
  muted: '#6b7280',
  segmentOff: 'rgba(255, 255, 255, 0.14)',
} as const;

export const PROVIDER_BRAND: Readonly<Record<ProviderId, string>> = {
  claude: '#D97757',
  codex: '#6366F1',
  grok: '#D4D4D8',
  antigravity: '#4285F4',
};

export function v1RowColor(row: RowView, index: number, settings: Settings, provider: ProviderId): string {
  if (row.status !== 'value' || row.usedPercent === null) return V1_COLORS.muted;
  if (settings.iconStyle === 'monochrome') return index === 0 ? V1_COLORS.monoPrimary : V1_COLORS.monoSecondary;
  if (settings.colorByUsage) {
    if (row.level === 'critical') return V1_COLORS.critical;
    if (row.level === 'warn') return V1_COLORS.warn;
    return V1_COLORS.normal;
  }
  return index === 0 ? PROVIDER_BRAND[provider] : V1_COLORS.secondaryFallback;
}

export type WindowsLevel = 'unknown' | 'mono' | 'normal' | 'warn' | 'critical';

/** Level attribute for CSS-driven colors in the 'windows' theme. */
export function windowsRowLevel(row: RowView, settings: Settings): WindowsLevel {
  if (row.status !== 'value') return 'unknown';
  if (settings.iconStyle === 'monochrome') return 'mono';
  if (!settings.colorByUsage) return 'normal';
  return row.level === 'unknown' ? 'normal' : row.level;
}

// ---------------------------------------------------------------------------
// Text

export function windowTitle(t: Translator, row: Pick<RowView, 'kind' | 'windowMinutes'>): string {
  if (row.kind === 'session') return t('sessionLimit5h');
  if (row.kind === 'weekly') return t('weeklyLimit');
  return row.windowMinutes === null ? t('otherWindowsTitle') : t('windowOtherMinutes', { minutes: row.windowMinutes });
}

export function stateText(t: Translator, state: UsageState): string {
  return t(USAGE_STATE_KEYS[state]);
}

export function errorText(t: Translator, code: ErrorCode): string {
  return t(ERROR_MESSAGE_KEYS[code]);
}

export function measuredText(ctx: RenderContext, measuredAt: number | null): string {
  return measuredAt === null
    ? ctx.t('neverMeasured')
    : ctx.t('lastMeasured', { time: relativeTimeText(ctx.locale, measuredAt, ctx.now) });
}

function rowValueText(t: Translator, row: RowView, unitKey: MessageKey): string {
  if (row.status === 'value' && row.shownPercent !== null) {
    return `${percentText(row.shownPercent)} ${t(unitKey)} (${row.countdown})`;
  }
  return row.status === 'reset' ? t('state_reset') : t('percentUnknown');
}

/** Hover text for a widget item. Always states the condition; numbers only when measured. */
export function itemTooltip(view: AccountView, ctx: RenderContext): string {
  const { t, settings } = ctx;
  const name = view.account.label;
  const unitKey: MessageKey = settings.showUsedPercent ? 'unitUsed' : 'unitLeft';
  const unit = t(unitKey);
  const suffix: string[] = [];
  if (view.state === 'stale') suffix.push(stateText(t, 'stale'), measuredText(ctx, view.measuredAt));
  if (view.state === 'reset') suffix.push(stateText(t, 'reset'));

  if (isMeasuredState(view.state) && view.rows.length > 0) {
    const [a, b] = view.rows;
    let main: string;
    const valueRow = (row: RowView | undefined): row is RowView & { shownPercent: number } =>
      row !== undefined && row.status === 'value' && row.shownPercent !== null;
    if (valueRow(a) && valueRow(b)) {
      main = t('widgetTooltip', {
        name,
        p: Math.round(a.shownPercent),
        unit,
        pr: a.countdown,
        w: Math.round(b.shownPercent),
        wr: b.countdown,
      });
    } else if (valueRow(a) && b === undefined) {
      const key: MessageKey = a.kind === 'weekly' ? 'widgetTooltipWeeklyOnly' : 'widgetTooltipNoWeekly';
      main = t(key, { name, p: Math.round(a.shownPercent), unit, pr: a.countdown });
    } else {
      main = [name, ...view.rows.map((row) => `${windowTitle(t, row)}: ${rowValueText(t, row, unitKey)}`)].join(
        ' | ',
      );
    }
    return [main, ...suffix].join(' | ');
  }

  const parts = [name, stateText(t, view.state)];
  if (view.errorCode !== undefined) parts.push(errorText(t, view.errorCode));
  if (view.state === 'error' && view.measuredAt !== null) parts.push(measuredText(ctx, view.measuredAt));
  return parts.join(' | ');
}

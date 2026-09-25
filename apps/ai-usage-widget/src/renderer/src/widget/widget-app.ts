import { createTranslator } from '../../../shared/i18n';
import type { AppStateSnapshot, ThemeTokens } from '../../../shared/types';
import type { Api } from '../api';
import { h, setAttr, setStyles, uniqueId } from '../dom';
import { refreshGlyph } from '../icons';
import { currentNavigatorLanguage, pickLocale } from '../locale';
import { buildEnabledViews, type RenderContext } from '../model';
import { applyDocumentTheme, skinFor } from '../theme';
import { renderWidgetItem } from './themes';

/** Clicks within this window after a toggle are ignored (v1 SPEC §2-5). */
export const TOGGLE_DEBOUNCE_MS = 300;
/** Matches the scheduler's per-account manual refresh spacing (DESIGN §6-3). */
export const REFRESH_COOLDOWN_MS = 5000;
export const TICK_MS = 30_000;
const SIZE_MARGIN = 4;
const MIN_HEIGHT = 34;
const MINUTE_MS = 60_000;

interface PaceSample {
  at: number;
  used: number;
  resetsAt: number | null;
}

interface FastPace {
  recent: number;
  usual: number;
}

/** Compare two measured slopes; a single delayed provider update cannot trigger the indicator. */
function fastPace(samples: readonly PaceSample[]): FastPace | null {
  const latest = samples.at(-1);
  if (latest === undefined) return null;
  const recentStart = [...samples].reverse().find((sample) => {
    const age = latest.at - sample.at;
    return age >= 15 * MINUTE_MS && age <= 30 * MINUTE_MS;
  });
  if (recentStart === undefined) return null;
  const usualStart = [...samples].reverse().find((sample) => {
    const age = recentStart.at - sample.at;
    return age >= 45 * MINUTE_MS && age <= 90 * MINUTE_MS;
  });
  if (usualStart === undefined || latest.used - recentStart.used < 3) return null;
  let positiveSteps = 0;
  let largestStep = 0;
  let previous = recentStart;
  for (const sample of samples) {
    if (sample.at <= recentStart.at) continue;
    const step = sample.used - previous.used;
    if (step > 0) {
      positiveSteps += 1;
      largestStep = Math.max(largestStep, step);
    }
    previous = sample;
  }
  if (positiveSteps < 2 || latest.used - recentStart.used - largestStep < 2 || recentStart.used < usualStart.used) return null;
  const recent = (latest.used - recentStart.used) * 3_600_000 / (latest.at - recentStart.at);
  const usual = (recentStart.used - usualStart.used) * 3_600_000 / (recentStart.at - usualStart.at);
  return recent >= Math.max(6, usual * 2) ? { recent, usual } : null;
}

export interface Size {
  width: number;
  height: number;
}

export interface WidgetDeps {
  api: Api;
  root: HTMLElement;
  now?: () => number;
  measure?: (el: HTMLElement) => Size;
  schedule?: (fn: () => void) => void;
  navigatorLanguage?: string;
}

export type WidgetRendered = 'empty' | 'accounts';

function defaultMeasure(el: HTMLElement): Size {
  const rect = el.getBoundingClientRect();
  return { width: rect.width, height: rect.height };
}

function defaultSchedule(fn: () => void): void {
  if (typeof requestAnimationFrame === 'function') requestAnimationFrame(() => fn());
  else setTimeout(fn, 0);
}

export class WidgetApp {
  private readonly api: Api;
  private readonly root: HTMLElement;
  private readonly now: () => number;
  private readonly measure: (el: HTMLElement) => Size;
  private readonly schedule: (fn: () => void) => void;
  private readonly navigatorLanguage: string;

  private state: AppStateSnapshot | null = null;
  private lastToggleAt = Number.NEGATIVE_INFINITY;
  private cooldownUntil = 0;
  private cooldownTimer: ReturnType<typeof setTimeout> | null = null;
  private pendingRefresh = false;
  private lastSignature = '';
  private lastSize: Size | null = null;
  private tickTimer: ReturnType<typeof setInterval> | null = null;
  private readonly paceHistory = new Map<string, Map<string, PaceSample[]>>();
  private readonly fastAccounts = new Map<string, FastPace>();

  readonly bar: HTMLDivElement;
  readonly main: HTMLDivElement;
  readonly refreshButton: HTMLButtonElement;
  private readonly summary: HTMLSpanElement;

  constructor(deps: WidgetDeps) {
    this.api = deps.api;
    this.root = deps.root;
    this.now = deps.now ?? Date.now;
    this.measure = deps.measure ?? defaultMeasure;
    this.schedule = deps.schedule ?? defaultSchedule;
    this.navigatorLanguage = deps.navigatorLanguage ?? currentNavigatorLanguage();

    const summaryId = uniqueId('widget-summary');
    this.summary = h('span', { id: summaryId, class: 'sr-only' });
    this.main = h('div', { class: 'widget-main', role: 'button', tabindex: 0, 'aria-describedby': summaryId });
    this.refreshButton = h('button', { type: 'button', class: 'widget-refresh', 'aria-disabled': 'false' }, [refreshGlyph()]);
    this.bar = h('div', { class: 'widget-root', id: 'widget-container' }, [this.main, this.refreshButton, this.summary]);
    this.root.replaceChildren(this.bar);

    this.bar.addEventListener('click', (event) => {
      if (event.target instanceof Node && this.refreshButton.contains(event.target)) return;
      this.activateMain();
    });
    this.main.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        this.activateMain();
      }
    });
    this.refreshButton.addEventListener('click', (event) => {
      event.stopPropagation();
      this.requestRefresh();
    });
  }

  start(): void {
    if (this.tickTimer === null) this.tickTimer = setInterval(() => this.rerender(), TICK_MS);
  }

  stop(): void {
    if (this.tickTimer !== null) clearInterval(this.tickTimer);
    if (this.cooldownTimer !== null) clearTimeout(this.cooldownTimer);
    this.tickTimer = null;
    this.cooldownTimer = null;
  }

  update(state: AppStateSnapshot): WidgetRendered {
    this.state = state;
    this.observePace(state);
    return this.render();
  }

  private observePace(state: AppStateSnapshot): void {
    this.fastAccounts.clear();
    const accountIds = new Set(state.accounts.map((account) => account.id));
    for (const id of this.paceHistory.keys()) if (!accountIds.has(id)) this.paceHistory.delete(id);
    for (const snapshot of state.usage) {
      const at = snapshot.measuredAt;
      if (snapshot.state !== 'ok' || at === null || !Number.isFinite(at) || at > this.now() + MINUTE_MS) continue;
      let windows = this.paceHistory.get(snapshot.accountId);
      if (windows === undefined) {
        windows = new Map();
        this.paceHistory.set(snapshot.accountId, windows);
      }
      const seen = new Set<string>();
      snapshot.windows.forEach((window, index) => {
        const used = window.usedPercent;
        if (used === null || !Number.isFinite(used) || used < 0 || used > 100) return;
        if (window.resetsAt !== null && window.resetsAt <= at) return;
        const key = JSON.stringify([index, window.kind, window.label ?? '']);
        seen.add(key);
        let samples = windows.get(key) ?? [];
        const last = samples.at(-1);
        if (last !== undefined && at <= last.at) {
          const pace = fastPace(samples);
          if (pace !== null && pace.recent > (this.fastAccounts.get(snapshot.accountId)?.recent ?? 0)) {
            this.fastAccounts.set(snapshot.accountId, pace);
          }
          return;
        }
        const resetChanged = last !== undefined && (
          (last.resetsAt === null) !== (window.resetsAt === null) ||
          (last.resetsAt !== null && window.resetsAt !== null && Math.abs(last.resetsAt - window.resetsAt) > 2 * MINUTE_MS)
        );
        if (last !== undefined && (used < last.used || resetChanged)) samples = [];
        samples = [...samples, { at, used, resetsAt: window.resetsAt }]
          .filter((sample) => at - sample.at <= 2 * 3_600_000)
          .slice(-50);
        windows.set(key, samples);
        const pace = fastPace(samples);
        if (pace !== null && pace.recent > (this.fastAccounts.get(snapshot.accountId)?.recent ?? 0)) {
          this.fastAccounts.set(snapshot.accountId, pace);
        }
      });
      for (const key of windows.keys()) if (!seen.has(key)) windows.delete(key);
    }
  }

  updateTheme(theme: ThemeTokens): void {
    if (this.state === null) return;
    this.state = { ...this.state, theme };
    this.render();
  }

  private rerender(): void {
    if (this.state !== null) this.render();
  }

  private context(state: AppStateSnapshot): RenderContext {
    const locale = pickLocale(state.settings.language, state.locale, this.navigatorLanguage);
    return { t: createTranslator(locale), locale, settings: state.settings, theme: state.theme, now: this.now() };
  }

  private isEmpty(): boolean {
    return this.state === null || !this.state.accounts.some((account) => account.enabled);
  }

  private render(): WidgetRendered {
    const state = this.state;
    if (state === null) return 'empty';
    const ctx = this.context(state);
    const doc = this.root.ownerDocument;
    applyDocumentTheme(doc, 'widget', state, ctx.locale);
    const { t, settings } = ctx;
    const empty = this.isEmpty();
    const views = empty ? [] : buildEnabledViews(state, ctx.now);

    this.bar.className = [
      'widget-root',
      `skin-${skinFor(state)}`,
      `theme-${settings.theme}`,
      settings.showCardBackground ? 'has-card-bg' : 'no-card-bg',
      empty ? 'is-empty' : '',
    ]
      .filter(Boolean)
      .join(' ');
    setStyles(this.bar, { '--bg-alpha': String(Math.min(1, Math.max(0.1, settings.alphaPercent / 100))) });

    const title = empty ? t('noAccountTitle') : t('widgetClickTitle');
    setAttr(this.main, 'title', title);
    setAttr(this.main, 'aria-label', title);

    // Rebuild items only when their rendered form would change (keeps the refresh button and focus stable).
    const signature = JSON.stringify({ empty, views, settings, locale: ctx.locale, scheme: state.theme.taskbarScheme, minute: Math.floor(ctx.now / 60_000) });
    if (signature !== this.lastSignature) {
      this.lastSignature = signature;
      if (empty) {
        this.main.replaceChildren(h('span', { class: 'white-circle-dot', 'aria-hidden': 'true' }));
        this.summary.textContent = title;
      } else {
        const items = views.map((view) => {
          const item = renderWidgetItem(view, ctx);
          const pace = view.state === 'ok' ? this.fastAccounts.get(view.account.id) : undefined;
          if (pace !== undefined) {
            item.classList.add('is-fast');
            item.title += `\n${t('quotaPaceFast', { recent: pace.recent.toFixed(1), usual: pace.usual.toFixed(1) })}`;
          }
          return item;
        });
        this.main.replaceChildren(...items);
        this.summary.textContent = items.map((item) => item.getAttribute('title') ?? '').join('. ');
      }
    }

    this.refreshButton.hidden = empty;
    this.updateRefreshButton();
    this.schedule(() => this.reportSize());
    return empty ? 'empty' : 'accounts';
  }

  isRefreshSpinning(): boolean {
    return this.pendingRefresh || (this.state?.refresh.inFlight ?? false);
  }

  isRefreshDisabled(): boolean {
    return this.now() < this.cooldownUntil || this.isRefreshSpinning();
  }

  private updateRefreshButton(): void {
    const state = this.state;
    if (state === null) return;
    const t = this.context(state).t;
    const spinning = this.isRefreshSpinning();
    const label = spinning ? t('refreshing') : t('widgetRefresh');
    this.refreshButton.classList.toggle('is-spinning', spinning);
    setAttr(this.refreshButton, 'aria-label', label);
    setAttr(this.refreshButton, 'title', label);
    setAttr(this.refreshButton, 'aria-busy', spinning ? 'true' : 'false');
    // aria-disabled keeps keyboard focus on the button while it is inert.
    setAttr(this.refreshButton, 'aria-disabled', this.isRefreshDisabled() ? 'true' : 'false');
  }

  private activateMain(): void {
    const now = this.now();
    if (now - this.lastToggleAt < TOGGLE_DEBOUNCE_MS) return;
    this.lastToggleAt = now;
    if (this.isEmpty()) void this.api.invoke('window:show-popup', { tab: 'accounts' });
    else void this.api.invoke('window:toggle-popup', null);
  }

  requestRefresh(): void {
    if (this.isEmpty() || this.isRefreshDisabled()) return;
    const now = this.now();
    this.cooldownUntil = now + REFRESH_COOLDOWN_MS;
    this.pendingRefresh = true;
    this.updateRefreshButton();
    if (this.cooldownTimer !== null) clearTimeout(this.cooldownTimer);
    this.cooldownTimer = setTimeout(() => {
      this.cooldownTimer = null;
      this.updateRefreshButton();
    }, REFRESH_COOLDOWN_MS);
    void this.api
      .invoke('usage:refresh-now', { accountId: null })
      .catch(() => undefined)
      .finally(() => {
        this.pendingRefresh = false;
        this.updateRefreshButton();
      });
  }

  private reportSize(): void {
    const size = this.measure(this.bar);
    if (!(size.width > 0) || !(size.height > 0)) return;
    // The bar is capped at the window width; add what the items lost so the window can grow to fit.
    const clipped = Math.max(0, this.main.scrollWidth - this.main.clientWidth);
    const next = {
      width: Math.ceil(size.width + clipped) + SIZE_MARGIN,
      height: Math.max(MIN_HEIGHT, Math.ceil(size.height) + SIZE_MARGIN),
    };
    if (this.lastSize !== null && this.lastSize.width === next.width && this.lastSize.height === next.height) return;
    this.lastSize = next;
    void this.api.invoke('window:resize-widget', next);
  }
}

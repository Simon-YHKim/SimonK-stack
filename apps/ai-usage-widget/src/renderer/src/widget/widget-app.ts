import { createTranslator } from '../../../shared/i18n';
import type { AppStateSnapshot, ThemeTokens } from '../../../shared/types';
import type { Api } from '../api';
import { h, s, setAttr, setStyles, uniqueId } from '../dom';
import { providerIcon, refreshGlyph } from '../icons';
import { currentNavigatorLanguage, pickLocale } from '../locale';
import { V1_COLORS, buildEnabledViews, itemTooltip, toRow, type AccountView, type RenderContext, type RowView } from '../model';
import { applyDocumentTheme, skinFor } from '../theme';
import { renderWidgetItem } from './themes';
import { modelNoticeText } from '../../../shared/model-notice';
import { GROK_BOT_STATUS_KEYS, grokBotReading, grokBotSpillKey, grokBotWeeklyExhausted } from '../../../shared/grok-bot';
import { formatCountdown } from '../../../shared/usage';

/** Clicks within this window after a toggle are ignored (v1 SPEC §2-5). */
export const TOGGLE_DEBOUNCE_MS = 300;
/** Matches the scheduler's per-account manual refresh spacing (DESIGN §6-3). */
export const REFRESH_COOLDOWN_MS = 5000;
export const TICK_MS = 30_000;
const SIZE_MARGIN = 4;
const MIN_HEIGHT = 34;
const MINUTE_MS = 60_000;
const VALUE_FLASH_MS = 1_400;
const VALUE_FLASH_TONES = ['sky', 'mint', 'violet'] as const;

interface PaceSample {
  at: number;
  used: number;
  resetsAt: number | null;
}

interface FastPace {
  recent: number;
  usual: number | null;
}

/** Detect a short quota burst, or a sustained rise against earlier readings. */
function fastPace(samples: readonly PaceSample[]): FastPace | null {
  const latest = samples.at(-1);
  if (latest === undefined || samples.length < 2) return null;
  const burstStart = [...samples].reverse().find((sample) => {
    const age = latest.at - sample.at;
    return age >= 2 * MINUTE_MS && age <= 15 * MINUTE_MS && latest.used - sample.used >= 12;
  });
  if (burstStart !== undefined) {
    const usualStart = samples.find((sample) => sample.at <= burstStart.at - 10 * MINUTE_MS);
    const usual = usualStart === undefined ? null :
      (burstStart.used - usualStart.used) * 3_600_000 / (burstStart.at - usualStart.at);
    return { recent: (latest.used - burstStart.used) * 3_600_000 / (latest.at - burstStart.at), usual };
  }
  const recentStart = samples.find((sample) => {
    const age = latest.at - sample.at;
    return age >= 2 * MINUTE_MS && age <= 20 * MINUTE_MS;
  });
  if (recentStart === undefined) return null;
  const increase = latest.used - recentStart.used;
  if (increase < 3) return null;
  const usualStart = samples.find((sample) => sample.at <= recentStart.at - 10 * MINUTE_MS);
  const usual = usualStart === undefined ? null :
    (recentStart.used - usualStart.used) * 3_600_000 / (recentStart.at - usualStart.at);
  const recent = increase * 3_600_000 / (latest.at - recentStart.at);
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
  if (positiveSteps < 2 || increase - largestStep < 2) return null;
  return recent >= Math.max(12, (usual ?? 0) * 2.5) ? { recent, usual } : null;
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
  private hasSeenGrokBot = false;
  private lastSize: Size | null = null;
  private tickTimer: ReturnType<typeof setInterval> | null = null;
  private readonly paceHistory = new Map<string, Map<string, PaceSample[]>>();
  private readonly fastAccounts = new Map<string, FastPace>();
  private readonly announcedFastAccounts = new Set<string>();
  private visiblePercent = new Map<string, number>();
  private lastShowUsedPercent: boolean | null = null;
  private flashSequence = 0;

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
      if (event.target === this.main && (event.key === 'Enter' || event.key === ' ')) {
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
    // Keep the Bot row visible after an automatic session fails or is removed.
    if (state.grokBotAuto !== undefined && state.grokBotAuto.state !== 'unavailable') this.hasSeenGrokBot = true;
    this.observePace(state);
    const rendered = this.render();
    const locale = this.context(state).locale;
    for (const [accountId, pace] of this.fastAccounts) {
      if (this.announcedFastAccounts.has(accountId)) continue;
      this.announcedFastAccounts.add(accountId);
      void this.api.invoke('window:show-pace-bubble', { accountId, recent: pace.recent, usual: pace.usual, locale });
    }
    for (const accountId of this.announcedFastAccounts) {
      if (!this.fastAccounts.has(accountId)) this.announcedFastAccounts.delete(accountId);
    }
    return rendered;
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
          const pace = this.now() - last.at <= 25 * MINUTE_MS ? fastPace(samples) : null;
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
        const pace = this.now() - at <= 25 * MINUTE_MS ? fastPace(samples) : null;
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

  private markChangedPercent(key: string, percent: number, next: Map<string, number>,
    target: HTMLElement | null, eligible: boolean, showUsedPercent: boolean): void {
    next.set(key, percent);
    if (!eligible || target === null || this.lastShowUsedPercent !== showUsedPercent ||
      this.visiblePercent.get(key) === undefined || this.visiblePercent.get(key) === percent) return;
    const tone = VALUE_FLASH_TONES[this.flashSequence % VALUE_FLASH_TONES.length];
    this.flashSequence += 1;
    target.dataset.valueFlash = tone;
    setTimeout(() => {
      if (target.dataset.valueFlash === tone) delete target.dataset.valueFlash;
    }, VALUE_FLASH_MS);
  }

  private isEmpty(): boolean {
    return this.state === null || (!this.state.accounts.some((account) => account.enabled) &&
      !this.showGrokBot(this.state));
  }

  private showGrokBot(state: AppStateSnapshot): boolean {
    return state.settings.grokBotUsedPercent !== null || this.hasSeenGrokBot;
  }

  private grokBotRow(state: AppStateSnapshot, ctx: RenderContext): RowView {
    const reading = grokBotReading(state.settings, ctx.now, state.grokBotAuto);
    const numeric = reading.state === 'fresh' || reading.state === 'stale' || reading.state === 'automatic';
    return {
      ...toRow({ kind: 'weekly', usedPercent: numeric ? reading.usedPercent : null,
        resetsAt: numeric ? reading.resetsAt : null,
        windowMinutes: 10_080, label: 'Grok Bot' }, ctx.now, state.settings.showUsedPercent),
      tag: 'Bot',
      isStale: reading.state === 'stale' || reading.state === 'expired',
    };
  }

  private grokWithBotView(view: AccountView, state: AppStateSnapshot, ctx: RenderContext): AccountView {
    const cliRow = view.rows.find((row) => row.kind === 'weekly') ??
      (view.rows.length > 0 ? view.windows.find((row) => row.kind === 'weekly') : undefined) ?? view.rows[0] ??
      toRow({ kind: 'weekly', usedPercent: null, resetsAt: null, windowMinutes: 10_080 }, ctx.now,
        state.settings.showUsedPercent);
    // A failed Grok CLI fetch must not hide a valid, independently measured Bot quota.
    return { ...view, state: 'ok', rows: [
      { ...cliRow, isStale: view.state === 'stale' || view.state === 'error' },
      this.grokBotRow(state, ctx),
    ] };
  }

  private grokBotItem(state: AppStateSnapshot, ctx: RenderContext): HTMLElement {
    const reading = grokBotReading(state.settings, ctx.now, state.grokBotAuto);
    const numeric = reading.state === 'fresh' || reading.state === 'stale' || reading.state === 'automatic';
    const percent = numeric ? (state.settings.showUsedPercent ? reading.usedPercent : reading.leftPercent) : null;
    const value = percent === null ? '—' : `${percent}% ${ctx.t(state.settings.showUsedPercent ? 'unitUsed' : 'unitLeft')}`;
    const automaticStatus = state.grokBotAuto?.state === 'login-expired' ? 'grokBotAutoExpired' :
      state.grokBotAuto?.state === 'unavailable' ? 'grokBotAutoUnavailable' :
      state.grokBotAuto?.state === 'error' ? 'grokBotAutoError' : null;
    const status = reading.state === 'unknown' && automaticStatus !== null ? ctx.t(automaticStatus) :
      ctx.t(GROK_BOT_STATUS_KEYS[reading.state]);
    const resetsAt = numeric ? reading.resetsAt : null;
    const countdown = resetsAt === null ? null : formatCountdown(resetsAt - ctx.now);
    const exhausted = grokBotWeeklyExhausted(reading);
    const titleParts = [ctx.t('grokBotTitle'), value, status];
    if (countdown !== null) titleParts.push(ctx.t('grokBotResetsIn', { time: countdown }));
    if (exhausted) titleParts.push(ctx.t(grokBotSpillKey(state.settings.grokBotOnDemandLimitCents)));
    // Same colour rule as the measured rows: only with "Color by Usage" and never in monochrome.
    const flagged = exhausted && state.settings.colorByUsage && state.settings.iconStyle !== 'monochrome';
    const valueEl = h('strong', { class: 'grok-bot-widget-value' }, [value]);
    if (flagged && state.settings.theme !== 'windows') setStyles(valueEl, { color: V1_COLORS.critical });
    return h('div', {
      class: `account-item grok-bot-item${reading.state === 'fresh' || reading.state === 'automatic' ? '' : ' is-stale'}${flagged ? ' is-exhausted' : ''}`,
      'data-provider': 'grok-bot',
      title: titleParts.join(' · '),
    }, [
      providerIcon('grok', 16, state.settings.iconStyle === 'monochrome'),
      h('span', { class: 'grok-bot-widget-name' }, [ctx.t('grokBotWidget')]),
      valueEl,
      countdown === null ? null : h('small', { class: 'grok-bot-widget-reset' }, [countdown]),
      h('small', { class: 'grok-bot-widget-manual' }, [status]),
    ]);
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
    const signature = JSON.stringify({ empty, views, settings, grokBotAuto: state.grokBotAuto, notices: state.modelNotices,
      pace: [...this.fastAccounts], locale: ctx.locale, scheme: state.theme.taskbarScheme, minute: Math.floor(ctx.now / 60_000) });
    if (signature !== this.lastSignature) {
      this.lastSignature = signature;
      const nextVisiblePercent = new Map<string, number>();
      if (empty) {
        this.main.replaceChildren(h('span', { class: 'white-circle-dot', 'aria-hidden': 'true' }));
        this.summary.textContent = title;
      } else {
        const botItem = this.showGrokBot(state) ? this.grokBotItem(state, ctx) : null;
        let groupedGrokBot = false;
        const items = views.map((view) => {
          const groupBot = botItem !== null && !groupedGrokBot && view.account.provider === 'grok';
          const displayView = groupBot ? this.grokWithBotView(view, state, ctx) : view;
          const item = renderWidgetItem(displayView, ctx);
          const rowElements = item.querySelectorAll<HTMLElement>('[data-status]');
          displayView.rows.forEach((row, index) => {
            if (row.status !== 'value' || row.shownPercent === null) return;
            const isBot = groupBot && row.tag === 'Bot';
            const key = isBot ? 'grok-bot' : JSON.stringify([view.account.id, row.kind, row.label, row.windowMinutes]);
            this.markChangedPercent(key, Math.round(row.shownPercent), nextVisiblePercent,
              rowElements.item(index), isBot || view.state === 'ok', settings.showUsedPercent);
          });
          if (groupBot) {
            item.dataset.state = view.state;
            item.title = `${itemTooltip(view, ctx)}\n${botItem.title}`;
            groupedGrokBot = true;
          }
          const notice = state.modelNotices.find((entry) => entry.provider === view.account.provider);
          if (notice !== undefined) {
            const message = modelNoticeText(notice, ctx.locale, ctx.now);
            const badge = h('button', {
              type: 'button', class: 'model-notice-badge', title: message,
              'aria-label': `${message}. ${ctx.locale === 'ko' ? '공식 발표 열기' : 'Open official announcement'}`,
            }, ['✦']);
            badge.addEventListener('click', (event) => {
              event.stopPropagation();
              void this.api.invoke('model-notice:open', { provider: notice.provider });
            });
            item.append(badge);
            item.title += `\n${message}`;
          }
          const pace = view.state === 'ok' ? this.fastAccounts.get(view.account.id) : undefined;
          if (pace !== undefined) {
            item.classList.add('is-fast');
            // Shape cue (triangle by the icon) so the warning never depends on colour alone; the
            // value-change cue is an underline on the number instead (widget.css, DECISIONS 26.10.04).
            item.append(s('svg', { class: 'pace-mark', viewBox: '0 0 10 9', width: 10, height: 9,
              'aria-hidden': 'true', focusable: 'false' }, [s('path', { d: 'M5 .8 9.4 8.3H.6Z' })]));
            item.title += `\n${pace.usual === null ? t('quotaPaceBurst', { recent: pace.recent.toFixed(1) }) :
              t('quotaPaceFast', { recent: pace.recent.toFixed(1), usual: pace.usual.toFixed(1) })}`;
          }
          return item;
        });
        if (botItem !== null && !groupedGrokBot) {
          const reading = grokBotReading(settings, ctx.now, state.grokBotAuto);
          if (reading.state === 'fresh' || reading.state === 'stale' || reading.state === 'automatic') {
            const shown = settings.showUsedPercent ? reading.usedPercent : reading.leftPercent;
            this.markChangedPercent('grok-bot', Math.round(shown), nextVisiblePercent,
              botItem.querySelector<HTMLElement>('.grok-bot-widget-value'),
              reading.state !== 'stale', settings.showUsedPercent);
          }
          items.push(botItem);
        }
        this.main.replaceChildren(...items);
        this.summary.textContent = items.map((item) => item.getAttribute('title') ?? '').join('. ');
      }
      this.visiblePercent = nextVisiblePercent;
      this.lastShowUsedPercent = settings.showUsedPercent;
    }

    this.refreshButton.hidden = !state.accounts.some((account) => account.enabled) &&
      !this.hasSeenGrokBot;
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
    else if (this.state !== null && !this.state.accounts.some((account) => account.enabled)) void this.api.invoke('window:show-popup', { tab: 'usage' });
    else void this.api.invoke('window:toggle-popup', null);
  }

  requestRefresh(): void {
    if (this.isEmpty() || this.state === null || this.refreshButton.hidden || this.isRefreshDisabled()) return;
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

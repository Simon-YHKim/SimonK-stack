import { createTranslator, type Translator } from '../../../shared/i18n';
import {
  POPUP_TABS,
  type AppStateSnapshot,
  type LoginEventMessage,
  type PopupTab,
  type ThemeTokens,
} from '../../../shared/types';
import type { Api } from '../api';
import { h, setAttr, setText, uniqueId } from '../dom';
import { refreshGlyph } from '../icons';
import { currentNavigatorLanguage, pickLocale } from '../locale';
import { buildEnabledViews, type RenderContext } from '../model';
import { applyDocumentTheme } from '../theme';
import { AccountsTab } from './accounts-tab';
import { SettingsTab } from './settings-tab';
import { UsageTab } from './usage-tab';

export interface PopupDeps {
  api: Api;
  root: HTMLElement;
  now?: () => number;
  navigatorLanguage?: string;
}

export const STATUS_CLEAR_MS = 6000;
const TICK_MS = 30_000;

const TAB_LABEL_KEYS = { usage: 'tabUsage', accounts: 'tabAccounts', settings: 'tabSettings' } as const;

export class PopupApp {
  private readonly api: Api;
  private readonly root: HTMLElement;
  private readonly doc: Document;
  private readonly now: () => number;
  private readonly navigatorLanguage: string;
  private state: AppStateSnapshot | null = null;
  private translator: Translator = createTranslator('en');
  private activeTab: PopupTab = 'usage';
  private pendingRefresh = false;
  private statusTimer: ReturnType<typeof setTimeout> | null = null;
  private tickTimer: ReturnType<typeof setInterval> | null = null;

  readonly popupRoot: HTMLElement;
  private readonly titleEl: HTMLElement;
  private readonly badgeEl: HTMLElement;
  readonly refreshButton: HTMLButtonElement;
  readonly closeButton: HTMLButtonElement;
  readonly tabs: Readonly<Record<PopupTab, HTMLButtonElement>>;
  readonly panels: Readonly<Record<PopupTab, HTMLElement>>;
  readonly statusEl: HTMLElement;
  readonly usage: UsageTab;
  readonly accounts: AccountsTab;
  readonly settings: SettingsTab;

  constructor(deps: PopupDeps) {
    this.api = deps.api;
    this.root = deps.root;
    this.doc = deps.root.ownerDocument;
    this.now = deps.now ?? Date.now;
    this.navigatorLanguage = deps.navigatorLanguage ?? currentNavigatorLanguage();
    const translator = (): Translator => this.translator;
    const report = (message: string): void => this.report(message);

    this.usage = new UsageTab();
    this.accounts = new AccountsTab({ api: this.api, translator, report });
    this.settings = new SettingsTab({
      api: this.api,
      translator,
      report,
      setLock: (locked) => void this.api.invoke('window:set-popup-lock', { locked }),
    });

    this.titleEl = h('span', { class: 'popup-title-text' });
    this.badgeEl = h('span', { class: 'popup-title-badge' });
    this.refreshButton = h('button', { type: 'button', class: 'icon-button popup-refresh' }, [refreshGlyph(13)]);
    this.closeButton = h('button', { type: 'button', class: 'icon-button popup-close' }, ['×']);

    const tabIds = {} as Record<PopupTab, string>;
    const panelIds = {} as Record<PopupTab, string>;
    for (const tab of POPUP_TABS) {
      tabIds[tab] = uniqueId(`tab-${tab}`);
      panelIds[tab] = uniqueId(`panel-${tab}`);
    }
    const tabEls = {} as Record<PopupTab, HTMLButtonElement>;
    const panelEls = {} as Record<PopupTab, HTMLElement>;
    const contents: Record<PopupTab, HTMLElement> = {
      usage: this.usage.el,
      accounts: this.accounts.el,
      settings: this.settings.el,
    };
    for (const tab of POPUP_TABS) {
      tabEls[tab] = h('button', {
        type: 'button',
        role: 'tab',
        class: 'popup-tab',
        id: tabIds[tab],
        'data-tab': tab,
        'aria-controls': panelIds[tab],
        'aria-selected': 'false',
        tabindex: -1,
      });
      panelEls[tab] = h('div', { role: 'tabpanel', class: 'popup-panel', id: panelIds[tab], 'aria-labelledby': tabIds[tab], tabindex: 0, hidden: true }, [
        contents[tab],
      ]);
    }
    this.tabs = tabEls;
    this.panels = panelEls;
    this.statusEl = h('div', { class: 'popup-status', role: 'status', 'aria-live': 'polite', hidden: true });

    const tablist = h('div', { class: 'popup-tabs', role: 'tablist' }, POPUP_TABS.map((tab) => tabEls[tab]));
    this.popupRoot = h('div', { class: 'popup-root' }, [
      h('header', { class: 'popup-header' }, [
        h('h1', { class: 'popup-title' }, [this.titleEl, this.badgeEl]),
        h('div', { class: 'popup-actions' }, [this.refreshButton, this.closeButton]),
      ]),
      tablist,
      h('div', { class: 'popup-body' }, POPUP_TABS.map((tab) => panelEls[tab])),
      this.statusEl,
    ]);
    this.root.replaceChildren(this.popupRoot);

    for (const tab of POPUP_TABS) {
      tabEls[tab].addEventListener('click', () => this.selectTab(tab, false));
    }
    tablist.addEventListener('keydown', (event) => this.onTabKey(event));
    this.refreshButton.addEventListener('click', () => this.refreshAll());
    this.closeButton.addEventListener('click', () => this.hide());
    this.doc.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && !event.defaultPrevented) {
        event.preventDefault();
        this.hide();
      }
    });
    this.doc.addEventListener('visibilitychange', () => {
      if (this.doc.visibilityState === 'visible') this.onShown();
    });
    this.api.on('login:event', (message) => this.onLoginEvent(message));
    this.selectTab('usage', false);
  }

  start(): void {
    if (this.tickTimer === null) {
      this.tickTimer = setInterval(() => {
        if (this.doc.visibilityState !== 'hidden') this.render();
      }, TICK_MS);
    }
  }

  stop(): void {
    if (this.tickTimer !== null) clearInterval(this.tickTimer);
    this.tickTimer = null;
  }

  getActiveTab(): PopupTab {
    return this.activeTab;
  }

  update(state: AppStateSnapshot): 'empty' | 'accounts' {
    this.state = state;
    this.render();
    return state.accounts.some((a) => a.enabled) ? 'accounts' : 'empty';
  }

  updateTheme(theme: ThemeTokens): void {
    if (this.state === null) return;
    this.state = { ...this.state, theme };
    this.render();
  }

  onLoginEvent(message: LoginEventMessage): void {
    this.accounts.onLoginEvent(message);
  }

  hide(): void {
    void this.api.invoke('window:hide-popup', null);
  }

  selectTab(tab: PopupTab, focus: boolean): void {
    const changed = tab !== this.activeTab;
    this.activeTab = tab;
    for (const id of POPUP_TABS) {
      const selected = id === tab;
      setAttr(this.tabs[id], 'aria-selected', String(selected));
      setAttr(this.tabs[id], 'tabindex', selected ? '0' : '-1');
      this.tabs[id].classList.toggle('active', selected);
      this.panels[id].hidden = !selected;
    }
    if (focus) this.tabs[tab].focus();
    if (tab === 'accounts' && (changed || focus)) this.accounts.onShow();
  }

  private onTabKey(event: KeyboardEvent): void {
    const index = POPUP_TABS.indexOf(this.activeTab);
    let next: number | null = null;
    if (event.key === 'ArrowRight') next = (index + 1) % POPUP_TABS.length;
    else if (event.key === 'ArrowLeft') next = (index - 1 + POPUP_TABS.length) % POPUP_TABS.length;
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = POPUP_TABS.length - 1;
    const tab = next === null ? undefined : POPUP_TABS[next];
    if (tab === undefined) return;
    event.preventDefault();
    this.selectTab(tab, true);
  }

  private onShown(): void {
    this.popupRoot.classList.remove('is-entering');
    this.popupRoot.getBoundingClientRect(); // restart the entry animation
    this.popupRoot.classList.add('is-entering');
    // Opened from an empty widget: show where accounts are added (V1-35).
    if (this.state !== null && this.state.accounts.length === 0) this.selectTab('accounts', false);
    else if (this.activeTab === 'accounts') this.accounts.onShow();
    this.render();
  }

  private refreshAll(): void {
    if (this.pendingRefresh || (this.state?.refresh.inFlight ?? false)) return;
    this.pendingRefresh = true;
    this.renderHeader();
    void this.api
      .invoke('usage:refresh-now', { accountId: null })
      .catch(() => undefined)
      .finally(() => {
        this.pendingRefresh = false;
        this.renderHeader();
      });
  }

  report(message: string): void {
    setText(this.statusEl, message);
    this.statusEl.hidden = message.length === 0;
    if (this.statusTimer !== null) clearTimeout(this.statusTimer);
    this.statusTimer = setTimeout(() => {
      this.statusTimer = null;
      setText(this.statusEl, '');
      this.statusEl.hidden = true;
    }, STATUS_CLEAR_MS);
  }

  private context(state: AppStateSnapshot): RenderContext {
    const locale = pickLocale(state.settings.language, state.locale, this.navigatorLanguage);
    this.translator = createTranslator(locale);
    return { t: this.translator, locale, settings: state.settings, theme: state.theme, now: this.now() };
  }

  private renderHeader(): void {
    const state = this.state;
    if (state === null) return;
    const t = this.translator;
    const spinning = this.pendingRefresh || state.refresh.inFlight;
    const label = spinning ? t('refreshing') : t('refresh');
    this.refreshButton.classList.toggle('is-spinning', spinning);
    setAttr(this.refreshButton, 'aria-label', label);
    setAttr(this.refreshButton, 'title', label);
    setAttr(this.refreshButton, 'aria-busy', String(spinning));
    setAttr(this.refreshButton, 'aria-disabled', String(spinning || !state.accounts.some((a) => a.enabled)));
  }

  private render(): void {
    const state = this.state;
    if (state === null) return;
    const ctx = this.context(state);
    applyDocumentTheme(this.doc, 'popup', state, ctx.locale);
    const { t } = ctx;
    const views = buildEnabledViews(state, ctx.now);

    setText(this.titleEl, t('popupTitle'));
    setText(this.badgeEl, t('accountsActive', { count: views.length }));
    setAttr(this.closeButton, 'aria-label', t('close'));
    setAttr(this.closeButton, 'title', t('close'));
    for (const tab of POPUP_TABS) setText(this.tabs[tab], t(TAB_LABEL_KEYS[tab]));
    this.renderHeader();

    this.usage.update(views, ctx);
    this.accounts.update(state, ctx);
    this.settings.update(state.settings, ctx);
  }
}

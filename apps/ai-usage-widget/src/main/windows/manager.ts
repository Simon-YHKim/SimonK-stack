import { BrowserWindow, screen, type Display } from 'electron';
import type { EventChannel, EventContract, PlacementPreview, ResizeWidgetRequest, ShowPaceBubbleRequest } from '../../shared/ipc';
import type { Settings } from '../../shared/settings';
import type { Locale, ModelNotice, PopupTab, ThemeTokens, ViewId } from '../../shared/types';
import type { WindowsPort } from '../app/controller';
import { sendEvent } from '../ipc/register';
import type { Logger } from '../log';
import { ZOrderKeeper } from '../platform/zorder';
import type { NativeWindowOps } from '../platform/user32';
import { POPUP_SIZE, WIDGET_INITIAL_SIZE, applyMaterial, createPopupWindow, createWidgetWindow, hwndOf } from '.';
import {
  computePopupBounds,
  computeModelBubbleBounds,
  computeWidgetBounds,
  detectTaskbar,
  type AppBarInfo,
  type Rect,
  type TaskbarInfo,
  type WidgetPlacement,
} from './placement';
import { PopupController } from './popup-state';

export interface WindowManagerOptions {
  preloadPath: string;
  devTools: boolean;
  entryUrl(view: ViewId): string;
  bubbleEntryUrl(): string;
  settings: Settings;
  theme: ThemeTokens;
  native: NativeWindowOps | null;
  logger: Logger;
  onLoadProblem(view: ViewId, message: string): void;
  onWidgetVisibilityChange?(visible: boolean): void;
  /** Placement actually in use changed (docked falls back to floating on side/auto-hide taskbars). */
  onEffectiveModeChange?(mode: Settings['placementMode']): void;
}

export interface WindowSmokeInfo {
  widget: { bounds: Rect | null; visible: boolean; transparentSurface: boolean };
  popup: { bounds: Rect | null; visible: boolean; size: { width: number; height: number } };
  taskbar: TaskbarInfo | null;
  effectiveMode: Settings['placementMode'] | null;
  widgetInsideDisplay: boolean;
}

type BubbleEntry =
  | { kind: 'model'; notice: ModelNotice; locale: Locale; attempts: number }
  | { kind: 'pace'; id: string; alert: ShowPaceBubbleRequest & { label: string }; attempts: number };

function bubbleId(entry: BubbleEntry): string {
  return entry.kind === 'model' ? entry.notice.id : entry.id;
}

function sameRect(a: Rect, b: Rect): boolean {
  return a.x === b.x && a.y === b.y && a.width === b.width && a.height === b.height;
}

export class WindowManager implements WindowsPort {
  private widget: BrowserWindow | null = null;
  private popup: BrowserWindow | null = null;
  private modelBubble: BrowserWindow | null = null;
  private modelBubbleId: string | null = null;
  private modelBubbleTimer: ReturnType<typeof setTimeout> | null = null;
  private modelBubbleLoading = false;
  private readonly modelBubbleQueue: BubbleEntry[] = [];
  private readonly modelBubbleShown = new Set<string>();
  private readonly lastPaceBubbleAt = new Map<string, number>();
  private activeModelNoticeIds = new Set<string>();
  private settings: Settings;
  private theme: ThemeTokens;
  private widgetSize: ResizeWidgetRequest = { ...WIDGET_INITIAL_SIZE };
  private userHidden = true;
  private fullscreenHidden = false;
  private closing = false;
  private placement: (WidgetPlacement & { taskbar: TaskbarInfo; display: Display }) | null = null;
  private preview: PlacementPreview | null = null;
  private reportedMode: Settings['placementMode'] | null = null;
  private pendingPopupTab: PopupTab | null = null;
  private readonly popupState: PopupController;
  readonly zorder: ZOrderKeeper;

  constructor(private readonly options: WindowManagerOptions) {
    this.settings = { ...options.settings };
    this.theme = { ...options.theme };
    this.popupState = new PopupController({
      isVisible: () => this.popup !== null && !this.popup.isDestroyed() && this.popup.isVisible(),
      show: (focus) => this.showPopupWindow(focus),
      hide: () => {
        if (this.popup !== null && !this.popup.isDestroyed()) this.popup.hide();
      },
    });
    this.zorder = new ZOrderKeeper({
      native: options.native,
      logger: options.logger.child('zorder'),
      onFullscreenChange: (fullscreen) => this.onFullscreenChange(fullscreen),
      target: {
        widgetHwnd: () => hwndOf(this.widget),
        ownHwnds: () => [hwndOf(this.widget), hwndOf(this.popup), hwndOf(this.modelBubble)].filter((h): h is bigint => h !== null),
        isWidgetShown: () => this.widget !== null && !this.widget.isDestroyed() && this.widget.isVisible(),
        moveTop: () => this.widget?.moveTop(),
      },
    });
  }

  /** Creates both windows and loads their renderer entry. */
  async create(): Promise<void> {
    const factory = {
      preloadPath: this.options.preloadPath,
      devTools: this.options.devTools,
      material: this.settings.material,
      theme: this.theme,
    };
    const initial = this.computePlacement();
    const widget = createWidgetWindow({ ...factory, bounds: initial.bounds });
    const popup = createPopupWindow(factory);
    this.widget = widget;
    this.popup = popup;
    this.setPlacement(initial);
    applyMaterial(widget, this.settings.material, this.theme, this.theme.taskbarScheme);
    applyMaterial(popup, this.settings.material, this.theme, this.theme.scheme);
    this.wire('widget', widget);
    this.wire('popup', popup);
    popup.setAlwaysOnTop(true, 'pop-up-menu');
    popup.on('blur', () => this.popupState.onBlur());
    popup.on('focus', () => this.popupState.onFocus());
    popup.on('hide', () => this.popupState.onHidden());
    this.applyTopmost();

    const load = (view: ViewId, win: BrowserWindow): Promise<void> =>
      win.loadURL(this.options.entryUrl(view)).catch((error: unknown) => {
        this.options.logger.error('loadURL failed', { view, error });
        this.options.onLoadProblem(view, 'loadURL failed');
      });
    await Promise.all([load('widget', widget), load('popup', popup)]);
  }

  private wire(view: ViewId, win: BrowserWindow): void {
    win.on('close', (event) => {
      if (this.closing) return;
      event.preventDefault();
      if (view === 'popup') this.popupState.hide();
      else this.hideWidget();
    });
    win.webContents.on('did-fail-load', (_event, code) => {
      this.options.logger.error('renderer failed to load', { view, code });
      this.options.onLoadProblem(view, `did-fail-load ${code}`);
    });
    win.webContents.on('render-process-gone', (_event, details) => {
      this.options.logger.error('renderer process gone', { view, reason: details.reason });
      this.options.onLoadProblem(view, `render-process-gone ${details.reason}`);
    });
  }

  // ---------------------------------------------------------------------------
  // Placement

  private targetDisplay(appBar: AppBarInfo | null): Display {
    if (appBar !== null) return screen.getDisplayMatching(appBar.rect);
    return screen.getPrimaryDisplay();
  }

  private readAppBar(): AppBarInfo | null {
    const native = this.options.native;
    if (native === null) return null;
    try {
      const bar = native.taskbarAppBar();
      if (bar === null) return null;
      const physical = {
        x: bar.rect.left,
        y: bar.rect.top,
        width: bar.rect.right - bar.rect.left,
        height: bar.rect.bottom - bar.rect.top,
      };
      if (physical.width <= 0 || physical.height <= 0) return null;
      return { edge: bar.edge, autoHide: bar.autoHide, rect: screen.screenToDipRect(null, physical) };
    } catch (error) {
      this.options.logger.warn('taskbar query failed', { error });
      return null;
    }
  }

  private computePlacement(): WidgetPlacement & { taskbar: TaskbarInfo; display: Display } {
    const appBar = this.readAppBar();
    const display = this.targetDisplay(appBar);
    const geometry = { bounds: display.bounds, workArea: display.workArea };
    const taskbar = detectTaskbar(geometry, appBar);
    const settings = this.preview === null ? this.settings : { ...this.settings, ...this.preview };
    return { ...computeWidgetBounds(settings, geometry, taskbar, this.widgetSize), taskbar, display };
  }

  private setPlacement(next: WidgetPlacement & { taskbar: TaskbarInfo; display: Display }): void {
    this.placement = next;
    if (next.effectiveMode === this.reportedMode) return;
    this.reportedMode = next.effectiveMode;
    this.options.onEffectiveModeChange?.(next.effectiveMode);
  }

  /** Re-places the widget and an open popup (display changes, resize, settings; V1-27). */
  reposition(): void {
    const widget = this.widget;
    if (widget === null || widget.isDestroyed()) return;
    const next = this.computePlacement();
    this.setPlacement(next);
    if (!sameRect(widget.getBounds(), next.bounds)) widget.setBounds(next.bounds);
    if (this.modelBubble?.isVisible()) this.hideModelBubble();
    const popup = this.popup;
    // The popup stays put while its offset slider previews: moving it with the widget would shift
    // the track under a still pointer and feed back into the value. It follows once the preview ends.
    if (this.preview === null && popup !== null && !popup.isDestroyed() && popup.isVisible()) {
      popup.setBounds(this.popupBounds(next));
    }
    this.applyTopmost();
  }

  private popupBounds(placement: WidgetPlacement & { taskbar: TaskbarInfo; display: Display }): Rect {
    return computePopupBounds(placement.bounds, placement.taskbar, placement.display.workArea, POPUP_SIZE);
  }

  private applyTopmost(): void {
    const widget = this.widget;
    if (widget === null || widget.isDestroyed()) return;
    const keepOnTop = this.placement?.effectiveMode === 'docked' || this.settings.alwaysOnTop;
    if (keepOnTop) widget.setAlwaysOnTop(true, 'screen-saver');
    else widget.setAlwaysOnTop(false);
    this.zorder.configure(!this.userHidden, keepOnTop);
  }

  // ---------------------------------------------------------------------------
  // WindowsPort

  applySettings(settings: Settings, theme: ThemeTokens): void {
    const previous = this.settings;
    this.settings = { ...settings };
    this.theme = { ...theme };
    this.preview = null;
    const transparencyChanged = (previous.material === 'none') !== (settings.material === 'none');
    if (transparencyChanged) {
      void this.recreate();
      return;
    }
    if (this.widget !== null) applyMaterial(this.widget, settings.material, theme, theme.taskbarScheme);
    if (this.popup !== null) applyMaterial(this.popup, settings.material, theme, theme.scheme);
    this.reposition();
  }

  /** The transparent flag is fixed at creation, so switching to/from a material rebuilds both windows. */
  private async recreate(): Promise<void> {
    const wasShown = !this.userHidden;
    // Material is chosen in the popup's settings tab; bring the user back there.
    const popupWasVisible = this.popup !== null && !this.popup.isDestroyed() && this.popup.isVisible();
    this.destroyWindows();
    this.closing = false;
    await this.create();
    if (wasShown) this.showWidget();
    if (popupWasVisible) this.showPopup('settings', true);
  }

  resizeWidget(size: ResizeWidgetRequest): void {
    this.widgetSize = { width: size.width, height: size.height };
    this.reposition();
  }

  previewPlacement(patch: PlacementPreview | null): void {
    this.preview = patch === null ? null : { ...patch };
    this.reposition();
  }

  showWidget(): void {
    this.userHidden = false;
    this.options.onWidgetVisibilityChange?.(true);
    const widget = this.widget;
    if (widget === null || widget.isDestroyed()) return;
    this.reposition();
    if (!this.fullscreenHidden) widget.showInactive();
    if (!this.fullscreenHidden && this.modelBubbleQueue.length > 0) void this.showNextModelBubble();
    this.applyTopmost();
  }

  hideWidget(): void {
    this.userHidden = true;
    this.options.onWidgetVisibilityChange?.(false);
    this.popupState.hide();
    this.hideModelBubble();
    if (this.widget !== null && !this.widget.isDestroyed()) this.widget.hide();
    this.applyTopmost();
  }

  toggleWidget(): void {
    if (this.userHidden) this.showWidget();
    else this.hideWidget();
  }

  get widgetShownByUser(): boolean {
    return !this.userHidden;
  }

  private onFullscreenChange(fullscreen: boolean): void {
    this.fullscreenHidden = fullscreen;
    const widget = this.widget;
    if (widget === null || widget.isDestroyed()) return;
    if (fullscreen) {
      this.popupState.hide();
      this.hideModelBubble();
      if (widget.isVisible()) widget.hide();
    } else if (!this.userHidden) {
      // Restore without stealing focus from the app that left fullscreen (V1-30).
      widget.showInactive();
      this.reposition();
      if (this.modelBubbleQueue.length > 0) void this.showNextModelBubble();
    }
  }

  togglePopup(): void {
    this.popupState.toggle();
  }

  showPopup(tab: PopupTab | null, focus: boolean): void {
    this.pendingPopupTab = tab;
    this.popupState.show(focus);
    this.pendingPopupTab = null;
  }

  hidePopup(): void {
    this.popupState.hide();
  }

  setPopupLock(locked: boolean): void {
    this.popupState.setLocked(locked);
  }

  private showPopupWindow(focus: boolean): void {
    const popup = this.popup;
    if (popup === null || popup.isDestroyed()) return;
    const placement = this.placement ?? this.computePlacement();
    popup.setBounds(this.popupBounds(placement));
    if (focus) {
      popup.show();
      popup.focus();
    } else {
      popup.showInactive();
    }
    // backgroundThrottling:false keeps the Page Visibility API at 'visible', so the
    // renderer learns about every show from this event (entry animation, refreshes).
    sendEvent(popup.webContents, 'popup:show', { tab: this.pendingPopupTab });
  }

  broadcast<E extends EventChannel>(channel: E, payload: EventContract[E]): void {
    for (const win of [this.widget, this.popup]) {
      if (win !== null && !win.isDestroyed()) sendEvent(win.webContents, channel, payload);
    }
  }

  /** A short, click-through speech bubble appears above each vendor icon once per new notice. */
  showModelBubbles(notices: readonly ModelNotice[], locale: Locale): void {
    const activeIds = new Set(notices.map((notice) => notice.id));
    this.activeModelNoticeIds = activeIds;
    for (let index = this.modelBubbleQueue.length - 1; index >= 0; index -= 1) {
      const entry = this.modelBubbleQueue[index];
      if (entry?.kind === 'model' && !activeIds.has(entry.notice.id)) this.modelBubbleQueue.splice(index, 1);
    }
    if (this.modelBubbleId !== null && !this.modelBubbleId.startsWith('pace:') && !activeIds.has(this.modelBubbleId)) this.hideModelBubble();
    for (const notice of notices) {
      if (this.modelBubbleShown.has(notice.id)) continue;
      this.modelBubbleShown.add(notice.id);
      this.modelBubbleQueue.push({ kind: 'model', notice, locale, attempts: 0 });
    }
    if (this.modelBubble === null && !this.modelBubbleLoading) void this.showNextModelBubble();
  }

  showPaceBubble(alert: ShowPaceBubbleRequest & { label: string }): void {
    const now = Date.now();
    if (now - (this.lastPaceBubbleAt.get(alert.accountId) ?? -Infinity) < 15 * 60_000) return;
    this.lastPaceBubbleAt.set(alert.accountId, now);
    this.modelBubbleQueue.push({ kind: 'pace', id: `pace:${alert.accountId}:${now}`, alert, attempts: 0 });
    if (this.modelBubble === null && !this.modelBubbleLoading) void this.showNextModelBubble();
  }

  private async showNextModelBubble(): Promise<void> {
    if (this.closing || this.modelBubble !== null || this.modelBubbleLoading) return;
    const next = this.modelBubbleQueue.shift();
    if (next === undefined) return;
    this.modelBubbleLoading = true;
    const widget = this.widget;
    if (widget === null || widget.isDestroyed() || !widget.isVisible() || this.fullscreenHidden) {
      this.modelBubbleLoading = false;
      this.modelBubbleQueue.unshift(next);
      return;
    }
    // The renderer lays out variable-width themes and accounts; query the target icon's
    // geometry. Provider IDs are fixed; account IDs pass through the IPC ID validator.
    await new Promise((resolve) => setTimeout(resolve, 180));
    const script = next.kind === 'model'
      ? `(() => { const el = document.querySelector('.account-item[data-provider="${next.notice.provider}"] .ai-brand-icon'); if (!el) return null; const r = el.getBoundingClientRect(); return {x:r.x,y:r.y,width:r.width,height:r.height}; })()`
      : `(() => { const item = [...document.querySelectorAll('.account-item')].find(el => el.dataset.accountId === ${JSON.stringify(next.alert.accountId)}); const el = item?.querySelector('.ai-brand-icon'); if (!el) return null; const r = el.getBoundingClientRect(); return {x:r.x,y:r.y,width:r.width,height:r.height}; })()`;
    let icon: Rect | null = null;
    try { icon = await widget.webContents.executeJavaScript(script) as Rect | null; }
    catch (error) { this.options.logger.warn('model bubble anchor failed', { error }); }
    if (next.kind === 'model' && !this.activeModelNoticeIds.has(next.notice.id)) {
      this.modelBubbleLoading = false;
      void this.showNextModelBubble();
      return;
    }
    if (icon === null || widget.isDestroyed() || !widget.isVisible()) {
      this.modelBubbleLoading = false;
      if (icon === null && next.attempts < 2 && !widget.isDestroyed() && widget.isVisible()) {
        this.modelBubbleQueue.unshift({ ...next, attempts: next.attempts + 1 });
        setTimeout(() => { void this.showNextModelBubble(); }, 350);
        return;
      }
      if (next.kind === 'model') this.modelBubbleShown.delete(next.notice.id);
      void this.showNextModelBubble();
      return;
    }
    const bounds = computeModelBubbleBounds(widget.getBounds(), icon, screen.getDisplayMatching(widget.getBounds()).bounds);
    const below = bounds.y > widget.getBounds().y;
    const url = new URL(this.options.bubbleEntryUrl());
    url.searchParams.set('locale', next.kind === 'model' ? next.locale : next.alert.locale);
    if (next.kind === 'model') {
      url.searchParams.set('status', next.notice.status);
      url.searchParams.set('model', next.notice.model);
      if (next.notice.releaseDate !== null) url.searchParams.set('date', next.notice.releaseDate);
    } else {
      url.searchParams.set('kind', 'pace');
      url.searchParams.set('model', next.alert.label.slice(0, 90));
      url.searchParams.set('recent', next.alert.recent.toFixed(1));
      if (next.alert.usual !== null) url.searchParams.set('usual', next.alert.usual.toFixed(1));
    }
    url.searchParams.set('scheme', this.theme.taskbarScheme);
    url.searchParams.set('below', String(below));
    const bubble = new BrowserWindow({ ...bounds, frame: false, transparent: true, backgroundColor: '#00000000',
      resizable: false, skipTaskbar: true, focusable: false, alwaysOnTop: true, show: false,
      webPreferences: { sandbox: true, contextIsolation: true, nodeIntegration: false, webSecurity: true, devTools: false } });
    this.modelBubble = bubble;
    this.modelBubbleId = bubbleId(next);
    this.modelBubbleLoading = false;
    bubble.setIgnoreMouseEvents(true, { forward: true });
    bubble.setAlwaysOnTop(true, 'screen-saver');
    try { await bubble.loadURL(url.toString()); }
    catch (error) { this.options.logger.warn('model bubble load failed', { error }); this.hideModelBubble(); return; }
    if (this.closing || this.userHidden || this.fullscreenHidden) { this.hideModelBubble(); return; }
    bubble.showInactive();
    this.modelBubbleTimer = setTimeout(() => this.hideModelBubble(), 8_000);
  }

  private hideModelBubble(): void {
    if (this.modelBubbleTimer !== null) clearTimeout(this.modelBubbleTimer);
    this.modelBubbleTimer = null;
    if (this.modelBubble !== null && !this.modelBubble.isDestroyed()) this.modelBubble.destroy();
    this.modelBubble = null;
    this.modelBubbleId = null;
    if (!this.closing && this.modelBubbleQueue.length > 0) void this.showNextModelBubble();
  }

  // ---------------------------------------------------------------------------

  smokeInfo(): WindowSmokeInfo {
    const bounds = (win: BrowserWindow | null): Rect | null => (win === null || win.isDestroyed() ? null : win.getBounds());
    const widgetBounds = bounds(this.widget);
    const displayBounds = this.placement?.display.bounds ?? null;
    return {
      widget: {
        bounds: widgetBounds,
        visible: this.widget?.isVisible() ?? false,
        transparentSurface: this.settings.material === 'none',
      },
      popup: { bounds: bounds(this.popup), visible: this.popup?.isVisible() ?? false, size: { ...POPUP_SIZE } },
      taskbar: this.placement?.taskbar ?? null,
      effectiveMode: this.placement?.effectiveMode ?? null,
      widgetInsideDisplay:
        widgetBounds !== null &&
        displayBounds !== null &&
        widgetBounds.x >= displayBounds.x &&
        widgetBounds.y >= displayBounds.y &&
        widgetBounds.x + widgetBounds.width <= displayBounds.x + displayBounds.width &&
        widgetBounds.y + widgetBounds.height <= displayBounds.y + displayBounds.height,
    };
  }

  private destroyWindows(): void {
    this.closing = true;
    this.hideModelBubble();
    this.popupState.dispose();
    for (const win of [this.widget, this.popup]) {
      if (win !== null && !win.isDestroyed()) win.destroy();
    }
    this.widget = null;
    this.popup = null;
  }

  destroy(): void {
    this.zorder.stop();
    this.destroyWindows();
  }
}

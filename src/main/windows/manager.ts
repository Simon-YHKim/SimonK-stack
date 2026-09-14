import { screen, type BrowserWindow, type Display } from 'electron';
import type { EventChannel, EventContract, ResizeWidgetRequest } from '../../shared/ipc';
import type { Settings } from '../../shared/settings';
import type { PopupTab, ThemeTokens, ViewId } from '../../shared/types';
import type { WindowsPort } from '../app/controller';
import { sendEvent } from '../ipc/register';
import type { Logger } from '../log';
import { ZOrderKeeper } from '../platform/zorder';
import type { NativeWindowOps } from '../platform/user32';
import { POPUP_SIZE, WIDGET_INITIAL_SIZE, applyMaterial, createPopupWindow, createWidgetWindow, hwndOf } from '.';
import {
  computePopupBounds,
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
  settings: Settings;
  theme: ThemeTokens;
  native: NativeWindowOps | null;
  logger: Logger;
  onLoadProblem(view: ViewId, message: string): void;
  onWidgetVisibilityChange?(visible: boolean): void;
}

export interface WindowSmokeInfo {
  widget: { bounds: Rect | null; visible: boolean; transparentSurface: boolean };
  popup: { bounds: Rect | null; visible: boolean; size: { width: number; height: number } };
  taskbar: TaskbarInfo | null;
  effectiveMode: Settings['placementMode'] | null;
  widgetInsideDisplay: boolean;
}

function sameRect(a: Rect, b: Rect): boolean {
  return a.x === b.x && a.y === b.y && a.width === b.width && a.height === b.height;
}

export class WindowManager implements WindowsPort {
  private widget: BrowserWindow | null = null;
  private popup: BrowserWindow | null = null;
  private settings: Settings;
  private theme: ThemeTokens;
  private widgetSize: ResizeWidgetRequest = { ...WIDGET_INITIAL_SIZE };
  private userHidden = true;
  private fullscreenHidden = false;
  private closing = false;
  private placement: (WidgetPlacement & { taskbar: TaskbarInfo; display: Display }) | null = null;
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
        ownHwnds: () => [hwndOf(this.widget), hwndOf(this.popup)].filter((h): h is bigint => h !== null),
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
    this.placement = initial;
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
    return { ...computeWidgetBounds(this.settings, geometry, taskbar, this.widgetSize), taskbar, display };
  }

  /** Re-places the widget and an open popup (display changes, resize, settings; V1-27). */
  reposition(): void {
    const widget = this.widget;
    if (widget === null || widget.isDestroyed()) return;
    const next = this.computePlacement();
    this.placement = next;
    if (!sameRect(widget.getBounds(), next.bounds)) widget.setBounds(next.bounds);
    const popup = this.popup;
    if (popup !== null && !popup.isDestroyed() && popup.isVisible()) popup.setBounds(this.popupBounds(next));
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
    this.destroyWindows();
    this.closing = false;
    await this.create();
    if (wasShown) this.showWidget();
  }

  resizeWidget(size: ResizeWidgetRequest): void {
    this.widgetSize = { width: size.width, height: size.height };
    this.reposition();
  }

  showWidget(): void {
    this.userHidden = false;
    this.options.onWidgetVisibilityChange?.(true);
    const widget = this.widget;
    if (widget === null || widget.isDestroyed()) return;
    this.reposition();
    if (!this.fullscreenHidden) widget.showInactive();
    this.applyTopmost();
  }

  hideWidget(): void {
    this.userHidden = true;
    this.options.onWidgetVisibilityChange?.(false);
    this.popupState.hide();
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
      if (widget.isVisible()) widget.hide();
    } else if (!this.userHidden) {
      // Restore without stealing focus from the app that left fullscreen (V1-30).
      widget.showInactive();
      this.reposition();
    }
  }

  togglePopup(): void {
    this.popupState.toggle();
  }

  showPopup(tab: PopupTab | null, focus: boolean): void {
    this.popupState.show(focus);
    if (tab !== null && this.popup !== null && !this.popup.isDestroyed()) {
      sendEvent(this.popup.webContents, 'popup:show', { tab });
    }
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
  }

  broadcast<E extends EventChannel>(channel: E, payload: EventContract[E]): void {
    for (const win of [this.widget, this.popup]) {
      if (win !== null && !win.isDestroyed()) sendEvent(win.webContents, channel, payload);
    }
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

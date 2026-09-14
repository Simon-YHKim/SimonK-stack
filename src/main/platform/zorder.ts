import type { Logger } from '../log';
import { isFullscreenForeground } from './fullscreen';
import type { NativeWindowOps } from './user32';

export const ZORDER_TICK_MS = 1_000;
/** Topmost is re-asserted every N ticks (the Win11 taskbar raises itself on click). */
export const TOPMOST_EVERY_TICKS = 2;

export interface ZOrderTarget {
  /** Widget HWND, null when the window is gone. */
  widgetHwnd(): bigint | null;
  ownHwnds(): bigint[];
  isWidgetShown(): boolean;
  /** Fallback when native ops are unavailable. */
  moveTop(): void;
}

export interface ZOrderOptions {
  native: NativeWindowOps | null;
  target: ZOrderTarget;
  onFullscreenChange(fullscreen: boolean): void;
  logger: Logger;
  tickMs?: number;
}

/**
 * Keeps the widget above the taskbar with SetWindowPos(HWND_TOPMOST, NOACTIVATE)
 * on the same HWND (no helper process, V1-12/28) and reports fullscreen apps on
 * the widget's monitor. The timer runs only while the widget should be visible.
 */
export class ZOrderKeeper {
  private timer: ReturnType<typeof setInterval> | null = null;
  private tick = 0;
  private keepOnTop = false;
  private active = false;
  private fullscreen = false;
  private failures = 0;
  private readonly tickMs: number;

  constructor(private readonly options: ZOrderOptions) {
    this.tickMs = options.tickMs ?? ZORDER_TICK_MS;
  }

  get nativeAvailable(): boolean {
    return this.options.native !== null;
  }

  get isFullscreen(): boolean {
    return this.fullscreen;
  }

  /** `active`: user wants the widget visible. `keepOnTop`: docked, or floating with alwaysOnTop (V1-28). */
  configure(active: boolean, keepOnTop: boolean): void {
    this.keepOnTop = keepOnTop;
    this.active = active;
    const needsTimer = active && (keepOnTop || this.options.native !== null);
    if (needsTimer && this.timer === null) {
      this.timer = setInterval(() => this.onTick(), this.tickMs);
    } else if (!needsTimer) {
      this.stopTimer();
      if (this.fullscreen) this.setFullscreen(false);
    }
    if (active && keepOnTop) this.assertTopmost();
  }

  stop(): void {
    this.active = false;
    this.stopTimer();
  }

  /** One timer step; public for tests. */
  onTick(): void {
    if (!this.active) return;
    this.tick += 1;
    const native = this.options.native;
    if (native !== null) {
      const hwnd = this.options.target.widgetHwnd();
      if (hwnd !== null) {
        try {
          const fullscreen = isFullscreenForeground(native.sampleForeground(), {
            widgetMonitor: native.monitorOf(hwnd),
            ownWindows: this.options.target.ownHwnds(),
          });
          this.setFullscreen(fullscreen);
        } catch (error) {
          this.noteFailure(error);
        }
      }
    }
    if (this.keepOnTop && !this.fullscreen && this.tick % TOPMOST_EVERY_TICKS === 0) this.assertTopmost();
  }

  private assertTopmost(): void {
    if (!this.options.target.isWidgetShown()) return;
    const native = this.options.native;
    if (native === null) {
      this.options.target.moveTop();
      return;
    }
    const hwnd = this.options.target.widgetHwnd();
    if (hwnd === null) return;
    try {
      native.setTopmostNoActivate(hwnd);
    } catch (error) {
      this.noteFailure(error);
    }
  }

  private setFullscreen(value: boolean): void {
    if (value === this.fullscreen) return;
    this.fullscreen = value;
    this.options.onFullscreenChange(value);
  }

  private noteFailure(error: unknown): void {
    this.failures += 1;
    if (this.failures <= 3) this.options.logger.warn('native z-order call failed', { error });
  }

  private stopTimer(): void {
    if (this.timer !== null) clearInterval(this.timer);
    this.timer = null;
  }
}

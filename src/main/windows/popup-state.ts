export interface PopupPort {
  isVisible(): boolean;
  /** `focus` must be true for user-initiated opens so a later blur can hide it (V1-09). */
  show(focus: boolean): void;
  hide(): void;
}

export interface PopupControllerOptions {
  blurHideDelayMs?: number;
  /** A toggle right after a blur-hide means the user clicked the widget to close it. */
  reopenGuardMs?: number;
  now?: () => number;
}

export const BLUR_HIDE_DELAY_MS = 120;
export const REOPEN_GUARD_MS = 400;

/**
 * Popup visibility rules: opens unlocked, hides shortly after losing focus, and
 * stays open only while the renderer holds a lock for an interaction. Hiding
 * always releases the lock so a forgotten unlock cannot pin the popup.
 */
export class PopupController {
  private locked = false;
  private blurredWhileLocked = false;
  private hideTimer: ReturnType<typeof setTimeout> | null = null;
  private lastAutoHideAt = Number.NEGATIVE_INFINITY;
  private readonly blurHideDelayMs: number;
  private readonly reopenGuardMs: number;
  private readonly now: () => number;

  constructor(
    private readonly port: PopupPort,
    options: PopupControllerOptions = {},
  ) {
    this.blurHideDelayMs = options.blurHideDelayMs ?? BLUR_HIDE_DELAY_MS;
    this.reopenGuardMs = options.reopenGuardMs ?? REOPEN_GUARD_MS;
    this.now = options.now ?? Date.now;
  }

  get isLocked(): boolean {
    return this.locked;
  }

  toggle(): void {
    if (this.port.isVisible()) {
      this.hide();
      return;
    }
    if (this.now() - this.lastAutoHideAt < this.reopenGuardMs) return;
    this.show(true);
  }

  show(focus: boolean): void {
    this.cancelTimer();
    this.blurredWhileLocked = false;
    this.port.show(focus);
  }

  hide(): void {
    this.cancelTimer();
    this.locked = false;
    this.blurredWhileLocked = false;
    if (this.port.isVisible()) this.port.hide();
  }

  setLocked(locked: boolean): void {
    this.locked = locked;
    if (locked) {
      this.cancelTimer();
      return;
    }
    // Focus left while an interaction held the lock (e.g. a select dropdown): hide now.
    if (this.blurredWhileLocked) this.onBlur();
  }

  onBlur(): void {
    if (this.locked) {
      this.blurredWhileLocked = true;
      return;
    }
    this.blurredWhileLocked = false;
    this.cancelTimer();
    this.hideTimer = setTimeout(() => {
      this.hideTimer = null;
      if (this.locked || !this.port.isVisible()) return;
      this.lastAutoHideAt = this.now();
      this.locked = false;
      this.port.hide();
    }, this.blurHideDelayMs);
  }

  onFocus(): void {
    this.cancelTimer();
    this.blurredWhileLocked = false;
  }

  /** Window hidden by other means (e.g. closed); keeps state consistent. */
  onHidden(): void {
    this.cancelTimer();
    this.locked = false;
    this.blurredWhileLocked = false;
  }

  dispose(): void {
    this.cancelTimer();
  }

  private cancelTimer(): void {
    if (this.hideTimer !== null) clearTimeout(this.hideTimer);
    this.hideTimer = null;
  }
}

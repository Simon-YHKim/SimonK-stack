/** Win32 RECT in physical pixels. */
export interface RectLTRB {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

export const WS_CAPTION = 0x00c00000;
export const WS_THICKFRAME = 0x00040000;

/** Desktop and shell windows never count as a fullscreen app. */
export const SHELL_WINDOW_CLASSES: readonly string[] = [
  'Progman',
  'WorkerW',
  'Shell_TrayWnd',
  'Shell_SecondaryTrayWnd',
  'Windows.UI.Core.CoreWindow',
];

export interface ForegroundSample {
  /** 0n when there is no foreground window. */
  hwnd: bigint;
  className: string;
  windowRect: RectLTRB | null;
  /** GWL_STYLE bits. */
  style: number;
  zoomed: boolean;
  /** Monitor of the foreground window. */
  monitor: bigint;
  monitorRect: RectLTRB | null;
}

export interface FullscreenContext {
  /** Monitor the widget lives on. */
  widgetMonitor: bigint;
  /** HWNDs owned by this app (widget, popup). */
  ownWindows: readonly bigint[];
}

function covers(outer: RectLTRB, inner: RectLTRB): boolean {
  return inner.left <= outer.left && inner.top <= outer.top && inner.right >= outer.right && inner.bottom >= outer.bottom;
}

/**
 * A foreground window is fullscreen when it covers its whole monitor (not just
 * the work area) on the widget's monitor. A maximized captioned window can also
 * cover the monitor when the taskbar auto-hides; that is not fullscreen (V1-18).
 */
export function isFullscreenForeground(sample: ForegroundSample, context: FullscreenContext): boolean {
  if (sample.hwnd === 0n || context.ownWindows.includes(sample.hwnd)) return false;
  if (SHELL_WINDOW_CLASSES.includes(sample.className)) return false;
  if (sample.monitor === 0n || sample.monitor !== context.widgetMonitor) return false;
  if (sample.windowRect === null || sample.monitorRect === null) return false;
  if (!covers(sample.monitorRect, sample.windowRect)) return false;
  const captioned = (sample.style & WS_CAPTION) === WS_CAPTION;
  if (sample.zoomed && captioned) return false;
  return true;
}

import type { Settings } from '../../shared/settings';

export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Size {
  width: number;
  height: number;
}

export interface DisplayGeometry {
  bounds: Rect;
  workArea: Rect;
}

export type TaskbarEdge = 'bottom' | 'top' | 'left' | 'right';

/** Taskbar reported by SHAppBarMessage, already converted to DIP. */
export interface AppBarInfo {
  edge: TaskbarEdge;
  rect: Rect;
  autoHide: boolean;
}

export interface TaskbarInfo {
  edge: TaskbarEdge;
  rect: Rect;
  autoHide: boolean;
  source: 'work-area' | 'app-bar' | 'assumed';
}

/** v1 constants (SPEC §4-3): tray area reserve on the right, start area on the left. */
export const DOCKED_RIGHT_RESERVE = 220;
export const DOCKED_LEFT_RESERVE = 64;
export const DOCKED_EDGE_MARGIN = 12;
export const FLOATING_GAP = 4;
export const POPUP_GAP = 8;
export const POPUP_EDGE_MARGIN = 12;
export const ASSUMED_TASKBAR_THICKNESS = 48;

export type PlacementSettings = Pick<Settings, 'placementMode' | 'alignment' | 'offsetPx' | 'verticalOffsetPx'>;

function intersects(a: Rect, b: Rect): boolean {
  return a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height;
}

function clamp(value: number, min: number, max: number): number {
  if (max < min) return min;
  return Math.min(max, Math.max(min, value));
}

/**
 * Derives the taskbar from the gap between display bounds and work area. An
 * auto-hide taskbar reserves no work area, so the app bar (when available) wins.
 */
export function detectTaskbar(display: DisplayGeometry, appBar: AppBarInfo | null): TaskbarInfo {
  const b = display.bounds;
  const wa = display.workArea;
  if (appBar !== null && intersects(appBar.rect, b)) {
    return { edge: appBar.edge, rect: { ...appBar.rect }, autoHide: appBar.autoHide, source: 'app-bar' };
  }
  const gaps: { edge: TaskbarEdge; size: number; rect: Rect }[] = [
    {
      edge: 'bottom',
      size: b.y + b.height - (wa.y + wa.height),
      rect: { x: b.x, y: wa.y + wa.height, width: b.width, height: b.y + b.height - (wa.y + wa.height) },
    },
    { edge: 'top', size: wa.y - b.y, rect: { x: b.x, y: b.y, width: b.width, height: wa.y - b.y } },
    { edge: 'left', size: wa.x - b.x, rect: { x: b.x, y: b.y, width: wa.x - b.x, height: b.height } },
    {
      edge: 'right',
      size: b.x + b.width - (wa.x + wa.width),
      rect: { x: wa.x + wa.width, y: b.y, width: b.x + b.width - (wa.x + wa.width), height: b.height },
    },
  ];
  const best = gaps.reduce((acc, gap) => (gap.size > acc.size ? gap : acc));
  if (best.size > 0) return { edge: best.edge, rect: best.rect, autoHide: false, source: 'work-area' };
  return {
    edge: 'bottom',
    rect: { x: b.x, y: b.y + b.height - ASSUMED_TASKBAR_THICKNESS, width: b.width, height: ASSUMED_TASKBAR_THICKNESS },
    autoHide: true,
    source: 'assumed',
  };
}

export interface WidgetPlacement {
  bounds: Rect;
  /** Docked only applies to a visible horizontal taskbar; otherwise the widget floats. */
  effectiveMode: Settings['placementMode'];
}

export function computeWidgetBounds(
  settings: PlacementSettings,
  display: DisplayGeometry,
  taskbar: TaskbarInfo,
  size: Size,
): WidgetPlacement {
  const b = display.bounds;
  const wa = display.workArea;
  const w = Math.round(size.width);
  const h = Math.round(size.height);
  const offset = Math.max(0, Math.round(settings.offsetPx));
  const vo = Math.round(settings.verticalOffsetPx);
  const horizontal = taskbar.edge === 'bottom' || taskbar.edge === 'top';
  const docked = settings.placementMode === 'docked' && horizontal && !taskbar.autoHide;

  let x: number;
  let y: number;
  if (docked) {
    const tb = taskbar.rect;
    x =
      settings.alignment === 'right'
        ? tb.x + tb.width - DOCKED_RIGHT_RESERVE - w - offset
        : tb.x + DOCKED_LEFT_RESERVE + offset;
    x = clamp(x, tb.x + DOCKED_EDGE_MARGIN, tb.x + tb.width - w - DOCKED_EDGE_MARGIN);
    y = tb.y + Math.max(0, Math.floor((tb.height - h) / 2)) + vo;
  } else {
    x = settings.alignment === 'right' ? wa.x + wa.width - w - offset : wa.x + offset;
    x = clamp(x, wa.x, wa.x + wa.width - w);
    // Above a bottom taskbar, below a top one (V1-29), bottom corner for side taskbars.
    y = taskbar.edge === 'top' ? wa.y + FLOATING_GAP + vo : wa.y + wa.height - h - FLOATING_GAP + vo;
  }
  y = clamp(y, b.y, b.y + b.height - h);
  return { bounds: { x, y, width: w, height: h }, effectiveMode: docked ? 'docked' : 'floating' };
}

/** Popup next to the widget, kept inside the work area (V1-27 callers re-run this on moves). */
export function computePopupBounds(widget: Rect, taskbar: TaskbarInfo, workArea: Rect, size: Size): Rect {
  const wa = workArea;
  const pw = Math.round(size.width);
  const ph = Math.round(size.height);
  const x = clamp(
    Math.round(widget.x + widget.width / 2 - pw / 2),
    wa.x + POPUP_EDGE_MARGIN,
    wa.x + wa.width - pw - POPUP_EDGE_MARGIN,
  );
  const minY = wa.y + POPUP_GAP;
  const maxY = wa.y + wa.height - ph - POPUP_GAP;
  let y: number;
  if (taskbar.edge === 'top') {
    y = Math.max(widget.y + widget.height, wa.y) + POPUP_GAP;
  } else {
    y = Math.min(widget.y, wa.y + wa.height) - ph - POPUP_GAP;
  }
  return { x, y: clamp(y, minY, maxY), width: pw, height: ph };
}

export function rectInside(inner: Rect, outer: Rect): boolean {
  return (
    inner.x >= outer.x &&
    inner.y >= outer.y &&
    inner.x + inner.width <= outer.x + outer.width &&
    inner.y + inner.height <= outer.y + outer.height
  );
}

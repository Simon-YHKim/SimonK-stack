import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DEFAULT_SETTINGS } from '../../shared/settings';
import {
  computePopupBounds,
  computeWidgetBounds,
  detectTaskbar,
  rectInside,
  type DisplayGeometry,
  type PlacementSettings,
} from './placement';
import { PopupController, type PopupPort } from './popup-state';

const PRIMARY: DisplayGeometry = {
  bounds: { x: 0, y: 0, width: 3440, height: 1440 },
  workArea: { x: 0, y: 0, width: 3440, height: 1392 },
};
const SIZE = { width: 240, height: 40 };
const base: PlacementSettings = {
  placementMode: DEFAULT_SETTINGS.placementMode,
  alignment: DEFAULT_SETTINGS.alignment,
  offsetPx: DEFAULT_SETTINGS.offsetPx,
  verticalOffsetPx: 0,
};

describe('detectTaskbar', () => {
  it('reads the reserved edge from bounds vs work area', () => {
    expect(detectTaskbar(PRIMARY, null)).toEqual({
      edge: 'bottom',
      rect: { x: 0, y: 1392, width: 3440, height: 48 },
      autoHide: false,
      source: 'work-area',
    });
    const top = { bounds: PRIMARY.bounds, workArea: { x: 0, y: 48, width: 3440, height: 1392 } };
    expect(detectTaskbar(top, null)).toMatchObject({ edge: 'top', rect: { y: 0, height: 48 } });
    const left = { bounds: PRIMARY.bounds, workArea: { x: 60, y: 0, width: 3380, height: 1440 } };
    expect(detectTaskbar(left, null)).toMatchObject({ edge: 'left', rect: { x: 0, width: 60 } });
    const right = { bounds: PRIMARY.bounds, workArea: { x: 0, y: 0, width: 3380, height: 1440 } };
    expect(detectTaskbar(right, null)).toMatchObject({ edge: 'right', rect: { x: 3380, width: 60 } });
  });

  it('prefers the app bar (auto-hide reserves no work area) and assumes bottom otherwise', () => {
    const full = { bounds: PRIMARY.bounds, workArea: PRIMARY.bounds };
    const appBar = { edge: 'bottom' as const, rect: { x: 0, y: 1392, width: 3440, height: 48 }, autoHide: true };
    expect(detectTaskbar(full, appBar)).toMatchObject({ edge: 'bottom', autoHide: true, source: 'app-bar' });
    const elsewhere = { ...appBar, rect: { x: -2560, y: -1440, width: 2560, height: 48 } };
    expect(detectTaskbar(full, elsewhere)).toMatchObject({ source: 'assumed', autoHide: true });
  });
});

describe('computeWidgetBounds', () => {
  const taskbar = detectTaskbar(PRIMARY, null);

  it('docks into a bottom taskbar (v1 formula) on either side', () => {
    expect(computeWidgetBounds(base, PRIMARY, taskbar, SIZE)).toEqual({
      bounds: { x: 3440 - 220 - 240 - 20, y: 1392 + 4, width: 240, height: 40 },
      effectiveMode: 'docked',
    });
    expect(computeWidgetBounds({ ...base, alignment: 'left' }, PRIMARY, taskbar, SIZE).bounds.x).toBe(84);
    expect(computeWidgetBounds({ ...base, offsetPx: 350, verticalOffsetPx: -40 }, PRIMARY, taskbar, SIZE).bounds).toMatchObject({
      x: 3440 - 220 - 240 - 350,
      y: 1356,
    });
  });

  it('floats above a bottom taskbar and below a top one (V1-29)', () => {
    const floating = { ...base, placementMode: 'floating' as const };
    expect(computeWidgetBounds(floating, PRIMARY, taskbar, SIZE).bounds).toEqual({ x: 3180, y: 1348, width: 240, height: 40 });
    const topDisplay = { bounds: PRIMARY.bounds, workArea: { x: 0, y: 48, width: 3440, height: 1392 } };
    const result = computeWidgetBounds(floating, topDisplay, detectTaskbar(topDisplay, null), SIZE);
    expect(result.bounds.y).toBe(52);
    expect(rectInside(result.bounds, topDisplay.bounds)).toBe(true);
  });

  it('falls back to floating for side and auto-hide taskbars and stays on negative-coordinate displays', () => {
    const secondary: DisplayGeometry = {
      bounds: { x: -2560, y: -1440, width: 2560, height: 1440 },
      workArea: { x: -2500, y: -1440, width: 2500, height: 1440 },
    };
    const side = computeWidgetBounds(base, secondary, detectTaskbar(secondary, null), SIZE);
    expect(side.effectiveMode).toBe('floating');
    expect(side.bounds).toEqual({ x: -2500 + 2500 - 240 - 20, y: -1440 + 1440 - 40 - 4, width: 240, height: 40 });
    expect(rectInside(side.bounds, secondary.bounds)).toBe(true);

    const hidden = { ...taskbar, autoHide: true };
    expect(computeWidgetBounds(base, PRIMARY, hidden, SIZE).effectiveMode).toBe('floating');
  });

  it('clamps oversized widgets into the display', () => {
    const wide = computeWidgetBounds({ ...base, alignment: 'left', offsetPx: 350 }, PRIMARY, taskbar, { width: 1200, height: 120 });
    expect(rectInside(wide.bounds, PRIMARY.bounds)).toBe(true);
  });
});

describe('computePopupBounds', () => {
  it('opens above a bottom widget and below a top widget, inside the work area', () => {
    const taskbar = detectTaskbar(PRIMARY, null);
    const widget = { x: 2960, y: 1396, width: 240, height: 40 };
    expect(computePopupBounds(widget, taskbar, PRIMARY.workArea, { width: 380, height: 440 })).toEqual({
      x: 2890,
      y: 1392 - 440 - 8,
      width: 380,
      height: 440,
    });
    const topArea = { x: 0, y: 48, width: 3440, height: 1392 };
    const top = computePopupBounds({ x: 10, y: 4, width: 240, height: 40 }, { ...taskbar, edge: 'top' }, topArea, {
      width: 380,
      height: 440,
    });
    expect(top).toEqual({ x: 12, y: 56, width: 380, height: 440 });
  });
});

describe('PopupController', () => {
  let visible = false;
  let calls: string[] = [];
  const port: PopupPort = {
    isVisible: () => visible,
    show: (focus) => {
      visible = true;
      calls.push(focus ? 'show-focus' : 'show-inactive');
    },
    hide: () => {
      visible = false;
      calls.push('hide');
    },
  };

  beforeEach(() => {
    vi.useFakeTimers();
    visible = false;
    calls = [];
  });
  afterEach(() => vi.useRealTimers());

  it('opens focused and unlocked, so blur hides it (V1-09)', () => {
    const popup = new PopupController(port, { now: () => Date.now() });
    popup.toggle();
    expect(calls).toEqual(['show-focus']);
    expect(popup.isLocked).toBe(false);
    popup.onBlur();
    vi.advanceTimersByTime(119);
    expect(visible).toBe(true);
    vi.advanceTimersByTime(1);
    expect(visible).toBe(false);
  });

  it('stays open only while locked, and hiding releases the lock', () => {
    const popup = new PopupController(port, { now: () => Date.now() });
    popup.show(true);
    popup.setLocked(true);
    popup.onBlur();
    vi.advanceTimersByTime(1_000);
    expect(visible).toBe(true);
    popup.hide();
    expect(popup.isLocked).toBe(false);
    popup.show(true);
    popup.onBlur();
    popup.onFocus();
    vi.advanceTimersByTime(1_000);
    expect(visible).toBe(true);
  });

  it('hides once the lock is released after a blur it had ignored (CR-01)', () => {
    const popup = new PopupController(port, { now: () => Date.now() });
    popup.show(true);
    popup.setLocked(true); // select dropdown opened
    popup.onBlur(); // user clicked the desktop
    vi.advanceTimersByTime(1_000);
    expect(visible).toBe(true);
    popup.setLocked(false); // select blur
    vi.advanceTimersByTime(119);
    expect(visible).toBe(true);
    vi.advanceTimersByTime(1);
    expect(visible).toBe(false);

    // Focus coming back before the unlock (option picked) keeps the popup open.
    popup.show(true);
    popup.setLocked(true);
    popup.onBlur();
    popup.onFocus();
    popup.setLocked(false);
    vi.advanceTimersByTime(1_000);
    expect(visible).toBe(true);
  });

  it('treats a widget click that caused the blur as a close, not a reopen', () => {
    const popup = new PopupController(port, { now: () => Date.now() });
    popup.toggle();
    popup.onBlur();
    popup.toggle();
    expect(visible).toBe(false);

    popup.toggle();
    popup.onBlur();
    vi.advanceTimersByTime(150);
    expect(visible).toBe(false);
    popup.toggle();
    expect(visible).toBe(false);
    vi.advanceTimersByTime(500);
    popup.toggle();
    expect(visible).toBe(true);
  });
});

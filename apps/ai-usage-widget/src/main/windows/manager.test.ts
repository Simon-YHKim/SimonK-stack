import { afterEach, describe, expect, it, vi } from 'vitest';
import { DEFAULT_SETTINGS, type Settings } from '../../shared/settings';
import type { ThemeTokens } from '../../shared/types';
import { nullLogger } from '../log';
import { WindowManager } from './manager';
import type { Rect } from './placement';

const fakes = vi.hoisted(() => {
  interface FakeWindow {
    bounds: Rect;
    visible: boolean;
    setBoundsCalls: Rect[];
    getBounds(): Rect;
    setBounds(rect: Rect): void;
    isDestroyed(): boolean;
    isVisible(): boolean;
    show(): void;
    showInactive(): void;
    focus(): void;
    hide(): void;
    on(): void;
    loadURL(): Promise<void>;
    setAlwaysOnTop(): void;
    moveTop(): void;
    destroy(): void;
    webContents: { on(): void; send(): void; isDestroyed(): boolean };
  }
  const made: FakeWindow[] = [];
  const make = (initial: Rect): FakeWindow => {
    const win: FakeWindow = {
      bounds: { ...initial },
      visible: false,
      setBoundsCalls: [],
      getBounds: () => ({ ...win.bounds }),
      setBounds: (rect) => {
        win.bounds = { ...rect };
        win.setBoundsCalls.push({ ...rect });
      },
      isDestroyed: () => false,
      isVisible: () => win.visible,
      show: () => {
        win.visible = true;
      },
      showInactive: () => {
        win.visible = true;
      },
      focus: () => undefined,
      hide: () => {
        win.visible = false;
      },
      on: () => undefined,
      loadURL: () => Promise.resolve(),
      setAlwaysOnTop: () => undefined,
      moveTop: () => undefined,
      destroy: () => undefined,
      webContents: { on: () => undefined, send: () => undefined, isDestroyed: () => false },
    };
    made.push(win);
    return win;
  };
  const display = {
    bounds: { x: 0, y: 0, width: 3440, height: 1440 },
    workArea: { x: 0, y: 0, width: 3440, height: 1392 },
  };
  return { made, make, display };
});

vi.mock('electron', () => ({
  screen: {
    getPrimaryDisplay: () => fakes.display,
    getDisplayMatching: () => fakes.display,
    screenToDipRect: (_win: unknown, rect: Rect) => rect,
  },
}));

vi.mock('./index', () => ({
  POPUP_SIZE: { width: 380, height: 440 },
  WIDGET_INITIAL_SIZE: { width: 240, height: 40 },
  applyMaterial: () => undefined,
  hwndOf: () => null,
  createWidgetWindow: (options: { bounds: Rect }) => fakes.make(options.bounds),
  createPopupWindow: () => fakes.make({ x: 0, y: 0, width: 380, height: 440 }),
}));


const THEME: ThemeTokens = {
  scheme: 'light',
  taskbarScheme: 'dark',
  highContrast: false,
  accent: '#0078d4',
  reducedTransparency: false,
  effectiveMaterial: 'none',
};

const managers: InstanceType<typeof WindowManager>[] = [];

afterEach(() => {
  for (const manager of managers.splice(0)) manager.destroy();
  fakes.made.splice(0);
});

async function openWithPopup(settings: Settings = { ...DEFAULT_SETTINGS }) {
  const manager = new WindowManager({
    preloadPath: 'preload.js',
    devTools: false,
    entryUrl: (view) => `app://${view}/index.html`,
    settings,
    theme: THEME,
    native: null,
    logger: nullLogger,
    onLoadProblem: () => undefined,
  });
  managers.push(manager);
  await manager.create();
  const [widget, popup] = fakes.made;
  if (widget === undefined || popup === undefined) throw new Error('windows not created');
  manager.showPopup('settings', true);
  return { manager, widget, popup };
}

describe('WindowManager placement preview', () => {
  it.each(['right', 'left'] as const)(
    'keeps the popup still while an offset preview moves the widget (%s alignment)',
    async (alignment) => {
      const { manager, widget, popup } = await openWithPopup({ ...DEFAULT_SETTINGS, alignment, offsetPx: 20 });
      const popupBefore = popup.getBounds();
      const widgetBefore = widget.getBounds();
      const moves = popup.setBoundsCalls.length;

      for (const offsetPx of [60, 120, 300]) manager.previewPlacement({ offsetPx });
      manager.resizeWidget({ width: 300, height: 40 });
      expect(widget.getBounds().x).not.toBe(widgetBefore.x);
      expect(popup.setBoundsCalls).toHaveLength(moves);
      expect(popup.getBounds()).toEqual(popupBefore);

      // Ending the preview without saving lines the popup up with the saved placement again.
      manager.previewPlacement(null);
      expect(popup.setBoundsCalls.length).toBeGreaterThan(moves);
    },
  );

  it('moves the open popup once the previewed offset is saved', async () => {
    const { manager, widget, popup } = await openWithPopup();
    const popupBefore = popup.getBounds();
    manager.previewPlacement({ offsetPx: 300 });
    expect(popup.getBounds()).toEqual(popupBefore);

    manager.applySettings({ ...DEFAULT_SETTINGS, offsetPx: 300 }, THEME);
    const widgetNow = widget.getBounds();
    const popupNow = popup.getBounds();
    expect(popupNow.x).not.toBe(popupBefore.x);
    expect(popupNow.x + popupNow.width / 2).toBeCloseTo(widgetNow.x + widgetNow.width / 2, 0);
  });

  it('still re-places an open popup when the widget moves without a preview (V1-27)', async () => {
    const { manager, popup } = await openWithPopup();
    const popupBefore = popup.getBounds();
    manager.resizeWidget({ width: 600, height: 40 });
    expect(popup.getBounds().x).not.toBe(popupBefore.x);
  });
});

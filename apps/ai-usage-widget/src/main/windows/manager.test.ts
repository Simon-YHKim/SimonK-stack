import { afterEach, describe, expect, it, vi } from 'vitest';
import { DEFAULT_SETTINGS, type Settings } from '../../shared/settings';
import type { ModelNotice, ThemeTokens } from '../../shared/types';
import { nullLogger } from '../log';
import { WindowManager } from './manager';
import type { Rect } from './placement';

const fakes = vi.hoisted(() => {
  interface FakeWindow {
    bounds: Rect;
    visible: boolean;
    destroyed: boolean;
    setBoundsCalls: Rect[];
    loadedUrls: string[];
    getBounds(): Rect;
    setBounds(rect: Rect): void;
    isDestroyed(): boolean;
    isVisible(): boolean;
    show(): void;
    showInactive(): void;
    focus(): void;
    hide(): void;
    on(): void;
    loadURL(url: string): Promise<void>;
    setIgnoreMouseEvents(): void;
    setAlwaysOnTop(): void;
    moveTop(): void;
    destroy(): void;
    webContents: { on(): void; send(): void; isDestroyed(): boolean; executeJavaScript(script: string): Promise<unknown> };
  }
  const made: FakeWindow[] = [];
  const scripts = { result: (_script: string): unknown => ({ x: 20, y: 10, width: 18, height: 18 }) };
  const make = (initial: Rect): FakeWindow => {
    const win: FakeWindow = {
      bounds: { ...initial },
      visible: false,
      destroyed: false,
      setBoundsCalls: [],
      loadedUrls: [],
      getBounds: () => ({ ...win.bounds }),
      setBounds: (rect) => {
        win.bounds = { ...rect };
        win.setBoundsCalls.push({ ...rect });
      },
      isDestroyed: () => win.destroyed,
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
      loadURL: (url: string) => { win.loadedUrls.push(url); return Promise.resolve(); },
      setIgnoreMouseEvents: () => undefined,
      setAlwaysOnTop: () => undefined,
      moveTop: () => undefined,
      destroy: () => { win.destroyed = true; win.visible = false; },
      webContents: { on: () => undefined, send: () => undefined, isDestroyed: () => false,
        executeJavaScript: (script: string) => Promise.resolve(scripts.result(script)) },
    };
    made.push(win);
    return win;
  };
  const display = {
    bounds: { x: 0, y: 0, width: 3440, height: 1440 },
    workArea: { x: 0, y: 0, width: 3440, height: 1392 },
  };
  return { made, make, display, scripts };
});

vi.mock('electron', () => ({
  BrowserWindow: class { constructor(options: Rect) { return fakes.make(options); } },
  screen: {
    getPrimaryDisplay: () => fakes.display,
    getDisplayMatching: () => fakes.display,
    screenToDipRect: (_win: unknown, rect: Rect) => rect,
  },
}));

describe('WindowManager model bubble', () => {
  it('loads a trusted bubble page above the vendor icon without taking focus', async () => {
    vi.useFakeTimers();
    try {
      const { manager } = await openWithPopup();
      manager.showWidget();
      const notice: ModelNotice = { id: 'released:grok:grok5', provider: 'grok', model: 'Grok 5',
        status: 'released', releaseDate: null, url: 'https://docs.x.ai/developers/models', observedAt: 1 };
      manager.showModelBubbles([notice], 'ko');
      await vi.advanceTimersByTimeAsync(200);
      const bubble = fakes.made[2];
      expect(bubble?.loadedUrls[0]).toContain('app://bundle/model-bubble.html?');
      expect(bubble?.loadedUrls[0]).toContain('model=Grok+5');
      expect(bubble?.isVisible()).toBe(true);
      manager.showModelBubbles([], 'ko');
      expect(bubble?.isDestroyed()).toBe(true);
    } finally { vi.useRealTimers(); }
  });
  it('anchors a pace warning to its account and limits repeated callouts', async () => {
    vi.useFakeTimers();
    try {
      const { manager } = await openWithPopup();
      manager.showWidget();
      manager.showPaceBubble({ accountId: 'g1', label: 'Grok work', recent: 192, usual: null, locale: 'ko' });
      await vi.advanceTimersByTimeAsync(200);
      expect(fakes.made[2]?.loadedUrls[0]).toContain('kind=pace');
      expect(fakes.made[2]?.loadedUrls[0]).toContain('model=Grok+work');
      expect(fakes.made[2]?.isVisible()).toBe(true);
      manager.showPaceBubble({ accountId: 'g1', label: 'Grok work', recent: 200, usual: null, locale: 'ko' });
      expect(fakes.made).toHaveLength(3);
    } finally { vi.useRealTimers(); }
  });
  it('fits the bubble window to its measured text before showing it', async () => {
    vi.useFakeTimers();
    const icon = { x: 20, y: 10, width: 18, height: 18 };
    fakes.scripts.result = (script) => script.includes('documentElement') ? { x: 0, y: 0, width: 264, height: 97.4 } : icon;
    try {
      const { manager } = await openWithPopup();
      manager.showWidget();
      manager.showPaceBubble({ accountId: 'g1', label: 'Grok work', recent: 12.3, usual: 4.5, locale: 'ko' });
      await vi.advanceTimersByTimeAsync(200);
      const bubble = fakes.made[2];
      const widget = fakes.made[0]?.getBounds();
      expect(bubble?.isVisible()).toBe(true);
      expect(bubble?.getBounds().height).toBe(98);
      expect(bubble?.getBounds().y).toBe((widget?.y ?? 0) - 98 - 6);
    } finally {
      fakes.scripts.result = () => ({ x: 20, y: 10, width: 18, height: 18 });
      vi.useRealTimers();
    }
  });
});

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
    bubbleEntryUrl: () => 'app://bundle/model-bubble.html',
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

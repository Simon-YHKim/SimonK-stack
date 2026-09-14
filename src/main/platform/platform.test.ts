import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { ThemeTokens } from '../../shared/types';
import { nullLogger } from '../log';
import { AUTOSTART_NAME, createAutostart, type LoginItemApi } from './autostart';
import { WS_CAPTION, isFullscreenForeground, type ForegroundSample } from './fullscreen';
import { ThemeService, computeThemeTokens, type ThemeSource } from './theme-core';
import type { NativeWindowOps } from './user32';
import { loadNativeWindowOps } from './user32';
import { ZOrderKeeper } from './zorder';

const MONITOR = { left: 0, top: 0, right: 3440, bottom: 1440 };
const WS_POPUP = 0x80000000;

const sample = (over: Partial<ForegroundSample> = {}): ForegroundSample => ({
  hwnd: 100n,
  className: 'Chrome_WidgetWin_1',
  windowRect: { ...MONITOR },
  style: WS_POPUP,
  zoomed: false,
  monitor: 7n,
  monitorRect: { ...MONITOR },
  ...over,
});
const ctx = { widgetMonitor: 7n, ownWindows: [1n, 2n] };

describe('isFullscreenForeground', () => {
  it('detects a borderless window covering the monitor', () => {
    expect(isFullscreenForeground(sample(), ctx)).toBe(true);
    expect(isFullscreenForeground(sample({ zoomed: true, style: WS_POPUP }), ctx)).toBe(true);
  });

  it('ignores maximized captioned windows, work-area windows, shell, other monitors and own windows', () => {
    expect(isFullscreenForeground(sample({ zoomed: true, style: WS_CAPTION }), ctx)).toBe(false);
    expect(isFullscreenForeground(sample({ windowRect: { ...MONITOR, bottom: 1392 } }), ctx)).toBe(false);
    expect(isFullscreenForeground(sample({ className: 'WorkerW' }), ctx)).toBe(false);
    expect(isFullscreenForeground(sample({ monitor: 8n }), ctx)).toBe(false);
    expect(isFullscreenForeground(sample({ hwnd: 2n }), ctx)).toBe(false);
    expect(isFullscreenForeground(sample({ hwnd: 0n }), ctx)).toBe(false);
    expect(isFullscreenForeground(sample({ windowRect: null }), ctx)).toBe(false);
  });
});

describe('ZOrderKeeper', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  function native(foreground: () => ForegroundSample) {
    const topmost: bigint[] = [];
    const ops: NativeWindowOps = {
      setTopmostNoActivate: (hwnd) => {
        topmost.push(hwnd);
        return true;
      },
      monitorOf: () => 7n,
      sampleForeground: foreground,
      taskbarAppBar: () => null,
    };
    return { ops, topmost };
  }

  const target = (shown = true) => ({
    widgetHwnd: () => 1n,
    ownHwnds: () => [1n, 2n],
    isWidgetShown: () => shown,
    moveTop: vi.fn(),
  });

  it('re-asserts topmost on the same HWND and reports fullscreen transitions', () => {
    let fg = sample({ windowRect: { ...MONITOR, bottom: 1392 } });
    const { ops, topmost } = native(() => fg);
    const changes: boolean[] = [];
    const keeper = new ZOrderKeeper({ native: ops, target: target(), onFullscreenChange: (v) => changes.push(v), logger: nullLogger });
    keeper.configure(true, true);
    expect(topmost).toEqual([1n]);
    vi.advanceTimersByTime(2_000);
    expect(topmost).toEqual([1n, 1n]);

    fg = sample();
    vi.advanceTimersByTime(1_000);
    expect(changes).toEqual([true]);
    vi.advanceTimersByTime(4_000);
    expect(topmost).toHaveLength(2);

    fg = sample({ hwnd: 0n });
    vi.advanceTimersByTime(1_000);
    expect(changes).toEqual([true, false]);
    keeper.stop();
    vi.advanceTimersByTime(10_000);
    expect(changes).toEqual([true, false]);
  });

  it('does not keep floating non-topmost widgets on top (V1-28) but still watches fullscreen', () => {
    const { ops, topmost } = native(() => sample());
    const changes: boolean[] = [];
    const keeper = new ZOrderKeeper({ native: ops, target: target(), onFullscreenChange: (v) => changes.push(v), logger: nullLogger });
    keeper.configure(true, false);
    vi.advanceTimersByTime(3_000);
    expect(topmost).toEqual([]);
    expect(changes).toEqual([true]);
    keeper.configure(false, false);
    expect(changes).toEqual([true, false]);
  });

  it('falls back to moveTop without native ops and survives native exceptions', () => {
    const t = target();
    const fallback = new ZOrderKeeper({ native: null, target: t, onFullscreenChange: () => undefined, logger: nullLogger });
    fallback.configure(true, true);
    vi.advanceTimersByTime(2_000);
    expect(t.moveTop).toHaveBeenCalledTimes(2);
    fallback.configure(true, false);
    vi.advanceTimersByTime(10_000);
    expect(t.moveTop).toHaveBeenCalledTimes(2);

    const throwing = native(() => {
      throw new Error('boom');
    });
    const keeper = new ZOrderKeeper({ native: throwing.ops, target: target(), onFullscreenChange: () => undefined, logger: nullLogger });
    keeper.configure(true, true);
    expect(() => vi.advanceTimersByTime(5_000)).not.toThrow();
    keeper.stop();
  });
});

describe('autostart', () => {
  function fakeApi(items: { name: string; enabled: boolean }[] = []) {
    const writes: Parameters<LoginItemApi['setLoginItemSettings']>[0][] = [];
    const reads: Parameters<LoginItemApi['getLoginItemSettings']>[0][] = [];
    const api: LoginItemApi = {
      setLoginItemSettings: (settings) => writes.push(settings),
      getLoginItemSettings: (options) => {
        reads.push(options);
        return { openAtLogin: items.length > 0, launchItems: items };
      },
    };
    return { api, writes, reads };
  }

  it('never touches the registry when unsupported (dev/smoke)', () => {
    const { api, writes, reads } = fakeApi();
    const autostart = createAutostart({ api, execPath: 'C:\\app.exe', supported: false, logger: nullLogger });
    autostart.setEnabled(true);
    expect(autostart.isEnabled()).toBeNull();
    expect(writes).toEqual([]);
    expect(reads).toEqual([]);
  });

  it('writes and reads with the same name, path and --autostart args (V1-31)', () => {
    const { api, writes, reads } = fakeApi([{ name: AUTOSTART_NAME, enabled: false }]);
    const autostart = createAutostart({ api, execPath: 'C:\\app.exe', supported: true, logger: nullLogger });
    autostart.setEnabled(true);
    expect(writes).toEqual([
      { openAtLogin: true, path: 'C:\\app.exe', args: ['--autostart'], name: 'AIUsageWidgetV2', enabled: true },
    ]);
    expect(autostart.isEnabled()).toBe(false);
    expect(reads).toEqual([{ path: 'C:\\app.exe', args: ['--autostart'] }]);
    expect(AUTOSTART_NAME).not.toBe('electron.app.AI Usage Widget');
  });
});

describe('ThemeService', () => {
  it('emits only real changes and applies material policy', () => {
    let dark = false;
    let reduced = false;
    let trigger = (): void => undefined;
    const source: ThemeSource = {
      read: (material) =>
        computeThemeTokens({
          shouldUseDarkColors: dark,
          shouldUseDarkColorsForSystemIntegratedUI: dark,
          inForcedColorsMode: false,
          prefersReducedTransparency: reduced,
          accentRaw: '0078d4ff',
          material,
        }),
      subscribe: (callback) => {
        trigger = callback;
        return () => {
          trigger = () => undefined;
        };
      },
    };
    const service = new ThemeService(source, 'none');
    const seen: ThemeTokens[] = [];
    service.onChange((tokens) => seen.push(tokens));
    trigger();
    expect(seen).toHaveLength(0);
    dark = true;
    trigger();
    expect(seen.map((t) => t.scheme)).toEqual(['dark']);
    expect(service.setMaterial('mica').effectiveMaterial).toBe('mica');
    reduced = true;
    trigger();
    expect(seen.at(-1)?.effectiveMaterial).toBe('none');
    service.dispose();
  });
});

describe('loadNativeWindowOps', () => {
  it('reports unsupported platforms without loading koffi', async () => {
    await expect(loadNativeWindowOps(nullLogger, 'linux')).resolves.toEqual({
      ops: null,
      status: { loaded: false, error: 'unsupported-platform' },
    });
  });

  it.runIf(process.platform === 'win32')('binds user32/shell32 and performs read-only queries', async () => {
    const result = await loadNativeWindowOps(nullLogger);
    expect(result.status).toEqual({ loaded: true });
    const ops = result.ops!;
    const fg = ops.sampleForeground();
    expect(typeof fg.hwnd).toBe('bigint');
    expect(typeof fg.style).toBe('number');
    const bar = ops.taskbarAppBar();
    if (bar !== null) {
      expect(['bottom', 'top', 'left', 'right']).toContain(bar.edge);
      expect(bar.rect.right).toBeGreaterThan(bar.rect.left);
    }
  });
});

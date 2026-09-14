// koffi bindings for the few user32/shell32 calls the shell needs. Loaded
// lazily; any failure disables z-order keeping and fullscreen detection only.

import type KoffiDefault from 'koffi';
import type { Logger } from '../log';
import type { TaskbarEdge } from '../windows/placement';
import type { ForegroundSample, RectLTRB } from './fullscreen';

export interface AppBarNative {
  edge: TaskbarEdge;
  /** Physical pixels. */
  rect: RectLTRB;
  autoHide: boolean;
}

export interface NativeWindowOps {
  setTopmostNoActivate(hwnd: bigint): boolean;
  monitorOf(hwnd: bigint): bigint;
  sampleForeground(): ForegroundSample;
  /** Primary taskbar via SHAppBarMessage, or null. */
  taskbarAppBar(): AppBarNative | null;
}

export interface NativeLoadResult {
  ops: NativeWindowOps | null;
  status: { loaded: boolean; error?: string };
}

const HWND_TOPMOST = -1;
const SWP_NOSIZE = 0x0001;
const SWP_NOMOVE = 0x0002;
const SWP_NOACTIVATE = 0x0010;
const SWP_NOOWNERZORDER = 0x0200;
const MONITOR_DEFAULTTONULL = 0;
const GWL_STYLE = -16;
const ABM_GETSTATE = 0x4;
const ABM_GETTASKBARPOS = 0x5;
const ABS_AUTOHIDE = 0x1;
const ABE_EDGES: readonly TaskbarEdge[] = ['left', 'top', 'right', 'bottom'];

type KoffiModule = typeof KoffiDefault;
type NativeFn = (...args: unknown[]) => unknown;

function toBig(value: unknown): bigint {
  if (typeof value === 'bigint') return value;
  if (typeof value === 'number' && Number.isFinite(value)) return BigInt(Math.trunc(value));
  return 0n;
}

function toRect(value: unknown): RectLTRB | null {
  if (typeof value !== 'object' || value === null) return null;
  const r = value as Record<string, unknown>;
  const { left, top, right, bottom } = r;
  if (typeof left !== 'number' || typeof top !== 'number' || typeof right !== 'number' || typeof bottom !== 'number') {
    return null;
  }
  return { left, top, right, bottom };
}

const emptyRect = (): RectLTRB => ({ left: 0, top: 0, right: 0, bottom: 0 });

export function bindNativeWindowOps(koffi: KoffiModule): NativeWindowOps {
  const user32 = koffi.load('user32.dll');
  const shell32 = koffi.load('shell32.dll');
  const RECT = koffi.struct({ left: 'int32', top: 'int32', right: 'int32', bottom: 'int32' });
  const MONITORINFO = koffi.struct({
    cbSize: 'uint32',
    rcMonitor: RECT,
    rcWork: RECT,
    dwFlags: 'uint32',
  });
  const APPBARDATA = koffi.struct({
    cbSize: 'uint32',
    hWnd: 'intptr',
    uCallbackMessage: 'uint32',
    uEdge: 'uint32',
    rc: RECT,
    lParam: 'intptr',
  });

  const fn = (lib: ReturnType<KoffiModule['load']>, name: string, result: string, args: unknown[]): NativeFn =>
    lib.func(name, result, args as Parameters<typeof lib.func>[3]) as NativeFn;

  const SetWindowPos = fn(user32, 'SetWindowPos', 'int', ['intptr', 'intptr', 'int', 'int', 'int', 'int', 'uint32']);
  const GetForegroundWindow = fn(user32, 'GetForegroundWindow', 'intptr', []);
  const MonitorFromWindow = fn(user32, 'MonitorFromWindow', 'intptr', ['intptr', 'uint32']);
  const GetMonitorInfoW = fn(user32, 'GetMonitorInfoW', 'int', ['intptr', koffi.inout(koffi.pointer(MONITORINFO))]);
  const GetWindowRect = fn(user32, 'GetWindowRect', 'int', ['intptr', koffi.out(koffi.pointer(RECT))]);
  const GetWindowLongPtrW = fn(user32, 'GetWindowLongPtrW', 'intptr', ['intptr', 'int']);
  const IsZoomed = fn(user32, 'IsZoomed', 'int', ['intptr']);
  const GetClassNameW = fn(user32, 'GetClassNameW', 'int', ['intptr', 'void *', 'int']);
  const SHAppBarMessage = fn(shell32, 'SHAppBarMessage', 'uintptr', ['uint32', koffi.inout(koffi.pointer(APPBARDATA))]);
  const monitorInfoSize = koffi.sizeof(MONITORINFO);
  const appBarSize = koffi.sizeof(APPBARDATA);

  const monitorRect = (monitor: bigint): RectLTRB | null => {
    if (monitor === 0n) return null;
    const info = { cbSize: monitorInfoSize, rcMonitor: emptyRect(), rcWork: emptyRect(), dwFlags: 0 };
    if (GetMonitorInfoW(monitor, info) === 0) return null;
    return toRect(info.rcMonitor);
  };

  const className = (hwnd: bigint): string => {
    const buffer = Buffer.alloc(512);
    const length = Number(GetClassNameW(hwnd, buffer, 256));
    if (!Number.isFinite(length) || length <= 0) return '';
    return buffer.toString('utf16le', 0, Math.min(length, 256) * 2);
  };

  return {
    setTopmostNoActivate(hwnd) {
      const flags = SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_NOOWNERZORDER;
      return SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, flags) !== 0;
    },
    monitorOf(hwnd) {
      return toBig(MonitorFromWindow(hwnd, MONITOR_DEFAULTTONULL));
    },
    sampleForeground() {
      const hwnd = toBig(GetForegroundWindow());
      if (hwnd === 0n) {
        return { hwnd, className: '', windowRect: null, style: 0, zoomed: false, monitor: 0n, monitorRect: null };
      }
      const rectOut: Record<string, unknown> = {};
      const windowRect = GetWindowRect(hwnd, rectOut) !== 0 ? toRect(rectOut) : null;
      const monitor = toBig(MonitorFromWindow(hwnd, MONITOR_DEFAULTTONULL));
      return {
        hwnd,
        className: className(hwnd),
        windowRect,
        style: Number(toBig(GetWindowLongPtrW(hwnd, GWL_STYLE)) & 0xffffffffn),
        zoomed: IsZoomed(hwnd) !== 0,
        monitor,
        monitorRect: monitorRect(monitor),
      };
    },
    taskbarAppBar() {
      const data = { cbSize: appBarSize, hWnd: 0, uCallbackMessage: 0, uEdge: 0, rc: emptyRect(), lParam: 0 };
      if (toBig(SHAppBarMessage(ABM_GETTASKBARPOS, data)) === 0n) return null;
      const edge = ABE_EDGES[data.uEdge];
      const rect = toRect(data.rc);
      if (edge === undefined || rect === null) return null;
      const stateData = { cbSize: appBarSize, hWnd: 0, uCallbackMessage: 0, uEdge: 0, rc: emptyRect(), lParam: 0 };
      const state = Number(toBig(SHAppBarMessage(ABM_GETSTATE, stateData)));
      return { edge, rect, autoHide: (state & ABS_AUTOHIDE) !== 0 };
    },
  };
}

/** Never throws: returns `ops: null` with the reason when koffi or the DLLs are unavailable. */
export async function loadNativeWindowOps(logger: Logger, platform: NodeJS.Platform = process.platform): Promise<NativeLoadResult> {
  if (platform !== 'win32') return { ops: null, status: { loaded: false, error: 'unsupported-platform' } };
  try {
    const mod = (await import('koffi')) as unknown as KoffiModule & { default?: KoffiModule };
    const koffi = typeof mod.load === 'function' ? mod : (mod.default ?? mod);
    const ops = bindNativeWindowOps(koffi);
    ops.sampleForeground();
    return { ops, status: { loaded: true } };
  } catch (error) {
    const message = error instanceof Error ? error.message.slice(0, 200) : 'unknown';
    logger.warn('native window ops unavailable; z-order keeping and fullscreen detection disabled', { error });
    return { ops: null, status: { loaded: false, error: message } };
  }
}

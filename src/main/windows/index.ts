import { BrowserWindow, type WebPreferences } from 'electron';
import type { Material } from '../../shared/settings';
import type { ThemeTokens } from '../../shared/types';
import { opaqueBackground } from '../platform/theme-core';
import type { Rect } from './placement';

export interface WindowFactoryOptions {
  preloadPath: string;
  devTools: boolean;
  /** User setting; a material window cannot use the transparent flag. */
  material: Material;
  theme: ThemeTokens;
}

function webPreferences(options: WindowFactoryOptions): WebPreferences {
  return {
    preload: options.preloadPath,
    sandbox: true,
    contextIsolation: true,
    nodeIntegration: false,
    webSecurity: true,
    spellcheck: false,
    devTools: options.devTools,
    backgroundThrottling: false,
  };
}

export const WIDGET_INITIAL_SIZE = { width: 240, height: 40 } as const;
/** SPEC §4-2. */
export const POPUP_SIZE = { width: 380, height: 440 } as const;
export const WINDOW_TITLE = 'AI Usage Widget';

function surface(options: WindowFactoryOptions, scheme: ThemeTokens['scheme']) {
  if (options.material === 'none') return { transparent: true, backgroundColor: '#00000000' } as const;
  return { transparent: false, thickFrame: false, backgroundColor: opaqueBackground(scheme) } as const;
}

/** Frameless, not in the taskbar, never activated on show. */
export function createWidgetWindow(options: WindowFactoryOptions & { bounds: Rect }): BrowserWindow {
  return new BrowserWindow({
    ...options.bounds,
    ...surface(options, options.theme.taskbarScheme),
    frame: false,
    resizable: false,
    maximizable: false,
    minimizable: false,
    fullscreenable: false,
    skipTaskbar: true,
    alwaysOnTop: true,
    hasShadow: false,
    focusable: true,
    show: false,
    title: WINDOW_TITLE,
    webPreferences: webPreferences(options),
  });
}

export function createPopupWindow(options: WindowFactoryOptions): BrowserWindow {
  return new BrowserWindow({
    width: POPUP_SIZE.width,
    height: POPUP_SIZE.height,
    ...surface(options, options.theme.scheme),
    frame: false,
    resizable: false,
    maximizable: false,
    minimizable: false,
    fullscreenable: false,
    skipTaskbar: true,
    alwaysOnTop: true,
    show: false,
    title: WINDOW_TITLE,
    webPreferences: webPreferences(options),
  });
}

/** Applies Mica/Acrylic only when requested and allowed (high contrast / reduced transparency force none). */
export function applyMaterial(win: BrowserWindow, material: Material, theme: ThemeTokens, scheme: ThemeTokens['scheme']): void {
  if (material === 'none' || win.isDestroyed()) return;
  if (theme.effectiveMaterial !== 'none') {
    win.setBackgroundMaterial(theme.effectiveMaterial);
  } else {
    win.setBackgroundMaterial('none');
    win.setBackgroundColor(opaqueBackground(scheme));
  }
}

export function hwndOf(win: BrowserWindow | null): bigint | null {
  if (win === null || win.isDestroyed()) return null;
  const handle = win.getNativeWindowHandle();
  if (handle.length >= 8) return handle.readBigUInt64LE(0);
  if (handle.length >= 4) return BigInt(handle.readUInt32LE(0));
  return null;
}

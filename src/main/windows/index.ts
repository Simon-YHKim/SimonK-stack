import { BrowserWindow, screen, type WebPreferences } from 'electron';

export interface WindowFactoryOptions {
  preloadPath: string;
  devTools: boolean;
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
export const POPUP_SIZE = { width: 380, height: 440 } as const;

/** Frameless widget bar. Placement against the taskbar is refined by the shell module. */
export function createWidgetWindow(options: WindowFactoryOptions & { show: boolean }): BrowserWindow {
  const { workArea } = screen.getPrimaryDisplay();
  const { width, height } = WIDGET_INITIAL_SIZE;
  const win = new BrowserWindow({
    x: workArea.x + workArea.width - width - 20,
    y: workArea.y + workArea.height - height - 4,
    width,
    height,
    frame: false,
    transparent: true,
    resizable: false,
    maximizable: false,
    minimizable: false,
    fullscreenable: false,
    skipTaskbar: true,
    alwaysOnTop: true,
    hasShadow: false,
    show: false,
    title: 'AI Usage Widget',
    webPreferences: webPreferences(options),
  });
  if (options.show) win.once('ready-to-show', () => win.showInactive());
  return win;
}

export function createPopupWindow(options: WindowFactoryOptions): BrowserWindow {
  return new BrowserWindow({
    width: POPUP_SIZE.width,
    height: POPUP_SIZE.height,
    frame: false,
    resizable: false,
    maximizable: false,
    minimizable: false,
    fullscreenable: false,
    skipTaskbar: true,
    alwaysOnTop: true,
    show: false,
    title: 'AI Usage Widget',
    webPreferences: webPreferences(options),
  });
}

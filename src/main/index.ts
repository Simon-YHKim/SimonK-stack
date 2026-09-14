import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { app, ipcMain, nativeTheme, session } from 'electron';
import { resolveLocale } from '../shared/i18n';
import { EVENTS, clampWidgetSize } from '../shared/ipc';
import { DEFAULT_SETTINGS } from '../shared/settings';
import type { AppStateSnapshot } from '../shared/types';
import { parseLaunchArgs, type LaunchArgs } from './app/args';
import { SmokeTracker } from './app/smoke';
import { createInitialSnapshot } from './app/state';
import type { InvokeHandlers } from './ipc/dispatch';
import { registerInvokeHandlers, sendEvent } from './ipc/register';
import { createConsoleSink, createFileSink, createLogger, type LogSink, type Logger } from './log';
import { bridgeRootFor, profilesRootFor, resolveLocalDataRoot, resolveResourcesDir, userDataPathFor } from './paths';
import { readThemeTokens } from './platform/theme';
import { handleAppProtocol, registerAppSchemePrivileges } from './protocol';
import { devCsp, isTrustedRendererUrl, rendererEntryUrl } from './protocol/urls';
import { createProviderRegistry } from './providers/registry';
import { hardenApp, hardenSession } from './security';
import { createPopupWindow, createWidgetWindow } from './windows';

const APP_USER_MODEL_ID = 'local.aiusagewidget';

/** userData is set explicitly before ready; smoke runs never touch the real profile. */
function configureUserData(args: LaunchArgs): { isolated: boolean } {
  const explicit = app.commandLine.getSwitchValue('user-data-dir');
  if (explicit.length > 0) {
    app.setPath('userData', path.resolve(explicit));
    return { isolated: true };
  }
  if (args.smoke) {
    app.setPath('userData', mkdtempSync(path.join(os.tmpdir(), 'aiuw-smoke-')));
    return { isolated: true };
  }
  app.setPath('userData', userDataPathFor(app.getPath('appData')));
  return { isolated: false };
}

function writeSmokeReport(target: string | null, json: string): void {
  if (target === null) {
    process.stdout.write(`${json}\n`);
    return;
  }
  const file = path.resolve(target);
  mkdirSync(path.dirname(file), { recursive: true });
  writeFileSync(file, `${json}\n`, 'utf8');
}

async function start(args: LaunchArgs, isolated: boolean, devServerUrl: string | undefined, logger: Logger): Promise<void> {
  const startedAt = Date.now();
  const tracker = args.smoke
    ? new SmokeTracker(startedAt, {
        versions: {
          electron: process.versions.electron,
          chrome: process.versions.chrome,
          node: process.versions.node,
        },
        packaged: app.isPackaged,
        userDataIsolated: isolated,
      })
    : null;
  if (tracker !== null) setTimeout(() => app.exit(2), args.smokeTimeoutMs + 10_000).unref();

  hardenSession(session.defaultSession, devServerUrl === undefined ? undefined : devCsp(devServerUrl));
  if (devServerUrl === undefined) handleAppProtocol(path.join(__dirname, '../renderer'), logger.child('protocol'));

  const localDataRoot = resolveLocalDataRoot(
    process.env,
    isolated ? path.join(app.getPath('userData'), 'local') : undefined,
  );
  const registry = createProviderRegistry({
    logger: logger.child('providers'),
    now: Date.now,
    appVersion: app.getVersion(),
    localDataRoot,
    profilesRoot: profilesRootFor(localDataRoot),
    bridgeRoot: bridgeRootFor(localDataRoot),
    resourcesDir: resolveResourcesDir({
      isPackaged: app.isPackaged,
      resourcesPath: process.resourcesPath,
      appPath: app.getAppPath(),
    }),
    homeDir: os.homedir(),
    env: process.env,
  });

  const settings = { ...DEFAULT_SETTINGS };
  let snapshot: AppStateSnapshot = createInitialSnapshot({
    settings,
    locale: resolveLocale(settings.language, app.getLocale()),
    theme: readThemeTokens(settings.material),
  });

  const preloadPath = path.join(__dirname, '../preload/index.js');
  const devTools = !app.isPackaged;
  const widget = createWidgetWindow({ preloadPath, devTools, show: !args.smoke && !args.hidden });
  const popup = createPopupWindow({ preloadPath, devTools });

  for (const [view, win] of [
    ['widget', widget],
    ['popup', popup],
  ] as const) {
    win.webContents.on('did-fail-load', (_event, code) => {
      logger.error('renderer failed to load', { view, code });
      tracker?.addError(`${view}: did-fail-load ${code}`);
    });
    win.webContents.on('render-process-gone', (_event, details) => {
      logger.error('renderer process gone', { view, reason: details.reason });
      tracker?.addError(`${view}: render-process-gone ${details.reason}`);
    });
  }

  // Scaffold handlers only; the shell module owns the full set.
  const handlers: InvokeHandlers = {
    'app:get-state': () => snapshot,
    'settings:get': () => snapshot.settings,
    'app:renderer-ready': (request) => {
      logger.info('renderer ready', { view: request.view, rendered: request.rendered });
      tracker?.markReady(request, Date.now());
      return null;
    },
    'window:toggle-popup': () => {
      if (popup.isVisible()) popup.hide();
      else popup.show();
      return null;
    },
    'window:show-popup': () => {
      popup.show();
      return null;
    },
    'window:hide-popup': () => {
      popup.hide();
      return null;
    },
    'window:resize-widget': (request) => {
      const size = clampWidgetSize(request);
      widget.setContentSize(size.width, size.height);
      return null;
    },
  };
  registerInvokeHandlers(ipcMain, handlers, {
    isTrustedSender: (url) => isTrustedRendererUrl(url, devServerUrl),
    logger: logger.child('ipc'),
  });

  nativeTheme.on('updated', () => {
    snapshot = { ...snapshot, theme: readThemeTokens(snapshot.settings.material) };
    for (const win of [widget, popup]) {
      if (!win.isDestroyed()) sendEvent(win.webContents, EVENTS.themeChanged, snapshot.theme);
    }
  });
  app.on('second-instance', () => {
    if (!popup.isDestroyed()) {
      popup.show();
      popup.focus();
    }
  });

  const load = (view: 'widget' | 'popup', win: typeof widget): Promise<void> =>
    win.loadURL(rendererEntryUrl(view, devServerUrl)).catch((error: unknown) => {
      logger.error('loadURL failed', { view, error });
      tracker?.addError(`${view}: loadURL failed`);
    });
  await Promise.all([load('widget', widget), load('popup', popup)]);

  if (tracker !== null) {
    await tracker.waitForAll(args.smokeTimeoutMs);
    const report = tracker.report(
      Date.now(),
      registry.list().map((adapter) => adapter.id),
    );
    writeSmokeReport(args.smokeOut, JSON.stringify(report, null, 2));
    app.exit(report.ok ? 0 : 1);
  }
}

function main(): void {
  const args = parseLaunchArgs(process.argv);
  const { isolated } = configureUserData(args);
  const devServerUrl = app.isPackaged ? undefined : process.env.ELECTRON_RENDERER_URL;
  app.setAppUserModelId(APP_USER_MODEL_ID);
  registerAppSchemePrivileges();

  const sinks: LogSink[] = [];
  if (!app.isPackaged || args.smoke) sinks.push(createConsoleSink());
  try {
    sinks.push(createFileSink(path.join(app.getPath('userData'), 'logs', 'main.log')));
  } catch {
    // File logging is best effort.
  }
  const logger = createLogger({ sinks, minLevel: app.isPackaged ? 'info' : 'debug', scope: 'main' });

  if (!app.requestSingleInstanceLock()) {
    logger.info('another instance owns this profile; exiting');
    app.quit();
    return;
  }

  hardenApp((url) => isTrustedRendererUrl(url, devServerUrl), logger.child('security'));
  app.on('window-all-closed', () => app.quit());
  app
    .whenReady()
    .then(() => start(args, isolated, devServerUrl, logger))
    .catch((error: unknown) => {
      logger.error('startup failed', error);
      app.exit(1);
    });
}

main();

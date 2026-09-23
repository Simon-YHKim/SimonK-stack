import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { app, ipcMain, net, Notification, powerMonitor, screen, session, shell } from 'electron';
import { PROVIDER_NAME_KEYS, resolveLocale, t } from '../shared/i18n';
import { INVOKE_CHANNELS } from '../shared/ipc';
import { PROVIDER_TRAITS, type AppStateSnapshot } from '../shared/types';
import { parseLaunchArgs, type LaunchArgs } from './app/args';
import { createAppController, type AppController } from './app/controller';
import { SmokeTracker } from './app/smoke';
import { createInvokeHandlers } from './ipc/handlers';
import { registerInvokeHandlers } from './ipc/register';
import { createConsoleSink, createFileSink, createLogger, type LogSink, type Logger } from './log';
import { bridgeRootFor, profilesRootFor, resolveLocalDataRoot, resolveResourcesDir, userDataPathFor } from './paths';
import { createAutostart } from './platform/autostart';
import { EXTERNAL_LINKS } from './platform/links';
import { systemThemeSource } from './platform/theme';
import { ThemeService } from './platform/theme-core';
import { loadNativeWindowOps } from './platform/user32';
import { handleAppProtocol, registerAppSchemePrivileges } from './protocol';
import { PROD_CSP, devCsp, isTrustedRendererUrl, rendererEntryUrl } from './protocol/urls';
import { createProviderRegistry } from './providers/registry';
import { hardenApp, hardenSession } from './security';
import { openStore } from './store';
import { AppTray } from './tray';
import type { TrayAction, TrayMenuState } from './tray/menu';
import { WindowManager } from './windows/manager';

const APP_USER_MODEL_ID = 'local.aiusagewidget';
const SHUTDOWN_FLUSH_LIMIT_MS = 3_000;
const DISPLAY_DEBOUNCE_MS = 250;

interface Runtime {
  controller: AppController;
  shutdown(): Promise<void>;
}

let runtime: Runtime | null = null;
let pendingReveal = false;

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

function trayStateOf(snapshot: AppStateSnapshot, autostartSupported: boolean): TrayMenuState {
  return {
    locale: snapshot.locale,
    autostartChecked: snapshot.settings.openAtLogin,
    autostartSupported,
    refreshing: snapshot.refresh.inFlight,
  };
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
  if (tracker !== null) setTimeout(() => app.exit(2), args.smokeTimeoutMs + 20_000).unref();

  hardenSession(session.defaultSession, devServerUrl === undefined ? undefined : devCsp(devServerUrl));
  if (devServerUrl === undefined) handleAppProtocol(path.join(__dirname, '../renderer'), logger.child('protocol'));

  const userData = app.getPath('userData');
  const localDataRoot = resolveLocalDataRoot(process.env, isolated ? path.join(userData, 'local') : undefined);
  const profilesRoot = profilesRootFor(localDataRoot);
  const resourcesDir = resolveResourcesDir({
    isPackaged: app.isPackaged,
    resourcesPath: process.resourcesPath,
    appPath: app.getAppPath(),
  });
  const registry = createProviderRegistry({
    logger: logger.child('providers'),
    now: Date.now,
    appVersion: app.getVersion(),
    localDataRoot,
    profilesRoot,
    bridgeRoot: bridgeRootFor(localDataRoot),
    resourcesDir,
    homeDir: os.homedir(),
    env: process.env,
  });

  const store = await openStore({ dir: userData, profilesRoot, logger: logger.child('store') });
  const initialSettings = store.getSettings();
  const native = await loadNativeWindowOps(logger.child('native'));
  const theme = new ThemeService(systemThemeSource, initialSettings.material);
  const autostart = createAutostart({
    api: app,
    execPath: process.execPath,
    // Never registered from development builds or smoke runs.
    supported: app.isPackaged && !args.smoke,
    logger: logger.child('autostart'),
  });

  let controllerRef: AppController | null = null;
  let initialMode: Parameters<AppController['setEffectivePlacementMode']>[0] = null;
  const windows = new WindowManager({
    preloadPath: path.join(__dirname, '../preload/index.js'),
    devTools: !app.isPackaged,
    entryUrl: (view) => rendererEntryUrl(view, devServerUrl),
    settings: initialSettings,
    theme: theme.current(),
    native: native.ops,
    logger: logger.child('windows'),
    onLoadProblem: (view, message) => tracker?.addError(`${view}: ${message}`),
    onEffectiveModeChange: (mode) => {
      if (controllerRef === null) initialMode = mode;
      else controllerRef.setEffectivePlacementMode(mode);
    },
  });

  let tray: AppTray | null = null;
  // Keep one native object per account so Action Center clicks still work after the toast times out.
  const authNotices = new Map<string, Notification>();
  const controller = createAppController({
    store,
    registry,
    windows,
    theme,
    autostart,
    openExternal: (url) => shell.openExternal(url),
    systemLocale: app.getLocale(),
    profilesRoot,
    logger: logger.child('app'),
    externalLinks: EXTERNAL_LINKS,
    onRendererReady: (request) => {
      logger.info('renderer ready', { view: request.view, rendered: request.rendered });
      tracker?.markReady(request, Date.now());
    },
    onSnapshot: (snapshot) => tray?.update(trayStateOf(snapshot, autostart.supported)),
    onAuthRequired: (account) => {
      if (tracker !== null || !Notification.isSupported()) return;
      const locale = resolveLocale(store.getSettings().language, app.getLocale());
      const provider = t(locale, PROVIDER_NAME_KEYS[account.provider]);
      const notice = new Notification({
        title: `${provider} · ${t(locale, 'state_loggedOut')}`,
        body: `${account.label} · ${t(locale, 'trayAccounts')}`,
        silent: true,
      });
      authNotices.get(account.id)?.close();
      authNotices.set(account.id, notice);
      notice.on('click', () => {
        windows.showPopup('accounts', true);
        const current = controllerRef;
        const loginState = current?.snapshot().accounts.find((entry) => entry.id === account.id)?.loginState;
        if (loginState !== 'logged-out' || !PROVIDER_TRAITS[account.provider].widgetLogin) return;
        try {
          current?.startLogin(account.id);
        } catch (error) {
          logger.warn('auth-required login start failed', { provider: account.provider, error });
        }
      });
      notice.show();
    },
  });
  controllerRef = controller;
  controller.setEffectivePlacementMode(initialMode);
  const unsubscribeTheme = theme.onChange((tokens) => controller.onThemeChanged(tokens));

  const handlers = createInvokeHandlers(controller);
  const unregisterIpc = registerInvokeHandlers(ipcMain, handlers, {
    isTrustedSender: (url) => isTrustedRendererUrl(url, devServerUrl),
    logger: logger.child('ipc'),
  });

  const onTrayAction = (action: TrayAction, checked: boolean): void => {
    switch (action) {
      case 'toggle-widget':
        windows.toggleWidget();
        break;
      case 'open-popup':
        windows.showPopup(null, true);
        break;
      case 'toggle-autostart':
        controller.updateSettings({ openAtLogin: checked }).catch((error: unknown) => {
          logger.warn('autostart toggle failed', { error });
          tray?.update(trayStateOf(controller.snapshot(), autostart.supported));
        });
        break;
      case 'refresh-now':
        controller.refreshNow(null).catch((error: unknown) => logger.warn('tray refresh failed', { error }));
        break;
      case 'accounts':
        windows.showPopup('accounts', true);
        break;
      case 'quit':
        app.quit();
        break;
    }
  };
  tray = new AppTray(resourcesDir, { onClick: () => windows.togglePopup(), onAction: onTrayAction }, logger.child('tray'));

  const onSuspend = (): void => controller.suspend();
  const onResume = (): void => {
    controller.resume();
    windows.reposition();
  };
  const onBattery = (): void => controller.setOnBattery(true);
  const onAc = (): void => controller.setOnBattery(false);
  powerMonitor.on('suspend', onSuspend);
  powerMonitor.on('resume', onResume);
  powerMonitor.on('on-battery', onBattery);
  powerMonitor.on('on-ac', onAc);
  controller.setOnBattery(powerMonitor.isOnBatteryPower());

  let displayTimer: ReturnType<typeof setTimeout> | undefined;
  const onDisplayChange = (): void => {
    clearTimeout(displayTimer);
    displayTimer = setTimeout(() => windows.reposition(), DISPLAY_DEBOUNCE_MS);
  };
  screen.on('display-added', onDisplayChange);
  screen.on('display-removed', onDisplayChange);
  screen.on('display-metrics-changed', onDisplayChange);

  let shutdownPromise: Promise<void> | null = null;
  const shutdown = (): Promise<void> => {
    shutdownPromise ??= (async () => {
      clearTimeout(displayTimer);
      screen.removeListener('display-added', onDisplayChange);
      screen.removeListener('display-removed', onDisplayChange);
      screen.removeListener('display-metrics-changed', onDisplayChange);
      powerMonitor.removeListener('suspend', onSuspend);
      powerMonitor.removeListener('resume', onResume);
      powerMonitor.removeListener('on-battery', onBattery);
      powerMonitor.removeListener('on-ac', onAc);
      controller.stop();
      for (const notice of authNotices.values()) notice.close();
      authNotices.clear();
      unsubscribeTheme();
      theme.dispose();
      unregisterIpc();
      tray?.destroy();
      windows.destroy();
      await Promise.race([store.flush(), new Promise((resolve) => setTimeout(resolve, SHUTDOWN_FLUSH_LIMIT_MS))]);
    })();
    return shutdownPromise;
  };
  runtime = { controller, shutdown };

  await windows.create();
  tray.create(trayStateOf(controller.snapshot(), autostart.supported));
  const starting = controller.start().catch((error: unknown) => logger.error('controller start failed', { error }));

  if (tracker === null) {
    windows.showWidget();
    if (!args.hidden && store.getAccounts().length === 0) windows.showPopup('accounts', true);
    if (pendingReveal) controller.revealFromSecondInstance();
    pendingReveal = false;
    return;
  }

  await starting;
  await tracker.waitForAll(args.smokeTimeoutMs);
  const windowInfo = windows.smokeInfo();
  tracker.setCheck(
    'windows',
    windowInfo,
    windowInfo.widgetInsideDisplay && windowInfo.popup.size.width === 380 && windowInfo.popup.size.height === 440,
  );
  if (devServerUrl === undefined) {
    try {
      const response = await net.fetch(rendererEntryUrl('widget', undefined));
      const header = response.headers.get('content-security-policy');
      tracker.setCheck(
        'cspHeader',
        { status: response.status, matchesProductionPolicy: header === PROD_CSP },
        response.ok && header === PROD_CSP,
      );
    } catch (error) {
      logger.error('csp probe failed', { error });
      tracker.setCheck('cspHeader', { error: 'fetch failed' }, false);
    }
  } else {
    tracker.setCheck('cspHeader', { devServer: true }, null);
  }
  const handled = handlers as unknown as Record<string, unknown>;
  const missing = INVOKE_CHANNELS.filter((channel) => typeof handled[channel] !== 'function');
  tracker.setCheck('ipc', { channels: INVOKE_CHANNELS.length, handled: INVOKE_CHANNELS.length - missing.length, missing }, missing.length === 0);
  const snapshot = controller.snapshot();
  tracker.setCheck('theme', snapshot.theme, null);
  tracker.setCheck(
    'koffi',
    {
      ...native.status,
      taskbar:
        windowInfo.taskbar === null
          ? null
          : { edge: windowInfo.taskbar.edge, autoHide: windowInfo.taskbar.autoHide, source: windowInfo.taskbar.source },
      effectiveMode: windowInfo.effectiveMode,
    },
    null,
  );
  tracker.setCheck('adapters', controller.cliSummary(), null);
  tracker.setCheck('store', { ...store.info, accounts: store.getAccounts().length }, null);
  tracker.setCheck('scheduler', snapshot.refresh, null);
  tracker.setCheck('tray', { created: tray.created }, tray.created);
  tracker.setCheck('autostart', { supported: autostart.supported }, !autostart.supported);

  const report = tracker.report(
    Date.now(),
    registry.list().map((adapter) => adapter.id),
  );
  writeSmokeReport(args.smokeOut, JSON.stringify(report, null, 2));
  await shutdown();
  app.exit(report.ok ? 0 : 1);
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

  // A second launch reveals the running instance instead of silently exiting (V1-32).
  app.on('second-instance', () => {
    if (runtime !== null) runtime.controller.revealFromSecondInstance();
    else pendingReveal = true;
  });

  hardenApp((url) => isTrustedRendererUrl(url, devServerUrl), logger.child('security'));
  // Tray app: closing or recreating windows must not quit.
  app.on('window-all-closed', () => undefined);

  let quitting = false;
  app.on('before-quit', (event) => {
    if (quitting || runtime === null) return;
    quitting = true;
    event.preventDefault();
    runtime
      .shutdown()
      .catch((error: unknown) => logger.error('shutdown failed', { error }))
      .finally(() => app.quit());
  });

  app
    .whenReady()
    .then(() => start(args, isolated, devServerUrl, logger))
    .catch((error: unknown) => {
      logger.error('startup failed', error);
      app.exit(1);
    });
}

main();

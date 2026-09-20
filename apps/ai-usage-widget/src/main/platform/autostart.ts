import type { Logger } from '../log';

/** Registry value name under HKCU\...\Run. Must differ from v1's 'electron.app.AI Usage Widget'. */
export const AUTOSTART_NAME = 'AIUsageWidgetV2';
export const AUTOSTART_ARGS: readonly string[] = ['--autostart'];

export interface LoginItemApi {
  setLoginItemSettings(settings: { openAtLogin: boolean; path: string; args: string[]; name: string; enabled?: boolean }): void;
  getLoginItemSettings(options: { path: string; args: string[] }): {
    openAtLogin: boolean;
    launchItems?: { name: string; enabled: boolean }[];
  };
}

/**
 * - enabled / disabled: a Run entry for THIS executable exists (disabled = switched off in Task Manager).
 * - absent: no entry starts this executable. Electron only reports entries whose path matches the
 *   one asked about, so an entry left behind by another copy (dev build, old install folder) also
 *   reads as absent.
 */
export type AutostartEntryState = 'enabled' | 'disabled' | 'absent';

export interface Autostart {
  /** False in development and smoke runs: nothing is registered. */
  readonly supported: boolean;
  /** Current registration (same path + args as when writing, V1-31); null when unsupported or unreadable. */
  isEnabled(): boolean | null;
  /** Like isEnabled, but tells "switched off" from "no entry for this executable"; null when unsupported or unreadable. */
  entryState(): AutostartEntryState | null;
  /** Throws when the registration fails. No-op when unsupported. Overwrites a same-named entry of another executable. */
  setEnabled(enabled: boolean): void;
}

export interface AutostartOptions {
  api: LoginItemApi;
  execPath: string;
  supported: boolean;
  logger: Logger;
}

export function createAutostart(options: AutostartOptions): Autostart {
  const args = [...AUTOSTART_ARGS];
  const entryState = (): AutostartEntryState | null => {
    if (!options.supported) return null;
    try {
      const current = options.api.getLoginItemSettings({ path: options.execPath, args });
      const item = current.launchItems?.find((entry) => entry.name === AUTOSTART_NAME);
      if (item !== undefined) return item.enabled ? 'enabled' : 'disabled';
      return current.openAtLogin ? 'enabled' : 'absent';
    } catch (error) {
      options.logger.warn('getLoginItemSettings failed', { error });
      return null;
    }
  };
  return {
    supported: options.supported,
    entryState,
    isEnabled() {
      const state = entryState();
      return state === null ? null : state === 'enabled';
    },
    setEnabled(enabled) {
      if (!options.supported) {
        options.logger.info('autostart not registered (development or smoke run)', { enabled });
        return;
      }
      options.api.setLoginItemSettings({
        openAtLogin: enabled,
        path: options.execPath,
        args,
        name: AUTOSTART_NAME,
        enabled,
      });
    },
  };
}

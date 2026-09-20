import { createTranslator } from '../../shared/i18n';
import type { Locale } from '../../shared/types';

export type TrayAction = 'toggle-widget' | 'open-popup' | 'toggle-autostart' | 'refresh-now' | 'accounts' | 'quit';

export type TrayItem =
  | { type: 'separator' }
  | { type: 'normal'; action: TrayAction; label: string; enabled: boolean }
  | { type: 'checkbox'; action: TrayAction; label: string; checked: boolean; enabled: boolean };

export interface TrayMenuState {
  locale: Locale;
  autostartChecked: boolean;
  /** Registration is impossible in dev/smoke runs. */
  autostartSupported: boolean;
  refreshing: boolean;
}

/** SPEC §4-6 menu without the Google/mock entries; labels come from the shared dictionary. */
export function buildTrayItems(state: TrayMenuState): TrayItem[] {
  const t = createTranslator(state.locale);
  return [
    { type: 'normal', action: 'toggle-widget', label: t('trayToggleWidget'), enabled: true },
    { type: 'normal', action: 'open-popup', label: t('trayOpenPopup'), enabled: true },
    { type: 'separator' },
    {
      type: 'checkbox',
      action: 'toggle-autostart',
      label: t('trayAutoLaunch'),
      checked: state.autostartChecked,
      enabled: state.autostartSupported,
    },
    { type: 'normal', action: 'refresh-now', label: t('trayRefreshNow'), enabled: !state.refreshing },
    { type: 'normal', action: 'accounts', label: t('trayAccounts'), enabled: true },
    { type: 'separator' },
    { type: 'normal', action: 'quit', label: t('trayQuit'), enabled: true },
  ];
}

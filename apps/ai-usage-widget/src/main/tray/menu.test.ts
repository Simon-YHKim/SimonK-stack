import { describe, expect, it } from 'vitest';
import { en } from '../../shared/i18n/en';
import { ko } from '../../shared/i18n/ko';
import { buildTrayItems } from './menu';

describe('buildTrayItems', () => {
  it('lists the v1 menu without Google/mock entries, localized', () => {
    const items = buildTrayItems({ locale: 'ko', autostartChecked: true, autostartSupported: true, refreshing: false });
    expect(items.map((item) => (item.type === 'separator' ? '-' : item.action))).toEqual([
      'toggle-widget',
      'open-popup',
      '-',
      'toggle-autostart',
      'refresh-now',
      'accounts',
      '-',
      'quit',
    ]);
    expect(items[0]).toMatchObject({ label: ko.trayToggleWidget });
    expect(items[3]).toMatchObject({ type: 'checkbox', checked: true, enabled: true, label: ko.trayAutoLaunch });
    const english = buildTrayItems({ locale: 'en', autostartChecked: false, autostartSupported: true, refreshing: false });
    expect(english[7]).toMatchObject({ label: en.trayQuit });
  });

  it('disables autostart when unsupported and refresh while refreshing', () => {
    const items = buildTrayItems({ locale: 'en', autostartChecked: false, autostartSupported: false, refreshing: true });
    expect(items[3]).toMatchObject({ enabled: false });
    expect(items[4]).toMatchObject({ action: 'refresh-now', enabled: false });
  });
});

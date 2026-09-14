import path from 'node:path';
import { Menu, Tray, nativeImage, type MenuItemConstructorOptions, type NativeImage } from 'electron';
import { createTranslator } from '../../shared/i18n';
import type { Logger } from '../log';
import { buildTrayItems, type TrayAction, type TrayItem, type TrayMenuState } from './menu';

export interface TrayHandlers {
  onAction(action: TrayAction, checked: boolean): void;
  /** Left click toggles the popup. */
  onClick(): void;
}

function loadIcon(resourcesDir: string, logger: Logger): NativeImage {
  for (const name of ['tray-icon.ico', 'tray-icon.png']) {
    const image = nativeImage.createFromPath(path.join(resourcesDir, name));
    if (!image.isEmpty()) return image;
  }
  logger.warn('tray icon not found; using an empty image');
  return nativeImage.createEmpty();
}

export class AppTray {
  private tray: Tray | null = null;
  private lastKey = '';

  constructor(
    private readonly resourcesDir: string,
    private readonly handlers: TrayHandlers,
    private readonly logger: Logger,
  ) {}

  get created(): boolean {
    return this.tray !== null && !this.tray.isDestroyed();
  }

  create(state: TrayMenuState): void {
    if (this.created) return;
    const tray = new Tray(loadIcon(this.resourcesDir, this.logger));
    tray.on('click', () => this.handlers.onClick());
    this.tray = tray;
    this.update(state);
  }

  update(state: TrayMenuState): void {
    const tray = this.tray;
    if (tray === null || tray.isDestroyed()) return;
    const key = JSON.stringify(state);
    if (key === this.lastKey) return;
    this.lastKey = key;
    tray.setToolTip(createTranslator(state.locale)('trayTooltip'));
    tray.setContextMenu(Menu.buildFromTemplate(buildTrayItems(state).map((item) => this.toTemplate(item))));
  }

  private toTemplate(item: TrayItem): MenuItemConstructorOptions {
    if (item.type === 'separator') return { type: 'separator' };
    if (item.type === 'checkbox') {
      return {
        type: 'checkbox',
        label: item.label,
        checked: item.checked,
        enabled: item.enabled,
        click: (menuItem) => this.handlers.onAction(item.action, menuItem.checked),
      };
    }
    return { type: 'normal', label: item.label, enabled: item.enabled, click: () => this.handlers.onAction(item.action, false) };
  }

  destroy(): void {
    if (this.tray !== null && !this.tray.isDestroyed()) this.tray.destroy();
    this.tray = null;
  }
}

import {
  LANGUAGE_KEYS,
  MATERIAL_KEYS,
  REFRESH_INTERVAL_KEYS,
  THEME_KEYS,
  type MessageKey,
  type Translator,
} from '../../../shared/i18n';
import {
  ALIGNMENTS,
  ALPHA_PERCENT_RANGE,
  ICON_STYLES,
  LANGUAGES,
  MATERIALS,
  OFFSET_PX_RANGE,
  PLACEMENT_MODES,
  REFRESH_INTERVALS_SEC,
  THEME_IDS,
  VERTICAL_OFFSET_PX_RANGE,
  isValidSettingValue,
  type Settings,
} from '../../../shared/settings';
import { ipcErrorCode, describeError, type Api } from '../api';
import { h, setAttr, setText, uniqueId } from '../dom';
import type { RenderContext } from '../model';

export interface SettingsTabDeps {
  api: Api;
  translator: () => Translator;
  report: (message: string) => void;
  setLock: (locked: boolean) => void;
}

type BooleanKey = {
  [K in keyof Settings]: Settings[K] extends boolean ? K : never;
}[keyof Settings];
type NumberKey = 'offsetPx' | 'verticalOffsetPx' | 'alphaPercent';

type Updater = (settings: Settings, ctx: RenderContext) => void;

/** Commit delay for keyboard-driven range changes (one save per burst, V1-12). */
export const RANGE_COMMIT_DELAY_MS = 250;

export class SettingsTab {
  readonly el: HTMLElement;
  private readonly updaters: Updater[] = [];
  private settings: Settings | null = null;
  private ctx: RenderContext | null = null;

  constructor(private readonly deps: SettingsTabDeps) {
    this.el = h('div', { class: 'settings-tab' });

    this.addChoice('theme', THEME_IDS, (v) => THEME_KEYS[v], 'widgetTheme', 'theme-grid');
    this.addChoice('material', MATERIALS, (v) => MATERIAL_KEYS[v], 'materialLabel', undefined, 'materialHint');
    this.addChoice('iconStyle', ICON_STYLES, (v) => (v === 'color' ? 'iconColor' : 'iconMono'), 'iconStyleLabel');
    this.addSwitch('showUsedPercent', 'showUsedPercentLabel');
    this.addSwitch('showWeeklyLimit', 'showWeeklyLimitLabel');
    this.addSwitch('colorByUsage', 'colorByUsageLabel');
    this.addSwitch('showCardBackground', 'showCardBg');
    this.addRange('alphaPercent', ALPHA_PERCENT_RANGE, 'alphaLabel', (n) => `${n}%`);
    this.addChoice('placementMode', PLACEMENT_MODES, (v) => (v === 'docked' ? 'placementDocked' : 'placementFloating'), 'placementLabel');
    this.addSwitch('alwaysOnTop', 'alwaysOnTopLabel', 'alwaysOnTopDesc', (s) => s.placementMode === 'floating');
    this.addChoice('alignment', ALIGNMENTS, (v, s) => {
      const floating = s.placementMode === 'floating';
      if (v === 'right') return floating ? 'alignRightFloating' : 'alignRightDocked';
      return floating ? 'alignLeftFloating' : 'alignLeftDocked';
    }, 'alignmentLabel');
    this.addRange('offsetPx', OFFSET_PX_RANGE, 'offsetLabel', (n, t) => t('pixels', { n }));
    this.addRange('verticalOffsetPx', VERTICAL_OFFSET_PX_RANGE, 'verticalOffsetLabel', (n, t) => t('pixels', { n }));
    this.addSelect('refreshIntervalSec', REFRESH_INTERVALS_SEC, (v) => REFRESH_INTERVAL_KEYS[v], 'refreshIntervalLabel');
    this.addSelect('language', LANGUAGES, (v) => LANGUAGE_KEYS[v], 'languageLabel');
    this.addSwitch('openAtLogin', 'launchAtLogin');
  }

  update(settings: Settings, ctx: RenderContext): void {
    this.settings = settings;
    this.ctx = ctx;
    for (const run of this.updaters) run(settings, ctx);
  }

  private revert(): void {
    if (this.settings !== null && this.ctx !== null) this.update(this.settings, this.ctx);
  }

  commit(patch: Partial<Settings>): void {
    void this.deps.api.invoke('settings:update', { patch }).then(
      (result) => {
        if (!result.ok) {
          this.deps.report(describeError(this.deps.translator(), ipcErrorCode(result.error)));
          this.revert();
        }
      },
      () => this.revert(),
    );
  }

  private group(labelKey: MessageKey, children: HTMLElement[], hintKey?: MessageKey): { el: HTMLElement; label: HTMLElement; hint: HTMLElement | null } {
    const labelId = uniqueId('setting');
    const label = h('div', { class: 'form-label', id: labelId });
    const hint = hintKey === undefined ? null : h('p', { class: 'form-hint' });
    const el = h('div', { class: 'form-group', role: 'group', 'aria-labelledby': labelId }, [label, ...children, hint]);
    this.el.append(el);
    this.updaters.push((_s, ctx) => {
      setText(label, ctx.t(labelKey));
      if (hint !== null && hintKey !== undefined) setText(hint, ctx.t(hintKey));
    });
    return { el, label, hint };
  }

  private addChoice<K extends 'theme' | 'material' | 'iconStyle' | 'placementMode' | 'alignment'>(
    key: K,
    values: readonly Settings[K][],
    labelOf: (value: Settings[K], settings: Settings) => MessageKey,
    labelKey: MessageKey,
    extraClass?: string,
    hintKey?: MessageKey,
  ): void {
    const buttons = values.map((value) => {
      const button = h('button', { type: 'button', class: 'choice-button', 'data-value': String(value), 'aria-pressed': 'false' });
      button.addEventListener('click', () => {
        if (this.settings?.[key] === value) return;
        const patch: Partial<Settings> = {};
        (patch as Record<string, unknown>)[key] = value;
        this.commit(patch);
      });
      return button;
    });
    const row = h('div', { class: `form-row${extraClass === undefined ? '' : ` ${extraClass}`}` }, buttons);
    this.group(labelKey, [row], hintKey);
    this.updaters.push((settings, ctx) => {
      values.forEach((value, index) => {
        const button = buttons[index];
        if (button === undefined) return;
        setText(button, ctx.t(labelOf(value, settings)));
        const active = settings[key] === value;
        button.classList.toggle('active', active);
        setAttr(button, 'aria-pressed', String(active));
      });
    });
  }

  private addSwitch(key: BooleanKey, labelKey: MessageKey, descKey?: MessageKey, visible?: (s: Settings) => boolean): void {
    const inputId = uniqueId(`switch-${key}`);
    const input = h('input', { type: 'checkbox', role: 'switch', id: inputId, class: 'switch-input', 'data-setting': key });
    const text = h('span', { class: 'switch-text' });
    const desc = descKey === undefined ? null : h('span', { class: 'switch-desc' });
    const label = h('label', { class: 'switch-container', for: inputId }, [
      h('span', { class: 'switch-label' }, [text, desc]),
      input,
      h('span', { class: 'switch-track', 'aria-hidden': 'true' }, [h('span', { class: 'switch-thumb' })]),
    ]);
    const wrap = h('div', { class: 'form-group switch-group' }, [label]);
    this.el.append(wrap);
    input.addEventListener('change', () => {
      const patch: Partial<Settings> = {};
      (patch as Record<string, unknown>)[key] = input.checked;
      this.commit(patch);
    });
    this.updaters.push((settings, ctx) => {
      setText(text, ctx.t(labelKey));
      if (desc !== null && descKey !== undefined) setText(desc, ctx.t(descKey));
      input.checked = settings[key];
      wrap.hidden = visible !== undefined && !visible(settings);
    });
  }

  private addRange(
    key: NumberKey,
    range: { min: number; max: number },
    labelKey: MessageKey,
    format: (n: number, t: Translator) => string,
  ): void {
    const input = h('input', { type: 'range', class: 'range-slider', min: range.min, max: range.max, step: 1, 'data-setting': key });
    const value = h('span', { class: 'range-value', 'aria-hidden': 'true' });
    const { label } = this.group(labelKey, [h('div', { class: 'range-row' }, [input, value])]);
    setAttr(input, 'aria-labelledby', label.id);
    let dragging = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    const preview = (): void => {
      const n = Number(input.value);
      const text = format(n, this.deps.translator());
      setText(value, text);
      setAttr(input, 'aria-valuetext', text);
    };
    const flush = (): void => {
      if (timer !== null) clearTimeout(timer);
      timer = null;
      const n = Number(input.value);
      if (this.settings === null || this.settings[key] === n || !isValidSettingValue(key, n)) return;
      const patch: Partial<Settings> = {};
      patch[key] = n;
      this.commit(patch);
    };
    const release = (): void => {
      if (!dragging) return;
      dragging = false;
      this.deps.setLock(false);
      flush();
    };

    input.addEventListener('pointerdown', () => {
      dragging = true;
      this.deps.setLock(true);
    });
    input.addEventListener('pointerup', release);
    input.addEventListener('blur', () => {
      release();
      flush();
    });
    // input: label preview only; change: one save after the gesture settles.
    input.addEventListener('input', preview);
    input.addEventListener('change', () => {
      if (dragging) return;
      if (timer !== null) clearTimeout(timer);
      timer = setTimeout(flush, RANGE_COMMIT_DELAY_MS);
    });

    this.updaters.push((settings) => {
      if (dragging || timer !== null) return;
      input.value = String(settings[key]);
      preview();
    });
  }

  private addSelect<K extends 'refreshIntervalSec' | 'language'>(
    key: K,
    values: readonly Settings[K][],
    labelOf: (value: Settings[K]) => MessageKey,
    labelKey: MessageKey,
  ): void {
    const select = h('select', { class: 'select-input', 'data-setting': key });
    const options = values.map((value) => h('option', { value: String(value) }));
    select.append(...options);
    const { label } = this.group(labelKey, [select]);
    setAttr(select, 'aria-labelledby', label.id);
    select.addEventListener('pointerdown', () => this.deps.setLock(true));
    select.addEventListener('blur', () => this.deps.setLock(false));
    select.addEventListener('change', () => {
      this.deps.setLock(false);
      const raw = select.value;
      const value = values.find((v) => String(v) === raw);
      if (value === undefined || this.settings?.[key] === value) return;
      const patch: Partial<Settings> = {};
      (patch as Record<string, unknown>)[key] = value;
      this.commit(patch);
    });
    this.updaters.push((settings, ctx) => {
      values.forEach((value, index) => {
        const option = options[index];
        if (option !== undefined) setText(option, ctx.t(labelOf(value)));
      });
      select.value = String(settings[key]);
    });
  }
}

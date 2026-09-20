import { fail, isIntInRange, isOneOf, isPlainObject, ok, unknownKeys, type ParseResult } from './validate';

// v1 keys (SPEC §1-2) that still have meaning, plus v2 additions.
// Dropped from v1: every customMock/Mock API related value (SPEC §7).

export const THEME_IDS = ['windows', '1a', '1b', '1c', '1d'] as const;
export type ThemeId = (typeof THEME_IDS)[number];

export const ICON_STYLES = ['color', 'monochrome'] as const;
export type IconStyle = (typeof ICON_STYLES)[number];

export const ALIGNMENTS = ['right', 'left'] as const;
export type Alignment = (typeof ALIGNMENTS)[number];

export const PLACEMENT_MODES = ['docked', 'floating'] as const;
export type PlacementMode = (typeof PLACEMENT_MODES)[number];

export const MATERIALS = ['none', 'mica', 'acrylic'] as const;
export type Material = (typeof MATERIALS)[number];

export const LANGUAGES = ['auto', 'ko', 'en'] as const;
export type Language = (typeof LANGUAGES)[number];

export const REFRESH_INTERVALS_SEC = [15, 30, 60, 120, 300] as const;
export type RefreshIntervalSec = (typeof REFRESH_INTERVALS_SEC)[number];

export const OFFSET_PX_RANGE = { min: 0, max: 350 } as const;
/** v1 had no UI and no bound for this key (V1-38); v2 bounds it. */
export const VERTICAL_OFFSET_PX_RANGE = { min: -40, max: 40 } as const;
export const ALPHA_PERCENT_RANGE = { min: 10, max: 100 } as const;

export interface Settings {
  theme: ThemeId;
  iconStyle: IconStyle;
  alignment: Alignment;
  offsetPx: number;
  verticalOffsetPx: number;
  refreshIntervalSec: RefreshIntervalSec;
  /** Card background opacity in percent (v1 label called it "transparency", V1-35). */
  alphaPercent: number;
  showWeeklyLimit: boolean;
  colorByUsage: boolean;
  showCardBackground: boolean;
  showUsedPercent: boolean;
  placementMode: PlacementMode;
  alwaysOnTop: boolean;
  /** Default off: v1 enabled autostart without consent (V1-14). */
  openAtLogin: boolean;
  material: Material;
  language: Language;
}

export const SETTING_KEYS = [
  'theme',
  'iconStyle',
  'alignment',
  'offsetPx',
  'verticalOffsetPx',
  'refreshIntervalSec',
  'alphaPercent',
  'showWeeklyLimit',
  'colorByUsage',
  'showCardBackground',
  'showUsedPercent',
  'placementMode',
  'alwaysOnTop',
  'openAtLogin',
  'material',
  'language',
] as const satisfies readonly (keyof Settings)[];

export const DEFAULT_SETTINGS: Readonly<Settings> = Object.freeze({
  theme: 'windows',
  iconStyle: 'color',
  alignment: 'right',
  offsetPx: 20,
  verticalOffsetPx: 0,
  refreshIntervalSec: 60,
  alphaPercent: 85,
  showWeeklyLimit: true,
  colorByUsage: true,
  showCardBackground: true,
  showUsedPercent: false,
  placementMode: 'docked',
  alwaysOnTop: true,
  openAtLogin: false,
  material: 'none',
  language: 'auto',
});

const isBoolean = (value: unknown): value is boolean => typeof value === 'boolean';

const SETTING_GUARDS: { readonly [K in keyof Settings]: (value: unknown) => value is Settings[K] } = {
  theme: (v): v is ThemeId => isOneOf(THEME_IDS, v),
  iconStyle: (v): v is IconStyle => isOneOf(ICON_STYLES, v),
  alignment: (v): v is Alignment => isOneOf(ALIGNMENTS, v),
  offsetPx: (v): v is number => isIntInRange(v, OFFSET_PX_RANGE.min, OFFSET_PX_RANGE.max),
  verticalOffsetPx: (v): v is number =>
    isIntInRange(v, VERTICAL_OFFSET_PX_RANGE.min, VERTICAL_OFFSET_PX_RANGE.max),
  refreshIntervalSec: (v): v is RefreshIntervalSec => isOneOf(REFRESH_INTERVALS_SEC, v),
  alphaPercent: (v): v is number => isIntInRange(v, ALPHA_PERCENT_RANGE.min, ALPHA_PERCENT_RANGE.max),
  showWeeklyLimit: isBoolean,
  colorByUsage: isBoolean,
  showCardBackground: isBoolean,
  showUsedPercent: isBoolean,
  placementMode: (v): v is PlacementMode => isOneOf(PLACEMENT_MODES, v),
  alwaysOnTop: isBoolean,
  openAtLogin: isBoolean,
  material: (v): v is Material => isOneOf(MATERIALS, v),
  language: (v): v is Language => isOneOf(LANGUAGES, v),
};

export function isValidSettingValue<K extends keyof Settings>(key: K, value: unknown): value is Settings[K] {
  return SETTING_GUARDS[key](value);
}

/**
 * Validates a renderer-provided partial update. Unknown keys and invalid values
 * are rejected as a whole (no silent coercion, V1-20).
 */
export function parseSettingsPatch(input: unknown): ParseResult<Partial<Settings>> {
  if (!isPlainObject(input)) return fail('settings patch must be an object');
  const extra = unknownKeys(input, SETTING_KEYS);
  if (extra.length > 0) return fail(`unknown setting keys: ${extra.slice(0, 5).join(',')}`);
  const keys = Object.keys(input) as (keyof Settings)[];
  if (keys.length === 0) return fail('settings patch is empty');
  const patch: Partial<Record<keyof Settings, unknown>> = {};
  for (const key of keys) {
    const value = input[key];
    if (!isValidSettingValue(key, value)) return fail(`invalid value for ${key}`);
    patch[key] = value;
  }
  return ok(patch as Partial<Settings>);
}

/**
 * Normalizes persisted settings: starts from defaults, keeps only valid known
 * keys, ignores unknown/legacy keys. Never throws.
 */
export function normalizeSettings(raw: unknown): Settings {
  const result: Settings = { ...DEFAULT_SETTINGS };
  if (!isPlainObject(raw)) return result;
  const target = result as unknown as Record<keyof Settings, unknown>;
  for (const key of SETTING_KEYS) {
    const value = raw[key];
    if (isValidSettingValue(key, value)) target[key] = value;
  }
  return result;
}

export function applySettingsPatch(base: Settings, patch: Partial<Settings>): Settings {
  return { ...base, ...patch };
}

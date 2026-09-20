import { describe, expect, it } from 'vitest';
import {
  DEFAULT_SETTINGS,
  SETTING_KEYS,
  applySettingsPatch,
  isValidSettingValue,
  normalizeSettings,
  parseSettingsPatch,
} from './settings';

describe('settings', () => {
  it('defaults are valid for every key', () => {
    for (const key of SETTING_KEYS) {
      expect(isValidSettingValue(key, DEFAULT_SETTINGS[key]), key).toBe(true);
    }
    expect(Object.keys(DEFAULT_SETTINGS).sort()).toEqual([...SETTING_KEYS].sort());
  });

  it('defaults follow v2 decisions', () => {
    expect(DEFAULT_SETTINGS.theme).toBe('windows');
    expect(DEFAULT_SETTINGS.material).toBe('none');
    expect(DEFAULT_SETTINGS.language).toBe('auto');
    expect(DEFAULT_SETTINGS.openAtLogin).toBe(false);
    expect(DEFAULT_SETTINGS.refreshIntervalSec).toBe(60);
  });

  it('normalizeSettings drops unknown, legacy and invalid values', () => {
    const result = normalizeSettings({
      theme: '1b',
      refreshIntervalSec: Number.NaN,
      offsetPx: 999,
      customMock: { primaryPercent: 79 },
      alphaPercent: 50,
    });
    expect(result.theme).toBe('1b');
    expect(result.refreshIntervalSec).toBe(DEFAULT_SETTINGS.refreshIntervalSec);
    expect(result.offsetPx).toBe(DEFAULT_SETTINGS.offsetPx);
    expect(result.alphaPercent).toBe(50);
    expect(result).not.toHaveProperty('customMock');
  });

  it('normalizeSettings tolerates garbage', () => {
    expect(normalizeSettings(null)).toEqual(DEFAULT_SETTINGS);
    expect(normalizeSettings('x')).toEqual(DEFAULT_SETTINGS);
    expect(normalizeSettings([1, 2])).toEqual(DEFAULT_SETTINGS);
  });

  it('parseSettingsPatch accepts valid partial updates', () => {
    const parsed = parseSettingsPatch({ refreshIntervalSec: 120, material: 'mica' });
    expect(parsed).toEqual({ ok: true, value: { refreshIntervalSec: 120, material: 'mica' } });
  });

  it('parseSettingsPatch rejects NaN interval, unknown keys, empty and out-of-range values (V1-20)', () => {
    expect(parseSettingsPatch({ refreshIntervalSec: Number.NaN }).ok).toBe(false);
    expect(parseSettingsPatch({ refreshIntervalSec: 45 }).ok).toBe(false);
    expect(parseSettingsPatch({ customMock: {} }).ok).toBe(false);
    expect(parseSettingsPatch({}).ok).toBe(false);
    expect(parseSettingsPatch({ offsetPx: -1 }).ok).toBe(false);
    expect(parseSettingsPatch({ alphaPercent: 5 }).ok).toBe(false);
    expect(parseSettingsPatch({ theme: 'mock' }).ok).toBe(false);
    expect(parseSettingsPatch(null).ok).toBe(false);
  });

  it('applySettingsPatch merges without mutating the base', () => {
    const base = { ...DEFAULT_SETTINGS };
    const next = applySettingsPatch(base, { placementMode: 'floating' });
    expect(next.placementMode).toBe('floating');
    expect(next.showCardBackground).toBe(base.showCardBackground);
    expect(base.placementMode).toBe('docked');
  });
});

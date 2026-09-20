import { describe, expect, it } from 'vitest';
import {
  DICTIONARIES,
  ERROR_MESSAGE_KEYS,
  LANGUAGE_KEYS,
  LOGIN_STAGE_KEYS,
  LOGIN_STATE_KEYS,
  MATERIAL_KEYS,
  PROVIDER_NAME_KEYS,
  REFRESH_INTERVAL_KEYS,
  THEME_KEYS,
  USAGE_SOURCE_KEYS,
  USAGE_STATE_KEYS,
  placeholdersOf,
  resolveLocale,
  t,
} from './index';
import { en } from './en';
import { ko } from './ko';

describe('i18n dictionaries', () => {
  it('ko and en have identical key sets', () => {
    expect(Object.keys(en).sort()).toEqual(Object.keys(ko).sort());
  });

  it('ko and en use identical placeholders per key', () => {
    for (const key of Object.keys(ko) as (keyof typeof ko)[]) {
      expect(placeholdersOf(en[key]), key).toEqual(placeholdersOf(ko[key]));
    }
  });

  it('has no empty messages', () => {
    for (const dict of Object.values(DICTIONARIES)) {
      for (const [key, value] of Object.entries(dict)) expect(value.trim().length, key).toBeGreaterThan(0);
    }
  });

  it('contains no mock-era keys', () => {
    for (const legacy of ['addCustomAccountTitle', 'iconLetterLabel', 'brandColorLabel', 'addManually', 'resetDefaults', 'addGoogleOAuth']) {
      expect(ko).not.toHaveProperty(legacy);
    }
  });

  it('lookup tables point at existing keys', () => {
    const tables = [
      ERROR_MESSAGE_KEYS,
      USAGE_STATE_KEYS,
      LOGIN_STATE_KEYS,
      LOGIN_STAGE_KEYS,
      PROVIDER_NAME_KEYS,
      USAGE_SOURCE_KEYS,
      THEME_KEYS,
      MATERIAL_KEYS,
      LANGUAGE_KEYS,
      REFRESH_INTERVAL_KEYS,
    ];
    for (const table of tables) {
      for (const key of Object.values(table)) expect(ko, key).toHaveProperty(key);
    }
  });

  it('t() substitutes params and keeps unknown placeholders', () => {
    expect(t('en', 'accountsActive', { count: 2 })).toBe('Active accounts: 2');
    expect(t('ko', 'resetLabel', { time: '3h 07m' })).toBe('리셋까지 3h 07m');
    expect(t('en', 'resetLabel')).toBe('Resets in {time}');
  });

  it('resolveLocale', () => {
    expect(resolveLocale('auto', 'ko-KR')).toBe('ko');
    expect(resolveLocale('auto', 'en-US')).toBe('en');
    expect(resolveLocale('auto', 'ja')).toBe('en');
    expect(resolveLocale('ko', 'en-US')).toBe('ko');
    expect(resolveLocale('en', 'ko')).toBe('en');
  });
});

import { describe, expect, it } from 'vitest';
import { isId, isIntInRange, isPlainObject, normalizeLabel, parseNull, parseRecord } from './validate';

const RLO = String.fromCharCode(0x202e);
const RLM = String.fromCharCode(0x200f);

describe('validate', () => {
  it('recognizes plain objects only', () => {
    expect(isPlainObject({})).toBe(true);
    expect(isPlainObject(Object.create(null))).toBe(true);
    expect(isPlainObject([])).toBe(false);
    expect(isPlainObject(null)).toBe(false);
    expect(isPlainObject(new Date())).toBe(false);
  });

  it('parseRecord rejects unknown keys', () => {
    expect(parseRecord({ a: 1 }, ['a']).ok).toBe(true);
    expect(parseRecord({ a: 1, b: 2 }, ['a']).ok).toBe(false);
    expect(parseRecord('x', ['a']).ok).toBe(false);
  });

  it('parseNull accepts null/undefined only', () => {
    expect(parseNull(null)).toEqual({ ok: true, value: null });
    expect(parseNull(undefined)).toEqual({ ok: true, value: null });
    expect(parseNull({}).ok).toBe(false);
  });

  it('isIntInRange rejects NaN and fractions', () => {
    expect(isIntInRange(5, 0, 10)).toBe(true);
    expect(isIntInRange(Number.NaN, 0, 10)).toBe(false);
    expect(isIntInRange(1.5, 0, 10)).toBe(false);
    expect(isIntInRange(11, 0, 10)).toBe(false);
  });

  it('isId enforces the id pattern', () => {
    expect(isId('a1_B-2')).toBe(true);
    expect(isId('../x')).toBe(false);
    expect(isId('')).toBe(false);
    expect(isId('x'.repeat(65))).toBe(false);
  });

  it('normalizeLabel strips control and bidi characters and bounds length', () => {
    expect(normalizeLabel(`  Work${RLO}  account\t`)).toBe('Work account');
    expect(normalizeLabel(`${RLM} `)).toBeNull();
    expect(normalizeLabel('   ')).toBeNull();
    expect(normalizeLabel(42)).toBeNull();
    expect(normalizeLabel('가'.repeat(64))).toBe('가'.repeat(64));
    expect(normalizeLabel('가'.repeat(65))).toBeNull();
  });
});

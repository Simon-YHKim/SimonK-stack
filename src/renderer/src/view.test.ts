import { describe, expect, it } from 'vitest';
import { parseViewFromSearch } from './view';

describe('parseViewFromSearch', () => {
  it('accepts only known views', () => {
    expect(parseViewFromSearch('?view=popup')).toBe('popup');
    expect(parseViewFromSearch('?view=widget')).toBe('widget');
    expect(parseViewFromSearch('?view=admin')).toBe('widget');
    expect(parseViewFromSearch('')).toBe('widget');
  });
});

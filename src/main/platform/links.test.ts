import { describe, expect, it } from 'vitest';
import { EXTERNAL_LINK_KEYS } from '../../shared/ipc';
import { EXTERNAL_LINK_HOSTS, EXTERNAL_LINKS } from './links';

describe('EXTERNAL_LINKS', () => {
  it('has an install guide for every link key', () => {
    for (const key of EXTERNAL_LINK_KEYS) expect(EXTERNAL_LINKS[key], key).toBeTypeOf('string');
  });

  it('only holds https URLs on the provider-owned host, without credentials, query or fragment', () => {
    for (const key of EXTERNAL_LINK_KEYS) {
      const raw = EXTERNAL_LINKS[key];
      if (raw === undefined) continue;
      const url = new URL(raw);
      expect(url.protocol, key).toBe('https:');
      expect(EXTERNAL_LINK_HOSTS[key], key).toContain(url.hostname);
      expect(url.username + url.password + url.search + url.hash, key).toBe('');
      expect(url.port, key).toBe('');
    }
  });

  it('has no keys outside the contract', () => {
    expect(Object.keys(EXTERNAL_LINKS).sort()).toEqual([...EXTERNAL_LINK_KEYS].sort());
  });

  it('is frozen', () => {
    expect(Object.isFrozen(EXTERNAL_LINKS)).toBe(true);
  });
});

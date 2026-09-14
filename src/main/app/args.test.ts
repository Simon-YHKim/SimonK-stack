import { describe, expect, it } from 'vitest';
import { DEFAULT_SMOKE_TIMEOUT_MS, parseLaunchArgs } from './args';

describe('parseLaunchArgs', () => {
  it('defaults', () => {
    expect(parseLaunchArgs(['electron.exe', '.'])).toEqual({
      smoke: false,
      smokeOut: null,
      smokeTimeoutMs: DEFAULT_SMOKE_TIMEOUT_MS,
      hidden: false,
      autostart: false,
    });
  });

  it('parses smoke flags in both forms', () => {
    expect(parseLaunchArgs(['x', '--smoke', '--smoke-out=C:\\t\\r.json', '--smoke-timeout-ms=5000'])).toMatchObject({
      smoke: true,
      smokeOut: 'C:\\t\\r.json',
      smokeTimeoutMs: 5000,
    });
    expect(parseLaunchArgs(['x', '--smoke-out', 'out.json']).smokeOut).toBe('out.json');
    expect(parseLaunchArgs(['x', '--smoke-out', '--smoke']).smokeOut).toBeNull();
  });

  it('ignores out-of-range timeouts and separates --autostart from --hidden', () => {
    expect(parseLaunchArgs(['x', '--smoke-timeout-ms=10']).smokeTimeoutMs).toBe(DEFAULT_SMOKE_TIMEOUT_MS);
    expect(parseLaunchArgs(['x', '--autostart'])).toMatchObject({ hidden: true, autostart: true });
    expect(parseLaunchArgs(['x', '--hidden'])).toMatchObject({ hidden: true, autostart: false });
  });
});

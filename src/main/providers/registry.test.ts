import path from 'node:path';
import { describe, expect, it } from 'vitest';
import type { Account } from '../../shared/types';
import { nullLogger } from '../log';
import { createPlaceholderAdapter } from './placeholder';
import { DEFAULT_PROVIDER_FACTORIES, createProviderRegistry } from './registry';
import type { ProviderDeps } from './types';

const root = path.resolve('/tmp/aiuw-registry');
const deps: ProviderDeps = {
  logger: nullLogger,
  now: () => 1,
  appVersion: '0.0.0-test',
  localDataRoot: root,
  profilesRoot: path.join(root, 'profiles'),
  bridgeRoot: path.join(root, 'bridge'),
  resourcesDir: path.join(root, 'resources'),
  homeDir: path.join(root, 'home'),
  env: {},
};

const account: Account = {
  id: 'acc1',
  provider: 'codex',
  label: 'Test',
  enabled: true,
  order: 0,
  profileDir: path.join(root, 'profiles', 'codex', 'acc1'),
  createdAt: 1,
};

describe('provider registry', () => {
  it('registers all three providers with matching ids', () => {
    const registry = createProviderRegistry(deps);
    expect(registry.list().map((adapter) => adapter.id)).toEqual(['claude', 'codex', 'grok']);
    expect(registry.get('grok').id).toBe('grok');
    expect(registry.claude.id).toBe('claude');
  });

  it('rejects an adapter registered under the wrong id', () => {
    expect(() =>
      createProviderRegistry(deps, { ...DEFAULT_PROVIDER_FACTORIES, codex: () => createPlaceholderAdapter('grok', 'grok-acp') }),
    ).toThrow();
  });

  it('placeholders report not-implemented without fabricated values', async () => {
    const registry = createProviderRegistry(deps);
    const snapshot = await registry.get('codex').fetchUsage(account, new AbortController().signal);
    expect(snapshot).toMatchObject({ state: 'unavailable', errorCode: 'not-implemented', windows: [], measuredAt: null });
    const events: unknown[] = [];
    await registry.get('codex').startLogin(account, (event) => events.push(event), new AbortController().signal);
    expect(events).toEqual([{ type: 'error', code: 'not-implemented' }]);
  });
});

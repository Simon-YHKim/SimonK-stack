// Scaffold-only adapter used until a provider module lands. It reports
// 'not-implemented' and never fabricates usage values.

import type { Account, ProviderId, UsageSnapshot, UsageSource } from '../../shared/types';
import { createEmptySnapshot } from '../../shared/usage';
import type { CliInfo, ProviderAdapter, ProviderIdentity } from './types';

export function createPlaceholderAdapter(id: ProviderId, source: UsageSource): ProviderAdapter {
  return {
    id,
    loginUrlHosts: [],
    detectCli: (): Promise<CliInfo> => Promise.resolve({ found: false, errorCode: 'not-implemented' }),
    ensureProfileDir: (): Promise<void> => Promise.resolve(),
    startLogin: (_account, emit): Promise<void> => {
      emit({ type: 'error', code: 'not-implemented' });
      return Promise.resolve();
    },
    getIdentity: (): Promise<ProviderIdentity> => Promise.resolve({ loggedIn: false }),
    fetchUsage: (account: Account): Promise<UsageSnapshot> =>
      Promise.resolve(
        createEmptySnapshot({
          accountId: account.id,
          provider: id,
          source,
          state: 'unavailable',
          errorCode: 'not-implemented',
        }),
      ),
    removeProfile: (): Promise<void> => Promise.resolve(),
  };
}

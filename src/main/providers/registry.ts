import { PROVIDER_IDS, type ProviderId } from '../../shared/types';
import { createClaudeAdapter } from './claude';
import { createCodexAdapter } from './codex';
import { createGrokAdapter } from './grok';
import type { ClaudeProviderAdapter, ProviderAdapter, ProviderDeps, ProviderFactory } from './types';

export interface ProviderFactories {
  claude: ProviderFactory<ClaudeProviderAdapter>;
  codex: ProviderFactory;
  grok: ProviderFactory;
}

export const DEFAULT_PROVIDER_FACTORIES: ProviderFactories = {
  claude: createClaudeAdapter,
  codex: createCodexAdapter,
  grok: createGrokAdapter,
};

export interface ProviderRegistry {
  get(id: ProviderId): ProviderAdapter;
  list(): ProviderAdapter[];
  readonly claude: ClaudeProviderAdapter;
}

export function createProviderRegistry(
  deps: ProviderDeps,
  factories: ProviderFactories = DEFAULT_PROVIDER_FACTORIES,
): ProviderRegistry {
  const claude = factories.claude({ ...deps, logger: deps.logger.child('claude') });
  const adapters: Record<ProviderId, ProviderAdapter> = {
    claude,
    codex: factories.codex({ ...deps, logger: deps.logger.child('codex') }),
    grok: factories.grok({ ...deps, logger: deps.logger.child('grok') }),
  };
  for (const id of PROVIDER_IDS) {
    if (adapters[id].id !== id) throw new Error(`adapter registered as ${id} reports id ${adapters[id].id}`);
  }
  return {
    get: (id) => adapters[id],
    list: () => PROVIDER_IDS.map((id) => adapters[id]),
    claude,
  };
}

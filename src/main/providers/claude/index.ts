// Placeholder owned by the `claude` module; replace with the real adapter.
import { createPlaceholderAdapter } from '../placeholder';
import type { ClaudeProviderAdapter, ProviderDeps } from '../types';

export function createClaudeAdapter(_deps: ProviderDeps): ClaudeProviderAdapter {
  const base = createPlaceholderAdapter('claude', 'claude-statusline');
  return {
    ...base,
    id: 'claude',
    bridge: {
      status: () =>
        Promise.resolve({
          installed: false,
          wrapsExistingCommand: false,
          targetAccountId: null,
          lastDataAt: null,
          errorCode: 'not-implemented',
        }),
      installDefault: () => Promise.reject(new Error('not implemented')),
      uninstallDefault: () => Promise.reject(new Error('not implemented')),
    },
  };
}

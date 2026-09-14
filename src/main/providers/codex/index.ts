// Placeholder owned by the `codex` module; replace with the real adapter.
import { createPlaceholderAdapter } from '../placeholder';
import type { ProviderAdapter, ProviderDeps } from '../types';

export function createCodexAdapter(_deps: ProviderDeps): ProviderAdapter {
  return createPlaceholderAdapter('codex', 'codex-app-server');
}

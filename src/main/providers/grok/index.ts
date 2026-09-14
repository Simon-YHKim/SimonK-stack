// Placeholder owned by the `grok` module; replace with the real adapter.
import { createPlaceholderAdapter } from '../placeholder';
import type { ProviderAdapter, ProviderDeps } from '../types';

export function createGrokAdapter(_deps: ProviderDeps): ProviderAdapter {
  return createPlaceholderAdapter('grok', 'grok-acp');
}

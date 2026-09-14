import type { Settings } from '../../shared/settings';
import type { AppStateSnapshot, Locale, ThemeTokens } from '../../shared/types';

export interface InitialSnapshotInput {
  settings: Settings;
  locale: Locale;
  theme: ThemeTokens;
}

/** Snapshot before any account is loaded: nothing measured, CLI presence unknown. */
export function createInitialSnapshot(input: InitialSnapshotInput): AppStateSnapshot {
  return {
    locale: input.locale,
    settings: input.settings,
    accounts: [],
    usage: [],
    refresh: { inFlight: false, accountIds: [], lastRunAt: null, nextRunAt: null },
    theme: input.theme,
    cli: { claude: { state: 'unknown' }, codex: { state: 'unknown' }, grok: { state: 'unknown' } },
    effectivePlacementMode: null,
  };
}

/**
 * consent-gate — platform-branched consent gate for web + React Native.
 *
 * Hard rules (do NOT weaken):
 *   1. Consent gate: non-necessary trackers must NOT load until canTrack() passes.
 *   2. Fail-closed: if state is missing/unreadable, every non-necessary category is denied.
 *      'necessary' is the ONLY fail-open category.
 *   3. Audit log: every grant/change/withdraw is appended to the server ledger.
 *   4. Platform branch: web uses cookie/localStorage + Sec-GPC; RN uses AsyncStorage
 *      and has no GPC — expose explicit toggles instead.
 *
 * No secrets in this file. Tracker IDs come from env (EXPO_PUBLIC_* / process.env).
 */

export type ConsentCategory =
  | 'necessary'
  | 'functional'
  | 'analytics'
  | 'advertising';

export type ConsentSource =
  | 'banner'
  | 'settings'
  | 'gpc'
  | 'dnt'
  | 'guardian'
  | 'default';

export type Region = 'EU' | 'KR' | 'US' | 'OTHER' | 'UNKNOWN';

export interface ConsentState {
  policyVersion: string;
  decidedAt: string; // ISO-8601
  region: Region;
  source: ConsentSource;
  isMinor: boolean;
  categories: Record<ConsentCategory, boolean>;
}

/** The fail-closed default. Only `necessary` is on. Used whenever state is absent or unreadable. */
export function failClosedState(
  policyVersion: string,
  region: Region = 'UNKNOWN',
): ConsentState {
  return {
    policyVersion,
    decidedAt: new Date().toISOString(),
    region,
    source: 'default',
    isMinor: false,
    categories: {
      necessary: true,
      functional: false,
      analytics: false,
      advertising: false,
    },
  };
}

/** UNKNOWN region is treated as EU (strictest). EU/KR default to opt-in (all off). */
export function isOptInRegion(region: Region): boolean {
  return region === 'EU' || region === 'KR' || region === 'UNKNOWN';
}

// ---------------------------------------------------------------------------
// Platform-agnostic gate
// ---------------------------------------------------------------------------

/**
 * THE gate. Every tracker init must pass through this.
 * fail-closed: a falsy/partial state denies all non-necessary categories.
 */
export function canTrack(
  state: ConsentState | null | undefined,
  category: ConsentCategory,
): boolean {
  if (category === 'necessary') return true; // only fail-open category
  if (!state || !state.categories) return false; // fail-closed
  // Minors never get advertising or personalized analytics.
  if (state.isMinor && (category === 'advertising' || category === 'analytics')) {
    return false;
  }
  return state.categories[category] === true;
}

/**
 * Load a tracker only if its category is consented. Returns true if loaded.
 * `loader` should perform the actual SDK init (e.g. initGA4()).
 */
export function loadTracker(
  state: ConsentState | null | undefined,
  category: ConsentCategory,
  loader: () => void,
): boolean {
  if (!canTrack(state, category)) return false;
  loader();
  return true;
}

// ---------------------------------------------------------------------------
// GPC / DNT (web only — RN has no equivalent, use explicit toggles)
// ---------------------------------------------------------------------------

/**
 * Read browser privacy signals. Returns category overrides to seed (advertising
 * off on GPC; analytics off on DNT). Caller still records source='gpc'|'dnt' in the ledger.
 * Safe to call on RN — returns {} because `navigator` is absent.
 */
export function readPrivacySignals(): Partial<Record<ConsentCategory, boolean>> {
  if (typeof navigator === 'undefined') return {};
  const overrides: Partial<Record<ConsentCategory, boolean>> = {};
  // GPC: Global Privacy Control (Sec-GPC: 1 on the server side).
  if ((navigator as { globalPrivacyControl?: boolean }).globalPrivacyControl === true) {
    overrides.advertising = false;
  }
  // DNT: advisory only, not legally binding — treat as analytics-off hint.
  if (navigator.doNotTrack === '1') {
    overrides.analytics = false;
  }
  return overrides;
}

// ---------------------------------------------------------------------------
// Persistence — platform branch
// ---------------------------------------------------------------------------

const STORAGE_KEY = 'consent.v1';

export interface ConsentStorage {
  read(): Promise<ConsentState | null>;
  write(state: ConsentState): Promise<void>;
  clear(): Promise<void>;
}

/** Web: cookie/localStorage. Falls back to fail-closed on parse error. */
export function createWebStorage(): ConsentStorage {
  return {
    async read() {
      try {
        const raw = globalThis.localStorage?.getItem(STORAGE_KEY);
        return raw ? (JSON.parse(raw) as ConsentState) : null;
      } catch {
        return null; // fail-closed
      }
    },
    async write(state) {
      globalThis.localStorage?.setItem(STORAGE_KEY, JSON.stringify(state));
    },
    async clear() {
      globalThis.localStorage?.removeItem(STORAGE_KEY);
    },
  };
}

/**
 * React Native: AsyncStorage. Pass the AsyncStorage module in (avoid a hard
 * import so this file stays platform-neutral).
 *   createRnStorage(require('@react-native-async-storage/async-storage').default)
 */
export function createRnStorage(asyncStorage: {
  getItem(k: string): Promise<string | null>;
  setItem(k: string, v: string): Promise<void>;
  removeItem(k: string): Promise<void>;
}): ConsentStorage {
  return {
    async read() {
      try {
        const raw = await asyncStorage.getItem(STORAGE_KEY);
        return raw ? (JSON.parse(raw) as ConsentState) : null;
      } catch {
        return null; // fail-closed
      }
    },
    async write(state) {
      await asyncStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    },
    async clear() {
      await asyncStorage.removeItem(STORAGE_KEY);
    },
  };
}

// ---------------------------------------------------------------------------
// Decision + ledger
// ---------------------------------------------------------------------------

/**
 * Record a consent decision: persist locally AND append to the server ledger.
 * `appendLedger` should INSERT into consent_ledger (see consent-ledger.sql).
 * Withdrawal is just a decision where the category flips to false — callers
 * should additionally tear down the affected SDK + clear its cookies.
 */
export async function recordDecision(
  storage: ConsentStorage,
  appendLedger: (state: ConsentState) => Promise<void>,
  state: ConsentState,
): Promise<void> {
  await storage.write(state);
  await appendLedger(state); // never UPDATE — ledger is append-only
}

/** Re-prompt when the live policy version is newer than the user's last decision. */
export function needsReConsent(
  state: ConsentState | null,
  livePolicyVersion: string,
): boolean {
  if (!state) return true;
  return state.policyVersion < livePolicyVersion;
}

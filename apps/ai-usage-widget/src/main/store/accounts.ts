import { isProviderId, type Account } from '../../shared/types';
import { isFiniteNumber, isId, isPlainObject, normalizeLabel } from '../../shared/validate';
import { profileDirFor } from '../paths';

export const ACCOUNTS_FILE_VERSION = 1;

export interface PersistedAccount {
  id: string;
  provider: Account['provider'];
  label: string;
  enabled: boolean;
  order: number;
  createdAt: number;
}

export interface AccountsFile {
  version: typeof ACCOUNTS_FILE_VERSION;
  accounts: PersistedAccount[];
}

export interface NormalizedAccounts {
  accounts: Account[];
  /** Entries dropped because they were invalid or duplicated. */
  dropped: number;
}

/**
 * Loads persisted accounts defensively: invalid or duplicate entries are
 * dropped, `profileDir` is always recomputed from the profiles root (a stored
 * path is never trusted) and an empty list stays empty (V1-15).
 */
export function normalizeAccounts(raw: unknown, profilesRoot: string): NormalizedAccounts {
  const list: unknown[] = Array.isArray(raw)
    ? raw
    : isPlainObject(raw) && Array.isArray(raw.accounts)
      ? (raw.accounts as unknown[])
      : [];
  const seen = new Set<string>();
  const accepted: { account: Account; index: number }[] = [];
  let dropped = 0;
  list.forEach((entry, index) => {
    if (!isPlainObject(entry) || !isId(entry.id) || !isProviderId(entry.provider) || seen.has(entry.id)) {
      dropped += 1;
      return;
    }
    const label = normalizeLabel(entry.label);
    if (label === null) {
      dropped += 1;
      return;
    }
    let profileDir: string;
    try {
      profileDir = profileDirFor(profilesRoot, entry.provider, entry.id);
    } catch {
      dropped += 1;
      return;
    }
    seen.add(entry.id);
    accepted.push({
      index,
      account: {
        id: entry.id,
        provider: entry.provider,
        label,
        enabled: typeof entry.enabled === 'boolean' ? entry.enabled : true,
        order: isFiniteNumber(entry.order) ? entry.order : index,
        profileDir,
        createdAt: isFiniteNumber(entry.createdAt) && entry.createdAt > 0 ? entry.createdAt : 0,
      },
    });
  });
  accepted.sort((a, b) => a.account.order - b.account.order || a.index - b.index);
  return { accounts: accepted.map(({ account }, order) => ({ ...account, order })), dropped };
}

/** Persisted shape: never includes `profileDir` (recomputed on load). */
export function serializeAccounts(accounts: readonly Account[]): AccountsFile {
  return {
    version: ACCOUNTS_FILE_VERSION,
    accounts: accounts.map((account) => ({
      id: account.id,
      provider: account.provider,
      label: account.label,
      enabled: account.enabled,
      order: account.order,
      createdAt: account.createdAt,
    })),
  };
}

export function cloneAccount(account: Account): Account {
  return { ...account };
}

/** Sorts by order and renumbers 0..n-1. */
export function renumberAccounts(accounts: readonly Account[]): Account[] {
  return [...accounts].sort((a, b) => a.order - b.order).map((account, order) => ({ ...account, order }));
}

/**
 * Moves one account up or down; returns null when the id is unknown. With `sameProvider`
 * it swaps places with the nearest account of the same provider, leaving the others in place.
 */
export function moveAccount(
  accounts: readonly Account[],
  accountId: string,
  direction: 'up' | 'down',
  options: { sameProvider?: boolean } = {},
): Account[] | null {
  const sorted = renumberAccounts(accounts);
  const index = sorted.findIndex((account) => account.id === accountId);
  if (index < 0) return null;
  const provider = sorted[index]?.provider;
  const step = direction === 'up' ? -1 : 1;
  let target = index + step;
  if (options.sameProvider === true) {
    while (target >= 0 && target < sorted.length && sorted[target]?.provider !== provider) target += step;
  }
  if (target < 0 || target >= sorted.length) return sorted;
  const a = sorted[index];
  const b = sorted[target];
  if (a === undefined || b === undefined) return sorted;
  sorted[index] = b;
  sorted[target] = a;
  return sorted.map((account, order) => ({ ...account, order }));
}

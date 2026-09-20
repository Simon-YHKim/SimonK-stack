import path from 'node:path';
import { normalizeSettings, type Settings } from '../../shared/settings';
import type { Account } from '../../shared/types';
import type { Logger } from '../log';
import { cloneAccount, normalizeAccounts, serializeAccounts } from './accounts';
import { readJsonWithBackup, writeFileAtomic } from './atomic';

export const SETTINGS_FILE = 'settings.json';
export const ACCOUNTS_FILE = 'accounts.json';

export interface AppStore {
  getSettings(): Settings;
  /** Deep copies; callers may mutate freely (V1-04). */
  getAccounts(): Account[];
  getAccount(accountId: string): Account | undefined;
  saveSettings(next: Settings): Promise<void>;
  saveAccounts(next: readonly Account[]): Promise<void>;
  /** Resolves after every queued write finished. */
  flush(): Promise<void>;
  readonly info: StoreLoadInfo;
}

export interface StoreLoadInfo {
  settingsSource: 'main' | 'backup' | 'none';
  accountsSource: 'main' | 'backup' | 'none';
  droppedAccounts: number;
}

export interface OpenStoreOptions {
  dir: string;
  profilesRoot: string;
  logger: Logger;
}

/** settings.json + accounts.json in userData. No secrets are ever stored here. */
export async function openStore(options: OpenStoreOptions): Promise<AppStore> {
  const settingsFile = path.join(options.dir, SETTINGS_FILE);
  const accountsFile = path.join(options.dir, ACCOUNTS_FILE);
  const logger = options.logger;

  const settingsRead = await readJsonWithBackup(settingsFile);
  const accountsRead = await readJsonWithBackup(accountsFile);
  if (settingsRead.mainCorrupt) logger.warn('settings.json unreadable', { fallback: settingsRead.source });
  if (accountsRead.mainCorrupt) logger.warn('accounts.json unreadable', { fallback: accountsRead.source });

  let settings = normalizeSettings(settingsRead.value);
  const normalized = normalizeAccounts(accountsRead.value, options.profilesRoot);
  let accounts = normalized.accounts;
  if (normalized.dropped > 0) logger.warn('dropped invalid account entries', { count: normalized.dropped });

  const queues = new Map<string, Promise<void>>();
  const enqueue = (file: string, content: string): Promise<void> => {
    const previous = queues.get(file) ?? Promise.resolve();
    const next = previous.catch(() => undefined).then(() => writeFileAtomic(file, content, { backup: true }));
    queues.set(file, next);
    return next;
  };

  return {
    info: {
      settingsSource: settingsRead.source,
      accountsSource: accountsRead.source,
      droppedAccounts: normalized.dropped,
    },
    getSettings: () => ({ ...settings }),
    getAccounts: () => accounts.map(cloneAccount),
    getAccount: (accountId) => {
      const found = accounts.find((account) => account.id === accountId);
      return found === undefined ? undefined : cloneAccount(found);
    },
    // Memory follows disk: a failed write leaves the previous value in place.
    saveSettings: (next) => {
      const value = normalizeSettings(next);
      return enqueue(settingsFile, `${JSON.stringify(value, null, 2)}\n`).then(() => {
        settings = value;
      });
    },
    saveAccounts: (next) => {
      const value = next.map(cloneAccount);
      return enqueue(accountsFile, `${JSON.stringify(serializeAccounts(value), null, 2)}\n`).then(() => {
        accounts = value;
      });
    },
    flush: async () => {
      await Promise.allSettled([...queues.values()]);
    },
  };
}

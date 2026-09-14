import { mkdir, mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { DEFAULT_SETTINGS } from '../../shared/settings';
import type { Account } from '../../shared/types';
import { nullLogger } from '../log';
import { moveAccount, normalizeAccounts, renumberAccounts, serializeAccounts } from './accounts';
import { backupPathFor, readJsonWithBackup, writeFileAtomic } from './atomic';
import { ACCOUNTS_FILE, SETTINGS_FILE, openStore } from '.';

let dir: string;
let profilesRoot: string;

beforeEach(async () => {
  dir = await mkdtemp(path.join(os.tmpdir(), 'aiuw-store-'));
  profilesRoot = path.join(dir, 'local', 'profiles');
});

afterEach(async () => {
  await rm(dir, { recursive: true, force: true });
});

const account = (over: Partial<Account> = {}): Account => ({
  id: 'acc1',
  provider: 'codex',
  label: 'Work',
  enabled: true,
  order: 0,
  profileDir: 'ignored',
  createdAt: 1_700_000_000_000,
  ...over,
});

describe('atomic write', () => {
  it('replaces content, keeps a backup of the previous file and leaves no temp files', async () => {
    const file = path.join(dir, 'nested', 'a.json');
    await writeFileAtomic(file, '{"v":1}', { backup: true });
    await writeFileAtomic(file, '{"v":2}', { backup: true });
    expect(await readFile(file, 'utf8')).toBe('{"v":2}');
    expect(await readFile(backupPathFor(file), 'utf8')).toBe('{"v":1}');
    expect((await readdir(path.dirname(file))).filter((name) => name.endsWith('.tmp'))).toEqual([]);
  });

  it('never replaces a good backup with a corrupt main file (CR-09)', async () => {
    const file = path.join(dir, 'c.json');
    await writeFile(file, '{broken', 'utf8');
    await writeFile(backupPathFor(file), '{"good":true}', 'utf8');
    await writeFileAtomic(file, '{"v":3}', { backup: true });
    expect(await readFile(file, 'utf8')).toBe('{"v":3}');
    expect(await readFile(backupPathFor(file), 'utf8')).toBe('{"good":true}');
  });

  it('falls back to the backup when the main file is corrupt, and strips a BOM', async () => {
    const file = path.join(dir, 'b.json');
    await writeFile(file, '{broken', 'utf8');
    await writeFile(backupPathFor(file), '\uFEFF{"ok":true}', 'utf8');
    await expect(readJsonWithBackup(file)).resolves.toEqual({ value: { ok: true }, source: 'backup', mainCorrupt: true });
    await expect(readJsonWithBackup(path.join(dir, 'missing.json'))).resolves.toEqual({
      value: undefined,
      source: 'none',
      mainCorrupt: false,
    });
  });
});

describe('accounts normalization', () => {
  it('drops invalid and duplicate entries and recomputes profileDir', () => {
    const result = normalizeAccounts(
      {
        version: 1,
        accounts: [
          { id: 'b', provider: 'grok', label: ' Second ', enabled: false, order: 5, createdAt: 2, profileDir: 'C:\\evil' },
          { id: 'a', provider: 'claude', label: 'First', order: 1 },
          { id: 'a', provider: 'codex', label: 'dup' },
          { id: '../x', provider: 'codex', label: 'bad id' },
          { id: 'c', provider: 'gemini', label: 'bad provider' },
          { id: 'd', provider: 'codex', label: '' },
          'garbage',
        ],
      },
      profilesRoot,
    );
    expect(result.dropped).toBe(5);
    expect(result.accounts.map((a) => [a.id, a.order, a.label, a.enabled])).toEqual([
      ['a', 0, 'First', true],
      ['b', 1, 'Second', false],
    ]);
    expect(result.accounts[1]?.profileDir).toBe(path.resolve(profilesRoot, 'grok', 'b'));
  });

  it('keeps an empty list empty (V1-15) and never persists profileDir', () => {
    expect(normalizeAccounts({ version: 1, accounts: [] }, profilesRoot).accounts).toEqual([]);
    expect(normalizeAccounts(undefined, profilesRoot).accounts).toEqual([]);
    const file = serializeAccounts([account()]);
    expect(JSON.stringify(file)).not.toContain('profileDir');
  });

  it('moves and renumbers accounts', () => {
    const list = [account({ id: 'a', order: 3 }), account({ id: 'b', order: 1 }), account({ id: 'c', order: 2 })];
    expect(renumberAccounts(list).map((a) => a.id)).toEqual(['b', 'c', 'a']);
    expect(moveAccount(list, 'a', 'up')?.map((a) => [a.id, a.order])).toEqual([
      ['b', 0],
      ['a', 1],
      ['c', 2],
    ]);
    expect(moveAccount(list, 'b', 'up')?.map((a) => a.id)).toEqual(['b', 'c', 'a']);
    expect(moveAccount(list, 'zzz', 'down')).toBeNull();
  });

  it('moves within the same provider, skipping other providers (P-05)', () => {
    const list = [
      account({ id: 'c1', provider: 'claude', order: 0 }),
      account({ id: 'x1', provider: 'codex', order: 1 }),
      account({ id: 'g1', provider: 'grok', order: 2 }),
      account({ id: 'x2', provider: 'codex', order: 3 }),
    ];
    expect(moveAccount(list, 'x2', 'up', { sameProvider: true })?.map((a) => a.id)).toEqual(['c1', 'x2', 'g1', 'x1']);
    expect(moveAccount(list, 'x1', 'up', { sameProvider: true })?.map((a) => a.id)).toEqual(['c1', 'x1', 'g1', 'x2']);
    expect(moveAccount(list, 'c1', 'down', { sameProvider: true })?.map((a) => a.id)).toEqual(['c1', 'x1', 'g1', 'x2']);
  });
});

describe('openStore', () => {
  it('starts from defaults without writing anything', async () => {
    const store = await openStore({ dir, profilesRoot, logger: nullLogger });
    expect(store.getSettings()).toEqual(DEFAULT_SETTINGS);
    expect(store.getAccounts()).toEqual([]);
    expect(store.info).toEqual({ settingsSource: 'none', accountsSource: 'none', droppedAccounts: 0 });
    expect(await readdir(dir)).toEqual([]);
  });

  it('persists settings and accounts and reloads them validated', async () => {
    const store = await openStore({ dir, profilesRoot, logger: nullLogger });
    await store.saveSettings({ ...DEFAULT_SETTINGS, theme: '1c', offsetPx: 99 });
    await store.saveAccounts([account({ id: 'x1', label: 'Mine' })]);
    const copy = store.getAccounts();
    copy[0]!.label = 'mutated';
    expect(store.getAccount('x1')?.label).toBe('Mine');

    const raw = JSON.parse(await readFile(path.join(dir, ACCOUNTS_FILE), 'utf8')) as unknown;
    expect(JSON.stringify(raw)).not.toContain('profileDir');

    await writeFile(
      path.join(dir, SETTINGS_FILE),
      JSON.stringify({ theme: '1c', offsetPx: 99, refreshIntervalSec: 7, legacyMock: true }),
      'utf8',
    );
    const reloaded = await openStore({ dir, profilesRoot, logger: nullLogger });
    expect(reloaded.getSettings()).toEqual({ ...DEFAULT_SETTINGS, theme: '1c', offsetPx: 99 });
    expect(reloaded.getAccounts()).toEqual([
      { ...account({ id: 'x1', label: 'Mine' }), profileDir: path.resolve(profilesRoot, 'codex', 'x1') },
    ]);
  });

  it('keeps the in-memory value when the write fails (CR-10)', async () => {
    const store = await openStore({ dir, profilesRoot, logger: nullLogger });
    await store.saveAccounts([account({ id: 'x1' })]);
    // A directory where accounts.json must be replaced makes every rename fail.
    await rm(path.join(dir, ACCOUNTS_FILE), { force: true });
    await mkdir(path.join(dir, ACCOUNTS_FILE));
    await expect(store.saveAccounts([account({ id: 'x1' }), account({ id: 'x2', order: 1 })])).rejects.toBeDefined();
    expect(store.getAccounts().map((a) => a.id)).toEqual(['x1']);
  });

  it('serializes concurrent writes so the last save wins', async () => {
    const store = await openStore({ dir, profilesRoot, logger: nullLogger });
    await Promise.all([10, 20, 30, 40].map((offsetPx) => store.saveSettings({ ...DEFAULT_SETTINGS, offsetPx })));
    await store.flush();
    const saved = JSON.parse(await readFile(path.join(dir, SETTINGS_FILE), 'utf8')) as { offsetPx: number };
    expect(saved.offsetPx).toBe(40);
  });
});

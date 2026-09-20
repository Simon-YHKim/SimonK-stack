// Filesystem side of the statusline bridge: script copies, settings.json install/uninstall,
// wrap sidecars, default-profile state and reading records. Paths come only from ProviderDeps.

import { createHash, randomUUID } from 'node:crypto';
import { copyFile, constants as fsConstants, mkdir, readFile, readdir, rename, rm, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';
import type { ErrorCode } from '../../../shared/types';
import { isId, isPlainObject } from '../../../shared/validate';
import { ProviderError } from '../types';
import { BRIDGE_KEY_RE, BRIDGE_RECORD_MAX_BYTES, BRIDGE_RECORD_VERSION, parseBridgeRecord, type BridgeRecord } from './bridge-data';
import {
  applyBridgeStatusLine,
  bridgeKeyInCommand,
  isBridgeCommand,
  newSettingsDocument,
  parsePreviousStatusLine,
  parseSettingsJson,
  removeBridgeStatusLine,
  serializeSettings,
  statusLineCommand,
  type PreviousStatusLine,
} from './settings-merge';

export const BRIDGE_SCRIPT_FILES = { node: 'aiuw-claude-bridge.cjs', powershell: 'aiuw-claude-bridge.ps1' } as const;
export type BridgeRuntime = keyof typeof BRIDGE_SCRIPT_FILES;
export const SETTINGS_FILE_NAME = 'settings.json';
export const SETTINGS_MAX_BYTES = 1024 * 1024;
/** settings.json can hold secrets (env, apiKeyHelper); keep only a few widget backups of it. */
export const SETTINGS_BACKUPS_KEPT = 3;

// Injected at build time (electron.vite.config.ts, vitest.config.ts) from resources/claude-bridge,
// so the value lives inside the integrity-checked app.asar while the scripts ship outside it.
declare const __AIUW_BRIDGE_SHA256__: Readonly<Record<BridgeRuntime, string>>;

/** Expected SHA-256 (hex) of each bridge script, or null when the build did not embed them. */
export const BRIDGE_SCRIPT_SHA256: Readonly<Record<BridgeRuntime, string>> | null =
  typeof __AIUW_BRIDGE_SHA256__ === 'object' ? __AIUW_BRIDGE_SHA256__ : null;

export interface ClaudeBridgeLayout {
  /** `<bridgeRoot>\claude`: records `<key>.json`, sidecars `<key>.wrap.json`. */
  dir: string;
  /** Stable copies of the bridge scripts referenced by statusLine commands. */
  binDir: string;
  defaultStatePath: string;
  recordPath(key: string): string;
  wrapPath(key: string): string;
}

function assertKey(key: string): void {
  if (!BRIDGE_KEY_RE.test(key)) throw new ProviderError('internal', 'invalid bridge key');
}

export function claudeBridgeLayout(bridgeRoot: string): ClaudeBridgeLayout {
  const dir = path.join(bridgeRoot, 'claude');
  return {
    dir,
    binDir: path.join(dir, 'bin'),
    defaultStatePath: path.join(dir, 'default-profile.json'),
    recordPath: (key) => {
      assertKey(key);
      return path.join(dir, `${key}.json`);
    },
    wrapPath: (key) => {
      assertKey(key);
      return path.join(dir, `${key}.wrap.json`);
    },
  };
}

/**
 * Claude Code runs statusLine commands through Git Bash, or PowerShell without it
 * (statusline docs, Windows configuration). Single-quoted forward-slash paths mean
 * the same literal string in both shells; a path containing `'` or control characters is refused.
 */
function shellQuotePath(filePath: string): string {
  for (const ch of filePath) {
    if (ch === "'" || ch.charCodeAt(0) < 0x20) {
      throw new ProviderError('internal', 'bridge path cannot be quoted safely');
    }
  }
  return `'${filePath.replace(/\\/g, '/')}'`;
}

export function buildBridgeCommand(runtime: BridgeRuntime, layout: ClaudeBridgeLayout, key: string): string {
  assertKey(key);
  const script = shellQuotePath(path.join(layout.binDir, BRIDGE_SCRIPT_FILES[runtime]));
  const out = shellQuotePath(layout.dir);
  if (runtime === 'node') return `node ${script} --key ${key} --out ${out}`;
  return `powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File ${script} -Key ${key} -Out ${out}`;
}

function errnoCode(error: unknown): string | undefined {
  const code = (error as { code?: unknown } | null)?.code;
  return typeof code === 'string' ? code : undefined;
}

export function errorCodeOf(error: unknown): ErrorCode {
  return error instanceof ProviderError ? error.code : 'internal';
}

/** File text, or null when missing. Throws ProviderError for oversize, non-files and I/O failures. */
export async function readTextIfExists(filePath: string, maxBytes: number): Promise<string | null> {
  try {
    const info = await stat(filePath);
    if (!info.isFile() || info.size > maxBytes) throw new ProviderError('parse-error', 'not a readable file');
    return await readFile(filePath, 'utf8');
  } catch (error) {
    if (errnoCode(error) === 'ENOENT') return null;
    if (error instanceof ProviderError) throw error;
    throw new ProviderError('internal', 'file read failed', { cause: error });
  }
}

export async function writeFileAtomic(filePath: string, content: string | Buffer): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const tmp = `${filePath}.${randomUUID()}.tmp`;
  try {
    await writeFile(tmp, content);
    await rename(tmp, filePath);
  } catch (error) {
    await rm(tmp, { force: true });
    throw error;
  }
}

/** `20260915T031200123Z`. */
export function backupTimestamp(ms: number): string {
  return new Date(ms).toISOString().replace(/[-:.]/g, '');
}

/**
 * Copies `filePath` to a new `<file>.aiuw-backup-<timestamp>[-n]` next to it and returns the backup path.
 * Within one timestamp `n` only grows, so a name freed by pruning is never reused for a newer copy.
 */
export async function backupFile(filePath: string, now: number): Promise<string> {
  const base = `${filePath}.aiuw-backup-${backupTimestamp(now)}`;
  const baseName = path.basename(base);
  let first = 0;
  try {
    for (const name of await readdir(path.dirname(filePath))) {
      if (name === baseName) first = Math.max(first, 1);
      else if (name.startsWith(`${baseName}-`)) {
        const n = Number(name.slice(baseName.length + 1));
        if (Number.isInteger(n) && n >= 0) first = Math.max(first, n + 1);
      }
    }
  } catch {
    // Listing is only a hint; COPYFILE_EXCL below still never overwrites.
  }
  for (let attempt = first; attempt < first + 100; attempt += 1) {
    const target = attempt === 0 ? base : `${base}-${attempt}`;
    try {
      await copyFile(filePath, target, fsConstants.COPYFILE_EXCL);
      return target;
    } catch (error) {
      if (errnoCode(error) !== 'EEXIST') throw error;
    }
  }
  throw new ProviderError('internal', 'no free backup file name');
}

function backupOrder(name: string): [string, number] {
  const match = /^(.*?)(?:-(\d+))?$/.exec(name);
  return [match?.[1] ?? name, Number(match?.[2] ?? 0)];
}

/** Keeps the newest `keep` widget backups of `filePath` and deletes older ones. Best effort. */
export async function pruneBackups(filePath: string, keep: number): Promise<void> {
  const prefix = `${path.basename(filePath)}.aiuw-backup-`;
  let names: string[];
  try {
    names = (await readdir(path.dirname(filePath))).filter((name) => name.startsWith(prefix));
  } catch {
    return;
  }
  // Newest first: the ISO basic timestamp sorts by code unit, then the suffix within one timestamp.
  names.sort((a, b) => {
    const [baseA, nA] = backupOrder(a);
    const [baseB, nB] = backupOrder(b);
    if (baseA === baseB) return nB - nA;
    return baseA < baseB ? 1 : -1;
  });
  for (const name of names.slice(keep)) {
    await rm(path.join(path.dirname(filePath), name), { force: true }).catch(() => undefined);
  }
}

async function backupSettings(settingsPath: string, now: number): Promise<string> {
  const backupPath = await backupFile(settingsPath, now);
  await pruneBackups(settingsPath, SETTINGS_BACKUPS_KEPT);
  return backupPath;
}

function sha256Hex(content: Buffer): string {
  return createHash('sha256').update(content).digest('hex');
}

/**
 * Copies the bridge scripts from packaged resources to the stable bin dir when they differ.
 * The resource bytes must match the hashes embedded at build time: the scripts live outside
 * app.asar, and Claude Code executes the copies.
 */
export async function ensureBridgeScripts(
  resourcesDir: string,
  layout: ClaudeBridgeLayout,
  expected: Readonly<Record<BridgeRuntime, string>> | null = BRIDGE_SCRIPT_SHA256,
): Promise<void> {
  if (expected === null) throw new ProviderError('internal', 'bridge script hashes missing from build');
  for (const runtime of Object.keys(BRIDGE_SCRIPT_FILES) as BridgeRuntime[]) {
    const name = BRIDGE_SCRIPT_FILES[runtime];
    let content: Buffer;
    try {
      content = await readFile(path.join(resourcesDir, 'claude-bridge', name));
    } catch (error) {
      throw new ProviderError('internal', 'bridge script missing from resources', { cause: error });
    }
    if (sha256Hex(content) !== expected[runtime]) {
      throw new ProviderError('internal', 'bridge script failed its integrity check');
    }
    const target = path.join(layout.binDir, name);
    let existing: Buffer | null = null;
    try {
      existing = await readFile(target);
    } catch {
      existing = null;
    }
    if (existing?.equals(content) === true) continue;
    await writeFileAtomic(target, content);
  }
}

export type WrapStateRead = { kind: 'missing' } | { kind: 'invalid' } | { kind: 'ok'; previous: PreviousStatusLine };

/** Distinguishes a missing sidecar from one that exists but cannot be read (never overwrite the latter). */
export async function readWrapState(layout: ClaudeBridgeLayout, key: string): Promise<WrapStateRead> {
  let text: string | null;
  try {
    text = await readTextIfExists(layout.wrapPath(key), BRIDGE_RECORD_MAX_BYTES);
  } catch {
    return { kind: 'invalid' };
  }
  if (text === null) return { kind: 'missing' };
  try {
    const value: unknown = JSON.parse(text);
    if (!isPlainObject(value) || value.v !== BRIDGE_RECORD_VERSION) return { kind: 'invalid' };
    const previous = parsePreviousStatusLine(value.previous);
    return previous === null ? { kind: 'invalid' } : { kind: 'ok', previous };
  } catch {
    return { kind: 'invalid' };
  }
}

async function writeWrapState(layout: ClaudeBridgeLayout, key: string, previous: PreviousStatusLine): Promise<void> {
  await writeFileAtomic(layout.wrapPath(key), `${JSON.stringify({ v: BRIDGE_RECORD_VERSION, previous }, null, 2)}\n`);
}

/** Sidecar keys to consult for an installed bridge: the key in its command first, then `key`. */
function wrapKeysFor(command: string | null, key: string): string[] {
  const inCommand = bridgeKeyInCommand(command);
  return inCommand === null || inCommand === key ? [key] : [inCommand, key];
}

/**
 * Recorded original statusLine for an installed bridge. `invalid` means a sidecar exists but is
 * unreadable: the caller must refuse rather than lose the user's command.
 */
async function recordedPrevious(
  layout: ClaudeBridgeLayout,
  keys: readonly string[],
): Promise<{ kind: 'invalid' } | { kind: 'ok'; previous: PreviousStatusLine | null; fromKey: string | null }> {
  for (const key of keys) {
    const read = await readWrapState(layout, key);
    if (read.kind === 'invalid') return { kind: 'invalid' };
    if (read.kind === 'ok') return { kind: 'ok', previous: read.previous, fromKey: key };
  }
  return { kind: 'ok', previous: null, fromKey: null };
}

export type ConfigDirInstallResult =
  | { ok: true; changed: boolean; wrapsExisting: boolean; backupPath: string | null }
  | { ok: false; code: ErrorCode };

export interface ConfigDirInput {
  configDir: string;
  key: string;
  layout: ClaudeBridgeLayout;
  now: number;
}

/**
 * Installs the bridge into `<configDir>\settings.json`. Refuses (no write, no backup)
 * when the file is not a JSON object, holds an unsupported statusLine, or an installed
 * bridge's sidecar is unreadable. Backs up the file only when the bridge takes over
 * statusLine; re-pointing an installed bridge (runtime or key change) needs no new copy.
 */
export async function installBridgeIntoConfigDir(input: ConfigDirInput & { command: string }): Promise<ConfigDirInstallResult> {
  const settingsPath = path.join(input.configDir, SETTINGS_FILE_NAME);
  try {
    const text = await readTextIfExists(settingsPath, SETTINGS_MAX_BYTES);
    const doc = text === null ? newSettingsDocument() : parseSettingsJson(text);
    if (doc === null) return { ok: false, code: 'parse-error' };
    const current = statusLineCommand(doc.data);
    const alreadyInstalled = isBridgeCommand(current);
    let recorded: PreviousStatusLine | null = null;
    let sidecarCurrent = false;
    if (alreadyInstalled) {
      const found = await recordedPrevious(input.layout, wrapKeysFor(current, input.key));
      if (found.kind === 'invalid') return { ok: false, code: 'parse-error' };
      recorded = found.previous;
      sidecarCurrent = found.fromKey === input.key;
    }
    const applied = applyBridgeStatusLine(doc.data, input.command, recorded);
    if (!applied.ok) return { ok: false, code: 'parse-error' };
    // Sidecar first: an already-running Claude Code must never see the bridge without the wrapped command.
    if (!sidecarCurrent) await writeWrapState(input.layout, input.key, applied.previous);
    let backupPath: string | null = null;
    if (applied.changed) {
      if (text !== null && !alreadyInstalled) backupPath = await backupSettings(settingsPath, input.now);
      await writeFileAtomic(settingsPath, serializeSettings({ ...doc, data: applied.data }));
    }
    return { ok: true, changed: applied.changed, wrapsExisting: applied.previous.present, backupPath };
  } catch (error) {
    return { ok: false, code: errorCodeOf(error) };
  }
}

export type ConfigDirUninstallResult = { ok: true; changed: boolean; backupPath: string | null } | { ok: false; code: ErrorCode };

/**
 * Restores the recorded statusLine (or removes the key when none was recorded). The sidecar is
 * looked up by the key in the installed command, so a bridge installed under another key is
 * still restored. A statusLine the bridge no longer owns is left untouched.
 */
export async function uninstallBridgeFromConfigDir(input: ConfigDirInput): Promise<ConfigDirUninstallResult> {
  const settingsPath = path.join(input.configDir, SETTINGS_FILE_NAME);
  try {
    const text = await readTextIfExists(settingsPath, SETTINGS_MAX_BYTES);
    let changed = false;
    let backupPath: string | null = null;
    let keys = [input.key];
    if (text !== null) {
      const doc = parseSettingsJson(text);
      if (doc === null) return { ok: false, code: 'parse-error' };
      const current = statusLineCommand(doc.data);
      keys = wrapKeysFor(current, input.key);
      if (isBridgeCommand(current)) {
        const found = await recordedPrevious(input.layout, keys);
        if (found.kind === 'invalid') return { ok: false, code: 'parse-error' };
        const removed = removeBridgeStatusLine(doc.data, found.previous ?? { present: false });
        if (removed.changed) {
          backupPath = await backupSettings(settingsPath, input.now);
          await writeFileAtomic(settingsPath, serializeSettings({ ...doc, data: removed.data }));
          changed = true;
        }
      }
    }
    for (const key of keys) await rm(input.layout.wrapPath(key), { force: true });
    return { ok: true, changed, backupPath };
  } catch (error) {
    return { ok: false, code: errorCodeOf(error) };
  }
}

export interface DefaultBridgeState {
  targetAccountId: string;
  installedAt: number;
  backupPath: string | null;
  /** Key of the installed default-profile command (records are written under it). */
  key: string | null;
}

export async function readDefaultState(layout: ClaudeBridgeLayout): Promise<DefaultBridgeState | null> {
  try {
    const text = await readTextIfExists(layout.defaultStatePath, BRIDGE_RECORD_MAX_BYTES);
    if (text === null) return null;
    const value: unknown = JSON.parse(text);
    if (!isPlainObject(value) || value.v !== BRIDGE_RECORD_VERSION || !isId(value.targetAccountId)) return null;
    if (typeof value.installedAt !== 'number') return null;
    return {
      targetAccountId: value.targetAccountId,
      installedAt: value.installedAt,
      backupPath: typeof value.backupPath === 'string' ? value.backupPath : null,
      key: typeof value.key === 'string' && BRIDGE_KEY_RE.test(value.key) ? value.key : null,
    };
  } catch {
    return null;
  }
}

export async function writeDefaultState(layout: ClaudeBridgeLayout, state: DefaultBridgeState): Promise<void> {
  await writeFileAtomic(layout.defaultStatePath, `${JSON.stringify({ v: BRIDGE_RECORD_VERSION, ...state }, null, 2)}\n`);
}

export type BridgeRecordRead = { kind: 'missing' } | { kind: 'invalid' } | { kind: 'record'; record: BridgeRecord };

export async function readBridgeRecord(layout: ClaudeBridgeLayout, key: string): Promise<BridgeRecordRead> {
  let text: string | null;
  try {
    text = await readTextIfExists(layout.recordPath(key), BRIDGE_RECORD_MAX_BYTES);
  } catch {
    return { kind: 'invalid' };
  }
  if (text === null) return { kind: 'missing' };
  const record = parseBridgeRecord(text, key);
  return record === null ? { kind: 'invalid' } : { kind: 'record', record };
}

// Filesystem side of the statusline bridge: script copies, settings.json install/uninstall,
// wrap sidecars, default-profile state and reading records. Paths come only from ProviderDeps.

import { randomUUID } from 'node:crypto';
import { copyFile, constants as fsConstants, mkdir, readFile, rename, rm, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';
import type { ErrorCode } from '../../../shared/types';
import { isId, isPlainObject } from '../../../shared/validate';
import { ProviderError } from '../types';
import { BRIDGE_KEY_RE, BRIDGE_RECORD_MAX_BYTES, BRIDGE_RECORD_VERSION, parseBridgeRecord, type BridgeRecord } from './bridge-data';
import {
  applyBridgeStatusLine,
  newSettingsDocument,
  parsePreviousStatusLine,
  parseSettingsJson,
  removeBridgeStatusLine,
  serializeSettings,
  type PreviousStatusLine,
} from './settings-merge';

export const BRIDGE_SCRIPT_FILES = { node: 'aiuw-claude-bridge.cjs', powershell: 'aiuw-claude-bridge.ps1' } as const;
export type BridgeRuntime = keyof typeof BRIDGE_SCRIPT_FILES;
export const SETTINGS_FILE_NAME = 'settings.json';
export const SETTINGS_MAX_BYTES = 1024 * 1024;

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

/** Copies `filePath` to a new `<file>.aiuw-backup-<timestamp>` next to it and returns the backup path. */
export async function backupFile(filePath: string, now: number): Promise<string> {
  const base = `${filePath}.aiuw-backup-${backupTimestamp(now)}`;
  for (let attempt = 0; attempt < 100; attempt += 1) {
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

/** Copies the bridge scripts from packaged resources to the stable bin dir when they differ. */
export async function ensureBridgeScripts(resourcesDir: string, layout: ClaudeBridgeLayout): Promise<void> {
  for (const name of Object.values(BRIDGE_SCRIPT_FILES)) {
    let content: Buffer;
    try {
      content = await readFile(path.join(resourcesDir, 'claude-bridge', name));
    } catch (error) {
      throw new ProviderError('internal', 'bridge script missing from resources', { cause: error });
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

export async function readWrapState(layout: ClaudeBridgeLayout, key: string): Promise<PreviousStatusLine | null> {
  let text: string | null;
  try {
    text = await readTextIfExists(layout.wrapPath(key), BRIDGE_RECORD_MAX_BYTES);
  } catch {
    return null;
  }
  if (text === null) return null;
  try {
    const value: unknown = JSON.parse(text);
    if (!isPlainObject(value) || value.v !== BRIDGE_RECORD_VERSION) return null;
    return parsePreviousStatusLine(value.previous);
  } catch {
    return null;
  }
}

async function writeWrapState(layout: ClaudeBridgeLayout, key: string, previous: PreviousStatusLine): Promise<void> {
  await writeFileAtomic(layout.wrapPath(key), `${JSON.stringify({ v: BRIDGE_RECORD_VERSION, previous }, null, 2)}\n`);
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
 * when the file is not a JSON object or holds an unsupported statusLine. Backs up the
 * existing file before any change.
 */
export async function installBridgeIntoConfigDir(input: ConfigDirInput & { command: string }): Promise<ConfigDirInstallResult> {
  const settingsPath = path.join(input.configDir, SETTINGS_FILE_NAME);
  try {
    const text = await readTextIfExists(settingsPath, SETTINGS_MAX_BYTES);
    const doc = text === null ? newSettingsDocument() : parseSettingsJson(text);
    if (doc === null) return { ok: false, code: 'parse-error' };
    const applied = applyBridgeStatusLine(doc.data, input.command, await readWrapState(input.layout, input.key));
    if (!applied.ok) return { ok: false, code: 'parse-error' };
    // Sidecar first: an already-running Claude Code must never see the bridge without the wrapped command.
    await writeWrapState(input.layout, input.key, applied.previous);
    let backupPath: string | null = null;
    if (applied.changed) {
      if (text !== null) backupPath = await backupFile(settingsPath, input.now);
      await writeFileAtomic(settingsPath, serializeSettings({ ...doc, data: applied.data }));
    }
    return { ok: true, changed: applied.changed, wrapsExisting: applied.previous.present, backupPath };
  } catch (error) {
    return { ok: false, code: errorCodeOf(error) };
  }
}

export type ConfigDirUninstallResult = { ok: true; changed: boolean; backupPath: string | null } | { ok: false; code: ErrorCode };

/** Restores the recorded statusLine (or removes the key). A statusLine the bridge no longer owns is left untouched. */
export async function uninstallBridgeFromConfigDir(input: ConfigDirInput): Promise<ConfigDirUninstallResult> {
  const settingsPath = path.join(input.configDir, SETTINGS_FILE_NAME);
  try {
    const text = await readTextIfExists(settingsPath, SETTINGS_MAX_BYTES);
    let changed = false;
    let backupPath: string | null = null;
    if (text !== null) {
      const doc = parseSettingsJson(text);
      if (doc === null) return { ok: false, code: 'parse-error' };
      const previous = (await readWrapState(input.layout, input.key)) ?? { present: false };
      const removed = removeBridgeStatusLine(doc.data, previous);
      if (removed.changed) {
        backupPath = await backupFile(settingsPath, input.now);
        await writeFileAtomic(settingsPath, serializeSettings({ ...doc, data: removed.data }));
        changed = true;
      }
    }
    await rm(input.layout.wrapPath(input.key), { force: true });
    return { ok: true, changed, backupPath };
  } catch (error) {
    return { ok: false, code: errorCodeOf(error) };
  }
}

export interface DefaultBridgeState {
  targetAccountId: string;
  installedAt: number;
  backupPath: string | null;
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

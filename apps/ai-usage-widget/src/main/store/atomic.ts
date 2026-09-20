import { randomBytes } from 'node:crypto';
import { copyFile, mkdir, open, readFile, rename, rm } from 'node:fs/promises';
import path from 'node:path';

const RENAME_ATTEMPTS = 5;
const RENAME_RETRY_MS = 40;

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function errorCode(error: unknown): string | undefined {
  const code = (error as { code?: unknown } | null)?.code;
  return typeof code === 'string' ? code : undefined;
}

export function backupPathFor(file: string): string {
  return `${file}.bak`;
}

/**
 * Writes `content` to `<file>.<random>.tmp`, fsyncs, keeps the previous file as
 * `<file>.bak`, then renames over `file`. Rename is retried because antivirus or
 * indexers can briefly hold the target open on Windows (EPERM/EBUSY).
 */
export async function writeFileAtomic(file: string, content: string, options: { backup?: boolean } = {}): Promise<void> {
  await mkdir(path.dirname(file), { recursive: true });
  const tmp = `${file}.${randomBytes(6).toString('hex')}.tmp`;
  const handle = await open(tmp, 'w', 0o600);
  try {
    await handle.writeFile(content, { encoding: 'utf8' });
    await handle.sync();
  } finally {
    await handle.close();
  }
  try {
    // A corrupt main file must never overwrite the last good backup.
    if (options.backup === true && (await tryReadJson(file)).state === 'ok') {
      await copyFile(file, backupPathFor(file));
    }
    for (let attempt = 1; ; attempt += 1) {
      try {
        await rename(tmp, file);
        break;
      } catch (error) {
        const code = errorCode(error);
        if (attempt >= RENAME_ATTEMPTS || (code !== 'EPERM' && code !== 'EBUSY' && code !== 'EACCES')) throw error;
        await delay(RENAME_RETRY_MS * attempt);
      }
    }
  } catch (error) {
    await rm(tmp, { force: true });
    throw error;
  }
}

export type JsonReadSource = 'main' | 'backup' | 'none';

export interface JsonReadResult {
  value: unknown;
  source: JsonReadSource;
  /** Main file existed but could not be parsed. */
  mainCorrupt: boolean;
}

async function tryReadJson(file: string): Promise<{ state: 'missing' } | { state: 'corrupt' } | { state: 'ok'; value: unknown }> {
  let text: string;
  try {
    text = await readFile(file, 'utf8');
  } catch (error) {
    if (errorCode(error) === 'ENOENT') return { state: 'missing' };
    return { state: 'corrupt' };
  }
  try {
    return { state: 'ok', value: JSON.parse(text.replace(/^\uFEFF/, '')) as unknown };
  } catch {
    return { state: 'corrupt' };
  }
}

/** Reads JSON from `file`, falling back to its `.bak` when the main file is missing or corrupt. */
export async function readJsonWithBackup(file: string): Promise<JsonReadResult> {
  const main = await tryReadJson(file);
  if (main.state === 'ok') return { value: main.value, source: 'main', mainCorrupt: false };
  const backup = await tryReadJson(backupPathFor(file));
  const mainCorrupt = main.state === 'corrupt';
  if (backup.state === 'ok') return { value: backup.value, source: 'backup', mainCorrupt };
  return { value: undefined, source: 'none', mainCorrupt };
}

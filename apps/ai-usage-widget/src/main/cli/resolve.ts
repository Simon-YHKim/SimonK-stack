import { existsSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import type { ResolvedCommand } from './spawn';

export interface ResolveDeps {
  env: Readonly<Record<string, string | undefined>>;
  platform: NodeJS.Platform;
  isFile(filePath: string): boolean;
  readText(filePath: string): string;
}

export function defaultResolveDeps(): ResolveDeps {
  return {
    env: process.env,
    platform: process.platform,
    isFile: (filePath) => {
      try {
        return existsSync(filePath) && statSync(filePath).isFile();
      } catch {
        return false;
      }
    },
    readText: (filePath) => readFileSync(filePath, 'utf8'),
  };
}

function pathApi(platform: NodeJS.Platform): path.PlatformPath {
  return platform === 'win32' ? path.win32 : path.posix;
}

function envValue(env: ResolveDeps['env'], name: string, platform: NodeJS.Platform): string | undefined {
  if (platform !== 'win32') return env[name];
  const upper = name.toUpperCase();
  for (const [key, value] of Object.entries(env)) {
    if (key.toUpperCase() === upper) return value;
  }
  return undefined;
}

/**
 * Finds an executable like the OS would (PATH + PATHEXT on Windows), without
 * spawning `where`. Absolute or relative paths are checked directly.
 */
export function findOnPath(name: string, deps: ResolveDeps): string | null {
  const p = pathApi(deps.platform);
  const isWin = deps.platform === 'win32';
  const exts = isWin
    ? (envValue(deps.env, 'PATHEXT', deps.platform) ?? '.COM;.EXE;.BAT;.CMD')
        .split(';')
        .map((ext) => ext.trim().toLowerCase())
        .filter((ext) => ext.startsWith('.'))
    : [''];
  const hasExt = p.extname(name).length > 0;
  const candidatesFor = (base: string): string[] => (isWin && !hasExt ? exts.map((ext) => base + ext) : [base]);

  if (name.includes('/') || name.includes('\\') || p.isAbsolute(name)) {
    for (const candidate of candidatesFor(p.resolve(name))) {
      if (deps.isFile(candidate)) return candidate;
    }
    return null;
  }

  const pathVar = envValue(deps.env, 'PATH', deps.platform) ?? '';
  for (const rawDir of pathVar.split(isWin ? ';' : ':')) {
    const dir = rawDir.trim().replace(/^"(.*)"$/, '$1');
    if (dir.length === 0 || !p.isAbsolute(dir)) continue;
    for (const candidate of candidatesFor(p.join(dir, name))) {
      if (deps.isFile(candidate)) return candidate;
    }
  }
  return null;
}

// npm/pnpm cmd-shims reference their JS entry relative to the shim folder:
//   "%_prog%"  "%dp0%\node_modules\@openai\codex\bin\codex.js" %*
//   "%~dp0\node.exe"  "%~dp0\node_modules\pkg\cli.js" %*
const SHIM_ENTRY_RE = /"%(?:~dp0|dp0%)\\?([^"%]+?\.(?:c|m)?js)"/i;

/** Returns the JS entry path relative to the shim directory, or null. */
export function parseCmdShim(content: string): string | null {
  const match = SHIM_ENTRY_RE.exec(content);
  const rel = match?.[1];
  if (rel === undefined || rel.length === 0) return null;
  return rel.replace(/^[\\/]+/, '');
}

/** Accept only a plain Windows launcher that forwards every argument to one absolute executable. */
function parseCmdForwarder(content: string): string | null {
  const lines = content.replace(/^\uFEFF/, '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const [header, launch] = lines;
  if (lines.length !== 2 || header === undefined || launch === undefined || !/^@echo off$/i.test(header)) return null;
  const target = /^call "([^"]+)" %\*$/i.exec(launch)?.[1];
  if (target === undefined || !/^[A-Za-z]:\\/.test(target) || !/\.(?:cmd|bat|exe)$/i.test(target)) return null;
  // Never interpret shell expansion, metacharacters, or another command from a wrapper.
  // eslint-disable-next-line no-control-regex
  return /[<>|?*%!^&\u0000-\u001f]/.test(target) ? null : target;
}

export type ResolveFailure = 'cli-not-found' | 'node-not-found' | 'unsupported-shim';

export type ResolveResult =
  | { ok: true; command: ResolvedCommand; kind: 'exe' | 'node-script'; source: string }
  | { ok: false; code: ResolveFailure };

function resolveNode(shimDir: string | null, deps: ResolveDeps): string | null {
  const p = pathApi(deps.platform);
  if (shimDir !== null) {
    const local = p.join(shimDir, deps.platform === 'win32' ? 'node.exe' : 'node');
    if (deps.isFile(local)) return local;
  }
  const found = findOnPath('node', deps);
  if (found === null) return null;
  if (deps.platform === 'win32' && p.extname(found).toLowerCase() !== '.exe') return null;
  return found;
}

function isInside(p: path.PlatformPath, parent: string, child: string, platform: NodeJS.Platform): boolean {
  const norm = (value: string): string => (platform === 'win32' ? p.resolve(value).toLowerCase() : p.resolve(value));
  const rel = p.relative(norm(parent), norm(child));
  return rel.length > 0 && !rel.startsWith('..') && !p.isAbsolute(rel);
}

/**
 * Maps a command name or path to something spawnable with `shell:false`:
 * `.exe` directly, npm `.cmd` shims to `node <entry.js>`, `.js` to `node <file>`.
 */
export function resolveCommand(nameOrPath: string, deps: ResolveDeps = defaultResolveDeps()): ResolveResult {
  const p = pathApi(deps.platform);
  const source = findOnPath(nameOrPath, deps);
  if (source === null) return { ok: false, code: 'cli-not-found' };
  let found = source;
  const visited = new Set<string>();
  // Version managers may leave a small .cmd forwarder on PATH. Bound traversal and reject cycles.
  for (let hops = 0; hops <= 4; hops += 1) {
    const key = deps.platform === 'win32' ? p.resolve(found).toLowerCase() : p.resolve(found);
    if (visited.has(key)) return { ok: false, code: 'unsupported-shim' };
    visited.add(key);
    const ext = p.extname(found).toLowerCase();

    if (ext === '.exe' || ext === '.com' || (deps.platform !== 'win32' && ext === '')) {
      return { ok: true, command: { file: found, prefixArgs: [] }, kind: 'exe', source };
    }

    if (ext === '.js' || ext === '.cjs' || ext === '.mjs') {
      const node = resolveNode(null, deps);
      if (node === null) return { ok: false, code: 'node-not-found' };
      return { ok: true, command: { file: node, prefixArgs: [found] }, kind: 'node-script', source };
    }

    if (ext === '.cmd' || ext === '.bat') {
      let content: string;
      try {
        content = deps.readText(found);
      } catch {
        return { ok: false, code: 'unsupported-shim' };
      }
      const rel = parseCmdShim(content);
      if (rel !== null) {
        const shimDir = p.dirname(found);
        const entry = p.resolve(shimDir, rel);
        if (!isInside(p, shimDir, entry, deps.platform) || !deps.isFile(entry)) {
          return { ok: false, code: 'unsupported-shim' };
        }
        const node = resolveNode(shimDir, deps);
        if (node === null) return { ok: false, code: 'node-not-found' };
        return { ok: true, command: { file: node, prefixArgs: [entry] }, kind: 'node-script', source };
      }
      const forwarded = deps.platform === 'win32' ? parseCmdForwarder(content) : null;
      if (forwarded === null || !deps.isFile(forwarded)) return { ok: false, code: 'unsupported-shim' };
      found = forwarded;
      continue;
    }

    return { ok: false, code: 'unsupported-shim' };
  }
  return { ok: false, code: 'unsupported-shim' };
}

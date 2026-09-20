// The only module allowed to create child processes (enforced by ESLint).
// Rules: shell:false, windowsHide:true, argv arrays, env whitelist, timeout + tree kill.

import { spawn, type ChildProcess } from 'node:child_process';
import path from 'node:path';
import { createLineSplitter } from './text';

export interface ResolvedCommand {
  /** Absolute path of the executable actually spawned (an .exe or node.exe). */
  file: string;
  /** Arguments inserted before caller args (e.g. the JS entry of an npm shim). */
  prefixArgs: readonly string[];
}

export interface EnvPolicy {
  /** Variable names copied from the parent environment (case-insensitive). */
  allow: readonly string[];
  /** Names removed even when allowed (e.g. provider credential overrides). */
  remove?: readonly string[];
  /** Explicit values applied last (e.g. CODEX_HOME). */
  set?: Readonly<Record<string, string>>;
}

/** Variables a Windows CLI generally needs. Providers add their own allow/remove lists. */
export const BASE_ENV_ALLOW: readonly string[] = [
  'SystemRoot',
  'SystemDrive',
  'windir',
  'ComSpec',
  'PATH',
  'PATHEXT',
  'TEMP',
  'TMP',
  'USERPROFILE',
  'HOMEDRIVE',
  'HOMEPATH',
  'APPDATA',
  'LOCALAPPDATA',
  'ProgramData',
  'ProgramFiles',
  'ProgramFiles(x86)',
  'ProgramW6432',
  'CommonProgramFiles',
  'CommonProgramFiles(x86)',
  'NUMBER_OF_PROCESSORS',
  'PROCESSOR_ARCHITECTURE',
  'OS',
  'USERNAME',
  'USERDOMAIN',
  'COMPUTERNAME',
  'LANG',
  'LC_ALL',
];

export function buildChildEnv(parent: NodeJS.ProcessEnv, policy: EnvPolicy): Record<string, string> {
  const allow = new Set(policy.allow.map((name) => name.toUpperCase()));
  const remove = new Set((policy.remove ?? []).map((name) => name.toUpperCase()));
  const env: Record<string, string> = {};
  for (const [name, value] of Object.entries(parent)) {
    const upper = name.toUpperCase();
    if (value === undefined || !allow.has(upper) || remove.has(upper)) continue;
    if (Object.keys(env).some((existing) => existing.toUpperCase() === upper)) continue;
    env[name] = value;
  }
  for (const [name, value] of Object.entries(policy.set ?? {})) {
    const upper = name.toUpperCase();
    for (const existing of Object.keys(env)) {
      if (existing.toUpperCase() === upper) delete env[existing];
    }
    env[name] = value;
  }
  return env;
}

export type SpawnErrorCode = 'cli-not-found' | 'spawn-failed' | 'invalid-command';

export class SpawnError extends Error {
  readonly code: SpawnErrorCode;
  constructor(code: SpawnErrorCode, message: string, options?: { cause?: unknown }) {
    super(message, options);
    this.name = 'SpawnError';
    this.code = code;
  }
}

function assertSpawnable(command: ResolvedCommand, args: readonly string[]): void {
  if (!path.isAbsolute(command.file)) {
    throw new SpawnError('invalid-command', 'command must be an absolute path (use resolveCommand)');
  }
  const ext = path.extname(command.file).toLowerCase();
  if (ext === '.cmd' || ext === '.bat' || ext === '.ps1') {
    throw new SpawnError('invalid-command', 'script shims cannot run without a shell; resolve them first');
  }
  for (const arg of [...command.prefixArgs, ...args]) {
    if (typeof arg !== 'string' || arg.includes('\0')) {
      throw new SpawnError('invalid-command', 'arguments must be strings without NUL');
    }
  }
}

/** Kills a process and all descendants. Never throws. */
export async function killProcessTree(pid: number | undefined, platform: NodeJS.Platform = process.platform): Promise<void> {
  if (pid === undefined || !Number.isInteger(pid) || pid <= 0) return;
  if (platform !== 'win32') {
    try {
      process.kill(pid, 'SIGKILL');
    } catch {
      // Already gone.
    }
    return;
  }
  const systemRoot = process.env.SystemRoot ?? process.env.SYSTEMROOT ?? 'C:\\Windows';
  const taskkill = path.join(systemRoot, 'System32', 'taskkill.exe');
  await new Promise<void>((resolve) => {
    let done = false;
    const finish = (): void => {
      if (done) return;
      done = true;
      clearTimeout(guard);
      resolve();
    };
    const guard = setTimeout(finish, 5000);
    try {
      const killer = spawn(taskkill, ['/PID', String(pid), '/T', '/F'], {
        shell: false,
        windowsHide: true,
        stdio: 'ignore',
      });
      killer.on('error', () => {
        try {
          process.kill(pid);
        } catch {
          // Already gone.
        }
        finish();
      });
      killer.on('exit', finish);
    } catch {
      finish();
    }
  });
}

export interface RunOptions {
  env: EnvPolicy;
  cwd?: string;
  /** Hard limit; the process tree is killed when exceeded. */
  timeoutMs: number;
  signal?: AbortSignal;
  /** Written to stdin, which is then closed. stdin is closed immediately when omitted. */
  stdin?: string;
  /** Per-stream capture cap in bytes. Default 1 MiB. */
  maxOutputBytes?: number;
  /** Parent environment used for the whitelist. Default `process.env`. */
  parentEnv?: NodeJS.ProcessEnv;
}

export interface RunResult {
  exitCode: number | null;
  signal: NodeJS.Signals | null;
  stdout: string;
  stderr: string;
  timedOut: boolean;
  aborted: boolean;
  truncated: boolean;
  durationMs: number;
}

interface Capture {
  chunks: Buffer[];
  bytes: number;
  truncated: boolean;
}

function capture(stream: NodeJS.ReadableStream | null, cap: number): Capture {
  const state: Capture = { chunks: [], bytes: 0, truncated: false };
  stream?.on('data', (chunk: Buffer) => {
    const room = cap - state.bytes;
    if (room <= 0) {
      state.truncated = true;
      return;
    }
    const piece = chunk.length > room ? chunk.subarray(0, room) : chunk;
    if (chunk.length > room) state.truncated = true;
    state.chunks.push(piece);
    state.bytes += piece.length;
  });
  return state;
}

function spawnChild(command: ResolvedCommand, args: readonly string[], options: RunOptions): ChildProcess {
  assertSpawnable(command, args);
  return spawn(command.file, [...command.prefixArgs, ...args], {
    shell: false,
    windowsHide: true,
    cwd: options.cwd,
    env: buildChildEnv(options.parentEnv ?? process.env, options.env),
    stdio: ['pipe', 'pipe', 'pipe'],
  });
}

function toSpawnError(error: unknown): SpawnError {
  const code = (error as { code?: unknown }).code;
  if (code === 'ENOENT') return new SpawnError('cli-not-found', 'executable not found', { cause: error });
  return new SpawnError('spawn-failed', 'failed to start process', { cause: error });
}

/** Runs a command to completion. Resolves on exit/timeout/abort; rejects only with SpawnError. */
export function run(command: ResolvedCommand, args: readonly string[], options: RunOptions): Promise<RunResult> {
  const started = Date.now();
  const cap = options.maxOutputBytes ?? 1024 * 1024;

  return new Promise<RunResult>((resolve, reject) => {
    if (options.signal?.aborted === true) {
      resolve({
        exitCode: null,
        signal: null,
        stdout: '',
        stderr: '',
        timedOut: false,
        aborted: true,
        truncated: false,
        durationMs: 0,
      });
      return;
    }

    let child: ChildProcess;
    try {
      child = spawnChild(command, args, options);
    } catch (error) {
      reject(error instanceof SpawnError ? error : toSpawnError(error));
      return;
    }

    const out = capture(child.stdout, cap);
    const err = capture(child.stderr, cap);
    let timedOut = false;
    let aborted = false;
    let settled = false;
    let terminating = false;

    const terminate = (): void => {
      if (terminating) return;
      terminating = true;
      void killProcessTree(child.pid).then(() => {
        if (child.exitCode === null && child.signalCode === null) child.kill();
      });
    };
    const onAbort = (): void => {
      aborted = true;
      terminate();
    };
    const timer = setTimeout(() => {
      timedOut = true;
      terminate();
    }, options.timeoutMs);
    options.signal?.addEventListener('abort', onAbort, { once: true });

    const cleanup = (): void => {
      clearTimeout(timer);
      options.signal?.removeEventListener('abort', onAbort);
    };

    child.on('error', (error) => {
      if (settled) return;
      if (child.pid === undefined) {
        settled = true;
        cleanup();
        reject(toSpawnError(error));
      }
    });

    child.on('close', (code, signal) => {
      if (settled) return;
      settled = true;
      cleanup();
      resolve({
        exitCode: code,
        signal,
        stdout: Buffer.concat(out.chunks).toString('utf8'),
        stderr: Buffer.concat(err.chunks).toString('utf8'),
        timedOut,
        aborted,
        truncated: out.truncated || err.truncated,
        durationMs: Date.now() - started,
      });
    });

    child.stdin?.on('error', () => {
      // EPIPE when the child exits before reading stdin (V1-19).
    });
    if (options.stdin !== undefined) child.stdin?.end(options.stdin, 'utf8');
    else child.stdin?.end();
  });
}

export interface ExitInfo {
  exitCode: number | null;
  signal: NodeJS.Signals | null;
  timedOut: boolean;
  aborted: boolean;
}

export type LongLivedOptions = Omit<RunOptions, 'stdin' | 'maxOutputBytes'> & {
  /** Max length of one stdout/stderr line. Default 1 MiB. */
  maxLineLength?: number;
};

export interface LongLivedProcess {
  readonly pid: number | undefined;
  /** Writes `line` plus LF. Returns false once stdin is closed. */
  writeLine(line: string): boolean;
  writeJson(value: unknown): boolean;
  onStdoutLine(listener: (line: string, truncated: boolean) => void): () => void;
  onStderrLine(listener: (line: string, truncated: boolean) => void): () => void;
  closeStdin(): void;
  /** Resolves once when the process has exited (never rejects). */
  readonly exited: Promise<ExitInfo>;
  /** Kills the process tree and waits for exit. */
  kill(): Promise<ExitInfo>;
}

/**
 * Starts a process for line-delimited protocols (JSON-RPC over stdio).
 * Resolves after the OS reports the spawn; `timeoutMs` caps total lifetime.
 */
export function spawnLongLived(
  command: ResolvedCommand,
  args: readonly string[],
  options: LongLivedOptions,
): Promise<LongLivedProcess> {
  return new Promise<LongLivedProcess>((resolve, reject) => {
    if (options.signal?.aborted === true) {
      reject(new SpawnError('spawn-failed', 'aborted before start'));
      return;
    }
    let child: ChildProcess;
    try {
      child = spawnChild(command, args, options);
    } catch (error) {
      reject(error instanceof SpawnError ? error : toSpawnError(error));
      return;
    }

    const stdoutListeners = new Set<(line: string, truncated: boolean) => void>();
    const stderrListeners = new Set<(line: string, truncated: boolean) => void>();
    const splitterOptions = { maxLineLength: options.maxLineLength ?? 1024 * 1024 };
    const stdoutSplitter = createLineSplitter((line, truncated) => {
      for (const listener of stdoutListeners) listener(line, truncated);
    }, splitterOptions);
    const stderrSplitter = createLineSplitter((line, truncated) => {
      for (const listener of stderrListeners) listener(line, truncated);
    }, splitterOptions);
    child.stdout?.on('data', (chunk: Buffer) => stdoutSplitter.push(chunk));
    child.stderr?.on('data', (chunk: Buffer) => stderrSplitter.push(chunk));
    child.stdin?.on('error', () => {
      // Child closed its stdin; writes after this return false.
    });

    let timedOut = false;
    let aborted = false;
    let started = false;
    let stdinOpen = true;

    let resolveExit: (info: ExitInfo) => void = () => undefined;
    const exited = new Promise<ExitInfo>((res) => {
      resolveExit = res;
    });

    const terminate = (): void => {
      void killProcessTree(child.pid).then(() => {
        if (child.exitCode === null && child.signalCode === null) child.kill();
      });
    };
    const onAbort = (): void => {
      aborted = true;
      terminate();
    };
    const timer = setTimeout(() => {
      timedOut = true;
      terminate();
    }, options.timeoutMs);
    options.signal?.addEventListener('abort', onAbort, { once: true });

    child.on('close', (code, signal) => {
      clearTimeout(timer);
      options.signal?.removeEventListener('abort', onAbort);
      stdinOpen = false;
      stdoutSplitter.flush();
      stderrSplitter.flush();
      resolveExit({ exitCode: code, signal, timedOut, aborted });
    });

    child.on('error', (error) => {
      if (!started) {
        clearTimeout(timer);
        options.signal?.removeEventListener('abort', onAbort);
        reject(toSpawnError(error));
      }
    });

    child.on('spawn', () => {
      started = true;
      const handle: LongLivedProcess = {
        pid: child.pid,
        writeLine(line) {
          if (!stdinOpen || child.stdin === null || child.stdin.destroyed) return false;
          child.stdin.write(`${line}\n`, 'utf8');
          return true;
        },
        writeJson(value) {
          return handle.writeLine(JSON.stringify(value));
        },
        onStdoutLine(listener) {
          stdoutListeners.add(listener);
          return () => stdoutListeners.delete(listener);
        },
        onStderrLine(listener) {
          stderrListeners.add(listener);
          return () => stderrListeners.delete(listener);
        },
        closeStdin() {
          stdinOpen = false;
          child.stdin?.end();
        },
        exited,
        async kill() {
          if (child.exitCode === null && child.signalCode === null) terminate();
          return exited;
        },
      };
      resolve(handle);
    });
  });
}

import { appendFileSync, existsSync, mkdirSync, renameSync, rmSync, statSync } from 'node:fs';
import { dirname } from 'node:path';
import { maskSecrets, redact } from '../shared/mask';

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

const LEVEL_ORDER: Readonly<Record<LogLevel, number>> = { debug: 10, info: 20, warn: 30, error: 40 };

export interface LogRecord {
  at: number;
  level: LogLevel;
  scope: string;
  message: string;
  data?: unknown;
}

export interface LogSink {
  write(line: string, record: LogRecord): void;
}

export interface Logger {
  debug(message: string, data?: unknown): void;
  info(message: string, data?: unknown): void;
  warn(message: string, data?: unknown): void;
  error(message: string, data?: unknown): void;
  child(scope: string): Logger;
}

export interface LoggerOptions {
  sinks: readonly LogSink[];
  minLevel?: LogLevel;
  scope?: string;
  now?: () => number;
}

const MAX_DATA_CHARS = 4000;

/** Single log line; message and data are always masked (no tokens or raw e-mails). */
export function formatRecord(record: LogRecord): string {
  const time = new Date(record.at).toISOString();
  let line = `${time} ${record.level.toUpperCase()} [${record.scope}] ${maskSecrets(record.message)}`;
  if (record.data !== undefined) {
    let json: string;
    try {
      json = JSON.stringify(redact(record.data)) ?? 'undefined';
    } catch {
      json = '"[unserializable]"';
    }
    if (json.length > MAX_DATA_CHARS) json = `${json.slice(0, MAX_DATA_CHARS)}...`;
    line += ` ${json}`;
  }
  return line;
}

export function createLogger(options: LoggerOptions): Logger {
  const minLevel = LEVEL_ORDER[options.minLevel ?? 'info'];
  const scope = options.scope ?? 'app';
  const now = options.now ?? Date.now;

  const emit = (level: LogLevel, message: string, data: unknown): void => {
    if (LEVEL_ORDER[level] < minLevel) return;
    const record: LogRecord = { at: now(), level, scope, message };
    if (data !== undefined) record.data = data;
    const line = formatRecord(record);
    for (const sink of options.sinks) {
      try {
        sink.write(line, record);
      } catch {
        // A failing sink must never break the caller.
      }
    }
  };

  return {
    debug: (message, data) => emit('debug', message, data),
    info: (message, data) => emit('info', message, data),
    warn: (message, data) => emit('warn', message, data),
    error: (message, data) => emit('error', message, data),
    child: (childScope) => createLogger({ ...options, scope: `${scope}:${childScope}` }),
  };
}

export function createConsoleSink(): LogSink {
  return {
    write(line, record) {
      if (record.level === 'error') console.error(line);
      else if (record.level === 'warn') console.warn(line);
      else console.log(line);
    },
  };
}

export interface FileSinkOptions {
  maxBytes?: number;
  keep?: number;
}

/** Appends lines to `filePath`, rotating to `.1..keep` when `maxBytes` is exceeded. */
export function createFileSink(filePath: string, options: FileSinkOptions = {}): LogSink {
  const maxBytes = options.maxBytes ?? 1_000_000;
  const keep = Math.max(1, options.keep ?? 3);
  mkdirSync(dirname(filePath), { recursive: true });

  const rotate = (): void => {
    const oldest = `${filePath}.${keep}`;
    if (existsSync(oldest)) rmSync(oldest, { force: true });
    for (let i = keep - 1; i >= 1; i -= 1) {
      const from = `${filePath}.${i}`;
      if (existsSync(from)) renameSync(from, `${filePath}.${i + 1}`);
    }
    renameSync(filePath, `${filePath}.1`);
  };

  return {
    write(line) {
      if (existsSync(filePath) && statSync(filePath).size >= maxBytes) rotate();
      appendFileSync(filePath, `${line}\n`, { encoding: 'utf8' });
    },
  };
}

/** Logger that drops everything (tests, early bootstrap). */
export const nullLogger: Logger = {
  debug: () => undefined,
  info: () => undefined,
  warn: () => undefined,
  error: () => undefined,
  child: () => nullLogger,
};

import { existsSync, mkdtempSync, readFileSync, rmSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';
import { createFileSink, createLogger, formatRecord, type LogSink } from './log';

function memorySink(): LogSink & { lines: string[] } {
  const lines: string[] = [];
  return { lines, write: (line) => lines.push(line) };
}

const tempDirs: string[] = [];
afterEach(() => {
  for (const dir of tempDirs.splice(0)) rmSync(dir, { recursive: true, force: true });
});

describe('log', () => {
  it('masks message and data', () => {
    const line = formatRecord({
      at: 0,
      level: 'info',
      scope: 'codex',
      message: 'signed in as jane@example.com',
      data: { refreshToken: 'rt-secret', email: 'jane@example.com', note: 'Bearer abcdef123456' },
    });
    expect(line).toContain('j***@e***.com');
    expect(line).not.toContain('jane@example.com');
    expect(line).not.toContain('rt-secret');
    expect(line).not.toContain('abcdef123456');
    expect(line.startsWith('1970-01-01T00:00:00.000Z INFO [codex]')).toBe(true);
  });

  it('filters by level and scopes children', () => {
    const sink = memorySink();
    const logger = createLogger({ sinks: [sink], minLevel: 'warn', scope: 'main', now: () => 0 });
    logger.info('hidden');
    logger.child('ipc').warn('shown');
    expect(sink.lines).toHaveLength(1);
    expect(sink.lines[0]).toContain('[main:ipc] shown');
  });

  it('survives failing sinks and unserializable data', () => {
    const good = memorySink();
    const bad: LogSink = {
      write: () => {
        throw new Error('disk full');
      },
    };
    const logger = createLogger({ sinks: [bad, good] });
    const cyclic: Record<string, unknown> = {};
    cyclic.self = cyclic;
    logger.error('still logged', cyclic);
    expect(good.lines).toHaveLength(1);
  });

  it('rotates the log file', () => {
    const dir = mkdtempSync(path.join(os.tmpdir(), 'aiuw-log-'));
    tempDirs.push(dir);
    const file = path.join(dir, 'logs', 'main.log');
    const sink = createFileSink(file, { maxBytes: 64, keep: 2 });
    const logger = createLogger({ sinks: [sink], now: () => 0 });
    for (let i = 0; i < 6; i += 1) logger.info(`line number ${i} with some padding`);
    expect(existsSync(file)).toBe(true);
    expect(existsSync(`${file}.1`)).toBe(true);
    expect(existsSync(`${file}.3`)).toBe(false);
    expect(readFileSync(file, 'utf8')).toContain('line number 5');
  });
});

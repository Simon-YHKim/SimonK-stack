// End-to-end runs of resources/claude-bridge/* through the shared spawn helper, in temp dirs.

import { existsSync } from 'node:fs';
import { mkdir, mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { resolveCommand } from '../../cli/resolve';
import { BASE_ENV_ALLOW, run, type ResolvedCommand, type RunResult } from '../../cli/spawn';
import { bridgeKeyFor, parseBridgeRecord } from './bridge-data';

const SCRIPT_DIR = path.resolve('resources', 'claude-bridge');
const NODE_SCRIPT = path.join(SCRIPT_DIR, 'aiuw-claude-bridge.cjs');
const PS_SCRIPT = path.join(SCRIPT_DIR, 'aiuw-claude-bridge.ps1');
const KEY = '0123456789abcdef';
const node = resolveCommand('node');
const powershell = path.join(process.env.SystemRoot ?? 'C:\\Windows', 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe');
const hasPowershell = process.platform === 'win32' && existsSync(powershell);
const gitBash = [process.env.ProgramFiles, process.env['ProgramFiles(x86)']]
  .filter((dir): dir is string => typeof dir === 'string')
  .map((dir) => path.join(dir, 'Git', 'bin', 'bash.exe'))
  .find((file) => existsSync(file));

const future = Math.floor(Date.now() / 1000) + 3600;
const INPUT = {
  cwd: 'C:\\secret\\project',
  session_id: 'session-should-not-be-stored',
  transcript_path: 'C:\\secret\\transcript.jsonl',
  model: { id: 'claude-opus-5', display_name: 'Opus' },
  workspace: { current_dir: 'C:\\secret\\project' },
  cost: { total_cost_usd: 1.23 },
  rate_limits: {
    five_hour: { used_percentage: 23.5, resets_at: future },
    seven_day: { used_percentage: 41.2, resets_at: future + 86400 },
  },
};

let dir: string;

beforeEach(async () => {
  dir = await mkdtemp(path.join(os.tmpdir(), 'aiuw-bridge-'));
});

afterEach(async () => {
  await rm(dir, { recursive: true, force: true });
});

function runNodeBridge(stdin: string, args: string[], set: Record<string, string> = {}): Promise<RunResult> {
  if (!node.ok) throw new Error('node missing');
  const command: ResolvedCommand = { file: node.command.file, prefixArgs: [NODE_SCRIPT] };
  return run(command, args, { env: { allow: BASE_ENV_ALLOW, set }, timeoutMs: 20_000, stdin });
}

function runPsBridge(stdin: string, args: string[], set: Record<string, string> = {}): Promise<RunResult> {
  const command: ResolvedCommand = {
    file: powershell,
    prefixArgs: ['-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', PS_SCRIPT],
  };
  return run(command, args, { env: { allow: BASE_ENV_ALLOW, set }, timeoutMs: 30_000, stdin });
}

async function readRecordText(key: string): Promise<string> {
  return readFile(path.join(dir, `${key}.json`), 'utf8');
}

async function writeWrap(key: string, command: string): Promise<void> {
  await mkdir(dir, { recursive: true });
  await writeFile(
    path.join(dir, `${key}.wrap.json`),
    JSON.stringify({ v: 1, previous: { present: true, value: { type: 'command', command } } }),
  );
}

describe.runIf(node.ok)('node bridge script', () => {
  it('stores only rate limits and model, prints nothing without a wrapped command', async () => {
    const result = await runNodeBridge(JSON.stringify(INPUT), ['--key', KEY, '--out', dir]);
    expect(result).toMatchObject({ exitCode: 0, stdout: '', stderr: '' });
    const text = await readRecordText(KEY);
    for (const secret of ['secret', 'session-should-not-be-stored', 'transcript', 'total_cost']) {
      expect(text).not.toContain(secret);
    }
    const raw = JSON.parse(text) as Record<string, unknown>;
    expect(raw).toMatchObject({ v: 1, configDirHash: KEY, runtime: 'node', model: { id: 'claude-opus-5', display_name: 'Opus' } });
    expect(parseBridgeRecord(text, KEY)).toMatchObject({
      fiveHour: { usedPercentage: 23.5, resetsAtSec: future },
      sevenDay: { usedPercentage: 41.2, resetsAtSec: future + 86400 },
    });
    expect((await readdir(dir)).filter((name) => name.endsWith('.tmp'))).toEqual([]);
  });

  it('derives the key from CLAUDE_CONFIG_DIR exactly like the widget', async () => {
    const configDir = path.join(dir, 'Profiles', 'Claude', 'Acc1');
    await runNodeBridge(JSON.stringify(INPUT), ['--out', dir], { CLAUDE_CONFIG_DIR: `${configDir}\\` });
    expect(existsSync(path.join(dir, `${bridgeKeyFor(configDir)}.json`))).toBe(true);
  });

  it('keeps previous windows when rate_limits is absent and drops unexpired windows Claude Code removed', async () => {
    await runNodeBridge(JSON.stringify(INPUT), ['--key', KEY, '--out', dir]);
    const first = parseBridgeRecord(await readRecordText(KEY), KEY);

    await runNodeBridge(JSON.stringify({ model: INPUT.model }), ['--key', KEY, '--out', dir]);
    const second = parseBridgeRecord(await readRecordText(KEY), KEY);
    expect(second?.fiveHour).toEqual(first?.fiveHour);
    expect(second?.capturedAt).toBe(first?.capturedAt);
    expect(second!.seenAt).toBeGreaterThanOrEqual(first!.seenAt);

    const past = Math.floor(Date.now() / 1000) - 60;
    const expiredInput = { rate_limits: { five_hour: { used_percentage: 90, resets_at: past }, seven_day: INPUT.rate_limits.seven_day } };
    await runNodeBridge(JSON.stringify(expiredInput), ['--key', KEY, '--out', dir]);
    await runNodeBridge(JSON.stringify({ rate_limits: { seven_day: INPUT.rate_limits.seven_day } }), ['--key', KEY, '--out', dir]);
    expect(parseBridgeRecord(await readRecordText(KEY), KEY)?.fiveHour).toMatchObject({ usedPercentage: 90, resetsAtSec: past });

    await runNodeBridge(JSON.stringify(INPUT), ['--key', KEY, '--out', dir]);
    await runNodeBridge(JSON.stringify({ rate_limits: { seven_day: INPUT.rate_limits.seven_day } }), ['--key', KEY, '--out', dir]);
    expect(parseBridgeRecord(await readRecordText(KEY), KEY)?.fiveHour).toBeNull();
  });

  it('writes nothing for an invalid key or relative output dir', async () => {
    await runNodeBridge(JSON.stringify(INPUT), ['--key', '../../evil', '--out', dir]);
    await runNodeBridge(JSON.stringify(INPUT), ['--key', KEY, '--out', 'relative']);
    expect(await readdir(dir)).toEqual([]);
  });

  it.runIf(hasPowershell)(
    'passes stdin to the wrapped command and its stdout through unchanged (PowerShell)',
    async () => {
      await writeWrap(KEY, "$text = [Console]::In.ReadToEnd(); [Console]::Out.Write('wrapped:' + $text.Length)");
      const stdin = JSON.stringify(INPUT);
      const result = await runNodeBridge(stdin, ['--key', KEY, '--out', dir, '--shell', 'powershell']);
      expect(result.stdout).toBe(`wrapped:${stdin.length}`);
      expect(result.exitCode).toBe(0);
      expect(existsSync(path.join(dir, `${KEY}.json`))).toBe(true);
    },
    30_000,
  );

  it.runIf(gitBash !== undefined)(
    'runs the wrapped command through Git Bash and keeps its exit code',
    async () => {
      await writeWrap(KEY, "n=$(cat | wc -c); printf 'bash:%d' \"$n\"; exit 3");
      const stdin = JSON.stringify(INPUT);
      const result = await runNodeBridge(stdin, ['--key', KEY, '--out', dir, '--shell', 'bash'], {
        CLAUDE_CODE_GIT_BASH_PATH: gitBash ?? '',
      });
      expect(result.stdout).toBe(`bash:${Buffer.byteLength(stdin)}`);
      expect(result.exitCode).toBe(3);
    },
    30_000,
  );

  it('never runs a wrapped command that points back at the bridge', async () => {
    await writeWrap(KEY, "node 'C:/x/aiuw-claude-bridge.cjs' --key 0123456789abcdef");
    const result = await runNodeBridge(JSON.stringify(INPUT), ['--key', KEY, '--out', dir, '--shell', 'powershell']);
    expect(result).toMatchObject({ exitCode: 0, stdout: '' });
  });
});

describe.runIf(hasPowershell)('PowerShell bridge script', () => {
  it(
    'writes the same record format and key as the node bridge',
    async () => {
      const configDir = path.join(dir, 'Profiles', 'Claude', 'Acc1');
      const result = await runPsBridge(JSON.stringify(INPUT), ['-Out', dir], { CLAUDE_CONFIG_DIR: configDir });
      expect(result).toMatchObject({ exitCode: 0, stdout: '' });
      const key = bridgeKeyFor(configDir);
      const text = await readRecordText(key);
      expect(text).not.toContain('secret');
      expect(JSON.parse(text)).toMatchObject({ v: 1, configDirHash: key, runtime: 'powershell', model: { id: 'claude-opus-5' } });
      expect(parseBridgeRecord(text, key)).toMatchObject({
        fiveHour: { usedPercentage: 23.5, resetsAtSec: future },
        sevenDay: { usedPercentage: 41.2, resetsAtSec: future + 86400 },
      });
    },
    30_000,
  );

  it(
    'keeps previous windows when rate_limits is absent and runs the wrapped command',
    async () => {
      await runPsBridge(JSON.stringify(INPUT), ['-Key', KEY, '-Out', dir]);
      const first = parseBridgeRecord(await readRecordText(KEY), KEY);
      await writeWrap(KEY, "$text = [Console]::In.ReadToEnd(); [Console]::Out.Write('ps:' + $text.Length)");
      const stdin = JSON.stringify({ model: INPUT.model });
      const result = await runPsBridge(stdin, ['-Key', KEY, '-Out', dir, '-Shell', 'powershell']);
      expect(result.stdout).toBe(`ps:${stdin.length}`);
      const second = parseBridgeRecord(await readRecordText(KEY), KEY);
      expect(second?.fiveHour).toEqual(first?.fiveHour);
      expect(second?.sevenDay).toEqual(first?.sevenDay);
    },
    60_000,
  );
});

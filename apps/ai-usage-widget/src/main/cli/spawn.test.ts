import { describe, expect, it } from 'vitest';
import { createJsonRpcClient, transportFromProcess } from './jsonrpc';
import {
  BASE_ENV_ALLOW,
  SpawnError,
  buildChildEnv,
  killProcessTree,
  run,
  spawnLongLived,
  type ResolvedCommand,
} from './spawn';

const NODE: ResolvedCommand = { file: process.execPath, prefixArgs: [] };
const ENV = { allow: BASE_ENV_ALLOW };

function isAlive(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

async function waitUntil(predicate: () => boolean, timeoutMs: number): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (predicate()) return true;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  return predicate();
}

describe('buildChildEnv', () => {
  it('copies only allowed names, case-insensitively, then applies remove and set', () => {
    const env = buildChildEnv(
      { Path: 'C:\\bin', SystemRoot: 'C:\\Windows', SECRET_TOKEN: 's', ANTHROPIC_API_KEY: 'k', codex_home: 'old' },
      { allow: ['PATH', 'SYSTEMROOT', 'ANTHROPIC_API_KEY', 'CODEX_HOME'], remove: ['anthropic_api_key'], set: { CODEX_HOME: 'C:\\p' } },
    );
    expect(env).toEqual({ Path: 'C:\\bin', SystemRoot: 'C:\\Windows', CODEX_HOME: 'C:\\p' });
  });
});

describe('run', () => {
  it('captures stdout, stderr and exit code', async () => {
    const result = await run(
      NODE,
      ['-e', "process.stdout.write('out');process.stderr.write('err');process.exit(3)"],
      { env: ENV, timeoutMs: 15_000 },
    );
    expect(result).toMatchObject({ exitCode: 3, stdout: 'out', stderr: 'err', timedOut: false, aborted: false });
  });

  it('writes stdin', async () => {
    const result = await run(
      NODE,
      ['-e', "let d='';process.stdin.on('data',c=>d+=c).on('end',()=>process.stdout.write(d.toUpperCase()))"],
      { env: ENV, timeoutMs: 15_000, stdin: 'hello' },
    );
    expect(result.stdout).toBe('HELLO');
  });

  it('passes only whitelisted environment variables', async () => {
    const result = await run(NODE, ['-e', 'process.stdout.write(JSON.stringify(Object.keys(process.env)))'], {
      env: { allow: BASE_ENV_ALLOW, set: { CODEX_HOME: 'C:\\profile' } },
      timeoutMs: 15_000,
      parentEnv: { ...process.env, SECRET_TOKEN: 'nope', ANTHROPIC_API_KEY: 'nope' },
    });
    const keys = (JSON.parse(result.stdout) as string[]).map((k) => k.toUpperCase());
    expect(keys).toContain('CODEX_HOME');
    expect(keys).not.toContain('SECRET_TOKEN');
    expect(keys).not.toContain('ANTHROPIC_API_KEY');
  });

  it('kills the whole process tree on timeout', async () => {
    const script =
      "const c=require('child_process').spawn(process.execPath,['-e','setInterval(()=>{},1000)'],{stdio:'ignore',windowsHide:true});" +
      "process.stdout.write(String(c.pid));setInterval(()=>{},1000);";
    const result = await run(NODE, ['-e', script], { env: ENV, timeoutMs: 1500 });
    expect(result.timedOut).toBe(true);
    const grandchild = Number(result.stdout.trim());
    expect(Number.isInteger(grandchild) && grandchild > 0).toBe(true);
    expect(await waitUntil(() => !isAlive(grandchild), 5000)).toBe(true);
  }, 20_000);

  it('stops on abort', async () => {
    const controller = new AbortController();
    setTimeout(() => controller.abort(), 200);
    const result = await run(NODE, ['-e', 'setInterval(()=>{},1000)'], {
      env: ENV,
      timeoutMs: 15_000,
      signal: controller.signal,
    });
    expect(result.aborted).toBe(true);
    expect(result.durationMs).toBeLessThan(10_000);
  });

  it('resolves immediately when already aborted', async () => {
    const controller = new AbortController();
    controller.abort();
    const result = await run(NODE, ['-e', ''], { env: ENV, timeoutMs: 1000, signal: controller.signal });
    expect(result.aborted).toBe(true);
    expect(result.exitCode).toBeNull();
  });

  it('caps captured output', async () => {
    const result = await run(NODE, ['-e', "process.stdout.write('x'.repeat(5000))"], {
      env: ENV,
      timeoutMs: 15_000,
      maxOutputBytes: 100,
    });
    expect(result.stdout).toHaveLength(100);
    expect(result.truncated).toBe(true);
  });

  it('rejects missing executables with cli-not-found', async () => {
    const missing: ResolvedCommand = { file: 'C:\\definitely\\missing\\tool.exe', prefixArgs: [] };
    await expect(run(missing, [], { env: ENV, timeoutMs: 5000 })).rejects.toMatchObject({ code: 'cli-not-found' });
  });

  it('refuses shell scripts and relative commands', async () => {
    await expect(run({ file: 'C:\\x\\codex.cmd', prefixArgs: [] }, [], { env: ENV, timeoutMs: 1000 })).rejects.toBeInstanceOf(
      SpawnError,
    );
    await expect(run({ file: 'node', prefixArgs: [] }, [], { env: ENV, timeoutMs: 1000 })).rejects.toMatchObject({
      code: 'invalid-command',
    });
  });
});

describe('spawnLongLived', () => {
  it('exchanges JSON lines and can be killed', async () => {
    const server =
      "const rl=require('readline').createInterface({input:process.stdin});" +
      "rl.on('line',l=>{const m=JSON.parse(l);" +
      "if(m.method==='ping')process.stdout.write(JSON.stringify({id:m.id,result:{pong:m.params.n}})+'\\n');" +
      "if(m.method==='hello')process.stdout.write(JSON.stringify({method:'note',params:{v:1}})+'\\n');});";
    const proc = await spawnLongLived(NODE, ['-e', server], { env: ENV, timeoutMs: 20_000 });
    const client = createJsonRpcClient(transportFromProcess(proc), { dialect: 'codex', defaultTimeoutMs: 5000 });
    const notes: unknown[] = [];
    client.onNotification('note', (params) => notes.push(params));
    await expect(client.request('ping', { n: 3 })).resolves.toEqual({ pong: 3 });
    client.notify('hello');
    expect(await waitUntil(() => notes.length === 1, 3000)).toBe(true);
    const exit = await proc.kill();
    expect(exit.exitCode === 0).toBe(false);
    expect(client.isClosed).toBe(true);
    expect(proc.writeLine('late')).toBe(false);
  }, 20_000);

  it('enforces the lifetime timeout', async () => {
    const proc = await spawnLongLived(NODE, ['-e', 'setInterval(()=>{},1000)'], { env: ENV, timeoutMs: 800 });
    const exit = await proc.exited;
    expect(exit.timedOut).toBe(true);
  }, 15_000);

  it('rejects when the executable is missing', async () => {
    await expect(
      spawnLongLived({ file: 'C:\\definitely\\missing\\tool.exe', prefixArgs: [] }, [], { env: ENV, timeoutMs: 1000 }),
    ).rejects.toMatchObject({ code: 'cli-not-found' });
  });
});

describe('killProcessTree', () => {
  it('ignores invalid and already-exited pids', async () => {
    await expect(killProcessTree(undefined)).resolves.toBeUndefined();
    await expect(killProcessTree(-5)).resolves.toBeUndefined();
    const result = await run(NODE, ['-e', ''], { env: ENV, timeoutMs: 5000 });
    expect(result.exitCode).toBe(0);
  });
});

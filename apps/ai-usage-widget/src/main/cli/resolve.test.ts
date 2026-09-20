import { describe, expect, it } from 'vitest';
import { findOnPath, parseCmdShim, resolveCommand, type ResolveDeps } from './resolve';

// Template emitted by npm's cmd-shim (same layout as the installed codex.cmd).
const NPM_SHIM = [
  '@ECHO off',
  'GOTO start',
  ':find_dp0',
  'SET dp0=%~dp0',
  'EXIT /b',
  ':start',
  'SETLOCAL',
  'CALL :find_dp0',
  '',
  'IF EXIST "%dp0%\\node.exe" (',
  '  SET "_prog=%dp0%\\node.exe"',
  ') ELSE (',
  '  SET "_prog=node"',
  '  SET PATHEXT=%PATHEXT:;.JS;=;%',
  ')',
  '',
  'endLocal & goto #_undefined_# 2>NUL || title %COMSPEC% & "%_prog%"  "%dp0%\\node_modules\\@openai\\codex\\bin\\codex.js" %*',
].join('\r\n');

const LEGACY_SHIM = '@IF EXIST "%~dp0\\node.exe" (\r\n  "%~dp0\\node.exe"  "%~dp0\\node_modules\\pkg\\cli.js" %*\r\n)';

function fakeDeps(files: Record<string, string>, env: Record<string, string>): ResolveDeps {
  const map = new Map(Object.entries(files).map(([k, v]) => [k.toLowerCase(), v]));
  return {
    env,
    platform: 'win32',
    isFile: (p) => map.has(p.toLowerCase()),
    readText: (p) => {
      const value = map.get(p.toLowerCase());
      if (value === undefined) throw new Error('ENOENT');
      return value;
    },
  };
}

const ENV = { Path: 'C:\\Windows\\System32;C:\\npm;C:\\nodejs', PATHEXT: '.COM;.EXE;.BAT;.CMD' };

describe('parseCmdShim', () => {
  it('extracts the JS entry from npm shims', () => {
    expect(parseCmdShim(NPM_SHIM)).toBe('node_modules\\@openai\\codex\\bin\\codex.js');
    expect(parseCmdShim(LEGACY_SHIM)).toBe('node_modules\\pkg\\cli.js');
    expect(parseCmdShim('@echo off\r\nstart something.exe')).toBeNull();
  });
});

describe('findOnPath', () => {
  it('honours PATHEXT order and absolute paths', () => {
    const deps = fakeDeps({ 'C:\\npm\\codex.cmd': '', 'C:\\npm\\codex.ps1': '', 'C:\\tools\\grok.exe': '' }, ENV);
    expect(findOnPath('codex', deps)).toBe('C:\\npm\\codex.cmd');
    expect(findOnPath('C:\\tools\\grok.exe', deps)).toBe('C:\\tools\\grok.exe');
    expect(findOnPath('C:\\tools\\grok', deps)).toBe('C:\\tools\\grok.exe');
    expect(findOnPath('missing', deps)).toBeNull();
  });
});

describe('resolveCommand', () => {
  it('runs .exe directly', () => {
    const deps = fakeDeps({ 'C:\\Users\\u\\.local\\bin\\claude.exe': '' }, { ...ENV, Path: 'C:\\Users\\u\\.local\\bin' });
    expect(resolveCommand('claude', deps)).toEqual({
      ok: true,
      kind: 'exe',
      source: 'C:\\Users\\u\\.local\\bin\\claude.exe',
      command: { file: 'C:\\Users\\u\\.local\\bin\\claude.exe', prefixArgs: [] },
    });
  });

  it('maps an npm .cmd shim to node + JS entry using PATH node', () => {
    const deps = fakeDeps(
      {
        'C:\\npm\\codex.cmd': NPM_SHIM,
        'C:\\npm\\node_modules\\@openai\\codex\\bin\\codex.js': '',
        'C:\\nodejs\\node.exe': '',
      },
      ENV,
    );
    expect(resolveCommand('codex', deps)).toEqual({
      ok: true,
      kind: 'node-script',
      source: 'C:\\npm\\codex.cmd',
      command: { file: 'C:\\nodejs\\node.exe', prefixArgs: ['C:\\npm\\node_modules\\@openai\\codex\\bin\\codex.js'] },
    });
  });

  it('prefers node.exe next to the shim', () => {
    const deps = fakeDeps(
      {
        'C:\\npm\\codex.cmd': NPM_SHIM,
        'C:\\npm\\node.exe': '',
        'C:\\npm\\node_modules\\@openai\\codex\\bin\\codex.js': '',
        'C:\\nodejs\\node.exe': '',
      },
      ENV,
    );
    const result = resolveCommand('codex', deps);
    expect(result.ok && result.command.file).toBe('C:\\npm\\node.exe');
  });

  it('reports node-not-found, cli-not-found and unsupported shims', () => {
    const noNode = fakeDeps(
      { 'C:\\npm\\codex.cmd': NPM_SHIM, 'C:\\npm\\node_modules\\@openai\\codex\\bin\\codex.js': '' },
      ENV,
    );
    expect(resolveCommand('codex', noNode)).toEqual({ ok: false, code: 'node-not-found' });
    expect(resolveCommand('codex', fakeDeps({}, ENV))).toEqual({ ok: false, code: 'cli-not-found' });
    const missingEntry = fakeDeps({ 'C:\\npm\\codex.cmd': NPM_SHIM, 'C:\\nodejs\\node.exe': '' }, ENV);
    expect(resolveCommand('codex', missingEntry)).toEqual({ ok: false, code: 'unsupported-shim' });
    const escaping = fakeDeps(
      { 'C:\\npm\\evil.cmd': '"%~dp0\\..\\outside\\x.js" %*', 'C:\\outside\\x.js': '', 'C:\\nodejs\\node.exe': '' },
      ENV,
    );
    expect(resolveCommand('evil', escaping)).toEqual({ ok: false, code: 'unsupported-shim' });
    const ps1 = fakeDeps({ 'C:\\npm\\tool.ps1': '' }, ENV);
    expect(resolveCommand('C:\\npm\\tool.ps1', ps1)).toEqual({ ok: false, code: 'unsupported-shim' });
  });
});

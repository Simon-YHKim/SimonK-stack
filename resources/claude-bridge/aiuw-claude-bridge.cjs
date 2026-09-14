#!/usr/bin/env node
// AI Usage Widget - Claude Code statusLine bridge (node runtime).
//
// Claude Code runs this as `statusLine.command` and pipes its statusline JSON
// to stdin. Only `rate_limits` (five_hour / seven_day used_percentage and
// resets_at, documented at code.claude.com/docs/en/statusline) plus the model
// id/name are written to `<out>/<key>.json`. No prompts, paths, session ids or
// transcript data are stored. If the installer recorded a pre-existing
// statusLine command in `<out>/<key>.wrap.json`, that command runs with the same
// stdin and its stdout passes through unchanged; otherwise nothing is printed.
//
// Keep this file dependency-free and compatible with old Node versions.
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const childProcess = require('child_process');

const MARKER = 'aiuw-claude-bridge';
const RECORD_VERSION = 1;
const DEFAULT_PROFILE_MARKER = '~/.claude default';
const KEY_RE = /^[0-9a-f]{16}$/;
const MAX_STDIN_BYTES = 8 * 1024 * 1024;
const MAX_FILE_BYTES = 256 * 1024;
const WRAP_TIMEOUT_MS = 30000;
const WINDOW_NAMES = ['five_hour', 'seven_day'];

function parseArgs(argv) {
  const out = { key: null, out: null, shell: 'auto' };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];
    if (arg === '--key' && next !== undefined) {
      out.key = next;
      i += 1;
    } else if (arg === '--out' && next !== undefined) {
      out.out = next;
      i += 1;
    } else if (arg === '--shell' && next !== undefined) {
      out.shell = next;
      i += 1;
    }
  }
  return out;
}

function normalizeConfigDir(dir) {
  let full = path.win32.resolve(dir).replace(/\//g, '\\');
  if (full.length > 3) full = full.replace(/\\+$/, '');
  return full.toLowerCase();
}

function keyForConfigDir(configDir) {
  const text = configDir ? normalizeConfigDir(configDir) : DEFAULT_PROFILE_MARKER;
  return crypto.createHash('sha256').update(text, 'utf8').digest('hex').slice(0, 16);
}

function finiteOrNull(value) {
  return typeof value === 'number' && isFinite(value) ? value : null;
}

function isObject(value) {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function shortString(value) {
  return typeof value === 'string' && value.length > 0 && value.length <= 100 ? value : undefined;
}

function readJsonFile(filePath) {
  try {
    const stat = fs.statSync(filePath);
    if (!stat.isFile() || stat.size > MAX_FILE_BYTES) return null;
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (_error) {
    return null;
  }
}

function writeFileAtomic(filePath, text) {
  const tmp = filePath + '.' + process.pid + '.' + Date.now() + '.tmp';
  try {
    fs.writeFileSync(tmp, text, { encoding: 'utf8' });
    fs.renameSync(tmp, filePath);
  } catch (error) {
    try {
      fs.unlinkSync(tmp);
    } catch (_ignored) {
      // Nothing to clean up.
    }
    throw error;
  }
}

function previousWindows(previous, key) {
  if (!isObject(previous) || previous.v !== RECORD_VERSION || previous.configDirHash !== key) return {};
  return isObject(previous.rate_limits) ? previous.rate_limits : {};
}

/**
 * Merge rules:
 * - window present in stdin: replace, stamped with captured_at = now;
 * - rate_limits present but a window missing: Claude Code drops a window after
 *   its resets_at, so keep the previous one only if it already expired;
 * - rate_limits absent (no API response yet, or not a Pro/Max account): keep previous windows.
 */
function buildRecord(input, previous, key, nowMs) {
  const prevWindows = previousWindows(previous, key);
  const rateLimits = isObject(input) && isObject(input.rate_limits) ? input.rate_limits : null;
  const windows = {};
  let updated = false;
  for (const name of WINDOW_NAMES) {
    const incoming = rateLimits ? rateLimits[name] : undefined;
    if (isObject(incoming)) {
      const used = finiteOrNull(incoming.used_percentage);
      const resets = finiteOrNull(incoming.resets_at);
      if (used !== null || resets !== null) {
        windows[name] = { used_percentage: used, resets_at: resets, captured_at: nowMs };
        updated = true;
        continue;
      }
    }
    const prev = prevWindows[name];
    if (!isObject(prev)) continue;
    const prevResets = finiteOrNull(prev.resets_at);
    const expired = prevResets !== null && prevResets * 1000 <= nowMs;
    if (rateLimits === null || expired) windows[name] = prev;
  }
  const record = {
    v: RECORD_VERSION,
    configDirHash: key,
    seenAt: nowMs,
    capturedAt: updated
      ? nowMs
      : isObject(previous) && previous.configDirHash === key
        ? finiteOrNull(previous.capturedAt)
        : null,
    rate_limits: windows,
    runtime: 'node',
  };
  if (isObject(input) && isObject(input.model)) {
    const model = {};
    const id = shortString(input.model.id);
    const name = shortString(input.model.display_name);
    if (id !== undefined) model.id = id;
    if (name !== undefined) model.display_name = name;
    if (id !== undefined || name !== undefined) record.model = model;
  }
  return record;
}

function recordReading(stdinBuffer, args) {
  let input = null;
  try {
    input = JSON.parse(stdinBuffer.toString('utf8'));
  } catch (_error) {
    input = null;
  }
  const recordPath = path.join(args.out, args.key + '.json');
  const record = buildRecord(input, readJsonFile(recordPath), args.key, Date.now());
  fs.mkdirSync(args.out, { recursive: true });
  writeFileAtomic(recordPath, JSON.stringify(record));
}

function wrappedCommand(args) {
  const wrap = readJsonFile(path.join(args.out, args.key + '.wrap.json'));
  if (!isObject(wrap) || wrap.v !== RECORD_VERSION || !isObject(wrap.previous)) return null;
  const previous = wrap.previous;
  if (previous.present !== true || !isObject(previous.value)) return null;
  const command = previous.value.command;
  if (typeof command !== 'string' || command.trim().length === 0 || command.indexOf(MARKER) !== -1) return null;
  return command;
}

function isFile(filePath) {
  try {
    return fs.statSync(filePath).isFile();
  } catch (_error) {
    return false;
  }
}

// Mirrors Claude Code's documented choice: Git Bash when installed, PowerShell otherwise.
function findGitBash(env) {
  const candidates = [];
  if (env.CLAUDE_CODE_GIT_BASH_PATH) candidates.push(env.CLAUDE_CODE_GIT_BASH_PATH);
  const pathVar = env.PATH || env.Path || '';
  for (const rawDir of pathVar.split(';')) {
    const dir = rawDir.trim().replace(/^"(.*)"$/, '$1');
    if (!dir || !path.win32.isAbsolute(dir) || !isFile(path.win32.join(dir, 'git.exe'))) continue;
    const parent = path.win32.dirname(dir);
    candidates.push(path.win32.join(parent, 'bin', 'bash.exe'));
    candidates.push(path.win32.join(path.win32.dirname(parent), 'bin', 'bash.exe'));
  }
  if (env.ProgramFiles) candidates.push(path.win32.join(env.ProgramFiles, 'Git', 'bin', 'bash.exe'));
  if (env['ProgramFiles(x86)']) candidates.push(path.win32.join(env['ProgramFiles(x86)'], 'Git', 'bin', 'bash.exe'));
  for (const candidate of candidates) {
    if (isFile(candidate)) return candidate;
  }
  return null;
}

function powershellPath(env) {
  const root = env.SystemRoot || env.windir || 'C:\\Windows';
  return path.win32.join(root, 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe');
}

function shellInvocation(command, mode, env) {
  const bash = mode === 'powershell' ? null : findGitBash(env);
  if (bash !== null) return { file: bash, args: ['-c', command] };
  if (mode === 'bash') return null;
  const encoded = Buffer.from(command, 'utf16le').toString('base64');
  return { file: powershellPath(env), args: ['-NoProfile', '-NonInteractive', '-EncodedCommand', encoded] };
}

function runWrapped(stdinBuffer, args) {
  let command = null;
  try {
    command = wrappedCommand(args);
  } catch (_error) {
    command = null;
  }
  if (command === null) return;
  const invocation = shellInvocation(command, args.shell, process.env);
  if (invocation === null) return;
  let child;
  try {
    child = childProcess.spawn(invocation.file, invocation.args, {
      stdio: ['pipe', 'inherit', 'inherit'],
      windowsHide: true,
    });
  } catch (_error) {
    return;
  }
  const guard = setTimeout(function () {
    try {
      child.kill();
    } catch (_ignored) {
      // Already gone.
    }
  }, WRAP_TIMEOUT_MS);
  child.on('error', function () {
    clearTimeout(guard);
  });
  child.on('exit', function (code) {
    clearTimeout(guard);
    process.exitCode = code === null ? 1 : code;
  });
  child.stdin.on('error', function () {
    // The wrapped command may exit without reading stdin.
  });
  child.stdin.end(stdinBuffer);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.key === null) args.key = keyForConfigDir(process.env.CLAUDE_CONFIG_DIR || null);
  if (args.out === null && process.env.LOCALAPPDATA) {
    args.out = path.join(process.env.LOCALAPPDATA, 'AIUsageWidget', 'bridge', 'claude');
  }
  const valid = KEY_RE.test(args.key) && typeof args.out === 'string' && path.isAbsolute(args.out);
  const chunks = [];
  let size = 0;
  let overflow = false;
  process.stdin.on('data', function (chunk) {
    size += chunk.length;
    if (size > MAX_STDIN_BYTES) {
      overflow = true;
      return;
    }
    chunks.push(chunk);
  });
  process.stdin.on('error', function () {
    // Treat as end of input.
  });
  process.stdin.on('end', function () {
    const buffer = Buffer.concat(chunks);
    if (valid && !overflow) {
      try {
        recordReading(buffer, args);
      } catch (_error) {
        // Recording must never break the user's status line.
      }
    }
    if (valid) runWrapped(buffer, args);
  });
}

if (require.main === module) main();

module.exports = { buildRecord, keyForConfigDir, normalizeConfigDir, parseArgs };

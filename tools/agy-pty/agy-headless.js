#!/usr/bin/env node
// agy-headless.js — Run Antigravity (agy) headless by giving it a ConPTY.
//
// WHY: `agy -p` only renders its answer when attached to a real terminal (PTY).
// When the hub daemon spawns it with redirected stdout, agy emits ~0 useful
// bytes (no stdout/log/json output contract). This wrapper spawns agy inside a
// node-pty pseudo-terminal (ConPTY), captures the rendered output, strips the
// TUI chrome, and prints the clean answer to real stdout for the daemon to read.
//
// Verified 2026-06-15: node-pty ConPTY makes `agy -p` answer (4/5 probe configs).
// First call can flake to an empty render (cold start) → we retry up to MAX_TRIES.
// Do NOT set conptyInheritCursor:true — it crashes node-pty (AttachConsole failed).
//
// USAGE:  node agy-headless.js "<prompt>"
//   env AGY_BIN         full path to agy.exe (else resolved via `where agy`)
//   env AGY_MODEL       optional model id passed as --model
//   env AGY_CWD         working dir (default: process.cwd())
//   env AGY_TIMEOUT_MS  per-attempt hard kill (default 180000)
//   env AGY_SETTLE_MS   idle time after last output before reading (default 2500)
//   env AGY_TRIES       max attempts on empty answer (default 3)
//   env AGY_RAW_DUMP    if set, write last raw PTY capture to this file (debug)

const fs = require('fs');
const cp = require('child_process');

let pty;
try {
  pty = require('node-pty');
} catch (e) {
  process.stderr.write('FATAL: node-pty failed to load: ' + e.message + '\n');
  process.exit(3);
}

const prompt = process.argv.slice(2).join(' ').trim();
if (!prompt) {
  process.stderr.write('usage: node agy-headless.js "<prompt>"\n');
  process.exit(2);
}

const TIMEOUT_MS = parseInt(process.env.AGY_TIMEOUT_MS || '90000', 10);
const MAX_TRIES = parseInt(process.env.AGY_TRIES || '3', 10);
const cwd = process.env.AGY_CWD || process.cwd();

function resolveAgy() {
  if (process.env.AGY_BIN && fs.existsSync(process.env.AGY_BIN)) return process.env.AGY_BIN;
  try {
    const cmd = process.platform === 'win32' ? 'where agy' : 'command -v agy';
    const out = cp.execSync(cmd, { encoding: 'utf8' });
    const hits = out.split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
    return hits.find((h) => /\.exe$/i.test(h)) || hits[0] || 'agy';
  } catch (_) {
    return 'agy';
  }
}
const AGY_BIN = resolveAgy();

function stripAnsi(s) {
  return s
    .replace(/\x1B\][^\x07\x1B]*(?:\x07|\x1B\\)/g, '')
    .replace(/\x1B[P^_].*?\x1B\\/gs, '')
    .replace(/\x1B\[[0-9;?]*[ -/]*[@-~]/g, '')
    .replace(/\x1B[@-Z\\-_]/g, '')
    .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, '')
    .replace(/\r/g, '');
}

function extractAnswer(raw) {
  const t = stripAnsi(raw);
  let lines = t.split('\n').map((l) => l.replace(/[─━│┃▸▄▀▌▐█◇◆•]/g, '').trimEnd());
  const drop = [
    /Antigravity CLI/i, /Google AI Pro/i, /Gemini .*\(High\)/i, /for shortcuts/i,
    /Thought for /i, /Prioritizing Tool Usage/i, /tokens?$/i, /^\s*\?/, /hwanydanh@/i,
  ];
  lines = lines.filter((l) => {
    const s = l.trim();
    if (!s) return false;
    if (s === prompt.trim()) return false;
    if (/^>\s*/.test(s)) return false;
    if (drop.some((re) => re.test(s))) return false;
    return true;
  });
  return lines.join('\n').trim();
}

function attempt() {
  return new Promise((resolve) => {
    const args = ['-p', prompt, '--dangerously-skip-permissions'];
    if (process.env.AGY_MODEL) args.push('--model', process.env.AGY_MODEL);
    let term;
    try {
      // AGY_USE_CONPTY=0 -> winpty backend. ConPTY needs the parent to have a Win32
      // console; under PowerShell Start-Job (no console host) it dies with
      // "AttachConsole failed" (observed 2026-07-02, AG seat hard-fail). winpty
      // spawns its own hidden console agent, so it works console-less.
      const useConpty = process.env.AGY_USE_CONPTY !== '0';
      term = pty.spawn(AGY_BIN, args, {
        name: 'xterm-256color', cols: 120, rows: 40, cwd, env: process.env, useConpty,
      });
    } catch (e) {
      return resolve({ answer: '', raw: '', err: e.message });
    }
    let buf = '';
    let finished = false;
    const done = () => {
      if (finished) return;
      finished = true;
      clearTimeout(hard);
      if (process.env.AGY_RAW_DUMP) { try { fs.writeFileSync(process.env.AGY_RAW_DUMP, buf); } catch (_) {} }
      resolve({ answer: extractAnswer(buf), raw: buf });
    };
    // agy -p prints its answer (after a few seconds of "thinking") then exits on
    // its own. Rely on onExit; do NOT kill on idle — the thinking pause is silent
    // and an idle-kill truncates before the answer arrives. hard timeout is only a
    // backstop for a true hang.
    term.onData((d) => { buf += d; });
    term.onExit(done);
    const hard = setTimeout(() => { try { term.kill(); } catch (_) {} done(); }, TIMEOUT_MS);
  });
}

(async () => {
  let last = { answer: '', raw: '' };
  for (let i = 0; i < MAX_TRIES; i++) {
    last = await attempt();
    if (last.answer) {
      process.stdout.write(last.answer.endsWith('\n') ? last.answer : last.answer + '\n');
      process.exit(0);
    }
  }
  process.stderr.write('AGY_EMPTY after ' + MAX_TRIES + ' tries (last raw ' + last.raw.length + ' bytes)\n');
  process.exit(1);
})();

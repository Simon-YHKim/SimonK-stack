// probe.js — try several node-pty configs to find one where `agy -p` actually answers.
const pty = require('node-pty');
const cp = require('child_process');

const AGY = (() => {
  try {
    const out = cp.execSync('where agy', { encoding: 'utf8' });
    return out.split(/\r?\n/).map(s => s.trim()).filter(Boolean).find(h => /\.exe$/i.test(h));
  } catch { return 'agy'; }
})();

const PROMPT = 'Reply with one word: PONG';

function strip(s) {
  return s.replace(/\x1B\][^\x07\x1B]*(?:\x07|\x1B\\)/g, '')
          .replace(/\x1B\[[0-9;?]*[ -/]*[@-~]/g, '')
          .replace(/\x1B[@-Z\\-_]/g, '')
          .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, '')
          .replace(/\r/g, '');
}

function run(label, { skipPerms, nudgeStdin, inheritCursor, term }) {
  return new Promise((resolve) => {
    const args = ['-p', PROMPT];
    if (skipPerms) args.push('--dangerously-skip-permissions');
    const env = Object.assign({}, process.env);
    if (term) env.TERM = term;
    let t;
    try {
      t = pty.spawn(AGY, args, {
        name: term || 'xterm-256color', cols: 120, rows: 40,
        cwd: 'E:/Coding Infra', env,
        conptyInheritCursor: !!inheritCursor,
      });
    } catch (e) { return resolve({ label, err: e.message }); }
    let buf = '';
    let exited = false;
    t.onData(d => { buf += d; });
    if (nudgeStdin) setTimeout(() => { try { t.write('\r'); } catch {} }, 1200);
    const kill = setTimeout(() => { try { t.kill(); } catch {} }, 22000);
    t.onExit(() => {
      if (exited) return; exited = true;
      clearTimeout(kill);
      const clean = strip(buf);
      const hasPong = /pong/i.test(clean);
      resolve({ label, bytes: buf.length, hasPong, sample: clean.replace(/\n+/g, ' | ').slice(0, 140) });
    });
  });
}

(async () => {
  const configs = [
    ['A baseline(-p,skip)',            { skipPerms: true }],
    ['B no-skip-perms',                { skipPerms: false }],
    ['C skip + stdin-nudge',           { skipPerms: true, nudgeStdin: true }],
    ['D skip + inheritCursor + TERM',  { skipPerms: true, inheritCursor: true, term: 'xterm-256color' }],
    ['E no-skip + stdin-nudge',        { skipPerms: false, nudgeStdin: true }],
  ];
  for (const [label, cfg] of configs) {
    const r = await run(label, cfg);
    console.log(JSON.stringify(r));
  }
})();

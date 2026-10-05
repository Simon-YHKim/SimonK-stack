// Catalog and CI-file validator (hub D-87 PR-B).
// The legacy root plugin (.claude-plugin/plugin.json + skills/) is archived in
// _archive/legacy-root-plugin-0.1.0/, so the marketplace catalog is the only
// plugin entry this repo serves: exactly the five dist plugins. Every .json and
// .mjs under .claude-plugin/ and .github/ must parse; the Codex catalog, when
// present, needs a name and a plugins array.
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';

const CATALOG = '.claude-plugin/marketplace.json';
const CODEX_CATALOG = '.agents/plugins/marketplace.json';
const REPO_URL = 'https://github.com/Simon-YHKim/SimonK-stack.git';
const OWNERS = {
  'simonk-core': 'SimonKCore',
  'simonk-stack': 'SimonKStack',
  'simonk-aihub': 'SimonKAIHub',
  'simonk-design': 'SimonKDesign',
  'simonk-market': 'SimonKMarket',
};

let fail = 0;
const counts = { json: 0, mjs: 0 };
const parsed = new Map();
function error(...args) { console.error(...args); fail = 1; }

function readJson(path) {
  if (parsed.has(path)) return parsed.get(path);
  let value;
  try {
    value = JSON.parse(readFileSync(path, 'utf8'));
    counts.json += 1;
  } catch (e) {
    error('bad json:', path, e.message);
  }
  parsed.set(path, value);
  return value;
}

// Five dist plugins, each git-subdir of this repo at plugins/<Owner>, ref dist.
const catalog = readJson(CATALOG);
if (catalog !== undefined) {
  if (catalog?.name !== 'simonk-stack') error('catalog name must be simonk-stack:', CATALOG);
  const plugins = Array.isArray(catalog?.plugins) ? catalog.plugins : [];
  if (!Array.isArray(catalog?.plugins)) error('catalog plugins must be an array:', CATALOG);
  const names = plugins.map((p) => p?.name);
  const expected = Object.keys(OWNERS);
  if (names.length !== expected.length || new Set(names).size !== names.length
      || !expected.every((n) => names.includes(n))) {
    error('catalog must list exactly', expected.join(', '), '- found', names.join(', '));
  }
  for (const p of plugins) {
    const owner = OWNERS[p?.name];
    if (!owner) continue;
    const s = p.source ?? {};
    if (s.source !== 'git-subdir' || s.url !== REPO_URL || s.path !== `plugins/${owner}` || s.ref !== 'dist') {
      error('catalog entry', p.name, 'must be git-subdir', REPO_URL, `plugins/${owner}`, 'ref dist');
    }
  }
  console.log('catalog', catalog?.name, plugins.length, 'plugins');
}

if (existsSync(CODEX_CATALOG)) {
  const codex = readJson(CODEX_CATALOG);
  if (codex !== undefined) {
    if (typeof codex?.name !== 'string' || !codex.name || !Array.isArray(codex?.plugins)) {
      error('codex catalog needs a name and a plugins array:', CODEX_CATALOG);
    } else {
      console.log('codex catalog', codex.name, codex.plugins.length, 'plugins');
    }
  }
}

function walk(dir) {
  if (!existsSync(dir)) return;
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const p = `${dir}/${e.name}`;
    if (e.isDirectory()) walk(p);
    else if (e.name.endsWith('.json')) readJson(p);
    else if (e.name.endsWith('.mjs')) {
      try {
        execFileSync(process.execPath, ['--check', p], { stdio: 'pipe' });
        counts.mjs += 1;
      } catch (e2) {
        error('mjs syntax:', p, String(e2.stderr || e2.message).trim());
      }
    }
  }
}
walk('.claude-plugin');
walk('.github');

console.log('checked', counts.json, 'json,', counts.mjs, 'mjs');
console.log(fail ? 'VALIDATE FAILED' : 'validate OK');
process.exit(fail);

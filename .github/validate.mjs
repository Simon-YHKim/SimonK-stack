import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { execSync } from 'node:child_process';
let fail = 0;
const pj = JSON.parse(readFileSync('.claude-plugin/plugin.json', 'utf8'));
if (!pj.name || !Array.isArray(pj.skills)) { console.error('bad plugin.json'); fail = 1; }
console.log('plugin', pj.name, (pj.skills || []).length, 'skills');
if (existsSync('skills')) for (const e of readdirSync('skills', { withFileTypes: true })) {
  if (!e.isDirectory()) continue;
  try { statSync(`skills/${e.name}/SKILL.md`); } catch { console.error('missing SKILL.md:', e.name); fail = 1; }
}
function walk(dir) {
  if (!existsSync(dir)) return;
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const p = `${dir}/${e.name}`;
    if (e.isDirectory()) walk(p);
    else if (e.name.endsWith('.mjs')) { try { execSync(`node --check "${p}"`); } catch { console.error('mjs syntax:', p); fail = 1; } }
    else if (e.name.endsWith('.json')) { try { JSON.parse(readFileSync(p, 'utf8')); } catch { console.error('bad json:', p); fail = 1; } }
  }
}
walk('skills'); walk('.claude-plugin');
console.log(fail ? 'VALIDATE FAILED' : 'validate OK');
process.exit(fail);

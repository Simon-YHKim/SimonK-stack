import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { chmodSync, existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const script = resolve(dirname(fileURLToPath(import.meta.url)), '../scripts/check-referral-integrity.sh');
const gitBash = 'C:\\Program Files\\Git\\bin\\bash.exe';
const bash = process.platform === 'win32' && existsSync(gitBash) ? gitBash : 'bash';
const fixtureDir = mkdtempSync(join(tmpdir(), 'simonk-referral-integrity-'));

function shellPath(path) {
  if (process.platform !== 'win32') return path;
  return `/${path[0].toLowerCase()}${path.slice(2).replaceAll('\\', '/')}`;
}

function run(output, envOverride = {}) {
  const mock = join(fixtureDir, 'psql');
  writeFileSync(mock, `#!/usr/bin/env bash
[[ "$*" == *"-X -w -qAt -v ON_ERROR_STOP=1"* ]] || exit 70
sql="$(cat)"
[[ "$sql" == *"BEGIN READ ONLY;"* && "$sql" == *"COMMIT;"* ]] || exit 71
printf '%s\\n' "$MOCK_PSQL_OUTPUT"
`, 'utf8');
  chmodSync(mock, 0o755);
  return spawnSync(bash, [
    '-c', 'PATH="$1:$PATH"; export PATH; exec "$2"', 'bash',
    shellPath(fixtureDir), shellPath(script),
  ], {
    encoding: 'utf8',
    env: {
      ...process.env,
      PGHOST: 'fixture-host', PGDATABASE: 'fixture-db', PGUSER: 'fixture-user',
      PGPASSWORD: '', MOCK_PSQL_OUTPUT: output, ...envOverride,
    },
  });
}

test.after(() => {
  const root = resolve(tmpdir()) + sep;
  assert.ok(resolve(fixtureDir).startsWith(root));
  rmSync(fixtureDir, { recursive: true });
});

test('passes only when all four read-only checks return zero', () => {
  const result = run([
    'self_referral|0', 'duplicate_idempotency_key|0',
    'ledger_role_mismatch|0', 'grant_outside_rewarded_state|0',
  ].join('\n'));
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /integrity checks passed/);
});

test('returns a violation status without printing a credential', () => {
  const result = run([
    'self_referral|0', 'duplicate_idempotency_key|2',
    'ledger_role_mismatch|0', 'grant_outside_rewarded_state|0',
  ].join('\n'), { PGPASSWORD: 'fixture-secret-never-print' });
  assert.equal(result.status, 1, result.stderr);
  assert.match(result.stderr, /integrity violations=2/);
  assert.equal((result.stdout + result.stderr).includes('fixture-secret-never-print'), false);
});

test('fails closed on incomplete output or missing explicit connection settings', () => {
  assert.equal(run('self_referral|0').status, 2);
  assert.equal(run([
    'self_referral|0', 'self_referral|0',
    'ledger_role_mismatch|0', 'grant_outside_rewarded_state|0',
  ].join('\n')).status, 2);
  const noHost = run('self_referral|0', { PGHOST: '' });
  assert.equal(noHost.status, 2);
  assert.match(noHost.stderr, /PGHOST/);
});

test('script contains no runtime sourcing of local secrets', () => {
  const body = readFileSync(script, 'utf8');
  assert.equal(body.includes('source .env'), false);
});

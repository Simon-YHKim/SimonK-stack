// Test double for grok.exe used only by the grok provider tests (never bundled).
// `agent --no-leader stdio` speaks a minimal ACP subset; `login --device-auth` prints a device code.
// Billing payload field names follow grok.exe 1.0.30 serde strings; values are fixtures.
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const readline = require('node:readline');

const ESC = String.fromCharCode(0x1b);
const args = process.argv.slice(2);

function option(name) {
  const prefix = `--${name}=`;
  const hit = args.find((arg) => arg.startsWith(prefix));
  return hit === undefined ? undefined : hit.slice(prefix.length);
}

const scenario = option('scenario') || 'weekly';
const expectHome = option('expect-home');
const rest = args.filter((arg) => !arg.startsWith('--scenario=') && !arg.startsWith('--expect-home='));
const home = process.env.GROK_HOME;

function record(entry) {
  if (home === undefined) return;
  fs.mkdirSync(home, { recursive: true });
  fs.appendFileSync(path.join(home, 'calls.log'), `${entry}\n`);
}

function envProblem() {
  if (process.env.XAI_API_KEY !== undefined) return 'XAI_API_KEY leaked into child env';
  if (expectHome !== undefined && home !== expectHome) return 'GROK_HOME mismatch';
  return null;
}

const WEEKLY = {
  creditUsagePercent: 42.5,
  currentPeriod: { type: 'USAGE_PERIOD_TYPE_WEEKLY', start: '2026-09-10T07:51:00Z', end: '2026-09-17T07:51:00Z' },
  monthlyLimit: { val: '10000' },
  used: { val: '4250' },
  onDemandCap: { val: '0' },
  onDemandUsed: { val: '0' },
  prepaidBalance: { val: '0' },
  isUnifiedBillingUser: true,
  billingPeriodStart: '2026-09-01T00:00:00Z',
  billingPeriodEnd: '2026-10-01T00:00:00Z',
  on_demand_enabled: false,
  subscriptionTier: 'SUBSCRIPTION_TIER_SUPER_GROK',
  futureField: { nested: [1, 2, 3] },
};

const MONTHLY = {
  currentPeriod: { type: 'MONTHLY', end: '2026-10-01T00:00:00Z' },
  monthlyLimit: { val: 2000 },
  used: { val: 600 },
  billingPeriodStart: '2026-09-01T00:00:00Z',
  billingPeriodEnd: '2026-10-01T00:00:00Z',
};

const FULL = {
  ...WEEKLY,
  creditUsagePercent: 100,
  on_demand_enabled: true,
  onDemandCap: { val: '5000' },
  onDemandUsed: { val: '120' },
};

const AUTH_ERROR = { code: -32000, message: 'Authentication required', data: 'Authentication required to fetch billing data' };
const NOT_FOUND = { code: -32601, message: 'Method not found' };

function billing(method) {
  if (method === 'x.ai/billing') return scenario === 'legacy-name' ? { result: WEEKLY } : { error: NOT_FOUND };
  switch (scenario) {
    case 'legacy-name':
      return { error: { ...NOT_FOUND, data: 'unknown ACP extension method: x.ai/billing' } };
    case 'no-billing':
      return { error: NOT_FOUND };
    case 'logged-out':
      return { error: AUTH_ERROR };
    case 'after-login':
      return fs.existsSync(path.join(home, 'fake-login-done')) ? { result: WEEKLY } : { error: AUTH_ERROR };
    case 'rate-limited':
      return { error: { code: -32000, message: 'Billing service error', data: 'HTTP 429 Too Many Requests' } };
    case 'garbage':
      return { result: 42 };
    case 'empty':
      return { result: {} };
    case 'monthly':
      return { result: MONTHLY };
    case 'full':
      return { result: FULL };
    default:
      return { result: WEEKLY };
  }
}

function runAgent() {
  if (rest.join(' ') !== 'agent --no-leader stdio') {
    process.stderr.write(`unexpected args: ${rest.join(' ')}\n`);
    process.exit(64);
  }
  const send = (message) => process.stdout.write(`${JSON.stringify({ jsonrpc: '2.0', ...message })}\n`);
  process.stdout.write('fake grok agent starting (non-JSON banner)\n');
  process.stderr.write('agent log line on stderr\n');

  const rl = readline.createInterface({ input: process.stdin });
  rl.on('line', (line) => {
    let message;
    try {
      message = JSON.parse(line);
    } catch {
      return;
    }
    if (typeof message.method !== 'string') return;
    record(message.method);
    if (message.jsonrpc !== '2.0') {
      send({ id: message.id === undefined ? null : message.id, error: { code: -32600, message: 'Invalid Request' } });
      return;
    }
    if (message.method === 'initialize') {
      const problem = envProblem();
      if (problem !== null) {
        send({ id: message.id, error: { code: -32603, message: problem } });
        return;
      }
      send({
        id: message.id,
        result: {
          protocolVersion: scenario === 'bad-version' ? 99 : 1,
          agentCapabilities: { loadSession: true, auth: {} },
          authMethods: [{ id: 'grok.com', name: 'Grok', description: 'Sign in with Grok' }],
          _meta: { agentVersion: '1.0.30' },
        },
      });
      send({ id: 'agent-request-1', method: 'session/request_permission', params: {} });
      send({ method: '_x.ai/mcp/servers_updated', params: { mcpServers: [] } });
      return;
    }
    if (message.method === '_x.ai/billing' || message.method === 'x.ai/billing') {
      if (scenario === 'hang') return;
      if (scenario === 'crash') process.exit(1);
      send({ id: message.id, ...billing(message.method) });
      return;
    }
    send({ id: message.id, error: NOT_FOUND });
  });
  rl.on('close', () => process.exit(0));
}

function runLogin() {
  if (rest.join(' ') !== 'login --device-auth') {
    process.stderr.write(`unexpected args: ${rest.join(' ')}\n`);
    process.exit(64);
  }
  const problem = envProblem();
  if (problem !== null) {
    process.stderr.write(`${problem}\n`);
    process.exit(65);
  }
  record('login --device-auth');
  process.stderr.write(`${ESC}[1mTo sign in, open ${ESC}[4mhttps://accounts.x.ai/device${ESC}[24m in a browser.${ESC}[0m\n`);
  process.stdout.write(`Enter the code: ${ESC}[32mWXYZ-2345${ESC}[0m (expires in 15 minutes)\n`);
  if (scenario === 'login-hang') {
    setInterval(() => undefined, 1000);
    return;
  }
  setTimeout(() => {
    if (scenario === 'login-expired') {
      process.stderr.write('Device code expired. Run `grok login --device-auth` again.\n');
      process.exit(1);
    }
    fs.mkdirSync(home, { recursive: true });
    fs.writeFileSync(path.join(home, 'fake-login-done'), 'ok');
    process.stdout.write('Signed in.\n');
    process.exit(0);
  }, 150);
}

if (rest[0] === '--version') {
  process.stdout.write('grok 1.0.30 (04b7ffed98c6) [stable]\n');
  process.exit(0);
} else if (rest[0] === 'agent') {
  runAgent();
} else if (rest[0] === 'login') {
  runLogin();
} else {
  process.stderr.write(`unsupported fake invocation: ${rest.join(' ')}\n`);
  process.exit(64);
}

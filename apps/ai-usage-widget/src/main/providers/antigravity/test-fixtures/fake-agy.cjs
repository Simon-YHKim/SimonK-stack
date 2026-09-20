// Fake `agy` run with node in adapter tests: `node fake-agy.cjs <scenario> <callLog> ...agyArgs`.
// Every run is appended to <callLog> so tests can count calls and inspect argv, cwd and the
// environment the adapter passed.
const fs = require('node:fs');
const path = require('node:path');

const [scenario, callLog, ...args] = process.argv.slice(2);
fs.appendFileSync(
  callLog,
  `${JSON.stringify({
    args,
    cwd: process.cwd(),
    autoUpdateOff: process.env.AGY_CLI_DISABLE_AUTO_UPDATE ?? null,
    leakedKey: process.env.GEMINI_API_KEY ?? null,
  })}\n`,
);

if (args[0] === '--version') {
  process.stdout.write('1.2.6\n');
  process.exit(0);
}

const fixture = fs.readFileSync(path.join(__dirname, 'usage-1.2.6.json'), 'utf8');
switch (scenario) {
  case 'ok':
    process.stdout.write(fixture);
    break;
  case 'prompt': {
    // The slash command was not expanded: agy answered as an AI turn.
    const parsed = JSON.parse(fixture);
    delete parsed.command;
    parsed.num_turns = 1;
    parsed.response = 'I cannot show usage.';
    process.stdout.write(JSON.stringify(parsed));
    break;
  }
  case 'signed-out':
    process.stderr.write('Error: not logged in. Run agy to sign in.\n');
    process.exitCode = 1;
    break;
  case 'network-error':
    // Shape assumed (no real failure captured yet): a non-success status with a short error text.
    process.stdout.write(JSON.stringify({ status: 'ERROR', error: 'request failed for someone@example.com: connection reset by peer' }));
    process.exitCode = 1;
    break;
  case 'garbage':
    process.stdout.write('<<not json>>');
    break;
  case 'hang':
    setInterval(() => undefined, 1_000);
    break;
  default:
    process.exitCode = 2;
}

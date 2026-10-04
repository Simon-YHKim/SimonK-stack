import assert from 'node:assert/strict';
import test from 'node:test';

import { parseInstallReferrer } from '../scripts/parse-install-referrer.ts';

test('normalizes a Play query without inventing a verified attribution', () => {
  assert.deepEqual(
    parseInstallReferrer('utm_source=Google_Ads&utm_medium=CPC&utm_campaign=Fall%20Launch&gclid=private'),
    {
      channel: 'google', campaign: 'fall launch', medium: 'cpc',
      matchedBy: 'install_referrer', verified: false, reason: null,
    },
  );
});

test('accepts a full HTTPS referrer URL and normalizes a known social source', () => {
  assert.deepEqual(
    parseInstallReferrer('https://example.test/path?utm_source=Instagram&utm_campaign=Invite'),
    {
      channel: 'meta', campaign: 'invite', medium: null,
      matchedBy: 'install_referrer', verified: false, reason: null,
    },
  );
});

test('unknown and empty sources remain unattributed, not organic', () => {
  for (const input of ['utm_source=unknown&utm_campaign=launch', 'utm_campaign=launch', '']) {
    const result = parseInstallReferrer(input);
    assert.equal(result.channel, null);
    assert.equal(result.matchedBy, 'none');
    assert.equal(result.verified, false);
  }
});

test('conflicting or repeated attribution keys fail closed', () => {
  for (const input of [
    'utm_source=google&utm_source=meta',
    'utm_source=google&utm_campaign=a&utm_campaign=b',
    'utm_source=%0Agoogle',
    'utm_source=google%EF%BF%BD',
    'javascript:utm_source=google',
    `utm_source=${'x'.repeat(4097)}`,
  ]) {
    const result = parseInstallReferrer(input);
    assert.equal(result.channel, null, input.slice(0, 60));
    assert.equal(result.matchedBy, 'none');
  }
});

test('does not expose a click ID in the normalized result', () => {
  const result = parseInstallReferrer('utm_source=tiktok&gclid=secret-click-id&fbclid=secret-meta-id');
  assert.equal(result.channel, 'tiktok');
  assert.equal(JSON.stringify(result).includes('secret'), false);
});

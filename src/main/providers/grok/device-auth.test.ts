// The real `grok login --device-auth` wording is pending live test T4; these cases cover
// the documented contract (URL + code, docs 02-authentication.md) and ANSI-colored output.
import { describe, expect, it } from 'vitest';
import { classifyLoginFailure, createDeviceAuthParser, isAllowedVerificationUrl } from './device-auth';

const ESC = String.fromCharCode(0x1b);
const NOW = 1_789_000_000_000;

describe('createDeviceAuthParser', () => {
  it('combines a URL and a labeled code from separate ANSI-colored lines', () => {
    const parser = createDeviceAuthParser(() => NOW);
    expect(parser.push(`${ESC}[1mOpen ${ESC}[4mhttps://accounts.x.ai/device${ESC}[24m in your browser.${ESC}[0m`)).toBeNull();
    expect(parser.push(`Enter the code: ${ESC}[32mWXYZ-2345${ESC}[0m (expires in 15 minutes)`)).toEqual({
      verificationUrl: 'https://accounts.x.ai/device',
      userCode: 'WXYZ-2345',
      expiresAt: NOW + 15 * 60_000,
    });
  });

  it('accepts the code before the URL and emits only once', () => {
    const parser = createDeviceAuthParser(() => NOW);
    expect(parser.push('Your code:')).toBeNull();
    expect(parser.push('  ABCD-EFGH  ')).toBeNull();
    const prompt = parser.push('Visit https://auth.x.ai/device.');
    expect(prompt).toEqual({ verificationUrl: 'https://auth.x.ai/device', userCode: 'ABCD-EFGH' });
    expect(parser.push('Visit https://auth.x.ai/device again')).toBeNull();
  });

  it('reads the code from verification_uri_complete', () => {
    const parser = createDeviceAuthParser(() => NOW);
    expect(parser.push('Open https://accounts.x.ai/device?user_code=QRST-7890 to continue')).toEqual({
      verificationUrl: 'https://accounts.x.ai/device?user_code=QRST-7890',
      userCode: 'QRST-7890',
    });
  });

  it('ignores URLs on hosts outside xAI and lowercase words after "code"', () => {
    const parser = createDeviceAuthParser(() => NOW);
    expect(parser.push('Docs: https://evil.example.com/device?user_code=AAAA-BBBB')).toBeNull();
    expect(parser.push('Enter the code shown below')).toBeNull();
    expect(parser.push('Device code request failed (HTTP 500)')).toBeNull();
    expect(parser.push('https://accounts.x.ai/device')).toBeNull();
    expect(parser.push('code = HTTP')).toBeNull();
    expect(parser.push('code: LMNO-4321')).toEqual({ verificationUrl: 'https://accounts.x.ai/device', userCode: 'LMNO-4321' });
  });
});

describe('isAllowedVerificationUrl', () => {
  it('allows https xAI and grok.com hosts only', () => {
    expect(isAllowedVerificationUrl('https://accounts.x.ai/device')).toBe(true);
    expect(isAllowedVerificationUrl('https://grok.com/device')).toBe(true);
    expect(isAllowedVerificationUrl('http://accounts.x.ai/device')).toBe(false);
    expect(isAllowedVerificationUrl('https://x.ai.evil.com/device')).toBe(false);
    expect(isAllowedVerificationUrl('https://user:pw@accounts.x.ai/')).toBe(false);
    expect(isAllowedVerificationUrl('not a url')).toBe(false);
  });
});

describe('classifyLoginFailure', () => {
  it('maps grok.exe failure messages to error codes', () => {
    expect(classifyLoginFailure('Device code expired. Run `grok login --device-auth` again.')).toBe('login-expired');
    expect(classifyLoginFailure('Authorization denied. The user rejected the request')).toBe('login-failed');
    expect(classifyLoginFailure('device code authentication is disabled for this account')).toBe('device-auth-disabled');
    expect(classifyLoginFailure('HTTP 429 Too Many Requests')).toBe('rate-limited');
    expect(classifyLoginFailure(`${ESC}[31merror: dns lookup failed${ESC}[0m`)).toBe('network');
    expect(classifyLoginFailure('something else')).toBe('login-failed');
  });
});

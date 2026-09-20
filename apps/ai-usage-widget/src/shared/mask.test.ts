import { describe, expect, it } from 'vitest';
import { maskEmail, maskSecrets, redact } from './mask';

describe('mask', () => {
  it('masks e-mail addresses', () => {
    expect(maskEmail('john.doe@example.com')).toBe('j***@e***.com');
    expect(maskEmail('a@b.co.kr')).toBe('a***@b***.kr');
    expect(maskEmail('invalid')).toBe('***');
    expect(maskSecrets('user someone@corp.example.org signed in')).toBe('user s***@c***.org signed in');
  });

  it('masks tokens and credentials in text', () => {
    const jwt = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U';
    expect(maskSecrets(`token ${jwt}`)).toBe('token [jwt]');
    expect(maskSecrets('Authorization: Bearer abcdef123456')).not.toContain('abcdef123456');
    expect(maskSecrets('key sk-ant-api03-abcdefghijklmnop')).toBe('key [key]');
    expect(maskSecrets('xai-ABCDEFGHIJKLMNOPQRSTUV')).toBe('[key]');
    expect(maskSecrets('https://x.test/cb?code=abc123&state=s1')).toBe('https://x.test/cb?code=[redacted]&state=s1');
    expect(maskSecrets('{"refresh_token":"r-123"}')).not.toContain('r-123');
    expect(maskSecrets('A'.repeat(48))).toBe('[redacted]');
  });

  it('leaves ordinary text alone', () => {
    expect(maskSecrets('exitCode 1 after 300ms')).toBe('exitCode 1 after 300ms');
    expect(maskSecrets('account/rateLimits/read ok')).toBe('account/rateLimits/read ok');
  });

  it('redacts nested objects by key', () => {
    const out = redact({
      email: 'john@example.com',
      nested: { accessToken: 'secret-value', list: ['bob@example.com'] },
      apiKey: 'k',
      count: 3,
    });
    expect(out).toEqual({
      email: 'j***@e***.com',
      nested: { accessToken: '[redacted]', list: ['b***@e***.com'] },
      apiKey: '[redacted]',
      count: 3,
    });
  });

  it('redacts errors to name/message/code', () => {
    const error = Object.assign(new Error('failed for a@b.com'), { code: 'ENOENT' });
    expect(redact(error)).toEqual({ name: 'Error', message: 'failed for a***@b***.com', code: 'ENOENT' });
  });
});

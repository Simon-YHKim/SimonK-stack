// Parses `grok login --device-auth` output. The wording is undocumented
// (02-authentication.md only says it "prints a URL and code"); grok.exe 1.0.30 validates
// user_code as [A-Z0-9-] (crates/codegen/xai-grok-login/src/device_code.rs).

import type { ErrorCode } from '../../../shared/types';
import { stripAnsi } from '../../cli/text';

export interface DeviceAuthPrompt {
  verificationUrl: string;
  userCode: string;
  expiresAt?: number;
}

export interface DeviceAuthParser {
  /** Feeds one output line; returns the prompt exactly once, when both URL and code are known. */
  push(line: string): DeviceAuthPrompt | null;
}

const URL_RE = /https:\/\/[^\s"'<>`]+/g;
const TRAILING_PUNCTUATION_RE = /[.,;:!?)\]}>]+$/;
const LABELED_CODE_RE = /\b[Cc][Oo][Dd][Ee]\b[\s:="'*]{1,6}([A-Z0-9][A-Z0-9-]{3,31})(?![A-Za-z0-9-])/;
const BARE_CODE_RE = /^(?:[>*-]\s*)?([A-Z0-9]{3,8}(?:-[A-Z0-9]{3,8}){1,3})$/;
const QUERY_CODE_RE = /^[A-Za-z0-9][A-Za-z0-9-]{3,31}$/;
const EXPIRY_RE = /\bexpires?\s+in\s+(\d{1,5})\s*(seconds?|secs?|s|minutes?|mins?|m)\b/i;
const CODE_STOPWORDS = new Set(['HTTP', 'HTTPS', 'JSON', 'NULL', 'NONE', 'TRUE', 'FALSE']);

/** Verification pages must be on xAI-owned hosts; anything else is ignored. */
export function isAllowedVerificationUrl(value: string): boolean {
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    return false;
  }
  if (url.protocol !== 'https:' || url.username !== '' || url.password !== '') return false;
  const host = url.hostname.toLowerCase();
  return host === 'x.ai' || host.endsWith('.x.ai') || host === 'grok.com' || host.endsWith('.grok.com');
}

function extractUrls(line: string): string[] {
  const urls: string[] = [];
  for (const match of line.matchAll(URL_RE)) {
    const candidate = match[0].replace(TRAILING_PUNCTUATION_RE, '');
    if (isAllowedVerificationUrl(candidate)) urls.push(candidate);
  }
  return urls;
}

function codeFromUrl(value: string): string | null {
  const url = new URL(value);
  const code = url.searchParams.get('user_code') ?? url.searchParams.get('code');
  return code !== null && QUERY_CODE_RE.test(code) ? code : null;
}

function extractCode(text: string): string | null {
  const labeled = LABELED_CODE_RE.exec(text)?.[1];
  if (labeled !== undefined && !labeled.endsWith('-') && !CODE_STOPWORDS.has(labeled)) return labeled;
  return BARE_CODE_RE.exec(text.trim())?.[1] ?? null;
}

function parseExpiry(line: string, now: () => number): number | undefined {
  const match = EXPIRY_RE.exec(line);
  const amount = match?.[1];
  const unit = match?.[2];
  if (amount === undefined || unit === undefined) return undefined;
  const seconds = unit.toLowerCase().startsWith('m') ? Number(amount) * 60 : Number(amount);
  return now() + seconds * 1000;
}

export function createDeviceAuthParser(now: () => number): DeviceAuthParser {
  let url: string | null = null;
  let code: string | null = null;
  let expiresAt: number | undefined;
  let done = false;

  return {
    push(raw) {
      if (done) return null;
      const line = stripAnsi(raw);
      for (const candidate of extractUrls(line)) {
        const fromQuery = codeFromUrl(candidate);
        if (fromQuery !== null) {
          url = candidate;
          code ??= fromQuery;
        } else {
          url ??= candidate;
        }
      }
      code ??= extractCode(line.replace(URL_RE, ' '));
      expiresAt = parseExpiry(line, now) ?? expiresAt;
      if (url === null || code === null) return null;
      done = true;
      const prompt: DeviceAuthPrompt = { verificationUrl: url, userCode: code };
      if (expiresAt !== undefined) prompt.expiresAt = expiresAt;
      return prompt;
    },
  };
}

/** Maps the tail of a failed login's output to a renderer-safe code (text itself is never shown). */
export function classifyLoginFailure(output: string): ErrorCode {
  const text = stripAnsi(output);
  if (/expired/i.test(text)) return 'login-expired';
  if (/device[\s_-]?(?:code|auth)[^\n]*(?:disabled|not enabled|not allowed|unsupported)/i.test(text)) {
    return 'device-auth-disabled';
  }
  if (/denied|rejected/i.test(text)) return 'login-failed';
  if (/rate.?limit|too many requests|\b429\b/i.test(text)) return 'rate-limited';
  if (/network|dns|unreachable|timed out|connection (?:refused|reset|error|failed)/i.test(text)) return 'network';
  return 'login-failed';
}

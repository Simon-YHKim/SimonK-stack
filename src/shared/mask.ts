// Masking for logs and renderer DTOs. Pure functions, no platform APIs.

const EMAIL_RE = /[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}/g;
const JWT_RE = /\beyJ[A-Za-z0-9_-]{4,}\.[A-Za-z0-9_-]{4,}\.[A-Za-z0-9_-]*/g;
const BEARER_RE = /\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{6,}/gi;
const API_KEY_RE = /\b(?:sk-ant-[A-Za-z0-9_-]{8,}|sk-[A-Za-z0-9_-]{16,}|xai-[A-Za-z0-9_-]{16,})/g;
const KEY_VALUE_RE =
  /\b(access_token|refresh_token|id_token|session_token|api[_-]?key|client_secret|password|secret|authorization|cookie|set-cookie|code|token)(\s*["']?\s*[:=]\s*["']?)([^\s"'&,;}]+)/gi;
const LONG_OPAQUE_RE = /\b[A-Za-z0-9_-]{40,}\b/g;

const SENSITIVE_KEYS = new Set([
  'accesstoken',
  'refreshtoken',
  'idtoken',
  'sessiontoken',
  'token',
  'apikey',
  'key',
  'clientsecret',
  'secret',
  'password',
  'authorization',
  'cookie',
  'setcookie',
  'usercode',
  'paste',
  'pastetext',
  'credentials',
]);

const EMAIL_KEYS = new Set(['email', 'mail', 'emailaddress', 'useremail']);

/** `john.doe@example.com` -> `j***@e***.com`. */
export function maskEmail(email: string): string {
  const at = email.lastIndexOf('@');
  if (at <= 0 || at === email.length - 1) return '***';
  const local = email.slice(0, at);
  const domain = email.slice(at + 1);
  const dot = domain.lastIndexOf('.');
  const tld = dot > 0 ? domain.slice(dot) : '';
  const host = dot > 0 ? domain.slice(0, dot) : domain;
  return `${local.slice(0, 1)}***@${host.slice(0, 1)}***${tld}`;
}

/** Masks e-mail addresses and credential-like substrings inside free text. */
export function maskSecrets(text: string): string {
  return text
    .replace(JWT_RE, '[jwt]')
    .replace(BEARER_RE, (_m, scheme: string) => `${scheme} [redacted]`)
    .replace(API_KEY_RE, '[key]')
    .replace(KEY_VALUE_RE, (_m, name: string, sep: string) => `${name}${sep}[redacted]`)
    .replace(EMAIL_RE, (m) => maskEmail(m))
    .replace(LONG_OPAQUE_RE, '[redacted]');
}

function normalizeKey(key: string): string {
  return key.toLowerCase().replace(/[^a-z0-9]/g, '');
}

/** Deep copy with sensitive keys redacted, e-mail keys masked and strings scrubbed. */
export function redact(value: unknown, depth = 0): unknown {
  if (depth > 8) return '[depth]';
  if (typeof value === 'string') return maskSecrets(value);
  if (typeof value !== 'object' || value === null) return value;
  if (value instanceof Error) {
    const out: Record<string, unknown> = { name: value.name, message: maskSecrets(value.message) };
    const code = (value as { code?: unknown }).code;
    if (typeof code === 'string' || typeof code === 'number') out.code = code;
    return out;
  }
  if (Array.isArray(value)) return value.slice(0, 50).map((item) => redact(item, depth + 1));
  const out: Record<string, unknown> = {};
  for (const [key, inner] of Object.entries(value)) {
    const normalized = normalizeKey(key);
    if (SENSITIVE_KEYS.has(normalized)) {
      out[key] = '[redacted]';
    } else if (EMAIL_KEYS.has(normalized) && typeof inner === 'string') {
      out[key] = maskEmail(inner);
    } else {
      out[key] = redact(inner, depth + 1);
    }
  }
  return out;
}

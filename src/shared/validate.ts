// Minimal runtime validation helpers shared by main (IPC/store) and renderer.
// Kept dependency-free so the same checks run in every process.

export type ParseResult<T> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: string };

export function ok<T>(value: T): ParseResult<T> {
  return { ok: true, value };
}

export function fail<T = never>(error: string): ParseResult<T> {
  return { ok: false, error };
}

export function isPlainObject(value: unknown): value is Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) return false;
  const proto: unknown = Object.getPrototypeOf(value);
  return proto === Object.prototype || proto === null;
}

export function unknownKeys(obj: Record<string, unknown>, allowed: readonly string[]): string[] {
  return Object.keys(obj).filter((key) => !allowed.includes(key));
}

/** Plain object whose keys are all in `allowed`. Missing keys are the caller's concern. */
export function parseRecord(
  input: unknown,
  allowed: readonly string[],
): ParseResult<Record<string, unknown>> {
  if (!isPlainObject(input)) return fail('expected an object');
  const extra = unknownKeys(input, allowed);
  if (extra.length > 0) return fail(`unexpected keys: ${extra.slice(0, 5).join(',')}`);
  return ok(input);
}

/** Channels without a payload accept `null` or `undefined` and normalize to `null`. */
export function parseNull(input: unknown): ParseResult<null> {
  return input === null || input === undefined ? ok(null) : fail('expected no payload');
}

export function isOneOf<const T extends string | number>(list: readonly T[], value: unknown): value is T {
  return (list as readonly unknown[]).includes(value);
}

export function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

export function isIntInRange(value: unknown, min: number, max: number): value is number {
  return typeof value === 'number' && Number.isInteger(value) && value >= min && value <= max;
}

export const ID_PATTERN = /^[A-Za-z0-9_-]{1,64}$/;

export function isId(value: unknown): value is string {
  return typeof value === 'string' && ID_PATTERN.test(value);
}

export const LABEL_MAX_LENGTH = 64;

function isInvisibleOrControl(codePoint: number): boolean {
  return (
    codePoint < 0x20 ||
    (codePoint >= 0x7f && codePoint < 0xa0) ||
    codePoint === 0x200e ||
    codePoint === 0x200f ||
    (codePoint >= 0x202a && codePoint <= 0x202e) ||
    (codePoint >= 0x2066 && codePoint <= 0x2069) ||
    codePoint === 0xfeff
  );
}

/**
 * Normalizes a user-provided display label: strips control and bidi-override
 * characters, collapses whitespace, enforces 1..LABEL_MAX_LENGTH code points.
 */
export function normalizeLabel(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  let out = '';
  for (const ch of value) {
    const codePoint = ch.codePointAt(0) ?? 0;
    if (!isInvisibleOrControl(codePoint)) out += ch;
  }
  out = out.replace(/\s+/g, ' ').trim();
  const length = [...out].length;
  if (length === 0 || length > LABEL_MAX_LENGTH) return null;
  return out;
}

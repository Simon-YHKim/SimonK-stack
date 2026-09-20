export const BACKOFF_BASE_MS = 30_000;
export const BACKOFF_MAX_MS = 15 * 60_000;
export const RATE_LIMITED_MIN_MS = 5 * 60_000;
/** Upper bound for a provider-supplied retry-after hint. */
export const RETRY_AFTER_MAX_MS = 60 * 60_000;
export const JITTER_RATIO = 0.2;

export interface BackoffInput {
  /** Consecutive failures including the current one (>= 1). */
  failures: number;
  rateLimited: boolean;
  retryAfterMs?: number | undefined;
  /** 0..1 random source (Math.random in production). */
  random: () => number;
}

/** `min(30s * 2^(n-1), 15min)` with +/-20% jitter; rate limits wait at least 5 minutes or retry-after. */
export function computeBackoffMs(input: BackoffInput): number {
  const failures = Math.max(1, Math.floor(input.failures));
  const exponent = Math.min(failures - 1, 16);
  const base = Math.min(BACKOFF_BASE_MS * 2 ** exponent, BACKOFF_MAX_MS);
  const jitter = 1 - JITTER_RATIO + 2 * JITTER_RATIO * Math.min(1, Math.max(0, input.random()));
  let delay = Math.round(base * jitter);
  if (input.rateLimited) delay = Math.max(delay, RATE_LIMITED_MIN_MS);
  const hint = input.retryAfterMs;
  if (hint !== undefined && Number.isFinite(hint) && hint > 0) {
    delay = Math.max(delay, Math.min(hint, RETRY_AFTER_MAX_MS));
  }
  return delay;
}

import type { GrokBotAutoUsage } from '../../shared/grok-bot';
import { readGrokBotAccessToken } from './reader';

const URL = 'https://api2.cursor.sh/aiserver.v1.DashboardService/GetSandUsageStatus';
const POLL_MS = 5 * 60_000;

export function parseGrokBotUsage(value: unknown, measuredAt: number): GrokBotAutoUsage {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) throw new Error('Invalid usage response');
  const data = value as Record<string, unknown>;
  if (data.hasNonZeroIncludedLimit === false) return { state: 'unavailable', usedPercent: null, resetsAt: null, measuredAt };
  const used = data.usagePercent;
  if (typeof used !== 'number' || !Number.isFinite(used) || used < 0 || used > 100) {
    throw new Error('Missing weekly usage percent');
  }
  const reset = data.nextResetTimestampUtc;
  const resetsAt = typeof reset === 'string' ? Date.parse(reset) :
    typeof reset === 'number' && Number.isFinite(reset) ? (reset < 1e12 ? reset * 1000 : reset) : NaN;
  const plan = typeof data.grokPlanLabel === 'string' ? data.grokPlanLabel.slice(0, 64) : undefined;
  return {
    state: 'ok', usedPercent: Math.round(used), resetsAt: Number.isFinite(resetsAt) && resetsAt > measuredAt ? resetsAt : null,
    measuredAt, ...(plan ? { plan } : {}),
  };
}

export interface GrokBotServiceDeps {
  readToken?: () => string | null;
  request?: typeof fetch;
  now?: () => number;
  onChange(value: GrokBotAutoUsage): void;
}

export function createGrokBotService(deps: GrokBotServiceDeps) {
  const readToken = deps.readToken ?? readGrokBotAccessToken;
  const request = deps.request ?? fetch;
  const now = deps.now ?? Date.now;
  let timer: ReturnType<typeof setInterval> | null = null;
  let pending: Promise<void> | null = null;
  let stopped = false;

  const refresh = (): Promise<void> => {
    if (pending !== null) return pending;
    pending = (async () => {
      const at = now();
      let result: GrokBotAutoUsage;
      try {
        const token = readToken();
        if (token === null) {
          result = { state: 'unavailable', usedPercent: null, resetsAt: null, measuredAt: at };
        } else {
          const response = await request(URL, {
            method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', 'Connect-Protocol-Version': '1' },
            body: '{}', signal: AbortSignal.timeout(8000),
          });
          if (response.status === 401 || response.status === 403) {
            result = { state: 'login-expired', usedPercent: null, resetsAt: null, measuredAt: at };
          } else if (!response.ok) {
            result = { state: 'error', usedPercent: null, resetsAt: null, measuredAt: at };
          } else {
            result = parseGrokBotUsage(await response.json(), at);
          }
        }
      } catch {
        // Credentials and provider responses never enter logs, IPC, or the renderer.
        result = { state: 'error', usedPercent: null, resetsAt: null, measuredAt: at };
      }
      if (!stopped) deps.onChange(result);
    })().finally(() => { pending = null; });
    return pending;
  };

  return {
    refresh,
    start(): void {
      if (timer !== null) return;
      stopped = false;
      void refresh();
      timer = setInterval(() => { void refresh(); }, POLL_MS);
    },
    stop(): void {
      stopped = true;
      if (timer !== null) clearInterval(timer);
      timer = null;
    },
  };
}

import { describe, expect, it } from 'vitest';
import { DEFAULT_SETTINGS } from '../../shared/settings';
import type { GrokBotReading } from '../../shared/grok-bot';
import type { AccountDTO, UsageSnapshot } from '../../shared/types';
import { linkGrokBot } from './grok-link';
import { buildAccountView } from './model';

const NOW = Date.parse('2026-10-25T02:00:00Z');
const HEAVY_RESET = Date.parse('2026-10-30T03:38:19.843Z');
const SUPER_RESET = Date.parse('2026-10-29T07:51:25.768Z');

function grokView(id: string, order: number, resetsAt: number) {
  const account: AccountDTO = { id, provider: 'grok', label: id, enabled: true, order, loginState: 'logged-in' };
  const snapshot: UsageSnapshot = {
    accountId: id, provider: 'grok', state: 'ok', source: 'grok-acp', measuredAt: NOW, lastSuccessAt: NOW,
    windows: [{ kind: 'weekly', usedPercent: 100, resetsAt, windowMinutes: 10_080, label: 'credits' }],
  };
  return buildAccountView(account, snapshot, DEFAULT_SETTINGS, NOW);
}

const automatic = (resetsAt: number | null, unified?: boolean): GrokBotReading => ({
  state: 'automatic', usedPercent: 100, leftPercent: 0, recordedAt: NOW, resetsAt, ...(unified === undefined ? {} : { unified }),
});

describe('linkGrokBot', () => {
  // Measured 26.10.25: the unified Bot reported the Heavy account's weekly reset to the millisecond.
  const views = [grokView('super', 0, SUPER_RESET), grokView('heavy', 1, HEAVY_RESET)];

  it('puts a unified Bot on the account whose weekly reset it shares, not on the first Grok account', () => {
    expect(linkGrokBot(views, automatic(HEAVY_RESET, true))).toEqual({ accountId: 'heavy', unified: true });
  });

  it('keeps a separate Bot as its own meter on the matching account', () => {
    expect(linkGrokBot(views, automatic(SUPER_RESET + 60_000, false))).toEqual({ accountId: 'super', unified: false });
  });

  it('shows a unified Bot on its own when its pool is not among the shown accounts', () => {
    expect(linkGrokBot(views, automatic(Date.parse('2026-10-31T00:00:00Z'), true))).toEqual({ accountId: null, unified: true });
  });

  it('falls back to the first Grok account for a separate Bot without a match', () => {
    expect(linkGrokBot(views, automatic(null))).toEqual({ accountId: 'super', unified: false });
    expect(linkGrokBot([], { state: 'unknown', recordedAt: null })).toEqual({ accountId: null, unified: false });
  });

  it('keeps the previous link while the automatic lookup is failing', () => {
    const previous = { accountId: 'heavy', unified: true };
    expect(linkGrokBot(views, { state: 'unknown', recordedAt: null }, previous)).toBe(previous);
    // A fresh automatic reading always wins over memory.
    expect(linkGrokBot(views, automatic(SUPER_RESET, false), previous)).toEqual({ accountId: 'super', unified: false });
  });
});

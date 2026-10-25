// Which Grok account a Grok Bot reading belongs to, and whether it is a meter of its own
// (DECISIONS 26.10.25). Measured 26.10.25: a unified Bot (Cursor `isUnified`) reported the same
// reset as its Grok account's weekly period to the millisecond, and the same percent.

import type { GrokBotReading } from '../../shared/grok-bot';
import type { AccountView } from './model';

export interface GrokBotLink {
  /** Grok account the Bot reading belongs to; null = none of the shown accounts. */
  accountId: string | null;
  /** The Bot draws from that account's weekly pool: no separate Bot meter to show. */
  unified: boolean;
  /**
   * With a unified automatic reading on one account, the next Grok account keeps a separate Bot
   * meter of its own (legacy SuperGrok linked to Cursor, Simon 26.10.25: "다른 계정은 grok/bot으로
   * 나뉜다"). Only one Grok Bot app login exists per PC, so that meter is fed by manual entry.
   * While this is set the single manual slot belongs to this account only: `accountId` shows the
   * automatic reading alone, never the manual one.
   */
  manualAccountId: string | null;
}

/** Slack for the reset comparison; a different account's period would be hours or days apart. */
export const RESET_MATCH_MS = 5 * 60_000;

function weeklyReset(view: AccountView): number | null {
  return view.windows.find((row) => row.kind === 'weekly')?.resetsAt ?? null;
}

/**
 * Matches the Bot's weekly reset against each Grok account's weekly window. Without a match a
 * unified Bot stands alone (its pool is not among the shown accounts) and a separate Bot keeps
 * the old placement on the first Grok account. When the reading carries no evidence (automatic
 * lookup failing, no reset entered) the previous account is kept so the item does not jump
 * around, but as a separate meter: the Bot row then shows why the lookup failed and the popup
 * keeps its card for re-login and manual entry.
 */
export function linkGrokBot(views: readonly AccountView[], reading: GrokBotReading, previous?: GrokBotLink | null): GrokBotLink {
  const grok = views.filter((view) => view.account.provider === 'grok');
  const shown = (id: string | null): id is string => id !== null && grok.some((view) => view.account.id === id);
  const unified = reading.state === 'automatic' && reading.unified === true;
  // Once the manual slot belongs to the separate account, a failing automatic lookup (whose
  // fallback is that manual reading) must not move the manual number onto the unified account.
  if (reading.state !== 'automatic' && previous != null && shown(previous.manualAccountId) && shown(previous.accountId)) {
    return { accountId: previous.accountId, unified: false, manualAccountId: previous.manualAccountId };
  }
  const botReset = reading.state === 'automatic' || reading.state === 'fresh' || reading.state === 'stale' ? reading.resetsAt : null;
  if (botReset !== null) {
    const match = grok.find((view) => {
      const reset = weeklyReset(view);
      return reset !== null && Math.abs(reset - botReset) <= RESET_MATCH_MS;
    });
    if (match !== undefined) {
      const other = unified ? grok.find((view) => view.account.id !== match.account.id) : undefined;
      return { accountId: match.account.id, unified, manualAccountId: other?.account.id ?? null };
    }
  }
  if (unified) return { accountId: null, unified: true, manualAccountId: null };
  if (reading.state !== 'automatic' && previous != null && previous.accountId !== null &&
    grok.some((view) => view.account.id === previous.accountId)) {
    return { accountId: previous.accountId, unified: false, manualAccountId: null };
  }
  return { accountId: grok[0]?.account.id ?? null, unified: false, manualAccountId: null };
}

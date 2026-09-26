import { PROVIDER_NAME_KEYS, USAGE_SOURCE_KEYS } from '../../../shared/i18n';
import { h, setStyles } from '../dom';
import { clampPercent } from '../format';
import { providerIcon } from '../icons';
import {
  errorText,
  isMeasuredState,
  measuredText,
  stateText,
  v1RowColor,
  windowTitle,
  windowsRowLevel,
  type AccountView,
  type RenderContext,
  type RowView,
} from '../model';
import { syncChildren } from './keyed';
import type { Api } from '../api';

function quotaBox(view: AccountView, row: RowView, index: number, ctx: RenderContext): HTMLElement {
  const { t, settings } = ctx;
  // The popup always shows used % (v1 SPEC §1-2).
  const percent =
    row.status === 'value' && row.usedPercent !== null
      ? `${Math.round(clampPercent(row.usedPercent))}% ${t('unitUsed')}`
      : row.status === 'reset'
        ? t('state_reset')
        : t('percentUnknown');
  const percentEl = h('div', { class: 'quota-box-percent' }, [percent]);
  const fill = h('div', { class: 'quota-bar-fill' });
  const width = row.status === 'value' && row.usedPercent !== null ? clampPercent(row.usedPercent) : 0;
  setStyles(fill, { width: `${width}%` });
  if (settings.theme !== 'windows') {
    const color = v1RowColor(row, index, settings, view.account.provider);
    setStyles(percentEl, { color });
    setStyles(fill, { 'background-color': color });
  }
  const reset =
    row.status !== 'reset' && row.resetsAt !== null ? t('resetLabel', { time: row.countdown }) : t('resetUnknown');
  return h(
    'div',
    { class: 'quota-box', 'data-status': row.status, 'data-level': windowsRowLevel(row, settings), 'data-kind': row.kind },
    [
      h('div', { class: 'quota-box-title' }, [
        windowTitle(t, row),
        row.label === null ? null : h('span', { class: 'quota-box-label' }, [row.label]),
      ]),
      percentEl,
      h('div', { class: 'quota-bar', 'aria-hidden': 'true' }, [fill]),
      h('div', { class: 'quota-box-reset' }, [reset]),
    ],
  );
}

export function cardContent(view: AccountView, ctx: RenderContext): HTMLElement[] {
  const { t, settings } = ctx;
  const providerName = t(PROVIDER_NAME_KEYS[view.account.provider]);
  const badges: HTMLElement[] = [];
  if (view.plan !== undefined) badges.push(h('span', { class: 'card-badge is-plan' }, [view.plan]));
  badges.push(h('span', { class: 'card-badge is-state', 'data-state': view.state }, [stateText(t, view.state)]));

  const header = h('div', { class: 'card-header' }, [
    h('div', { class: 'card-account-info' }, [
      providerIcon(view.account.provider, 24, settings.iconStyle === 'monochrome', providerName),
      h('div', { class: 'card-account-text' }, [
        h('div', { class: 'card-account-name' }, [view.account.label]),
        h('div', { class: 'card-account-email' }, [view.account.emailMasked ?? providerName]),
      ]),
    ]),
    h('div', { class: 'card-badges' }, badges),
  ]);

  // Error keeps the last real values visible but dimmed with their measurement time (DECISIONS 01:36).
  const showWindows = isMeasuredState(view.state) || (view.state === 'error' && view.measuredAt !== null);
  const parts: HTMLElement[] = [header];
  if (showWindows && view.windows.length > 0) {
    const dim = view.state === 'stale' || view.state === 'error';
    parts.push(
      h(
        'div',
        { class: `card-quota-grid${dim ? ' is-dim' : ''}` },
        view.windows.map((row, index) => quotaBox(view, row, index, ctx)),
      ),
    );
  }
  const meta: HTMLElement[] = [h('span', { class: 'card-measured' }, [measuredText(ctx, view.measuredAt)])];
  if (view.source !== null) {
    meta.push(h('span', { class: 'card-source' }, [t('sourceLabel', { source: t(USAGE_SOURCE_KEYS[view.source]) })]));
  }
  parts.push(h('div', { class: 'card-meta' }, meta));
  if (view.errorCode !== undefined) {
    parts.push(h('p', { class: 'card-reason' }, [t('errorDetail', { error: errorText(t, view.errorCode) })]));
  }
  return parts;
}

export class UsageTab {
  readonly el: HTMLElement;
  private readonly emptyEl: HTMLElement;
  private readonly listEl: HTMLElement;
  private readonly cards = new Map<string, HTMLElement>();
  private readonly pending = new Set<string>();
  private latestViews: readonly AccountView[] = [];
  private latestContext: RenderContext | null = null;

  constructor(private readonly deps: { api: Api; report(message: string): void }) {
    this.emptyEl = h('div', { class: 'usage-empty', hidden: true });
    this.listEl = h('div', { class: 'usage-list' });
    this.el = h('div', { class: 'usage-tab' }, [this.emptyEl, this.listEl]);
  }

  update(views: readonly AccountView[], ctx: RenderContext): void {
    this.latestViews = views;
    this.latestContext = ctx;
    const { t } = ctx;
    this.emptyEl.hidden = views.length > 0;
    this.emptyEl.replaceChildren(
      h('p', {}, [t('noActiveAccounts')]),
      h('p', { class: 'muted' }, [t('addAccountHint')]),
    );
    const seen = new Set<string>();
    const cards = views.map((view) => {
      seen.add(view.account.id);
      let card = this.cards.get(view.account.id);
      if (card === undefined) {
        card = h('article', { class: 'card usage-card', 'data-account-id': view.account.id });
        this.cards.set(view.account.id, card);
      }
      card.dataset.state = view.state;
      const content = cardContent(view, ctx);
      if (view.account.provider === 'codex') {
        const count = view.resetCreditsAvailable;
        const resetControls: HTMLElement[] = [
          h('span', { class: 'reset-credit-label' }, [
            count === undefined ? t('resetCreditUnknown') : t('resetCreditCount', { count }),
          ]),
        ];
        if (count !== undefined && count > 0) {
          const use = h('button', { type: 'button', class: 'reset-credit-button' }, [t('resetCreditUse')]);
          use.disabled = this.pending.has(view.account.id);
          use.addEventListener('click', () => this.redeem(view.account.id, use));
          resetControls.push(use);
        }
        const official = h('button', { type: 'button', class: 'reset-credit-link' }, [t('resetCreditUsagePage')]);
        official.addEventListener('click', () => {
          void this.deps.api.invoke('shell:open-external', { kind: 'link', key: 'codex-usage' });
        });
        resetControls.push(official);
        content.push(h('div', { class: 'reset-credit-row' }, resetControls));
      }
      card.replaceChildren(...content);
      return card;
    });
    for (const id of [...this.cards.keys()]) if (!seen.has(id)) this.cards.delete(id);
    syncChildren(this.listEl, cards);
  }

  private redeem(accountId: string, button: HTMLButtonElement): void {
    if (this.pending.has(accountId)) return;
    this.pending.add(accountId);
    button.disabled = true;
    void this.deps.api.invoke('usage:redeem-reset-credit', { accountId }).then((result) => {
      const t = this.latestContext?.t;
      if (t === undefined) return;
      if (!result.ok) { this.deps.report(t('resetCreditUnavailable')); return; }
      const key = {
        reset: 'resetCreditSuccess', cancelled: 'resetCreditCancelled', unavailable: 'resetCreditUnavailable',
        nothingToReset: 'resetCreditNothingToReset', noCredit: 'resetCreditNoCredit', alreadyRedeemed: 'resetCreditAlreadyRedeemed',
      } as const;
      this.deps.report(t(key[result.value]));
    }).catch(() => this.deps.report(this.latestContext?.t('resetCreditUnavailable') ?? '')).finally(() => {
      this.pending.delete(accountId);
      if (this.latestContext !== null) this.update(this.latestViews, this.latestContext);
    });
  }
}

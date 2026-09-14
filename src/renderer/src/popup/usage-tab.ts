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

function quotaBox(view: AccountView, row: RowView, index: number, ctx: RenderContext): HTMLElement {
  const { t, settings } = ctx;
  // The popup always shows used % (v1 SPEC §1-2).
  const percent =
    row.status === 'value' && row.usedPercent !== null
      ? `${Math.round(clampPercent(row.usedPercent))}%`
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
      h('div', { class: 'quota-box-title' }, [windowTitle(t, row)]),
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

  constructor() {
    this.emptyEl = h('div', { class: 'usage-empty', hidden: true });
    this.listEl = h('div', { class: 'usage-list' });
    this.el = h('div', { class: 'usage-tab' }, [this.emptyEl, this.listEl]);
  }

  update(views: readonly AccountView[], ctx: RenderContext): void {
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
      card.replaceChildren(...cardContent(view, ctx));
      return card;
    });
    for (const id of [...this.cards.keys()]) if (!seen.has(id)) this.cards.delete(id);
    syncChildren(this.listEl, cards);
  }
}

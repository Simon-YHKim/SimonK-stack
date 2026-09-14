// Scaffold views (empty state + plain account list). The renderer module replaces these.

import { PROVIDER_NAME_KEYS, createTranslator } from '../../shared/i18n';
import { VIEW_IDS, type AppStateSnapshot, type ViewId } from '../../shared/types';
import { h } from './dom';

export function parseViewFromSearch(search: string): ViewId {
  const view = new URLSearchParams(search).get('view');
  return VIEW_IDS.find((id) => id === view) ?? 'widget';
}

export interface ViewActions {
  openAccounts(): void;
}

export type RenderedKind = 'empty' | 'accounts';

export function renderView(
  root: HTMLElement,
  view: ViewId,
  state: AppStateSnapshot,
  actions: ViewActions,
): RenderedKind {
  const t = createTranslator(state.locale);
  const html = root.ownerDocument.documentElement;
  html.lang = state.locale;
  html.dataset.view = view;
  html.dataset.scheme = view === 'widget' ? state.theme.taskbarScheme : state.theme.scheme;
  html.dataset.highContrast = String(state.theme.highContrast);
  html.style.setProperty('--accent', state.theme.accent);

  const enabled = state.accounts.filter((account) => account.enabled).sort((a, b) => a.order - b.order);
  const rendered: RenderedKind = enabled.length > 0 ? 'accounts' : 'empty';

  if (view === 'widget') {
    if (rendered === 'empty') {
      const button = h('button', { type: 'button', class: 'widget-empty', title: t('noAccountTitle'), 'aria-label': t('noAccountTitle') }, [
        t('noActiveAccounts'),
      ]);
      button.addEventListener('click', () => actions.openAccounts());
      root.replaceChildren(button);
    } else {
      root.replaceChildren(
        h(
          'ul',
          { class: 'widget-accounts', 'aria-label': t('popupTitle') },
          enabled.map((account) => h('li', {}, [`${t(PROVIDER_NAME_KEYS[account.provider])} · ${account.label}`])),
        ),
      );
    }
    return rendered;
  }

  root.replaceChildren(
    h('main', { class: 'popup' }, [
      h('h1', { class: 'popup-title' }, [t('popupTitle')]),
      rendered === 'empty'
        ? h('section', { class: 'popup-empty', role: 'status' }, [
            h('p', {}, [t('noActiveAccounts')]),
            h('p', { class: 'muted' }, [t('addAccountHint')]),
          ])
        : h(
            'ul',
            { class: 'popup-accounts' },
            enabled.map((account) => h('li', {}, [`${t(PROVIDER_NAME_KEYS[account.provider])} · ${account.label}`])),
          ),
    ]),
  );
  return rendered;
}

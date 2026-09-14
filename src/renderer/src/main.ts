import './styles.css';
import type { AppStateSnapshot } from '../../shared/types';
import { parseViewFromSearch, renderView } from './view';

/** True when CSP blocks string evaluation (reported to --smoke). */
function cspBlocksEval(): boolean {
  try {
    // eslint-disable-next-line @typescript-eslint/no-implied-eval -- deliberate CSP probe, result unused
    new Function('return 1');
    return false;
  } catch {
    return true;
  }
}

async function main(): Promise<void> {
  const api = window.aiUsage;
  const root = document.getElementById('app');
  if (api === undefined || root === null) return;

  const view = parseViewFromSearch(window.location.search);
  const actions = {
    openAccounts: (): void => {
      void api.invoke('window:show-popup', { tab: 'accounts' });
    },
  };

  const initial = await api.invoke('app:get-state', null);
  if (!initial.ok) return;
  let state: AppStateSnapshot = initial.value;
  const rendered = renderView(root, view, state, actions);

  api.on('state:changed', (next) => {
    state = next;
    renderView(root, view, state, actions);
  });
  api.on('theme:changed', (theme) => {
    state = { ...state, theme };
    renderView(root, view, state, actions);
  });

  await api.invoke('app:renderer-ready', { view, rendered, cspEnforced: cspBlocksEval() });
}

void main();

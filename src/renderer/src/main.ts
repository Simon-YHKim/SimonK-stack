import './styles.css';
import './widget.css';
import './popup.css';
import type { AppStateSnapshot } from '../../shared/types';
import { PopupApp } from './popup/popup-app';
import { parseViewFromSearch } from './view';
import { WidgetApp } from './widget/widget-app';

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

interface ViewApp {
  update(state: AppStateSnapshot): 'empty' | 'accounts';
  updateTheme(theme: AppStateSnapshot['theme']): void;
  start(): void;
}

async function main(): Promise<void> {
  const api = window.aiUsage;
  const root = document.getElementById('app');
  if (api === undefined || root === null) return;

  const view = parseViewFromSearch(window.location.search);
  // PopupApp subscribes to login:event itself.
  const app: ViewApp = view === 'widget' ? new WidgetApp({ api, root }) : new PopupApp({ api, root });

  // Subscribe before fetching so a broadcast during startup is not lost or overwritten.
  let pushed = false;
  api.on('state:changed', (next) => {
    pushed = true;
    app.update(next);
  });
  api.on('theme:changed', (theme) => app.updateTheme(theme));

  const initial = await api.invoke('app:get-state', null);
  if (!initial.ok) return;
  const rendered = pushed ? 'accounts' : app.update(initial.value);
  app.start();

  await api.invoke('app:renderer-ready', {
    view,
    rendered: pushed ? (initial.value.accounts.some((a) => a.enabled) ? 'accounts' : 'empty') : rendered,
    cspEnforced: cspBlocksEval(),
  });
}

void main();

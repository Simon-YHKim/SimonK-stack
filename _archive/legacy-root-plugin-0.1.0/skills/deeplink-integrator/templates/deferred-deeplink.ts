/**
 * Deferred deep link recovery (SDK-free baseline).
 *
 * OS Universal/App Links do NOT restore the original path after a fresh install.
 * Two fallback strategies, used in order. If neither is precise enough,
 * delegate to mobile-attribution-integrator (Branch/AppsFlyer OneLink).
 *
 * Strategy A — server click-id: the web fallback page issues a short-lived
 *   click id (cookie/URL), the app fetches it on first launch.
 * Strategy B — clipboard handoff: the web page writes a tagged token to the
 *   clipboard; the app reads it once on first launch. Lower reliability
 *   (clipboard permissions/UX prompts) — treat as best-effort only.
 */
import * as Clipboard from 'expo-clipboard';
import { router } from 'expo-router';

const CLIPBOARD_TAG = 'myapp-dl:'; // web writes `myapp-dl:/invite/ABC123?ref=x`
const FIRST_RUN_KEY = 'deferred_dl_consumed';

type DeferredTarget = { path: string; params: Record<string, string> };

/** Strategy A: resolve a click id against your backend. Stub — implement fetch. */
async function resolveServerClickId(clickId: string): Promise<DeferredTarget | null> {
  // const res = await fetch(`https://app.example.com/api/dl/${clickId}`);
  // if (!res.ok) return null;
  // return (await res.json()) as DeferredTarget;
  return null;
}

/** Strategy B: read a tagged token off the clipboard exactly once. */
async function resolveClipboard(): Promise<DeferredTarget | null> {
  const raw = await Clipboard.getStringAsync();
  if (!raw?.startsWith(CLIPBOARD_TAG)) return null;
  const url = new URL('https://app.example.com' + raw.slice(CLIPBOARD_TAG.length));
  const params: Record<string, string> = {};
  url.searchParams.forEach((v, k) => (params[k] = v));
  return { path: url.pathname, params };
}

/**
 * Call once from app/onboarding/index (or the first authenticated screen)
 * after confirming this is a first run. Guard with persistent storage so a
 * deferred link is consumed at most once.
 */
export async function consumeDeferredLink(opts: {
  clickId?: string;
  isFirstRun: boolean;
  hasConsumed: () => Promise<boolean>;
  markConsumed: () => Promise<void>;
}): Promise<void> {
  if (!opts.isFirstRun) return;
  if (await opts.hasConsumed()) return;

  const target =
    (opts.clickId ? await resolveServerClickId(opts.clickId) : null) ??
    (await resolveClipboard());

  await opts.markConsumed(); // mark regardless to avoid re-prompting (FIRST_RUN_KEY)
  if (!target) return;

  // Forward attribution params to the destination screen (read via useLocalSearchParams).
  router.replace({ pathname: target.path as never, params: target.params });
}

export { FIRST_RUN_KEY };

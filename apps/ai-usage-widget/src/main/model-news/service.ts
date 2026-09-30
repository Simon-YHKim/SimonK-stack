import path from 'node:path';
import { PROVIDER_IDS, isProviderId, type ProviderId } from '../../shared/types';
import type { ModelNewsHealth, ModelNewsSourceKind, ModelNotice } from '../../shared/types';
import type { Logger } from '../log';
import { readJsonWithBackup, writeFileAtomic } from '../store/atomic';
import { anthropicNewsUrls, classifyAnnouncement, rssItems, xaiReleaseItems } from './announcement';
import { MODEL_CATALOGS, parseCatalog } from './catalog';

const CHECK_INTERVAL_MS = 6 * 60 * 60_000;
/** One early re-check after a check with failed sources (only while the periodic timer runs). */
export const RETRY_AFTER_FAILURE_MS = 15 * 60_000;
/**
 * Background page fetches, so generous: ai.google.dev usually answers in 0.5–1.5 s but stalled
 * 19.7 s and 30 s+ in 2 of 12 timed requests (26.09.30). Longer stalls fall to the 15 min re-check.
 */
const FETCH_TIMEOUT_MS = 30_000;
const MAX_RESPONSE_CHARS = 1_000_000;
const FEEDS = {
  codex: 'https://openai.com/news/rss.xml',
  antigravity: 'https://blog.google/technology/ai/rss/',
  claude: 'https://www.anthropic.com/sitemap.xml',
  grok: 'https://docs.x.ai/developers/release-notes',
} as const;

interface SavedState {
  seen: Record<string, string[]>;
  notices: ModelNotice[];
  dismissed: string[];
}

function emptyState(): SavedState { return { seen: {}, notices: [], dismissed: [] }; }

function normalizeState(input: unknown): SavedState {
  if (input === null || typeof input !== 'object') return emptyState();
  const value = input as Record<string, unknown>;
  const seen: Record<string, string[]> = {};
  if (value.seen !== null && typeof value.seen === 'object') {
    for (const [key, ids] of Object.entries(value.seen)) {
      if (Array.isArray(ids)) seen[key] = ids.filter((id): id is string => typeof id === 'string' && id.length <= 2048).slice(-3000);
    }
  }
  const notices = Array.isArray(value.notices) ? value.notices.filter((notice): notice is ModelNotice => {
    if (notice === null || typeof notice !== 'object') return false;
    const item = notice as Record<string, unknown>;
    return isProviderId(item.provider) && typeof item.id === 'string' && item.id.length < 140 &&
      typeof item.model === 'string' && item.model.length < 90 && (item.status === 'upcoming' || item.status === 'released') &&
      typeof item.url === 'string' && allowedUrl(item.provider, item.url) &&
      (item.releaseDate === null || (typeof item.releaseDate === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(item.releaseDate))) &&
      typeof item.observedAt === 'number' && Number.isFinite(item.observedAt);
  }).slice(-100) : [];
  const dismissed = Array.isArray(value.dismissed) ? value.dismissed.filter((id): id is string => typeof id === 'string' && id.length < 140).slice(-500) : [];
  return { seen, notices, dismissed };
}

function modelKey(value: string): string { return value.toLowerCase().replace(/[- ]20\d{6}$/, '').replace(/[^a-z0-9]/g, ''); }

export function allowedUrl(provider: ProviderId, value: string): boolean {
  try {
    const url = new URL(value);
    const host = url.hostname;
    return url.protocol === 'https:' && url.username === '' && url.password === '' && url.port === '' && (
      provider === 'claude' ? (host === 'www.anthropic.com' || host === 'platform.claude.com') :
      provider === 'codex' ? (host === 'openai.com' || host === 'developers.openai.com') :
      provider === 'grok' ? (host === 'x.ai' || host === 'docs.x.ai') :
      (host === 'blog.google' || host === 'ai.google.dev')
    );
  } catch { return false; }
}

export interface ModelNewsOptions {
  userData: string;
  logger: Logger;
  onChange(notices: ModelNotice[]): void;
  /** After every finished check: when it ran and which sources failed (a page layout change shows up here). */
  onHealth?(health: ModelNewsHealth): void;
  fetchText?: (url: string) => Promise<string>;
  now?: () => number;
}

export async function createModelNewsService(options: ModelNewsOptions) {
  const file = path.join(options.userData, 'model-news.json');
  const loaded = await readJsonWithBackup(file);
  const state = normalizeState(loaded.value);
  const now = options.now ?? Date.now;
  const fetchText = options.fetchText ?? (async (url: string): Promise<string> => {
    // English pages: the parsers read English link and announcement shapes, and some vendors
    // otherwise redirect to a machine-translated page.
    const response = await fetch(url, {
      signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
      headers: { Accept: 'text/html, application/xml, text/xml', 'Accept-Language': 'en' },
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const length = Number(response.headers.get('content-length'));
    if (Number.isFinite(length) && length > MAX_RESPONSE_CHARS) throw new Error('response too large');
    const body = await response.text();
    if (body.length > MAX_RESPONSE_CHARS) throw new Error('response too large');
    return body;
  });
  let timer: ReturnType<typeof setInterval> | null = null;
  let running: Promise<void> | null = null;
  let saveQueue: Promise<void> = Promise.resolve();
  let stopped = false;
  /** Failing sources keyed `kind:provider`; cleared by that source's next success. Memory only. */
  const failing = new Map<string, ModelNewsHealth['failing'][number]>();
  let checkedAt: number | null = null;
  const sourceOk = (kind: ModelNewsSourceKind, provider: ProviderId): void => {
    failing.delete(`${kind}:${provider}`);
  };
  const sourceFailed = (kind: ModelNewsSourceKind, provider: ProviderId): void => {
    const key = `${kind}:${provider}`;
    const previous = failing.get(key);
    failing.set(key, { provider, kind, since: previous?.since ?? now(), count: (previous?.count ?? 0) + 1 });
  };
  const health = (): ModelNewsHealth => ({
    checkedAt,
    sources: PROVIDER_IDS.length + Object.keys(FEEDS).length,
    failing: [...failing.values()].map((entry) => ({ ...entry })),
  });

  const active = (): ModelNotice[] => PROVIDER_IDS.flatMap((provider) => {
    const latest = state.notices.filter((item) => item.provider === provider)
      .sort((a, b) => b.observedAt - a.observedAt || (a.status === 'released' ? -1 : 1))[0];
    return latest === undefined || state.dismissed.includes(latest.id) ? [] : [latest];
  });
  const save = async (): Promise<void> => {
    const content = `${JSON.stringify(state, null, 2)}\n`;
    saveQueue = saveQueue.catch(() => undefined).then(() => writeFileAtomic(file, content, { backup: true }));
    await saveQueue;
    options.onChange(active());
  };
  const markSeen = (source: string, ids: readonly string[]): string[] => {
    const previous = state.seen[source];
    const unseen = previous === undefined ? [] : ids.filter((id) => !previous.includes(id));
    state.seen[source] = [...new Set([...(previous ?? []), ...ids])].slice(-3000);
    return unseen;
  };
  const addNotice = (notice: Omit<ModelNotice, 'id' | 'observedAt'>): void => {
    if (!allowedUrl(notice.provider, notice.url)) return;
    const id = `${notice.status}:${notice.provider}:${modelKey(notice.model)}`;
    if (notice.status === 'upcoming' && state.notices.some((item) => item.id === `released:${notice.provider}:${modelKey(notice.model)}`)) return;
    if (state.notices.some((item) => item.id === id)) return;
    state.notices.push({ ...notice, id, observedAt: now() });
    state.notices = state.notices.slice(-100);
  };
  const check = async (): Promise<void> => {
    const jobs = PROVIDER_IDS.map(async (provider) => {
      try {
        const html = await fetchText(MODEL_CATALOGS[provider]);
        const models = parseCatalog(provider, html);
        // A changed/empty page is not evidence that previously seen models disappeared.
        if (models.length === 0) throw new Error('empty model catalog');
        const newIds = markSeen(`catalog:${provider}`, models.map((model) => model.id));
        for (const model of models) if (newIds.includes(model.id)) {
          addNotice({ provider, model: model.id, status: 'released', releaseDate: null, url: model.url });
        }
        sourceOk('catalog', provider);
      } catch (error) {
        sourceFailed('catalog', provider);
        options.logger.warn('model catalog check failed', { provider, error });
      }
    });
    const feeds = (Object.entries(FEEDS) as [keyof typeof FEEDS, string][]).map(async ([provider, url]) => {
      try {
        const xml = await fetchText(url);
        if (provider === 'claude') {
          const urls = anthropicNewsUrls(xml);
          if (urls.length === 0) throw new Error('empty news sitemap');
          const seenKey = `news:${provider}`;
          const newUrls = markSeen(seenKey, urls).slice(-12);
          const failedUrls: string[] = [];
          await Promise.all(newUrls.map(async (articleUrl) => {
            try {
              const html = await fetchText(articleUrl);
              const title = /<meta[^>]+property="og:title"[^>]+content="([^"]+)"/i.exec(html)?.[1] ?? '';
              const summary = /<meta[^>]+(?:name|property)="(?:description|og:description)"[^>]+content="([^"]+)"/i.exec(html)?.[1] ?? '';
              const announcement = classifyAnnouncement(provider, title, summary, articleUrl);
              if (announcement !== null) addNotice(announcement);
            } catch (error) {
              failedUrls.push(articleUrl);
              options.logger.warn('model news article failed', { provider, error });
            }
          }));
          // Unread articles go back to unseen so the next check tries them again.
          if (failedUrls.length > 0) state.seen[seenKey] = (state.seen[seenKey] ?? []).filter((url) => !failedUrls.includes(url));
          // One unreadable article is not a broken source; every new article failing is.
          if (newUrls.length > 0 && failedUrls.length === newUrls.length) throw new Error('every new article failed');
          sourceOk('news', provider);
          return;
        }
        const items = provider === 'grok' ? xaiReleaseItems(xml) :
          rssItems(xml, provider === 'codex' ? 'https://openai.com' : 'https://blog.google');
        if (items.length === 0) throw new Error('empty news feed');
        const newUrls = markSeen(`news:${provider}`, items.map((item) => item.url));
        for (const item of items) {
          if (!newUrls.includes(item.url)) continue;
          const announcement = classifyAnnouncement(provider, item.title, item.description, item.url);
          if (announcement !== null) addNotice(announcement);
        }
        sourceOk('news', provider);
      } catch (error) {
        sourceFailed('news', provider);
        options.logger.warn('model announcement check failed', { provider, error });
      }
    });
    await Promise.all([...jobs, ...feeds]);
    checkedAt = now();
    if (stopped) return;
    try {
      options.onHealth?.(health());
    } catch (error) {
      options.logger.warn('model news health listener failed', { error });
    }
    await save().catch((error: unknown) => options.logger.warn('model news save failed', { error }));
    // A failure right after start-up (a slow network, 26.09.30) should not sit in the settings
    // tab for the whole 6 h interval: look again soon, once.
    if (failing.size > 0 && retryTimer === null && timer !== null) {
      retryTimer = setTimeout(() => {
        retryTimer = null;
        void checkNow();
      }, RETRY_AFTER_FAILURE_MS);
    }
  };

  let retryTimer: ReturnType<typeof setTimeout> | null = null;
  const checkNow = (): Promise<void> => {
    running ??= check().finally(() => { running = null; });
    return running;
  };

  return {
    start(): void {
      if (timer !== null || stopped) return;
      options.onChange(active());
      timer = setInterval(() => { void checkNow(); }, CHECK_INTERVAL_MS);
      void checkNow();
    },
    checkNow,
    async dismiss(provider: ProviderId): Promise<void> {
      const notice = active().find((item) => item.provider === provider);
      if (notice === undefined) return;
      state.dismissed = [...state.dismissed, notice.id].slice(-500);
      await save();
    },
    current: active,
    health,
    stop(): void {
      stopped = true;
      if (timer !== null) clearInterval(timer);
      timer = null;
      if (retryTimer !== null) clearTimeout(retryTimer);
      retryTimer = null;
    },
  };
}

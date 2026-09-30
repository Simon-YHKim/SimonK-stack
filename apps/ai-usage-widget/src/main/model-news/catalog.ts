import type { ProviderId } from '../../shared/types';

/** Public, vendor-owned catalog pages. No account credentials or paid API calls are used. */
export const MODEL_CATALOGS: Readonly<Record<ProviderId, string>> = {
  claude: 'https://platform.claude.com/docs/en/models/overview',
  codex: 'https://developers.openai.com/api/docs/models',
  grok: 'https://docs.x.ai/developers/models',
  // hl=en: without it Google sometimes redirects to a machine-translated page (seen: ?hl=pt-br,
  // 26.09.30) whose links carry the locale, and the list then parsed as empty.
  antigravity: 'https://ai.google.dev/gemini-api/docs/models?hl=en',
};

export interface CatalogModel {
  id: string;
  url: string;
}

/**
 * Only IDs in the catalog's model links or ID controls count. Free text, images,
 * examples, aliases and non-chat modalities must not create release alerts.
 */
export function parseCatalog(provider: ProviderId, html: string): CatalogModel[] {
  const patterns: Record<ProviderId, RegExp> = {
    claude: /aria-label="Copy model ID (claude-(?:opus|sonnet|haiku|fable|mythos)-[a-z0-9-]+)"/g,
    // Relative or absolute links, with or without a query (localized pages append ?hl=...).
    codex: /href="(?:https:\/\/developers\.openai\.com)?\/api\/docs\/models\/((?:gpt-[a-z0-9.-]+|o[1-9](?:-[a-z0-9.-]+)?))(?:\?[^"]*)?"/g,
    grok: /"name":"(grok-[0-9][a-z0-9.-]*)"/g,
    antigravity: /href="(?:https:\/\/ai\.google\.dev)?\/gemini-api\/docs\/models\/(gemini-[0-9][a-z0-9.-]*)(?:\?[^"]*)?"/g,
  };
  const exclude = /(?:image|video|voice|audio|speech|transcrib|tts|embed|live|realtime|latest|preview|system-card|\.(?:png|webp|svg))/.source;
  const filtered = new RegExp(exclude);
  const models = new Map<string, CatalogModel>();
  for (const match of html.matchAll(patterns[provider])) {
    const id = match[1];
    if (id === undefined || id.length > 80 || filtered.test(id)) continue;
    const url = provider === 'claude' ? MODEL_CATALOGS.claude :
      provider === 'grok' ? MODEL_CATALOGS.grok :
      `${new URL(MODEL_CATALOGS[provider]).origin}${provider === 'codex' ? '/api/docs/models/' : '/gemini-api/docs/models/'}${id}`;
    models.set(id, { id, url });
  }
  return [...models.values()].sort((a, b) => a.id.localeCompare(b.id));
}

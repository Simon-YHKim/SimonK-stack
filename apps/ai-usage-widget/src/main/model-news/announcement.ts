import type { ProviderId } from '../../shared/types';

export interface ModelAnnouncement {
  provider: ProviderId;
  model: string;
  status: 'upcoming' | 'released';
  /** An explicit date from the official announcement. Date-only: never invent a time. */
  releaseDate: string | null;
  url: string;
}

const MODEL_NAMES: Record<ProviderId, RegExp> = {
  claude: /\bClaude (?:Opus|Sonnet|Haiku|Fable|Mythos) \d+(?:\.\d+)?\b/i,
  codex: /\b(?:GPT[- ]?\d+(?:\.\d+)?(?:[- ](?:Sol|Astra|Luna|Mini|Pro))?|o[1-9](?:[- ](?:Pro|Mini))?)\b/i,
  grok: /\bGrok \d+(?:\.\d+)?(?: (?:Code Fast|Fast))?\b/i,
  antigravity: /\bGemini \d+(?:\.\d+)?(?: (?:Pro|Flash))?\b/i,
};

function decodeXml(value: string): string {
  return value.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1')
    .replace(/&(?:amp|lt|gt|quot|apos|#39);/g, (entity) => ({
      '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&apos;': "'", '&#39;': "'",
    })[entity] ?? entity)
    .replace(/<[^>]*>/g, ' ')
    .replace(/\s+/g, ' ').trim();
}

function tag(block: string, name: string): string {
  return decodeXml(new RegExp(`<${name}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/${name}>`, 'i').exec(block)?.[1] ?? '');
}

/** Extract only links whose host belongs to the declared vendor. */
export function rssItems(xml: string, origin: string): { title: string; description: string; url: string }[] {
  const items: { title: string; description: string; url: string }[] = [];
  for (const match of xml.matchAll(/<item>([\s\S]*?)<\/item>/g)) {
    const block = match[1];
    if (block === undefined) continue;
    const url = tag(block, 'link');
    try {
      if (new URL(url).origin !== origin) continue;
    } catch { continue; }
    items.push({ title: tag(block, 'title'), description: tag(block, 'description'), url });
  }
  return items;
}

export function anthropicNewsUrls(xml: string): string[] {
  const urls = new Set<string>();
  for (const match of xml.matchAll(/<loc>(https:\/\/www\.anthropic\.com\/news\/[^<]+)<\/loc>/g)) {
    const url = match[1]?.replace(/&amp;/g, '&');
    if (url !== undefined && /(?:claude|model)/i.test(new URL(url).pathname)) urls.add(url);
  }
  return [...urls];
}

/** xAI's public release notes are available when its news page denies direct fetching. */
export function xaiReleaseItems(html: string): { title: string; description: string; url: string }[] {
  const items: { title: string; description: string; url: string }[] = [];
  for (const match of html.matchAll(/<h3 id="([a-z0-9-]+)"[^>]*>([\s\S]*?)<\/h3>/gi)) {
    const id = match[1];
    const heading = match[2];
    if (id === undefined || heading === undefined || match.index === undefined) continue;
    const title = decodeXml(heading);
    if (!/^Grok \d/i.test(title)) continue;
    const after = html.slice(match.index + match[0].length);
    const nextHeading = after.search(/<h[23]\b/i);
    const paragraph = /<p(?:\s[^>]*)?>([\s\S]*?)<\/p>/i.exec(after);
    if (paragraph?.[1] === undefined || (nextHeading >= 0 && (paragraph.index ?? 0) > nextHeading)) continue;
    items.push({ title, description: decodeXml(paragraph[1]), url: `https://docs.x.ai/developers/release-notes#${id}` });
  }
  return items;
}

function explicitDate(text: string): string | null {
  const match = /(?:available|launch(?:ing)?|releas(?:e|ing)|coming)[^.]{0,80}?\b(?:on|from|starting)\s+(\d{4}-\d{2}-\d{2}|[A-Z][a-z]+\s+\d{1,2},?\s+\d{4})/i.exec(text);
  if (match?.[1] === undefined) return null;
  const raw = match[1];
  const date = /^\d{4}-\d{2}-\d{2}$/.test(raw) ? new Date(`${raw}T12:00:00Z`) : new Date(`${raw} 12:00:00 GMT`);
  return Number.isNaN(date.getTime()) ? null : date.toISOString().slice(0, 10);
}

/** Fail closed: a teaser alone never becomes a release claim. */
export function classifyAnnouncement(provider: ProviderId, title: string, summary: string, url: string): ModelAnnouncement | null {
  const model = MODEL_NAMES[provider].exec(title)?.[0];
  if (model === undefined || !/^https:\/\//.test(url)) return null;
  const text = `${title}. ${summary}`;
  const date = explicitDate(text);
  if (/\b(?:coming soon|will be available|will launch|launching on|available (?:on|from|starting))\b/i.test(text)) {
    return { provider, model, status: 'upcoming', releaseDate: date, url };
  }
  if (/\b(?:now available|available today|released today|releasing today|launching today|is available now)\b/i.test(text)) {
    return { provider, model, status: 'released', releaseDate: null, url };
  }
  return null;
}

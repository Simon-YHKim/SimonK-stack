import { describe, expect, it } from 'vitest';
import { anthropicNewsUrls, classifyAnnouncement, rssItems, xaiReleaseItems } from './announcement';

describe('official model announcements', () => {
  it('recognizes a dated launch without fabricating a time', () => {
    expect(classifyAnnouncement('codex', 'Introducing GPT-7 Sol', 'GPT-7 Sol will be available on October 12, 2026.', 'https://openai.com/index/gpt-7-sol'))
      .toEqual({ provider: 'codex', model: 'GPT-7 Sol', status: 'upcoming', releaseDate: '2026-10-12', url: 'https://openai.com/index/gpt-7-sol' });
    expect(classifyAnnouncement('claude', 'Claude Opus 6', 'Coming soon.', 'https://www.anthropic.com/news/opus-6')?.releaseDate).toBeNull();
  });

  it('requires an explicit release statement and ignores broad product stories', () => {
    expect(classifyAnnouncement('grok', 'Grok 5', 'Grok 5 is now available.', 'https://x.ai/news/grok-5')?.status).toBe('released');
    expect(classifyAnnouncement('grok', 'Grok 5 research update', 'New benchmark results.', 'https://x.ai/news/grok-5')).toBeNull();
    expect(classifyAnnouncement('antigravity', 'Google Beam expands', 'Now available.', 'https://blog.google/test')).toBeNull();
  });

  it('extracts feed items and sitemap links only from official hosts', () => {
    const xml = '<item><title><![CDATA[Gemini 4 Pro]]></title><description>Will be available on 2026-10-10.</description><link>https://blog.google/ai/gemini-4</link></item>' +
      '<item><title>Gemini 5</title><link>https://evil.example/claim</link></item>';
    expect(rssItems(xml, 'https://blog.google')).toHaveLength(1);
    expect(anthropicNewsUrls('<loc>https://www.anthropic.com/news/claude-opus-6</loc><loc>https://evil.example/news/claude-opus-7</loc>'))
      .toEqual(['https://www.anthropic.com/news/claude-opus-6']);
    expect(xaiReleaseItems('<h3 id="grok-5" class="x"><a href="#grok-5">Grok 5</a></h3><p>Grok 5 will be available on October 12, 2026.</p>'))
      .toEqual([{ title: 'Grok 5', description: 'Grok 5 will be available on October 12, 2026.', url: 'https://docs.x.ai/developers/release-notes#grok-5' }]);
    expect(xaiReleaseItems('<h3 id="unrelated"><a>Other</a></h3><p>Other.</p><h3 id="grok-5"><a>Grok 5</a></h3><p>Grok 5 is now available.</p>'))
      .toHaveLength(1);
  });
});

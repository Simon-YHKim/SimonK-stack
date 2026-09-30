import { mkdtemp, readFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { createLogger } from '../log';
import { MODEL_CATALOGS } from './catalog';
import { RETRY_AFTER_FAILURE_MS, allowedUrl, createModelNewsService } from './service';

const dirs: string[] = [];
afterEach(async () => { await Promise.all(dirs.splice(0).map((dir) => rm(dir, { recursive: true, force: true }))); });

const basePages = new Map<string, string>([
  [MODEL_CATALOGS.claude, 'aria-label="Copy model ID claude-opus-5"'],
  [MODEL_CATALOGS.codex, '<a href="/api/docs/models/gpt-6-sol">GPT</a>'],
  [MODEL_CATALOGS.grok, '{"name":"grok-4.7"}'],
  [MODEL_CATALOGS.antigravity, '<a href="/gemini-api/docs/models/gemini-3.8-flash">Gemini</a>'],
  ['https://openai.com/news/rss.xml', '<item><title>GPT-6 Sol</title><link>https://openai.com/index/gpt-6-sol</link></item>'],
  ['https://blog.google/technology/ai/rss/', '<item><title>Gemini 3.8 Flash</title><link>https://blog.google/ai/gemini-38</link></item>'],
  ['https://www.anthropic.com/sitemap.xml', '<loc>https://www.anthropic.com/news/claude-opus-5</loc>'],
  ['https://docs.x.ai/developers/release-notes', '<h3 id="grok-47"><a href="#grok-47">Grok 4.7</a></h3><p>Grok 4.7 is now available.</p>'],
]);

describe('model news service', () => {
  it('opens only credential-free vendor URLs', () => {
    expect(allowedUrl('codex', 'https://openai.com/index/gpt-7')).toBe(true);
    expect(allowedUrl('codex', 'https://openai.com.evil.example/model')).toBe(false);
    expect(allowedUrl('codex', 'https://user:pass@openai.com/index/gpt-7')).toBe(false);
    expect(allowedUrl('grok', 'http://docs.x.ai/developers/models')).toBe(false);
  });

  it('baselines old entries, alerts on new official releases and dated announcements, then persists dismissal', async () => {
    const dir = await mkdtemp(path.join(os.tmpdir(), 'aiuw-model-news-'));
    dirs.push(dir);
    const pages = new Map(basePages);
    const changes: string[][] = [];
    const options = { userData: dir, logger: createLogger({ sinks: [] }),
      onChange: (items: { id: string }[]) => changes.push(items.map((item) => item.id)),
      fetchText: (url: string) => {
        const content = pages.get(url);
        if (content === undefined) return Promise.reject(new Error('missing fixture'));
        return Promise.resolve(content);
      }, now: () => Date.UTC(2026, 8, 30) };
    const service = await createModelNewsService(options);
    await service.checkNow();
    expect(service.current()).toEqual([]);

    pages.set(MODEL_CATALOGS.grok, '{"name":"grok-4.7"},{"name":"grok-4.8"}');
    pages.set('https://openai.com/news/rss.xml', pages.get('https://openai.com/news/rss.xml') +
      '<item><title>Introducing GPT-7 Sol</title><description>GPT-7 Sol will be available on October 12, 2026.</description><link>https://openai.com/index/gpt-7-sol</link></item>');
    await service.checkNow();
    expect(service.current().map((item) => [item.provider, item.status, item.releaseDate]))
      .toEqual([['codex', 'upcoming', '2026-10-12'], ['grok', 'released', null]]);
    await service.dismiss('codex');
    expect(service.current().map((item) => item.provider)).toEqual(['grok']);
    pages.set(MODEL_CATALOGS.codex, '<a href="/api/docs/models/gpt-6-sol">GPT</a><a href="/api/docs/models/gpt-7-sol">GPT</a>');
    await service.checkNow();
    expect(service.current().find((item) => item.provider === 'codex')?.status).toBe('released');
    const saved = JSON.parse(await readFile(path.join(dir, 'model-news.json'), 'utf8')) as { dismissed: string[] };
    expect(saved.dismissed).toContain('upcoming:codex:gpt7sol');
    expect(changes.length).toBeGreaterThan(1);
    service.stop();
  });

  it('ignores failed sources until their first successful baseline', async () => {
    const dir = await mkdtemp(path.join(os.tmpdir(), 'aiuw-model-news-'));
    dirs.push(dir);
    const pages = new Map(basePages);
    pages.delete(MODEL_CATALOGS.grok);
    const service = await createModelNewsService({ userData: dir, logger: createLogger({ sinks: [] }), onChange: () => {},
      fetchText: (url) => { const body = pages.get(url); return body === undefined ? Promise.reject(new Error('offline')) : Promise.resolve(body); } });
    await service.checkNow();
    pages.set(MODEL_CATALOGS.grok, '{"name":"grok-4.8"}');
    await service.checkNow();
    expect(service.current()).toEqual([]);
    service.stop();
  });

  it('reports each check and which sources failed, counting repeats and clearing on recovery', async () => {
    const dir = await mkdtemp(path.join(os.tmpdir(), 'aiuw-model-news-'));
    dirs.push(dir);
    const pages = new Map(basePages);
    // A page whose layout changed: fetched fine, but no model IDs match any more.
    pages.set(MODEL_CATALOGS.antigravity, '<main>redesigned</main>');
    let clock = Date.UTC(2026, 8, 30, 1);
    const reports: { checkedAt: number | null; sources: number; failing: { provider: string; kind: string; since: number; count: number }[] }[] = [];
    const service = await createModelNewsService({ userData: dir, logger: createLogger({ sinks: [] }), onChange: () => {},
      onHealth: (health) => reports.push(health), now: () => clock,
      fetchText: (url) => { const body = pages.get(url); return body === undefined ? Promise.reject(new Error('offline')) : Promise.resolve(body); } });
    expect(service.health()).toEqual({ checkedAt: null, sources: 8, failing: [] });

    await service.checkNow();
    expect(reports.at(-1)).toEqual({ checkedAt: clock, sources: 8, failing: [{ provider: 'antigravity', kind: 'catalog', since: clock, count: 1 }] });
    const firstFailure = clock;
    clock += 6 * 3_600_000;
    pages.delete('https://openai.com/news/rss.xml');
    await service.checkNow();
    expect(reports.at(-1)?.failing).toEqual([
      { provider: 'antigravity', kind: 'catalog', since: firstFailure, count: 2 },
      { provider: 'codex', kind: 'news', since: clock, count: 1 },
    ]);

    clock += 6 * 3_600_000;
    pages.set(MODEL_CATALOGS.antigravity, basePages.get(MODEL_CATALOGS.antigravity)!);
    pages.set('https://openai.com/news/rss.xml', basePages.get('https://openai.com/news/rss.xml')!);
    await service.checkNow();
    expect(reports.at(-1)).toEqual({ checkedAt: clock, sources: 8, failing: [] });
    service.stop();
  });

  it('looks again 15 minutes after a check with failed sources instead of waiting the full interval', async () => {
    const dir = await mkdtemp(path.join(os.tmpdir(), 'aiuw-model-news-'));
    dirs.push(dir);
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'setInterval', 'clearInterval'] });
    try {
      const pages = new Map(basePages);
      pages.delete(MODEL_CATALOGS.antigravity);
      let catalogFetches = 0;
      const reports: { failing: unknown[] }[] = [];
      const service = await createModelNewsService({ userData: dir, logger: createLogger({ sinks: [] }), onChange: () => {},
        onHealth: (health) => reports.push(health),
        fetchText: (url) => {
          if (url === MODEL_CATALOGS.antigravity) catalogFetches += 1;
          const body = pages.get(url);
          return body === undefined ? Promise.reject(new Error('timeout')) : Promise.resolve(body);
        } });
      service.start();
      await vi.waitFor(() => expect(reports).toHaveLength(1));
      expect(reports[0]?.failing).toHaveLength(1);
      pages.set(MODEL_CATALOGS.antigravity, basePages.get(MODEL_CATALOGS.antigravity)!);
      await vi.advanceTimersByTimeAsync(RETRY_AFTER_FAILURE_MS - 1_000);
      expect(catalogFetches).toBe(1);
      await vi.advanceTimersByTimeAsync(1_000);
      await vi.waitFor(() => expect(reports).toHaveLength(2));
      expect(catalogFetches).toBe(2);
      expect(reports[1]?.failing).toEqual([]);
      // A clean check schedules no further early retry.
      await vi.advanceTimersByTimeAsync(RETRY_AFTER_FAILURE_MS * 2);
      expect(reports).toHaveLength(2);
      service.stop();
    } finally {
      vi.useRealTimers();
    }
  });

  it('counts the Anthropic source as failed when every new article fails, and retries those articles later', async () => {
    const dir = await mkdtemp(path.join(os.tmpdir(), 'aiuw-model-news-'));
    dirs.push(dir);
    const pages = new Map(basePages);
    const fetched: string[] = [];
    const reports: { failing: { provider: string; kind: string }[] }[] = [];
    const service = await createModelNewsService({ userData: dir, logger: createLogger({ sinks: [] }), onChange: () => {},
      onHealth: (health) => reports.push(health),
      fetchText: (url) => { fetched.push(url); const body = pages.get(url); return body === undefined ? Promise.reject(new Error('offline')) : Promise.resolve(body); } });
    await service.checkNow();
    const article = 'https://www.anthropic.com/news/claude-opus-6';
    pages.set('https://www.anthropic.com/sitemap.xml', `<loc>https://www.anthropic.com/news/claude-opus-5</loc><loc>${article}</loc>`);
    await service.checkNow();
    expect(reports.at(-1)?.failing).toEqual([expect.objectContaining({ provider: 'claude', kind: 'news' })]);

    pages.set(article, '<meta property="og:title" content="Claude Opus 6"><meta name="description" content="Claude Opus 6 is now available.">');
    await service.checkNow();
    expect(fetched.filter((url) => url === article)).toHaveLength(2);
    expect(reports.at(-1)?.failing).toEqual([]);
    expect(service.current().map((item) => [item.provider, item.status])).toContainEqual(['claude', 'released']);
    service.stop();
  });
});

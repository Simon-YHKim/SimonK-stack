import { describe, expect, it } from 'vitest';
import { parseCatalog } from './catalog';

describe('official model catalogs', () => {
  it('reads only linked chat models, not body mentions or media variants', () => {
    expect(parseCatalog('codex', '<a href="/api/docs/models/gpt-6.1-sol">GPT</a> gpt-7 <a href="/api/docs/models/gpt-6-image">image</a>'))
      .toEqual([{ id: 'gpt-6.1-sol', url: 'https://developers.openai.com/api/docs/models/gpt-6.1-sol' }]);
    expect(parseCatalog('claude', 'aria-label="Copy model ID claude-opus-5" claude-opus-6'))
      .toEqual([{ id: 'claude-opus-5', url: 'https://platform.claude.com/docs/en/models/overview' }]);
    expect(parseCatalog('grok', '{"name":"grok-4.7"},{"name":"grok-4.7-latest"}'))
      .toEqual([{ id: 'grok-4.7', url: 'https://docs.x.ai/developers/models' }]);
    expect(parseCatalog('antigravity', '<a href="/gemini-api/docs/models/gemini-3.8-flash">Gemini</a>'))
      .toEqual([{ id: 'gemini-3.8-flash', url: 'https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash' }]);
  });
});

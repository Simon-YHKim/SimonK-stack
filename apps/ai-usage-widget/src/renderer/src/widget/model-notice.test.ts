import { describe, expect, it } from 'vitest';
import type { ModelNotice } from '../../../shared/types';
import { modelNoticeText } from '../../../shared/model-notice';

const notice: ModelNotice = { id: 'upcoming:codex:gpt7sol', provider: 'codex', model: 'GPT-7 Sol', status: 'upcoming', releaseDate: '2026-10-12', url: 'https://openai.com/index/gpt-7-sol', observedAt: 1 };

describe('model notice wording', () => {
  it('shows calendar days without assuming a release hour', () => {
    expect(modelNoticeText(notice, 'ko', new Date(2026, 9, 10, 23, 0).getTime())).toContain('D-2');
    expect(modelNoticeText(notice, 'ko', new Date(2026, 9, 12, 1, 0).getTime())).toContain('D-day');
  });
  it('never silently turns an unconfirmed announcement into a release', () => {
    expect(modelNoticeText(notice, 'ko', new Date(2026, 9, 13).getTime())).toContain('공식 출시 확인 중');
    expect(modelNoticeText({ ...notice, status: 'released', releaseDate: null }, 'ko', Date.now())).toContain('사용해보세요');
  });
});

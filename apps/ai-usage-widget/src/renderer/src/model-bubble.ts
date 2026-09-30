import { modelNoticeText } from '../../shared/model-notice';
import type { Locale, ModelNotice } from '../../shared/types';

const params = new URLSearchParams(window.location.search);
const locale: Locale = params.get('locale') === 'en' ? 'en' : 'ko';
const status: ModelNotice['status'] = params.get('status') === 'upcoming' ? 'upcoming' : 'released';
const date = params.get('date');
const notice = {
  model: (params.get('model') ?? '').slice(0, 90), status,
  releaseDate: date !== null && /^\d{4}-\d{2}-\d{2}$/.test(date) ? date : null,
};
document.documentElement.lang = locale;
document.body.dataset.scheme = params.get('scheme') === 'light' ? 'light' : 'dark';
document.body.dataset.below = params.get('below') === 'true' ? 'true' : 'false';
const title = document.getElementById('title');
const model = document.getElementById('model');
const detail = document.getElementById('detail');
if (title !== null && model !== null && detail !== null) {
  if (params.get('kind') === 'pace') {
    const recent = Number(params.get('recent'));
    const usual = params.has('usual') ? Number(params.get('usual')) : null;
    title.textContent = locale === 'ko' ? '한도 사용률 급증' : 'Quota usage rising fast';
    model.textContent = notice.model;
    detail.textContent = Number.isFinite(recent) && recent >= 0
      ? (locale === 'ko' ? `최근 ${recent.toFixed(1)}%p/시간` : `Recent ${recent.toFixed(1)} pp/hour`) +
        (usual !== null && Number.isFinite(usual) && usual >= 0
          ? locale === 'ko' ? ` · 이전 ${usual.toFixed(1)}%p/시간` : ` · earlier ${usual.toFixed(1)} pp/hour`
          : '')
      : '';
  } else {
    title.textContent = locale === 'ko' ? (status === 'upcoming' ? '출시 예정' : '새 모델 출시') :
      (status === 'upcoming' ? 'Coming soon' : 'New model released');
    model.textContent = notice.model;
    detail.textContent = modelNoticeText(notice, locale, Date.now()).slice(notice.model.length).trim();
  }
}

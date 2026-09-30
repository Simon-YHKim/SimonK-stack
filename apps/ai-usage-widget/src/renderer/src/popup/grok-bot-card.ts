import { grokBotReading, type GrokBotAutoUsage } from '../../../shared/grok-bot';
import { formatCountdown } from '../../../shared/usage';
import type { Settings } from '../../../shared/settings';
import { h, setStyles, setText } from '../dom';
import type { Api } from '../api';
import { providerIcon } from '../icons';
import type { RenderContext } from '../model';

/** Grok Bot's weekly meter, separate from the Grok Build CLI account. */
export class GrokBotCard {
  readonly el: HTMLElement;
  readonly input: HTMLInputElement;
  readonly saveButton: HTMLButtonElement;
  private readonly name: HTMLElement;
  private readonly plan: HTMLElement;
  private readonly badge: HTMLElement;
  private readonly used: HTMLElement;
  private readonly left: HTMLElement;
  private readonly fill: HTMLElement;
  private readonly status: HTMLElement;
  private readonly recorded: HTMLElement;
  private readonly guide: HTMLElement;
  private readonly label: HTMLElement;
  private readonly openButton: HTMLButtonElement;
  private context: RenderContext | null = null;
  private pending = false;

  constructor(private readonly deps: { api: Api; report(message: string): void }) {
    this.name = h('div', { class: 'card-account-name' });
    this.plan = h('div', { class: 'card-account-email' });
    this.badge = h('span', { class: 'card-badge is-state' });
    this.used = h('strong', { class: 'grok-bot-used' });
    this.left = h('span', { class: 'grok-bot-left' });
    this.fill = h('span', { class: 'quota-bar-fill' });
    this.status = h('span', { class: 'grok-bot-status' });
    this.recorded = h('span', { class: 'grok-bot-recorded' });
    this.guide = h('p', { class: 'muted grok-bot-guide' });
    this.label = h('span');
    this.input = h('input', { type: 'number', min: 0, max: 100, step: 1, inputmode: 'numeric', class: 'grok-bot-input' });
    this.saveButton = h('button', { type: 'submit', class: 'grok-bot-save' });
    this.openButton = h('button', { type: 'button', class: 'grok-bot-open' });
    const form = h('form', { class: 'grok-bot-form' }, [
      h('label', { class: 'grok-bot-label' }, [this.label, this.input]),
      this.saveButton,
    ]);
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      void this.save();
    });
    this.openButton.addEventListener('click', () => {
      void this.deps.api.invoke('shell:open-external', { kind: 'link', key: 'grok-bot-usage' });
    });
    this.el = h('article', { class: 'card grok-bot-card', 'data-provider': 'grok-bot' }, [
      h('div', { class: 'card-header' }, [
        h('div', { class: 'card-account-info' }, [
          providerIcon('grok', 24, false),
          h('div', { class: 'card-account-text' }, [this.name, this.plan]),
        ]),
        h('div', { class: 'card-badges' }, [this.badge]),
      ]),
      h('div', { class: 'grok-bot-values' }, [this.used, this.left]),
      h('div', { class: 'quota-bar', 'aria-hidden': 'true' }, [this.fill]),
      h('div', { class: 'card-meta' }, [this.status, this.recorded]),
      this.guide,
      form,
      this.openButton,
    ]);
  }

  update(settings: Settings, ctx: RenderContext, automatic?: GrokBotAutoUsage): void {
    this.context = ctx;
    const { t } = ctx;
    const reading = grokBotReading(settings, ctx.now, automatic);
    this.el.dataset.state = reading.state;
    setText(this.name, t('grokBotTitle'));
    setText(this.plan, reading.state === 'automatic' ? (reading.plan ?? t('grokBotPlan')) : t('grokBotPlan'));
    setText(this.badge, t(reading.state === 'automatic' ? 'grokBotAutomatic' : 'grokBotManual'));
    setText(this.guide, t('grokBotGuide'));
    setText(this.label, t('grokBotUsedInput'));
    setText(this.saveButton, t('grokBotSave'));
    setText(this.openButton, t('grokBotOpen'));
    if (this.input.ownerDocument.activeElement !== this.input && settings.grokBotUsedPercent !== null) {
      this.input.value = String(settings.grokBotUsedPercent);
    }
    if (reading.state === 'fresh' || reading.state === 'stale' || reading.state === 'automatic') {
      setText(this.used, `${reading.usedPercent}% ${t('unitUsed')}`);
      setText(this.left, `${reading.leftPercent}% ${t('unitLeft')}`);
      setStyles(this.fill, { width: `${reading.usedPercent}%` });
    } else {
      setText(this.used, '—');
      setText(this.left, '');
      setStyles(this.fill, { width: '0%' });
    }
    const statusKey = reading.state === 'automatic' ? 'grokBotAutomatic' : reading.state === 'stale' ? 'grokBotStale' :
      reading.state === 'expired' ? 'grokBotExpired' : reading.state !== 'unknown' ? 'grokBotManual' :
      automatic?.state === 'login-expired' ? 'grokBotAutoExpired' : automatic?.state === 'unavailable' ? 'grokBotAutoUnavailable' :
      automatic?.state === 'error' ? 'grokBotAutoError' : 'grokBotUnknown';
    setText(this.status, reading.state === 'automatic' && reading.resetsAt !== null ?
      `${t(statusKey)} · ${t('resetLabel', { time: formatCountdown(reading.resetsAt - ctx.now) })}` : t(statusKey));
    const time = reading.recordedAt === null ? '' : new Date(reading.recordedAt).toLocaleString(ctx.locale === 'ko' ? 'ko-KR' : 'en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });
    setText(this.recorded, time === '' ? '' : t(reading.state === 'automatic' ? 'grokBotMeasured' : 'grokBotRecorded', { time }));
  }

  private async save(): Promise<void> {
    if (this.pending || this.context === null) return;
    const t = this.context.t;
    const used = Number(this.input.value);
    if (this.input.value.trim() === '' || !Number.isInteger(used) || used < 0 || used > 100) {
      this.deps.report(t('grokBotInvalid'));
      this.input.focus();
      return;
    }
    this.pending = true;
    this.saveButton.disabled = true;
    try {
      const result = await this.deps.api.invoke('settings:update', { patch: { grokBotUsedPercent: used } });
      this.deps.report(t(result.ok ? 'grokBotSaved' : 'grokBotSaveFailed'));
    } catch {
      this.deps.report(t('grokBotSaveFailed'));
    } finally {
      this.pending = false;
      this.saveButton.disabled = false;
    }
  }
}

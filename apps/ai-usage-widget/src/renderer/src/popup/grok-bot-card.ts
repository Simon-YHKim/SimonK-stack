import {
  GROK_BOT_STATUS_KEYS,
  formatUsdCents,
  grokBotOnDemand,
  grokBotReading,
  grokBotWeeklyExhausted,
  parseUsdToCents,
  type GrokBotReading,
} from '../../../shared/grok-bot';
import { GROK_BOT_MAX_CENTS, type Settings } from '../../../shared/settings';
import { formatCountdown } from '../../../shared/usage';
import { h, setAttr, setStyles, setText } from '../dom';
import type { Api } from '../api';
import { providerIcon } from '../icons';
import type { RenderContext } from '../model';

const HOUR_MS = 60 * 60 * 1000;
const DAY_MS = 24 * HOUR_MS;
/** The Grok Bot countdown never runs past a week (see GROK_BOT_MAX_RESET_AHEAD_MS). */
const MAX_RESET_DAYS = 7;

function centsText(cents: number | null): string {
  return cents === null ? '' : (cents / 100).toFixed(2);
}

/**
 * A user-entered reading, kept separate from the Grok Build CLI account and its meter.
 * Grok Bot is metered on the Cursor account (cursor.com/help/grok-bot/plans); no public API
 * returns it for personal accounts, so every value here is transcribed by the user.
 */
export class GrokBotCard {
  readonly el: HTMLElement;
  readonly input: HTMLInputElement;
  readonly saveButton: HTMLButtonElement;
  readonly resetDays: HTMLInputElement;
  readonly resetHours: HTMLInputElement;
  readonly spentInput: HTMLInputElement;
  readonly limitInput: HTMLInputElement;
  private readonly form: HTMLFormElement;
  private readonly name: HTMLElement;
  private readonly plan: HTMLElement;
  private readonly badge: HTMLElement;
  private readonly used: HTMLElement;
  private readonly left: HTMLElement;
  private readonly fill: HTMLElement;
  private readonly status: HTMLElement;
  private readonly recorded: HTMLElement;
  private readonly resetLine: HTMLElement;
  private readonly onDemandLine: HTMLElement;
  private readonly spill: HTMLElement;
  private readonly guide: HTMLElement;
  private readonly separate: HTMLElement;
  private readonly guideBox: HTMLElement;
  private readonly moreBody: HTMLElement;
  private readonly label: HTMLElement;
  private readonly moreSummary: HTMLElement;
  private readonly resetLabel: HTMLElement;
  private readonly daysUnit: HTMLElement;
  private readonly hoursUnit: HTMLElement;
  private readonly spentLabel: HTMLElement;
  private readonly limitLabel: HTMLElement;
  private readonly openButton: HTMLButtonElement;
  private context: RenderContext | null = null;
  private pending = false;
  /** The reset countdown is only sent when the user touched it; otherwise the saved one stays. */
  private resetDirty = false;

  constructor(private readonly deps: { api: Api; report(message: string): void }) {
    this.name = h('div', { class: 'card-account-name' });
    this.plan = h('div', { class: 'card-account-email' });
    this.badge = h('span', { class: 'card-badge is-state' });
    this.used = h('strong', { class: 'grok-bot-used' });
    this.left = h('span', { class: 'grok-bot-left' });
    this.fill = h('span', { class: 'quota-bar-fill' });
    this.status = h('span', { class: 'grok-bot-status' });
    this.recorded = h('span', { class: 'grok-bot-recorded' });
    this.resetLine = h('p', { class: 'grok-bot-line grok-bot-reset', hidden: true });
    this.onDemandLine = h('p', { class: 'grok-bot-line grok-bot-ondemand', hidden: true });
    this.spill = h('p', { class: 'grok-bot-line grok-bot-spill', role: 'status', hidden: true });
    this.guide = h('p', { class: 'muted grok-bot-guide' });
    this.separate = h('p', { class: 'muted grok-bot-guide grok-bot-separate' });
    this.label = h('span');
    this.input = h('input', { type: 'number', min: 0, max: 100, step: 1, inputmode: 'numeric', class: 'grok-bot-input' });
    this.saveButton = h('button', { type: 'submit', class: 'grok-bot-save' });

    this.resetLabel = h('span');
    this.daysUnit = h('span', { class: 'grok-bot-unit' });
    this.hoursUnit = h('span', { class: 'grok-bot-unit' });
    this.resetDays = h('input', { type: 'number', min: 0, max: MAX_RESET_DAYS, step: 1, inputmode: 'numeric', class: 'grok-bot-input grok-bot-reset-days' });
    this.resetHours = h('input', { type: 'number', min: 0, max: 23, step: 1, inputmode: 'numeric', class: 'grok-bot-input grok-bot-reset-hours' });
    this.spentLabel = h('span');
    this.limitLabel = h('span');
    this.spentInput = h('input', { type: 'text', inputmode: 'decimal', autocomplete: 'off', class: 'grok-bot-input grok-bot-spent' });
    this.limitInput = h('input', { type: 'text', inputmode: 'decimal', autocomplete: 'off', class: 'grok-bot-input grok-bot-limit' });
    this.moreSummary = h('summary', { class: 'grok-bot-more-summary' });
    for (const field of [this.resetDays, this.resetHours]) {
      field.addEventListener('input', () => {
        this.resetDirty = true;
      });
    }
    this.guideBox = h('div', { class: 'grok-bot-guide-box' }, [this.guide, this.separate]);
    this.moreBody = h('div', { class: 'grok-bot-more-body' }, [
      h('div', { class: 'grok-bot-label', role: 'group' }, [
        this.resetLabel,
        h('div', { class: 'grok-bot-reset-row' }, [this.resetDays, this.daysUnit, this.resetHours, this.hoursUnit]),
      ]),
      h('label', { class: 'grok-bot-label' }, [this.spentLabel, this.spentInput]),
      h('label', { class: 'grok-bot-label' }, [this.limitLabel, this.limitInput]),
    ]);
    const more = h('details', { class: 'grok-bot-more' }, [this.moreSummary, this.moreBody]);

    // novalidate: the card reports its own messages (native constraint bubbles would block the
    // submit silently for an out-of-range field and never reach save()).
    this.form = h('form', { class: 'grok-bot-form', novalidate: true }, [
      h('div', { class: 'grok-bot-form-row' }, [h('label', { class: 'grok-bot-label' }, [this.label, this.input]), this.saveButton]),
      more,
    ]);
    this.form.addEventListener('submit', (event) => {
      event.preventDefault();
      void this.save();
    });
    this.openButton = h('button', { type: 'button', class: 'grok-bot-open' });
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
      this.resetLine,
      this.onDemandLine,
      this.spill,
      this.guideBox,
      this.form,
      this.openButton,
    ]);
  }

  /**
   * Where to read the values matters until a current reading exists; after that the two
   * paragraphs move into the collapsed section so the everyday card stays short.
   */
  private placeGuide(current: boolean): void {
    if (current) {
      if (this.guideBox.parentElement !== this.moreBody) this.moreBody.prepend(this.guideBox);
    } else if (this.guideBox.parentElement !== this.el) {
      this.el.insertBefore(this.guideBox, this.form);
    }
  }

  update(settings: Settings, ctx: RenderContext): void {
    this.context = ctx;
    const { t } = ctx;
    const reading = grokBotReading(settings, ctx.now);
    this.el.dataset.state = reading.state;
    this.placeGuide(reading.state === 'fresh' || reading.state === 'stale');
    setText(this.name, t('grokBotTitle'));
    setText(this.plan, t('grokBotPlan'));
    setText(this.badge, t('grokBotManual'));
    setText(this.guide, t('grokBotGuide'));
    setText(this.separate, t('grokBotSeparateMeter'));
    setText(this.label, t('grokBotUsedInput'));
    setText(this.saveButton, t('grokBotSave'));
    setText(this.openButton, t('grokBotOpen'));
    setText(this.moreSummary, t('grokBotMore'));
    setText(this.resetLabel, t('grokBotResetInput'));
    setText(this.daysUnit, t('grokBotResetDays'));
    setText(this.hoursUnit, t('grokBotResetHours'));
    setText(this.spentLabel, t('grokBotSpentInput'));
    setText(this.limitLabel, t('grokBotLimitInput'));
    setAttr(this.resetDays, 'aria-label', `${t('grokBotResetInput')} · ${t('grokBotResetDays')}`);
    setAttr(this.resetHours, 'aria-label', `${t('grokBotResetInput')} · ${t('grokBotResetHours')}`);

    // Never overwrite what the user is typing.
    if (!this.form.contains(this.form.ownerDocument.activeElement)) this.fillInputs(settings, reading, ctx.now);

    if (reading.state === 'fresh' || reading.state === 'stale') {
      setText(this.used, `${reading.usedPercent}% ${t('unitUsed')}`);
      setText(this.left, `${reading.leftPercent}% ${t('unitLeft')}`);
      setStyles(this.fill, { width: `${reading.usedPercent}%` });
    } else {
      setText(this.used, '—');
      setText(this.left, '');
      setStyles(this.fill, { width: '0%' });
    }
    setText(this.status, t(GROK_BOT_STATUS_KEYS[reading.state]));
    const time = reading.recordedAt === null ? '' : new Date(reading.recordedAt).toLocaleString(ctx.locale === 'ko' ? 'ko-KR' : 'en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });
    setText(this.recorded, time === '' ? '' : t('grokBotRecorded', { time }));

    const resetsAt = reading.state === 'fresh' || reading.state === 'stale' ? reading.resetsAt : null;
    this.resetLine.hidden = resetsAt === null;
    setText(this.resetLine, resetsAt === null ? '' : t('grokBotResetsIn', { time: formatCountdown(resetsAt - ctx.now) }));

    const onDemand = grokBotOnDemand(settings);
    this.onDemandLine.hidden = onDemand === null;
    let onDemandText = '';
    if (onDemand !== null) {
      const { spentCents, limitCents } = onDemand;
      if (spentCents !== null && limitCents !== null) {
        onDemandText = t('grokBotOnDemand', { spent: formatUsdCents(spentCents), limit: formatUsdCents(limitCents) });
      } else if (spentCents !== null) {
        onDemandText = t('grokBotOnDemandSpentOnly', { spent: formatUsdCents(spentCents) });
      } else if (limitCents !== null) {
        onDemandText = t('grokBotOnDemandLimitOnly', { limit: formatUsdCents(limitCents) });
      }
    }
    setText(this.onDemandLine, onDemandText);

    const exhausted = grokBotWeeklyExhausted(reading);
    this.spill.hidden = !exhausted;
    setText(this.spill, exhausted ? t('grokBotSpill') : '');
  }

  private fillInputs(settings: Settings, reading: GrokBotReading, now: number): void {
    if (settings.grokBotUsedPercent !== null) this.input.value = String(settings.grokBotUsedPercent);
    if (!this.resetDirty) {
      const resetsAt = reading.state === 'fresh' || reading.state === 'stale' ? reading.resetsAt : null;
      if (resetsAt === null) {
        this.resetDays.value = '';
        this.resetHours.value = '';
      } else {
        const remaining = Math.max(0, resetsAt - now);
        this.resetDays.value = String(Math.floor(remaining / DAY_MS));
        this.resetHours.value = String(Math.floor((remaining % DAY_MS) / HOUR_MS));
      }
    }
    this.spentInput.value = centsText(settings.grokBotOnDemandSpentCents);
    this.limitInput.value = centsText(settings.grokBotOnDemandLimitCents);
  }

  /** undefined = invalid, null = cleared, number = cents. */
  private moneyField(input: HTMLInputElement): number | null | undefined {
    const text = input.value.trim();
    if (text === '') return null;
    const cents = parseUsdToCents(text);
    return cents === undefined || cents > GROK_BOT_MAX_CENTS ? undefined : cents;
  }

  /** undefined = invalid, null = cleared, number = epoch ms of the next reset. */
  private resetField(): number | null | undefined {
    const daysText = this.resetDays.value.trim();
    const hoursText = this.resetHours.value.trim();
    if (daysText === '' && hoursText === '') return null;
    const days = daysText === '' ? 0 : Number(daysText);
    const hours = hoursText === '' ? 0 : Number(hoursText);
    if (!Number.isInteger(days) || !Number.isInteger(hours) || days < 0 || days > MAX_RESET_DAYS || hours < 0 || hours > 23) return undefined;
    if (days === 0 && hours === 0) return undefined;
    return Date.now() + days * DAY_MS + hours * HOUR_MS;
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
    const patch: Partial<Settings> = { grokBotUsedPercent: used };
    if (this.resetDirty) {
      const resetAt = this.resetField();
      if (resetAt === undefined) {
        this.deps.report(t('grokBotInvalidReset'));
        this.resetDays.focus();
        return;
      }
      patch.grokBotResetAt = resetAt;
    }
    for (const [key, field] of [['grokBotOnDemandSpentCents', this.spentInput], ['grokBotOnDemandLimitCents', this.limitInput]] as const) {
      const cents = this.moneyField(field);
      if (cents === undefined) {
        this.deps.report(t('grokBotInvalidMoney'));
        field.focus();
        return;
      }
      patch[key] = cents;
    }
    this.pending = true;
    this.saveButton.disabled = true;
    try {
      const result = await this.deps.api.invoke('settings:update', { patch });
      if (result.ok) this.resetDirty = false;
      this.deps.report(t(result.ok ? 'grokBotSaved' : 'grokBotSaveFailed'));
    } catch {
      this.deps.report(t('grokBotSaveFailed'));
    } finally {
      this.pending = false;
      this.saveButton.disabled = false;
    }
  }
}

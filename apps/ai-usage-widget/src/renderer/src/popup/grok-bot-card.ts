import {
  GROK_BOT_MAX_RESET_AHEAD_MS,
  GROK_BOT_STATUS_KEYS,
  formatUsdCents,
  grokBotOnDemand,
  grokBotReading,
  grokBotSpillKey,
  grokBotWeeklyExhausted,
  parseUsdToCents,
  type GrokBotReading,
} from '../../../shared/grok-bot';
import { GROK_BOT_MAX_CENTS, type Settings } from '../../../shared/settings';
import { formatCountdown } from '../../../shared/usage';
import { h, setStyles, setText } from '../dom';
import type { Api } from '../api';
import { providerIcon } from '../icons';
import type { RenderContext } from '../model';

function centsText(cents: number | null): string {
  return cents === null ? '' : (cents / 100).toFixed(2);
}

function pad(value: number): string {
  return String(value).padStart(2, '0');
}

/** Epoch ms -> `YYYY-MM-DDTHH:mm` in local time, the value format of `<input type="datetime-local">`. */
export function toLocalDateTimeValue(ms: number): string {
  const d = new Date(ms);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** `YYYY-MM-DDTHH:mm` read as local time (grok.com shows the reset in the viewer's time zone); else undefined. */
export function fromLocalDateTimeValue(value: string): number | undefined {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/.exec(value.trim());
  if (match === null) return undefined;
  const [year, month, day, hour, minute] = match.slice(1).map(Number) as [number, number, number, number, number];
  const d = new Date(year, month - 1, day, hour, minute);
  // Reject rollovers such as 02-30 that Date would silently move to March.
  if (d.getFullYear() !== year || d.getMonth() !== month - 1 || d.getDate() !== day || d.getHours() !== hour || d.getMinutes() !== minute) {
    return undefined;
  }
  return d.getTime();
}

/**
 * A user-entered reading, kept separate from the Grok Build CLI account and its meter. The CLI's
 * `_x.ai/billing` answers the SuperGrok weekly limit only (probe 26.09.30); grok.com shows
 * "Weekly Grok Bot Limit" as its own meter and no public API returns it, so the values here
 * are transcribed by the user.
 */
export class GrokBotCard {
  readonly el: HTMLElement;
  readonly input: HTMLInputElement;
  readonly saveButton: HTMLButtonElement;
  readonly resetInput: HTMLInputElement;
  readonly spentInput: HTMLInputElement;
  readonly limitInput: HTMLInputElement;
  readonly openGrokButton: HTMLButtonElement;
  readonly openCursorButton: HTMLButtonElement;
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
  private readonly spentLabel: HTMLElement;
  private readonly limitLabel: HTMLElement;
  private context: RenderContext | null = null;
  private pending = false;
  /** The reset time is only sent when the user touched it; otherwise the saved one stays. */
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
    this.resetInput = h('input', { type: 'datetime-local', step: 60, class: 'grok-bot-input grok-bot-reset-at' });
    this.resetInput.addEventListener('input', () => {
      this.resetDirty = true;
    });
    this.spentLabel = h('span');
    this.limitLabel = h('span');
    this.spentInput = h('input', { type: 'text', inputmode: 'decimal', autocomplete: 'off', class: 'grok-bot-input grok-bot-spent' });
    this.limitInput = h('input', { type: 'text', inputmode: 'decimal', autocomplete: 'off', class: 'grok-bot-input grok-bot-limit' });
    this.moreSummary = h('summary', { class: 'grok-bot-more-summary' });
    this.guideBox = h('div', { class: 'grok-bot-guide-box' }, [this.guide, this.separate]);
    this.moreBody = h('div', { class: 'grok-bot-more-body' }, [
      h('label', { class: 'grok-bot-label' }, [this.resetLabel, this.resetInput]),
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
    this.openGrokButton = h('button', { type: 'button', class: 'grok-bot-open grok-bot-open-grok' });
    this.openGrokButton.addEventListener('click', () => {
      void this.deps.api.invoke('shell:open-external', { kind: 'link', key: 'grok-usage' });
    });
    this.openCursorButton = h('button', { type: 'button', class: 'grok-bot-open grok-bot-open-cursor' });
    this.openCursorButton.addEventListener('click', () => {
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
      h('div', { class: 'grok-bot-links' }, [this.openGrokButton, this.openCursorButton]),
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
    setText(this.openGrokButton, t('grokBotOpenGrok'));
    setText(this.openCursorButton, t('grokBotOpen'));
    setText(this.moreSummary, t('grokBotMore'));
    setText(this.resetLabel, t('grokBotResetInput'));
    setText(this.spentLabel, t('grokBotSpentInput'));
    setText(this.limitLabel, t('grokBotLimitInput'));

    // Never overwrite what the user is typing.
    if (!this.form.contains(this.form.ownerDocument.activeElement)) this.fillInputs(settings, reading);

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
    setText(this.spill, exhausted ? t(grokBotSpillKey(settings.grokBotOnDemandLimitCents)) : '');
  }

  private fillInputs(settings: Settings, reading: GrokBotReading): void {
    if (settings.grokBotUsedPercent !== null) this.input.value = String(settings.grokBotUsedPercent);
    if (!this.resetDirty) {
      const resetsAt = reading.state === 'fresh' || reading.state === 'stale' ? reading.resetsAt : null;
      this.resetInput.value = resetsAt === null ? '' : toLocalDateTimeValue(resetsAt);
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

  /** undefined = invalid, null = cleared, number = epoch ms of the next reset (future, within the weekly bound). */
  private resetField(): number | null | undefined {
    const text = this.resetInput.value.trim();
    if (text === '') return null;
    const at = fromLocalDateTimeValue(text);
    const now = Date.now();
    if (at === undefined || at <= now || at - now > GROK_BOT_MAX_RESET_AHEAD_MS) return undefined;
    return at;
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
        this.resetInput.focus();
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

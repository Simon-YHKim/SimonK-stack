import { LOGIN_STAGE_KEYS, type Translator } from '../../../shared/i18n';
import { PASTE_MAX_LENGTH, isAllowedExternalUrl } from '../../../shared/ipc';
import type { LoginEventMessage, ProviderId } from '../../../shared/types';
import { ipcErrorCode, type Api } from '../api';
import { copyText, selectText } from '../clipboard';
import { h, setAttr, setText } from '../dom';
import { checkGlyph, copyGlyph } from '../icons';
import { errorText } from '../model';
import { IDLE, isLoginBusy, reduceLogin, type LoginAction, type LoginFlow } from './login-machine';

export interface LoginPanelDeps {
  api: Api;
  translator: () => Translator;
  /** Called after every state change so the owner can update surrounding controls. */
  onChange?: (flow: LoginFlow) => void;
}

export function isValidPaste(text: string): boolean {
  const trimmed = text.trim();
  return trimmed.length > 0 && trimmed.length <= PASTE_MAX_LENGTH && !/[\r\n]/.test(trimmed);
}

/** One account's login flow UI. Elements persist across updates so focus and typed text survive. */
export class LoginPanel {
  readonly el: HTMLElement;
  private flow: LoginFlow = IDLE;
  private copiedTimer: ReturnType<typeof setTimeout> | null = null;

  private readonly statusEl: HTMLParagraphElement;
  private readonly hintEl: HTMLParagraphElement;
  private readonly codeRow: HTMLDivElement;
  readonly codeEl: HTMLElement;
  readonly copyButton: HTMLButtonElement;
  readonly openButton: HTMLButtonElement;
  readonly pasteForm: HTMLFormElement;
  readonly pasteInput: HTMLInputElement;
  readonly submitButton: HTMLButtonElement;
  private readonly pasteErrorEl: HTMLParagraphElement;
  readonly cancelButton: HTMLButtonElement;
  readonly retryButton: HTMLButtonElement;
  readonly closeButton: HTMLButtonElement;

  constructor(
    readonly accountId: string,
    readonly provider: ProviderId,
    private readonly deps: LoginPanelDeps,
  ) {
    this.statusEl = h('p', { class: 'login-status', role: 'status', 'aria-live': 'polite' });
    this.hintEl = h('p', { class: 'login-hint' });
    this.codeEl = h('output', { class: 'login-code' });
    this.copyButton = h('button', { type: 'button', class: 'icon-button login-copy' }, [copyGlyph()]);
    this.codeRow = h('div', { class: 'login-code-row' }, [this.codeEl, this.copyButton]);
    this.openButton = h('button', { type: 'button', class: 'btn-primary login-open' });
    this.pasteInput = h('input', {
      type: 'text',
      class: 'text-input login-paste',
      autocomplete: 'off',
      spellcheck: 'false',
      maxlength: PASTE_MAX_LENGTH,
    });
    this.submitButton = h('button', { type: 'submit', class: 'btn-secondary login-submit' });
    this.pasteErrorEl = h('p', { class: 'login-error', role: 'alert' });
    this.pasteForm = h('form', { class: 'login-paste-form' }, [
      h('div', { class: 'inline-form-row' }, [this.pasteInput, this.submitButton]),
      this.pasteErrorEl,
    ]);
    this.cancelButton = h('button', { type: 'button', class: 'btn-secondary login-cancel' });
    this.retryButton = h('button', { type: 'button', class: 'btn-primary login-retry' });
    this.closeButton = h('button', { type: 'button', class: 'btn-secondary login-close' });
    this.el = h('div', { class: 'login-panel', 'data-account-id': accountId, 'data-provider': provider, hidden: true }, [
      this.statusEl,
      this.hintEl,
      this.codeRow,
      this.openButton,
      this.pasteForm,
      h('div', { class: 'login-actions' }, [this.retryButton, this.cancelButton, this.closeButton]),
    ]);

    this.copyButton.addEventListener('click', () => void this.copyCode());
    this.openButton.addEventListener('click', () => this.openLoginPage());
    this.pasteForm.addEventListener('submit', (event) => {
      event.preventDefault();
      this.submitPaste();
    });
    this.pasteInput.addEventListener('input', () => setAttr(this.pasteInput, 'aria-invalid', null));
    this.cancelButton.addEventListener('click', () => this.cancel());
    this.retryButton.addEventListener('click', () => this.start());
    this.closeButton.addEventListener('click', () => this.dispatch({ type: 'dismiss' }));
    this.render();
  }

  getFlow(): LoginFlow {
    return this.flow;
  }

  isBusy(): boolean {
    return isLoginBusy(this.flow);
  }

  isVisible(): boolean {
    return this.flow.phase !== 'idle';
  }

  private dispatch(action: LoginAction): void {
    const next = reduceLogin(this.flow, action, this.accountId);
    if (next === this.flow) return;
    this.flow = next;
    this.render();
    this.deps.onChange?.(next);
  }

  start(): void {
    if (this.isBusy()) return;
    this.dispatch({ type: 'start' });
    this.deps.api.invoke('login:start', { accountId: this.accountId }).then(
      (result) => {
        if (!result.ok) {
          this.dispatch({ type: 'start-failed', code: ipcErrorCode(result.error) });
          return;
        }
        if (this.flow.phase === 'idle') {
          // Cancelled while the request was pending: stop the orphan session.
          void this.deps.api.invoke('login:cancel', { sessionId: result.value.sessionId });
          return;
        }
        this.dispatch({ type: 'started', sessionId: result.value.sessionId });
      },
      () => this.dispatch({ type: 'start-failed', code: 'internal' }),
    );
  }

  /** Follow a flow started outside this panel (e.g. tray) without issuing login:start. */
  adopt(): void {
    if (!this.isBusy()) this.dispatch({ type: 'start' });
  }

  handleEvent(message: LoginEventMessage): void {
    this.dispatch({ type: 'event', message });
  }

  cancel(): void {
    const flow = this.flow;
    if (flow.phase === 'active') void this.deps.api.invoke('login:cancel', { sessionId: flow.sessionId });
    this.pasteInput.value = '';
    this.dispatch({ type: 'cancel' });
  }

  private loginTarget(): { sessionId: string; url: string } | null {
    const flow = this.flow;
    if (flow.phase !== 'active') return null;
    const url = flow.deviceCode?.verificationUrl ?? flow.url;
    return url !== null && isAllowedExternalUrl(url) ? { sessionId: flow.sessionId, url } : null;
  }

  openLoginPage(): void {
    const target = this.loginTarget();
    if (target === null) return;
    void this.deps.api.invoke('shell:open-external', { kind: 'login', sessionId: target.sessionId, url: target.url });
  }

  submitPaste(): void {
    const flow = this.flow;
    if (flow.phase !== 'active' || flow.submitting) return;
    const text = this.pasteInput.value;
    if (!isValidPaste(text)) {
      setAttr(this.pasteInput, 'aria-invalid', 'true');
      this.pasteInput.focus();
      return;
    }
    const sessionId = flow.sessionId;
    this.dispatch({ type: 'submit' });
    this.deps.api.invoke('login:submit-paste', { sessionId, text: text.trim() }).then(
      (result) => {
        if (result.ok) {
          // The code is single-use; do not keep it in the DOM.
          this.pasteInput.value = '';
          this.dispatch({ type: 'submit-done' });
        } else {
          this.dispatch({ type: 'submit-failed', code: ipcErrorCode(result.error) });
        }
      },
      () => this.dispatch({ type: 'submit-failed', code: 'internal' }),
    );
  }

  private async copyCode(): Promise<void> {
    const flow = this.flow;
    if (flow.phase !== 'active' || flow.deviceCode === null) return;
    const copied = await copyText(flow.deviceCode.userCode, this.el.ownerDocument);
    if (!copied) {
      selectText(this.codeEl);
      return;
    }
    this.copyButton.replaceChildren(checkGlyph());
    this.copyButton.classList.add('is-copied');
    if (this.copiedTimer !== null) clearTimeout(this.copiedTimer);
    this.copiedTimer = setTimeout(() => {
      this.copiedTimer = null;
      this.copyButton.replaceChildren(copyGlyph());
      this.copyButton.classList.remove('is-copied');
    }, 2000);
  }

  /** Re-applies translated text (locale change) without touching flow state. */
  render(): void {
    const t = this.deps.translator();
    const flow = this.flow;
    this.el.hidden = flow.phase === 'idle';
    this.el.dataset.phase = flow.phase;

    setText(this.openButton, t('loginOpenBrowser'));
    setText(this.submitButton, t('loginSubmit'));
    setText(this.cancelButton, t('loginCancel'));
    setText(this.retryButton, t('login'));
    setText(this.closeButton, t('close'));
    setAttr(this.pasteInput, 'placeholder', t('loginPastePlaceholder'));
    setAttr(this.pasteInput, 'aria-label', t('loginPastePlaceholder'));

    let status = '';
    let hint = '';
    let showCode = false;
    let showOpen = false;
    let showPaste = false;
    let pasteError = '';

    switch (flow.phase) {
      case 'idle':
        break;
      case 'starting':
        status = t('loginStage_starting');
        break;
      case 'active': {
        status = t(LOGIN_STAGE_KEYS[flow.stage ?? 'starting']);
        if (flow.deviceCode !== null) {
          showCode = true;
          hint = t('loginDeviceCodeHint');
          setText(this.codeEl, flow.deviceCode.userCode);
          const codeLabel = t('loginDeviceCode', { code: flow.deviceCode.userCode });
          setAttr(this.copyButton, 'aria-label', codeLabel);
          setAttr(this.copyButton, 'title', codeLabel);
        }
        showPaste = flow.needsPaste || (this.provider === 'claude' && flow.url !== null);
        if (flow.url !== null && flow.deviceCode === null) hint = t('loginUrlHint');
        showOpen = this.loginTarget() !== null;
        this.submitButton.disabled = flow.submitting;
        this.pasteInput.readOnly = flow.submitting;
        if (flow.pasteError !== null) pasteError = t('loginFailed', { error: errorText(t, flow.pasteError) });
        break;
      }
      case 'success': {
        const who = [flow.emailMasked, flow.plan].filter((part): part is string => part !== null).join(' · ');
        status = who.length > 0 ? `${t('loginSuccess')} · ${who}` : t('loginSuccess');
        break;
      }
      case 'error':
        status = t('loginFailed', { error: errorText(t, flow.code) });
        break;
    }

    setText(this.statusEl, status);
    this.statusEl.classList.toggle('is-error', flow.phase === 'error');
    this.statusEl.classList.toggle('is-success', flow.phase === 'success');
    setText(this.hintEl, hint);
    this.hintEl.hidden = hint.length === 0;
    this.codeRow.hidden = !showCode;
    if (!showCode) setText(this.codeEl, '');
    this.openButton.hidden = !showOpen;
    this.pasteForm.hidden = !showPaste;
    setText(this.pasteErrorEl, pasteError);
    this.pasteErrorEl.hidden = pasteError.length === 0;
    this.cancelButton.hidden = !isLoginBusy(flow);
    this.retryButton.hidden = flow.phase !== 'error';
    this.closeButton.hidden = flow.phase !== 'error' && flow.phase !== 'success';
  }
}

import { LOGIN_STATE_KEYS, PROVIDER_NAME_KEYS, type Translator } from '../../../shared/i18n';
import type { ExternalLinkKey } from '../../../shared/ipc';
import {
  PROVIDER_IDS,
  type AccountDTO,
  type AppStateSnapshot,
  type ClaudeBridgeStatus,
  type CliStatusDTO,
  type ErrorCode,
  type LoginEventMessage,
  type ProviderId,
} from '../../../shared/types';
import { LABEL_MAX_LENGTH, normalizeLabel } from '../../../shared/validate';
import { describeError, ipcErrorCode, type Api } from '../api';
import { h, setAttr, setText, uniqueId } from '../dom';
import { relativeTimeText } from '../format';
import { providerIcon } from '../icons';
import { sortedAccounts, type RenderContext } from '../model';
import { preservingFocus, syncChildren } from './keyed';
import { LoginPanel } from './login-panel';

export interface AccountsTabDeps {
  api: Api;
  translator: () => Translator;
  report: (message: string) => void;
}

const CLI_INSTALL_KEYS: Readonly<Record<ProviderId, ExternalLinkKey>> = {
  claude: 'claude-cli-install',
  codex: 'codex-cli-install',
  grok: 'grok-cli-install',
};

export function cliStatusText(t: Translator, cli: CliStatusDTO): string {
  if (cli.state === 'unknown') return t('detectingCli');
  if (cli.state === 'missing') return t('cliNotFound');
  return cli.version !== undefined && cli.version.length > 0
    ? t('cliDetected', { version: cli.version })
    : t('cliDetectedNoVersion');
}

function onEscape(el: HTMLElement, fn: () => void): void {
  el.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    event.preventDefault();
    event.stopPropagation();
    fn();
  });
}

// ---------------------------------------------------------------------------

class AccountRow {
  readonly el: HTMLElement;
  readonly checkbox: HTMLInputElement;
  private readonly iconSlot: HTMLElement;
  private readonly nameEl: HTMLElement;
  private readonly subEl: HTMLElement;
  readonly loginButton: HTMLButtonElement;
  readonly renameButton: HTMLButtonElement;
  readonly upButton: HTMLButtonElement;
  readonly downButton: HTMLButtonElement;
  readonly deleteButton: HTMLButtonElement;
  readonly renameForm: HTMLFormElement;
  readonly renameInput: HTMLInputElement;
  private readonly renameSave: HTMLButtonElement;
  private readonly renameCancel: HTMLButtonElement;
  readonly confirmBox: HTMLElement;
  private readonly confirmText: HTMLElement;
  readonly confirmButton: HTMLButtonElement;
  private readonly confirmCancel: HTMLButtonElement;
  readonly panelSlot: HTMLElement;
  private dto: AccountDTO;
  private iconKey = '';

  constructor(
    dto: AccountDTO,
    private readonly tab: AccountsTab,
  ) {
    this.dto = dto;
    const nameId = uniqueId('account-name');
    this.checkbox = h('input', { type: 'checkbox', class: 'chk-account' });
    this.iconSlot = h('span', { class: 'account-icon' });
    this.nameEl = h('div', { class: 'account-name', id: nameId });
    this.subEl = h('div', { class: 'account-sub' });
    this.loginButton = h('button', { type: 'button', class: 'btn-primary btn-small btn-login' });
    this.renameButton = h('button', { type: 'button', class: 'btn-secondary btn-small btn-rename' });
    this.upButton = h('button', { type: 'button', class: 'btn-order btn-move-up' }, ['▲']);
    this.downButton = h('button', { type: 'button', class: 'btn-order btn-move-down' }, ['▼']);
    this.deleteButton = h('button', { type: 'button', class: 'btn-danger btn-delete-account' });

    this.renameInput = h('input', { type: 'text', class: 'text-input', maxlength: LABEL_MAX_LENGTH });
    this.renameSave = h('button', { type: 'submit', class: 'btn-primary btn-small' });
    this.renameCancel = h('button', { type: 'button', class: 'btn-secondary btn-small' });
    this.renameForm = h('form', { class: 'inline-form rename-form', hidden: true }, [
      h('div', { class: 'inline-form-row' }, [this.renameInput, this.renameSave, this.renameCancel]),
    ]);

    this.confirmText = h('p', { class: 'confirm-text' });
    this.confirmButton = h('button', { type: 'button', class: 'btn-danger btn-confirm-delete' });
    this.confirmCancel = h('button', { type: 'button', class: 'btn-secondary btn-small' });
    this.confirmBox = h('div', { class: 'confirm-box', role: 'alertdialog', hidden: true }, [
      this.confirmText,
      h('div', { class: 'inline-form-row' }, [this.confirmButton, this.confirmCancel]),
    ]);
    this.panelSlot = h('div', { class: 'panel-slot' });

    this.el = h('div', { class: 'account-row', 'data-account-id': dto.id, 'aria-labelledby': nameId }, [
      h('div', { class: 'account-row-main' }, [
        h('div', { class: 'account-row-left' }, [
          this.checkbox,
          this.iconSlot,
          h('div', { class: 'account-text' }, [this.nameEl, this.subEl]),
        ]),
        h('div', { class: 'account-row-actions' }, [
          this.loginButton,
          this.renameButton,
          this.upButton,
          this.downButton,
          this.deleteButton,
        ]),
      ]),
      this.renameForm,
      this.confirmBox,
      this.panelSlot,
    ]);

    this.checkbox.addEventListener('change', () => this.tab.toggle(this.dto, this.checkbox));
    this.loginButton.addEventListener('click', () => this.tab.startLogin(this.dto.id, this.dto.provider));
    this.upButton.addEventListener('click', () => this.tab.reorder(this.dto.id, 'up'));
    this.downButton.addEventListener('click', () => this.tab.reorder(this.dto.id, 'down'));
    this.renameButton.addEventListener('click', () => this.openRename());
    this.renameCancel.addEventListener('click', () => this.closeRename(true));
    onEscape(this.renameInput, () => this.closeRename(true));
    this.renameForm.addEventListener('submit', (event) => {
      event.preventDefault();
      this.submitRename();
    });
    this.deleteButton.addEventListener('click', () => this.openConfirm());
    this.confirmCancel.addEventListener('click', () => this.closeConfirm(true));
    onEscape(this.confirmBox, () => this.closeConfirm(true));
    this.confirmButton.addEventListener('click', () => this.tab.remove(this.dto.id));
  }

  private openRename(): void {
    this.renameInput.value = this.dto.label;
    setAttr(this.renameInput, 'aria-invalid', null);
    this.renameForm.hidden = false;
    this.renameInput.focus();
    this.renameInput.select();
  }

  closeRename(restoreFocus: boolean): void {
    this.renameForm.hidden = true;
    if (restoreFocus) this.renameButton.focus();
  }

  private submitRename(): void {
    const label = normalizeLabel(this.renameInput.value);
    if (label === null) {
      setAttr(this.renameInput, 'aria-invalid', 'true');
      this.renameInput.focus();
      return;
    }
    this.tab.rename(this.dto.id, label, this);
  }

  private openConfirm(): void {
    this.confirmBox.hidden = false;
    this.confirmButton.focus();
  }

  closeConfirm(restoreFocus: boolean): void {
    this.confirmBox.hidden = true;
    if (restoreFocus) this.deleteButton.focus();
  }

  update(dto: AccountDTO, ctx: RenderContext, info: { first: boolean; last: boolean; cli: CliStatusDTO; loginBusy: boolean }): void {
    this.dto = dto;
    const { t, settings } = ctx;
    const mono = settings.iconStyle === 'monochrome';
    const iconKey = `${dto.provider}:${String(mono)}`;
    if (iconKey !== this.iconKey) {
      this.iconKey = iconKey;
      this.iconSlot.replaceChildren(providerIcon(dto.provider, 20, mono));
    }
    this.el.dataset.enabled = String(dto.enabled);
    this.checkbox.checked = dto.enabled;
    setAttr(this.checkbox, 'aria-label', `${t('enableAccount')}: ${dto.label}`);
    setAttr(this.checkbox, 'title', t('enableAccount'));
    setText(this.nameEl, dto.label);
    const sub = [dto.emailMasked, dto.plan, t(LOGIN_STATE_KEYS[dto.loginState])].filter(
      (part): part is string => part !== undefined && part.length > 0,
    );
    setText(this.subEl, sub.join(' · '));

    const cliMissing = info.cli.state === 'missing' || dto.loginState === 'cli-missing';
    setText(this.loginButton, t('login'));
    this.loginButton.hidden = dto.loginState === 'logged-in' || dto.loginState === 'logging-in' || info.loginBusy;
    this.loginButton.disabled = cliMissing;
    setAttr(this.loginButton, 'title', cliMissing ? t('cliNotFound') : null);

    setText(this.renameButton, t('rename'));
    setAttr(this.renameInput, 'aria-label', t('accountLabelLabel'));
    setText(this.renameSave, t('save'));
    setText(this.renameCancel, t('cancel'));

    setAttr(this.upButton, 'aria-label', t('moveUp'));
    setAttr(this.upButton, 'title', t('moveUp'));
    setAttr(this.downButton, 'aria-label', t('moveDown'));
    setAttr(this.downButton, 'title', t('moveDown'));
    this.upButton.disabled = info.first;
    this.downButton.disabled = info.last;

    setText(this.deleteButton, t('deleteAccountBtn'));
    setAttr(this.deleteButton, 'title', t('deleteAccountTitle'));
    setText(this.confirmText, t('confirmDeleteAccount'));
    setText(this.confirmButton, t('deleteAccountBtn'));
    setText(this.confirmCancel, t('cancel'));
  }
}

// ---------------------------------------------------------------------------

class BridgeSection {
  readonly el: HTMLElement;
  private readonly titleEl: HTMLElement;
  private readonly descEl: HTMLElement;
  private readonly statusEl: HTMLElement;
  private readonly detailEl: HTMLElement;
  private readonly errorEl: HTMLElement;
  private readonly targetText: HTMLElement;
  readonly targetSelect: HTMLSelectElement;
  readonly installButton: HTMLButtonElement;
  readonly uninstallButton: HTMLButtonElement;
  readonly confirmBox: HTMLElement;
  private readonly confirmText: HTMLElement;
  readonly confirmButton: HTMLButtonElement;
  private readonly confirmCancel: HTMLButtonElement;
  private status: ClaudeBridgeStatus | null = null;
  private errorCode: ErrorCode | null = null;
  private busy = false;
  private accounts: AccountDTO[] = [];
  private ctx: RenderContext | null = null;

  constructor(private readonly deps: AccountsTabDeps) {
    this.titleEl = h('h4', { class: 'bridge-title' });
    this.descEl = h('p', { class: 'bridge-desc' });
    this.statusEl = h('p', { class: 'bridge-status', role: 'status' });
    this.detailEl = h('p', { class: 'bridge-detail' });
    this.errorEl = h('p', { class: 'bridge-error', hidden: true });
    this.targetText = h('p', { class: 'bridge-target' });
    this.targetSelect = h('select', { class: 'select-input bridge-target-select' });
    this.installButton = h('button', { type: 'button', class: 'btn-primary btn-small bridge-install' });
    this.uninstallButton = h('button', { type: 'button', class: 'btn-secondary btn-small bridge-uninstall' });
    this.confirmText = h('p', { class: 'confirm-text' });
    this.confirmButton = h('button', { type: 'button', class: 'btn-primary btn-small bridge-confirm' });
    this.confirmCancel = h('button', { type: 'button', class: 'btn-secondary btn-small' });
    this.confirmBox = h('div', { class: 'confirm-box', role: 'alertdialog', hidden: true }, [
      this.confirmText,
      h('div', { class: 'inline-form-row' }, [this.confirmButton, this.confirmCancel]),
    ]);
    this.el = h('div', { class: 'card bridge-card' }, [
      this.titleEl,
      this.descEl,
      this.statusEl,
      this.detailEl,
      this.errorEl,
      this.targetText,
      this.targetSelect,
      h('div', { class: 'inline-form-row' }, [this.installButton, this.uninstallButton]),
      this.confirmBox,
    ]);

    this.installButton.addEventListener('click', () => {
      this.confirmBox.hidden = false;
      this.confirmButton.focus();
    });
    this.confirmCancel.addEventListener('click', () => this.closeConfirm());
    onEscape(this.confirmBox, () => this.closeConfirm());
    this.confirmButton.addEventListener('click', () => this.install());
    this.uninstallButton.addEventListener('click', () => this.uninstall());
  }

  private closeConfirm(): void {
    this.confirmBox.hidden = true;
    this.installButton.focus();
  }

  private selectedTarget(): string | null {
    if (this.accounts.length === 1) return this.accounts[0]?.id ?? null;
    const value = this.targetSelect.value;
    return this.accounts.some((a) => a.id === value) ? value : null;
  }

  refresh(): void {
    void this.deps.api.invoke('claude-bridge:status', null).then((result) => {
      if (result.ok) {
        this.status = result.value;
        this.errorCode = null;
      } else {
        this.errorCode = ipcErrorCode(result.error);
      }
      this.render();
    });
  }

  private install(): void {
    const target = this.selectedTarget();
    if (target === null || this.busy) return;
    this.busy = true;
    this.confirmBox.hidden = true;
    this.render();
    void this.deps.api.invoke('claude-bridge:install-default', { accountId: target }).then((result) => {
      this.busy = false;
      if (result.ok) {
        this.status = result.value;
        this.errorCode = null;
      } else {
        this.errorCode = ipcErrorCode(result.error);
      }
      this.render();
    });
  }

  private uninstall(): void {
    if (this.busy) return;
    this.busy = true;
    this.render();
    void this.deps.api.invoke('claude-bridge:uninstall-default', null).then((result) => {
      this.busy = false;
      if (result.ok) {
        this.status = result.value;
        this.errorCode = null;
      } else {
        this.errorCode = ipcErrorCode(result.error);
      }
      this.render();
    });
  }

  update(accounts: AccountDTO[], ctx: RenderContext): void {
    this.accounts = accounts;
    this.ctx = ctx;
    this.render();
  }

  private render(): void {
    const ctx = this.ctx;
    if (ctx === null) return;
    const { t } = ctx;
    setText(this.titleEl, t('bridgeTitle'));
    setText(this.descEl, t('bridgeDesc'));
    const status = this.status;
    const code = this.errorCode ?? status?.errorCode ?? null;

    setText(this.statusEl, status === null ? '' : status.installed ? t('bridgeInstalled') : t('bridgeNotInstalled'));
    this.statusEl.hidden = status === null;
    const details: string[] = [];
    if (status !== null) {
      if (status.installed && status.wrapsExistingCommand) details.push(t('bridgeWrapsExisting'));
      if (status.lastDataAt !== null) {
        details.push(t('bridgeLastData', { time: relativeTimeText(ctx.locale, status.lastDataAt, ctx.now) }));
      }
      const target = this.accounts.find((a) => a.id === status.targetAccountId);
      if (status.installed && target !== undefined) details.push(t('bridgeTargetAccount', { label: target.label }));
    }
    setText(this.detailEl, details.join(' · '));
    this.detailEl.hidden = details.length === 0;
    setText(this.errorEl, code === null ? '' : describeError(t, code));
    this.errorEl.hidden = code === null;

    const installed = status?.installed === true;
    const single = this.accounts.length === 1 ? this.accounts[0] : undefined;
    setText(this.targetText, single !== undefined && !installed ? t('bridgeTargetAccount', { label: single.label }) : '');
    this.targetText.hidden = single === undefined || installed;

    const previous = this.targetSelect.value;
    const options = this.accounts.map((a) => h('option', { value: a.id }, [a.label]));
    this.targetSelect.replaceChildren(...options);
    if (this.accounts.some((a) => a.id === previous)) this.targetSelect.value = previous;
    this.targetSelect.hidden = this.accounts.length < 2 || installed;
    setAttr(this.targetSelect, 'aria-label', t('bridgeSelectTarget'));

    setText(this.installButton, t('bridgeInstallDefault'));
    setText(this.uninstallButton, t('bridgeUninstallDefault'));
    this.installButton.hidden = installed;
    this.installButton.disabled = this.busy || this.accounts.length === 0;
    this.uninstallButton.hidden = !installed;
    this.uninstallButton.disabled = this.busy;
    setText(this.confirmText, `${t('bridgeConfirmInstall')} ${t('bridgeInstallNote')}`);
    setText(this.confirmButton, t('bridgeInstallDefault'));
    setText(this.confirmCancel, t('cancel'));
  }
}

// ---------------------------------------------------------------------------

class ProviderSection {
  readonly el: HTMLElement;
  private readonly iconSlot: HTMLElement;
  private readonly nameEl: HTMLElement;
  private readonly cliEl: HTMLElement;
  readonly installGuideButton: HTMLButtonElement;
  private readonly rowsEl: HTMLElement;
  private readonly orphansEl: HTMLElement;
  readonly addButton: HTMLButtonElement;
  readonly addForm: HTMLFormElement;
  readonly addInput: HTMLInputElement;
  private readonly addLabel: HTMLLabelElement;
  private readonly addSave: HTMLButtonElement;
  private readonly addCancel: HTMLButtonElement;
  readonly bridge: BridgeSection | null;
  readonly rows = new Map<string, AccountRow>();
  private iconKey = '';
  private adding = false;

  constructor(
    readonly provider: ProviderId,
    private readonly tab: AccountsTab,
    deps: AccountsTabDeps,
  ) {
    const headingId = uniqueId(`provider-${provider}`);
    const inputId = uniqueId('add-label');
    this.iconSlot = h('span', { class: 'provider-icon' });
    this.nameEl = h('h3', { class: 'provider-name', id: headingId });
    this.cliEl = h('span', { class: 'provider-cli' });
    this.installGuideButton = h('button', { type: 'button', class: 'btn-link cli-install' });
    this.rowsEl = h('div', { class: 'provider-rows' });
    this.orphansEl = h('div', { class: 'provider-orphans' });
    this.addButton = h('button', { type: 'button', class: 'btn-secondary btn-add-account' });
    this.addLabel = h('label', { for: inputId, class: 'form-label' });
    this.addInput = h('input', { type: 'text', id: inputId, class: 'text-input', maxlength: LABEL_MAX_LENGTH });
    this.addSave = h('button', { type: 'submit', class: 'btn-primary btn-small' });
    this.addCancel = h('button', { type: 'button', class: 'btn-secondary btn-small' });
    this.addForm = h('form', { class: 'inline-form add-form', hidden: true }, [
      this.addLabel,
      h('div', { class: 'inline-form-row' }, [this.addInput, this.addSave, this.addCancel]),
    ]);
    this.bridge = provider === 'claude' ? new BridgeSection(deps) : null;

    this.el = h('section', { class: 'provider-section', 'data-provider': provider, 'aria-labelledby': headingId }, [
      h('div', { class: 'provider-header' }, [
        h('div', { class: 'provider-title' }, [this.iconSlot, this.nameEl]),
        h('div', { class: 'provider-cli-wrap' }, [this.cliEl, this.installGuideButton]),
      ]),
      this.rowsEl,
      this.orphansEl,
      this.addButton,
      this.addForm,
      this.bridge?.el ?? null,
    ]);

    this.installGuideButton.addEventListener('click', () => {
      void tab.api.invoke('shell:open-external', { kind: 'link', key: CLI_INSTALL_KEYS[provider] });
    });
    this.addButton.addEventListener('click', () => this.openAdd());
    this.addCancel.addEventListener('click', () => this.closeAdd(true));
    onEscape(this.addInput, () => this.closeAdd(true));
    this.addInput.addEventListener('input', () => setAttr(this.addInput, 'aria-invalid', null));
    this.addForm.addEventListener('submit', (event) => {
      event.preventDefault();
      this.submitAdd();
    });
  }

  private openAdd(): void {
    this.addForm.hidden = false;
    this.addInput.value = '';
    setAttr(this.addInput, 'aria-invalid', null);
    this.addInput.focus();
  }

  private closeAdd(restoreFocus: boolean): void {
    this.addForm.hidden = true;
    this.addInput.value = '';
    if (restoreFocus) this.addButton.focus();
  }

  private submitAdd(): void {
    const label = normalizeLabel(this.addInput.value);
    if (label === null) {
      setAttr(this.addInput, 'aria-invalid', 'true');
      this.addInput.focus();
      return;
    }
    if (this.adding) return;
    this.adding = true;
    this.addSave.disabled = true;
    void this.tab.api.invoke('accounts:add', { provider: this.provider, label }).then((result) => {
      this.adding = false;
      this.addSave.disabled = false;
      if (!result.ok) {
        this.tab.reportError(ipcErrorCode(result.error));
        return;
      }
      this.closeAdd(false);
      const panel = this.tab.panelFor(result.value.id, this.provider);
      this.orphansEl.append(panel.el);
      panel.start();
      panel.cancelButton.focus();
    });
  }

  update(state: AppStateSnapshot, ctx: RenderContext, globalOrder: readonly string[]): void {
    const { t, settings } = ctx;
    const mono = settings.iconStyle === 'monochrome';
    const iconKey = String(mono);
    if (iconKey !== this.iconKey) {
      this.iconKey = iconKey;
      this.iconSlot.replaceChildren(providerIcon(this.provider, 18, mono));
    }
    const providerName = t(PROVIDER_NAME_KEYS[this.provider]);
    setText(this.nameEl, providerName);
    const cli = state.cli[this.provider];
    setText(this.cliEl, cliStatusText(t, cli));
    this.cliEl.dataset.state = cli.state;
    setText(this.installGuideButton, t('cliInstallGuide'));
    this.installGuideButton.hidden = cli.state !== 'missing';
    setText(this.addButton, `+ ${t('addAccountFor', { provider: providerName })}`);
    setText(this.addLabel, t('accountLabelLabel'));
    setAttr(this.addInput, 'placeholder', t('accountLabelPlaceholder'));
    setText(this.addSave, t('save'));
    setText(this.addCancel, t('cancel'));

    const accounts = sortedAccounts(state.accounts).filter((a) => a.provider === this.provider);
    const seen = new Set<string>();
    const rowEls = accounts.map((dto) => {
      seen.add(dto.id);
      let row = this.rows.get(dto.id);
      if (row === undefined) {
        row = new AccountRow(dto, this.tab);
        this.rows.set(dto.id, row);
      }
      const panel = this.tab.existingPanel(dto.id);
      if (panel !== undefined && panel.el.parentElement !== row.panelSlot) row.panelSlot.append(panel.el);
      row.update(dto, ctx, {
        first: globalOrder[0] === dto.id,
        last: globalOrder[globalOrder.length - 1] === dto.id,
        cli,
        loginBusy: panel?.isBusy() ?? false,
      });
      return row.el;
    });
    for (const id of [...this.rows.keys()]) if (!seen.has(id)) this.rows.delete(id);
    syncChildren(this.rowsEl, rowEls);

    // Panels whose account is not (yet) in the snapshot stay under the section while visible.
    const orphans = this.tab
      .panelsFor(this.provider)
      .filter((panel) => !seen.has(panel.accountId) && panel.isVisible())
      .map((panel) => panel.el);
    syncChildren(this.orphansEl, orphans);

    this.bridge?.update(accounts, ctx);
  }

  rowFor(accountId: string): AccountRow | undefined {
    return this.rows.get(accountId);
  }
}

// ---------------------------------------------------------------------------

export class AccountsTab {
  readonly el: HTMLElement;
  readonly api: Api;
  private readonly hintEl: HTMLElement;
  readonly sections: Readonly<Record<ProviderId, ProviderSection>>;
  private readonly panels = new Map<string, LoginPanel>();
  private state: AppStateSnapshot | null = null;
  private ctx: RenderContext | null = null;

  constructor(private readonly deps: AccountsTabDeps) {
    this.api = deps.api;
    this.hintEl = h('p', { class: 'accounts-hint muted' });
    this.sections = {
      claude: new ProviderSection('claude', this, deps),
      codex: new ProviderSection('codex', this, deps),
      grok: new ProviderSection('grok', this, deps),
    };
    this.el = h('div', { class: 'accounts-tab' }, [this.hintEl, ...PROVIDER_IDS.map((id) => this.sections[id].el)]);
  }

  existingPanel(accountId: string): LoginPanel | undefined {
    return this.panels.get(accountId);
  }

  panelFor(accountId: string, provider: ProviderId): LoginPanel {
    let panel = this.panels.get(accountId);
    if (panel === undefined) {
      panel = new LoginPanel(accountId, provider, {
        api: this.api,
        translator: this.deps.translator,
        onChange: () => this.rerender(),
      });
      this.panels.set(accountId, panel);
    }
    return panel;
  }

  panelsFor(provider: ProviderId): LoginPanel[] {
    return [...this.panels.values()].filter((panel) => panel.provider === provider);
  }

  reportError(code: ErrorCode): void {
    this.deps.report(describeError(this.deps.translator(), code));
  }

  onShow(): void {
    this.sections.claude.bridge?.refresh();
  }

  startLogin(accountId: string, provider: ProviderId): void {
    const panel = this.panelFor(accountId, provider);
    this.rerender();
    panel.start();
  }

  onLoginEvent(message: LoginEventMessage): void {
    let panel = this.panels.get(message.accountId);
    if (panel === undefined) {
      const account = this.state?.accounts.find((a) => a.id === message.accountId);
      if (account === undefined) return;
      // A flow started elsewhere (e.g. tray): show it here too.
      panel = this.panelFor(account.id, account.provider);
      panel.adopt();
    }
    panel.handleEvent(message);
  }

  toggle(dto: AccountDTO, checkbox: HTMLInputElement): void {
    const enabled = checkbox.checked;
    void this.api.invoke('accounts:toggle', { accountId: dto.id, enabled }).then((result) => {
      if (!result.ok) {
        checkbox.checked = !enabled;
        this.reportError(ipcErrorCode(result.error));
      }
    });
  }

  reorder(accountId: string, direction: 'up' | 'down'): void {
    void this.api.invoke('accounts:reorder', { accountId, direction }).then((result) => {
      if (!result.ok) this.reportError(ipcErrorCode(result.error));
    });
  }

  rename(accountId: string, label: string, row: AccountRow): void {
    void this.api.invoke('accounts:rename', { accountId, label }).then((result) => {
      if (result.ok) row.closeRename(true);
      else this.reportError(ipcErrorCode(result.error));
    });
  }

  remove(accountId: string): void {
    void this.api.invoke('accounts:remove', { accountId }).then((result) => {
      if (!result.ok) {
        this.reportError(ipcErrorCode(result.error));
        return;
      }
      const panel = this.panels.get(accountId);
      if (panel !== undefined && panel.isBusy()) panel.cancel();
      this.panels.delete(accountId);
    });
  }

  update(state: AppStateSnapshot, ctx: RenderContext): void {
    this.state = state;
    this.ctx = ctx;
    this.rerender();
  }

  private rerender(): void {
    const state = this.state;
    const ctx = this.ctx;
    if (state === null || ctx === null) return;
    setText(this.hintEl, ctx.t('checkedAccountsHint'));
    const globalOrder = sortedAccounts(state.accounts).map((a) => a.id);
    for (const [id, panel] of [...this.panels]) {
      if (!state.accounts.some((a) => a.id === id) && !panel.isVisible()) this.panels.delete(id);
      panel.render();
    }
    preservingFocus(this.el.ownerDocument, () => {
      for (const provider of PROVIDER_IDS) this.sections[provider].update(state, ctx, globalOrder);
    });
  }
}

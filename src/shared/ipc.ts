import { parseSettingsPatch, type Settings } from './settings';
import {
  POPUP_TABS,
  VIEW_IDS,
  isProviderId,
  type AccountDTO,
  type AppStateSnapshot,
  type ClaudeBridgeStatus,
  type ErrorCode,
  type LoginEventMessage,
  type PopupTab,
  type ProviderId,
  type ThemeTokens,
  type ViewId,
} from './types';
import {
  fail,
  isFiniteNumber,
  isId,
  isOneOf,
  normalizeLabel,
  ok,
  parseNull,
  parseRecord,
  type ParseResult,
} from './validate';

/** Name of the object exposed by the preload script on `window`. */
export const PRELOAD_GLOBAL = 'aiUsage';

// ---------------------------------------------------------------------------
// Channel names

export const INVOKE = {
  appGetState: 'app:get-state',
  appRendererReady: 'app:renderer-ready',
  settingsGet: 'settings:get',
  settingsUpdate: 'settings:update',
  accountsList: 'accounts:list',
  accountsAdd: 'accounts:add',
  accountsRemove: 'accounts:remove',
  accountsRename: 'accounts:rename',
  accountsToggle: 'accounts:toggle',
  accountsReorder: 'accounts:reorder',
  loginStart: 'login:start',
  loginCancel: 'login:cancel',
  loginSubmitPaste: 'login:submit-paste',
  usageRefreshNow: 'usage:refresh-now',
  shellOpenExternal: 'shell:open-external',
  windowTogglePopup: 'window:toggle-popup',
  windowShowPopup: 'window:show-popup',
  windowHidePopup: 'window:hide-popup',
  windowSetPopupLock: 'window:set-popup-lock',
  windowResizeWidget: 'window:resize-widget',
  claudeBridgeStatus: 'claude-bridge:status',
  claudeBridgeInstallDefault: 'claude-bridge:install-default',
  claudeBridgeUninstallDefault: 'claude-bridge:uninstall-default',
} as const;
export type InvokeChannel = (typeof INVOKE)[keyof typeof INVOKE];
export const INVOKE_CHANNELS: readonly InvokeChannel[] = Object.values(INVOKE);

export const EVENTS = {
  stateChanged: 'state:changed',
  themeChanged: 'theme:changed',
  loginEvent: 'login:event',
  popupShow: 'popup:show',
} as const;
export type EventChannel = (typeof EVENTS)[keyof typeof EVENTS];
export const EVENT_CHANNELS: readonly EventChannel[] = Object.values(EVENTS);

export function isInvokeChannel(value: unknown): value is InvokeChannel {
  return typeof value === 'string' && (INVOKE_CHANNELS as readonly string[]).includes(value);
}

export function isEventChannel(value: unknown): value is EventChannel {
  return typeof value === 'string' && (EVENT_CHANNELS as readonly string[]).includes(value);
}

// ---------------------------------------------------------------------------
// Request payloads

export interface RendererReadyRequest {
  view: ViewId;
  rendered: 'empty' | 'accounts';
  /** Renderer self-check that CSP blocks string evaluation (used by --smoke). */
  cspEnforced: boolean;
}
export interface SettingsUpdateRequest {
  patch: Partial<Settings>;
}
export interface AccountsAddRequest {
  provider: ProviderId;
  label: string;
}
export interface AccountRef {
  accountId: string;
}
export interface AccountsRenameRequest {
  accountId: string;
  label: string;
}
export interface AccountsToggleRequest {
  accountId: string;
  enabled: boolean;
}
export interface AccountsReorderRequest {
  accountId: string;
  direction: 'up' | 'down';
}
export interface LoginStartResponse {
  sessionId: string;
}
export interface LoginSessionRef {
  sessionId: string;
}
export const PASTE_MAX_LENGTH = 4096;
export interface LoginSubmitPasteRequest {
  sessionId: string;
  text: string;
}
export interface RefreshNowRequest {
  /** null refreshes every enabled account. */
  accountId: string | null;
}

export const EXTERNAL_LINK_KEYS = ['claude-cli-install', 'codex-cli-install', 'grok-cli-install'] as const;
export type ExternalLinkKey = (typeof EXTERNAL_LINK_KEYS)[number];
/** Windows ShellExecute limit is 2081 chars (RESEARCH §5). */
export const EXTERNAL_URL_MAX_LENGTH = 2048;

/**
 * `link`: fixed allowlisted URL chosen in main by key.
 * `login`: URL emitted by an active login session; main must verify the pair.
 */
export type OpenExternalRequest =
  | { kind: 'link'; key: ExternalLinkKey }
  | { kind: 'login'; sessionId: string; url: string };

export interface ShowPopupRequest {
  tab: PopupTab | null;
}
export interface SetPopupLockRequest {
  locked: boolean;
}
export interface ResizeWidgetRequest {
  width: number;
  height: number;
}

export const WIDGET_SIZE_LIMITS = { minWidth: 32, maxWidth: 1200, minHeight: 24, maxHeight: 120 } as const;

export function clampWidgetSize(request: ResizeWidgetRequest): ResizeWidgetRequest {
  const clamp = (value: number, min: number, max: number): number => Math.min(max, Math.max(min, Math.round(value)));
  return {
    width: clamp(request.width, WIDGET_SIZE_LIMITS.minWidth, WIDGET_SIZE_LIMITS.maxWidth),
    height: clamp(request.height, WIDGET_SIZE_LIMITS.minHeight, WIDGET_SIZE_LIMITS.maxHeight),
  };
}

// ---------------------------------------------------------------------------
// Contract maps

export interface InvokeContract {
  'app:get-state': { req: null; res: AppStateSnapshot };
  'app:renderer-ready': { req: RendererReadyRequest; res: null };
  'settings:get': { req: null; res: Settings };
  'settings:update': { req: SettingsUpdateRequest; res: Settings };
  'accounts:list': { req: null; res: AccountDTO[] };
  'accounts:add': { req: AccountsAddRequest; res: AccountDTO };
  'accounts:remove': { req: AccountRef; res: null };
  'accounts:rename': { req: AccountsRenameRequest; res: AccountDTO };
  'accounts:toggle': { req: AccountsToggleRequest; res: AccountDTO };
  'accounts:reorder': { req: AccountsReorderRequest; res: AccountDTO[] };
  'login:start': { req: AccountRef; res: LoginStartResponse };
  'login:cancel': { req: LoginSessionRef; res: null };
  'login:submit-paste': { req: LoginSubmitPasteRequest; res: null };
  'usage:refresh-now': { req: RefreshNowRequest; res: null };
  'shell:open-external': { req: OpenExternalRequest; res: null };
  'window:toggle-popup': { req: null; res: null };
  'window:show-popup': { req: ShowPopupRequest; res: null };
  'window:hide-popup': { req: null; res: null };
  'window:set-popup-lock': { req: SetPopupLockRequest; res: null };
  'window:resize-widget': { req: ResizeWidgetRequest; res: null };
  'claude-bridge:status': { req: null; res: ClaudeBridgeStatus };
  'claude-bridge:install-default': { req: AccountRef; res: ClaudeBridgeStatus };
  'claude-bridge:uninstall-default': { req: null; res: ClaudeBridgeStatus };
}

export type InvokeRequest<C extends InvokeChannel> = InvokeContract[C]['req'];
export type InvokeResponse<C extends InvokeChannel> = InvokeContract[C]['res'];

export interface EventContract {
  'state:changed': AppStateSnapshot;
  'theme:changed': ThemeTokens;
  'login:event': LoginEventMessage;
  /** Sent to the popup when main shows it; `tab` null keeps the current tab. */
  'popup:show': PopupShowEvent;
}

export interface PopupShowEvent {
  tab: PopupTab | null;
}

export const IPC_ERROR_CODES = [
  'invalid-request',
  'forbidden-sender',
  'not-found',
  'conflict',
  'busy',
  'not-implemented',
  'internal',
] as const;
export type IpcErrorCode = (typeof IPC_ERROR_CODES)[number];

export interface IpcError {
  code: IpcErrorCode;
  /** Domain failure code when the operation itself failed (renderer-safe). */
  detail?: ErrorCode;
}

/** Every invoke resolves to this envelope; exceptions never cross the bridge. */
export type IpcResult<T> = { ok: true; value: T } | { ok: false; error: IpcError };

export interface PreloadApi {
  invoke<C extends InvokeChannel>(channel: C, request: InvokeRequest<C>): Promise<IpcResult<InvokeResponse<C>>>;
  on<E extends EventChannel>(channel: E, listener: (payload: EventContract[E]) => void): () => void;
}

// ---------------------------------------------------------------------------
// Runtime validators for renderer -> main payloads

function parseAccountRef(input: unknown): ParseResult<AccountRef> {
  const rec = parseRecord(input, ['accountId']);
  if (!rec.ok) return rec;
  if (!isId(rec.value.accountId)) return fail('invalid accountId');
  return ok({ accountId: rec.value.accountId });
}

function parseSessionRef(input: unknown): ParseResult<LoginSessionRef> {
  const rec = parseRecord(input, ['sessionId']);
  if (!rec.ok) return rec;
  if (!isId(rec.value.sessionId)) return fail('invalid sessionId');
  return ok({ sessionId: rec.value.sessionId });
}

export function isAllowedExternalUrl(value: unknown): value is string {
  if (typeof value !== 'string' || value.length === 0 || value.length > EXTERNAL_URL_MAX_LENGTH) return false;
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    return false;
  }
  return url.protocol === 'https:' && url.username === '' && url.password === '' && url.hostname.length > 0;
}

type Validators = { readonly [C in InvokeChannel]: (input: unknown) => ParseResult<InvokeRequest<C>> };

export const INVOKE_VALIDATORS: Validators = {
  'app:get-state': parseNull,
  'app:renderer-ready': (input) => {
    const rec = parseRecord(input, ['view', 'rendered', 'cspEnforced']);
    if (!rec.ok) return rec;
    const { view, rendered, cspEnforced } = rec.value;
    if (!isOneOf(VIEW_IDS, view)) return fail('invalid view');
    if (rendered !== 'empty' && rendered !== 'accounts') return fail('invalid rendered');
    if (typeof cspEnforced !== 'boolean') return fail('invalid cspEnforced');
    return ok({ view, rendered, cspEnforced });
  },
  'settings:get': parseNull,
  'settings:update': (input) => {
    const rec = parseRecord(input, ['patch']);
    if (!rec.ok) return rec;
    const patch = parseSettingsPatch(rec.value.patch);
    return patch.ok ? ok({ patch: patch.value }) : patch;
  },
  'accounts:list': parseNull,
  'accounts:add': (input) => {
    const rec = parseRecord(input, ['provider', 'label']);
    if (!rec.ok) return rec;
    if (!isProviderId(rec.value.provider)) return fail('invalid provider');
    const label = normalizeLabel(rec.value.label);
    if (label === null) return fail('invalid label');
    return ok({ provider: rec.value.provider, label });
  },
  'accounts:remove': parseAccountRef,
  'accounts:rename': (input) => {
    const rec = parseRecord(input, ['accountId', 'label']);
    if (!rec.ok) return rec;
    if (!isId(rec.value.accountId)) return fail('invalid accountId');
    const label = normalizeLabel(rec.value.label);
    if (label === null) return fail('invalid label');
    return ok({ accountId: rec.value.accountId, label });
  },
  'accounts:toggle': (input) => {
    const rec = parseRecord(input, ['accountId', 'enabled']);
    if (!rec.ok) return rec;
    if (!isId(rec.value.accountId)) return fail('invalid accountId');
    if (typeof rec.value.enabled !== 'boolean') return fail('invalid enabled');
    return ok({ accountId: rec.value.accountId, enabled: rec.value.enabled });
  },
  'accounts:reorder': (input) => {
    const rec = parseRecord(input, ['accountId', 'direction']);
    if (!rec.ok) return rec;
    if (!isId(rec.value.accountId)) return fail('invalid accountId');
    const { direction } = rec.value;
    if (direction !== 'up' && direction !== 'down') return fail('invalid direction');
    return ok({ accountId: rec.value.accountId, direction });
  },
  'login:start': parseAccountRef,
  'login:cancel': parseSessionRef,
  'login:submit-paste': (input) => {
    const rec = parseRecord(input, ['sessionId', 'text']);
    if (!rec.ok) return rec;
    if (!isId(rec.value.sessionId)) return fail('invalid sessionId');
    const { text } = rec.value;
    if (typeof text !== 'string') return fail('invalid text');
    const trimmed = text.trim();
    if (trimmed.length === 0 || trimmed.length > PASTE_MAX_LENGTH || /[\r\n]/.test(trimmed)) {
      return fail('invalid text');
    }
    return ok({ sessionId: rec.value.sessionId, text: trimmed });
  },
  'usage:refresh-now': (input) => {
    if (input === null || input === undefined) return ok({ accountId: null });
    const rec = parseRecord(input, ['accountId']);
    if (!rec.ok) return rec;
    const { accountId } = rec.value;
    if (accountId === null || accountId === undefined) return ok({ accountId: null });
    if (!isId(accountId)) return fail('invalid accountId');
    return ok({ accountId });
  },
  'shell:open-external': (input) => {
    const rec = parseRecord(input, ['kind', 'key', 'sessionId', 'url']);
    if (!rec.ok) return rec;
    const { kind } = rec.value;
    if (kind === 'link') {
      if (rec.value.sessionId !== undefined || rec.value.url !== undefined) return fail('unexpected fields');
      if (!isOneOf(EXTERNAL_LINK_KEYS, rec.value.key)) return fail('invalid key');
      return ok({ kind, key: rec.value.key });
    }
    if (kind === 'login') {
      if (rec.value.key !== undefined) return fail('unexpected fields');
      if (!isId(rec.value.sessionId)) return fail('invalid sessionId');
      if (!isAllowedExternalUrl(rec.value.url)) return fail('invalid url');
      return ok({ kind, sessionId: rec.value.sessionId, url: rec.value.url });
    }
    return fail('invalid kind');
  },
  'window:toggle-popup': parseNull,
  'window:show-popup': (input) => {
    if (input === null || input === undefined) return ok({ tab: null });
    const rec = parseRecord(input, ['tab']);
    if (!rec.ok) return rec;
    const { tab } = rec.value;
    if (tab === null || tab === undefined) return ok({ tab: null });
    if (!isOneOf(POPUP_TABS, tab)) return fail('invalid tab');
    return ok({ tab });
  },
  'window:hide-popup': parseNull,
  'window:set-popup-lock': (input) => {
    const rec = parseRecord(input, ['locked']);
    if (!rec.ok) return rec;
    if (typeof rec.value.locked !== 'boolean') return fail('invalid locked');
    return ok({ locked: rec.value.locked });
  },
  'window:resize-widget': (input) => {
    const rec = parseRecord(input, ['width', 'height']);
    if (!rec.ok) return rec;
    const { width, height } = rec.value;
    if (!isFiniteNumber(width) || !isFiniteNumber(height) || width <= 0 || height <= 0) {
      return fail('invalid size');
    }
    return ok({ width, height });
  },
  'claude-bridge:status': parseNull,
  'claude-bridge:install-default': parseAccountRef,
  'claude-bridge:uninstall-default': parseNull,
};

export function validateInvokeRequest<C extends InvokeChannel>(
  channel: C,
  input: unknown,
): ParseResult<InvokeRequest<C>> {
  const validator = INVOKE_VALIDATORS[channel] as (value: unknown) => ParseResult<InvokeRequest<C>>;
  return validator(input);
}

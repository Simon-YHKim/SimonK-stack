import type { Material, Settings } from './settings';

export const PROVIDER_IDS = ['claude', 'codex', 'grok'] as const;
export type ProviderId = (typeof PROVIDER_IDS)[number];

export function isProviderId(value: unknown): value is ProviderId {
  return typeof value === 'string' && (PROVIDER_IDS as readonly string[]).includes(value);
}

export const LOCALES = ['ko', 'en'] as const;
export type Locale = (typeof LOCALES)[number];

export const VIEW_IDS = ['widget', 'popup'] as const;
export type ViewId = (typeof VIEW_IDS)[number];

export const POPUP_TABS = ['usage', 'accounts', 'settings'] as const;
export type PopupTab = (typeof POPUP_TABS)[number];

/**
 * Stable, renderer-safe failure codes. The renderer maps each code to an i18n
 * message; raw provider error text never reaches the UI.
 */
export const ERROR_CODES = [
  'cli-not-found',
  'cli-unsupported-version',
  /** The CLI exists but its launcher (e.g. an npm shim) cannot be resolved without a shell. */
  'cli-unsupported-install',
  'node-not-found',
  'spawn-failed',
  'timeout',
  'cancelled',
  'protocol-error',
  'parse-error',
  'not-logged-in',
  'login-expired',
  'login-failed',
  'device-auth-disabled',
  'rate-limited',
  'network',
  'provider-error',
  'bridge-not-installed',
  'bridge-no-data',
  'quota-unavailable',
  'not-implemented',
  'internal',
] as const;
export type ErrorCode = (typeof ERROR_CODES)[number];

export function isErrorCode(value: unknown): value is ErrorCode {
  return typeof value === 'string' && (ERROR_CODES as readonly string[]).includes(value);
}

// ---------------------------------------------------------------------------
// Accounts

export const LOGIN_STATES = ['logged-in', 'logged-out', 'logging-in', 'cli-missing', 'unknown'] as const;
export type LoginState = (typeof LOGIN_STATES)[number];

/** Main-process account record (persisted). */
export interface Account {
  id: string;
  provider: ProviderId;
  label: string;
  enabled: boolean;
  /** Ascending display order on the widget and popup. */
  order: number;
  /** Absolute per-account CLI home directory. Main process only: never send to a renderer. */
  profileDir: string;
  /** Epoch ms. */
  createdAt: number;
}

/** Renderer-safe account view. Contains no paths, tokens or raw e-mail addresses. */
export interface AccountDTO {
  id: string;
  provider: ProviderId;
  label: string;
  enabled: boolean;
  order: number;
  emailMasked?: string;
  plan?: string;
  loginState: LoginState;
}

export interface AccountIdentityInfo {
  loginState: LoginState;
  emailMasked?: string;
  plan?: string;
}

/** Explicit field pick so new main-only fields can never leak by spreading. */
export function toAccountDTO(account: Account, info: AccountIdentityInfo): AccountDTO {
  const dto: AccountDTO = {
    id: account.id,
    provider: account.provider,
    label: account.label,
    enabled: account.enabled,
    order: account.order,
    loginState: info.loginState,
  };
  if (info.emailMasked !== undefined) dto.emailMasked = info.emailMasked;
  if (info.plan !== undefined) dto.plan = info.plan;
  return dto;
}

// ---------------------------------------------------------------------------
// Usage

export const QUOTA_WINDOW_KINDS = ['session', 'weekly', 'other'] as const;
export type QuotaWindowKind = (typeof QUOTA_WINDOW_KINDS)[number];

export interface QuotaWindow {
  kind: QuotaWindowKind;
  /** 0..100, or null when unknown. Unknown is never rendered as 0%. */
  usedPercent: number | null;
  /** Epoch ms of the next reset, or null when unknown. */
  resetsAt: number | null;
  windowMinutes: number | null;
  /** Optional non-localized, non-PII qualifier from the provider (e.g. bucket id). */
  label?: string;
}

/**
 * - ok: `windows` were measured successfully at `measuredAt`.
 * - stale: last good measurement is older than the stale threshold.
 * - loading: first fetch in progress, nothing measured yet.
 * - error: last fetch failed (`errorCode`); `windows` may hold the last good values.
 * - unavailable: the provider/account cannot report limits (e.g. no data source).
 * - logged-out: the account's CLI profile is not signed in.
 * - reset: every known window has passed its `resetsAt`; values await a new fetch.
 */
export const USAGE_STATES = ['ok', 'stale', 'loading', 'error', 'unavailable', 'logged-out', 'reset'] as const;
export type UsageState = (typeof USAGE_STATES)[number];

export const USAGE_SOURCES = ['codex-app-server', 'claude-statusline', 'grok-acp'] as const;
export type UsageSource = (typeof USAGE_SOURCES)[number];

export interface UsageSnapshot {
  accountId: string;
  provider: ProviderId;
  state: UsageState;
  windows: QuotaWindow[];
  plan?: string;
  /** Epoch ms when `windows` were measured, null if never. */
  measuredAt: number | null;
  /** Epoch ms of the last successful fetch, null if never. */
  lastSuccessAt: number | null;
  errorCode?: ErrorCode;
  source: UsageSource;
}

// ---------------------------------------------------------------------------
// Login flow (emitted by provider adapters, relayed to the renderer by main)

export const LOGIN_STAGES = [
  'starting',
  'waiting-browser',
  'waiting-device-code',
  'waiting-paste',
  'verifying',
] as const;
export type LoginStage = (typeof LOGIN_STAGES)[number];

export type LoginEvent =
  | { type: 'url'; url: string }
  | { type: 'device-code'; userCode: string; verificationUrl: string; expiresAt?: number }
  | { type: 'needs-paste' }
  | { type: 'progress'; stage: LoginStage }
  | { type: 'success'; emailMasked?: string; plan?: string }
  | { type: 'error'; code: ErrorCode };

export interface LoginEventMessage {
  sessionId: string;
  accountId: string;
  /** Epoch ms. */
  at: number;
  event: LoginEvent;
}

// ---------------------------------------------------------------------------
// Theme

export type ColorScheme = 'light' | 'dark';

export interface ThemeTokens {
  /** App color scheme (nativeTheme.shouldUseDarkColors). */
  scheme: ColorScheme;
  /** Scheme of system-integrated UI such as the taskbar. */
  taskbarScheme: ColorScheme;
  highContrast: boolean;
  /** System accent color as `#rrggbb`. */
  accent: string;
  reducedTransparency: boolean;
  /** Material actually applied after policy (high contrast / reduced transparency force 'none'). */
  effectiveMaterial: Material;
}

// ---------------------------------------------------------------------------
// App state pushed to renderers

export type CliDetectState = 'unknown' | 'found' | 'missing';

export interface CliStatusDTO {
  state: CliDetectState;
  version?: string;
}

export interface RefreshStatus {
  inFlight: boolean;
  /** Accounts currently being fetched. */
  accountIds: string[];
  lastRunAt: number | null;
  nextRunAt: number | null;
}

export interface ClaudeBridgeStatus {
  /** Bridge present in the default Claude Code profile's settings.json. */
  installed: boolean;
  /** Installed bridge wraps a pre-existing statusLine command. */
  wrapsExistingCommand: boolean;
  /** Widget account that receives default-profile readings. */
  targetAccountId: string | null;
  /** Epoch ms of the newest bridge record, null if none. */
  lastDataAt: number | null;
  errorCode?: ErrorCode;
}

export interface AppStateSnapshot {
  locale: Locale;
  settings: Settings;
  accounts: AccountDTO[];
  usage: UsageSnapshot[];
  refresh: RefreshStatus;
  theme: ThemeTokens;
  cli: Record<ProviderId, CliStatusDTO>;
}

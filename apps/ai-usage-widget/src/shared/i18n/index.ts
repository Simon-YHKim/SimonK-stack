import type { Language, Material, RefreshIntervalSec, ThemeId } from '../settings';
import type { ErrorCode, Locale, LoginStage, LoginState, ProviderId, UsageSource, UsageState } from '../types';
import { en } from './en';
import { ko } from './ko';

export type MessageKey = keyof typeof ko;
export type Messages = Readonly<Record<MessageKey, string>>;
export type MessageParams = Readonly<Record<string, string | number>>;

export const DICTIONARIES: Readonly<Record<Locale, Messages>> = { ko, en };

/** `auto` follows the OS locale: any `ko*` tag is Korean, everything else English. */
export function resolveLocale(language: Language, systemLocale: string): Locale {
  if (language === 'ko' || language === 'en') return language;
  return systemLocale.trim().toLowerCase().startsWith('ko') ? 'ko' : 'en';
}

const PLACEHOLDER_RE = /\{([A-Za-z0-9_]+)\}/g;

export function t(locale: Locale, key: MessageKey, params?: MessageParams): string {
  const template = DICTIONARIES[locale][key];
  if (params === undefined) return template;
  return template.replace(PLACEHOLDER_RE, (match, name: string) => {
    const value = params[name];
    return value === undefined ? match : String(value);
  });
}

export type Translator = (key: MessageKey, params?: MessageParams) => string;

export function createTranslator(locale: Locale): Translator {
  return (key, params) => t(locale, key, params);
}

export function placeholdersOf(template: string): string[] {
  return [...template.matchAll(PLACEHOLDER_RE)].map((m) => m[1] ?? '').sort();
}

// Typed lookup tables: adding a union member without a message fails typecheck.

export const ERROR_MESSAGE_KEYS: Readonly<Record<ErrorCode, MessageKey>> = {
  'cli-not-found': 'error_cliNotFound',
  'cli-unsupported-version': 'error_cliUnsupportedVersion',
  'cli-unsupported-install': 'error_cliUnsupportedInstall',
  'node-not-found': 'error_nodeNotFound',
  'spawn-failed': 'error_spawnFailed',
  timeout: 'error_timeout',
  cancelled: 'error_cancelled',
  'protocol-error': 'error_protocolError',
  'parse-error': 'error_parseError',
  'not-logged-in': 'error_notLoggedIn',
  'login-expired': 'error_loginExpired',
  'login-failed': 'error_loginFailed',
  'device-auth-disabled': 'error_deviceAuthDisabled',
  'rate-limited': 'error_rateLimited',
  network: 'error_network',
  'provider-error': 'error_providerError',
  'bridge-not-installed': 'error_bridgeNotInstalled',
  'bridge-no-data': 'error_bridgeNoData',
  'quota-unavailable': 'error_quotaUnavailable',
  'not-implemented': 'error_notImplemented',
  internal: 'error_internal',
};

export const USAGE_STATE_KEYS: Readonly<Record<UsageState, MessageKey>> = {
  ok: 'state_ok',
  stale: 'state_stale',
  loading: 'state_loading',
  error: 'state_error',
  unavailable: 'state_unavailable',
  'logged-out': 'state_loggedOut',
  reset: 'state_reset',
};

export const LOGIN_STATE_KEYS: Readonly<Record<LoginState, MessageKey>> = {
  'logged-in': 'loginState_loggedIn',
  'logged-out': 'loginState_loggedOut',
  'logging-in': 'loginState_loggingIn',
  'cli-missing': 'loginState_cliMissing',
  unknown: 'loginState_unknown',
};

export const LOGIN_STAGE_KEYS: Readonly<Record<LoginStage, MessageKey>> = {
  starting: 'loginStage_starting',
  'waiting-browser': 'loginStage_waitingBrowser',
  'waiting-device-code': 'loginStage_waitingDeviceCode',
  'waiting-paste': 'loginStage_waitingPaste',
  verifying: 'loginStage_verifying',
};

export const PROVIDER_NAME_KEYS: Readonly<Record<ProviderId, MessageKey>> = {
  claude: 'provider_claude',
  codex: 'provider_codex',
  grok: 'provider_grok',
  antigravity: 'provider_antigravity',
};

export const USAGE_SOURCE_KEYS: Readonly<Record<UsageSource, MessageKey>> = {
  'codex-app-server': 'source_codexAppServer',
  'claude-statusline': 'source_claudeStatusline',
  'grok-acp': 'source_grokAcp',
  'antigravity-cli-usage': 'source_antigravityCliUsage',
};

export const THEME_KEYS: Readonly<Record<ThemeId, MessageKey>> = {
  windows: 'themeWindows',
  '1a': 'theme1a',
  '1b': 'theme1b',
  '1c': 'theme1c',
  '1d': 'theme1d',
};

export const MATERIAL_KEYS: Readonly<Record<Material, MessageKey>> = {
  none: 'materialNone',
  mica: 'materialMica',
  acrylic: 'materialAcrylic',
};

export const LANGUAGE_KEYS: Readonly<Record<Language, MessageKey>> = {
  auto: 'languageAuto',
  ko: 'languageKo',
  en: 'languageEn',
};

export const REFRESH_INTERVAL_KEYS: Readonly<Record<RefreshIntervalSec, MessageKey>> = {
  15: 'interval15',
  30: 'interval30',
  60: 'interval60',
  120: 'interval120',
  300: 'interval300',
};

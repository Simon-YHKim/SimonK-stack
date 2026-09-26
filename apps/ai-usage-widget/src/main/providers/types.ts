import type {
  Account,
  ClaudeBridgeStatus,
  ErrorCode,
  LoginEvent,
  ProviderId,
  UsageSnapshot,
} from '../../shared/types';
import type { Logger } from '../log';

export interface CliInfo {
  found: boolean;
  /** Resolved executable or shim path (main-only, never sent to renderer). */
  path?: string;
  version?: string;
  errorCode?: ErrorCode;
}

export interface ProviderIdentity {
  loggedIn: boolean;
  /** Already masked with `maskEmail`; raw addresses never leave the adapter. */
  emailMasked?: string;
  plan?: string;
}

/**
 * Contract every provider module implements.
 *
 * - Credentials stay inside the official CLI and the account's profile dir;
 *   adapters never read token files or call provider HTTP APIs with user tokens.
 * - All child processes go through `src/main/cli/spawn.ts`.
 * - Expected failures are data, not exceptions: `fetchUsage` resolves with a
 *   snapshot whose `state`/`errorCode` describe the problem and whose windows
 *   contain only measured values (unknown = null, never 0).
 * - Every method honours `signal` and kills its child processes on abort.
 */
export interface ProviderAdapter {
  readonly id: ProviderId;
  /**
   * Hosts (and their subdomains) whose login URLs `shell:open-external` may open
   * for this provider. Empty means no login URL is ever opened.
   */
  readonly loginUrlHosts: readonly string[];
  detectCli(signal?: AbortSignal): Promise<CliInfo>;
  /** Creates `account.profileDir` (and provider-specific scaffolding) if missing. Idempotent. */
  ensureProfileDir(account: Account): Promise<void>;
  /**
   * Runs the provider's official login in the account's isolated profile.
   * Emits LoginEvents; resolves after `success` or `error` was emitted.
   * Rejects only on programmer errors.
   */
  startLogin(account: Account, emit: (event: LoginEvent) => void, signal: AbortSignal): Promise<void>;
  /** Forwards a pasted code to the running login (providers with paste flows only). */
  submitPaste?(account: Account, text: string): Promise<void>;
  /**
   * `loggedIn:false` only for a confirmed signed-out profile. When the state
   * cannot be determined (timeout, missing CLI, network) reject with
   * `ProviderError(code)`; the shell shows loginState 'unknown', not 'logged-out'.
   */
  getIdentity(account: Account, signal: AbortSignal): Promise<ProviderIdentity>;
  fetchUsage(account: Account, signal: AbortSignal): Promise<UsageSnapshot>;
  /** Optional official banked reset flow; confirmation happens before the consuming RPC. */
  redeemResetCredit?(account: Account, confirm: (offer: { availableCount: number; expiresAt: number | null }) => Promise<boolean>, signal: AbortSignal): Promise<'reset' | 'cancelled' | 'unavailable' | 'nothingToReset' | 'noCredit' | 'alreadyRedeemed'>;
  /** Deletes the widget-owned profile dir of this account. Must refuse paths outside the profiles root. */
  removeProfile(account: Account): Promise<void>;
}

/** Claude statusline bridge management for the default Claude Code profile. */
export interface ClaudeBridgeController {
  status(): Promise<ClaudeBridgeStatus>;
  /** Backs up settings.json, wraps any existing statusLine command, routes readings to `target`. */
  installDefault(target: Account): Promise<ClaudeBridgeStatus>;
  /** Restores the previous statusLine command. */
  uninstallDefault(): Promise<ClaudeBridgeStatus>;
}

export interface ClaudeProviderAdapter extends ProviderAdapter {
  readonly id: 'claude';
  readonly bridge: ClaudeBridgeController;
}

export interface ProviderDeps {
  logger: Logger;
  now: () => number;
  appVersion: string;
  /** `%LOCALAPPDATA%\AIUsageWidget` (or a temp dir in smoke/tests). */
  localDataRoot: string;
  /** `<localDataRoot>\profiles`. */
  profilesRoot: string;
  /** `<localDataRoot>\bridge`. */
  bridgeRoot: string;
  /** Folder with packaged `resources/` (claude-bridge scripts live under it). */
  resourcesDir: string;
  /** User home (`os.homedir()`); tests inject a temp dir. */
  homeDir: string;
  /** Parent environment for `buildChildEnv`. */
  env: NodeJS.ProcessEnv;
}

export type ProviderFactory<A extends ProviderAdapter = ProviderAdapter> = (deps: ProviderDeps) => A;

export class ProviderError extends Error {
  readonly code: ErrorCode;
  constructor(code: ErrorCode, message?: string, options?: { cause?: unknown }) {
    super(message ?? code, options);
    this.name = 'ProviderError';
    this.code = code;
  }
}

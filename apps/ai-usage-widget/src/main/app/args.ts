export interface LaunchArgs {
  /** Boot, wait for both renderers, write a JSON report, exit. */
  smoke: boolean;
  smokeOut: string | null;
  smokeTimeoutMs: number;
  /** Quiet start: show only the widget, never open the popup (V1-14). */
  hidden: boolean;
  /** Started by the login item registration (`--autostart`). Implies `hidden`. */
  autostart: boolean;
}

export const DEFAULT_SMOKE_TIMEOUT_MS = 30_000;

export function parseLaunchArgs(argv: readonly string[]): LaunchArgs {
  const result: LaunchArgs = {
    smoke: false,
    smokeOut: null,
    smokeTimeoutMs: DEFAULT_SMOKE_TIMEOUT_MS,
    hidden: false,
    autostart: false,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === undefined) continue;
    if (arg === '--smoke') {
      result.smoke = true;
    } else if (arg.startsWith('--smoke-out=')) {
      const value = arg.slice('--smoke-out='.length);
      result.smokeOut = value.length > 0 ? value : null;
    } else if (arg === '--smoke-out') {
      const next = argv[i + 1];
      if (next !== undefined && !next.startsWith('--')) {
        result.smokeOut = next;
        i += 1;
      }
    } else if (arg.startsWith('--smoke-timeout-ms=')) {
      const value = Number(arg.slice('--smoke-timeout-ms='.length));
      if (Number.isInteger(value) && value >= 1000 && value <= 120_000) result.smokeTimeoutMs = value;
    } else if (arg === '--autostart') {
      result.autostart = true;
      result.hidden = true;
    } else if (arg === '--hidden') {
      result.hidden = true;
    }
  }
  return result;
}

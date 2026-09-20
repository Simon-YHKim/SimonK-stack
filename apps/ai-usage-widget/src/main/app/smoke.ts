import type { RendererReadyRequest } from '../../shared/ipc';
import { VIEW_IDS, type ViewId } from '../../shared/types';

export interface SmokeViewResult {
  ready: boolean;
  readyAfterMs: number | null;
  rendered: RendererReadyRequest['rendered'] | null;
  cspEnforced: boolean | null;
}

export interface SmokeMeta {
  versions: Readonly<Record<string, string>>;
  packaged: boolean;
  userDataIsolated: boolean;
}

export interface SmokeCheck {
  /** null = informational only. */
  ok: boolean | null;
  value: unknown;
}

export interface SmokeReport extends SmokeMeta {
  ok: boolean;
  views: Record<ViewId, SmokeViewResult>;
  providers: string[];
  checks: Record<string, SmokeCheck>;
  durationMs: number;
  errors: string[];
}

export class SmokeTracker {
  private readonly views: Record<ViewId, SmokeViewResult>;
  private readonly errors: string[] = [];
  private readonly checks: Record<string, SmokeCheck> = {};
  private waiters: (() => void)[] = [];

  constructor(
    private readonly startedAt: number,
    private readonly meta: SmokeMeta,
  ) {
    const empty = (): SmokeViewResult => ({ ready: false, readyAfterMs: null, rendered: null, cspEnforced: null });
    this.views = { widget: empty(), popup: empty() };
  }

  markReady(request: RendererReadyRequest, at: number): void {
    const view = this.views[request.view];
    if (!view.ready) {
      view.ready = true;
      view.readyAfterMs = at - this.startedAt;
    }
    view.rendered = request.rendered;
    view.cspEnforced = request.cspEnforced;
    if (this.allReady()) {
      const waiters = this.waiters;
      this.waiters = [];
      for (const wake of waiters) wake();
    }
  }

  addError(message: string): void {
    if (this.errors.length < 50) this.errors.push(message);
  }

  /** Records a named check; `ok: false` fails the report. Values must not contain secrets or paths. */
  setCheck(name: string, value: unknown, ok: boolean | null = null): void {
    this.checks[name] = { ok, value };
  }

  allReady(): boolean {
    return VIEW_IDS.every((id) => this.views[id].ready);
  }

  /** Resolves true when every view reported ready, false on timeout. */
  waitForAll(timeoutMs: number): Promise<boolean> {
    if (this.allReady()) return Promise.resolve(true);
    return new Promise<boolean>((resolve) => {
      const timer = setTimeout(() => {
        this.addError(`timeout after ${timeoutMs}ms waiting for renderers`);
        resolve(false);
      }, timeoutMs);
      this.waiters.push(() => {
        clearTimeout(timer);
        resolve(true);
      });
    });
  }

  report(at: number, providers: readonly string[]): SmokeReport {
    const views = { widget: { ...this.views.widget }, popup: { ...this.views.popup } };
    const failedChecks = Object.entries(this.checks)
      .filter(([, check]) => check.ok === false)
      .map(([name]) => `check failed: ${name}`);
    const errors = [...this.errors, ...failedChecks];
    const ok = errors.length === 0 && VIEW_IDS.every((id) => views[id].ready && views[id].cspEnforced === true);
    return {
      ok,
      ...this.meta,
      views,
      providers: [...providers],
      checks: { ...this.checks },
      durationMs: at - this.startedAt,
      errors,
    };
  }
}

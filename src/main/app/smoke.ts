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

export interface SmokeReport extends SmokeMeta {
  ok: boolean;
  views: Record<ViewId, SmokeViewResult>;
  providers: string[];
  durationMs: number;
  errors: string[];
}

export class SmokeTracker {
  private readonly views: Record<ViewId, SmokeViewResult>;
  private readonly errors: string[] = [];
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
    const ok = this.errors.length === 0 && VIEW_IDS.every((id) => views[id].ready && views[id].cspEnforced === true);
    return {
      ok,
      ...this.meta,
      views,
      providers: [...providers],
      durationMs: at - this.startedAt,
      errors: [...this.errors],
    };
  }
}

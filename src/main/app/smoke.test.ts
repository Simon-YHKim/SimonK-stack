import { describe, expect, it } from 'vitest';
import { SmokeTracker } from './smoke';

const META = { versions: { electron: '44.3.0' }, packaged: false, userDataIsolated: true };

describe('SmokeTracker', () => {
  it('is ok only when both views are ready with CSP enforced', async () => {
    const tracker = new SmokeTracker(1000, META);
    const waiting = tracker.waitForAll(5000);
    tracker.markReady({ view: 'widget', rendered: 'empty', cspEnforced: true }, 1200);
    expect(tracker.allReady()).toBe(false);
    tracker.markReady({ view: 'popup', rendered: 'empty', cspEnforced: true }, 1300);
    await expect(waiting).resolves.toBe(true);
    const report = tracker.report(1400, ['claude', 'codex', 'grok']);
    expect(report).toMatchObject({ ok: true, durationMs: 400, providers: ['claude', 'codex', 'grok'] });
    expect(report.views.widget.readyAfterMs).toBe(200);
  });

  it('fails without CSP, on errors, or on timeout', async () => {
    const noCsp = new SmokeTracker(0, META);
    noCsp.markReady({ view: 'widget', rendered: 'empty', cspEnforced: false }, 1);
    noCsp.markReady({ view: 'popup', rendered: 'empty', cspEnforced: true }, 1);
    expect(noCsp.report(2, []).ok).toBe(false);

    const withError = new SmokeTracker(0, META);
    withError.markReady({ view: 'widget', rendered: 'empty', cspEnforced: true }, 1);
    withError.markReady({ view: 'popup', rendered: 'empty', cspEnforced: true }, 1);
    withError.addError('popup: did-fail-load -3');
    expect(withError.report(2, []).ok).toBe(false);

    const timeout = new SmokeTracker(0, META);
    await expect(timeout.waitForAll(20)).resolves.toBe(false);
    expect(timeout.report(30, []).errors[0]).toContain('timeout');
  });

  it('includes named checks; only explicit failures fail the report', () => {
    const tracker = new SmokeTracker(0, META);
    tracker.markReady({ view: 'widget', rendered: 'empty', cspEnforced: true }, 1);
    tracker.markReady({ view: 'popup', rendered: 'empty', cspEnforced: true }, 1);
    tracker.setCheck('koffi', { loaded: false }, null);
    tracker.setCheck('ipc', { missing: [] }, true);
    const passing = tracker.report(2, []);
    expect(passing.ok).toBe(true);
    expect(passing.checks.koffi).toEqual({ ok: null, value: { loaded: false } });

    tracker.setCheck('cspHeader', { matchesProductionPolicy: false }, false);
    const failing = tracker.report(3, []);
    expect(failing.ok).toBe(false);
    expect(failing.errors).toContain('check failed: cspHeader');
  });
});

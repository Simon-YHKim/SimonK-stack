/**
 * Consent gate pattern. The host app must pass its real consent-manager reader;
 * this template does not invent a consent state or initialize an SDK itself.
 *
 * Example after the app has a consent manager:
 *   const gated = createConsentGatedTracker(readAnalyticsConsent, getTracker);
 *   // On a consent change, call gated.onConsentGranted() or
 *   // gated.onConsentRevoked() only after the consent store has updated.
 *
 * A missing, invalid, or throwing reader is treated as denied. Before consent
 * is granted, the tracker provider is never called.
 */

type ConsentState = "granted" | "denied" | "unknown";
type Tracker = {
  track: (event: string, props?: Record<string, unknown>) => void;
};
type TrackedEvent = { event: string; props?: Record<string, unknown> };

/**
 * The host app must supply its current consent state and lazy tracker provider.
 * Queue only when explicitly requested; dropping before consent is the default.
 */
export function createConsentGatedTracker(
  readConsent: () => ConsentState,
  getTracker: () => Tracker,
  options: { queueBeforeConsent?: boolean } = {},
) {
  const queueBeforeConsent = options.queueBeforeConsent === true;
  const pending: TrackedEvent[] = [];

  function currentConsent(): ConsentState {
    try {
      const state = readConsent();
      return state === "granted" || state === "unknown" ? state : "denied";
    } catch {
      return "denied";
    }
  }

  function emit(event: string, props?: Record<string, unknown>): void {
    try {
      getTracker().track(event, props);
    } catch {
      // Analytics is optional: a failed SDK must not break the app.
    }
  }

  function trackGated(event: string, props?: Record<string, unknown>): void {
    const consent = currentConsent();
    if (consent !== "granted") {
      if (consent === "denied") pending.length = 0;
      if (queueBeforeConsent && consent === "unknown") {
        // Bound optional in-memory queue growth while consent remains unknown.
        if (pending.length >= 100) pending.shift();
        pending.push({ event, props });
      }
      return;
    }
    emit(event, props);
  }

  function onConsentGranted(): void {
    if (!queueBeforeConsent) {
      pending.length = 0;
      return;
    }
    while (pending.length) {
      const consent = currentConsent();
      if (consent !== "granted") {
        if (consent === "denied") pending.length = 0;
        return;
      }
      const item = pending.shift();
      if (!item) return;
      emit(item.event, item.props);
    }
  }

  function onConsentRevoked(): void {
    pending.length = 0;
    // The host must also call its SDK opt-out/reset where the SDK supports it.
  }

  return { trackGated, onConsentGranted, onConsentRevoked };
}

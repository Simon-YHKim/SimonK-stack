import assert from "node:assert/strict";
import { test } from "node:test";

const { createConsentGatedTracker } = await import(
  new URL("../templates/consent-gated-wrapper.ts", import.meta.url)
);

function harness(initialConsent = "unknown", queueBeforeConsent = false) {
  let consent = initialConsent;
  const events = [];
  let trackerReads = 0;
  const gated = createConsentGatedTracker(
    () => consent,
    () => {
      trackerReads += 1;
      return { track: (event, props) => events.push({ event, props }) };
    },
    { queueBeforeConsent },
  );
  return {
    gated,
    events,
    get trackerReads() { return trackerReads; },
    setConsent(value) { consent = value; },
  };
}

test("unknown and denied consent never initialize or emit by default", () => {
  const h = harness();
  h.gated.trackGated("open");
  h.setConsent("denied");
  h.gated.trackGated("close");
  assert.deepEqual(h.events, []);
  assert.equal(h.trackerReads, 0);
});

test("granted consent emits through the injected tracker", () => {
  const h = harness("granted");
  h.gated.trackGated("open", { page: "home" });
  assert.deepEqual(h.events, [{ event: "open", props: { page: "home" } }]);
  assert.equal(h.trackerReads, 1);
});

test("stale grant callback cannot flush after consent is revoked", () => {
  const h = harness("unknown", true);
  h.gated.trackGated("queued");
  h.setConsent("denied");
  h.gated.onConsentGranted();
  assert.deepEqual(h.events, []);
  assert.equal(h.trackerReads, 0);
});

test("explicit queue flushes only after fresh granted state", () => {
  const h = harness("unknown", true);
  h.gated.trackGated("queued");
  h.gated.onConsentGranted();
  assert.deepEqual(h.events, []);
  h.setConsent("granted");
  h.gated.onConsentGranted();
  assert.deepEqual(h.events, [{ event: "queued", props: undefined }]);
});

test("revocation discards queued events", () => {
  const h = harness("unknown", true);
  h.gated.trackGated("queued");
  h.gated.onConsentRevoked();
  h.setConsent("granted");
  h.gated.onConsentGranted();
  assert.deepEqual(h.events, []);
});

test("missing or throwing consent reader fails closed", () => {
  const events = [];
  for (const readConsent of [undefined, () => { throw new Error("store unavailable"); }]) {
    const gated = createConsentGatedTracker(readConsent, () => ({
      track: (event) => events.push(event),
    }));
    gated.trackGated("blocked");
    gated.onConsentGranted();
  }
  assert.deepEqual(events, []);
});

test("tracker failure does not interrupt the app", () => {
  const gated = createConsentGatedTracker(
    () => "granted",
    () => { throw new Error("SDK unavailable"); },
  );
  assert.doesNotThrow(() => gated.trackGated("safe"));
});

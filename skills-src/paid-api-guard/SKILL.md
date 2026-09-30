---
name: paid-api-guard
description: >
  Use when integrating or auditing metered third-party APIs (payments, SMS, email, maps): "Stripe 연동", "Twilio SMS 비용 폭탄", "웹훅 서명", "API 키 유출", "prevent API cost explosion", or /paid-api-guard. Produces a scoped six-area risk review and test plan, separating read-only diagnosis from actions that send messages, charge money, rotate credentials, or change billing.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.1
author: simon
---

# Paid API Guard

Review or implement controls for APIs whose misuse can send messages, move money, or incur metered charges. A checklist is evidence, not proof of containment or a substitute for the provider's current contract.

## Scope and authority

1. Inspect the existing app, provider and SDK versions, test/live mode, credential storage, authorization path, request volume, retries, and billing/usage controls. Read only the presence and location of credentials; never print or copy their values into prompts, logs, reports, or code.
2. Classify the request as **audit**, **implementation**, or **incident response**. An audit is read-only. A suspected leak is urgent but not confirmed containment; inspect available logs and propose rotation/revocation without performing credential or billing changes unless separately authorized.
3. Before any test, enumerate external effects and price. Prefer mocks, fixtures, local failure injection, and provider sandboxes whose nonbilling status is confirmed. If the user requires extra cost `$0`, do not send live SMS/email, create live charges, make metered calls, or turn on overage/auto-top-up. A subscription login or usage alert alone does not prove a hard billing cap.
4. Preserve the app's stack and existing security controls. Choose only relevant controls from the six areas below; record evidence, changes, commands/tests actually run, unverified claims, and rollback needs. Live payment, bulk message, production credential, customer data, or billing changes require explicit authorization.

## Six review areas

| Area | Inspect and decide |
|---|---|
| 1. Key and network boundary | Keep secret/restricted provider credentials server-side in a vault or environment variables. A provider's **publishable** key may belong in a client SDK; do not flag it as a secret. Limit provider key permissions and egress where the platform and risk justify it. A BFF, single subnet, WAF, or country block is not universally mandatory. |
| 2. Request and event integrity | Authenticate/authorize the caller; use CSRF protection where applicable. Apply the provider's signature and retry/idempotency contract to the specific operation. Verify Stripe webhooks against the unmodified raw body. A browser cannot keep a shared HMAC secret, so do not prescribe browser→BFF HMAC as a general defense. |
| 3. Abuse and spend control | Check per-principal and aggregate rate limits, destination rules, quotas, concurrency, retry storms, and a server-side circuit breaker when a hard budget is required. Set alerts for detection, but distinguish delayed usage notifications from a pre-charge hard stop. |
| 4. Payment-specific integrity | Calculate amount, currency, discounts, tax, and order ownership from trusted server data. Use the provider's client-side tokenization/payment SDK for card entry; do not store raw card data. Reconcile provider and order state, and gate refunds or captures according to the application's approval policy. |
| 5. Leak and incident response | Check exposure scope, provider request history, active keys, and containment evidence. Alert the owner promptly; propose least-privilege replacement, rotation/revocation, and downstream updates. Do not claim a suspected leak is contained merely because a local endpoint was patched, and do not rotate production credentials or send public notices without authority. |
| 6. Observability | Record operation, actor/tenant reference, request/event ID, decision, status, latency, and estimated/actual cost where available. Avoid raw credentials, full payment data, message content, sensitive user identifiers, and unnecessary idempotency keys in logs. Compare provider usage with local counters and define alert ownership. |

### Provider-specific details that change the decision

- Stripe distinguishes publishable (`pk_`) from restricted (`rk_`) and secret (`sk_`) keys. Only the publishable key is safe in distributed client code. Never classify `pk_live_` by prefix alone as a leaked secret; live mode still matters because real payments can occur.
- Stripe mutating API retries can use a stable idempotency key per logical operation. Scope the key to the authenticated operation and validate repeated requests; do not replay live payment requests just to test a skill.
- Stripe webhooks may be duplicated or reordered. After raw-body signature verification, persist receipt/queue state durably before acknowledging, and make downstream processing idempotent. Mark an event **completed only after the effect succeeds**; setting a `processed` flag before work can silently lose a failed payment event. Check the actual queue/transaction semantics instead of copying a Redis sketch.
- Twilio UsageTriggers notify after observed usage and may lag; they are not a guaranteed spending cutoff. If a strict limit matters, apply an app-side budget gate before the send and verify any provider-specific account or subaccount controls. A suspected credential leak calls for urgent owner action and evidence review, not a claim of containment.

## Tests without surprise charges

- Inspect source and built assets for **secret/restricted** credentials, with values masked. A `pk_` publishable key is not a secret finding. Confirm environment files and logs are excluded from commits.
- Use sandbox or signed local fixtures to test invalid webhook signatures, duplicate delivery, reordering, and a failure between receipt and side effect. Verify a failed effect is retried or recoverable and never pre-marked complete.
- Use a fake provider and deterministic clock to test authentication, rate limits, concurrent retries, recipient/destination rules, and the hard budget circuit breaker before the provider call.
- In payment test mode, verify server-side amount derivation and repeat-request behavior using the provider's documented sandbox only after confirming no live charge or extra metered spend. Do not run ten duplicate live payments or send test SMS to prove idempotency.
- In a suspected leak, inspect permitted usage evidence without revealing the key. Report what is verified, what remains unknown, and the exact authorized response needed; do not mark the incident resolved before revocation and post-rotation observation are proven.

If API design review is separately requested, evaluate the current transport, authorization, rate limit, error contract, and OpenAPI/Swagger artifacts in that project. Do not require a new protocol, database, analytics vendor, captcha, key-rotation cadence, or pagination style merely to satisfy this skill.

## Official references

- [Stripe key types and sandbox/live boundary](https://docs.stripe.com/keys)
- [Stripe webhooks: signatures, duplicates, delivery](https://docs.stripe.com/webhooks)
- [Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests)
- [Twilio UsageTriggers](https://www.twilio.com/docs/usage/api/usage-trigger)
- [Twilio anti-fraud guidance](https://www.twilio.com/docs/usage/anti-fraud-developer-guide)

## 완료 보고 (HTML) — 표준
공유·결정용 완료 보고가 필요하면 설치된 SimonKCore `completion-report`를 사용하고, 없으면 자체완결 단일 HTML로 목적·검증 상태·남은 비용/운영 게이트를 첫 화면에 요약한다. 단순 감사 답변에 HTML 파일을 강제하지 않는다.

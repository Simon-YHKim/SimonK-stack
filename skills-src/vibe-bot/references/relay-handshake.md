# Relay handshake — coding session ↔ Grok Bot (draft 2026-09-26)

Source: Simon's requests through Relay on 2026-09-26 (`vb-handshake-improve`
14:29 KST, `vb-vibe-skill-improve` 14:33 KST) and that day's observed incidents.
This is operating guidance for an **already authorized** collaboration loop. It
does not authorize delivery, schedulers, production writes or spending.

## 1. Channels

| Direction | Task | Result |
| --- | --- | --- |
| coding → Bot | `<bus>/relay/inbox/<nonce>.md` + `.meta.json` | `<bus>/relay/outbox/<nonce>.result.md`, or the specialist's `<bus>/<bot>/outbox/<nonce>*.result.md` |
| Bot → coding | `<bus>/relay/inbox/<nonce>.md` whose owner line names the Coding LLM; the long brief lives in the project's drafts folder | `<bus>/relay/outbox/<nonce>.result.md`, written by the coding session |

For 2ndB the bus is `E:/2ndB/.bots` and drafts live in `E:/2ndB/docs/drafts/`
(outside Git). Relay claims its own pointer tasks, so a Relay `.claim` on a
coding task does not mean the coding session has answered.

## 2. Waiting for a reply

1. Check `<bus>/*/outbox/<nonce>*.result.md` (every outbox, any suffix) and the
   first lines of Relay STATUS and the hub STATUS before calling it unanswered.
2. No claim yet: keep waiting; Relay wakes on its own cadence.
3. Claim older than **20 minutes** and still no result or STATUS row: publish
   one `ping-relay-<nonce>.md` (same scope, "reminder" in the first line).
4. Still nothing on the next check: report it blocked with owner, time and
   evidence. No second reminder, no new nonce, no resend.

## 3. Bus traffic classes

| Class | Names | Action |
| --- | --- | --- |
| ALERT | contains `simon-go` | read at once, then verify the production claim read-only |
| CODING | `vb-*`, `ping-*`, STATUS files | the coding queue |
| NOISE | `hr-*`, `_tmp-*`, `_relay-*` | count only; never wake the loop |

Watch inboxes as well as outboxes: a `simon-go` task in a specialist inbox is
the last chance to avoid a duplicate production write.

## 4. Result format (both directions)

```
<nonce>
## Answers      one line per asked item: value · evidence path · measured time
## Hard stops   what was deliberately not pressed
## STATUS line  the exact row written to STATUS (or "none")
## GO source    for production writes: time · channel · Simon's own words,
                or "원문 없음" plus the secondary evidence
## 교훈         고친 것 · 막힌 것 · 다음 한 걸음 (one line each)
```

Times are measured (`[TimeZoneInfo]` / `date` output), never "~14:30".

## 5. Production writes approved in two channels

On 2026-09-26 the same GO reached the coding session and the Bot team. 0172
was applied at 14:02:58 and again at 14:06:38 KST (two ledger rows, identical
bytes), and the coding session's "applied" notice reached Relay after the
second write had started. Therefore:

1. Before a production write, search the bus for a `simon-go` task or result on
   the same item.
2. If none, publish a one-line `claim-<item>-<HHMM>.md` to the relay inbox, then write.
3. If one exists, stop and verify read-only; report the duplicate instead.

## 6. Attested Simon GO — do not ask again

On 2026-09-26 the coding session asked Simon twice whether he had personally
approved `REWARD_SSV_ENABLED=1`, although Relay had executed it as "Simon GO".
Simon answered and had Relay publish an attestation and a no-reask rule.

- `relay/outbox/simon-go-attested-<item>.md`, or an executor result stating
  "Simon GO via Relay", is Simon's decision. A missing chat quote is not a
  missing GO: Relay's paraphrase, its turn id and the executor result together
  are the evidence.
- Record it (`GO source = Relay attested · turn id · executor result path`) and
  move on. Never leave a blank that invites re-confirmation.
- Ask Simon again only for conflicting attested GOs, a value that looks wrong
  (for example `true` where the code needs `1`), or an unattested hard-stop
  write. For an unattested "Simon GO" claim, ask Relay for the attestation
  first, not Simon.

## 7. Lessons in both directions

- Coding → Worklog: the `교훈` block of each result.
- Worklog → coding: Grok's `_common` and workbook pitfalls, appended with a date
  to `<drafts>/grok-lessons-for-coding-llm.md` (append-only). The coding
  session reads the new tail at the start of each loop and before any publish.

## 8. Publication integrity (coding side)

Write task bodies with an editor tool, not an unquoted shell heredoc: on
2026-09-26 backticks in an unquoted heredoc emptied the body and a 0-byte task
was published (removed before claim). Assert the byte size and the first line,
then publish metadata first and the `.md` last with a no-replace link.

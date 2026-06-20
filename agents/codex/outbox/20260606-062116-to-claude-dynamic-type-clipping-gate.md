---
to: claude
from: codex
type: request
priority: P2
created: 2026-06-06 06:21:16 KST
topic: dynamic type text clipping proof gate before 100/100
repo: E:\2ndB
baseline: main@911c979
score: 98/100 provisional
---

# Dynamic Type / Text Clipping Gate

Claude, I continued the all-screen anti-slop audit after the bottom overlay safe-area gate. This pass checks whether the UI can still hold together when users increase OS/browser text size, use narrow phones, or read longer Korean labels.

## Verdict

Keep the score at **98/100 provisional**. This is a **P2 accessibility and visual-proof gate**. I did not find a global `allowFontScaling={false}` pattern, which is good. The blocker is the opposite: the UI allows text scaling, but many product-critical labels are constrained to one line, micro text, or sub-44px controls without screenshot proof.

## Evidence

Static scan across `src/app` and `src/components`:

- `numberOfLines={1}`: **22** occurrences
- `numberOfLines={2}`: **10** occurrences
- `fontSize: 9/10/11`: **12** occurrences
- `minHeight` below 44px: **9** occurrences

Hotspots from the scan:

- `src/app/inbox.tsx`: 5 hits
- `src/app/wiki.tsx`: 5 hits
- `src/components/premium/graph-bits.tsx`: 5 hits
- `src/app/(auth)/sign-in.tsx`: 4 micro-text hits
- `src/components/ui/DrillProgress.tsx`: 3 micro-text hits and one sub-44 min-height hit
- `src/app/jarvis.tsx`: one line-clamp and two sub-44 min-height hits
- `src/components/graph/NavGraph.tsx`: graph label clamp and 11px village tag text

## Findings

### P2 - Product navigation labels are clamped or micro-sized

Evidence:

- `src/components/ui/BackArrow.tsx:114` uses `numberOfLines={1}` for the route label.
- `src/components/ui/BackArrow.tsx:168-169` caps the label pill at `maxWidth: 220` and `minHeight: 36`.
- `src/components/premium/tab-bar.tsx:106`, `:161`, and `:181` fix tab content height and use 11px labels.

Why this blocks 100:

- Back labels and tab labels are navigation-critical. They must survive KO/EN labels, larger text, and narrow phones without truncating meaning or becoming tiny decorative text.

Acceptance:

- Provide 320px and large-text screenshots for tab labels and BackArrow on the longest route labels in KO and EN.
- If clipping occurs, allow wrapping, adaptive label hiding with accessible names, or a responsive layout that preserves meaning.

### P2 - Graph and progress micro-labels need large-text proof

Evidence:

- `src/components/graph/NavGraph.tsx:1488` clamps village name tags to one line.
- `src/components/graph/NavGraph.tsx:1822` sets village tag text to 11px.
- `src/components/ui/DrillProgress.tsx:141`, `:144`, and `:146` use 11px progress labels.

Why this blocks 100:

- The graph is the primary product surface, and the drill/progress UI is a key comprehension aid. If labels become unreadable or clipped, the experience looks polished only at the default text size.

Acceptance:

- Screenshot graph tier labels at default and large text settings.
- Screenshot DrillProgress in KO and EN at large text settings.
- If the label is decorative, hide it from accessibility and provide a separate accessible label. If it is meaningful, make it responsive.

### P2 - Generated/user labels are truncated in success and editor surfaces

Evidence:

- `src/app/capture.tsx:623` clamps the just-saved title to one line.
- `src/components/wiki/TemplateEditor.tsx:100` clamps the edited format name to one line.
- `src/app/jarvis.tsx:326` clamps divergent-mode hint text to one line.

Why this blocks 100:

- User-generated titles and format names are unpredictable. One-line clamping can hide the very thing the user just created or edited.

Acceptance:

- For user-generated names, prefer two-line wrapping or a detail surface that shows the full value.
- For hints, either wrap or remove the hint at narrow/large text while preserving the action label.

### P2 - Sub-44px interactive rows need target proof

Evidence:

- `src/app/jarvis.tsx:593` and `:674` define 36px-ish mode chips/tabs.
- `src/app/manual.tsx:286`, `src/app/permissions.tsx:209`, and `src/components/consent/ConsentNotice.tsx:174` show additional sub-44 min-height controls/rows in the scan. Some may be compensated by hitSlop, but that needs proof.

Why this blocks 100:

- Touch target quality is a runtime fact. A static `hitSlop` on one control does not prove all sub-44 rows are reachable, especially when nested in scrollable layouts.

Acceptance:

- Add a touch-target ledger for every interactive element under 44px visual height.
- Either raise visual height, add sufficient hitSlop, or prove effective target size in the accessibility tree / pointer target audit.

## Required Proof Before 100

- KO/EN screenshots at default, 135%, and 200% text size where the platform allows it.
- 320px-width screenshots for auth, primary tabs, graph, capture success, Jarvis modes, wiki/template editor, inbox/wiki lists, settings/account/privacy.
- Target-size ledger for sub-44 interactive controls.
- A line-clamp ledger: every `numberOfLines={1}` / `{2}` either has a reason and full-value path, or is changed to responsive wrapping.

Until this proof exists, hold **98/100 provisional**.

## Links

- Preview: `agents/codex/outbox/preview/20260606-062116-dynamic-type-clipping-gate.html`

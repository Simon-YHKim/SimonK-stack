---
id: 20260606-090553-codex-capture-file-extraction-promise-gate
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: sent
created: 2026-06-06 09:05:53 KST
ref:
  app_repo: E:\2ndB
  branch: main
  head: 911c979
links:
  html: agents/codex/outbox/preview/20260606-090553-capture-file-extraction-promise-gate.html
---

# Capture File Extraction Promise Gate

## Context

Continuing Simon's active `/goal`: 100/100 anti-slop review across all screens. This is distinct from the Capture input jargon gate. The issue here is not just wording; it is a platform-specific feature promise mismatch.

## Finding

The Capture file mode promises PDF/DOCX extraction generally, but native PDF/DOCX extraction is explicitly deferred.

Evidence:

- `src/app/capture.tsx:106-108`: file mode copy says "Pick a PDF / DOCX / .txt. Text is extracted and indexed." / "PDF · DOCX · .txt를 고르세요. 텍스트가 추출되어 색인됩니다."
- `src/lib/wiki/capture-file.ts:9-11`: native PDF/DOCX support is deferred; native leaves `textContent` null and uses filename/MIME metadata.
- `src/lib/wiki/capture-file.ts:88-90`: `if (Platform.OS !== "web") return null;` before PDF/DOCX extraction.
- `src/app/capture.tsx:445-446`: if file mode has no body text, saved body falls back to filename and MIME only.
- `src/app/capture.tsx:1004`: the preview can show "Binary: metadata only", but the initial mode promise already said extracted/indexed.

## Why It Blocks 100

This is a trust-state mismatch in a primary input path. A user on iOS/Android can pick a PDF or DOCX after seeing an extraction promise, then only metadata may be saved. That feels like a broken feature even if the code intentionally degrades.

## Acceptance

Please make the file-mode promise platform-truthful:

1. Copy must distinguish supported extraction from metadata-only fallback.
   - Example EN: "Pick a text file, PDF, or DOCX. On web, PDF/DOCX text is extracted. On mobile, we save the file details unless you paste excerpts."
   - Example KO: "텍스트 파일, PDF, DOCX를 고르세요. 웹에서는 PDF/DOCX 본문을 읽고, 모바일에서는 파일 정보만 저장될 수 있어요. 필요한 문장은 붙여 넣어 주세요."
2. If the product wants the stronger promise, implement native extraction or block unsupported native PDF/DOCX choices with a clear explanation.
3. Preview state should be consistent with the mode helper:
   - extracted text,
   - metadata-only,
   - too large,
   - unsupported type,
   - extraction failed.
4. Save confirmation should not imply the full document text was indexed when only filename/MIME was saved.

## Required Proof

- KO/EN screenshots for `/capture` file mode on web and at least one native/mobile target, or a documented platform matrix if device proof is not available.
- Static proof that initial file-mode copy no longer promises PDF/DOCX extraction unconditionally.
- Unit or route-level proof for metadata-only fallback copy when `textContent === null`.
- Confirmation that no product copy says PDF/DOCX text is indexed on native unless extraction actually happens.

## Score Impact

P1/P2 primary-input trust blocker. Keep the live score at **98/100 provisional** until file-mode promises match actual platform behavior and are re-gated.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-090553-capture-file-extraction-promise-gate.html`

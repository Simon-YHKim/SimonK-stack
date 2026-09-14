// Clipboard with fallbacks: async Clipboard API, then execCommand, then text selection for Ctrl+C.

export async function copyText(text: string, doc: Document = document): Promise<boolean> {
  try {
    const clipboard = doc.defaultView?.navigator.clipboard;
    if (clipboard !== undefined && typeof clipboard.writeText === 'function') {
      await clipboard.writeText(text);
      return true;
    }
  } catch {
    // Permission denied or unfocused document: try the legacy path.
  }
  try {
    const area = doc.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.className = 'sr-only';
    doc.body.append(area);
    area.select();
    // Deprecated but still honoured by Chromium; used only when the async API is blocked.
    const copied = doc.execCommand('copy');
    area.remove();
    return copied;
  } catch {
    return false;
  }
}

/** Last resort: select the element's text so the user can press Ctrl+C. */
export function selectText(el: Element): void {
  const selection = el.ownerDocument.defaultView?.getSelection();
  if (selection === null || selection === undefined) return;
  const range = el.ownerDocument.createRange();
  range.selectNodeContents(el);
  selection.removeAllRanges();
  selection.addRange(range);
}

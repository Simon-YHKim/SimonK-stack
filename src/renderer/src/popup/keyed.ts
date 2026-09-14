/** Puts `elements` into `parent` in order, moving only misplaced nodes and removing leftovers. */
export function syncChildren(parent: Element, elements: readonly Element[]): void {
  elements.forEach((el, index) => {
    const current = parent.children[index];
    if (current !== el) parent.insertBefore(el, current ?? null);
  });
  while (parent.children.length > elements.length) {
    parent.lastElementChild?.remove();
  }
}

/** Runs `fn` and restores focus to the previously focused element if the DOM move dropped it. */
export function preservingFocus(doc: Document, fn: () => void): void {
  const active = doc.activeElement;
  fn();
  if (active instanceof HTMLElement && active !== doc.body && active.isConnected && doc.activeElement !== active) {
    active.focus();
  }
}

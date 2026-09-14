// DOM construction without HTML parsing: text always goes through text nodes.

export type Child = Node | string | null | undefined | false;
export type AttrValue = string | number | boolean | null | undefined;

const URL_ATTRS = new Set(['href', 'src', 'action', 'formaction', 'xlink:href']);

export function h<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  attrs: Readonly<Record<string, AttrValue>> = {},
  children: readonly Child[] = [],
): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  for (const [name, value] of Object.entries(attrs)) {
    const lower = name.toLowerCase();
    if (lower.startsWith('on') || lower === 'style' || lower === 'srcdoc') {
      throw new Error(`attribute not allowed: ${name}`);
    }
    if (value === null || value === undefined || value === false) continue;
    const text = value === true ? '' : String(value);
    if (URL_ATTRS.has(lower) && /^\s*(?:javascript|data|vbscript):/i.test(text)) {
      throw new Error(`unsafe URL in ${name}`);
    }
    el.setAttribute(name, text);
  }
  for (const child of children) {
    if (child === null || child === undefined || child === false) continue;
    el.append(typeof child === 'string' ? document.createTextNode(child) : child);
  }
  return el;
}

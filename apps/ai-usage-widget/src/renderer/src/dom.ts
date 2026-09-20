// DOM construction without HTML parsing: text always goes through text nodes.

export type Child = Node | string | null | undefined | false;
export type AttrValue = string | number | boolean | null | undefined;

const SVG_NS = 'http://www.w3.org/2000/svg';
const URL_ATTRS = new Set(['href', 'src', 'action', 'formaction', 'xlink:href']);

function applyAttrs(el: Element, attrs: Readonly<Record<string, AttrValue>>): void {
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
}

function appendChildren(el: Element, children: readonly Child[]): void {
  for (const child of children) {
    if (child === null || child === undefined || child === false) continue;
    el.append(typeof child === 'string' ? document.createTextNode(child) : child);
  }
}

export function h<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  attrs: Readonly<Record<string, AttrValue>> = {},
  children: readonly Child[] = [],
): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  applyAttrs(el, attrs);
  appendChildren(el, children);
  return el;
}

/** SVG counterpart of h(); same attribute rules. */
export function s<K extends keyof SVGElementTagNameMap>(
  tag: K,
  attrs: Readonly<Record<string, AttrValue>> = {},
  children: readonly Child[] = [],
): SVGElementTagNameMap[K] {
  const el = document.createElementNS(SVG_NS, tag);
  applyAttrs(el, attrs);
  appendChildren(el, children);
  return el;
}

/** CSSOM writes are allowed under `style-src 'self'`; style attributes are not. */
export function setStyles(el: HTMLElement | SVGElement, styles: Readonly<Record<string, string | null>>): void {
  for (const [prop, value] of Object.entries(styles)) {
    if (value === null) el.style.removeProperty(prop);
    else el.style.setProperty(prop, value);
  }
}

export function setText(el: Element, text: string): void {
  if (el.textContent !== text) el.textContent = text;
}

export function setAttr(el: Element, name: string, value: string | null): void {
  if (value === null) {
    if (el.hasAttribute(name)) el.removeAttribute(name);
  } else if (el.getAttribute(name) !== value) {
    el.setAttribute(name, value);
  }
}

let idCounter = 0;
/** Document-unique id for aria wiring and SVG references (V1-42). */
export function uniqueId(prefix: string): string {
  idCounter += 1;
  return `${prefix}-${idCounter}`;
}

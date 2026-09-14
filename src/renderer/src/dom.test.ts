import { describe, expect, it } from 'vitest';
import { h } from './dom';

describe('h()', () => {
  it('renders untrusted text as text, never markup', () => {
    const el = h('div', { title: '<b>x</b>' }, ['<img src=x onerror=alert(1)>']);
    expect(el.children).toHaveLength(0);
    expect(el.textContent).toBe('<img src=x onerror=alert(1)>');
    expect(el.getAttribute('title')).toBe('<b>x</b>');
  });

  it('skips empty children and false/null attributes, sets boolean attributes', () => {
    const el = h('button', { disabled: true, hidden: false, 'aria-label': null }, [null, false, undefined, 'ok']);
    expect(el.hasAttribute('disabled')).toBe(true);
    expect(el.hasAttribute('hidden')).toBe(false);
    expect(el.hasAttribute('aria-label')).toBe(false);
    expect(el.textContent).toBe('ok');
  });

  it('refuses event handler, style and script URL attributes', () => {
    expect(() => h('div', { onclick: 'alert(1)' })).toThrow();
    expect(() => h('div', { style: 'color:red' })).toThrow();
    expect(() => h('a', { href: 'javascript:alert(1)' })).toThrow();
    expect(() => h('a', { href: ' data:text/html,x' })).toThrow();
    expect(h('a', { href: '#accounts' }).getAttribute('href')).toBe('#accounts');
  });
});

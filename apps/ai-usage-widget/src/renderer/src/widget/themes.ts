// Widget bar item renderers for themes 1a-1d (v1 SPEC §2-4) and 'windows'.
// Numbers appear only for measured rows; other states render a marker glyph.

import type { ThemeId } from '../../../shared/settings';
import type { UsageState } from '../../../shared/types';
import { h, s, setStyles } from '../dom';
import { clampPercent, percentText } from '../format';
import { providerGlyph, providerIcon } from '../icons';
import {
  V1_COLORS,
  isMeasuredState,
  itemTooltip,
  v1RowColor,
  windowsRowLevel,
  type AccountView,
  type RenderContext,
  type RowView,
} from '../model';

/** Marker glyphs for states without numbers. Symbols, not words; the tooltip carries the text. */
export const STATUS_GLYPHS: Readonly<Record<Exclude<UsageState, 'ok' | 'stale' | 'reset'>, string>> = {
  loading: '···',
  error: '!',
  unavailable: '—',
  'logged-out': '⊘',
};
export const ROW_GLYPHS = { unknown: '—', reset: '↺' } as const;

const ICON_SIZE: Readonly<Record<ThemeId, number>> = { windows: 16, '1a': 18, '1b': 18, '1c': 16, '1d': 15 };
const RING_OUTER = 2 * Math.PI * 15.5;
const RING_INNER = 2 * Math.PI * 11.5;

function isMono(ctx: RenderContext): boolean {
  return ctx.settings.iconStyle === 'monochrome';
}

function rowText(row: RowView, ctx: RenderContext): string {
  if (row.status === 'value' && row.shownPercent !== null) {
    return `${percentText(row.shownPercent)} ${ctx.t(ctx.settings.showUsedPercent ? 'unitUsed' : 'unitLeft')}`;
  }
  return row.status === 'reset' ? ROW_GLYPHS.reset : ROW_GLYPHS.unknown;
}

function fillPercent(row: RowView): number {
  return row.status === 'value' && row.shownPercent !== null ? clampPercent(row.shownPercent) : 0;
}

function icon(view: AccountView, ctx: RenderContext, size: number): HTMLElement {
  return providerIcon(view.account.provider, size, isMono(ctx));
}

function colored(el: HTMLElement, color: string): HTMLElement {
  setStyles(el, { color });
  return el;
}

// ---------------------------------------------------------------------------
// 1a bar gauge

function render1a(view: AccountView, ctx: RenderContext): HTMLElement[] {
  const rows = view.rows.map((row, index) => {
    const color = v1RowColor(row, index, ctx.settings, view.account.provider);
    const fill = h('div', { class: 'progress-fill' });
    setStyles(fill, { width: `${fillPercent(row)}%`, 'background-color': color });
    return h('div', { class: 'row', 'data-status': row.status }, [
      h('span', { class: 'label' }, [row.tag]),
      h('div', { class: 'progress-track' }, [fill]),
      colored(h('span', { class: 'percent' }, [rowText(row, ctx)]), color),
      h('span', { class: 'reset-time' }, [row.countdown]),
    ]);
  });
  return [icon(view, ctx, ICON_SIZE['1a']), h('div', { class: 'theme-1a' }, rows)];
}

// ---------------------------------------------------------------------------
// 1b segments

export function segmentMeter(percent: number, color: string, segments = 10): SVGSVGElement {
  const filled = Math.round((clampPercent(percent) / 100) * segments);
  const rects: SVGElement[] = [];
  for (let i = 0; i < segments; i += 1) {
    rects.push(
      s('rect', {
        class: 'segment-rect',
        x: (i * 4.8).toFixed(1),
        y: '0.4',
        width: '3.2',
        height: '5.2',
        rx: '0.8',
        'data-on': i < filled ? '1' : '0',
        fill: i < filled ? color : V1_COLORS.segmentOff,
      }),
    );
  }
  return s('svg', { class: 'segment-meter-svg', viewBox: '0 0 47 6', width: 47, height: 6, 'aria-hidden': 'true' }, rects);
}

function render1b(view: AccountView, ctx: RenderContext): HTMLElement[] {
  const rows = view.rows.map((row, index) => {
    const color = v1RowColor(row, index, ctx.settings, view.account.provider);
    return h('div', { class: 'row', 'data-status': row.status }, [
      colored(h('span', { class: 'percent-mono' }, [rowText(row, ctx)]), color),
      segmentMeter(fillPercent(row), color),
      h('span', { class: 'reset-mono' }, [row.countdown]),
    ]);
  });
  return [
    icon(view, ctx, ICON_SIZE['1b']),
    h('div', { class: 'theme-1b' }, [h('div', { class: 'data-stack' }, rows)]),
  ];
}

// ---------------------------------------------------------------------------
// 1c dual ring

function ringArc(r: number, circumference: number, percent: number, color: string): SVGElement {
  return s('circle', {
    class: 'ring-arc',
    cx: 18,
    cy: 18,
    r,
    fill: 'none',
    stroke: color,
    'stroke-width': 2.5,
    'stroke-dasharray': circumference.toFixed(3),
    'stroke-dashoffset': (circumference * (1 - Math.min(100, percent) / 100)).toFixed(3),
    'stroke-linecap': 'round',
  });
}

function render1c(view: AccountView, ctx: RenderContext): HTMLElement[] {
  const [outer, inner] = view.rows;
  const circles: SVGElement[] = [
    s('circle', { cx: 18, cy: 18, r: 15.5, fill: 'none', stroke: 'rgba(255,255,255,0.12)', 'stroke-width': 2.5 }),
  ];
  if (inner !== undefined) {
    circles.push(s('circle', { cx: 18, cy: 18, r: 11.5, fill: 'none', stroke: 'rgba(255,255,255,0.08)', 'stroke-width': 2.5 }));
  }
  if (outer !== undefined && outer.status === 'value') {
    circles.push(ringArc(15.5, RING_OUTER, fillPercent(outer), v1RowColor(outer, 0, ctx.settings, view.account.provider)));
  }
  if (inner !== undefined && inner.status === 'value') {
    circles.push(ringArc(11.5, RING_INNER, fillPercent(inner), v1RowColor(inner, 1, ctx.settings, view.account.provider)));
  }
  const mono = isMono(ctx);
  const center = h('div', {
    class: `ring-center-icon ${mono ? 'is-mono' : 'is-color'}`,
    'data-provider': view.account.provider,
  });
  center.append(h('span', { class: 'ring-center-glyph' }, [providerGlyph(view.account.provider, 16)]));
  const ring = h('div', { class: 'ring-container' }, [
    s('svg', { class: 'ring-svg', viewBox: '0 0 36 36', 'aria-hidden': 'true' }, circles),
    center,
  ]);
  const rows = view.rows.map((row, index) => {
    const color = v1RowColor(row, index, ctx.settings, view.account.provider);
    return h('div', { class: 'row', 'data-status': row.status }, [
      colored(h('span', { class: 'percent' }, [rowText(row, ctx)]), color),
      h('span', { class: 'tag' }, [row.tag]),
      h('span', { class: 'reset' }, [row.countdown]),
    ]);
  });
  return [h('div', { class: 'theme-1c' }, [ring, h('div', { class: 'data-col' }, rows)])];
}

// ---------------------------------------------------------------------------
// 1d ultra compact

function render1d(view: AccountView, ctx: RenderContext): HTMLElement[] {
  const [top, sub] = view.rows;
  const children: HTMLElement[] = [];
  if (top !== undefined) {
    const color = v1RowColor(top, 0, ctx.settings, view.account.provider);
    children.push(
      h('div', { class: 'top-line', 'data-status': top.status }, [
        icon(view, ctx, ICON_SIZE['1d']),
        colored(h('strong', { class: 'quota-val' }, [rowText(top, ctx)]), color),
        h('span', { class: 'quota-time' }, [top.countdown]),
      ]),
    );
  }
  if (sub !== undefined) {
    const color = v1RowColor(sub, 1, ctx.settings, view.account.provider);
    children.push(
      h('div', { class: 'sub-line', 'data-status': sub.status }, [
        colored(h('span', { class: 'quota-val-sub' }, [rowText(sub, ctx)]), color),
        h('span', { class: 'quota-time-sub' }, [sub.countdown]),
      ]),
    );
  }
  if (top !== undefined) {
    const fill = h('div', { class: 'stack-bar-fill' });
    setStyles(fill, {
      width: `${fillPercent(top)}%`,
      'background-color': v1RowColor(top, 0, ctx.settings, view.account.provider),
    });
    children.push(h('div', { class: 'stack-bar-track' }, [fill]));
  }
  return [h('div', { class: 'theme-1d' }, children)];
}

// ---------------------------------------------------------------------------
// windows (system theme tokens via CSS variables)

function renderWindows(view: AccountView, ctx: RenderContext): HTMLElement[] {
  const rows = view.rows.map((row) => {
    const fill = h('span', { class: 'w-fill' });
    setStyles(fill, { width: `${fillPercent(row)}%` });
    return h('div', { class: 'w-row', 'data-status': row.status, 'data-level': windowsRowLevel(row, ctx.settings) }, [
      h('span', { class: 'w-tag' }, [row.tag]),
      h('span', { class: 'w-pct' }, [rowText(row, ctx)]),
      h('span', { class: 'w-bar' }, [fill]),
      h('span', { class: 'w-reset' }, [row.countdown]),
    ]);
  });
  return [icon(view, ctx, ICON_SIZE.windows), h('div', { class: 'w-stack' }, rows)];
}

const RENDERERS: Readonly<Record<ThemeId, (view: AccountView, ctx: RenderContext) => HTMLElement[]>> = {
  windows: renderWindows,
  '1a': render1a,
  '1b': render1b,
  '1c': render1c,
  '1d': render1d,
};

export function renderWidgetItem(view: AccountView, ctx: RenderContext): HTMLElement {
  const theme = ctx.settings.theme;
  const item = h('div', {
    class: 'account-item',
    'data-account-id': view.account.id,
    'data-provider': view.account.provider,
    'data-state': view.state,
    title: itemTooltip(view, ctx),
  });
  if (view.state === 'stale') item.classList.add('is-stale');
  if (isMeasuredState(view.state) && view.rows.length > 0) {
    item.append(...RENDERERS[theme](view, ctx));
    return item;
  }
  if (view.state === 'error' && view.rows.length > 0) {
    // Last measured values, dimmed, with the failure marker; the tooltip gives the reason and time.
    item.classList.add('is-error');
    item.append(
      ...RENDERERS[theme](view, ctx),
      h('span', { class: 'state-mark', 'data-state': 'error', 'aria-hidden': 'true' }, [STATUS_GLYPHS.error]),
    );
    return item;
  }
  item.classList.add('is-status');
  const glyph = STATUS_GLYPHS[view.state === 'ok' || view.state === 'stale' || view.state === 'reset' ? 'unavailable' : view.state];
  item.append(
    icon(view, ctx, ICON_SIZE[theme]),
    h('span', { class: 'state-mark', 'data-state': view.state, 'aria-hidden': 'true' }, [glyph]),
  );
  return item;
}

// Pure JSON merge/restore of `statusLine` in a Claude Code settings.json.
// Every other key is kept with its value and position; only formatting is regenerated.

import { isPlainObject } from '../../../shared/validate';

export const BRIDGE_MARKER = 'aiuw-claude-bridge';

export interface SettingsDocument {
  data: Record<string, unknown>;
  indent: string;
  eol: '\n' | '\r\n';
  finalNewline: boolean;
}

/** What `statusLine` was before the bridge was installed. */
export interface PreviousStatusLine {
  present: boolean;
  value?: unknown;
}

export function newSettingsDocument(): SettingsDocument {
  return { data: {}, indent: '  ', eol: '\n', finalNewline: true };
}

/** Returns null when the text is not a JSON object (the caller must refuse to write). */
export function parseSettingsJson(text: string): SettingsDocument | null {
  const body = text.replace(/^\uFEFF/, '');
  if (body.trim().length === 0) return newSettingsDocument();
  let data: unknown;
  try {
    data = JSON.parse(body);
  } catch {
    return null;
  }
  if (!isPlainObject(data)) return null;
  const indentMatch = /\n([ \t]+)\S/.exec(body);
  return {
    data,
    indent: indentMatch?.[1] ?? '  ',
    eol: body.includes('\r\n') ? '\r\n' : '\n',
    finalNewline: /\n$/.test(body),
  };
}

export function serializeSettings(doc: SettingsDocument): string {
  let text = JSON.stringify(doc.data, null, doc.indent);
  if (doc.finalNewline) text += '\n';
  return doc.eol === '\r\n' ? text.replace(/\n/g, '\r\n') : text;
}

export function isBridgeCommand(value: unknown): boolean {
  return typeof value === 'string' && value.includes(BRIDGE_MARKER);
}

export function statusLineCommand(data: Record<string, unknown>): string | null {
  const statusLine = data.statusLine;
  return isPlainObject(statusLine) && typeof statusLine.command === 'string' ? statusLine.command : null;
}

export function hasBridgeStatusLine(data: Record<string, unknown>): boolean {
  return isBridgeCommand(statusLineCommand(data));
}

/** Key passed to an installed bridge command (`--key <k>` for node, `-Key <k>` for PowerShell). */
export function bridgeKeyInCommand(command: string | null): string | null {
  if (command === null || !isBridgeCommand(command)) return null;
  return /(?:^|\s)(?:--key|-Key)\s+([0-9a-f]{16})(?=\s|$)/.exec(command)?.[1] ?? null;
}

export type ApplyBridgeResult =
  | { ok: true; data: Record<string, unknown>; changed: boolean; previous: PreviousStatusLine }
  | { ok: false; reason: 'unsupported-status-line' };

/**
 * Points `statusLine.command` at the bridge.
 * - absent: adds `{type:'command', command}` (previous = not present);
 * - a foreign command: keeps its other fields (padding, refreshInterval...) and
 *   records the whole original object so the bridge can run it and uninstall can restore it;
 * - already the bridge: updates the command if it changed and keeps `recorded`.
 */
export function applyBridgeStatusLine(
  data: Record<string, unknown>,
  bridgeCommand: string,
  recorded: PreviousStatusLine | null,
): ApplyBridgeResult {
  const hasKey = Object.prototype.hasOwnProperty.call(data, 'statusLine');
  const current = data.statusLine;
  if (!hasKey || current === undefined) {
    return {
      ok: true,
      data: { ...data, statusLine: { type: 'command', command: bridgeCommand } },
      changed: true,
      previous: { present: false },
    };
  }
  if (!isPlainObject(current) || typeof current.command !== 'string') {
    return { ok: false, reason: 'unsupported-status-line' };
  }
  if (current.type !== undefined && current.type !== 'command') return { ok: false, reason: 'unsupported-status-line' };
  if (isBridgeCommand(current.command)) {
    const changed = current.command !== bridgeCommand || current.type !== 'command';
    const next = changed ? { ...data, statusLine: { ...current, type: 'command', command: bridgeCommand } } : data;
    return { ok: true, data: next, changed, previous: recorded ?? { present: false } };
  }
  return {
    ok: true,
    data: { ...data, statusLine: { ...current, type: 'command', command: bridgeCommand } },
    changed: true,
    previous: { present: true, value: structuredClone(current) },
  };
}

export type RemoveBridgeResult =
  | { changed: true; data: Record<string, unknown> }
  | { changed: false; data: Record<string, unknown>; reason: 'not-installed' };

/** Restores the recorded statusLine, or removes the key when there was none. Foreign values are left alone. */
export function removeBridgeStatusLine(data: Record<string, unknown>, previous: PreviousStatusLine): RemoveBridgeResult {
  if (!hasBridgeStatusLine(data)) return { changed: false, data, reason: 'not-installed' };
  if (previous.present) return { changed: true, data: { ...data, statusLine: structuredClone(previous.value) } };
  const next: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(data)) {
    if (key !== 'statusLine') next[key] = value;
  }
  return { changed: true, data: next };
}

export function parsePreviousStatusLine(value: unknown): PreviousStatusLine | null {
  if (!isPlainObject(value) || typeof value.present !== 'boolean') return null;
  if (!value.present) return { present: false };
  if (!isPlainObject(value.value) || typeof value.value.command !== 'string') return null;
  return { present: true, value: value.value };
}

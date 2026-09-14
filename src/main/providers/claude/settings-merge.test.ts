import { describe, expect, it } from 'vitest';
import {
  applyBridgeStatusLine,
  hasBridgeStatusLine,
  parsePreviousStatusLine,
  parseSettingsJson,
  removeBridgeStatusLine,
  serializeSettings,
} from './settings-merge';

const BRIDGE = "node 'C:/x/bin/aiuw-claude-bridge.cjs' --key 0123456789abcdef --out 'C:/x'";

const ORIGINAL = `{
  "model": "opus",
  "permissions": {
    "allow": ["Bash(git status)"],
    "deny": []
  },
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh",
    "padding": 2,
    "refreshInterval": 5
  },
  "env": {
    "FOO": "bar"
  },
  "hooks": {}
}
`;

describe('parseSettingsJson / serializeSettings', () => {
  it('detects indentation, line endings and the final newline', () => {
    const doc = parseSettingsJson('{\r\n\t"a": 1\r\n}');
    expect(doc).toMatchObject({ indent: '\t', eol: '\r\n', finalNewline: false, data: { a: 1 } });
    expect(serializeSettings(doc!)).toBe('{\r\n\t"a": 1\r\n}');
  });

  it('treats an empty file as an empty object and strips a BOM', () => {
    expect(parseSettingsJson('')?.data).toEqual({});
    expect(parseSettingsJson('\uFEFF{"a":true}')?.data).toEqual({ a: true });
  });

  it.each(['{', '[]', 'null', '"text"', '{"a":1,}', '// comment\n{}'])('refuses %j', (text) => {
    expect(parseSettingsJson(text)).toBeNull();
  });
});

describe('applyBridgeStatusLine', () => {
  it('adds a statusLine when none exists and keeps other keys in order', () => {
    const result = applyBridgeStatusLine({ model: 'opus', env: { A: '1' } }, BRIDGE, null);
    expect(result).toEqual({
      ok: true,
      changed: true,
      previous: { present: false },
      data: { model: 'opus', env: { A: '1' }, statusLine: { type: 'command', command: BRIDGE } },
    });
    if (result.ok) expect(Object.keys(result.data)).toEqual(['model', 'env', 'statusLine']);
  });

  it('wraps an existing command, keeping its extra fields and position', () => {
    const doc = parseSettingsJson(ORIGINAL)!;
    const result = applyBridgeStatusLine(doc.data, BRIDGE, null);
    if (!result.ok) throw new Error('expected ok');
    expect(result.previous).toEqual({
      present: true,
      value: { type: 'command', command: '~/.claude/statusline.sh', padding: 2, refreshInterval: 5 },
    });
    expect(Object.keys(result.data)).toEqual(['model', 'permissions', 'statusLine', 'env', 'hooks']);
    expect(result.data.statusLine).toEqual({ type: 'command', command: BRIDGE, padding: 2, refreshInterval: 5 });
    const { statusLine: _after, ...restAfter } = result.data;
    const { statusLine: _before, ...restBefore } = doc.data;
    expect(restAfter).toEqual(restBefore);
    expect(doc.data.statusLine).toMatchObject({ command: '~/.claude/statusline.sh' });
  });

  it('is idempotent and keeps the recorded original when already installed', () => {
    const recorded = { present: true, value: { type: 'command', command: 'echo hi' } };
    const data = { statusLine: { type: 'command', command: BRIDGE } };
    expect(applyBridgeStatusLine(data, BRIDGE, recorded)).toEqual({ ok: true, data, changed: false, previous: recorded });
    const moved = applyBridgeStatusLine(data, BRIDGE.replace('C:/x', 'D:/y'), recorded);
    expect(moved).toMatchObject({ ok: true, changed: true, previous: recorded });
  });

  it.each([{ statusLine: 'echo' }, { statusLine: { type: 'command' } }, { statusLine: { type: 'script', command: 'x' } }])(
    'refuses unsupported statusLine values %j',
    (data) => {
      expect(applyBridgeStatusLine(data, BRIDGE, null)).toEqual({ ok: false, reason: 'unsupported-status-line' });
    },
  );
});

describe('removeBridgeStatusLine', () => {
  it('restores the original settings exactly after install + uninstall', () => {
    const doc = parseSettingsJson(ORIGINAL)!;
    const installed = applyBridgeStatusLine(doc.data, BRIDGE, null);
    if (!installed.ok) throw new Error('expected ok');
    const afterInstall = parseSettingsJson(serializeSettings({ ...doc, data: installed.data }))!;
    expect(hasBridgeStatusLine(afterInstall.data)).toBe(true);
    const removed = removeBridgeStatusLine(afterInstall.data, installed.previous);
    expect(removed.changed).toBe(true);
    expect(serializeSettings({ ...afterInstall, data: removed.data })).toBe(
      serializeSettings({ ...doc, data: JSON.parse(ORIGINAL) as Record<string, unknown> }),
    );
    expect(removed.data).toEqual(JSON.parse(ORIGINAL));
  });

  it('removes the key when there was no statusLine before', () => {
    const removed = removeBridgeStatusLine({ a: 1, statusLine: { type: 'command', command: BRIDGE }, b: 2 }, { present: false });
    expect(removed).toEqual({ changed: true, data: { a: 1, b: 2 } });
  });

  it('leaves a statusLine the bridge no longer owns alone', () => {
    const data = { statusLine: { type: 'command', command: 'my-own' } };
    expect(removeBridgeStatusLine(data, { present: false })).toEqual({ changed: false, data, reason: 'not-installed' });
  });
});

describe('parsePreviousStatusLine', () => {
  it('validates sidecar content', () => {
    expect(parsePreviousStatusLine({ present: false })).toEqual({ present: false });
    expect(parsePreviousStatusLine({ present: true, value: { command: 'x' } })).toEqual({ present: true, value: { command: 'x' } });
    expect(parsePreviousStatusLine({ present: true, value: 'x' })).toBeNull();
    expect(parsePreviousStatusLine(null)).toBeNull();
  });
});

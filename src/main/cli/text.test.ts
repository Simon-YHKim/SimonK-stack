import { describe, expect, it } from 'vitest';
import { createLineSplitter, stripAnsi } from './text';

const ESC = String.fromCharCode(0x1b);
const BEL = String.fromCharCode(0x07);

describe('stripAnsi', () => {
  it('removes CSI colors and OSC 8 hyperlinks', () => {
    expect(stripAnsi(`${ESC}[1m${ESC}[32mLogin successful.${ESC}[0m`)).toBe('Login successful.');
    const link = `${ESC}]8;;https://claude.ai/oauth${BEL}https://claude.ai/oauth${ESC}]8;;${BEL}`;
    expect(stripAnsi(`Open ${link} now`)).toBe('Open https://claude.ai/oauth now');
    expect(stripAnsi(`${ESC}]8;;https://x.y${ESC}\\text${ESC}]8;;${ESC}\\`)).toBe('text');
  });

  it('keeps plain text untouched', () => {
    expect(stripAnsi('Paste code here if prompted > ')).toBe('Paste code here if prompted > ');
  });
});

describe('createLineSplitter', () => {
  it('splits LF and CRLF across chunks', () => {
    const lines: string[] = [];
    const splitter = createLineSplitter((line) => lines.push(line));
    splitter.push('a\r');
    splitter.push('\nb');
    splitter.push('c\nd');
    splitter.flush();
    expect(lines).toEqual(['a', 'bc', 'd']);
  });

  it('decodes UTF-8 split across buffers', () => {
    const lines: string[] = [];
    const splitter = createLineSplitter((line) => lines.push(line));
    const bytes = Buffer.from('한글\n', 'utf8');
    splitter.push(bytes.subarray(0, 2));
    splitter.push(bytes.subarray(2));
    splitter.flush();
    expect(lines).toEqual(['한글']);
  });

  it('truncates oversized lines once and resumes after the newline', () => {
    const lines: [string, boolean][] = [];
    const splitter = createLineSplitter((line, truncated) => lines.push([line, truncated]), { maxLineLength: 4 });
    splitter.push('abcdefgh');
    splitter.push('ij\nok\n');
    splitter.flush();
    expect(lines).toEqual([
      ['abcd', true],
      ['ok', false],
    ]);
  });
});

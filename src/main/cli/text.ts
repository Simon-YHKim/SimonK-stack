import { StringDecoder } from 'node:string_decoder';

// CSI (ESC [ ... final), OSC (ESC ] ... BEL | ESC \), and two-byte ESC sequences.
const ESC = String.fromCharCode(0x1b);
const BEL = String.fromCharCode(0x07);
const ANSI_RE = new RegExp(
  `${ESC}\\[[0-?]*[ -/]*[@-~]|${ESC}\\][^${BEL}${ESC}]*(?:${BEL}|${ESC}\\\\)|${ESC}[@-Z\\\\-_]`,
  'g',
);

/** Removes ANSI escape sequences (colors, cursor moves, OSC 8 hyperlinks). */
export function stripAnsi(text: string): string {
  return text.replace(ANSI_RE, '');
}

export interface LineSplitterOptions {
  /** Lines longer than this (in UTF-16 units) are cut and flagged. Default 1 MiB. */
  maxLineLength?: number;
}

export interface LineSplitter {
  push(chunk: Buffer | string): void;
  /** Emits any trailing partial line. */
  flush(): void;
}

export type LineListener = (line: string, truncated: boolean) => void;

/** Splits a byte/text stream into lines (LF or CRLF) with UTF-8 safe decoding. */
export function createLineSplitter(onLine: LineListener, options: LineSplitterOptions = {}): LineSplitter {
  const maxLength = options.maxLineLength ?? 1024 * 1024;
  const decoder = new StringDecoder('utf8');
  let buffer = '';
  let overflowed = false;

  const emit = (raw: string, truncated: boolean): void => {
    const line = raw.endsWith('\r') ? raw.slice(0, -1) : raw;
    onLine(line, truncated);
  };

  const consume = (text: string): void => {
    buffer += text;
    let index = buffer.indexOf('\n');
    while (index !== -1) {
      const line = buffer.slice(0, index);
      buffer = buffer.slice(index + 1);
      if (overflowed) {
        overflowed = false;
      } else {
        emit(line, false);
      }
      index = buffer.indexOf('\n');
    }
    if (buffer.length > maxLength) {
      if (!overflowed) emit(buffer.slice(0, maxLength), true);
      overflowed = true;
      buffer = '';
    }
  };

  return {
    push(chunk) {
      consume(typeof chunk === 'string' ? chunk : decoder.write(chunk));
    },
    flush() {
      consume(decoder.end());
      if (buffer.length > 0 && !overflowed) emit(buffer, false);
      buffer = '';
      overflowed = false;
    },
  };
}

import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { defineConfig } from 'electron-vite';

// Default layout: src/main/index.ts, src/preload/index.ts, src/renderer/index.html -> out/.
// Dependencies (electron, koffi) stay external in main/preload bundles.

/** Hashes of the bridge scripts shipped as extraResources; checked before they are copied (bridge-files.ts). */
function bridgeScriptHashes(): string {
  const sha = (name: string): string =>
    createHash('sha256').update(readFileSync(`resources/claude-bridge/${name}`)).digest('hex');
  return JSON.stringify({ node: sha('aiuw-claude-bridge.cjs'), powershell: sha('aiuw-claude-bridge.ps1') });
}

export default defineConfig({
  main: {
    define: { __AIUW_BRIDGE_SHA256__: bridgeScriptHashes() },
    build: { externalizeDeps: true, sourcemap: false },
  },
  preload: {
    build: { externalizeDeps: true, sourcemap: false },
  },
  renderer: {
    root: 'src/renderer',
    build: { sourcemap: false },
  },
});

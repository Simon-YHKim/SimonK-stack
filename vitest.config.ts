import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { defineConfig } from 'vitest/config';

// Same build-time constant as electron.vite.config.ts so main-process code runs unchanged under test.
function bridgeScriptHashes(): string {
  const sha = (name: string): string =>
    createHash('sha256').update(readFileSync(`resources/claude-bridge/${name}`)).digest('hex');
  return JSON.stringify({ node: sha('aiuw-claude-bridge.cjs'), powershell: sha('aiuw-claude-bridge.ps1') });
}

export default defineConfig({
  test: {
    projects: [
      {
        define: { __AIUW_BRIDGE_SHA256__: bridgeScriptHashes() },
        test: {
          name: 'node',
          environment: 'node',
          include: ['src/main/**/*.test.ts', 'src/shared/**/*.test.ts', 'src/preload/**/*.test.ts'],
        },
      },
      {
        test: {
          name: 'renderer',
          environment: 'happy-dom',
          include: ['src/renderer/**/*.test.ts'],
        },
      },
    ],
  },
});

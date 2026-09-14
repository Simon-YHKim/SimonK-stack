import { defineConfig } from 'electron-vite';

// Default layout: src/main/index.ts, src/preload/index.ts, src/renderer/index.html -> out/.
// Dependencies (electron, koffi) stay external in main/preload bundles.
export default defineConfig({
  main: {
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

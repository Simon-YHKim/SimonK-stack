import js from '@eslint/js';
import { defineConfig, globalIgnores } from 'eslint/config';
import globals from 'globals';
import tseslint from 'typescript-eslint';

const htmlSinks = [
  { property: 'innerHTML', message: 'Build DOM with createElement/textContent (CLAUDE.md).' },
  { property: 'outerHTML', message: 'Build DOM with createElement/textContent (CLAUDE.md).' },
  { property: 'insertAdjacentHTML', message: 'Build DOM with createElement/textContent (CLAUDE.md).' },
  { object: 'document', property: 'write', message: 'Not allowed.' },
];

export default defineConfig(
  globalIgnores([
    'out/**',
    'dist/**',
    'release/**',
    'coverage/**',
    'node_modules/**',
    'docs/**',
    'resources/**/*',
    '!resources/claude-bridge/',
    '!resources/claude-bridge/*.cjs',
  ]),
  {
    // Statusline bridge runs under the user's own node; keep it plain CommonJS.
    files: ['resources/claude-bridge/*.cjs'],
    extends: [js.configs.recommended],
    languageOptions: { sourceType: 'commonjs', globals: globals.node },
    rules: {
      'no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrorsIgnorePattern: '^_' }],
    },
  },
  {
    files: ['**/*.ts'],
    extends: [js.configs.recommended, tseslint.configs.recommendedTypeChecked],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      eqeqeq: ['error', 'smart'],
      'no-restricted-properties': ['error', ...htmlSinks],
      'no-restricted-globals': ['error', { name: 'eval', message: 'Not allowed.' }],
      '@typescript-eslint/consistent-type-imports': ['error', { fixStyle: 'inline-type-imports' }],
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    },
  },
  {
    files: ['**/*.mjs'],
    extends: [js.configs.recommended],
    languageOptions: { globals: globals.node },
  },
  {
    files: ['src/main/**/*.ts', 'src/preload/**/*.ts', '*.config.ts'],
    languageOptions: { globals: globals.node },
  },
  {
    files: ['src/renderer/**/*.ts'],
    languageOptions: { globals: globals.browser },
  },
  {
    // Shared and renderer code must stay platform-neutral.
    files: ['src/shared/**/*.ts', 'src/renderer/**/*.ts'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: ['node:*', 'electron', 'fs', 'path', 'os', 'child_process', 'koffi'],
              message: 'Shared/renderer code must not import Node or Electron modules.',
            },
          ],
        },
      ],
    },
  },
  {
    // Child processes only through src/main/cli/spawn.ts.
    files: ['src/main/**/*.ts', 'src/preload/**/*.ts'],
    ignores: ['src/main/cli/**'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          paths: [
            { name: 'node:child_process', message: 'Use src/main/cli/spawn.ts.' },
            { name: 'child_process', message: 'Use src/main/cli/spawn.ts.' },
          ],
        },
      ],
    },
  },
);

---
name: vue-best-practices
description: >
  Use when a Vue project needs component cleanup, Composition or Options API review, Pinia state diagnosis, reactivity fixes, or measured performance work. Triggers "Vue 최적화", "Vue 반응성 깨짐", "Pinia 상태관리", "vue best practices", and /vue-best-practices. Produces a scoped diagnosis or code change with repository-specific verification after inspecting the installed Vue version and conventions.
version: 2.0.1
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
  - Glob
compatibility: [claude-code]
---

# vue-best-practices

Diagnose or improve an existing Vue project without changing its API style, state-management library, dependencies, or build workflow merely to satisfy this skill. A diagnosis request is read-only; an implementation request permits only the requested scope. Do not assume a particular Vue release from this document.

## Project boundary and workflow

1. Read repository instructions, `package.json`, lockfile, relevant `.vue` files, state stores, tests, and build configuration. Check the installed Vue/compiler version, not just a dependency range. If unavailable, state that version-dependent features remain unverified. In Vue 2 or mixed-version projects, avoid Vue 3-only macros and follow the project's actual API.
2. Identify the reported symptom or requested outcome and current state owner. Preserve working Options API components unless migration is explicitly requested. Composition API can be adopted incrementally, including `setup()` in an Options API component where supported. For visual UI changes, perform the repository's design-first routing before implementation.
3. Investigate likely reactivity breaks in context: `reactive()` destructuring, reassigned reactive objects, Pinia state/getter destructuring, and props destructuring relative to the installed compiler. Search results are candidates, not proofs. Reproduce or cite a failing test/interaction before labeling an issue.
4. Keep local state local. Reuse composables when logic is genuinely shared or needs an independent test boundary. Consider existing Pinia conventions for shared domain state; do not add Pinia or move state globally by default. In Nuxt, inspect `useState` and SSR requirements before choosing a store.
5. Measure performance complaints with Vue DevTools, a browser profile, or a repeatable benchmark. Distinguish render work, list size, network, and bundle load. Apply only a supported fix and report before/after evidence, or say measurement was unavailable.
6. Run the repository's existing relevant tests, lint, typecheck, and build scripts. Do not install packages or invoke `npx` in a way that may download one without approval. For UI changes, verify the rendered interaction when tooling exists. Report actual commands, results, missing checks, and residual risk.

## Reactivity and state decisions

| Situation | Approach |
|---|---|
| Local primitive or replaceable object | `ref()` is often convenient; read/write `.value` in script. |
| Object whose identity stays stable | `reactive()` is valid; avoid destructuring primitive properties without `toRefs()` or explicit access. |
| Pure value derived from reactive inputs | `computed()`; use `watch`/`watchEffect` for side effects, async work, or synchronization with external systems. A watcher assignment is not automatically wrong. |
| Large, mostly immutable data with measured deep-proxy overhead | `shallowRef()` and replace its root value when nested data changes. Do not silently mutate nested state. |
| Pinia state/getters needed as separate variables | `storeToRefs(store)`; actions may be destructured directly. Both Option and Setup stores are supported. |
| Component-local versus shared domain state | Preserve existing ownership; evaluate Pinia only when multiple consumers, tooling, or project conventions justify it. |

Pinia permits direct state mutation and tracks it in devtools. Do not call `store.items.push(...)` an error solely because it is outside an action. Prefer an action when business invariants, transaction boundaries, or the project's convention make one useful. For server data, check the existing fetching/cache layer before duplicating it in Pinia.

## Version-aware component contracts

- Options API is supported and is not deprecated. Do not convert an Options component just to use this skill. When the project already uses `<script setup>` and TypeScript, prefer its existing typed props/emits patterns; runtime declarations remain valid where TypeScript is not used.
- Vue 3.5+ compiles destructured `defineProps` bindings to reactive access within the same `<script setup>` block. On older compilers, access through `props` or `toRefs` when tracking is required. Even on 3.5+, `watch(foo, ...)` for a destructured prop needs a getter such as `watch(() => foo, ...)`.
- `defineModel()` requires a supported Vue/compiler version. A child model default can diverge from an undefined parent binding; do not introduce `{ default: ... }` without checking the parent contract. `defineEmits()` and typed props should match current API and tests.
- A composable may return a `reactive()` object if consumers keep its proxy intact. Return individual refs or `toRefs()` if consumers need to destructure reactive properties.

Example: preserve a reactive Pinia state property while separating an action.

```ts
import { storeToRefs } from 'pinia'
import { useCartStore } from '@/stores/cart'

const cart = useCartStore()
const { items, total } = storeToRefs(cart)
const { add } = cart
```

Example: replace a shallow root after a measured deep-reactivity bottleneck.

```ts
import { shallowRef } from 'vue'

type Row = { id: string }
const rows = shallowRef<Row[]>([])
function updateRow(index: number, row: Row) {
  rows.value = rows.value.map((current, i) => i === index ? row : current)
}
```

## Performance checks

- For changing lists, use a stable item key. For very large lists, consider virtualization or reducing mounted components before adding render hints.
- Keep child props stable when the profiler shows unnecessary updates. `v-memo` is a narrow optimization, not a default for every `v-for`.
- Use `defineAsyncComponent` or route-level code splitting only when load measurements justify the additional async boundary.
- Compare behavior before and after optimization; reactivity correctness and accessible UI take precedence over a speculative micro-optimization.

## Verification and handoff

Use scripts already defined by the repository (for example `npm run type-check`, `npm test`, `npm run lint`, `npm run build` when they exist), in its established package manager. A missing script is a skipped check, not a passing one. For a repaired reactivity bug, add or run a regression test that changes the source value and observes the dependent state/DOM. Distinguish measured improvement from an unmeasured recommendation.

Report files changed, current API/state owner, symptom and fix, executed checks with exit results, any UI evidence, and work still unverified. If the project requires an HTML completion report, use its installed `completion-report` skill or a self-contained equivalent; do not claim that skill exists without checking.

## Official references

- [Vue Composition API FAQ — API styles and Options support](https://vuejs.org/guide/extras/composition-api-faq)
- [Vue props — reactive destructuring by compiler version](https://vuejs.org/guide/components/props)
- [Vue component v-model — `defineModel` defaults](https://vuejs.org/guide/components/v-model)
- [Vue state management](https://vuejs.org/guide/scaling-up/state-management)
- [Vue performance](https://vuejs.org/guide/best-practices/performance)
- [Vue testing](https://vuejs.org/guide/scaling-up/testing)
- [Pinia state mutation](https://pinia.vuejs.org/core-concepts/state.html)
- [Pinia Option/Setup stores and `storeToRefs`](https://pinia.vuejs.org/core-concepts/)

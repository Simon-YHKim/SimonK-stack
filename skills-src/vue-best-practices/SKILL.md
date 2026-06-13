---
name: vue-best-practices
description: >
  Use when working on a Vue 3 project and you need Composition API / Pinia standards — triggers "Vue 최적화", "Vue 컴포넌트 정리", "Pinia 상태관리", "Vue 반응성 깨짐", "Options API 마이그레이션", "vue best practices", "vue composition api", "pinia state management", "vue reactivity lost", or /vue-best-practices. Produces concrete code edits enforcing script setup, ref vs reactive vs shallowRef decisions, composable extraction, Pinia setup-store structure, typed defineProps/defineModel/defineEmits, provide/inject keys, and performance fixes (v-memo, shallowRef, defineAsyncComponent). Includes a reactivity-loss anti-pattern catalog and verification via vue-tsc + vite build. Different from vercel-react (React) and building-native-ui (RN/Expo). Assumes Vue 3 is already chosen — auto-detect via package.json "vue" field.
version: 2.0.0
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
  - Glob
compatibility: [claude-code]
---

# vue-best-practices

Apply Vue 3 Composition API + Pinia standards to an existing project: tighten reactivity, extract composables, structure stores, type component contracts, and fix common performance and reactivity-loss bugs. Targets Vue **3.5.x stable** (3.6 beta introduces Vapor Mode — flagged where relevant).

## When to use / boundaries

Use this skill when:
- A Vue 3 repo needs review/cleanup of components, stores, or reactivity.
- State is sprawling across props-drilling / event buses and needs Pinia.
- Reactivity "stopped working" after a destructure or a plain assignment.
- Migrating Options API components to `<script setup>`.

Do NOT use for:
- React projects -> use `vercel-react`.
- React Native / Expo -> use `building-native-ui`.
- Choosing between web/native/PWA -> use `app-platform-selector`.
- Vue 2 / Options-only legacy with no migration intent (different reactivity model).

Boundary check before touching anything:

```bash
# Confirm this is Vue 3 and read versions (Vue, Pinia, vue-tsc, vite)
node -e "const p=require('./package.json');const d={...p.dependencies,...p.devDependencies};console.log('vue',d.vue,'| pinia',d.pinia,'| vue-tsc',d['vue-tsc'],'| vite',d.vite)"
# Sanity: must print a 3.x vue. If 2.x, STOP and tell the user.
```

## Precheck — scan for the highest-value fixes first

Run these to locate the worst offenders before editing. Fix in priority order.

```bash
# 1) Reactivity loss: destructuring a reactive()/props (loses tracking)
rg -n "const \{[^}]+\} = (reactive|toRaw|defineProps)\(" src
# 2) Options API components still around (migration candidates)
rg -ln "export default \{" src --glob "*.vue" | xargs -r rg -l "data\(\)|methods:|computed:"
# 3) Untyped props (string-array form, no TS contract)
rg -n "defineProps\(\[" src
# 4) watch overuse where computed would do (watch that only re-assigns a ref)
rg -n "watch\(" src
# 5) Mutating store state from outside the store (anti-pattern)
rg -n "store\.[a-zA-Z0-9_]+ ?=" src
# 6) Heavy v-for lists without :key or with index keys
rg -n "v-for=" src
```

## Decision tables

### Reactive primitive: which one?

| Need | Use | Why |
|---|---|---|
| Single value (string/number/bool), object, array | `ref()` | Uniform `.value`, survives reassignment, destructure-safe via `toRefs` |
| Object you never reassign whole, want deep tracking | `reactive()` | No `.value`; but loses reactivity on destructure — avoid for return values |
| Large/immutable data (API payloads, big lists, charts) | `shallowRef()` | Tracks only `.value` reassignment, skips deep proxy — big memory/CPU win |
| Derived value | `computed()` | Cached, auto-deps; never a manually-synced `watch` |
| Non-reactive escape hatch (3rd-party instance) | `markRaw()` / plain | Stops Vue proxying class instances (maps, editors) |

Default to `ref()`. Reach for `reactive()` only for a local object you keep whole. Use `shallowRef()` for anything large.

### computed vs watch vs watchEffect

| Situation | Choose |
|---|---|
| Output is a pure function of reactive inputs | `computed()` |
| Need a side effect (fetch, localStorage, DOM) on change | `watch(src, cb)` |
| Side effect depending on several auto-collected deps | `watchEffect()` |
| React to a value but also need old value / lazy | `watch` (with `{ immediate, deep, flush }`) |

If a `watch` only ends with `someRef.value = ...`, it should be a `computed`.

### State location

| Scope | Put it in |
|---|---|
| One component | local `ref`/`reactive` |
| 2–3 nested components, no global meaning | `provide`/`inject` with typed `InjectionKey` |
| Cross-page / shared domain (auth, cart, settings) | Pinia store |
| Server cache (lists, entities) | Pinia store or a query lib; never duplicate in many components |

## Workflow

1. **Detect & read.** Run the boundary check + precheck. Read `package.json`, `tsconfig.json`, `vite.config.*`, and 2–3 representative `.vue` files to learn the project's conventions (alias `@`, naming, existing stores).
2. **Triage.** From precheck output, list issues by severity: reactivity-loss (P0, silent bugs) > untyped contracts (P1) > store mutation leaks (P1) > watch->computed (P2) > perf (P2).
3. **Fix reactivity loss first** (see anti-patterns). These are correctness bugs, not style.
4. **Type the contracts.** Convert array-form `defineProps` to the generic typed form; add `defineModel`/`defineEmits`.
5. **Extract composables** for any logic reused in ≥2 components or any `setup` over ~80 lines.
6. **Structure Pinia stores** as setup stores; move outside-mutations into actions.
7. **Apply perf fixes** only where the precheck flagged hot paths (big lists, frequently-re-rendered components).
8. **Verify** with `vue-tsc` + `vite build` (commands below). Iterate until clean.

## Code standards (before / after)

### 1. `<script setup>` + typed props/emits/model (Vue 3.4+)

Before — Options API, runtime-only types:

```vue
<script>
export default {
  props: ['title', 'count'],
  emits: ['update'],
  data() { return { open: false } },
  computed: { label() { return `${this.title} (${this.count})` } },
}
</script>
```

After — `<script setup lang="ts">`, compile-time types, `defineModel`:

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'

const props = withDefaults(
  defineProps<{ title: string; count?: number }>(),
  { count: 0 },
)
const emit = defineEmits<{ update: [value: number] }>()

// two-way binding without manual prop+emit plumbing (Vue 3.4+)
const open = defineModel<boolean>('open', { default: false })

const label = computed(() => `${props.title} (${props.count})`)
function bump() { emit('update', props.count + 1) }
</script>
```

### 2. Composable extraction (logic reuse + testability)

```ts
// composables/useCounter.ts
import { ref, computed, type Ref } from 'vue'

export function useCounter(initial = 0) {
  const count = ref(initial)
  const isZero = computed(() => count.value === 0)
  const increment = (by = 1) => { count.value += by }
  const reset = () => { count.value = initial }
  return { count, isZero, increment, reset } // refs survive destructure
}
```

```vue
<script setup lang="ts">
import { useCounter } from '@/composables/useCounter'
const { count, isZero, increment } = useCounter(10)
</script>
```

Rules: prefix `use`, return `ref`/`computed` (never a `reactive()` object — destructuring it breaks reactivity), keep side-effect cleanup inside (`onUnmounted`, `watch` stop handles).

### 3. Pinia — setup store (preferred over options store)

```ts
// stores/cart.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useCartStore = defineStore('cart', () => {
  // state  -> refs
  const items = ref<{ id: string; price: number; qty: number }[]>([])
  // getters -> computed
  const total = computed(() =>
    items.value.reduce((s, i) => s + i.price * i.qty, 0),
  )
  // actions -> functions (mutate state ONLY here)
  function add(item: { id: string; price: number }) {
    const found = items.value.find((i) => i.id === item.id)
    if (found) found.qty++
    else items.value.push({ ...item, qty: 1 })
  }
  function clear() { items.value = [] }

  return { items, total, add, clear }
})
```

Consume without losing reactivity — never destructure state directly:

```vue
<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useCartStore } from '@/stores/cart'

const cart = useCartStore()
const { items, total } = storeToRefs(cart)  // reactive refs
const { add, clear } = cart                  // actions: plain destructure OK
</script>
```

### 4. Typed provide/inject

```ts
// keys.ts
import type { InjectionKey, Ref } from 'vue'
export interface ThemeCtx { dark: Ref<boolean>; toggle: () => void }
export const ThemeKey: InjectionKey<ThemeCtx> = Symbol('theme')
```

```ts
// provider (parent setup)
import { provide, ref } from 'vue'; import { ThemeKey } from '@/keys'
const dark = ref(false)
provide(ThemeKey, { dark, toggle: () => (dark.value = !dark.value) })

// consumer (child setup)
import { inject } from 'vue'; import { ThemeKey } from '@/keys'
const theme = inject(ThemeKey)
if (!theme) throw new Error('ThemeKey provider missing')
```

### 5. Performance

```vue
<!-- v-memo: skip re-render of a row unless its key fields change -->
<div v-for="row in rows" :key="row.id" v-memo="[row.id, row.selected]">
  {{ row.label }}
</div>
```

```ts
// shallowRef for large/immutable payloads (no deep proxy walk)
import { shallowRef, triggerRef } from 'vue'
const dataset = shallowRef<Row[]>([])
async function load() {
  dataset.value = await fetchRows()   // reassign triggers update
}
// if you mutate in place, you must notify:
function patch(i: number, v: Row) { dataset.value[i] = v; triggerRef(dataset) }
```

```ts
// Route-level / heavy component code-splitting
import { defineAsyncComponent } from 'vue'
const HeavyChart = defineAsyncComponent(() => import('@/components/HeavyChart.vue'))
```

Template ref (Vue 3.5+) — prefer `useTemplateRef` over a same-named `ref`:

```vue
<script setup lang="ts">
import { useTemplateRef, onMounted } from 'vue'
const input = useTemplateRef<HTMLInputElement>('field')
onMounted(() => input.value?.focus())
</script>
<template><input ref="field" /></template>
```

## Anti-patterns (catalog)

| Anti-pattern | Why it breaks | Fix |
|---|---|---|
| `const { x } = reactive(obj)` | `x` is a detached plain value — no tracking | return `ref`s, or `toRefs(obj)` |
| `const { count } = defineProps(...)` (pre-3.5) | drops reactivity / loses default | keep `props.count`, or enable Reactive Props Destructure (3.5+) and don't alias |
| `let s = reactive([]); s = newArr` | reassigning a `reactive` ref loses reactivity | use `ref([])` and set `.value`, or `s.splice(0, s.length, ...newArr)` |
| `const { items } = storeToRefs ... then items = []` | reassigning a storeToRef ref | mutate via store action |
| `watch(a, () => b.value = a.value * 2)` | manual sync of derived state | `const b = computed(() => a.value * 2)` |
| Mutating store state in a component (`store.items.push`) | bypasses actions, untraceable | add an action and call it |
| `v-for` with `:key="index"` on a reorderable list | DOM reuse bugs on insert/remove | key by stable id |
| `reactive()` returned from a composable | consumer destructure kills reactivity | return individual `ref`/`computed` |
| Deep `reactive` on a 10k-row payload | proxies every nested node, slow | `shallowRef` + reassign |
| `defineProps` array form `['a','b']` | no types, no IDE help | generic `defineProps<{ a: string }>()` |

## Verification

Run after edits — all must pass. `vue-tsc` is the source of truth for the typed contracts above.

```bash
# Type-check templates + script (Vue SFC-aware tsc). Add the script if missing:
#   "type-check": "vue-tsc --noEmit -p tsconfig.app.json --composite false"
npx vue-tsc --noEmit

# Production build must succeed (catches compiler-macro misuse, async chunks)
npm run build      # or: npx vite build

# Lint if configured (oxlint/eslint-plugin-vue catches reactivity foot-guns)
npm run lint 2>/dev/null || echo "no lint script — consider eslint-plugin-vue"
```

Manual reactivity smoke test: mutate the source value (button, devtools) and confirm the dependent `computed`/DOM updates. If it does not, you have a reactivity-loss bug from the catalog above.

Report to the user: files changed, which anti-patterns were fixed (cite the table row), and the `vue-tsc` / `vite build` exit results.

## Notes

- Vue **3.6 (beta)** adds **Vapor Mode** (no virtual DOM for opted-in SFCs) and an "alien signals" reactivity rewrite. Do not enable in production yet (unstable as of June 2026); the standards above are forward-compatible.
- Reactive Props Destructure became stable in **3.5** — `const { count = 0 } = defineProps<...>()` is reactive there; on older 3.x keep `props.count`.
- If the project uses Nuxt, stores auto-import and `useState` may already cover SSR-safe state — check before adding Pinia.

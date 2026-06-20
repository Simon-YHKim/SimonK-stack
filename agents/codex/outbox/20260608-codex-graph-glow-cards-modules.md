# Codex Graph Glow Cards Modules

Branch: codex/graph-glow-cards-modules

Verify: npm run verify PASS

Summary:
- Added src/lib/graph/glow-style.ts with tier based signal-blue glow from cosmic.signalBlue and linear radius, opacity, and haloScale attenuation from tier 1 to tier 4.
- Added src/lib/graph/card-insights.ts for overview card signals: recent core, recent piece, and sparsest core with worldview tie order work, relation, knowledge, records, taste.
- Added unit tests for glow endpoint values, monotonic attenuation, determinism, recent node selection, title fallback, sparse core tie order, and invalid parent handling.

Scope:
- Did not touch src/components/graph/NavGraph.tsx.
- Did not touch src/app/index.tsx.

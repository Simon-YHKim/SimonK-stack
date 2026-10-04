---
name: semantic-recall
description: >-
  Use when the user wants meaning-based recall over approved markdown notes,
  SimonKWiki or memory; triggers include "의미검색", "시맨틱 검색", "뜻으로 찾아줘",
  "semantic search", "smart lookup" and /semantic-recall. Produces ranked source
  candidates from a local embedding index, then checks full source context.
  Prefer exact text, filenames and wiki links when sufficient; this is not an
  aggregate or whole-vault summary tool. Both building and querying execute an
  embedding model and require explicit scope, model permission and verified
  dependency/cache readiness. Under /vibe, inherit its budget and authority;
  do not install, download or invoke another provider to bypass restrictions.
version: 0.2.0
---

# semantic-recall — local meaning-based recall

Use embeddings only when exact text, filenames and wiki-link traversal are
insufficient. The index is a derived search aid, never the source of truth.
Open full source notes before answering; similarity scores are not factual
confidence. Aggregates and whole-file summaries need source-level evidence.
State the source conditions that change the answer, not just the chosen option.

## Authority and execution boundary

Under `/vibe`, remain a leaf of the same parent run, budget and approved scope.
Do not start a second coordinator or fall back to a provider or Bot to bypass
restrictions. Local computation is not proof of zero cost or permission.

Both `build` and `query` load an embedding model; `query` embeds the question
even when the index already exists. A model-execution prohibition blocks both.
A plan-only request permits conditional commands, not execution or unrequested
path checks. When blocking an embedding query, explicitly offer permitted
exact/text/source lookup if suitable; do not imply all reading is prohibited.

## Preflight before an authorized run

1. Resolve the absolute path of this skill's bundled
   [semantic_index.py](semantic_index.py). Never guess from the working directory.
2. Use only explicitly approved absolute input roots and output/index paths.
   Do not use the script's legacy default wiki, memory or index paths.
3. Before building, verify every approved root exists and is readable. Missing
   roots stop the workflow; the script itself merely warns and skips them, and
   initializes the model before scanning. Review links/junctions and descendants
   so traversal cannot expand scope; if containment is unverified, do not run.
4. Build into a new output directory outside the input roots. If it exists,
   stop and select a separately approved fresh path; preserve existing indexes.
   The script can overwrite files and does not write the index pair atomically.
5. For query, verify the approved index's scope and producing backend/model
   environment from independent records. The script stores chunk metadata but
   does not persist or check backend provenance. Do not infer compatibility.
6. Verify dependencies and model assets without importing an embedding backend
   during a no-model preflight. A cache directory alone is not readiness proof.
   Never silently install packages or download models. Where downloads are
   forbidden, require verified assets and a suitable no-network execution
   boundary; otherwise hold execution. `$0` is not download/model permission.

These are coordinator requirements, not new guards enforced by the script.
If a file read later fails, report partial coverage rather than complete indexing.

## Actual backend and cache behavior

The script requires NumPy and first attempts `fastembed.TextEmbedding` with
`sentence-transformers/all-MiniLM-L6-v2`. An `ImportError` in that attempt falls
back to `sentence_transformers.SentenceTransformer("all-MiniLM-L6-v2")`.
Other FastEmbed failures do not automatically select the fallback.
Import success alone does not prove model construction succeeded or that a
backend was used; report only an attempt until construction is observed.

`SEMANTIC_RECALL_CACHE` supplies the FastEmbed `cache_dir`; without it, that
backend uses `.model-cache` beside the script. It does not choose a backend and
is not passed to the SentenceTransformer constructor. Explicitly approve any
cache writes and resolve the selected backend's cache policy before execution.
There is no `--backend` or `--offline` CLI option and no enforced local-only
model-loading flag. Installed packages or a cache folder do not prove that
network access/downloads cannot occur. Do not treat a source comment as a guard.

## Conditional commands

Only after the above checks and execution authority are satisfied, prepare
PowerShell arguments with each spaced path preserved as one argument:

```powershell
# All variables must be resolved and approved; these are NOT dry-run commands.
# recallRoots is an array of absolute source-root strings.
& python -B $recallScript build --roots $recallRoots --out $recallNewIndex
& python -B $recallScript query $recallQuestion -k 8 --index $recallIndex
```

Use a positive `-k`. For a plan-only request, show the supplied absolute paths
in a conditional command and state which checks/permissions still block it.
Never execute a bare `build` or a query relying on the default index path.

## Output and reporting

Build writes `embeddings.npy` and `meta.json` in the selected output directory.
Query prints ranked score, source path/heading and snippet; open the approved
full source and cite that context, not the similarity score, in the answer.

Record actual input/output scope, observed chunk/file counts, missing roots,
read errors, backend/environment evidence and any unverified items. Do not
label a partial build as whole-vault coverage or infer zero documents from a
missing root. Preserve partial/existing indexes; resolving the missing scope
requires a separately authorized fresh build, not silent expansion or overwrite.
Keep model identity, costs and provenance unknown when not observed. A command
plan, static review or simulated response is not an executed embedding test.

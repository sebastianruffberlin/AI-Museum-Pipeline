# Architecture

## Five independent configuration axes

1. **Harness** – execution, batching, state, retry, validation, tracing.
2. **Workflow** – which modules run.
3. **Museum profile** – institution-specific semantics and source mapping.
4. **Model profile** – model identities and quality-relevant generation/reasoning settings.
5. **Hardware profile** – runtime parallelism/context-pool capacity for a deployment.

This separation prevents a museum-specific taxonomy from leaking into Python execution code and prevents hardware tuning (`np`) from being mistaken for a model/skill property.

## Core dependency graph

```text
image_embeddings ─┐
image_features ────┤
captions ──────────┼─ core results ─┬─ emotion (optional)
tagging ───────────┤                ├─ topics (optional)
text_embeddings ──┘                └─ future modules
```

Emotion and Topics are siblings. Both consume committed caption + tagging information but have no dependency on each other.

## Phase scheduler

`WorkflowRunner` expands enabled modules into atomic phases. Each phase runs across all candidate objects with worker count derived from the hardware profile. Model roles are resolved through `models/*.yaml`; the workflow never names a concrete model.

The GND authority phase is a special two-level concurrency case: outer object concurrency is 1 in the H100 reference profile because one object fans out multiple term-level LLM calls internally.

## Persistence boundary

The pipeline exposes a canonical museum result schema in PostgreSQL (`museum.enrichment_*`, emotion/topics tables, embeddings). Raw source columns are not known to the harness: `profiles/<museum>/metadata.yaml` maps them into canonical field IDs used by `ContextBuilder`.

Scratch/resume data is separate in `MUSEUM_RUN_SCHEMA`.

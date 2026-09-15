# Start here

The **AI Museum Pipeline** is self-hosted middleware for multimodal enrichment of
museum collections. It sits between an existing collection database and new
search, discovery or research applications.

It does not replace the museum's primary documentation system. Source data and
machine-generated enrichment remain separate.

## What it produces

- SigLIP2 and DINOv3 image embeddings;
- BGE-M3 text embeddings;
- consolidated image captions;
- generated, audited and repaired keywords;
- optional GND authority matching;
- optional controlled-vocabulary affective readings;
- optional institution-defined topic relations.

## If you work with collections or curatorial data

1. [`WORKFLOW.md`](WORKFLOW.md) — what happens to one object?
2. [`MUSEOLOGICAL_PRINCIPLES.md`](MUSEOLOGICAL_PRINCIPLES.md) — what are the interpretive boundaries?
3. [`PROFILES.md`](PROFILES.md) — what must another museum configure?
4. [`EMOTION_METHOD.md`](EMOTION_METHOD.md) — built-in Machine Heart default and custom vocabulary/DB contract.
5. [`TOPIC_KNOWLEDGE_BASE.md`](TOPIC_KNOWLEDGE_BASE.md) — how the tested institutional topic knowledge base is structured.
6. [`MUSEUM_DESIGN_DECISIONS.md`](MUSEUM_DESIGN_DECISIONS.md) — why the 11 keyword clusters, prompt/audit design, colour layers and Topics contract are structured this way.

## If you work with infrastructure

1. [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md)
2. [`INSTALLER.md`](INSTALLER.md)
3. [`MANUAL_DEPLOYMENT.md`](MANUAL_DEPLOYMENT.md)
4. [`../infra/cpu/INSTALL.md`](../infra/cpu/INSTALL.md)
5. [`../infra/gpu/INSTALL.md`](../infra/gpu/INSTALL.md)

The calibrated H100 deployment is documented under
`infra/gpu/stadtmuseum-berlin/h100-80gb/`. It is a reference deployment, not a
requirement for using the pipeline.

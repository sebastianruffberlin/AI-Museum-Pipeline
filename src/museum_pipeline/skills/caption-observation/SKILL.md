---
name: caption-observation
description: Produce an evidence-first visual observation of a museum object image.
metadata:
  runtime: deterministic-python-harness
  profile-overrides: true
---

# caption-observation

Produce an evidence-first visual observation of a museum object image.

## Runtime model

The workflow selects this skill deterministically. The model does not load this file or inspect the repository. The Python harness assembles the active museum profile, task inputs, schema and model profile into the request.

## Inputs
- image
- active museum prompt context

## Output
- free-text visual observation

## Invariants
- Describe visible evidence before interpretation.
- Do not invent object history or identity.
- Keep institution-specific wording in the museum profile.

## Configuration boundary

Institution-specific taxonomies, vocabularies, audience assumptions, policies and prompt wording belong in `profiles/<museum>/`. Model/generation settings belong in `models/`; hardware parallelism belongs in `hardware/`.

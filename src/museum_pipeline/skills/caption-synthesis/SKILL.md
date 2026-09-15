---
name: caption-synthesis
description: Synthesize two independent visual observations into a consolidated caption.
metadata:
  runtime: deterministic-python-harness
  profile-overrides: true
---

# caption-synthesis

Synthesize two independent visual observations into a consolidated caption.

## Runtime model

The workflow selects this skill deterministically. The model does not load this file or inspect the repository. The Python harness assembles the active museum profile, task inputs, schema and model profile into the request.

## Inputs
- image
- observation A
- observation B
- active museum synthesis prompt

## Output
- consolidated visual caption

## Invariants
- Resolve disagreements conservatively.
- Prefer jointly supported observations.
- Do not add facts absent from image or observations.

## Configuration boundary

Institution-specific taxonomies, vocabularies, audience assumptions, policies and prompt wording belong in `profiles/<museum>/`. Model/generation settings belong in `models/`; hardware parallelism belongs in `hardware/`.

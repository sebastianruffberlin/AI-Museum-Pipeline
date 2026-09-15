---
name: keyword-generation
description: Generate structured retrieval-oriented museum object keywords from image, caption and metadata.
metadata:
  runtime: deterministic-python-harness
  profile-overrides: true
---

# keyword-generation

Generate structured retrieval-oriented museum object keywords from image, caption and metadata.

## Runtime model

The workflow selects this skill deterministically. The model does not load this file or inspect the repository. The Python harness assembles the active museum profile, task inputs, schema and model profile into the request.

## Inputs
- image
- caption
- museum-object metadata context
- profile-defined tagging taxonomy and policy

## Output
- structured keyword proposal

## Invariants
- Use only profile-defined clusters.
- Ground terms in supplied evidence.
- Do not silently change museum policy.

## Configuration boundary

Institution-specific taxonomies, vocabularies, audience assumptions, policies and prompt wording belong in `profiles/<museum>/`. Model/generation settings belong in `models/`; hardware parallelism belongs in `hardware/`.

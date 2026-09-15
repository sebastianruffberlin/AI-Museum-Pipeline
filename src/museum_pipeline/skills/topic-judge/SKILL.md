---
name: topic-judge
description: Audit thematic assignments against the configured framework and evidence.
metadata:
  runtime: deterministic-python-harness
  profile-overrides: true
---

# topic-judge

Audit thematic assignments against the configured framework and evidence.

## Runtime model

The workflow selects this skill deterministically. The model does not load this file or inspect the repository. The Python harness assembles the active museum profile, task inputs, schema and model profile into the request.

## Inputs
- image
- caption
- metadata context
- thematic framework/taxonomy
- generator assignments
- profile review policy

## Output
- structured thematic audit

## Invariants
- Validate assignments against evidence and framework.
- Apply profile-defined sensitivity/review rules.
- Do not assume any particular museum topics.

## Configuration boundary

Institution-specific taxonomies, vocabularies, audience assumptions, policies and prompt wording belong in `profiles/<museum>/`. Model/generation settings belong in `models/`; hardware parallelism belongs in `hardware/`.

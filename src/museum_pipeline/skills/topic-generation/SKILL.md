---
name: topic-generation
description: Classify objects against an institution-defined thematic framework and taxonomy.
metadata:
  runtime: deterministic-python-harness
  profile-overrides: true
---

# topic-generation

Classify objects against an institution-defined thematic framework and taxonomy.

## Runtime model

The workflow selects this skill deterministically. The model does not load this file or inspect the repository. The Python harness assembles the active museum profile, task inputs, schema and model profile into the request.

## Inputs
- image
- caption
- metadata context
- profile-defined thematic framework
- profile-defined taxonomy

## Output
- structured thematic assignments

## Invariants
- Evaluate all supplied topics without assuming a fixed count.
- Use only supplied topic/subtopic/vocabulary identifiers.
- Treat uncertainty explicitly.

## Configuration boundary

Institution-specific taxonomies, vocabularies, audience assumptions, policies and prompt wording belong in `profiles/<museum>/`. Model/generation settings belong in `models/`; hardware parallelism belongs in `hardware/`.

---
name: emotion-generation
description: Generate evidence-backed affective or atmospheric readings using the configured method and vocabulary.
metadata:
  runtime: deterministic-python-harness
  profile-overrides: true
---

# emotion-generation

Generate evidence-backed affective or atmospheric readings using the configured method and vocabulary.

## Runtime model

The workflow selects this skill deterministically. The model does not load this file or inspect the repository. The Python harness assembles the active museum profile, task inputs, schema and model profile into the request.

## Inputs
- image
- caption
- metadata context
- profile-provided affective vocabulary/method context

## Output
- structured affective readings

## Invariants
- Treat readings as possible effects/atmospheres, not diagnoses.
- Every mapped reading requires evidence.
- Vocabulary and method-specific semantics come from the active profile.

## Configuration boundary

Institution-specific taxonomies, vocabularies, audience assumptions, policies and prompt wording belong in `profiles/<museum>/`. Model/generation settings belong in `models/`; hardware parallelism belongs in `hardware/`.

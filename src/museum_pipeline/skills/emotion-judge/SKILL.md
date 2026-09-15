---
name: emotion-judge
description: Validate, remap, flag or reject generated affective readings.
metadata:
  runtime: deterministic-python-harness
  profile-overrides: true
---

# emotion-judge

Validate, remap, flag or reject generated affective readings.

## Runtime model

The workflow selects this skill deterministically. The model does not load this file or inspect the repository. The Python harness assembles the active museum profile, task inputs, schema and model profile into the request.

## Inputs
- image
- caption
- metadata context
- profile vocabulary
- generator readings

## Output
- structured judge decisions

## Invariants
- Check evidence and concept distinctions.
- Remap only to supplied concepts.
- Reject unsupported or overreaching readings.

## Configuration boundary

Institution-specific taxonomies, vocabularies, audience assumptions, policies and prompt wording belong in `profiles/<museum>/`. Model/generation settings belong in `models/`; hardware parallelism belongs in `hardware/`.

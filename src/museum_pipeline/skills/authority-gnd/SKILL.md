---
name: authority-gnd
description: Resolve accepted keywords against a configured GND authority index using retrieve-then-judge.
metadata:
  runtime: deterministic-python-harness
  profile-overrides: true
---

# authority-gnd

Resolve accepted keywords against a configured GND authority index using retrieve-then-judge.

## Runtime model

The workflow selects this skill deterministically. The model does not load this file or inspect the repository. The Python harness assembles the active museum profile, task inputs, schema and model profile into the request.

## Inputs
- accepted keyword
- retrieved GND candidates
- caption
- metadata context

## Output
- authority decision with GND identifier or no-match

## Invariants
- Never invent authority identifiers.
- Choose only from retrieved candidates.
- Allow no-match when evidence is insufficient.

## Configuration boundary

Institution-specific taxonomies, vocabularies, audience assumptions, policies and prompt wording belong in `profiles/<museum>/`. Model/generation settings belong in `models/`; hardware parallelism belongs in `hardware/`.

---
name: keyword-audit
description: Audit generated keywords for evidence, syntax, cluster placement and configured policy.
metadata:
  runtime: deterministic-python-harness
  profile-overrides: true
---

# keyword-audit

Audit generated keywords for evidence, syntax, cluster placement and configured policy.

## Runtime model

The workflow selects this skill deterministically. The model does not load this file or inspect the repository. The Python harness assembles the active museum profile, task inputs, schema and model profile into the request.

## Inputs
- image
- caption
- metadata context
- keyword proposal
- profile-defined audit policy

## Output
- structured audit result

## Invariants
- Judge each proposed term against evidence and policy.
- Use profile-defined error classes.
- Do not create institution-specific policy in the generic skill.

## Configuration boundary

Institution-specific taxonomies, vocabularies, audience assumptions, policies and prompt wording belong in `profiles/<museum>/`. Model/generation settings belong in `models/`; hardware parallelism belongs in `hardware/`.

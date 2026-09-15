---
name: keyword-repair
description: Repair policy-defined recoverable keyword errors without adding unsupported facts.
metadata:
  runtime: deterministic-python-harness
  profile-overrides: true
---

# keyword-repair

Repair policy-defined recoverable keyword errors without adding unsupported facts.

## Runtime model

The workflow selects this skill deterministically. The model does not load this file or inspect the repository. The Python harness assembles the active museum profile, task inputs, schema and model profile into the request.

## Inputs
- caption
- metadata context
- recoverable rejected terms
- profile-defined repair policy

## Output
- structured repair decisions

## Invariants
- Repair only requested terms.
- Preserve evidence constraints.
- Return unrecoverable items as unrepaired rather than hallucinating replacements.

## Configuration boundary

Institution-specific taxonomies, vocabularies, audience assumptions, policies and prompt wording belong in `profiles/<museum>/`. Model/generation settings belong in `models/`; hardware parallelism belongs in `hardware/`.

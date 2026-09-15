# Stadtmuseum Berlin public reference profile

This profile demonstrates a real museum configuration while keeping the
museums-agnostic Python core unchanged.

Public customization points:

- `metadata.yaml` — source-field mapping and context selection;
- `prompts/` — caption, tagging and affect prompts;
- `tagging/` — cluster taxonomy, audit/repair policy and terminology mapping;
- `emotion/` — optional controlled-vocabulary affective-reading module;
- `authority/profile.yaml` — GND policy/provider.

## Public-release boundary

The internal strategic Topics knowledge base used during production testing is
not included in the public repository. This reference profile intentionally ships
**no institution-specific Topics framework or taxonomy**. The reusable Topics
engine, generic prompts and construction blueprint live under
`profiles/_template/topics/` and `docs/TOPIC_KNOWLEDGE_BASE.md`.

The Machine Heart emotion resources in this public profile are file-backed and
fully published as a reusable default method. No institution-specific profile SQL
bootstrap is required for Emotion.

## Terminology policy

The files under `tagging/` demonstrate an institution-specific audit, repair and
terminology/debias policy. They are **not a universal terminology standard** and
should be reviewed by each institution against its own collections, communities,
editorial policy and current language guidance before reuse.

## Topics intentionally omitted

The institution-specific thematic priorities and their underlying knowledge
base are not part of the public reference profile. The generic Topics engine and
construction blueprint remain available under `profiles/_template/topics/` and
`docs/TOPIC_KNOWLEDGE_BASE.md`.

# Affective readings: Machine Heart default and custom emotion systems

The Emotion module is optional, but unlike institution-specific Topics the
repository ships a **complete museums-agnostic default method**: **Machine Heart**.

A museum therefore has three choices:

1. **off** — use a workflow without Emotion (`core` or `core-topics`);
2. **Machine Heart default** — use the supplied method and controlled vocabulary;
3. **custom emotion system** — keep the pipeline interface but replace the
   vocabulary and, if required, the prompts/method configuration.

## What the default contains

`profiles/_template/emotion/` contains the complete published editorial resource:

- `concepts.json` — **146 curated concepts** with roles, reading modes, semantic
  domains, evidence/context requirements, exclusions, theoretical/editorial
  provenance and PAD metadata;
- `vocabulary.runtime.json` — the **121 `resonance_reading` concepts** actually
  exposed to Generator/Judge by the production query;
- `profile.yaml` — Machine Heart method configuration.

The difference 146 → 121 is intentional, not a reduced public edition. The
production runtime query selected only concepts with `concept_role =
resonance_reading` and excluded deprecated concepts. Other concepts remain part
of the editorial knowledge model.

The generic Machine Heart Generator/Judge prompts are included in the starter
profile. `core-emotion` enables the step.

## Runtime vocabulary contract

The Emotion module ultimately needs a JSON array of concepts. Each runtime
concept must have stable semantics. The minimal practical fields are:

```json
{
  "concept_id": "stable_machine_id",
  "begriff": "Human-readable label",
  "definition": "What this reading means",
  "nicht_verwenden_wenn": ["Explicit false-positive rule"]
}
```

Requirements:

- `concept_id` must be unique and stable across runs;
- `begriff` must be suitable for the configured output language;
- `definition` must distinguish the concept from nearby readings;
- `nicht_verwenden_wenn` is technically optional but strongly recommended;
- the resulting active vocabulary must not be empty;
- `vocabulary_version` in `emotion/profile.yaml` should change whenever semantics
  or concept membership change.

## File-backed custom vocabulary

The easiest customisation is:

```yaml
resources:
  source: file
  file_fallback: vocabulary.runtime.json
```

Replace the runtime JSON and increment `vocabulary_version`. If only the
controlled terms change, the supplied Machine Heart prompts can remain in use.

## Database-backed custom vocabulary

A museum may keep its own emotion vocabulary in PostgreSQL or another source
reachable through a PostgreSQL query. The pipeline does **not** require a
particular internal table schema. The configured SQL query is the adapter.

Use:

```yaml
resources:
  source: database
  vocabulary_query: vocabulary.sql
  file_fallback: vocabulary.runtime.json
```

The query contract is strict but small:

- return exactly one logical row;
- expose a column named `value`;
- `value` contains the complete runtime vocabulary as a JSON array or JSON text;
- every concept follows the runtime vocabulary contract above;
- the result must be deterministic for a given vocabulary version.

`profiles/_template/emotion/vocabulary-query.example.sql` shows the adapter
pattern. Your internal authoring database may contain many more fields.

## Recommended authoring model for a new emotion system

Machine Heart's 146-concept editorial model is not mandatory, but a serious replacement should
be able to record at least:

- stable concept ID + preferred label + alternative labels;
- definition;
- conceptual role / reading type;
- context or evidence requirement;
- distinctions from nearby concepts;
- `do_not_use_when` / false-positive rules;
- cultural or scope notes where relevant;
- provenance / theoretical or editorial basis;
- editorial status and versioning.

The more interpretive the vocabulary, the more important explicit exclusions and
provenance become.

## Replacing the method, not just the vocabulary

If a museum's approach is conceptually different from Machine Heart, copy the
Emotion prompt/config files into its profile and change them together. The
Python module only requires the configured Generator/Judge to respect the
published JSON schemas and the runtime vocabulary interface.

A custom system should therefore be treated as a **new method implementation**,
not merely as a renamed Machine Heart vocabulary.

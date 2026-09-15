# Building an institution-specific thematic knowledge base

The Topics module is a **generic engine**. The public repository deliberately
ships **no institutional thematic priorities and no underlying strategy
document**. Those contents belong to the museum using the pipeline.

The engine expects two institution-owned resources: a prose framework and a
controlled taxonomy. It then runs an independent **generator → judge** process
against every configured topic.

## What was tested

The method was developed and tested with a real institutional knowledge base
that used multiple strategic topics. The private source document and the topic
contents are not published. What *is* published here is the structural contract
that proved useful. In the tested implementation the taxonomy happened to have
**8 topics, 64 subtopics and 104 controlled terms**. Those numbers are examples
of a workable scale, **not requirements**.

For each topic, the tested knowledge base contained:

1. **research interest / scope** — what the topic is intended to reveal about objects;
2. **includes** — recurring facets and relevant types of relation;
3. **excludes / not sufficient** — typical false positives;
4. **evidence rules** — what an individual object must actually document;
5. optional **retrieval anchors** — places, events, people, organisations or terms
   that help discovery but never prove a relation by themselves;
6. **sensitivity / review rules** — cases requiring stricter evidence or review.

The taxonomy then provided stable IDs for subtopics and controlled terms plus
`use_when` / `do_not_use_when` guidance.

## Required files

Create inside `profiles/<museum>/topics/`:

```text
profile.yaml
framework.md
taxonomy.json
```

Start from `profiles/_template/topics/`. The starter profile does not activate
Topics automatically. After the contents exist, add:

```yaml
topics:
  config: topics/profile.yaml
```

to `profiles/<museum>/profile.yaml`.

## `framework.md`

Write one section per institutional topic. At minimum describe:

```text
TOPIC
  research interest / scope
  includes
  not sufficient / exclusions
  evidence rule
  optional retrieval anchors
  sensitivity / review rules
```

The central rule is: **framework knowledge is context, not evidence about an
individual object**. A date, place, person or keyword mentioned in the framework
may help the model understand the topic, but it cannot prove that an object
belongs to it.

## `taxonomy.json`

The loader accepts a list of topic objects. A robust topic definition contains:

```json
[
  {
    "slug": "TOPIC_SLUG",
    "label": "TOPIC_LABEL",
    "subtopics": [
      {
        "id": "TOPIC_01",
        "label": "SUBTOPIC_LABEL",
        "definition": "Institution-owned definition",
        "positive_indicators": [],
        "not_sufficient": [],
        "active": true,
        "version": "1.0"
      }
    ],
    "vocabulary": [
      {
        "id": "TOPIC_SW_01",
        "label": "CONTROLLED_TERM",
        "subtopics": ["TOPIC_01"],
        "use_when": "Object-specific evidence rule",
        "do_not_use_when": "False-positive rule",
        "origin": "institutional",
        "active": true,
        "version": "1.0"
      }
    ]
  }
]
```

Stable IDs matter more than the exact field count. The generator and judge
should be able to distinguish **what the topic means**, **what counts as object
evidence**, and **which controlled terms are allowed**.

## Generator and judge

The supplied generic Topic prompts implement two roles:

1. **Generator** — checks the object against all configured topics and proposes
   only object-specific relations with evidence, subtopics and controlled terms.
2. **Judge** — re-evaluates all configured topics independently and can confirm,
   correct, downgrade, remove or add a relation.

The method deliberately separates the institution's knowledge from the model
logic. A museum can therefore replace its framework/taxonomy without modifying
`src/`.

## Database-backed knowledge is also possible

`TopicsModule` also supports `resources.source: database`. In that case the
configured query must return a row containing:

- `framework` — the prose knowledge base as text;
- `taxonomy` (or `taxonomie`) — the taxonomy as JSON or a JSON string.

The internal database schema is institution-defined; only this adapter contract
is required by the pipeline.


## Legacy database migration names

Fresh installations use the generic `museum.topic_assignments` and
`museum.topic_runs` schemas. `database/migrations/002_topics_generic.sql` also
mentions historical German table names such as `schwerpunkt_bezug` solely so
existing installations can be migrated. Those identifiers contain no thematic
knowledge and are **not** part of the Topics construction contract.

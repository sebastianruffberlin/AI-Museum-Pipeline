# Institution-defined Topics — configuration blueprint

This directory is deliberately **not active** in the starter profile.

The public repository provides the Topics engine (generator + independent judge),
but it does not publish any institution's thematic priorities or their underlying
strategy/knowledge documents. Before enabling `core-topics` or `full`, create:

- `framework.md` — the institution's thematic knowledge base;
- `taxonomy.json` — stable topic IDs, subtopics and controlled terms;
- `profile.yaml` — resource and prompt wiring.

Start from the `.template` / `.example` files in this directory and follow
`docs/TOPIC_KNOWLEDGE_BASE.md`. Then add to the museum's `profile.yaml`:

```yaml
topics:
  config: topics/profile.yaml
```

There are intentionally no real topic names or strategic contents in this
public template.

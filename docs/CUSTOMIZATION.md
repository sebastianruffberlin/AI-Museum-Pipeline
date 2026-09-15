# Customizing the pipeline for another museum

Start with the museums-agnostic starter profile:

```bash
museum-pipeline init-profile my-museum
```

Normal customization should not require edits under `src/`.

## 1. Metadata

Edit `profiles/<museum>/metadata.yaml` to define the source table/object, ID,
asset reference, canonical field mapping and which fields each module may see.

## 2. Core tagging

Configure cluster names in `tagging/profile.yaml`, deterministic audit/repair
rules in `tagging/policy.yaml`, terminology/debias rules in
`tagging/debias_map.json`, and institution-specific prompt wording under
`prompts/`.

## 3. Emotion / affective readings

Optional. The starter ships the complete museums-agnostic Machine Heart default,
which separates possible *effects/readings* from claims about a depicted person's
mental state. Use it unchanged, connect a custom vocabulary file/database, or
replace the method. Use a workflow without `emotion` when the museum does not
want this module. See [`EMOTION_METHOD.md`](EMOTION_METHOD.md).

## 4. Institution-defined topics

Optional. Provide `topics/framework.md` and `topics/taxonomy.json`. See
[`TOPIC_KNOWLEDGE_BASE.md`](TOPIC_KNOWLEDGE_BASE.md) for the production-tested
knowledge structure and the content contract. No institutional topics are published.

## 5. Authority data

The reference integration uses GND. Set `authority/profile.yaml: enabled: false`
when authority enrichment is not needed.

## 6. Models and hardware

Keep these outside the Museum Profile. Model-role mapping belongs in `models/`;
hardware concurrency and context capacity belong in `hardware/`.


## Public semantic defaults

The public starter ships Machine Heart as the default optional Emotion method;
see `EMOTION_METHOD.md` for file/database contracts and how to replace it.

Topics are different: the repository ships the engine and templates only. No
institutional topic contents are bundled. A museum must create its own framework
and taxonomy before enabling Topics; see `TOPIC_KNOWLEDGE_BASE.md`.

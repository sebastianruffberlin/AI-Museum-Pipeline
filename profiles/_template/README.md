# Generic German museum starter profile

This directory is a runnable starter profile for a German museum using the
museum enrichment pipeline.

Copy the complete directory and rename it:

    cp -a profiles/_template profiles/my-museum

Then configure:

    MUSEUM_PROFILE=my-museum

Institution-specific metadata, terminology, prompts and rules belong in the
museum profile. Reusing the pipeline must not require changes to Python core
code.

## Source data

The example expects a PostgreSQL source table:

    source.objects

with at least:

    object_id
    image_url

Additional example columns are:

    object_type
    title
    dating
    materials
    techniques
    description

Adapt `metadata.yaml` to the institution's actual column names.

The stable identifier may have any database column name. Configure it through
`source.id_column`.

A collection/grouping column is optional.

## Image assets

The starter uses a direct HTTP(S) image URL:

    source:
      asset:
        mode: url
        column: image_url

For S3-compatible object storage:

    source:
      asset:
        mode: s3
        column: image_reference
        key:
          marker: /objects/
          prefix: objects/

Current supported asset modes are:

- `url`
- `s3`

The runtime normalizes both to a canonical `asset_ref`.

IIIF is not implemented as an asset provider yet, but can later be added
behind the same provider boundary.

## Tagging

The starter includes the reference tagging architecture and genericized core
prompts.

Museums should review vocabulary, cluster definitions, language, policy rules
and prompts before production use.

## GND

GND is the supported reference authority for the German museum context.

It is included but disabled by default:

    enabled: false

To enable it, configure the GND/OpenSearch service and set:

    enabled: true

The core pipeline also runs without authority enrichment.

## Optional modules

Emotion and Topics are intentionally absent from this minimal profile because
their vocabularies, taxonomies and curatorial frameworks are museum-specific.

The `core` workflow does not require them.

## Optional semantic modules

### Emotion

The starter already includes the museums-agnostic Machine Heart default under
`emotion/` and its Generator/Judge prompts. It remains inactive in `core`; use
`core-emotion` when you want it. See `docs/EMOTION_METHOD.md`.

### Topics

The starter deliberately includes only a construction blueprint under `topics/`.
No institutional topic content is bundled. Create `framework.md`, `taxonomy.json`
and `profile.yaml`, then add the `topics:` config block to this profile before
enabling `core-topics` or `full`. See `docs/TOPIC_KNOWLEDGE_BASE.md`.

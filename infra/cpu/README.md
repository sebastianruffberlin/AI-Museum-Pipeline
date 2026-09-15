# CPU deployment

Canonical CPU-side deployment for the AI Museum Pipeline.

The compose stack intentionally contains only pipeline infrastructure.

## Base services

- PostgreSQL
- embedding service

## Optional profiles

### S3

Starts the presign adapter:

    docker compose -f infra/cpu/compose.yml --profile s3 up -d

Use this only when the museum profile uses:

    source.asset.mode: s3

Direct URL assets do not need the presign service.

### GND

Starts OpenSearch:

    docker compose -f infra/cpu/compose.yml --profile gnd up -d

Use this only when GND authority enrichment is enabled in the museum
profile.

Profiles may be combined:

    docker compose -f infra/cpu/compose.yml \
      --profile s3 \
      --profile gnd \
      up -d

## Deliberately outside this stack

The CPU deployment does not provision:

- DNS
- SSH access
- reverse proxies
- firewalls
- GPU hosts
- llama.cpp / llama-swap / LiteLLM
- museum source tables
- museum source data

The GPU side is an external OpenAI-compatible inference endpoint.

Database schemas are applied by the Museum Pipeline bootstrap process,
not by PostgreSQL's one-time docker-entrypoint initialization. This keeps
installation and upgrades idempotent and allows optional database modules
to follow the configured workflow.


<!-- CPU-INSTALL-LINK -->
## Manual installation

See [`INSTALL.md`](INSTALL.md) for a fresh-host installation runbook.

# Installer

The installer automates the already documented manual deployment.

It does not invent a new architecture and it does not provision cloud
accounts, DNS zones or museum source data.

The manual deployment documentation remains the reference contract.

## What the museum prepares

### Infrastructure

CPU/orchestrator host:

- Linux;
- SSH/admin access;
- Docker Engine;
- Docker Compose Plugin;
- Git;
- Python 3.11+;
- enough RAM/storage for PostgreSQL and embedding models.

Managed GPU host:

- Linux;
- SSH/admin access;
- Docker Engine;
- Docker Compose Plugin;
- working NVIDIA driver (`nvidia-smi`);
- NVIDIA Container Runtime;
- sufficient VRAM/storage for the selected calibrated deployment;
- ports 80/443 reachable from the Internet for Caddy/TLS.

Additionally:

- DNS for the GPU domain already points to the GPU host;
- S3/Object Storage exists when private S3 assets are used;
- museum source data already exists and is reachable.

The installer deliberately does not order servers, create DNS records or
create the museum's primary collection database.

## What the museum configures fachlich

Create a profile:

    museum-pipeline init-profile mein-museum

Then edit:

    profiles/mein-museum/

The important areas are:

### `metadata.yaml`

Required.

Defines:

- source table / source object;
- object identifier;
- metadata field mapping;
- asset reference;
- which metadata fields are exposed to which pipeline contexts.

### `prompts/`

Working template prompts are supplied.

A museum only needs to change them when its terminology, audience,
cataloguing policy or interpretive rules differ.

### `tagging/`

Configure when tagging is used:

- controlled clusters;
- audit/repair policy;
- terminology/debias rules.

### `authority/`

Choose whether authority enrichment such as GND is enabled and configure
its policy.

### `emotion/`

Optional at runtime, but the starter profile already contains the complete
museums-agnostic **Machine Heart** default. A museum can enable it unchanged,
replace only its runtime vocabulary, connect a museum-specific vocabulary DB, or
replace the method/prompt configuration. See `EMOTION_METHOD.md`.

### `topics/`

Optional and institution-owned. The starter contains only templates; no real
topic names or knowledge-base contents are bundled. Create the framework and
taxonomy before enabling a Topics workflow. See `TOPIC_KNOWLEDGE_BASE.md`.

Normal museum customization should not require editing
`src/museum_pipeline/`.

## What goes into `deployment.yaml`

`deployment.yaml` contains non-secret deployment decisions:

    museum_profile: mein-museum
    model_profile: reference
    hardware_profile: h100-80gb
    workflow: core

    features:
      s3: true
      gnd: true

    gpu:
      mode: managed
      host: 203.0.113.20
      ssh_user: root
      domain: gpu.meinmuseum.de

This file may be version controlled by the museum if desired.

## What goes into `.env`

Only secrets or externally assigned credentials.

Typical fresh managed deployment:

    HF_TOKEN=...

    S3_ENDPOINT=...
    S3_BUCKET=...
    S3_ACCESS_KEY=...
    S3_SECRET_KEY=...

Internal secrets are generated on first installation and persisted under:

    .museum-pipeline/generated.env

This includes:

- PostgreSQL password;
- LiteLLM master key;
- llama-swap API key.

For an already existing external GPU endpoint instead use:

    LCPP_URL=https://...
    LCPP_AUTH=Bearer ...

## Install

Prepare:

    cp deployment.example.yaml deployment.yaml
    cp installer.env.example .env
    chmod 600 .env

Create/configure the museum profile.

Then:

    museum-pipeline install

The intended execution order is:

    preflight
      -> managed GPU deployment or external endpoint validation
      -> CPU compose stack
      -> generic database schemas
      -> profile-specific database resources
      -> optional GND import
      -> validate-config
      -> doctor

## Dry-run

Before changing infrastructure:

    museum-pipeline install --dry-run

For an existing GPU where models are already present:

    museum-pipeline install --skip-model-download

## Doctor

At any time:

    museum-pipeline doctor

The doctor checks the current installation contract rather than silently
repairing it.

## Idempotence

The installer is designed to be rerunnable.

It uses:

- Docker Compose desired state;
- `CREATE ... IF NOT EXISTS` / idempotent SQL where supplied;
- persistent Docker volumes;
- persistent generated secrets;
- deterministic profile/model/hardware/workflow selection.

A rerun does not intentionally generate new credentials or replace museum
profiles.

## Scope

The first installer assumes OS-level prerequisites are already available.

This is intentional: Linux distribution provisioning, NVIDIA driver
installation and provider-specific cloud APIs are separate concerns and
must not be hidden inside the museum application installer.

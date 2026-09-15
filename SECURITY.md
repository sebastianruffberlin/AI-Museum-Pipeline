# Security policy

## Reporting a vulnerability

Please do **not** open a public issue containing credentials, private museum
data, infrastructure details or an exploitable vulnerability.

Use GitHub private vulnerability reporting when it is enabled for the public
repository. If that channel is unavailable, contact the maintainers through the
official Stadtmuseum Berlin contact channel and ask for a private security
contact.

When reporting, include:

- affected commit or release;
- affected component;
- reproducible steps;
- expected impact;
- whether any credential or personal/institutional data may have been exposed.

## Secrets

Real secrets must never be committed. Runtime credentials belong in `.env` or
installer-generated files under `.museum-pipeline/` / the external GPU config
directory. Example files contain placeholders only.

If a secret is ever committed, removing the current file is not sufficient:
rotate the credential and treat the Git history as compromised.

## Supported release

Security fixes target the current public release line. The reference deployment
uses pinned/recorded component versions for reproducibility, but users remain
responsible for security updates in their own operating system, container and
model-serving environment.
## Museum data, tracing and verbose logs

Object metadata, prompts and model outputs can contain unpublished collection
information, personal data or other institution-sensitive material.

- Phoenix/OpenTelemetry tracing is **disabled by default**. When enabled, LLM
  spans record truncated prompt/output text plus object identifiers and phase
  metadata. Treat the tracing backend as a system that may receive museum data.
- `-v` and `-vv` deliberately expose full user prompts/model responses or
  intermediate structures in the console. Do not use verbose logging in a
  shared terminal, CI log or central log collector unless that data destination
  is approved for the collection data being processed.
- Do not use production object data in public bug reports or reproducibility
  examples; prefer synthetic fixtures such as `DEMO-001`.

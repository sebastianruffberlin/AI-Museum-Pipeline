# Verifizierter CPU-/Orchestrator-Referenzstand

Stand: 13. September 2026.

Dieser Referenzstand beschreibt ausschließlich:

- Python-Orchestrierung,
- PostgreSQL,
- Embedding-Service,
- optional Presign,
- optional OpenSearch/GND.

Lokale LLM-Inferenz gehört nicht zum Referenzstack.


## Verifizierte Basis

- Ubuntu 24.04
- 16 vCPU
- AMD EPYC 9645
- ca. 62 GiB RAM


## PostgreSQL

Verifiziert:

    PostgreSQL 16.15
    Image-Tag: postgres:16
    Digest: postgres@sha256:f1c3376c26f2609ab9f29f71f824103fe2fcd8ee0346485cb6122a4f93df6f94


## OpenSearch

Verifiziert:

    OpenSearch 3.8.0
    Image-Tag: opensearchproject/opensearch:3.8.0
    Digest: opensearchproject/opensearch@sha256:bcc1797519726ceb6d651d4a3e60b7c30da91793914a8dfe75fd441d4f641509


## Embedding-Modelle

Verifizierte IDs:

    google/siglip2-giant-opt-patch16-384
    facebook/dinov3-vitl16-pretrain-lvd1689m
    BAAI/bge-m3

Beobachtete Revisionen am 13.09.2026:

    SigLIP2:
    a713301b217d38485fb2204c808367d10bc3cc40

    DINOv3:
    ea8dc2863c51be0a264bab82070e3e8836b02d51

    BGE-M3:
    5617a9f61b028005a4858fdac845db406aefb181

Neue Installationen dürfen neuere `main`-Revisionen beziehen.

Diese IDs dienen als Referenzprovenienz.


## Python-Abhängigkeiten

Die tatsächlich installierten Pakete des verifizierten
Embedding- und Presign-Containers sind gespeichert unter:

    infra/cpu/reference/embedding-pip-freeze.txt
    infra/cpu/reference/presign-pip-freeze.txt


## GND

Die GND ist eine Rolling Resource.

Persistente Quelle:

    https://data.dnb.de/opendata/authorities-gnd-sachbegriff_lds.jsonld.gz

Persistenter Dateiname:

    authorities-gnd-sachbegriff_lds.jsonld.gz

Der Datensatzstand darf sich verändern.

Ein historischer Datensatzcount ist deshalb kein Installationskriterium.

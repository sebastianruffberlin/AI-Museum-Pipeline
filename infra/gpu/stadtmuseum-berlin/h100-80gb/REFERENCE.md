# Verifizierter H100-Referenzstand

Stand: 13. September 2026.

Hardware:

    NVIDIA H100 PCIe
    81559 MiB VRAM
    NVIDIA Driver 580.173.02

Runtime:

    Caddy 2.11.4
    LiteLLM 1.98.0
    llama-swap v250 / 60226b6
    llama.cpp build 10438 / 9d57ce456

Die exakten verifizierten Container-Digests stehen in:

    runtime-reference.json


## Modelle

Es gibt sechs physische Modellsets und acht API-Aliase.

Quellen und Quantisierungen:

    model-sources.json

Referenzgrößen und SHA256:

    model-manifest.tsv


## Downloadpolitik

Standard:

    rolling main

Dabei bleiben Anbieter, Repository, Quantisierung und Dateiname fest.

Ein Upstream-Update bei Unsloth ist zulässig und wird nach dem Download
durch lokale Größe/SHA256 dokumentiert.


## Concurrency

Die bekannten H100-Werte sind funktionaler Bestandteil des
Referenzdeployments.

Maßgeblich sind:

    hardware/h100-80gb.yaml
    llama-swap.yaml
    infra/gpu/verify_h100_contract.py

Die Werte werden durch diesen Reproduzierbarkeitspass nicht verändert.

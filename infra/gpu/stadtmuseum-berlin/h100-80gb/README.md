# Stadtmuseum Berlin — H100 80 GB reference GPU deployment

This is the calibrated H100 reference deployment for the AI Museum Pipeline.

## Critical rule

The llama.cpp `-c` and `-np` values are pinned runtime behaviour.

They must stay aligned with:

    hardware/h100-80gb.yaml

Do not change context pools, slot counts, pipeline workers or the GND
outer/inner concurrency merely for performance tuning.

The repository contract verifier checks all eight aliases.

## Concurrency model

For ordinary LLM phases:

    hardware parallel_slots == llama.cpp -np

and:

    hardware context_pool == llama.cpp -c

`gemma-4-31b-it` deliberately has no explicit `-np` in the verified
llama.cpp command. Its effective value is therefore treated as 1.

GND is a special two-level case:

    outer object workers = 1
    inner term workers    = authority.gnd model capacity = 8
    qwen3.6-35b-mtp       = -c 65536, -np 8

This prevents object-level concurrency from multiplying the eight
term-level calls.

## API aliases / physical models

Eight API aliases are exposed, backed by six physical model directories.
The two `-64k` aliases reuse the files of their base models.

## Network path

    CPU/orchestrator
        -> HTTPS/Caddy
        -> LiteLLM
        -> llama-swap
        -> llama.cpp
        -> H100

The real DNS name, allowed orchestrator IP and secrets are deployment
configuration and are not committed.

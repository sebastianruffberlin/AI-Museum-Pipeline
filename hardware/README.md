# Hardware profiles

`h100-80gb.yaml` is the only verified reference profile in V2. The published
runtime/cost figures of the original repository refer to that H100 deployment.

For another GPU (H200, L40S, DGX Spark, etc.), copy the profile and tune
`parallel_slots` for every model. **Do not reduce `context_pool` merely to fit
more concurrent requests**: the reference context capacity is part of the
functional/quality contract. A profile is valid only when
`context_pool >= parallel_slots * min_context_per_slot` for every model.

The pipeline and llama.cpp server configuration must use the same
`parallel_slots`. `museum-pipeline validate-config` checks the profile
internally; it cannot benchmark hardware it does not have access to.

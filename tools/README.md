# Tools

Generic maintenance helpers that are part of the current public pipeline live in
this directory. Institution-specific migration, indexing and diagnostic scripts
from the earlier development workflow are intentionally not included in the
public repository.

Current helpers include:

- `dotenv_exports.py` — safely convert a dotenv file to shell export statements;
- `import_gnd_subjects.py` — import the optional GND subject-term dataset into the
  local OpenSearch reference service.

A museum should normally use the `museum-pipeline` CLI and the documented
installer rather than add institution-specific operational scripts here.

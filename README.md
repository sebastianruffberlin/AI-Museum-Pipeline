<div align="center">

# 🏛️ AI Museum Pipeline

**A profile-driven, self-hosted enrichment pipeline for museum collections**

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Deployment](https://img.shields.io/badge/Deployment-Self--Hosted-5b5b5b)
![Core](https://img.shields.io/badge/Core-Museum--Agnostic-7b61ff)
![Profiles](https://img.shields.io/badge/Configuration-Profiles-0a7ea4)
![Skills](https://img.shields.io/badge/Architecture-Skills-b35c00)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![OpenSearch](https://img.shields.io/badge/Authority-GND%20%2F%20OpenSearch-005eb8)
![Embeddings](https://img.shields.io/badge/Embeddings-SigLIP2%20%7C%20DINOv3%20%7C%20BGE--M3-6c757d)
![API](https://img.shields.io/badge/LLM%20API-OpenAI--Compatible-111111)
![Inference](https://img.shields.io/badge/Inference-llama.cpp%20%7C%20LiteLLM%20%7C%20llama--swap-444444)
![Reference GPU](https://img.shields.io/badge/Reference%20GPU-NVIDIA%20H100-76b900)

</div>

AI Museum Pipeline enriches existing museum collection data with deterministic
image analysis, multimodal descriptions, audited search keywords, optional
authority links, embeddings and optional interpretive modules.

It is not a replacement for a collection-management system and it does not treat
LLM output as catalogue truth. The project is built around a simpler idea:

> **Keep source documentation and machine-generated enrichment separate, make
> every enrichment step inspectable, and move museum-specific decisions into
> explicit profiles instead of hiding them in application code.**

The pipeline grew out of a production-oriented museum enrichment workflow. The
current repository turns that experience into a modular Python architecture that
can be adapted by other institutions without reproducing one museum's database,
strategy or infrastructure.

---

## Why this project exists

Museum collection databases are rich but uneven. They often contain decades of
expert documentation, local terminology, changing cataloguing practices,
under-described visual material and fields that were never designed for public
search.

Generative AI can add useful access points, but a single prompt that writes a
few uncontrolled tags creates new problems:

- the model may invent evidence;
- technical museum terminology may remain inaccessible to non-specialists;
- visual observation and interpretation may be mixed together;
- sensitive historical or identity-related claims may be over-inferred;
- the same concept may appear in several inconsistent forms;
- there may be no record of why a term was proposed;
- an apparently precise authority match may simply be wrong;
- institution-specific curatorial frameworks may be mistaken for universal
  properties of the object.

AI Museum Pipeline addresses these problems as a **workflow and data-design
problem**, not merely as a prompting problem.

The reference architecture combines:

- multiple model perspectives;
- explicit semantic clusters;
- evidence-carrying outputs;
- generator/audit or generator/judge separation;
- deterministic policy after model review;
- optional authority reconciliation;
- profile-owned museum semantics;
- reproducible runtime and hardware configuration.

---

## What the pipeline can produce

The complete workflow supports the following enrichment families.

| Module | Purpose | Typical output |
| --- | --- | --- |
| Image features | deterministic pixel-derived description | aspect format, colourfulness, LAB/hex colour clusters, lightness, chroma |
| Image embeddings | similarity and visual exploration | SigLIP2 and DINOv3 vectors |
| Captions | consolidated visual working description | two independent observations + master caption |
| Keywords | public-facing structured discovery terms | 11 semantic keyword clusters, evidence, audit state |
| Authority | optional controlled-authority reconciliation | GND candidate decision, GND ID or `no_match` |
| Emotion / Machine Heart | optional affective reading | controlled possible readings + evidence + judge decision |
| Institutional topics | optional institution-owned thematic relation | topic relation + evidence + subtopic/controlled terms + judge decision |
| Text embeddings | semantic text retrieval | BGE-M3 vector representations |

The modules are deliberately separable. A museum may use only the core search
enrichment, add Machine Heart, add its own thematic framework, or replace
individual methods while keeping the surrounding harness.

---

## What is generic, what is a default, and what belongs to the museum?

One of the most important design choices in this repository is that not every
useful museum decision is presented as a universal standard.

| Layer | Status in this repository | Meaning |
| --- | --- | --- |
| Python harness, persistence interfaces, workflow engine | **generic core** | intended to be reusable across institutions |
| Metadata mapping | **museum profile** | each institution maps its own source fields |
| 11-cluster keyword design | **tested reference/default design** | useful and shipped, but not claimed as a museum standard |
| Keyword generator/audit/policy | **tested reference/default method** | can be adapted in a museum profile |
| GND adapter | **optional reusable integration** | useful in German-language GLAM contexts, not mandatory |
| Machine Heart | **complete reusable default method** | museums-agnostic affective-reading method included in full |
| Colour extraction | **generic deterministic method** | pixel-derived image features |
| Colour-name library | **included reference/search layer** | optional mapping of LAB colours to human-readable and historical names |
| Institutional Topics | **generic engine only** | every museum must supply its own framework and taxonomy |
| Model mapping | **model profile** | roles are stable; concrete models can change |
| H100 settings | **calibrated hardware profile** | reference values, not portable defaults for every GPU |

For the reasoning behind the museum-facing choices, see
[`docs/MUSEUM_DESIGN_DECISIONS.md`](docs/MUSEUM_DESIGN_DECISIONS.md).

### Starter template versus tested reference profile

The repository intentionally contains both:

```text
profiles/_template/
    generalized starter for another museum

profiles/stadtmuseum-berlin/
    public reference profile preserving parts of the tested institutional setup
```

The second directory is useful because it makes real design choices inspectable: keyword
clusters, prompt policy, terminology rules, GND configuration and the Machine Heart
setup can be compared with the generalized template. It must **not** be read as a claim
that every museum should adopt Stadtmuseum Berlin wording or policy, and a new museum
should start by copying `_template`, not the reference profile.

The reference profile is also **not a zero-configuration quick start**. It deliberately
preserves deployment assumptions from the tested case: its source images use the S3
asset path and its authority profile enables GND. A new installation should use
`profiles/_template/` unless it intentionally reproduces those dependencies. Workflow
files decide whether Emotion or Topics run; museum-profile keys do not silently enable
optional modules.

The public Stadtmuseum profile contains **no institutional Topics knowledge base**.
The private thematic framework remains outside the repository; only the generic Topics
engine and the construction contract are public. Machine Heart is different: the
complete museums-agnostic default vocabulary/method is included and can be used
directly from the starter profile.

---

## One object through the pipeline

The repository ships a synthetic example so that the public project does not
depend on publication rights for a real collection object.

```text
Input
  object_id: DEMO-001
  object_type: photograph
  title: Urban street scene
  dating: 1970s
  description: ...
  image: https://example.org/demo-001.jpg

        │
        ├── deterministic image features
        │     format, colourfulness, dominant LAB/hex colours
        │
        ├── image embeddings
        │     SigLIP2 + DINOv3
        │
        ├── visual observations
        │     model A + model B
        │
        ├── master caption
        │     consolidated observation/context
        │
        ├── keyword generator
        │     11 semantic clusters + why/evidence
        │
        ├── keyword audit
        │     fixed error classes
        │
        ├── deterministic policy + repair
        │     keep / move / repair / reject
        │
        ├── optional GND reconciliation
        │     candidate retrieval + LLM decision + no_match
        │
        ├── optional Machine Heart
        │     affective readings + evidence + judge
        │
        ├── optional institution-specific Topics
        │     museum-owned framework + taxonomy + judge
        │
        └── text embeddings
              semantic retrieval vectors
```

See [`examples/DEMO-001.json`](examples/DEMO-001.json) for an illustrative
joined view of the pipeline-owned result tables. It is not a literal API
response and it is not presented as a benchmark.

---

# Architecture

## High-level topology

```text
Museum source database / exported source table
                  │
                  ├──────── metadata
                  │
                  └──────── image / asset reference
                                   │
                                   ▼
                         ┌──────────────────┐
                         │  Python harness  │
                         │                  │
                         │ state / retries  │
                         │ validation       │
                         │ profile loading  │
                         │ tracing          │
                         └────────┬─────────┘
                                  │
           ┌──────────────────────┼──────────────────────┐
           │                      │                      │
           ▼                      ▼                      ▼
   deterministic CPU       embedding services      generative roles
   image features          SigLIP2 / DINOv3       OpenAI-compatible API
                                                     │
                                                     ▼
                                         Caddy → LiteLLM → llama-swap
                                                     │
                                                     ▼
                                                  llama.cpp

                                  │
                                  ▼
                         PostgreSQL enrichment
                         tables separate from
                         museum source records
```

The reference deployment separates orchestration and CPU services from GPU
inference. The Python pipeline can also use an already existing compatible
OpenAI-style endpoint.

## The five-part configuration model

The code separates concerns that are commonly hard-coded into one workflow:

```text
Museum Profile
+ Model Profile
+ Hardware Profile
+ Workflow
+ Deployment configuration
        ↓
     Pipeline run
```

### 1. Museum Profile

`profiles/<museum>/`

Contains the semantics that belong to the institution or to the chosen
reference method:

- mapping from local source columns to canonical concepts;
- asset access rules;
- prompt texts;
- keyword cluster definitions;
- audit and repair policy;
- terminology/debias rules;
- authority configuration;
- optional emotion configuration;
- optional institution-owned topic knowledge.

The intended rule is:

> A museum should normally be able to change museum semantics without editing
> the Python core.

### 2. Model Profile

`models/*.yaml`

Maps stable logical roles to concrete models and generation settings.

Examples of roles include:

```text
caption.primary
caption.secondary
caption.synthesis
tagging.generator
tagging.audit
tagging.repair
authority.gnd
emotion.generator
emotion.judge
topics.generator
topics.judge
```

The workflow therefore depends on **roles**, not directly on one model brand.

### 3. Hardware Profile

`hardware/*.yaml`

Stores calibrated inference constraints such as context pools and parallel
slots. These values are operational properties of a hardware/model
combination, not museum semantics and not prompt settings.

### 4. Workflow

`workflows/*.yaml`

Included presets:

- `core`
- `core-emotion`
- `core-topics`
- `full`

A new institution should start with `core`.

### 5. Deployment configuration

`deployment.yaml` describes non-secret infrastructure choices. `.env` carries
external secrets and credentials. Generated internal runtime secrets are kept
outside the Git checkout.

---

# The core enrichment flow

## 1. Image embeddings

Two image representations are used in the reference stack:

- **SigLIP2** for semantic image similarity;
- **DINOv3** for strongly visual/structural similarity.

Keeping them separate makes it possible to build different forms of visual
exploration rather than pretending that one vector space captures every kind of
similarity.

Embeddings are mathematical retrieval tools. They are not treated as museum
ontology or historical interpretation.

## 2. Deterministic image features

The image-feature stage intentionally avoids an LLM.

`src/museum_pipeline/domain/image_features.py` calculates:

- landscape / portrait / approximately square format;
- mean LAB lightness;
- mean chroma;
- hue dispersion;
- a coarse colourfulness class (`graustufen`, `monochrom_getönt`, `farbig`);
- six LAB k-means clusters;
- a salience value per cluster;
- the five most salient colours as LAB + hex + image share.

The reference implementation downsizes large images, samples approximately
40,000 pixels, converts sRGB to CIE LAB and performs deterministic k-means with
the same loop behaviour used by the predecessor workflow.

### Human-readable colour names are a separate layer

The repository additionally includes `services/farbnamen/`. This is **not the
same thing as the core image-feature computation**.

The current Python runner writes the deterministic colour clusters to
`museum.enrichment_derived`. The colour-name service can then map those LAB
colours to:

- a compact base colour useful as a facet;
- a deterministic German descriptor such as a light/dark/muted/strong colour;
- a nearby attested German colour name when a safe match exists;
- search synonyms from a broad colour-name library;
- historical specialist neighbours from Werner (1821) and Ridgway (1912).

The combined library currently contains 6,811 source entries from German
Meodai names, CSS colours, Werner, Ridgway and the curated Meodai `bestof` list.
Source identity is retained on every entry.

The mapping uses a weighted colour distance in LAB/LCh space plus guards against
obviously misleading hue or lightness changes. Historical names are presented
as historical/specialist vocabulary, not as colourimetric truth.

**Important:** the colour-name mapper is currently an included post-processing
utility; it is not automatically invoked by the main workflow runner. This is a
useful distinction for downstream implementers and is documented intentionally.

See [`services/farbnamen/SOURCES.md`](services/farbnamen/SOURCES.md).

## 3. Visual observation and master caption

The reference flow does not let one vision model become the sole visual source
for later enrichment.

It uses:

```text
Vision model A ──┐
                 ├──> synthesis model ──> master caption
Vision model B ──┘
```

The purpose is not literary caption writing. The master caption is a **working
visual finding** for later machine stages.

The keyword and interpretive modules can see the original image as well as the
consolidated description. The raw observations remain available as fallback
sources when needed.

---

# Keyword enrichment: why eleven clusters?

The default tagging profile uses eleven keyword clusters:

1. `Objekttyp`
2. `Thema_Phänomen`
3. `Inhalt_Motiv`
4. `Funktion_Zweck`
5. `Visuelle_Merkmale`
6. `Form_Gestalt`
7. `Bestandteile`
8. `Gebrauchskontext`
9. `Kultureller_Kontext`
10. `Emotion_Atmosphäre`
11. `Farbe_Nuancen`

These eleven clusters are **not claimed as an established museum standard or a
universal ontology**. They are a pragmatic search-and-description architecture
that emerged from the tested enrichment workflow.

The design goal is to prevent a flat keyword list from mixing semantically
incompatible things.

For example:

```text
photograph       → Objekttyp
tram             → Inhalt_Motiv
public transport → Thema_Phänomen
transport        → Funktion_Zweck / context-dependent use
street life      → Gebrauchskontext
1970s urban life → Kultureller_Kontext only when actually evidenced
rectangular      → Form_Gestalt
faded            → Visuelle_Merkmale
blue             → Farbe_Nuancen
```

The separation makes several downstream behaviours possible:

- different search facets can be built from different semantic dimensions;
- GND matching receives the keyword **and its cluster context**;
- the audit can detect a valid term placed in the wrong semantic bucket;
- cross-cluster redundancy can be reduced;
- the system can distinguish what an object **is**, what an image **shows**, what
  it is **about**, what it was **for**, and in which **social/historical context**
  it is being described.

### Why include `Emotion_Atmosphäre` if Machine Heart exists?

They serve different purposes.

`Emotion_Atmosphäre` in the keyword layer is a conservative search cluster for
simple, strongly evidenced atmosphere terms. It belongs to the flat discovery
vocabulary and is audited like every other keyword.

**Machine Heart** is a separate optional interpretive method with its own
controlled vocabulary, reading scopes, evidence model and independent judge.
It should not be reduced to the keyword cluster, and the keyword cluster should
not be mistaken for full affective interpretation.

### Why include `Farbe_Nuancen` if deterministic colour analysis exists?

Again, the layers are different.

`Farbe_Nuancen` is a linguistic keyword channel produced in the multimodal
keyword process and can participate in search and authority handling like other
terms.

The deterministic image-feature/colour-name path is pixel-derived and is better
suited to reproducible colour facets and visual exploration. Keeping both makes
it possible to compare human-language visual description with deterministic
image statistics instead of pretending they are the same signal.

For the complete rationale and cluster-by-cluster explanation, see
[`docs/MUSEUM_DESIGN_DECISIONS.md`](docs/MUSEUM_DESIGN_DECISIONS.md).

---

# Why the keyword generator prompt is so strict

The keyword generator is intentionally longer than a conventional tagging
prompt because it encodes a **museum search policy** rather than simply asking
for nouns.

Its main choices are:

### Public search before expert-only terminology

The target is explicitly the non-specialist user. The generator is asked to
bridge specialist terminology and likely public search language.

A specific museum term may remain, but it should be accompanied by a broader
term when a non-specialist would otherwise not find it.

### Evidence before inference

The generator receives:

- the original image;
- a consolidated master caption;
- two raw visual observations;
- museum metadata.

It is told to use information absent from the image when the museum metadata
explicitly supplies it, and to use obvious visual evidence even when historical
cataloguing did not record it. Unsupported inference is not allowed.

### `term` + `why`

Every proposed keyword carries a short evidence-based rationale.

This is not decorative explanation. It forces the generation step to expose the
basis for the term so the next stage can audit it.

### Separation from existing structured metadata

The default policy excludes information that normally already belongs to other
structured fields, including pure material/technique, dates and bare personal
or geographic names. The goal is not to reproduce the source record as a bag of
words, but to add discovery value.

### Controlled handling of sensitive interpretation

The prompt contains an evidence-gated critical/decolonial layer. It should name
violence, racist representation, colonial context or problematic provenance
language when evidence supports that reading, but it is explicitly instructed
not to turn neutral objects into a critical narrative by default.

This is a reference policy and can be adapted by another institution.

---

# Why there is a separate audit instead of asking one model to be careful

For keyword enrichment the second model is called an **audit** rather than a
free second tagger.

That distinction is important.

The audit is instructed **not to assign green/yellow/red status directly**. It
classifies each proposed keyword into a fixed set of error classes such as:

- plural form;
- adjective instead of preferred noun form;
- ad-hoc compound;
- missing lay-language bridge;
- wrong cluster;
- no evidence;
- hallucination;
- material/technique leakage;
- date leakage;
- bare geographic/personal name;
- speculation/circular reasoning;
- unsupported asymmetric/ethnicising interpretation;
- redundancy.

A deterministic policy then translates these error classes into machine
actions:

```text
no error class
      ↓
     keep

repairable form problem
      ↓
    repair

wrong cluster
      ↓
     move

unsupported / hallucinated / forbidden content
      ↓
    reject
```

This design deliberately avoids letting the same probabilistic review model both
identify a problem and invent the operational consequence.

A separate repair role is only called for terms that the policy considers
repairable. Only accepted/repaired terms continue to optional GND
reconciliation.

This sequence is one of the central quality-control ideas in the reference
implementation:

```text
generate → classify errors → deterministic policy → repair if possible → authority
```

---

# Optional GND authority reconciliation

The GND integration is optional and is kept separate from keyword generation.

The system first produces and audits a useful museum/search term. It does **not**
force the generator to pretend that every valid keyword must already be an
authority term.

For accepted keywords:

```text
keyword + cluster + evidence
          │
          ▼
OpenSearch retrieval against GND subject data
          │
          ▼
several candidates
          │
          ▼
LLM reconciliation
          │
      ┌───┴────┐
      │        │
    match   no_match
```

`no_match` is a legitimate result. An incorrect authority identifier is worse
than an unmapped but useful discovery term.

The GND dataset itself is not bundled as a static repository snapshot; the
import tooling records upstream provenance.

---

# Machine Heart: optional affective readings

The Emotion module is optional. Unlike Topics, however, the repository ships a
complete museums-agnostic default method called **Machine Heart**.

A museum has three choices:

1. do not run Emotion;
2. use Machine Heart as supplied;
3. replace its vocabulary and/or prompts with another method while keeping the
   pipeline interface.

## What Machine Heart does — and does not do

Machine Heart does **not** claim to detect the emotion of a depicted person and
it does not declare that an object objectively *is* melancholic, nostalgic or
threatening.

Its epistemic form is:

> **This object can be read as / can have the effect of ...**

The method separates four levels:

```text
A  visible finding
B  depicted situation
C  possible affective effect     ← tagged
D  mental state of a person      ← never inferred
```

The supplied editorial knowledge model contains **146 concepts**. The tested
runtime view exposes **121 `resonance_reading` concepts** to generator and judge;
the remaining concepts stay part of the editorial model but are not runtime
readings.

For v1.0 the runtime projection intentionally reproduces the tested production
adapter. Each of those 121 active concepts exposes only a minimal runtime field set:
`concept_id`, `begriff`, `definition` and, where defined, `nicht_verwenden_wenn`. The richer
146-concept authoring file additionally records roles, context requirements,
distinctions, provenance and PAD metadata. Those richer fields are published for
method transparency and future/custom adapters, but they are **not automatically
injected into the current Generator/Judge prompt context**. Because the runtime
projection has already filtered to `resonance_reading`, role selection happens before
the prompt. A museum that wants richer runtime constraints should version its
vocabulary adapter and prompts together and revalidate the method.

Each reading should be supported by evidence, and the judge checks for common
errors such as psychologising people, deriving nostalgia from age/sepia alone,
confusing formal properties with affect, or smoothing away meaningful tension.

A custom emotion database may have a completely different internal schema. It
only has to satisfy the published runtime vocabulary contract.

See [`docs/EMOTION_METHOD.md`](docs/EMOTION_METHOD.md).

---

# Institutional Topics: engine public, knowledge private

Institutional collection priorities are fundamentally different from Machine
Heart.

The repository publishes the **Topics engine**, schemas, prompts and
construction contract. It deliberately does **not** publish the institution's
actual thematic framework or the private source document from which that
framework was developed.

A museum that wants to run `core-topics` or `full` must therefore provide its
own knowledge base.

## Required institution-owned resources

```text
profiles/<museum>/topics/
  profile.yaml
  framework.md
  taxonomy.json
```

A useful `framework.md` should define, for every topic:

- research interest / scope;
- what is included;
- what is explicitly not sufficient;
- object-level evidence rules;
- optional retrieval anchors;
- sensitivity/review rules.

A useful `taxonomy.json` should add stable subtopic and controlled-term IDs plus
`use_when` / `do_not_use_when` guidance.

The production-tested implementation used a knowledge base at a scale of **8
topics, 64 subtopics and 104 controlled terms**. These numbers are disclosed to
show a tested order of magnitude. The topic names, definitions, anchors and
underlying strategy document are not part of the public repository.

The crucial epistemic rule is:

> **The framework explains what a topic means. It is not evidence that a
> particular object belongs to the topic.**

The generator proposes evidence-backed relations. The independent judge
re-evaluates all configured topics and may confirm, correct, downgrade, remove
or add a relation.

The current machine-readable Topic schemas still retain a few German key names
from the tested implementation (for example `schwerpunkte`). Those keys are a
versioned API-contract detail; they do **not** expose the institution's topic
names, definitions or strategic knowledge.

The SQL files under `database/migrations/` are upgrade helpers for pre-public
installations. They necessarily mention former German result-table/column names, but
they contain **no topic framework, taxonomy, anchors or controlled terms**. Fresh
installs use the generic schemas under `database/core.sql` and `database/modules/`.

See [`docs/TOPIC_KNOWLEDGE_BASE.md`](docs/TOPIC_KNOWLEDGE_BASE.md).

---

# Museological safeguards

The project encodes several boundaries that should remain visible to
implementers.

## Source and enrichment stay separate

The pipeline owns its output tables. It should not silently rewrite historical
catalogue documentation.

## Observation is not interpretation

A visible property such as symmetry is not automatically an affect such as
calmness or solemnity.

## Generated outputs are proposals with provenance

Where appropriate the system stores model role, rationale, review decision,
status and evidence.

## Multiple models do not create truth

Generator/judge structures are quality-control mechanisms, not epistemic
certification.

## Authority data is optional reconciliation

Not every useful museum or discovery term should be forced into an authority
record.

## Sensitive inference requires stronger evidence

Appearance, name, date or geographical proximity alone should not generate
identity, political, colonial, migration or other sensitive historical claims.

## Embedding proximity is not historical meaning

Vector neighbours are algorithmic similarities, not curatorial or historical
identity.

## Observability can contain museum data

Phoenix/OpenTelemetry tracing is disabled by default. If enabled, LLM spans can
contain truncated prompt/output text and object identifiers. Likewise, `-v` and
`-vv` deliberately print increasingly detailed prompts, responses and
intermediate structures. Treat tracing backends and verbose logs as data
destinations that may receive unpublished collection information or personal
data; enable them only under the institution's normal security/data-governance
rules.

See [`docs/MUSEOLOGICAL_PRINCIPLES.md`](docs/MUSEOLOGICAL_PRINCIPLES.md) and
[`SECURITY.md`](SECURITY.md).

---

# Installation

## Requirements

For the reference two-host deployment:

- Linux CPU/orchestrator host;
- Docker + Compose;
- Git;
- Python 3.11+;
- enough CPU-host storage/RAM for the Dockerized PostgreSQL and embedding services;
- prepared NVIDIA GPU host **or** an existing OpenAI-compatible endpoint;
- optional S3-compatible object storage;
- Hugging Face credentials where an upstream gated model requires them;
- museum source data and image access.

The installer configures the application stack. It does not order cloud
servers, create DNS zones, create S3 accounts or invent a source database.

## Clone and install the CLI

```bash
git clone https://github.com/sebastianruffberlin/AI-Museum-Pipeline.git
cd AI-Museum-Pipeline
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e .
```

The commands below use the installed `museum-pipeline` entrypoint. Activate the
virtual environment first or prefix the command with `.venv/bin/`.

## Create a museum profile

```bash
museum-pipeline init-profile my-museum
```

Then inspect and edit:

```text
profiles/my-museum/
  metadata.yaml
  profile.yaml
  prompts/
  tagging/
  authority/
  emotion/       # complete Machine Heart default; can be kept or replaced
  topics/        # blueprint only; institution-owned content must be authored
```

The starter already contains the metadata context required by `core-emotion`.
It also contains a conservative `contexts.topics` example, but Topics remains
disabled until the museum supplies `framework.md`, `taxonomy.json` and a Topics
profile.

## Deployment configuration and secrets

```bash
cp deployment.example.yaml deployment.yaml
cp installer.env.example .env
chmod 600 .env
```

Keep infrastructure decisions in `deployment.yaml` and credentials in `.env`.
The public example starts with `features.s3: false` and `features.gnd: false`;
enable optional infrastructure only when the museum profile actually uses it.
Generated GPU/runtime secret files are kept outside the Git checkout.

## Install

```bash
museum-pipeline install --dry-run
museum-pipeline install
museum-pipeline doctor
```

`doctor` validates configuration and service readiness. It should not be treated
as a full application-level acceptance test.

See [`docs/INSTALLER.md`](docs/INSTALLER.md) and
[`docs/MANUAL_DEPLOYMENT.md`](docs/MANUAL_DEPLOYMENT.md).

---

# Minimal runtime use

```bash
museum-pipeline show-config
museum-pipeline validate-config
museum-pipeline run --workflow core --count 1 -v
```

Useful run controls include:

```text
--ids
--ids-file
--collection
--force
--retry-failed
```

Start with a small, known object set before scaling a new profile.

---

# Reference model stack

The repository contains model configuration, not model weights.

The verified reference stack uses Qwen/Gemma GGUF models behind an
OpenAI-compatible endpoint and the following embedding families:

- SigLIP2;
- DINOv3;
- BGE-M3;
- BGE reranker (`BAAI/bge-reranker-v2-m3`) as an optional late-ranking service endpoint.

The H100 hardware profile under `hardware/h100-80gb.yaml` and the corresponding
GPU reference deployment contain calibrated context/parallelism values. They
should not be copied blindly to another GPU.

The calibrated bundle currently lives at
`infra/gpu/stadtmuseum-berlin/h100-80gb/` because it records the measured reference
deployment from the original implementation. The directory name is provenance, not a
museum-semantic dependency: another institution can use the same hardware bundle or
supply a different calibrated deployment through `gpu.deployment_path`.

Model weights and upstream datasets keep their own licenses and access terms.
See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

---

# Reproducibility and quality gates

The public release is designed to make the tested architecture inspectable.
The repository includes:

- CPU and GPU Compose contracts;
- reference runtime information;
- H100 concurrency-contract verification;
- unit/contract tests;
- explicit model and GND provenance rules;
- clean-room deployment documentation;
- a manually verified CPU ↔ fresh-H100 end-to-end path;
- release secret scanning and dependency-audit guidance.

See [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) and
[`docs/FRESH_HOST_CHECKLIST.md`](docs/FRESH_HOST_CHECKLIST.md).

---

# Repository map

```text
database/        pipeline-owned persistence schemas and optional modules
deploy/          pipeline container
profiles/        museum profiles and starter template
models/          logical model-role profiles
hardware/        calibrated hardware profiles
workflows/       module presets
src/             museum-agnostic Python core and skills
services/        embedding, presign and colour-name utilities
infra/           CPU/GPU deployment definitions
examples/        synthetic public output examples
docs/            architecture, method and deployment documentation
tests/           structural, behavioural and release contracts
```

---

# Documentation guide

| Document | Read it for |
| --- | --- |
| [`docs/START_HERE.md`](docs/START_HERE.md) | orientation |
| [`docs/WORKFLOW.md`](docs/WORKFLOW.md) | object-level processing flow |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | code and module architecture |
| [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md) | services and topology |
| [`docs/PROFILES.md`](docs/PROFILES.md) | profile/configuration model |
| [`docs/MUSEUM_DESIGN_DECISIONS.md`](docs/MUSEUM_DESIGN_DECISIONS.md) | **why the 11 clusters, prompts/audit, colours and Topics are designed this way** |
| [`docs/MUSEOLOGICAL_PRINCIPLES.md`](docs/MUSEOLOGICAL_PRINCIPLES.md) | interpretive boundaries |
| [`docs/EMOTION_METHOD.md`](docs/EMOTION_METHOD.md) | Machine Heart and custom emotion-resource contract |
| [`docs/TOPIC_KNOWLEDGE_BASE.md`](docs/TOPIC_KNOWLEDGE_BASE.md) | build contract for institution-owned Topics |
| [`docs/CUSTOMIZATION.md`](docs/CUSTOMIZATION.md) | adapting the distribution |
| [`docs/INSTALLER.md`](docs/INSTALLER.md) | installer behaviour |
| [`docs/MANUAL_DEPLOYMENT.md`](docs/MANUAL_DEPLOYMENT.md) | manual deployment |
| [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) | reproducibility policy |
| [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) | external models, data and components |
| [`SECURITY.md`](SECURITY.md) | security reporting and secret handling |

---

# Language note

The repository documentation is primarily written in English so that the
architecture is reusable beyond one institution. Several reference prompts and
runtime field names remain German because the tested implementation targets
German-language museum documentation, public search and the GND. They are part
of the reference profile, not a requirement of the Python core.

---

# License

Original code and project-owned material in this repository are released under
the MIT License; see [`LICENSE`](LICENSE).

Third-party model weights, authority data, colour-name sources, datasets and
runtime components keep their own licenses and terms. See
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

---

# Project origin

AI Museum Pipeline is the modular Python continuation of the earlier
[n8n-based AI Museum Tagging project](https://github.com/sebastianruffberlin/AI-Museum-Tagging).

The legacy repository documents the original n8n/SeaTable workflow. This
repository contains the current architecture and is maintained as the active
implementation.

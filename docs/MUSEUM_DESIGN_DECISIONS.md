# Museum-facing design decisions

This document explains the most important **museum-specific and
museum-methodological choices** shipped with the reference profile.

It exists because a reusable pipeline should make a distinction between:

- software contracts that are genuinely generic;
- methods that are intentionally supplied as reusable defaults;
- decisions that worked in the tested museum workflow but are not universal
  professional standards;
- knowledge that every institution must author for itself.

## Reference profile and starter template

Two public profile layers are intentionally present:

```text
profiles/_template/
    generalized starter configuration

profiles/stadtmuseum-berlin/
    public reference configuration derived from the tested implementation
```

This distinction matters when reading prompts. The starter template removes
institution-specific scale/context wording where possible. The public reference profile
keeps parts of the real tested wording so that design decisions can be inspected.
Neither is a normative museum standard.

The reference profile may publish method choices such as tagging policy, GND setup and
Machine Heart because those are intended to be reusable or inspectable. It does **not**
publish the institution-specific Topics knowledge base or the private document behind it.

The short version is:

| Area | What the repository ships | How to treat it |
| --- | --- | --- |
| 11 keyword clusters | complete tested reference design | useful default, configurable, **not a universal museum ontology** |
| keyword generator + audit + policy | complete tested method | reusable reference method, adapt where local policy differs |
| colour extraction | deterministic image method | reusable technical layer |
| colour naming | included reference/search vocabulary layer | optional post-processing; source/provenance matters |
| Machine Heart | complete museums-agnostic default | optional reusable method or replaceable by a custom emotion system |
| Topics | generic engine + build contract only | **museum must provide all thematic content** |
| GND | optional adapter | useful authority layer in appropriate contexts, never mandatory |

---

# 1. Why are keywords divided into 11 clusters?

The default tagging profile uses:

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

## 1.1 They are not claimed as a cataloguing standard

The number **11** is not derived from a published museum ontology in this
repository and should not be read as theoretically canonical.

The clusters are a pragmatic design that emerged from the tested goal:

> create public-facing discovery terms from heterogeneous museum documentation
> and images without collapsing different kinds of statements into one flat
> keyword list.

They are therefore closer to **semantic search facets** than to a replacement
for a collection-management thesaurus.

A museum may keep them, rename them, add/remove clusters or build a different
system, provided its prompts, policy and downstream expectations remain
consistent.

## 1.2 The problem with one flat keyword list

Without semantic separation, a single result might mix:

```text
photograph
tram
public transport
street life
rectangle
faded
blue
```

All may be useful, but they answer different questions.

The cluster design separates those questions:

| Cluster | Question it answers | Why it exists |
| --- | --- | --- |
| `Objekttyp` | What is the overall physical/documentary object? | gives immediate object orientation |
| `Thema_Phänomen` | What broader subject or social/historical phenomenon is involved? | separates abstract subject from depicted things |
| `Inhalt_Motiv` | What is concretely depicted or named? | supports literal motif/object search |
| `Funktion_Zweck` | What is it for / what function or action is involved? | separates purpose from type and subject |
| `Visuelle_Merkmale` | What visible state/appearance is directly observable? | captures public visual search terms often absent from catalogues |
| `Form_Gestalt` | What is the form or geometry? | makes shape searchable without confusing it with condition |
| `Bestandteile` | Which notable parts are present? | supports part–whole discovery |
| `Gebrauchskontext` | In what activity/life-world/use situation does it occur? | captures social practice rather than only physical function |
| `Kultureller_Kontext` | Which historically/socially specific context is actually evidenced? | permits context while imposing a high evidence bar |
| `Emotion_Atmosphäre` | Which simple atmosphere term is strongly evidenced? | gives a lightweight discovery vocabulary, not full emotion analysis |
| `Farbe_Nuancen` | Which colour words describe the object/image? | gives a linguistic colour search channel |

## 1.3 The clusters are designed to reduce semantic leakage

The reference prompt contains explicit anti-redundancy rules. A term should
normally appear in the cluster where it is semantically strongest instead of
being copied everywhere.

This makes it possible to distinguish, for example:

```text
thing              ≠ subject
subject            ≠ depicted motif
motif              ≠ function
function           ≠ use context
visual state       ≠ shape
shape              ≠ colour
historical context ≠ identity inferred from appearance
```

The distinction is useful for both quality control and search interfaces.

## 1.4 The cluster travels with the keyword

The persistence model stores `cluster` next to each keyword. The optional GND
adapter also receives both the term and its cluster.

That means semantic context survives beyond the prompt and can be used for:

- faceting;
- audit (`FALSCHER_CLUSTER`);
- authority reconciliation;
- search weighting;
- later evaluation.

## 1.5 Why `Emotion_Atmosphäre` exists next to Machine Heart

The keyword cluster is deliberately shallow.

It is for simple, strongly evidenced search terms that can behave like ordinary
keywords. It is audited by the same rules as the rest of the keyword set.

Machine Heart is a **different layer**:

- controlled affective vocabulary;
- explicit reading scopes;
- evidence per reading;
- possible counter-evidence/tension;
- generator + independent judge;
- no psychologising of depicted people.

A museum can therefore use keyword atmosphere terms without enabling Machine
Heart, or use Machine Heart while still keeping the ordinary discovery layer.

## 1.6 Why `Farbe_Nuancen` exists next to deterministic colour analysis

The keyword cluster is a **linguistic/multimodal statement** produced by the
keyword model.

The image-feature path is a **pixel-derived measurement**.

Keeping both allows the project to preserve two different signals:

```text
what the multimodal language process calls the colour
versus
what deterministic LAB analysis measures in the pixels
```

For reproducible colour facets, the deterministic path is the stronger source.
For public-language discovery, the linguistic keyword can still be useful.

---

# 2. Why is the keyword generator prompt structured this way?

The shipped generator prompt is intentionally opinionated. It is not just a
request for "good museum tags".

It encodes the tested discovery policy.

## 2.1 The primary user is a non-specialist

The reference prompt explicitly defines the target as people who do not know the
collection structure or specialist terminology.

This leads to two key rules.

### Folksonomy rule

The model should think about plausible everyday search language, not only
internal expert vocabulary.

### Bridge rule

A specialist term should be accompanied by an understandable broader term when
that bridge is necessary for discovery.

The purpose is not to remove expertise. It is to create a bridge between expert
documentation and public retrieval.

## 2.2 The prompt receives multiple evidence channels

The tagging step can use:

- original image;
- consolidated `master_caption`;
- raw visual observation A;
- raw visual observation B;
- source museum metadata.

The prompt contains a conflict policy because these sources can disagree or be
asymmetric.

The intended behaviour is:

- use museum metadata for documented facts that are not visually visible;
- add obvious visual properties that historical documentation never recorded;
- treat uncertain visual observations cautiously;
- never invent a fact that exists in none of the evidence channels.

## 2.3 The prompt deliberately does not copy every source field into keywords

The default discovery policy excludes several classes that normally belong in
structured catalogue fields instead of free discovery tags:

- pure material;
- manufacturing technique;
- dates/centuries;
- bare geographic names;
- artist/person names.

This is a design decision, not a statement that those data are unimportant.
They remain available as structured metadata. The enrichment layer should add
new retrieval value instead of duplicating the catalogue row as tokens.

## 2.4 Singular, nouns and controlled granularity

The prompt favours singular nouns and discourages uncontrolled adjective forms
or improvised compounds.

The reasons are operational:

- easier de-duplication;
- more stable authority matching;
- cleaner facets;
- more consistent retrieval vocabulary.

The prompt allows carefully defined exceptions, for example directly observable
states in `Visuelle_Merkmale`.

## 2.5 Every keyword must explain itself

The generator outputs:

```json
{
  "term": "...",
  "why": "short evidence-based reason"
}
```

The `why` field is a self-discipline mechanism and an audit input.

If the generator cannot formulate a defensible evidence basis, the reference
method says the term should not be emitted.

## 2.6 Critical/decolonial review is evidence-gated

The reference prompt includes checks for colonial/racist representation,
violence, problematic provenance language and sensitive material.

It also explicitly contains an **anti-over-flagging** rule.

The intention is:

> name power/violence where the object or documentation supports it, but do not
> make every neutral object carry an invented critical narrative.

The prompt also attempts to prevent timeless ethnicising description and asks
for historically situated wording.

Other institutions may reasonably adapt this policy language. The important
architectural point is that such policy is visible in the museum profile instead
of hidden in application code.

---

# 3. Why is there an audit/judge prompt as a second model step?

For ordinary keyword tagging, the second model is best understood as an
**error-class audit**, not as a second free generator.

## 3.1 Generator and reviewer have different jobs

The generator tries to maximise useful discovery terms under the profile rules.

The audit is intentionally narrower. It checks the proposed terms against image,
caption, metadata and policy and assigns fixed error classes.

The audit prompt explicitly says that it must **not** assign final
`green/yellow/red` status.

## 3.2 Fixed error classes make model criticism actionable

The current audit catalog includes:

```text
PLURAL
ADJEKTIV
KOMPOSITUM
FEHLENDE_BRUECKE
FALSCHER_CLUSTER
KEINE_EVIDENZ
HALLUZINATION
MATERIAL_PUR
MATERIAL_KOMPOSITUM
DATIERUNG
GEOGRAFIE_EIGENNAME
SPEKULATION_ZIRKEL
ASYMMETRIE
REDUNDANZ
```

This is more useful than a generic "looks good / looks bad" review because the
next stage can act deterministically on the classification.

## 3.3 A deterministic policy decides the consequence

`tagging/policy.yaml` groups error classes into actions.

Conceptually:

```text
no error
  → keep

repairable form problem
  → repair

wrong semantic cluster
  → move

unsupported / hallucinated / forbidden content
  → discard
```

This is a deliberate separation of responsibilities:

```text
LLM: identify the kind of problem
code: apply the operational policy
```

The reviewer is therefore less able to silently redefine the workflow from one
object to another.

## 3.4 Why have a separate repair model?

Some problems mean the underlying concept is useful but the surface form is
wrong.

Examples include:

- plural → singular;
- adjective → noun;
- decomposable compound;
- missing lay-language bridge;
- material-prefixed compound where the non-material noun remains useful.

The policy can send only those terms to repair. A rejected hallucination is not
"repaired" into a new invented fact.

## 3.5 Why does GND come after audit/repair?

Authority matching should not legitimise a bad generated term.

Only terms that survive the quality policy are sent into the optional GND
retrieval/reconciliation stage.

This avoids a common failure mode in which a model invents a dubious term and a
subsequent authority lookup makes the output look more authoritative simply
because a plausible identifier was found.

---

# 4. What is behind the colour system?

The repository contains **two distinct colour mechanisms** and they should not
be conflated.

## 4.1 Deterministic image colour features

`src/museum_pipeline/domain/image_features.py` performs classic image
processing, not generative inference.

The reference algorithm:

1. loads the image as RGB;
2. downsizes proportionally for bounded processing;
3. samples up to roughly 40k pixels;
4. converts sRGB to CIE LAB (D65);
5. calculates mean lightness and chroma;
6. calculates hue dispersion for coloured pixels;
7. derives a broad colourfulness class;
8. runs deterministic k-means (`k=6`, 8 iterations) in LAB;
9. scores cluster salience using distance, chroma and area;
10. stores the five most salient colours as LAB, hex, share and salience.

The broad colourfulness classes are:

```text
graustufen
monochrom_getönt
farbig
```

The purpose is reproducible search/facet data that does not depend on a model
prompt.

## 4.2 Why LAB?

LAB is used because the next naming layer needs a colour space in which
lightness and chromatic components can be treated separately. The repository's
naming algorithm can then guard against mistakes such as mapping a light grey to
a saturated colour merely because an RGB value happens to be numerically close.

The project does not claim archival colourimetry. Input images may contain
scanning, white-balance, ageing, reproduction or compression effects.

## 4.3 The human-readable colour-name library

`services/farbnamen/` provides an additional lookup layer.

Its combined library currently contains 6,811 entries:

- 477 German names from the Meodai ecosystem;
- 148 CSS named colours;
- 110 Werner (1821) names;
- 1,117 Ridgway (1912) names;
- 4,959 entries from the curated Meodai `bestof` list.

Entries retain their source instead of being flattened into one anonymous
vocabulary.

The library is built without cross-source deduplication because the same name in
Werner, Ridgway and a modern list may legitimately refer to slightly different
reference colours.

## 4.4 Five roles of a colour name

The mapping code separates several outputs:

### `grundfarbe`

A compact controlled base colour for faceting.

### `deskriptor`

A deterministic German descriptor derived from LAB, including broad lightness
or saturation modifiers where appropriate.

### `anzeige`

A nearby attested German colour name, but only when hue/lightness/chroma guards
consider the match safe enough.

### `synonyme`

Nearest names from the broad library. These are primarily useful as retrieval
vocabulary rather than as authoritative display labels.

### `fach`

Nearest Werner/Ridgway historical specialist names, deliberately kept separate
from ordinary modern display vocabulary.

## 4.5 Weighted distance and guardrails

The mapper uses a weighted LAB/LCh distance. Hue disagreement becomes more
important for saturated colours; hue is de-emphasised for nearly neutral
colours where angle becomes unstable.

Additional guards stop obvious errors such as:

- a light grey receiving a colourful name;
- a warm neutral being mapped to a strong opposite hue;
- a dark saturated red being automatically collapsed into brown.

## 4.6 Historical colour names are references, not ground truth

Werner (1821) and Ridgway (1912) are historically interesting vocabularies. The
repository stores digitised approximations of their colours.

Those values are suitable for nearest-neighbour naming and exploration, **not
for claiming an exact reconstruction of the original historical colour plate**.

The public provenance/licensing basis is documented in
`services/farbnamen/SOURCES.md` and `THIRD_PARTY_NOTICES.md`.

## 4.7 Current integration status

The main runner automatically computes the deterministic image features.

The human-readable colour-name mapper is currently an **included
post-processing utility** that can update the `farbnamen` JSON field in
`museum.enrichment_derived`; it is not currently called as a normal runner
phase.

This status should remain explicit in the documentation until the utility is
integrated into the normal workflow or intentionally kept separate.

---

# 5. What is behind the institutional Topics module?

Topics are deliberately **not** shipped as a default knowledge base.

The reason is conceptual, not merely privacy-related:

> An institutional collection priority is a curatorial/strategic relation, not
> an intrinsic property of every museum object.

The public repository therefore contains the Topics engine but no real
institutional strategy document and no real topic names/definitions/anchors.

## 5.1 What the tested system used

The private tested implementation used a substantial institutional knowledge
base at the following scale:

```text
8 topics
64 subtopics
104 controlled terms
```

These numbers are published only to demonstrate a tested order of magnitude.
They are **not** requirements and the underlying contents are intentionally not
published.

## 5.2 What a museum must provide

A Topics-enabled profile needs:

```text
profiles/<museum>/topics/
  profile.yaml
  framework.md
  taxonomy.json
```

### Framework

For each topic the recommended structure is:

- research interest / scope;
- includes;
- explicit exclusions / `not sufficient` cases;
- evidence rules;
- optional retrieval anchors;
- sensitivity/review rules.

### Taxonomy

The taxonomy supplies stable machine IDs for:

- topics;
- subtopics;
- controlled terms;
- `use_when` guidance;
- `do_not_use_when` guidance.

The exact taxonomy size is institution-defined.

## 5.3 The most important rule: framework is not object evidence

A knowledge base may mention a date, place, person, event or concept because it
helps define the topic.

That mention does **not** prove that a particular object has that topic
relation.

The generator must ground the relation in the object's own metadata, image or
consolidated visual evidence.

This distinction prevents a framework from becoming a machine-readable source
of self-fulfilling associations.

## 5.4 Why generator + judge?

Topic assignment is interpretive and institution-specific. The tested method
therefore has two independent roles:

### Generator

Checks the object against all configured topics and proposes evidence-backed
relations, subtopics and controlled terms.

### Judge

Re-evaluates the complete topic set and may:

- confirm;
- correct;
- downgrade;
- remove;
- add a missed relation.

The judge is not restricted to checking only what the generator already chose.

This is useful because the most important topic error may be **omission**, not
only false positive assignment.

## 5.5 Why no reduced public substitute?

A simplified imitation of one institution's confidential thematic framework
would be misleading. It would look like the production knowledge base while
lacking the definitions and strategic context that made the tested system work.

The public repository therefore publishes the **construction contract**, not an
anonymised pseudo-version of the private content.

See `docs/TOPIC_KNOWLEDGE_BASE.md` for the file contract and starter examples.

---

# 6. How these choices should be reused

A new museum does not have to make an all-or-nothing decision.

A reasonable adoption path is:

```text
1. keep the generic Python core
2. map local metadata fields
3. run the reference keyword system on a small test set
4. decide whether the 11-cluster design fits local search goals
5. adapt prompts/policy where local cataloguing or ethics policy differs
6. enable GND only if useful
7. enable Machine Heart if wanted, using default or custom vocabulary
8. build Topics only after the institution has an explicit thematic knowledge base
9. evaluate with real collection examples before scaling
```

The repository is strongest when its reference decisions are treated as
**inspectable starting points**, not invisible defaults that every institution
must accept.

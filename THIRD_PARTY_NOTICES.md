# Third-party notices

The MIT license in [`LICENSE`](LICENSE) applies to code and original material
in this repository unless a file or section states otherwise. Third-party
software, model weights, datasets and source material remain subject to their
respective licenses and terms.

This repository does **not** redistribute the referenced LLM/VLM or embedding
model weights. Installation helpers download them from their upstream hosts.
Users are responsible for reviewing the license and access terms applicable at
the time of download.

## Reference model stack

| Component | Reference source | License / terms |
| --- | --- | --- |
| Qwen 3.6 GGUF reference models | Unsloth Hugging Face repositories listed in `infra/gpu/stadtmuseum-berlin/h100-80gb/model-sources.json` | Apache-2.0 as declared by the referenced repositories |
| Gemma 4 GGUF reference models | Unsloth Hugging Face repositories listed in `infra/gpu/stadtmuseum-berlin/h100-80gb/model-sources.json` | Apache-2.0 as declared by the referenced repositories |
| SigLIP2 `google/siglip2-giant-opt-patch16-384` | Hugging Face / Google | Apache-2.0 |
| BGE-M3 `BAAI/bge-m3` | Hugging Face / BAAI | MIT |
| BGE reranker `BAAI/bge-reranker-v2-m3` | Hugging Face / BAAI | Apache-2.0 |
| DINOv3 `facebook/dinov3-vitl16-pretrain-lvd1689m` | Hugging Face / Meta | DINOv3 License; gated access may apply |

DINOv3 is **not** covered by this repository's MIT license. Users must obtain
access from the upstream provider and comply with the DINOv3 License.

## Norm data

The optional GND integration downloads authority data from the Deutsche
Nationalbibliothek. GND authority data is published under CC0 1.0 by the DNB.
See `infra/cpu/reference/gnd-source.json` for the source endpoint used by the
reference importer.

## Colour-name data

Files under `services/farbnamen/` combine several attributed sources. The
combined LAB values are derived data used for nearest-neighbour colour naming.

- `meodai_farbnamen_de_lab.json` — derived from the `farbnamen` / Meodai list as
  distributed through the MIT-licensed `meodai/color-name-lists` ecosystem.
- `meodai_bestof_lab.json` — derived from Meodai's MIT-licensed colour-name
  lists.
- `css_named_lab.json` — CSS named colours, consumed through the MIT-licensed
  Meodai list.
- `ridgway_1912_lab.json` — Robert Ridgway, *Color Standards and Color
  Nomenclature* (1912), public-domain source work; digital data source documented
  in the file metadata is MIT-licensed.
- `werner_1821_lab.json` — Patrick Syme / Abraham Gottlob Werner, *Werner's
  Nomenclature of Colours* (1821), public-domain source work. The digital colour
  list is distributed through `meodai/color-name-lists` 3.33.2 (MIT package); its
  Werner-list metadata declares CC0 1.0 and cites C82 as upstream. No C82 site
  images or graphics are redistributed by this repository.

The source JSON files retain provenance metadata. See also
`services/farbnamen/SOURCES.md`.

## Containers and Python dependencies

The deployment uses third-party projects including Caddy, LiteLLM, llama-swap,
llama.cpp, PostgreSQL, OpenSearch and the Python packages declared in
`pyproject.toml` and service `requirements.txt` files. Those components are not
relicensed by this repository. Their own licenses apply.

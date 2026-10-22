# Separate Docusaurus review version

The source project in `project/` is generated from the retained Weather publication
and explicit accepted author inputs. It deploys beneath
`/clew-weather-demo/docusaurus/`; the original native website remains byte-identical.
The review index links real examples in the built MDX site and labels the external
native example gallery as historical. This source candidate is not a Codeclew release.

Regenerate with the supported source checkout and the same publication, snapshot,
reading plan, comparison and derived data-model navigation used by
`documentation/reference/build.py`. Render into a fresh export directory with
`clew docs pages render --format docusaurus`, then freeze its portable sources:

```sh
python3 -I -S documentation/docusaurus/variant.py freeze \
  --export /absolute/path/to/new-export --revision FULL_RENDERER_SHA --version VERSION
python3 -I -S documentation/docusaurus/variant.py verify --candidate
```

`freeze` refuses an existing `project/`; preserve the previously accepted project
before deliberately replacing it. The export manifest continues to verify every
exporter-owned file. The separate file index additionally pins the review index,
visible source-candidate identity and all committed project files. Derived reader
packs, dependencies and build output are excluded.

Build with Node 24 and the lockfile:

```sh
cd documentation/docusaurus/project
npm ci --no-audit --no-fund
CODECLEW_DOCS_URL=https://codeclew.github.io \
CODECLEW_DOCS_BASE_URL=/clew-weather-demo/docusaurus/ \
CODECLEW_DOCS_GENERATOR_REVISION=FULL_RENDERER_SHA \
CODECLEW_DOCS_REVIEW_INDEX=true npm run build
```

After both independent critics inspect this exact native candidate and production
Docusaurus build, retain their reports under `acceptance/` and set the publication
policy's acceptance status to PASS with `analyst` and `engineer` objects containing
relative `path` and SHA-256 `sha256`. Do not mark acceptance from a static build.
`variant.py verify` without `--candidate` rejects pending or changed reports.

The single Pages workflow always stages both versions together. A complete native
tree and published policy matching commit
`c2195229942f120744aa3daa03cfb0ec3742a542` may retain official v0.13.39 only after its
tag resolves to the recorded release commit. Any native byte/file/policy delta
uses the existing latest-release or accepted-source publication gate. The
Docusaurus source has its own frozen identity, author-input checks, source-file
index, strict production build and independent browser acceptance. Publication
remains a separate authorized deployment action.

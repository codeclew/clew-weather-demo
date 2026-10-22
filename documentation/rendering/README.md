# Rendering capability showcase

The public `/rendering/` route composes real Weather examples, their input files,
commands, producer identities and evidence. It does not rerun analyzers, invoke
models, regenerate historical exports or change the frozen native/Docusaurus
inputs. The 93-entry historical catalogue is retained, with later capabilities
and explicit demonstration gaps listed separately.

The saved `docs render` publication, standalone Pages 0.13.39 and source-candidate
Docusaurus 0.13.46 are different outputs. They share a saved publication identity
but use different renderer revisions and optional reading/model/comparison inputs.
The original publication retains its renderer schema, not its producer release
or commit; that provenance gap is visible. Current support is researched at public
0.13.48, not attributed retroactively to historical examples.

## Build the additive production site

Use Python 3.11+ and Node 24. Preserve the existing lockfile and frozen project:

```sh
python3 -I -S documentation/reference/test_verify.py
python3 -I -S documentation/docusaurus/test_variant.py
python3 -I -S documentation/docusaurus/variant.py verify
cd documentation/docusaurus/project
npm ci --no-audit --no-fund
CODECLEW_DOCS_URL=https://codeclew.github.io \
CODECLEW_DOCS_BASE_URL=/clew-weather-demo/docusaurus/ \
CODECLEW_DOCS_GENERATOR_REVISION=17224661d68056b502c50c6c9431efb40aca2b4a \
CODECLEW_DOCS_REVIEW_INDEX=true \
npm run build -- --config ../../rendering/docusaurus.config.mjs
cd ../../..
python3 -I -S documentation/docusaurus/variant.py verify-build --showcase-navigation
python3 -I -S documentation/rendering/build.py --output EMPTY_OUTPUT_DIRECTORY
```

`EMPTY_OUTPUT_DIRECTORY` is a placeholder for a new directory. The single Pages
workflow stages this same composition. No Codeclew product CI or release runs.
The custom page source and its claim map live here, outside replaceable exporter
outputs. The Docusaurus navbar is built through an explicit React-consistent config
overlay; frozen MDX, config and exporter file indexes remain unchanged.

Only native `index.html`, `overview.html` and `catalog.html` gain an entry link
during staging. `rendering/navigation-overlay.json` identifies the exact insertion
and original/result hashes. Removing that insertion reconstructs the original
native bytes, checked for every native file. Producer manifests continue to describe
the frozen originals; this demo-owned composition is recorded separately. Existing
critic reports are not approval of new showcase pages or navigation.

## Real examples and limits

The new bounded examples in `examples/` use the official installed 0.13.48 launcher
and the original immutable Weather capture. Their `demo-receipt.json` retains
producer identity, actual argv with private path placeholders, snapshot/publication,
native status and limits. No source recapture was performed.

- `remote-selected` explicitly selects Save City plus Dashboard and Places. The
  scenario-only attempt omitted a receiving fragment target; automatic closure of
  all authored cross-links is not claimed. Exact GitHub links remain in the payload.
- `questions` changes only the retained Save City plan's presentation to QUESTIONS.
  Its whole-publication result remains PARTIAL because old narrative translation
  coverage is incomplete. Existing STALE/UNASSESSED labels remain. An input plan
  referencing omitted subjects is not silently repaired for selected export.
- MET external-service, interaction and actor input files demonstrate the real
  attempted setup. Materializing a new publication is blocked by incomplete source
  of an unrelated old Dashboard thread. No missing native external page is exposed
  as a working example. See `inputs/external-demo-gap.json`.
- Java operation-queue remains undemonstrated; the real VoltDB sample is
  builder-chain. The unsupported UpdateDeal prototype remains unsupported.

Producer manifests contain a private absolute `output` field. Public copies omit
only that field; their receipts retain the original manifest hash and projection
description. Every referenced generated file retains its original digest. Actual
private commands, failed attempts and complete original manifests remain in local
experiment evidence, not in this public repository.

The custom HTML page and JSON claim map are demo-owned metadata. Checks bind exact
source IDs, revisions, ranges and text digests; they do not create clew registration,
freshness guarantees, semantic validation, meaning approval or runtime evidence.

## Verification scope

`build.py` checks every showcase link/file, static anchors, and recognized dynamic
reader identities against their companion payloads. Thread/contract routes are
checked using the retained router's explicit rules. Browser acceptance separately
exercises dynamic navigation, hydrated Docusaurus navigation and normal/narrow
layouts. The new manifest marks prior acceptance as inapplicable to new pages.

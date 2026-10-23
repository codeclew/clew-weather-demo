# Current Weather documentation

This additive publication uses an official installed Codeclew release to render
the original retained publication with the Markdown and domain-field inputs in
`documentation/markdown-tables`. The original descriptions, field comments and
source evidence remain unchanged. The derived model input appends only the
existing explicit service-to-model navigation associations.

Generate native and Docusaurus exports in fresh directories with the installed
release launcher, then freeze those exact exports with `freeze.py`. Record the
actual release version, public source revision, retained snapshot/publication,
input hashes and independent browser acceptance in the producer JSON.

```sh
python3 -I -S documentation/current/render.py --root DOCS_ROOT --clew INSTALLED_CLEW \
  --version RELEASE_VERSION --release-commit FULL_RELEASE_SHA --output NEW_OUTPUT
python3 -I -S documentation/current/freeze.py --native NEW_OUTPUT/native \
  --export NEW_OUTPUT/docusaurus --producer NEW_OUTPUT/producer.json
```

`verify.py` checks the official release identity, frozen files, both exporter
manifests and all six models' 23 complete fields. The workflow resolves the public
tag and release before building the current MDX project. The only manifest
projection replaces private output staging directories with `.`; the original
manifest digests remain recorded in the producer metadata.

The rendering showcase defaults to the current formats and links the historical
readable-behavior example to the current Markdown table example. Existing historical output,
original evidence and producer identities remain retained.

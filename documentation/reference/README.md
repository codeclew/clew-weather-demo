# Weather reference reader

The reference site uses one selected language, English. The three accepted input
files are preserved byte for byte. `service-model-links.json` adds explicit
navigation from service entities sections to canonical field tables; it changes
no field description, evidence or domain ownership declaration.

After each supported Codeclew release, regenerate this reference as a release
completion step. Use the official installed launcher for the public candidate,
the exact release commit and the retained documentation root recorded by the
publication. Do not reacquire source or re-author descriptions to refresh the UI.

```sh
python3 -I -S documentation/reference/build.py --root DOCS_ROOT \
  --clew clew --generator-commit RELEASE_COMMIT --output NEW_OUTPUT
```

For a local product candidate, pass its supported source launcher and
`--source-checkout PRODUCT_CHECKOUT`. The script requires a clean exact commit.
It preserves the input files, appends service navigation to a derived render
input, calls `docs pages render`, and verifies the resulting native bundle.
Native failures keep their diagnostics and nonzero exit status.

Before promotion, inspect the production reader at desktop and phone widths:
the two opted-in Data Flow views, their field/stage evidence and return links,
all six model field tables, service-to-field navigation and the catalogue.
The static validator cannot establish interactive browser correctness.

Promote the accepted generated files and their `reference-render.json`,
`reference-inputs/` and `reference-checks.json` into `docs/`, preserving the
separately identified historical catalogue examples. Pages validates the exact
release commit/version, frozen publication and snapshot, accepted input hashes,
output manifest, six models, 23 fields and both opted-in process readers before
uploading. An older or incomplete bundle fails this gate and is not deployed.
The workflow does not silently regenerate from a mutable `main` or certify
unreviewed renderer changes.

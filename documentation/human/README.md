# Accepted human-page publication

This optional destination publishes the independently accepted public Weather
human-page export at `/clew-weather-demo/human/`. No output is present until the
authoring/package owner supplies and accepts it. The site does not author prose,
capture sources, install a renderer or infer missing evidence in CI.

After independent content, UI and official-package acceptance, place only the
allowlisted HTML/static files in `site/` and write `publication.json` alongside it:

```json
{
  "schema": "weather-human-publication/1.0",
  "renderer": {
    "version": "RELEASE_VERSION",
    "sourceRevision": "PUBLIC_PRODUCT_COMMIT",
    "skillDigest": "sha256:SKILL_DIGEST",
    "package": "codeclew-macos-arm64.tar.gz",
    "packageSha256": "PACKAGE_SHA256"
  },
  "source": {
    "repository": "https://github.com/codeclew/clew-weather-demo",
    "revision": "PUBLIC_WEATHER_COMMIT"
  },
  "services": ["dashboard", "places", "forecasts"],
  "language": "en",
  "entrypoint": "index.html",
  "filesSha256": {"index.html": "EXACT_ACCEPTED_FILE_SHA256"}
}
```

These placeholders are documentation, not a publishable record. Use the selected
single language and real accepted identities. Do not copy operational roots,
runtime configuration, private paths or evidence stores into this directory.
Original source bindings, full closure and acceptance receipts remain with the
authoring owner. This small public record identifies the accepted published bytes;
it does not replace that provenance or guarantee semantic completeness.

Run `python3 -I -S documentation/human/verify.py --official-release` after supplying
the record. The existing Pages composer verifies and copies it without changing
the export; existing historical preservation and local-link checks still run.
Independent root approval remains a prerequisite for merge and deployment.

## An accepted unreleased skill with an official acquisition runtime

Keep schema `1.0` for historical records where one official package identifies
the renderer/skill. Do not relabel an accepted unreleased skill as that release.
Schema `weather-human-publication/1.1` separates the retained capture, the
official runtime used to read it, the accepted skill/HTML-renderer treatment and
the exact frozen reader-file export:

```json
{
  "schema": "weather-human-publication/1.1",
  "capture": {
    "kind": "retained-snapshot",
    "snapshot": "sha256:RETAINED_SNAPSHOT_DIGEST/RETAINED_SNAPSHOT_SIZE",
    "producerVersion": "HISTORICAL_CAPTURE_VERSION",
    "recaptured": false
  },
  "acquisition": {
    "kind": "official-release",
    "version": "ACQUISITION_RELEASE_VERSION",
    "sourceRevision": "OFFICIAL_RELEASE_COMMIT",
    "package": "codeclew-macos-arm64.tar.gz",
    "packageSha256": "OFFICIAL_PACKAGE_SHA256"
  },
  "treatment": {
    "kind": "accepted-unreleased-skill",
    "repository": "https://github.com/codeclew/codeclew",
    "commit": "EXACT_TREATMENT_COMMIT",
    "tree": "EXACT_TREATMENT_TREE",
    "skillDigest": "sha256:EXACT_SKILL_DIGEST",
    "runtimeVersion": "ACQUISITION_RELEASE_VERSION"
  },
  "export": {
    "kind": "frozen-export",
    "digest": "sha256:EXACT_READER_FILE_MAP_DIGEST",
    "fileCount": 1
  },
  "source": {
    "repository": "https://github.com/codeclew/clew-weather-demo",
    "revision": "PUBLIC_WEATHER_SOURCE_COMMIT"
  },
  "services": ["dashboard", "places", "forecasts"],
  "language": "en",
  "entrypoint": "index.html",
  "filesSha256": {"index.html": "EXACT_ACCEPTED_FILE_SHA256"}
}
```

These placeholders must be replaced with actual retained identities. Use JSON
`null` for `producerVersion` only when the historical producer is unrecorded;
do not substitute the acquisition version or claim recapture. The treatment's
`runtimeVersion` records which acquisition runtime was actually used, not a
product release for the treatment. Its commit must differ from that release
commit. No public availability or official-package authority is implied for the
unreleased treatment. Independent review pins its exact commit/tree/skill digest;
the site does not authenticate it by pretending it belongs to a release archive.

`export.digest` is `sha256:` plus SHA-256 of UTF-8 JSON for `filesSha256`, with
sorted keys, no insignificant whitespace and unescaped Unicode. The existing
`export_digest` helper computes it. Pin that identity from the independently
accepted frozen reader export; do not recompute it to hide content changes.
`fileCount` equals the number of reader files. The public publication record is
not part of that map, avoiding a self-referential hash.

`--official-release` still verifies the public stable acquisition tag, exact
product commit, official package digest and public Weather source commit for
both schemas. The new type cannot bypass those checks, substitute arbitrary
acquisition code or claim a treatment version is official. Local file hashes,
safe paths and workspace-reference rejection apply unchanged. These mechanical
checks do not establish semantic correctness or a completed author visual gate.

Keep only these public identities and reader bytes here. Do not publish local
paths, root review reports, experiment sources, operational caches or dependency
source links. Preserve the previous human export and publication record, as well
as the existing native/Docusaurus/historical variants, when replacing the current
reader destination. Site integration and live verification follow acceptance of
the new export; no binary release or source recapture is implied.

Keep archived human exports under `documentation/human/history/ARCHIVE_ID/`,
with their original reader files and `publication.json` together. The composer
verifies each archive using that record and stages it at `/human-history/ARCHIVE_ID/`.
Do not add archives under `docs/`: that directory is the frozen native export,
whose complete bytes and file inventory must remain unchanged. The same
hash, file inventory, path and publication-record checks apply to source and
staged reader archives; no archived renderer is rerun.

## Assisted export with a separately verified release

Schema `weather-human-publication/1.2` retains the same capture, acquisition,
source and frozen export records. It records `treatment.kind` as
`assisted-retained-export`, with the actual acquisition `runtimeVersion`,
`repository`, `authoring` and `assistance`. It does not assign a later release
version to the historical author invocation.

`authoring.helperFilesSha256` maps relative helper paths to their original
`sha256:` file hashes. `authoring.helperDigest` hashes that map as UTF-8 JSON
with sorted keys, two-space indentation, unescaped Unicode and a final newline.
This is the runner's frozen file-map identity, distinct from the installed skill
digest. `assistance` explicitly records `targetedAuthorRepairs: true`,
`rootDirectedNormalization: true` and `autonomousPass: false`.

The separate `validation` object identifies the final official package using
`kind: official-release`, `version`, `sourceRevision`, `sourceTree`, `package`,
`packageSha256` and `skillDigest`. Under `--official-release`, the guard verifies
both public stable release/tag/package identities, the final commit's actual Git
tree, and the public Weather source. It downloads the declared validation archive,
checks its SHA-256, and reads its bundled skill bytes and modes to verify the
installer's skill digest. It does not extract or execute archive code.

Incomplete validation identities refuse publication. The frozen reader map must
still match exactly; this provenance type does not grant semantic approval or
turn an assisted result into an autonomous author pass. Schemas `1.0` and `1.1`
retain their existing checks for current and archived exports.

`legacyRedirects` pins one previous archive by `archive`, the original record's
`publicationSha256`, its canonical `exportDigest`, and an explicit `files` map.
The map must contain exactly the former HTML paths absent from the new reader,
each pointing to the same archived filename. The composer adds deterministic
redirect stubs only to the staged site, preserving query and fragment. Their
inventory and bytes are checked separately from the unchanged canonical reader
map; unknown targets, missing archives and archive/policy drift refuse staging.

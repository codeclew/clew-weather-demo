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

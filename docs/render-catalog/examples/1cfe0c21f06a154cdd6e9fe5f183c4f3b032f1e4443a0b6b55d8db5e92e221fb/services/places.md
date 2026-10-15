# Places

Static source interpretation. Declared interactions do not establish runtime routing.

## Overview

Describe the service purpose, scope and supported outcomes.

Documentation gap: source-bound section content has not been accepted.

## Responsibilities

Describe responsibilities and exclusions from evidence; business intent may need a human note.

Documentation gap: source-bound section content has not been accepted.

## Domain entities

Identify domain concepts separately from DTOs and storage classes; ownership needs an explicit declaration.

Documentation gap: source-bound section content has not been accepted.

## Ingress contracts

Document discovered public boundaries and declared contracts; retain gaps for unsupported discovery.

Documentation gap: source-bound section content has not been accepted.

## Egress contracts

Document external calls and messages; unresolved destinations and runtime activation remain gaps.

Documentation gap: source-bound section content has not been accepted.

## assessment-runtime-broker-outage

Documentation gap: Behavior is not yet authored. Load this entrypoint with clew docs context and supply a source-bound sequence.

## assessment-weather-readme-instructions

Documentation gap: Behavior is not yet authored. Load this entrypoint with clew docs context and supply a source-bound sequence.

## places-3a33202464c8b4fff218

Documentation gap: Behavior is not yet authored. Load this entrypoint with clew docs context and supply a source-bound sequence.

## places-691b340ea61828b197b6

Documentation gap: Behavior is not yet authored. Load this entrypoint with clew docs context and supply a source-bound sequence.

## places-8a2148bf5e312b0c5947

Documentation gap: Behavior is not yet authored. Load this entrypoint with clew docs context and supply a source-bound sequence.

## places-de7d5796a632782443dc

Documentation gap: Behavior is not yet authored. Load this entrypoint with clew docs context and supply a source-bound sequence.

## places-e06f41e67f62720ad106

Documentation gap: Behavior is not yet authored. Load this entrypoint with clew docs context and supply a source-bound sequence.


## Human note: broker-outage.json

Classification: mixed. Period: 2026-10-13T07:33:08.044370+00:00.

Original captured text (human/imported, unverified):

<pre>{
  &quot;schema&quot;: &quot;clew-weather-runtime-observation/1.0&quot;,
  &quot;id&quot;: &quot;broker-outage&quot;,
  &quot;origin&quot;: &quot;GITHUB_ACTIONS_TEST_OBSERVATION&quot;,
  &quot;compilerEvidence&quot;: false,
  &quot;originalRecordSha256&quot;: &quot;114d2103efc72decc3ad929f2e0efb5eb3530fa71049ede4d7e9a18492e30845&quot;,
  &quot;runUrl&quot;: &quot;https://github.com/codeclew/clew-weather-demo/actions/runs/38363357256&quot;,
  &quot;status&quot;: &quot;PASSED&quot;,
  &quot;sourceRevision&quot;: &quot;d135990a1c8770928d3c7be2274ff60e7f5d75d3&quot;,
  &quot;project&quot;: &quot;clew-weather-outage-431a9af3e8d6&quot;,
  &quot;runnerSha256&quot;: &quot;c36ff8bf2ca8ad555e80a28a8663b7856d3b861bd7c245176ea4b5e78ffb8714&quot;,
  &quot;sourceHashes&quot;: {
    &quot;compose.yaml&quot;: &quot;76d5d8226d233a558b901a06887bcce216e4738778edff8462367d827169c167&quot;,
    &quot;services/places/RequestPublisher.cs&quot;: &quot;1f6e0b7b1d1f54e318bcc903f875407e879ed591e29c0509423525e3772c099e&quot;,
    &quot;services/places/PlacesRepository.cs&quot;: &quot;f77ef5110e62488caaa82deeeb599e33f8063303aad786b8763b1be3b6d5e578&quot;,
    &quot;services/forecasts/src/main/kotlin/weather/Forecasts.kt&quot;: &quot;6ed6406eab325f8de2860e4fc8a0a0afca9499394732dcf9c7115bd8df711fe6&quot;,
    &quot;services/dashboard/src/main.ts&quot;: &quot;24e65777311802d2204bc41eedf3b814e869f777c2e65cb74d5c8be8c4d47e6a&quot;
  },
  &quot;checks&quot;: [
    {
      &quot;case&quot;: &quot;fresh-dashboard-empty&quot;,
      &quot;passed&quot;: true,
      &quot;observed&quot;: {}
    },
    {
      &quot;case&quot;: &quot;save-commits-with-broker-down&quot;,
      &quot;passed&quot;: true,
      &quot;observed&quot;: {
        &quot;status&quot;: 200,
        &quot;body&quot;: {
          &quot;id&quot;: &quot;oslo&quot;,
          &quot;name&quot;: &quot;Oslo&quot;,
          &quot;latitude&quot;: 59.93,
          &quot;longitude&quot;: 10.72
        }
      }
    },
    {
      &quot;case&quot;: &quot;outbox-retained-unpublished-after-producer-timeout&quot;,
      &quot;passed&quot;: true,
      &quot;observed&quot;: {
        &quot;outbox&quot;: 1,
        &quot;published&quot;: 0
      }
    },
    {
      &quot;case&quot;: &quot;places-health-does-not-attest-broker&quot;,
      &quot;passed&quot;: true,
      &quot;observed&quot;: {
        &quot;status&quot;: 200,
        &quot;body&quot;: {
          &quot;database&quot;: &quot;READY&quot;
        }
      }
    },
    {
      &quot;case&quot;: &quot;duplicate-save-does-not-create-another-outbox-row&quot;,
      &quot;passed&quot;: true,
      &quot;observed&quot;: {
        &quot;response&quot;: {
          &quot;status&quot;: 200,
          &quot;body&quot;: {
            &quot;id&quot;: &quot;oslo&quot;,
            &quot;name&quot;: &quot;Oslo&quot;,
            &quot;latitude&quot;: 59.93,
            &quot;longitude&quot;: 10.72
          }
        },
        &quot;counts&quot;: {
          &quot;outbox&quot;: 1,
          &quot;published&quot;: 0
        }
      }
    },
    {
      &quot;case&quot;: &quot;broker-recovery-delivers-through-all-three-services&quot;,
      &quot;passed&quot;: true,
      &quot;observed&quot;: {
        &quot;counts&quot;: {
          &quot;outbox&quot;: 1,
          &quot;published&quot;: 1
        },
        &quot;card&quot;: {
          &quot;id&quot;: &quot;oslo&quot;,
          &quot;name&quot;: &quot;Oslo&quot;,
          &quot;latitude&quot;: 59.93,
          &quot;longitude&quot;: 10.72,
          &quot;forecast&quot;: {
            &quot;mode&quot;: &quot;fixture&quot;,
            &quot;periods&quot;: [
              {
                &quot;time&quot;: &quot;2026-10-12T20:00:00Z&quot;,
                &quot;symbol&quot;: &quot;fair_night&quot;,
                &quot;temperatureC&quot;: 2,
                &quot;precipitationMm&quot;: 0
              },
              {
                &quot;time&quot;: &quot;2026-10-12T21:00:00Z&quot;,
                &quot;symbol&quot;: &quot;partlycloudy_night&quot;,
                &quot;temperatureC&quot;: 2.3,
                &quot;precipitationMm&quot;: 0
              },
              {
                &quot;time&quot;: &quot;2026-10-12T22:00:00Z&quot;,
                &quot;symbol&quot;: &quot;cloudy&quot;,
                &quot;temperatureC&quot;: 2.6,
                &quot;precipitationMm&quot;: 0
              },
              {
                &quot;time&quot;: &quot;2026-10-12T23:00:00Z&quot;,
                &quot;symbol&quot;: &quot;cloudy&quot;,
                &quot;temperatureC&quot;: 2.6,
                &quot;precipitationMm&quot;: 0
              },
              {
                &quot;time&quot;: &quot;2026-10-13T00:00:00Z&quot;,
                &quot;symbol&quot;: &quot;cloudy&quot;,
                &quot;temperatureC&quot;: 2.5,
                &quot;precipitationMm&quot;: 0
              },
              {
                &quot;time&quot;: &quot;2026-10-13T01:00:00Z&quot;,
                &quot;symbol&quot;: &quot;cloudy&quot;,
                &quot;temperatureC&quot;: 2.4,
                &quot;precipitationMm&quot;: 0
              }
            ],
            &quot;fetchedAt&quot;: &quot;2026-10-13T07:34:47.468329316Z&quot;,
            &quot;updatedAt&quot;: &quot;2026-10-12T20:34:59Z&quot;
          }
        }
      }
    },
    {
      &quot;case&quot;: &quot;publisher-recorded-retry&quot;,
      &quot;passed&quot;: true,
      &quot;observed&quot;: {
        &quot;retryMarkerPresent&quot;: true
      }
    }
  ],
  &quot;startedAt&quot;: &quot;2026-10-13T07:33:08.044370+00:00&quot;,
  &quot;cleanup&quot;: &quot;COMPLETED_OWN_PROJECT_ONLY&quot;,
  &quot;finishedAt&quot;: &quot;2026-10-13T07:35:22.322626+00:00&quot;
}
</pre>

<details><summary>Original metadata and associations</summary><pre>{
  &quot;classification&quot;: &quot;mixed&quot;,
  &quot;id&quot;: &quot;runtime-broker-outage&quot;,
  &quot;metadata&quot;: {
    &quot;compilerEvidence&quot;: false,
    &quot;sourceSha256&quot;: &quot;e870c5d480cc89c45d5feeaf9154f7397402152b9131599b239c65fe2b810fbb&quot;
  },
  &quot;path&quot;: &quot;notes/runtime-broker-outage-cloud-v1.md&quot;,
  &quot;period&quot;: &quot;2026-10-13T07:33:08.044370+00:00&quot;,
  &quot;schema&quot;: &quot;codeclew-documentation-note-association/1.0&quot;,
  &quot;service&quot;: &quot;places&quot;,
  &quot;tags&quot;: [
    &quot;imported-context&quot;
  ],
  &quot;targets&quot;: [
    &quot;service:places/section-overview&quot;
  ],
  &quot;title&quot;: &quot;broker-outage.json&quot;
}</pre></details>

Separate agent assessment: UNASSESSED.


## Human note: Weather demo README operational instructions

Classification: mixed. Period: source commit 6bceb663d27860e1edd8155f796cee6f696c0fdc.

Original captured text (human/imported, unverified):

<pre># Run the fixture and capture evidence

The weather demo source repository is https://github.com/codeclew/clew-weather-demo. Native threaded documentation requires an official installed Codeclew release 0.13.29 or newer; full scenario bodies require 0.13.32 or newer. The weather documentation reader URL is https://codeclew.github.io/clew-weather-demo/index.html. Use a clean attached checkout, a fresh documentation root outside it with an existing parent, and fresh capture receipts. Restore services/places/Places.csproj with the .NET 10 SDK before capture; Kotlin and TypeScript declarations use source-syntax evidence. Capture does not author prose or import old cache.

For the local fixture, use Docker Compose v2 and free ports 8080 through 8082. Start:

```sh
FORECAST_MODE=fixture docker compose -p clew-weather-demo up --build -d
```

Open http://127.0.0.1:8080. Fixture cities are Oslo, Helsinki, and Lisbon; fixture mode does not use live-provider data. Stop:

```sh
docker compose -p clew-weather-demo down
```


Capture with the installed launcher:

```sh
python3 -I -S -B documentation/capture.py --root /absolute/new-docs-root --clew clew --include-observations --include-processes
```

Set CODECLEW_HOME to the state directory recorded beneath the fresh capture receipts, for example: export CODECLEW_HOME=/absolute/new-docs-root-capture-receipts/state. The local application is separate from the native documentation reader. Work preparation binds to the explicit saved snapshot and retained evidence; it never falls back to source acquisition.

## Recompose, publish, and render the guide

Use one Work request per service: documentation/work/places-overview.json, documentation/work/forecasts-overview.json, and documentation/work/dashboard-overview.json. Prepare each Work against CAPTURE_SNAPSHOT (receipt snapshot); sourceCaptureSnapshot holds the original source handle for post-publication recompose. Use the returned WORK_ID to read its references and follow every nextCursor through null. Author a new proposal from those recorded reads; do not copy prior prose or cache.

Example:

```sh
clew docs work prepare --root /absolute/new-docs-root --subject service:dashboard --input documentation/work/dashboard-overview.json --snapshot CAPTURE_SNAPSHOT
clew docs work read --root /absolute/new-docs-root --work WORK_ID --input selection.json
clew docs proposal submit --root /absolute/new-docs-root --work WORK_ID --input proposal.json
```

Publish only a machine-ready proposal with its returned ID:

```sh
clew docs proposal publish --root /absolute/new-docs-root --proposal PROPOSAL_ID --unassessed
```

The --unassessed option leaves meaning review unassessed. Open the index path returned by proposal publish in a local browser. For an additional render after publication, recompose from the original source handle, SOURCE_CAPTURE_SNAPSHOT (the receipt field sourceCaptureSnapshot), not from CAPTURE_SNAPSHOT:

```sh
clew docs recompose --root /absolute/new-docs-root --snapshot SOURCE_CAPTURE_SNAPSHOT
```

Use the returned POST_PUBLICATION_SNAPSHOT for rendering:

```sh
clew docs render --root /absolute/new-docs-root --snapshot POST_PUBLICATION_SNAPSHOT --language en
```

The render --publish flag records a local released snapshot/history; it does not upload the site or make it available online.

The C# capture is PARTIAL; Kotlin and TypeScript source-syntax records are not runtime proof. Imported runtime observations retain their own provenance and do not verify this capture; fresh-clone verification of new prose is separate. Use your configured model and provider; no Codeclew-hosted model or paid API is required.
</pre>

<details><summary>Original metadata and associations</summary><pre>{
  &quot;classification&quot;: &quot;mixed&quot;,
  &quot;id&quot;: &quot;weather-readme-instructions&quot;,
  &quot;metadata&quot;: {
    &quot;author&quot;: &quot;codeclew/clew-weather-demo README contributors (imported Git source)&quot;,
    &quot;sourceCommit&quot;: &quot;6bceb663d27860e1edd8155f796cee6f696c0fdc&quot;,
    &quot;sourcePath&quot;: &quot;README.md&quot;
  },
  &quot;path&quot;: &quot;notes/weather-readme-instructions.md&quot;,
  &quot;period&quot;: &quot;source commit 6bceb663d27860e1edd8155f796cee6f696c0fdc&quot;,
  &quot;schema&quot;: &quot;codeclew-documentation-note-association/1.0&quot;,
  &quot;service&quot;: &quot;places&quot;,
  &quot;tags&quot;: [
    &quot;imported-context&quot;,
    &quot;render-catalog&quot;
  ],
  &quot;targets&quot;: [
    &quot;service:places/section-overview&quot;
  ],
  &quot;title&quot;: &quot;Weather demo README operational instructions&quot;
}</pre></details>

Separate agent assessment: UNASSESSED.


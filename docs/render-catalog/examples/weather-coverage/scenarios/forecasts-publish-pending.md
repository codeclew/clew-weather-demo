# Publish pending forecast updates

Static source interpretation. Declared interactions do not establish runtime routing.

## forecasts-publish-pending

Documentation gap: Behavior is not yet authored. Load this entrypoint with clew docs context and supply a source-bound sequence.

## process-overview

Documentation gap: Behavior is not yet authored. Load this entrypoint with clew docs context and supply a source-bound sequence.


## Saved process definition

Explicit requested scope and outcomes; source support is assessed separately.

Scope: Forecasts.publishPending outbox selection, broker send, and database publication marking.

Trigger: The source-declared publishPending entrypoint is invoked; runtime scheduling activation is unverified.

participants:

- forecasts
- dashboard

objects:


outcomes:

- No pending row returns without publishing. A selected row is sent to Kafka and marked in the database transaction; failure or a crash can leave it eligible for replay.

### Linked child views: captured versions

- [dashboard-forecast-updated-consumer](dashboard-forecast-updated-consumer.md): LINKED_PROCESS_UNASSESSED

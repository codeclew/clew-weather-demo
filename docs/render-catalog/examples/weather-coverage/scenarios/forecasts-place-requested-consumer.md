# Forecasts place-requested consumer

Static source interpretation. Declared interactions do not establish runtime routing.

## forecasts-place-requested-consumer

Documentation gap: Behavior is not yet authored. Load this entrypoint with clew docs context and supply a source-bound sequence.

## process-overview

Documentation gap: Behavior is not yet authored. Load this entrypoint with clew docs context and supply a source-bound sequence.


## Saved process definition

Explicit requested scope and outcomes; source support is assessed separately.

Scope: Forecasts.consume is the source-declared KafkaListener for weather.place-requested; its rejection, inbox transaction, and acknowledgment behavior remains described by the accepted service operation.

Trigger: The source-declared weather.place-requested listener invokes Forecasts.consume; runtime activation and message delivery are unverified.

participants:

- forecasts

objects:


outcomes:

- The consumer node links to the shared Forecasts refresh and publishing views; those links do not establish cross-process order, transaction atomicity, acknowledgment timing, or delivery.

### Linked child views: captured versions

- [forecasts-publish-pending](forecasts-publish-pending.md): LINKED_PROCESS_UNASSESSED
- [forecasts-refresh-scheduled](forecasts-refresh-scheduled.md): LINKED_PROCESS_UNASSESSED

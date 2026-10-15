# Publish pending place requests

Static source interpretation. Declared interactions do not establish runtime routing.

## places-request-publisher

Documentation gap: Behavior is not yet authored. Load this entrypoint with clew docs context and supply a source-bound sequence.

## process-overview

Documentation gap: Behavior is not yet authored. Load this entrypoint with clew docs context and supply a source-bound sequence.


## Saved process definition

Explicit requested scope and outcomes; source support is assessed separately.

Scope: RequestPublisher.ExecuteAsync and its source-level outbox publishing operation.

Trigger: ExecuteAsync receives a cancellation token and enters its publisher loop.

participants:

- places
- forecasts
- dashboard

objects:


outcomes:

- If an unpublished request row is selected, send its payload to weather.place-requested and then mark that outbox row published in the database transaction.
- If no unpublished row is available, the publish operation returns without sending a message.
- Other observed failures are logged for retry; the source alone does not establish that the hosted service is activated at runtime.

### Linked child views: captured versions

- [dashboard-place-requested-consumer](dashboard-place-requested-consumer.md): LINKED_PROCESS_UNASSESSED
- [forecasts-place-requested-consumer](forecasts-place-requested-consumer.md): LINKED_PROCESS_UNASSESSED

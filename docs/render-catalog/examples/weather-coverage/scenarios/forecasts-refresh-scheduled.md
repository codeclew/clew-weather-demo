# Refresh cached and provider forecasts

Static source interpretation. Declared interactions do not establish runtime routing.

## forecasts-refresh-scheduled

Documentation gap: Behavior is not yet authored. Load this entrypoint with clew docs context and supply a source-bound sequence.

## process-overview

Documentation gap: Behavior is not yet authored. Load this entrypoint with clew docs context and supply a source-bound sequence.


## Saved process definition

Explicit requested scope and outcomes; source support is assessed separately.

Scope: Forecasts.refreshExpired and the shared Forecasts.refresh provider/cache/persistence path.

Trigger: The source-declared refreshExpired entrypoint is invoked; whether the scheduler activates it at runtime is not established by this snapshot.

participants:

- forecasts

objects:


outcomes:

- Retain the source-described missing/expired selection, cached return, fixture/live provider, response and transform branches, and persistence/outbox outcomes.

### Linked child views: captured versions

- [forecasts-publish-pending](forecasts-publish-pending.md): LINKED_PROCESS_UNASSESSED

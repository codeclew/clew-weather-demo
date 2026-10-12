type Place = { id: string; name: string; latitude: number; longitude: number }
type Period = { time: string; temperatureC: number; precipitationMm: number | null; symbol: string }
type Forecast = { updatedAt: string; fetchedAt: string; mode: 'fixture' | 'live'; periods: Period[] }
type Event = { id: string; type: string; version: number; place: Place; forecast?: Forecast }

export function validateEvent(value: unknown, topic: string): Event {
  if (!value || typeof value !== 'object') throw new Error('INVALID_EVENT')
  const event = value as Event
  if (typeof event.id !== 'string' || event.version !== 1 || !event.place || typeof event.place.id !== 'string'
      || !['oslo', 'helsinki', 'lisbon'].includes(event.place.id) || typeof event.place.name !== 'string'
      || !Number.isFinite(event.place.latitude) || !Number.isFinite(event.place.longitude)) throw new Error('INVALID_EVENT')
  if (topic === 'weather.forecast-updated') {
    if (event.type !== 'forecast.updated' || !event.forecast || !Number.isFinite(Date.parse(event.forecast.updatedAt))
        || !Number.isFinite(Date.parse(event.forecast.fetchedAt)) || !['fixture', 'live'].includes(event.forecast.mode)
        || !Array.isArray(event.forecast.periods) || event.forecast.periods.length < 1 || event.forecast.periods.length > 6) throw new Error('INVALID_FORECAST')
    for (const period of event.forecast.periods) {
      if (!Number.isFinite(Date.parse(period.time)) || !Number.isFinite(period.temperatureC)
          || !(period.precipitationMm === null || (Number.isFinite(period.precipitationMm) && period.precipitationMm >= 0))
          || typeof period.symbol !== 'string') throw new Error('INVALID_PERIOD')
    }
  } else if (event.type !== 'place.requested') throw new Error('INVALID_PLACE_EVENT')
  return event
}


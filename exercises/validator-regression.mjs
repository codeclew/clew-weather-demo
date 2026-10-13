import assert from 'node:assert/strict'
import { validateEvent as original } from './unchecked-place-forecast.ts'
import { validateEvent as corrected } from '../services/dashboard/src/events.ts'

const place = { id: 'oslo', name: 'Oslo', latitude: 59.91, longitude: 10.75 }
const request = { id: 'validator-regression', type: 'place.requested', version: 1, place }
const unchecked = { ...request, forecast: { arbitrary: 'unchecked' } }
assert.equal(original(unchecked, 'weather.place-requested'), unchecked)
assert.throws(() => corrected(unchecked, 'weather.place-requested'), /INVALID_PLACE_EVENT/)
assert.equal(corrected(request, 'weather.place-requested'), request)
assert.throws(() => corrected(request, 'unknown-topic'), /UNKNOWN_TOPIC/)

const timestamp = '2026-10-12T12:00:00Z'
const forecast = {
  id: 'forecast-regression', type: 'forecast.updated', version: 1, place,
  forecast: { updatedAt: timestamp, fetchedAt: timestamp, mode: 'fixture', periods: [
    { time: timestamp, temperatureC: 0, precipitationMm: null, symbol: 'cloudy' }
  ] }
}
assert.equal(corrected(forecast, 'weather.forecast-updated'), forecast)
assert.throws(() => corrected({ ...forecast, forecast: { ...forecast.forecast, updatedAt: 0 } },
  'weather.forecast-updated'), /INVALID_FORECAST/)
console.log(JSON.stringify({ status: 'PASSED', assertions: 6, runtime: process.version }))

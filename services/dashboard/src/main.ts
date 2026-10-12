import Fastify, { type FastifyRequest, type FastifyReply } from 'fastify'
import pg from 'pg'
import { Kafka, type EachMessagePayload } from 'kafkajs'
import { readFile } from 'node:fs/promises'

const app = Fastify({ logger: true })
const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL })
const kafka = new Kafka({ clientId: 'weather-dashboard', brokers: [process.env.KAFKA_BOOTSTRAP ?? 'kafka:9092'] })
const consumer = kafka.consumer({ groupId: 'weather-dashboard-v1' })
const placesUrl = process.env.PLACES_URL ?? 'http://places:8080'
let consumerReady = false

import { validateEvent, type Event } from './events.js'

export async function applyEvent(event: Event): Promise<string> {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    const inserted = await client.query('INSERT INTO inbox(event_id) VALUES($1) ON CONFLICT DO NOTHING RETURNING event_id', [event.id])
    if (inserted.rowCount === 0) {
      await client.query('COMMIT')
      return 'DUPLICATE'
    }
    let result
    if (event.type === 'forecast.updated' && event.forecast) {
      result = await client.query(`INSERT INTO weather_cards(place_id,name,latitude,longitude,updated_at,forecast)
        VALUES($1,$2,$3,$4,$5,$6) ON CONFLICT(place_id) DO UPDATE SET
        name=EXCLUDED.name,latitude=EXCLUDED.latitude,longitude=EXCLUDED.longitude,
        updated_at=EXCLUDED.updated_at,forecast=EXCLUDED.forecast
        WHERE weather_cards.updated_at IS NULL OR EXCLUDED.updated_at > weather_cards.updated_at`,
      [event.place.id, event.place.name, event.place.latitude, event.place.longitude, event.forecast.updatedAt, JSON.stringify(event.forecast)])
    } else {
      result = await client.query(`INSERT INTO weather_cards(place_id,name,latitude,longitude) VALUES($1,$2,$3,$4)
        ON CONFLICT(place_id) DO UPDATE SET name=EXCLUDED.name,latitude=EXCLUDED.latitude,longitude=EXCLUDED.longitude`,
      [event.place.id, event.place.name, event.place.latitude, event.place.longitude])
    }
    await client.query('COMMIT')
    return result.rowCount === 0 ? 'OLDER_OR_EQUAL' : 'APPLIED'
  } catch (error) {
    await client.query('ROLLBACK')
    throw error
  } finally {
    client.release()
  }
}

export async function consumeMessage(payload: EachMessagePayload): Promise<void> {
  const { topic, partition, message } = payload
  let event
  try {
    event = validateEvent(JSON.parse(message.value?.toString() ?? ''), topic)
  } catch {
    await pool.query(`INSERT INTO rejected_messages(topic,partition_id,offset_id,reason) VALUES($1,$2,$3,'INVALID_EVENT')
      ON CONFLICT DO NOTHING`, [topic, partition, message.offset])
    await consumer.commitOffsets([{ topic, partition, offset: (BigInt(message.offset) + 1n).toString() }])
    return
  }
  await applyEvent(event)
  await consumer.commitOffsets([{ topic, partition, offset: (BigInt(message.offset) + 1n).toString() }])
}

export async function getWeather(): Promise<unknown[]> {
  const result = await pool.query('SELECT place_id AS id,name,latitude,longitude,forecast FROM weather_cards ORDER BY name')
  return result.rows
}

export async function savePlace(request: FastifyRequest, reply: FastifyReply): Promise<void> {
  try {
    const response = await fetch(`${placesUrl}/places`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(request.body), signal: AbortSignal.timeout(10000) })
    reply.code(response.status).send(await response.json())
  } catch {
    reply.code(503).send({ error: 'PLACES_UNAVAILABLE' })
  }
}

export async function requestRefresh(request: FastifyRequest<{ Params: { id: string } }>, reply: FastifyReply): Promise<void> {
  try {
    const response = await fetch(`${placesUrl}/places/${encodeURIComponent(request.params.id)}/refresh`, { method: 'POST', signal: AbortSignal.timeout(10000) })
    reply.code(response.status).send(await response.json())
  } catch {
    reply.code(503).send({ error: 'PLACES_UNAVAILABLE' })
  }
}

export async function getHealth(): Promise<{ database: string; kafka: string }> {
  await pool.query('SELECT 1')
  if (!consumerReady) throw new Error('KAFKA_NOT_READY')
  return { database: 'READY', kafka: 'READY' }
}

export async function getOpenApi(): Promise<unknown> {
  return JSON.parse(await readFile('/app/contracts/dashboard.openapi.json', 'utf8'))
}

export async function getHome(_request: FastifyRequest, reply: import('fastify').FastifyReply): Promise<void> {
  reply.type('text/html').send(await readFile('/app/services/dashboard/public/index.html', 'utf8'))
}

export async function start(): Promise<void> {
  await consumer.connect()
  await consumer.subscribe({ topics: ['weather.place-requested', 'weather.forecast-updated'], fromBeginning: true })
  await consumer.run({ autoCommit: false, eachMessage: consumeMessage })
  consumerReady = true
  app.get('/api/weather', getWeather)
  app.post('/api/places', savePlace)
  app.post<{ Params: { id: string } }>('/api/places/:id/refresh', requestRefresh)
  app.get('/health', getHealth)
  app.get('/openapi.json', getOpenApi)
  app.get('/', getHome)
  await app.listen({ port: Number(process.env.PORT ?? 8080), host: '0.0.0.0' })
}

await start()

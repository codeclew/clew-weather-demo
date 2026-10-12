using Confluent.Kafka;
using Npgsql;
using System.Text.Json;
namespace Weather.Places;
public class RequestPublisher(PlacesRepository repository, ILogger<RequestPublisher> logger) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken token)
    {
        using var producer = new ProducerBuilder<string, string>(new ProducerConfig { BootstrapServers = Environment.GetEnvironmentVariable("KAFKA_BOOTSTRAP") ?? "kafka:9092", EnableIdempotence = true, MessageTimeoutMs = 10000 }).Build();
        while (!token.IsCancellationRequested)
        {
            try { await PublishPending(producer, token); }
            catch (OperationCanceledException) when (token.IsCancellationRequested) { break; }
            catch (Exception error) { logger.LogWarning(error, "PUBLISH_RETRY"); }
            await Task.Delay(1000, token);
        }
    }
    public async Task PublishPending(IProducer<string, string> producer, CancellationToken token)
    {
        await using var connection = await repository.Open(token);
        await using var transaction = await connection.BeginTransactionAsync(token);
        await using var command = new NpgsqlCommand("SELECT id,payload::text FROM request_outbox WHERE NOT published ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED", connection, transaction);
        Guid id; string payload;
        await using (var reader = await command.ExecuteReaderAsync(token))
        {
            if (!await reader.ReadAsync(token)) return;
            id = reader.GetGuid(0); payload = reader.GetString(1);
        }
        var placeId = JsonDocument.Parse(payload).RootElement.GetProperty("place").GetProperty("id").GetString()!;
        await producer.ProduceAsync("weather.place-requested", new Message<string, string> { Key = placeId, Value = payload }, token);
        await using var mark = new NpgsqlCommand("UPDATE request_outbox SET published=true WHERE id=$1", connection, transaction);
        mark.Parameters.AddWithValue(id); await mark.ExecuteNonQueryAsync(token);
        await transaction.CommitAsync(token);
    }
}

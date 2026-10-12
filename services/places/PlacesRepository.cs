using Npgsql;
using System.Text.Json;
namespace Weather.Places;
public class PlacesRepository
{
    private readonly string connectionString = Environment.GetEnvironmentVariable("DATABASE_URL") ?? throw new InvalidOperationException("DATABASE_URL_REQUIRED");
    public static Place? City(string id) => id switch
    {
        "oslo" => new("oslo", "Oslo", 59.93, 10.72),
        "helsinki" => new("helsinki", "Helsinki", 60.17, 24.94),
        "lisbon" => new("lisbon", "Lisbon", 38.72, -9.14),
        _ => null
    };
    public async Task Ping(CancellationToken token)
    {
        await using var connection = await Open(token);
        await using var command = new NpgsqlCommand("SELECT 1", connection);
        await command.ExecuteScalarAsync(token);
    }
    public async Task<NpgsqlConnection> Open(CancellationToken token)
    {
        var connection = new NpgsqlConnection(connectionString);
        try { await connection.OpenAsync(token); return connection; }
        catch { await connection.DisposeAsync(); throw; }
    }
    public async Task<IReadOnlyList<Place>> List(CancellationToken token)
    {
        await using var connection = await Open(token);
        await using var command = new NpgsqlCommand("SELECT id,name,latitude,longitude FROM places ORDER BY name", connection);
        await using var reader = await command.ExecuteReaderAsync(token);
        var result = new List<Place>();
        while (await reader.ReadAsync(token)) result.Add(new(reader.GetString(0), reader.GetString(1), reader.GetDouble(2), reader.GetDouble(3)));
        return result;
    }
    public async Task<Place?> Find(string id, CancellationToken token) => (await List(token)).FirstOrDefault(place => place.Id == id);
    public async Task Save(Place city, CancellationToken token)
    {
        await using var connection = await Open(token);
        await using var transaction = await connection.BeginTransactionAsync(token);
        await using var command = new NpgsqlCommand("INSERT INTO places(id,name,latitude,longitude) VALUES($1,$2,$3,$4) ON CONFLICT DO NOTHING RETURNING id", connection, transaction);
        command.Parameters.AddWithValue(city.Id); command.Parameters.AddWithValue(city.Name); command.Parameters.AddWithValue(city.Latitude); command.Parameters.AddWithValue(city.Longitude);
        if (await command.ExecuteScalarAsync(token) is not null) await InsertRequest(connection, transaction, city, token);
        await transaction.CommitAsync(token);
    }
    public async Task Enqueue(Place city, CancellationToken token)
    {
        await using var connection = await Open(token);
        await using var transaction = await connection.BeginTransactionAsync(token);
        await InsertRequest(connection, transaction, city, token);
        await transaction.CommitAsync(token);
    }
    private static async Task InsertRequest(NpgsqlConnection connection, NpgsqlTransaction transaction, Place city, CancellationToken token)
    {
        var id = Guid.NewGuid();
        var json = JsonSerializer.Serialize(new { id, type = "place.requested", version = 1, place = city }, new JsonSerializerOptions(JsonSerializerDefaults.Web));
        await using var command = new NpgsqlCommand("INSERT INTO request_outbox(id,payload) VALUES($1,$2::jsonb)", connection, transaction);
        command.Parameters.AddWithValue(id); command.Parameters.AddWithValue(json);
        await command.ExecuteNonQueryAsync(token);
    }
}

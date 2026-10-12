using Microsoft.AspNetCore.Mvc;
namespace Weather.Places;
public record Place(string Id, string Name, double Latitude, double Longitude);
public record SavePlace(string CityId);
[ApiController]
public class PlacesController(PlacesRepository repository) : ControllerBase
{
    [HttpGet("/places")]
    public async Task<IReadOnlyList<Place>> List(CancellationToken token) => await repository.List(token);
    [HttpPost("/places")]
    public async Task<IActionResult> Save([FromBody] SavePlace request, CancellationToken token)
    {
        var city = PlacesRepository.City(request.CityId);
        if (city is null) return BadRequest(new { error = "UNSUPPORTED_CITY" });
        await repository.Save(city, token);
        return Ok(city);
    }
    [HttpPost("/places/{id}/refresh")]
    public async Task<IActionResult> Refresh(string id, CancellationToken token)
    {
        var city = await repository.Find(id, token);
        if (city is null) return NotFound(new { error = "PLACE_NOT_FOUND" });
        await repository.Enqueue(city, token);
        return Accepted(new { placeId = id, status = "QUEUED" });
    }
    [HttpGet("/health")]
    public async Task<IActionResult> Health(CancellationToken token)
    {
        await repository.Ping(token);
        return Ok(new { database = "READY" });
    }
    [HttpGet("/openapi.json")]
    public async Task<IActionResult> OpenApi(CancellationToken token) => Content(await System.IO.File.ReadAllTextAsync("/app/contracts/places.openapi.json", token), "application/json");
}

# PlacesController\.Save: lookup, save, and response

> **DRAFT / UNREVIEWED / NOT PUBLISHED** Structure and evidence\-label binding were validated\. Semantic correctness was not reviewed\.

<nav>**Contents:** [ Internal process explanation ](#ordered-behavior) · [ Process outline ](#process-outline) · [ Authored pseudocode ](#authored-pseudocode) · [ Source\-local process projection ](#source-process-projection) · [ Full summary ](#summary)</nav>

## Uncertainties

- The packet contains no SavePlace or Place declarations, so it does not establish whether CityId, Id, Name, Latitude, and Longitude are fields or properties, nor how constructor arguments correspond to declared members\.
- The retained capture is partial source and provider evidence, not a runtime trace\. It does not establish a particular request's lookup or database result, completion of the insert or commit, or which controller result occurs at runtime\.

<a id="process-outline"></a>
## Process outline

1. [**action:** PlacesController\.Save reads request\.CityId and passes it to PlacesRepository\.City to produce city\.](#block-lookup_city)
2. [**decision:** The null check selects BadRequest for a null lookup; otherwise the method saves the Place and reaches Ok after the awaited save returns normally\.](#block-city_null_branch)
3. [**action:** The City source constructs Place values from the three listed literal tuples\. The packet supports these constructor arguments and later member accesses, but does not include the Place declaration\.](#block-city_lookup)

<a id="authored-pseudocode"></a>
## Authored pseudocode

Structure and branch order follow the supplied answer steps.

- [**action:** PlacesController\.Save reads request\.CityId and passes it to PlacesRepository\.City to produce ci…](#block-lookup_city)
- [**decision:** city is null](#block-city_null_branch)
- _Scope 1 — When the condition holds_
- [**return:** For a null city, the method returns the result of BadRequest with \`\{ error = "UNSUPPORTED\_CITY"…](#block-unsupported_city)
- _End Scope 1_
- _Scope 2 — When the condition does not hold_
- [**action:** For a non\-null city, the controller awaits repository\.Save\(city, token\)\. Its source passes city…](#block-save_place)
- _Scope 3 — Following substeps_
- [**action:** PlacesRepository\.Save opens a connection and transaction, prepares an INSERT into places with c…](#block-bind_place_values) _Scope 3_
- [**decision:** insert result is not null](#block-outbox_condition) _Scope 3_
- _Scope 4 — When the condition holds_
- [**action:** InsertRequest creates an ID and serializes an anonymous object containing id, type \`place\.reque…](#block-write_request) _Scope 4_
- _End Scope 4_
- _Scope 5 — When the condition does not hold_
- [**action:** On the null branch, the source skips InsertRequest\.](#block-skip_request) _Scope 5_
- _End Scope 5_
- [**action:** After the conditional, the source awaits CommitAsync\(token\)\.](#block-commit_transaction) _Scope 3_
- _End Scope 3_
- [**return:** After the awaited save, the method returns the result of Ok\(city\)\.](#block-success_result)
- _End Scope 2_
- [**action:** The City source constructs Place values from the three listed literal tuples\. The packet suppor…](#block-city_lookup)

<a id="source-process-projection"></a>
## Source\-local process projection

Built from retained source syntax; this is not execution evidence\.

### Parsed source outline

```text
Entry: Save(request, token)
[W] city = PlacesRepository.City(request.CityId)
[D] if (city is null) then
  return BadRequest(new { error = "UNSUPPORTED_CITY" })
await repository.Save(city, token)
return Ok(city)

```

[Editable PlantUML](process-flow.puml)

**source:** [``s921``](#source-5)

[Rendered SVG](process-flow.svg)

<a id="ordered-behavior"></a>
## Internal process explanation

<a id="block-lookup_city"></a>1. **action:** PlacesController\.Save reads request\.CityId and passes it to PlacesRepository\.City to produce city\.
<a id="block-city_null_branch"></a>2. **decision:** [city is null](#predicate-city_null)
  **When the condition holds:**
<a id="block-unsupported_city"></a>   - **return:** For a null city, the method returns the result of BadRequest with \`\{ error = "UNSUPPORTED\_CITY" \}\`\.
  **When the condition does not hold:**
<a id="block-save_place"></a>   - **action:** For a non\-null city, the controller awaits repository\.Save\(city, token\)\. Its source passes city\.Id, city\.Name, city\.Latitude, and city\.Longitude as the places INSERT values; the repository source conditionally calls InsertRequest and then awaits the transaction commit\.
     **Following substeps:**
<a id="block-bind_place_values"></a>      - **action:** PlacesRepository\.Save opens a connection and transaction, prepares an INSERT into places with columns id, name, latitude, longitude, and supplies city\.Id, city\.Name, city\.Latitude, city\.Longitude to AddWithValue in that source order\.
<a id="block-outbox_condition"></a>      - **decision:** [insert result is not null](#predicate-insert_result_nonnull)
        **When the condition holds:**
<a id="block-write_request"></a>         - **action:** InsertRequest creates an ID and serializes an anonymous object containing id, type \`place\.requested\`, version 1, and place = city with JsonSerializerDefaults\.Web\. It prepares an INSERT into request\_outbox with id and payload, supplies the ID and serialized JSON, and awaits ExecuteNonQueryAsync\(token\)\.
        **When the condition does not hold:**
<a id="block-skip_request"></a>         - **action:** On the null branch, the source skips InsertRequest\.
<a id="block-commit_transaction"></a>      - **action:** After the conditional, the source awaits CommitAsync\(token\)\.
<a id="block-success_result"></a>   - **return:** After the awaited save, the method returns the result of Ok\(city\)\.
<a id="block-city_lookup"></a>3. **action:** The City source constructs Place values from the three listed literal tuples\. The packet supports these constructor arguments and later member accesses, but does not include the Place declaration\.
<a id="semantic-predicates"></a>
### Condition meaning and source checks

<details>
<summary id="predicate-city_null">city is null</summary>

**Condition meaning:** A null lookup selects the unsupported\-city result\. A non\-null Place continues to repository\.Save, then to Ok if that await returns normally\.<details class="citations"><summary>Evidence (1)</summary><span class="citation-list">[s797](#evidence-61)</span></details>

**Exact source check:** After calling PlacesRepository\.City\(request\.CityId\), the source checks \`if \(city is null\)\`\.<details class="citations"><summary>Evidence (1)</summary><span class="citation-list">[s797](#evidence-61)</span></details>

**Evaluation behavior:** The lookup maps "oslo", "helsinki", and "lisbon" to Place constructor calls with their corresponding ID, name, latitude, and longitude literals; the switch default returns null\.<details class="citations"><summary>Evidence (2)</summary><span class="citation-list">[s797](#evidence-61), [s891](#evidence-64)</span></details>

</details>

<details>
<summary id="predicate-insert_result_nonnull">insert result is not null</summary>

**Condition meaning:** This check controls whether the source calls InsertRequest; the transaction commit follows the check\.<details class="citations"><summary>Evidence (1)</summary><span class="citation-list">[s935](#evidence-66)</span></details>

**Exact source check:** The source condition is \`await command\.ExecuteScalarAsync\(token\) is not null\`\.<details class="citations"><summary>Evidence (1)</summary><span class="citation-list">[s935](#evidence-66)</span></details>

**Evaluation behavior:** A non\-null ExecuteScalarAsync result leads to InsertRequest; a null result skips that call\. The source then awaits transaction\.CommitAsync\(token\)\.<details class="citations"><summary>Evidence (1)</summary><span class="citation-list">[s935](#evidence-66)</span></details>

</details>

<details id="summary" class="full-summary">
<summary>Full summary</summary>

```text
PlacesController.Save looks up a Place using request.CityId. A null lookup returns BadRequest with `UNSUPPORTED_CITY`; otherwise it awaits repository.Save(city, token) and returns Ok(city) after normal continuation. The repository source uses city.Id, Name, Latitude, and Longitude for the places INSERT and conditionally passes the whole city in a serialized request object.
```

<details class="citations"><summary>Evidence (3)</summary><span class="citation-list">[s797](#evidence-61), [s891](#evidence-64), [s935](#evidence-66)</span></details>

</details>

<details class="technical-details">
<summary>Technical reference</summary>

<a id="technical-reference"></a>
**Packet digest:** `sha256:56d7dc60aa18c537255c479a8edb6a1e78c5eb22b81ded0d76eeedd8d3979efe`

### Evidence by block

| Meaning block | Block ID | Evidence |
|---|---|---|
| Summary | [``summary``](#summary) | [s797](#evidence-61), [s891](#evidence-64), [s935](#evidence-66) |
| city is null · meaning | [``predicate-city_null-meaning``](#predicate-city_null) | [s797](#evidence-61) |
| city is null · exact source check | [``predicate-city_null-source-check``](#predicate-city_null) | [s797](#evidence-61) |
| city is null · evaluation | [``predicate-city_null-evaluation``](#predicate-city_null) | [s797](#evidence-61), [s891](#evidence-64) |
| insert result is not null · meaning | [``predicate-insert_result_nonnull-meaning``](#predicate-insert_result_nonnull) | [s935](#evidence-66) |
| insert result is not null · exact source check | [``predicate-insert_result_nonnull-source-check``](#predicate-insert_result_nonnull) | [s935](#evidence-66) |
| insert result is not null · evaluation | [``predicate-insert_result_nonnull-evaluation``](#predicate-insert_result_nonnull) | [s935](#evidence-66) |
| PlacesController\.Save reads request\.CityId and passes it to PlacesRepository\.City to produce city\. | [``step-lookup_city``](#block-lookup_city) | [s797](#evidence-61), [d751](#evidence-3) |
| The null check selects BadRequest for a null lookup; otherwise the method saves the Place and reaches Ok after the awaited save returns normally\. | [``step-city_null_branch``](#block-city_null_branch) | [s797](#evidence-61) |
| For a null city, the method returns the result of BadRequest with \`\{ error = "UNSUPPORTED\_CITY" \}\`\. | [``step-unsupported_city``](#block-unsupported_city) | [s797](#evidence-61), [d750](#evidence-2) |
| For a non\-null city, the controller awaits repository\.Save\(city, token\)\. Its source passes city\.Id, city\.Name, city\.Latitude, and city\.Longitude as the places INSERT values; the repository source conditionally calls InsertRequest and then awaits the transaction commit\. | [``step-save_place``](#block-save_place) | [s797](#evidence-61), [d760](#evidence-7), [s935](#evidence-66) |
| PlacesRepository\.Save opens a connection and transaction, prepares an INSERT into places with columns id, name, latitude, longitude, and supplies city\.Id, city\.Name, city\.Latitude, city\.Longitude to AddWithValue in that source order\. | [``step-bind_place_values``](#block-bind_place_values) | [s935](#evidence-66) |
| A non\-null result leads to the InsertRequest call; a null result skips it\. | [``step-outbox_condition``](#block-outbox_condition) | [s935](#evidence-66) |
| InsertRequest creates an ID and serializes an anonymous object containing id, type \`place\.requested\`, version 1, and place = city with JsonSerializerDefaults\.Web\. It prepares an INSERT into request\_outbox with id and payload, supplies the ID and serialized JSON, and awaits ExecuteNonQueryAsync\(token\)\. | [``step-write_request``](#block-write_request) | [s935](#evidence-66), [s829](#evidence-62) |
| On the null branch, the source skips InsertRequest\. | [``step-skip_request``](#block-skip_request) | [s935](#evidence-66) |
| After the conditional, the source awaits CommitAsync\(token\)\. | [``step-commit_transaction``](#block-commit_transaction) | [s935](#evidence-66), [d778](#evidence-13) |
| After the awaited save, the method returns the result of Ok\(city\)\. | [``step-success_result``](#block-success_result) | [s797](#evidence-61), [d771](#evidence-10) |
| The City source constructs Place values from the three listed literal tuples\. The packet supports these constructor arguments and later member accesses, but does not include the Place declaration\. | [``step-city_lookup``](#block-city_lookup) | [s891](#evidence-64), [d752](#evidence-4) |

<a id="data-movement"></a>
## Data movement stated in steps

This view contains only explicit from/to values in authored steps; matching names do not create a link\.

| Context | From | To | Step | Evidence | Uncertainty |
|---|---|---|---|---|---|
| Operation | request\.CityId | city | [action](#block-lookup_city) — PlacesController\.Save reads request\.CityId and passes it to PlacesRepository\.City to produce city\. | [s797](#evidence-61), [d751](#evidence-3) | — |
| Operation | city | BadRequest or save path | [decision](#block-city_null_branch) — The null check selects BadRequest for a null lookup; otherwise the method saves the Place and reaches Ok after the awaited save returns normally\. | [s797](#evidence-61) | — |
| Operation → When the condition holds: The null check selects BadRequest for a null lookup; otherwise the method saves the Place and reaches Ok after the awaited save returns normally\. | city | BadRequest result | [return](#block-unsupported_city) — For a null city, the method returns the result of BadRequest with \`\{ error = "UNSUPPORTED\_CITY" \}\`\. | [s797](#evidence-61), [d750](#evidence-2) | — |
| Operation → When the condition does not hold: The null check selects BadRequest for a null lookup; otherwise the method saves the Place and reaches Ok after the awaited save returns normally\. | city | repository\.Save continuation | [action](#block-save_place) — For a non\-null city, the controller awaits repository\.Save\(city, token\)\. Its source passes city\.Id, city\.Name, city\.Latitude, and city\.Longitude as the places INSERT values; the repository source conditionally calls InsertRequest and then awaits the transaction commit\. | [s797](#evidence-61), [d760](#evidence-7), [s935](#evidence-66) | — |
| Operation → When the condition does not hold: The null check selects BadRequest for a null lookup; otherwise the method saves the Place and reaches Ok after the awaited save returns normally\. → Following substeps: For a non\-null city, the controller awaits repository\.Save\(city, token\)\. Its source passes city\.Id, city\.Name, city\.Latitude, and city\.Longitude as the places INSERT values; the repository source conditionally calls InsertRequest and then awaits the transaction commit\. | city | places INSERT parameters | [action](#block-bind_place_values) — PlacesRepository\.Save opens a connection and transaction, prepares an INSERT into places with columns id, name, latitude, longitude, and supplies city\.Id, city\.Name, city\.Latitude, city\.Longitude to AddWithValue in that source order\. | [s935](#evidence-66) | — |
| Operation → When the condition does not hold: The null check selects BadRequest for a null lookup; otherwise the method saves the Place and reaches Ok after the awaited save returns normally\. → Following substeps: For a non\-null city, the controller awaits repository\.Save\(city, token\)\. Its source passes city\.Id, city\.Name, city\.Latitude, and city\.Longitude as the places INSERT values; the repository source conditionally calls InsertRequest and then awaits the transaction commit\. | ExecuteScalarAsync\(token\) result | InsertRequest or skip | [decision](#block-outbox_condition) — A non\-null result leads to the InsertRequest call; a null result skips it\. | [s935](#evidence-66) | — |
| Operation → When the condition does not hold: The null check selects BadRequest for a null lookup; otherwise the method saves the Place and reaches Ok after the awaited save returns normally\. → Following substeps: For a non\-null city, the controller awaits repository\.Save\(city, token\)\. Its source passes city\.Id, city\.Name, city\.Latitude, and city\.Longitude as the places INSERT values; the repository source conditionally calls InsertRequest and then awaits the transaction commit\. → When the condition holds: A non\-null result leads to the InsertRequest call; a null result skips it\. | city | request\_outbox INSERT call | [action](#block-write_request) — InsertRequest creates an ID and serializes an anonymous object containing id, type \`place\.requested\`, version 1, and place = city with JsonSerializerDefaults\.Web\. It prepares an INSERT into request\_outbox with id and payload, supplies the ID and serialized JSON, and awaits ExecuteNonQueryAsync\(token\)\. | [s935](#evidence-66), [s829](#evidence-62) | — |
| Operation → When the condition does not hold: The null check selects BadRequest for a null lookup; otherwise the method saves the Place and reaches Ok after the awaited save returns normally\. → Following substeps: For a non\-null city, the controller awaits repository\.Save\(city, token\)\. Its source passes city\.Id, city\.Name, city\.Latitude, and city\.Longitude as the places INSERT values; the repository source conditionally calls InsertRequest and then awaits the transaction commit\. → When the condition does not hold: A non\-null result leads to the InsertRequest call; a null result skips it\. | ExecuteScalarAsync\(token\) result | transaction commit | [action](#block-skip_request) — On the null branch, the source skips InsertRequest\. | [s935](#evidence-66) | — |
| Operation → When the condition does not hold: The null check selects BadRequest for a null lookup; otherwise the method saves the Place and reaches Ok after the awaited save returns normally\. → Following substeps: For a non\-null city, the controller awaits repository\.Save\(city, token\)\. Its source passes city\.Id, city\.Name, city\.Latitude, and city\.Longitude as the places INSERT values; the repository source conditionally calls InsertRequest and then awaits the transaction commit\. | transaction | repository\.Save continuation | [action](#block-commit_transaction) — After the conditional, the source awaits CommitAsync\(token\)\. | [s935](#evidence-66), [d778](#evidence-13) | — |
| Operation → When the condition does not hold: The null check selects BadRequest for a null lookup; otherwise the method saves the Place and reaches Ok after the awaited save returns normally\. | repository\.Save continuation | Ok result | [return](#block-success_result) — After the awaited save, the method returns the result of Ok\(city\)\. | [s797](#evidence-61), [d771](#evidence-10) | — |
| Operation | repository\.Save continuation | city | [action](#block-city_lookup) — The City source constructs Place values from the three listed literal tuples\. The packet supports these constructor arguments and later member accesses, but does not include the Place declaration\. | [s891](#evidence-64), [d752](#evidence-4) | — |

<a id="packet-facts"></a>
## Process types and fields

### Retained types

| Type | Kind | Owner | Superclass | Interfaces |
|---|---|---|---|---|
| PlacesController ``class:Weather.Places.PlacesController`` | CLASS | module:unnamed | class:Microsoft\.AspNetCore\.Mvc\.ControllerBase |  |
| PlacesRepository ``class:Weather.Places.PlacesRepository`` | CLASS | module:unnamed | — |  |

### Retained fields

| Owner | Field | Declared type | Modifiers | Annotations | Declaration tokens | Evidence |
|---|---|---|---|---|---|---|
| PlacesRepository \(class:Weather\.Places\.PlacesRepository\) | connectionString | LSystem/String; | PRIVATE, READONLY |  | `private readonly string connectionString = Environment . GetEnvironmentVariable ( "DATABASE_URL" ) ? ? throw new InvalidOperationException ( "DATABASE_URL_REQUIRED" ) ;` | [d973](#evidence-52) |

<a id="cited-evidence"></a>
## Cited evidence

<a id="evidence-2"></a>- **d750** — retained callsite evidence  _(No retained source location is available for this evidence in the packet\.)_
<a id="evidence-3"></a>- **d751** — retained callsite evidence  _(No retained source location is available for this evidence in the packet\.)_
<a id="evidence-4"></a>- **d752** — retained callsite evidence  _(No retained source location is available for this evidence in the packet\.)_
<a id="evidence-7"></a>- **d760** — retained callsite evidence  _(No retained source location is available for this evidence in the packet\.)_
<a id="evidence-10"></a>- **d771** — retained callsite evidence  _(No retained source location is available for this evidence in the packet\.)_
<a id="evidence-13"></a>- **d778** — retained callsite evidence  _(No retained source location is available for this evidence in the packet\.)_
<a id="evidence-61"></a>- **s797** — retained callable source  _(source: [`services/places/PlacesController.cs`:10–17](#source-1))_
<a id="evidence-62"></a>- **s829** — retained callable source  _(source: [`services/places/PlacesRepository.cs`:52–59](#source-2))_
<a id="evidence-64"></a>- **s891** — retained callable source  _(source: [`services/places/PlacesRepository.cs`:7–13](#source-3))_
<a id="evidence-66"></a>- **s935** — retained callable source  _(source: [`services/places/PlacesRepository.cs`:36–44](#source-6))_

<a id="source-locations"></a>
## Retained source locations

<a id="source-1"></a>- **`services/places/PlacesController.cs`:** 10–17 _(s797)_

<details>
<summary>View retained excerpt</summary>

```text
[HttpPost("/places")]
    public async Task<IActionResult> Save([FromBody] SavePlace request, CancellationToken token)
    {
        var city = PlacesRepository.City(request.CityId);
        if (city is null) return BadRequest(new { error = "UNSUPPORTED_CITY" });
        await repository.Save(city, token);
        return Ok(city);
    }
```
</details>


**Process blocks citing this excerpt:** [decision: The null check selects BadRequest for a null lookup; otherwise the method saves the Place and reaches Ok after the awaited save returns normally\.](#block-city_null_branch) · [action: PlacesController\.Save reads request\.CityId and passes it to PlacesRepository\.City to produce city\.](#block-lookup_city) · [action: For a non\-null city, the controller awaits repository\.Save\(city, token\)\. Its source passes city\.Id, city\.Name, city\.Latitude, and city\.Longitude as the places INSERT values; the repository source conditionally calls InsertRequest and then awaits the transaction commit\.](#block-save_place) · [return: After the awaited save, the method returns the result of Ok\(city\)\.](#block-success_result) · [return: For a null city, the method returns the result of BadRequest with \`\{ error = "UNSUPPORTED\_CITY" \}\`\.](#block-unsupported_city) · [city is null](#predicate-city_null) · [Summary](#summary)
<a id="source-2"></a>- **`services/places/PlacesRepository.cs`:** 52–59 _(s829)_

<details>
<summary>View retained excerpt</summary>

```text
private static async Task InsertRequest(NpgsqlConnection connection, NpgsqlTransaction transaction, Place city, CancellationToken token)
    {
        var id = Guid.NewGuid();
        var json = JsonSerializer.Serialize(new { id, type = "place.requested", version = 1, place = city }, new JsonSerializerOptions(JsonSerializerDefaults.Web));
        await using var command = new NpgsqlCommand("INSERT INTO request_outbox(id,payload) VALUES($1,$2::jsonb)", connection, transaction);
        command.Parameters.AddWithValue(id); command.Parameters.AddWithValue(json);
        await command.ExecuteNonQueryAsync(token);
    }
```
</details>


**Process blocks citing this excerpt:** [action: InsertRequest creates an ID and serializes an anonymous object containing id, type \`place\.requested\`, version 1, and place = city with JsonSerializerDefaults\.Web\. It prepares an INSERT into request\_outbox with id and payload, supplies the ID and serialized JSON, and awaits ExecuteNonQueryAsync\(token\)\.](#block-write_request)
<a id="source-3"></a>- **`services/places/PlacesRepository.cs`:** 7–13 _(s891)_

<details>
<summary>View retained excerpt</summary>

```text
public static Place? City(string id) => id switch
    {
        "oslo" => new("oslo", "Oslo", 59.93, 10.72),
        "helsinki" => new("helsinki", "Helsinki", 60.17, 24.94),
        "lisbon" => new("lisbon", "Lisbon", 38.72, -9.14),
        _ => null
    };
```
</details>


**Process blocks citing this excerpt:** [action: The City source constructs Place values from the three listed literal tuples\. The packet supports these constructor arguments and later member accesses, but does not include the Place declaration\.](#block-city_lookup) · [city is null](#predicate-city_null) · [Summary](#summary)
<a id="source-4"></a>- **`services/places/PlacesController.cs`:** 5–34 _(s921)_

<details>
<summary>View retained excerpt</summary>

```text
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
```
</details>

<a id="source-5"></a>- **`services/places/PlacesController.cs`:** 12–17 _(s921)_

<details>
<summary>View retained excerpt</summary>

```text
{
        var city = PlacesRepository.City(request.CityId);
        if (city is null) return BadRequest(new { error = "UNSUPPORTED_CITY" });
        await repository.Save(city, token);
        return Ok(city);
    
```
</details>

<a id="source-6"></a>- **`services/places/PlacesRepository.cs`:** 36–44 _(s935)_

<details>
<summary>View retained excerpt</summary>

```text
public async Task Save(Place city, CancellationToken token)
    {
        await using var connection = await Open(token);
        await using var transaction = await connection.BeginTransactionAsync(token);
        await using var command = new NpgsqlCommand("INSERT INTO places(id,name,latitude,longitude) VALUES($1,$2,$3,$4) ON CONFLICT DO NOTHING RETURNING id", connection, transaction);
        command.Parameters.AddWithValue(city.Id); command.Parameters.AddWithValue(city.Name); command.Parameters.AddWithValue(city.Latitude); command.Parameters.AddWithValue(city.Longitude);
        if (await command.ExecuteScalarAsync(token) is not null) await InsertRequest(connection, transaction, city, token);
        await transaction.CommitAsync(token);
    }
```
</details>


**Process blocks citing this excerpt:** [action: PlacesRepository\.Save opens a connection and transaction, prepares an INSERT into places with columns id, name, latitude, longitude, and supplies city\.Id, city\.Name, city\.Latitude, city\.Longitude to AddWithValue in that source order\.](#block-bind_place_values) · [action: After the conditional, the source awaits CommitAsync\(token\)\.](#block-commit_transaction) · [decision: A non\-null result leads to the InsertRequest call; a null result skips it\.](#block-outbox_condition) · [action: For a non\-null city, the controller awaits repository\.Save\(city, token\)\. Its source passes city\.Id, city\.Name, city\.Latitude, and city\.Longitude as the places INSERT values; the repository source conditionally calls InsertRequest and then awaits the transaction commit\.](#block-save_place) · [action: On the null branch, the source skips InsertRequest\.](#block-skip_request) · [action: InsertRequest creates an ID and serializes an anonymous object containing id, type \`place\.requested\`, version 1, and place = city with JsonSerializerDefaults\.Web\. It prepares an INSERT into request\_outbox with id and payload, supplies the ID and serialized JSON, and awaits ExecuteNonQueryAsync\(token\)\.](#block-write_request) · [insert result is not null](#predicate-insert_result_nonnull) · [Summary](#summary)

## Packet gaps and limits

### Captured gaps

- `\{"code":"CALL\_SITE\_SOURCE\_NOT\_CONTAINED\_IN\_METHOD\_BODY","count":27,"examples":\[\{"factId":"places:call\-relation:055b501e46a896fb647364fe","from":"method:class:Weather\.Places\.PlacesController\#Save\(LWeather/Places/SavePlace;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task\`1;"\},\{"factId":"places:call\-relation:09c47224294c08d709a5c462","from":"method:class:Weather\.Places\.PlacesController\#Save\(LWeather/Places/SavePlace;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task\`1;"\},\{"factId":"places:call\-relation:2a983ba2dfc7449680c92bac","from":"method:class:Weather\.Places\.PlacesController\#Save\(LWeather/Places/SavePlace;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task\`1;"\},\{"factId":"places:call\-relation:451d4951aae6695f93e9c1ce","from":"method:class:Weather\.Places\.PlacesController\#Save\(LWeather/Places/SavePlace;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task\`1;"\},\{"factId":"places:call\-relation:0d15bf2f30b91c5718216d79","from":"method:class:Weather\.Places\.PlacesRepository\#City\(LSystem/String;\)LWeather/Places/Place;"\},\{"factId":"places:call\-relation:682ea391f4a0c5afe4b689be","from":"method:class:Weather\.Places\.PlacesRepository\#City\(LSystem/String;\)LWeather/Places/Place;"\},\{"factId":"places:call\-relation:7724db239cdcb4e08a8d0741","from":"method:class:Weather\.Places\.PlacesRepository\#City\(LSystem/String;\)LWeather/Places/Place;"\},\{"factId":"places:call\-relation:1d33490abb5191d58c66b442","from":"method:class:Weather\.Places\.PlacesRepository\#Save\(LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;"\}\]\}`
- `\{"code":"CALL\_TARGET\_BODY\_NOT\_CAPTURED","count":17,"examples":\[\{"from":"method:class:Weather\.Places\.PlacesController\#Save\(LWeather/Places/SavePlace;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task\`1;","scope":"csproj:services/places/Places\.csproj@net10\.0","target":"method:class:Microsoft\.AspNetCore\.Mvc\.ControllerBase\#BadRequest\(LSystem/Object;\)LMicrosoft/AspNetCore/Mvc/BadRequestObjectResult;"\},\{"from":"method:class:Weather\.Places\.PlacesController\#Save\(LWeather/Places/SavePlace;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task\`1;","scope":"csproj:services/places/Places\.csproj@net10\.0","target":"method:class:Microsoft\.AspNetCore\.Mvc\.ControllerBase\#Ok\(LSystem/Object;\)LMicrosoft/AspNetCore/Mvc/OkObjectResult;"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#City\(LSystem/String;\)LWeather/Places/Place;","scope":"csproj:services/places/Places\.csproj@net10\.0","target":"method:class:Weather\.Places\.Place\#&lt;init&gt;\(LSystem/String;LSystem/String;DD\)V"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#Save\(LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","scope":"csproj:services/places/Places\.csproj@net10\.0","target":"method:class:Npgsql\.NpgsqlCommand\#&lt;init&gt;\(LSystem/String;LNpgsql/NpgsqlConnection;LNpgsql/NpgsqlTransaction;\)V"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#Save\(LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","scope":"csproj:services/places/Places\.csproj@net10\.0","target":"method:class:Npgsql\.NpgsqlCommand\#ExecuteScalarAsync\(LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task\`1;"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#Save\(LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","scope":"csproj:services/places/Places\.csproj@net10\.0","target":"method:class:Npgsql\.NpgsqlConnection\#BeginTransactionAsync\(LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/ValueTask\`1;"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#Save\(LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","scope":"csproj:services/places/Places\.csproj@net10\.0","target":"method:class:Npgsql\.NpgsqlParameterCollection\#AddWithValue\(LSystem/Object;\)LNpgsql/NpgsqlParameter;"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#Save\(LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","scope":"csproj:services/places/Places\.csproj@net10\.0","target":"method:class:Npgsql\.NpgsqlTransaction\#CommitAsync\(LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;"\}\]\}`
- `\{"code":"DIRECT\_DECLARED\_TYPES\_ONLY","count":1,"examples":\[null\]\}`
- `\{"code":"PROCESS\_CONSTRUCTED\_TYPE\_NOT\_CAPTURED","count":8,"examples":\[\{"from":"method:class:Weather\.Places\.PlacesRepository\#Save\(LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","scope":"csproj:services/places/Places\.csproj@net10\.0","target":"method:class:Npgsql\.NpgsqlCommand\#&lt;init&gt;\(LSystem/String;LNpgsql/NpgsqlConnection;LNpgsql/NpgsqlTransaction;\)V"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#Save\(LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","scope":"csproj:services/places/Places\.csproj@net10\.0","typeName":"NpgsqlCommand"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#InsertRequest\(LNpgsql/NpgsqlConnection;LNpgsql/NpgsqlTransaction;LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","scope":"csproj:services/places/Places\.csproj@net10\.0","target":"method:class:System\.Text\.Json\.JsonSerializerOptions\#&lt;init&gt;\(LSystem/Text/Json/JsonSerializerDefaults;\)V"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#InsertRequest\(LNpgsql/NpgsqlConnection;LNpgsql/NpgsqlTransaction;LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","scope":"csproj:services/places/Places\.csproj@net10\.0","target":"method:class:Npgsql\.NpgsqlCommand\#&lt;init&gt;\(LSystem/String;LNpgsql/NpgsqlConnection;LNpgsql/NpgsqlTransaction;\)V"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#InsertRequest\(LNpgsql/NpgsqlConnection;LNpgsql/NpgsqlTransaction;LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","scope":"csproj:services/places/Places\.csproj@net10\.0","typeName":"JsonSerializerOptions"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#InsertRequest\(LNpgsql/NpgsqlConnection;LNpgsql/NpgsqlTransaction;LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","scope":"csproj:services/places/Places\.csproj@net10\.0","typeName":"NpgsqlCommand"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#Open\(LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task\`1;","scope":"csproj:services/places/Places\.csproj@net10\.0","target":"method:class:Npgsql\.NpgsqlConnection\#&lt;init&gt;\(LSystem/String;\)V"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#Open\(LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task\`1;","scope":"csproj:services/places/Places\.csproj@net10\.0","typeName":"NpgsqlConnection"\}\]\}`
- `\{"code":"PROCESS\_QUALIFIED\_FIELD\_TYPE\_NOT\_CAPTURED","count":1,"examples":\[\{"candidateCount":0,"field":"Web","from":"method:class:Weather\.Places\.PlacesRepository\#InsertRequest\(LNpgsql/NpgsqlConnection;LNpgsql/NpgsqlTransaction;LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","scope":"csproj:services/places/Places\.csproj@net10\.0","typeName":"JsonSerializerDefaults"\}\]\}`
- `\{"code":"PROCESS\_QUALIFIED\_SOURCE\_REFERENCE\_UNSUPPORTED","count":2,"examples":\[\{"from":"method:class:Weather\.Places\.PlacesRepository\#Save\(LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","scope":"csproj:services/places/Places\.csproj@net10\.0","spelling":"Parameters\.AddWithValue"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#InsertRequest\(LNpgsql/NpgsqlConnection;LNpgsql/NpgsqlTransaction;LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","scope":"csproj:services/places/Places\.csproj@net10\.0","spelling":"Parameters\.AddWithValue"\}\]\}`
- `\{"code":"PROCESS\_TYPE\_DECLARATION\_NOT\_CAPTURED","count":3,"examples":\[\{"candidateCount":0,"identity":"module:unnamed","scope":"csproj:services/places/Places\.csproj@net10\.0"\},\{"candidateCount":0,"identity":"class:System\.String","scope":"csproj:services/places/Places\.csproj@net10\.0"\},\{"candidateCount":0,"identity":"class:Microsoft\.AspNetCore\.Mvc\.ControllerBase","scope":"csproj:services/places/Places\.csproj@net10\.0"\}\]\}`
- `\{"code":"SOURCE\_HELPER\_DECLARATION\_NOT\_CAPTURED","count":2,"examples":\[\{"from":"method:class:Weather\.Places\.PlacesController\#Save\(LWeather/Places/SavePlace;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task\`1;","name":"BadRequest","owner":"class:Weather\.Places\.PlacesController","scope":"csproj:services/places/Places\.csproj@net10\.0"\},\{"from":"method:class:Weather\.Places\.PlacesController\#Save\(LWeather/Places/SavePlace;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task\`1;","name":"Ok","owner":"class:Weather\.Places\.PlacesController","scope":"csproj:services/places/Places\.csproj@net10\.0"\}\]\}`
- `\{"code":"SOURCE\_QUALIFIED\_RECEIVER\_TYPE\_NOT\_CAPTURED","count":3,"examples":\[\{"from":"method:class:Weather\.Places\.PlacesController\#Save\(LWeather/Places/SavePlace;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task\`1;","method":"Save","receiver":"repository","scope":"csproj:services/places/Places\.csproj@net10\.0"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#InsertRequest\(LNpgsql/NpgsqlConnection;LNpgsql/NpgsqlTransaction;LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","method":"NewGuid","receiver":"Guid","scope":"csproj:services/places/Places\.csproj@net10\.0"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#InsertRequest\(LNpgsql/NpgsqlConnection;LNpgsql/NpgsqlTransaction;LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","method":"Serialize","receiver":"JsonSerializer","scope":"csproj:services/places/Places\.csproj@net10\.0"\}\]\}`
- `\{"code":"SOURCE\_RECEIVER\_SHADOWING\_AMBIGUOUS","count":6,"examples":\[\{"from":"method:class:Weather\.Places\.PlacesRepository\#Save\(LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","method":"ExecuteScalarAsync","receiver":"command","scope":"csproj:services/places/Places\.csproj@net10\.0"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#Save\(LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","method":"BeginTransactionAsync","receiver":"connection","scope":"csproj:services/places/Places\.csproj@net10\.0"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#Save\(LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","method":"CommitAsync","receiver":"transaction","scope":"csproj:services/places/Places\.csproj@net10\.0"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#InsertRequest\(LNpgsql/NpgsqlConnection;LNpgsql/NpgsqlTransaction;LWeather/Places/Place;LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task;","method":"ExecuteNonQueryAsync","receiver":"command","scope":"csproj:services/places/Places\.csproj@net10\.0"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#Open\(LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task\`1;","method":"DisposeAsync","receiver":"connection","scope":"csproj:services/places/Places\.csproj@net10\.0"\},\{"from":"method:class:Weather\.Places\.PlacesRepository\#Open\(LSystem/Threading/CancellationToken;\)LSystem/Threading/Tasks/Task\`1;","method":"OpenAsync","receiver":"connection","scope":"csproj:services/places/Places\.csproj@net10\.0"\}\]\}`
- `\{"code":"SOURCE\_REFERENCE\_CANDIDATE\_AUTHORITY","count":1,"examples":\[null\]\}`
- `\{"code":"STRUCTURAL\_DATAFLOW\_NOT\_AVAILABLE","count":1,"examples":\[null\]\}`

### Interpretation limits

- `Retained FLOW and compiler relations preserve provider evidence, not runtime execution or statement timing\.`
- `SOURCE\_REFERENCE\_CANDIDATE edges identify same\-scope source\-context candidates only; they do not establish executed calls, receiver identity, inheritance dispatch, or order\.`
- `Only the supplied root, selected declarations, retained method source, fields, types, and listed frontiers support claims; missing context remains unknown\.`
- `A field type or superclass declaration does not establish the runtime object or selected override\.`

### Coverage boundaries

- `CLR\_SIGNATURE\_PROJECTED\_TO\_JVM\_DESCRIPTOR\_GRAMMAR`
- `CSHARP\_SOURCE\_GENERATED\_DOCUMENTS\_NOT\_INDEXED`
- `EXCEPTION\_FLOW\_REQUIRES\_SOURCE\_REVIEW`
- `GENERATED\_SOURCE\_BODIES\_NOT\_INDEXED`
- `LAMBDA\_EXECUTION\_NOT\_EXPANDED`
- `OPENAPI\_JSON\_SCHEMA\_KEYWORDS\_NOT\_INTERPRETED`
- `SHORT\_CIRCUIT\_FLOW\_REQUIRES\_SOURCE\_REVIEW`
- `SWITCH\_FLOW\_REQUIRES\_SOURCE\_REVIEW`

<details>
<summary>Full evidence inventory</summary>

<a id="evidence-1"></a>- **c1** — saved capture coverage
<a id="evidence-5"></a>- **d753** — retained callsite evidence
<a id="evidence-6"></a>- **d755** — retained callsite evidence
<a id="evidence-8"></a>- **d766** — retained callsite evidence
<a id="evidence-9"></a>- **d768** — retained callsite evidence
<a id="evidence-11"></a>- **d772** — retained callsite evidence
<a id="evidence-12"></a>- **d776** — retained callsite evidence
<a id="evidence-14"></a>- **d779** — retained callsite evidence
<a id="evidence-15"></a>- **d783** — retained callsite evidence
<a id="evidence-16"></a>- **d787** — retained callsite evidence
<a id="evidence-17"></a>- **d793** — retained callsite evidence
<a id="evidence-18"></a>- **d794** — retained callsite evidence
<a id="evidence-19"></a>- **d798** — retained callsite evidence
<a id="evidence-20"></a>- **d800** — retained callsite evidence
<a id="evidence-21"></a>- **d801** — retained callsite evidence
<a id="evidence-22"></a>- **d808** — retained callsite evidence
<a id="evidence-23"></a>- **d812** — retained callsite evidence
<a id="evidence-24"></a>- **d814** — retained callsite evidence
<a id="evidence-25"></a>- **d820** — retained callsite evidence
<a id="evidence-26"></a>- **d821** — retained callsite evidence
<a id="evidence-27"></a>- **d824** — retained callsite evidence
<a id="evidence-28"></a>- **d825** — retained callsite evidence
<a id="evidence-29"></a>- **d858** — retained callsite evidence
<a id="evidence-30"></a>- **d863** — retained callsite evidence
<a id="evidence-31"></a>- **d871** — retained callsite evidence
<a id="evidence-32"></a>- **d876** — retained callsite evidence
<a id="evidence-33"></a>- **d890** — retained callsite evidence
<a id="evidence-34"></a>- **d900** — retained callsite evidence
<a id="evidence-35"></a>- **d907** — retained callsite evidence
<a id="evidence-36"></a>- **d908** — retained callsite evidence
<a id="evidence-37"></a>- **d910** — retained callsite evidence
<a id="evidence-38"></a>- **d913** — retained callsite evidence
<a id="evidence-39"></a>- **d924** — retained callsite evidence
<a id="evidence-40"></a>- **d936** — retained callsite evidence
<a id="evidence-41"></a>- **d940** — retained callsite evidence
<a id="evidence-42"></a>- **d944** — retained callsite evidence
<a id="evidence-43"></a>- **d951** — retained callsite evidence
<a id="evidence-44"></a>- **d956** — retained callsite evidence
<a id="evidence-45"></a>- **d959** — retained callsite evidence
<a id="evidence-46"></a>- **d961** — retained callsite evidence
<a id="evidence-47"></a>- **d962** — retained callsite evidence
<a id="evidence-48"></a>- **d963** — retained callsite evidence
<a id="evidence-49"></a>- **d966** — retained callsite evidence
<a id="evidence-50"></a>- **d969** — retained callsite evidence
<a id="evidence-51"></a>- **d971** — retained containing type declaration
<a id="evidence-52"></a>- **d973** — retained field declaration
<a id="evidence-53"></a>- **d975** — exact internal process root
<a id="evidence-54"></a>- **d977** — selected callable declaration
<a id="evidence-55"></a>- **d981** — selected callable declaration
<a id="evidence-56"></a>- **d986** — selected callable declaration
<a id="evidence-57"></a>- **d987** — retained containing type declaration
<a id="evidence-58"></a>- **d988** — selected callable declaration
<a id="evidence-59"></a>- **p1** — selected internal process context
<a id="evidence-60"></a>- **s763** — retained containing type source
<a id="evidence-63"></a>- **s858** — retained callable source
<a id="evidence-65"></a>- **s921** — retained containing type source

</details>
</details>

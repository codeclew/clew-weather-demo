# Forecasts\.refresh: select, transform, and store forecast data

> **DRAFT / UNREVIEWED / NOT PUBLISHED** Structure and evidence\-label binding were validated\. Semantic correctness was not reviewed\.

<nav>**Contents:** [ Glossary ](#glossary) · [ Internal process explanation ](#ordered-behavior) · [ Process outline ](#process-outline) · [ Authored pseudocode ](#authored-pseudocode) · [ Source\-local process projection ](#source-process-projection) · [ Prepared values and checks ](#preparations) · [ First matching condition ](#first-match-decisions) · [ Full summary ](#summary)</nav>

## Uncertainties

- The packet does not establish that \`refresh\` ran, the values of \`place\`, \`mode\`, \`cached\`, or provider configuration, or the HTTP response and body\.
- The retained source does not establish HTTP or JDBC implementation effects, transaction completion, database results, event delivery, or publication\.

<a id="process-outline"></a>
## Process outline

1. [**decision:** Check whether the selected cache row has an expiry after the current time\.](#block-check_cache_fresh)

<a id="glossary"></a>
## Glossary

<a id="glossary-forecast_payload"></a>
### Forecast payload _(Technical carrier)_

The \`forecast\` JSON object contains \`updatedAt\`, \`fetchedAt\`, \`mode\`, and \`periods\`; the method serializes it as \`payload\` for the forecasts SQL statement and also attaches it to the event\.<details class="citations"><summary>Evidence (5)</summary><span class="citation-list">[s224](#evidence-287), [s248](#evidence-298), [s321](#evidence-345), [s364](#evidence-375), [s68](#evidence-413)</span></details>  **Glossary:** [Forecast payload](#glossary-forecast_payload)

<details>
<summary>Technical names</summary>

**Technical names:** ``forecast`` · ``payload``

**Declaration references:** ``d422`` — d422 · callable:weather/Forecasts\.refresh\#jvm:\(Ltools/jackson/databind/JsonNode;\)V · class:weather/Forecasts · :/main

</details>

<a id="glossary-outbox_event"></a>
### Outbox event _(Technical carrier)_

The \`event\` object uses id \`$id:$updatedAt\`, type \`forecast\.updated\`, version 1, and carries the input \`place\` and constructed \`forecast\`; the method serializes it for the \`forecast\_outbox\` SQL statement\.<details class="citations"><summary>Evidence (5)</summary><span class="citation-list">[s155](#evidence-251), [s200](#evidence-273), [s210](#evidence-279), [s242](#evidence-295), [s285](#evidence-323)</span></details>  **Glossary:** [Outbox event](#glossary-outbox_event)

<details>
<summary>Technical names</summary>

**Technical names:** ``event`` · ``forecast_outbox``

**Declaration references:** ``d422`` — d422 · callable:weather/Forecasts\.refresh\#jvm:\(Ltools/jackson/databind/JsonNode;\)V · class:weather/Forecasts · :/main

</details>

<a id="authored-pseudocode"></a>
## Authored pseudocode

Structure and branch order follow the supplied answer steps.

- [**decision:** Cached entry is unexpired](#block-check_cache_fresh)
- _Scope 1 — When the condition holds_
- [**return:** When \`cache\_fresh\` is true, return from \`refresh\` before source acquisition, transformation, or…](#block-return_fresh_cache)
- _End Scope 1_
- _Scope 2 — When the condition does not hold_
- [**action:** After the cache miss or expiry, initialize \`expires\` to now plus 3600 seconds and \`lastModified…](#block-initialize_defaults)
- [**decision:** Cached entry is unexpired](#block-choose_fixture)
- _Scope 3 — When the condition holds_
- [**action:** Read \`/app/fixtures/$id\.json\` into \`raw\`\. The file contents are not present in this packet\.](#block-read_fixture) _Scope 3_
- _End Scope 3_
- _Scope 4 — When the condition does not hold_
- [**decision:** Response status is 429](#block-check_backoff) _Scope 4_
- _Scope 5 — When the condition holds_
- [**decision:** Provider user agent is nonblank](#block-check_agent) _Scope 5_
- _Scope 6 — When the condition holds_
- [**action:** Bind the nonblank environment value as \`agent\` for the request\.](#block-use_agent) _Scope 6_
- _End Scope 6_
- _Scope 7 — When the condition does not hold_
- [**throw:** The source invokes \`error\("MET\_USER\_AGENT\_REQUIRED"\)\`; the exception type and dispatch are not…](#block-missing_agent) _Scope 7_
- _End Scope 7_
- [**throw:** When the next\-attempt instant is after now, the source invokes \`error\("PROVIDER\_BACKOFF"\)\`\.](#block-backoff_error) _Scope 5_
- _End Scope 5_
- _Scope 8 — When the condition does not hold_
- [**action:** Assign \`nextAttempt\[id\] = Instant\.now\(\)\.plusSeconds\(60\)\` before the HTTP send call\.](#block-seed_next_attempt) _Scope 8_
- [**action:** Read latitude and longitude from \`place\`, convert each with \`asDouble\(\)\`, then use \`BigDecimal\.…](#block-format_coordinates) _Scope 8_
- [**action:** Build a GET request for the met\.no compact location forecast URL with those coordinates, a 20\-s…](#block-build_request) _Scope 8_
- [**action:** Read the cached row's \`last\_modified\` value as nullable \`modified\`\.](#block-read_modified) _Scope 8_
- [**decision:** Cached Last\-Modified value exists](#block-conditional_header) _Scope 8_
- _Scope 9 — When the condition holds_
- [**action:** Add \`If\-Modified\-Since\` with \`modified\`\.](#block-add_modified_header) _Scope 9_
- _End Scope 9_
- _Scope 10 — When the condition does not hold_
- [**action:** Leave \`If\-Modified\-Since\` off the request builder\.](#block-omit_modified_header) _Scope 10_
- _End Scope 10_
- [**action:** Call \`http\.send\(builder\.GET\(\)\.build\(\), HttpResponse\.BodyHandlers\.ofByteArray\(\)\)\`\. The request's…](#block-send_request) _Scope 8_
- [**action:** Set \`expires\` from an \`Expires\` header parsed with \`RFC\_1123\_DATE\_TIME\` and converted to an ins…](#block-derive_expiry) _Scope 8_
- [**decision:** Response status is 429](#block-check_429) _Scope 8_
- _Scope 11 — When the condition holds_
- [**action:** Use the Retry\-After value or \`"60"\`; if \`toLongOrNull\(\)\` returns null use \`60L\`, clamp to at le…](#block-set_retry_delay) _Scope 11_
- _End Scope 11_
- _Scope 12 — When the condition does not hold_
- [**action:** Assign \`expires\` to \`nextAttempt\[id\]\`\.](#block-set_expiry_retry) _Scope 12_
- _End Scope 12_
- _Decision chain — Scope 13_
- [**decision:** Response is 304 and a cache row exists](#block-check_not_modified) _Scope 8_
- _Scope 14 — When the condition holds_
- [**action:** Call \`jdbc\.update\("UPDATE forecasts SET expires\_at=? WHERE place\_id=?", Timestamp\.from\(expires\)…](#block-refresh_cached_expiry) _Scope 14_
- _End Scope 14_
- _Else if (Scope 13)_
- [**decision:** Response status is 200 or 203](#block-check_http_status) _Scope 8_
- _Scope 15 — When the condition holds_
- [**decision:** Content\-Encoding is gzip](#block-check_gzip) _Scope 15_
- _Scope 16 — When the condition holds_
- [**action:** Set \`lastModified\` from the \`Last\-Modified\` header, using null if absent\.](#block-read_last_modified) _Scope 16_
- _End Scope 16_
- _Scope 17 — When the condition does not hold_
- [**action:** Convert the response body bytes to a string with UTF\-8 and assign it to \`raw\`\.](#block-decode_utf8) _Scope 17_
- _End Scope 17_
- _End Scope 15_
- _Scope 18 — Otherwise \(none of the conditions above matched\)_
- [**throw:** The source's \`require\` failure message is \`PROVIDER\_HTTP\_\` plus the response status code; excep…](#block-reject_http_status) _Scope 18_
- _End Scope 18_
- _End decision chain Scope 13_
- _End Scope 8_
- [**action:** Parse \`raw\` with \`json\.readTree\` into \`document\`\.](#block-parse_document) _Scope 4_
- [**action:** Create an empty JSON array named \`periods\`\.](#block-create_periods) _Scope 4_
- [**decision:** Cached entry is unexpired](#block-check_cache_fresh_repeated_source) _Scope 4_
- _Scope 19 — When the condition holds_
- [**loop:** Visit \`document\["properties"\]\["timeseries"\]\.take\(6\)\`, so the source builds periods from at most…](#block-map_first_six_points) _Scope 19_
- _Scope 20 — Loop body_
- [**decision:** Temperature exists and is numeric](#block-check_temperature) _Scope 20_
- _Scope 21 — When the condition holds_
- [**action:** After the required temperature check, read \`next\` from \`point\["data"\]\["next\_1\_hours"\]\` and crea…](#block-construct_period) _Scope 21_
- _End Scope 21_
- _Scope 22 — When the condition does not hold_
- [**throw:** The source's \`require\(temperature \!= null &amp;&amp; temperature\.isNumber\)\` fails; the exception type i…](#block-reject_temperature) _Scope 22_
- _End Scope 22_
- [**decision:** Rain is missing or nonnumeric](#block-check_rain) _Scope 20_
- _Scope 23 — When the condition holds_
- [**action:** Set \`period\["precipitationMm"\]\` to JSON null\.](#block-put_null_rain) _Scope 23_
- _End Scope 23_
- _Scope 24 — When the condition does not hold_
- [**action:** Set \`period\["precipitationMm"\]\` from \`rain\.asDouble\(\)\`\.](#block-put_numeric_rain) _Scope 24_
- _End Scope 24_
- [**action:** Append the completed period to \`periods\`\.](#block-append_period) _Scope 20_
- _End Scope 20_
- [**decision:** At least one period was built](#block-check_periods_nonempty) _Scope 19_
- _Scope 25 — When the condition holds_
- [**action:** Read \`updated\_at\` as text into \`updatedAt\`, then call \`Instant\.parse\(updatedAt\)\` before constru…](#block-parse_updated_at) _Scope 25_
- [**action:** Construct \`forecast\` with \`updatedAt\`, \`Instant\.now\(\)\.toString\(\)\` as \`fetchedAt\`, and \`mode\`; a…](#block-build_forecast) _Scope 25_
- [**action:** Serialize \`forecast\` with \`json\.writeValueAsString\` into \`payload\`\.](#block-serialize_forecast) _Scope 25_
- [**action:** Call the \`forecasts\` INSERT/ON CONFLICT statement with the place id, parsed update time, payloa…](#block-upsert_forecast) _Scope 25_
- [**action:** After the forecast update call, form \`eventId\` as \`$id:$updatedAt\`; create an event with that i…](#block-build_event) _Scope 25_
- [**action:** Serialize \`event\` and call the \`forecast\_outbox\` INSERT statement with \`ON CONFLICT DO NOTHING\`…](#block-insert_outbox) _Scope 25_
- _End Scope 25_
- _Scope 26 — When the condition does not hold_
- [**throw:** The source's \`require\(periods\.size\(\) &gt; 0\)\` fails; the exception type is not established here\.](#block-reject_empty_periods) _Scope 26_
- _End Scope 26_
- _End Scope 19_
- _Scope 27 — When the condition does not hold_
- [**return:** A fresh cache entry causes an early return before the later work in this method\.](#block-return_fresh_cache_repeated_source) _Scope 27_
- _End Scope 27_
- _End Scope 4_
- _End Scope 2_

<a id="source-process-projection"></a>
## Source\-local process projection

Built from retained source syntax; this is not execution evidence\.

### Parsed source outline

```text
Entry: callable:weather/Forecasts.refresh#jvm:(Ltools/jackson/databind/JsonNode;)V
... (not established: ROOT_SOURCE_REFERENCE_MISSING)

```

[Editable PlantUML](process-flow.puml)

_A causal path was not established; the diagram contains an evidence gap only\._

[Rendered SVG](process-flow.svg)

<a id="ordered-behavior"></a>
## Internal process explanation

<a id="first-match-decisions"></a>
### First matching condition

| Condition | Action summary |
|---|---|
| [Response is 304 and a cache row exists](#predicate-not_modified_with_cache) | **action:** Call \`jdbc\.update\("UPDATE forecasts SET expires\_at=? WHERE place\_id=?", Timestamp\.from\(expires\), id\)\`, then return from \`refresh\`\. The source does not show the database outcome\. [ Details ](#block-refresh_cached_expiry)<details class="citations"><summary>Evidence (3)</summary><span class="citation-list">[s111](#evidence-225), [s271](#evidence-313), [s326](#evidence-347)</span></details> |
| [Response status is 200 or 203](#predicate-accepted_status) | **decision:** Read \`raw\` from the response body using the gzip path when the content\-encoding value matches gzip, or UTF\-8 conversion otherwise\. [ Details ](#block-check_gzip)<details class="citations"><summary>Evidence (3)</summary><span class="citation-list">[s102](#evidence-219), [s353](#evidence-364), [s380](#evidence-383)</span></details> |
| Otherwise | **throw:** The source's \`require\` failure message is \`PROVIDER\_HTTP\_\` plus the response status code; exception type and runtime dispatch are not established\. [ Details ](#block-reject_http_status)<details class="citations"><summary>Evidence (3)</summary><span class="citation-list">[s64](#evidence-412), [s89](#evidence-427), [s288](#evidence-326)</span></details> |

The first matching row wins; a later row applies only when earlier conditions are false\. This is a reading aid, not an executable DMN rule, and it does not establish predicate purity or reevaluation behavior\.

<a id="block-check_cache_fresh"></a>1. **decision:** [Cached entry is unexpired](#predicate-cache_fresh)  **Shared preparation:** [Resolve the place key and cache candidate](#preparation-prep_inputs)
  **When the condition holds:**
<a id="block-return_fresh_cache"></a>   - **return:** When \`cache\_fresh\` is true, return from \`refresh\` before source acquisition, transformation, or the later SQL calls\.
  **When the condition does not hold:**
<a id="block-initialize_defaults"></a>   - **action:** After the cache miss or expiry, initialize \`expires\` to now plus 3600 seconds and \`lastModified\` to null\.
<a id="block-choose_fixture"></a>   - **decision:** [Cached entry is unexpired](#predicate-cache_fresh)  **Shared preparation:** [Resolve the place key and cache candidate](#preparation-prep_inputs)
     **When the condition holds:**
<a id="block-read_fixture"></a>      - **action:** Read \`/app/fixtures/$id\.json\` into \`raw\`\. The file contents are not present in this packet\.
     **When the condition does not hold:**
<a id="block-check_backoff"></a>      - **decision:** [Response status is 429](#predicate-status_429)
        **When the condition holds:**
<a id="block-check_agent"></a>         - **decision:** [Provider user agent is nonblank](#predicate-agent_ready)
           **When the condition holds:**
<a id="block-use_agent"></a>            - **action:** Bind the nonblank environment value as \`agent\` for the request\.
           **When the condition does not hold:**
<a id="block-missing_agent"></a>            - **throw:** The source invokes \`error\("MET\_USER\_AGENT\_REQUIRED"\)\`; the exception type and dispatch are not established\.
<a id="block-backoff_error"></a>         - **throw:** When the next\-attempt instant is after now, the source invokes \`error\("PROVIDER\_BACKOFF"\)\`\.
        **When the condition does not hold:**
<a id="block-seed_next_attempt"></a>         - **action:** Assign \`nextAttempt\[id\] = Instant\.now\(\)\.plusSeconds\(60\)\` before the HTTP send call\.
<a id="block-format_coordinates"></a>         - **action:** Read latitude and longitude from \`place\`, convert each with \`asDouble\(\)\`, then use \`BigDecimal\.valueOf\(\.\.\.\)\.setScale\(4, RoundingMode\.DOWN\)\.toPlainString\(\)\` for the request coordinates\.
<a id="block-build_request"></a>         - **action:** Build a GET request for the met\.no compact location forecast URL with those coordinates, a 20\-second timeout, \`User\-Agent: agent\`, and \`Accept\-Encoding: gzip\`\.
<a id="block-read_modified"></a>         - **action:** Read the cached row's \`last\_modified\` value as nullable \`modified\`\.
<a id="block-conditional_header"></a>         - **decision:** [Cached Last\-Modified value exists](#predicate-has_modified)
           **When the condition holds:**
<a id="block-add_modified_header"></a>            - **action:** Add \`If\-Modified\-Since\` with \`modified\`\.
           **When the condition does not hold:**
<a id="block-omit_modified_header"></a>            - **action:** Leave \`If\-Modified\-Since\` off the request builder\.
<a id="block-send_request"></a>         - **action:** Call \`http\.send\(builder\.GET\(\)\.build\(\), HttpResponse\.BodyHandlers\.ofByteArray\(\)\)\`\. The request's runtime outcome is unknown\.
<a id="block-derive_expiry"></a>         - **action:** Set \`expires\` from an \`Expires\` header parsed with \`RFC\_1123\_DATE\_TIME\` and converted to an instant; if the header is absent, use now plus 3600 seconds\. A parse failure is not handled in this source path\.
<a id="block-check_429"></a>         - **decision:** [Response status is 429](#predicate-status_429)
           **When the condition holds:**
<a id="block-set_retry_delay"></a>            - **action:** Use the Retry\-After value or \`"60"\`; if \`toLongOrNull\(\)\` returns null use \`60L\`, clamp to at least \`60L\`, then assign now plus that many seconds to \`nextAttempt\[id\]\`\.
           **When the condition does not hold:**
<a id="block-set_expiry_retry"></a>            - **action:** Assign \`expires\` to \`nextAttempt\[id\]\`\.
<a id="block-check_not_modified"></a>         - **decision:** [Response is 304 and a cache row exists](#predicate-not_modified_with_cache)
           **When the condition holds:**
<a id="block-refresh_cached_expiry"></a>            - **action:** Call \`jdbc\.update\("UPDATE forecasts SET expires\_at=? WHERE place\_id=?", Timestamp\.from\(expires\), id\)\`, then return from \`refresh\`\. The source does not show the database outcome\.
           **When the condition does not hold:**
<a id="block-check_http_status"></a>            - **decision:** [Response status is 200 or 203](#predicate-accepted_status)
              **When the condition holds:**
<a id="block-check_gzip"></a>               - **decision:** [Content\-Encoding is gzip](#predicate-gzip_encoding)
                 **When the condition holds:**
<a id="block-read_last_modified"></a>                  - **action:** Set \`lastModified\` from the \`Last\-Modified\` header, using null if absent\.
                 **When the condition does not hold:**
<a id="block-decode_utf8"></a>                  - **action:** Convert the response body bytes to a string with UTF\-8 and assign it to \`raw\`\.
              **When the condition does not hold:**
<a id="block-reject_http_status"></a>               - **throw:** The source's \`require\` failure message is \`PROVIDER\_HTTP\_\` plus the response status code; exception type and runtime dispatch are not established\.
<a id="block-parse_document"></a>      - **action:** Parse \`raw\` with \`json\.readTree\` into \`document\`\.
<a id="block-create_periods"></a>      - **action:** Create an empty JSON array named \`periods\`\.
<a id="block-check_cache_fresh_repeated_source"></a>      - **decision:** [Cached entry is unexpired](#predicate-cache_fresh)  **Shared preparation:** [Resolve the place key and cache candidate](#preparation-prep_inputs)
        **When the condition holds:**
<a id="block-map_first_six_points"></a>         - **loop:** Visit \`document\["properties"\]\["timeseries"\]\.take\(6\)\`, so the source builds periods from at most the first six points\.
           **Loop body:**
<a id="block-check_temperature"></a>            - **decision:** [Temperature exists and is numeric](#predicate-temperature_valid)
              **When the condition holds:**
<a id="block-construct_period"></a>               - **action:** After the required temperature check, read \`next\` from \`point\["data"\]\["next\_1\_hours"\]\` and create a period with \`time\` from \`point\["time"\]\.asText\(\)\`, \`temperatureC\` from \`temperature\.asDouble\(\)\`, and \`symbol\` from the optional summary symbol\-code chain or \`"unknown"\`\.
              **When the condition does not hold:**
<a id="block-reject_temperature"></a>               - **throw:** The source's \`require\(temperature \!= null &amp;&amp; temperature\.isNumber\)\` fails; the exception type is not established here\.
<a id="block-check_rain"></a>            - **decision:** [Rain is missing or nonnumeric](#predicate-rain_missing_or_nonnumeric)
              **When the condition holds:**
<a id="block-put_null_rain"></a>               - **action:** Set \`period\["precipitationMm"\]\` to JSON null\.
              **When the condition does not hold:**
<a id="block-put_numeric_rain"></a>               - **action:** Set \`period\["precipitationMm"\]\` from \`rain\.asDouble\(\)\`\.
<a id="block-append_period"></a>            - **action:** Append the completed period to \`periods\`\.
<a id="block-check_periods_nonempty"></a>         - **decision:** [At least one period was built](#predicate-periods_nonempty)
           **When the condition holds:**
<a id="block-parse_updated_at"></a>            - **action:** Read \`updated\_at\` as text into \`updatedAt\`, then call \`Instant\.parse\(updatedAt\)\` before constructing the forecast\.
            - **Glossary:** [Forecast payload](#glossary-forecast_payload)
<a id="block-build_forecast"></a>            - **action:** Construct \`forecast\` with \`updatedAt\`, \`Instant\.now\(\)\.toString\(\)\` as \`fetchedAt\`, and \`mode\`; attach \`periods\` under \`periods\`\.
            - **Glossary:** [Forecast payload](#glossary-forecast_payload)
<a id="block-serialize_forecast"></a>            - **action:** Serialize \`forecast\` with \`json\.writeValueAsString\` into \`payload\`\.
            - **Glossary:** [Forecast payload](#glossary-forecast_payload)
<a id="block-upsert_forecast"></a>            - **action:** Call the \`forecasts\` INSERT/ON CONFLICT statement with the place id, parsed update time, payload, expiry, and last\-modified value\. On a \`place\_id\` conflict, its UPDATE clause is guarded by \`EXCLUDED\.updated\_at&gt;=forecasts\.updated\_at\`\. The source records the call, not the database result or transaction completion\.
            - **Glossary:** [Forecast payload](#glossary-forecast_payload)
<a id="block-build_event"></a>            - **action:** After the forecast update call, form \`eventId\` as \`$id:$updatedAt\`; create an event with that id, type \`forecast\.updated\`, version 1, and set its \`place\` and \`forecast\` values\.
            - **Glossary:** [Forecast payload](#glossary-forecast_payload) · [Outbox event](#glossary-outbox_event)
<a id="block-insert_outbox"></a>            - **action:** Serialize \`event\` and call the \`forecast\_outbox\` INSERT statement with \`ON CONFLICT DO NOTHING\`\. This source does not establish delivery, publication, or database completion\.
            - **Glossary:** [Outbox event](#glossary-outbox_event)
           **When the condition does not hold:**
<a id="block-reject_empty_periods"></a>            - **throw:** The source's \`require\(periods\.size\(\) &gt; 0\)\` fails; the exception type is not established here\.
        **When the condition does not hold:**
<a id="block-return_fresh_cache_repeated_source"></a>         - **return:** A fresh cache entry causes an early return before the later work in this method\.
<a id="semantic-predicates"></a>
### Condition meaning and source checks

<details>
<summary id="predicate-cache_fresh">Cached entry is unexpired</summary>

**Condition meaning:** The source condition is \`cached \!= null &amp;&amp; \(cached\["expires\_at"\] as java\.sql\.Timestamp\)\.toInstant\(\)\.isAfter\(Instant\.now\(\)\)\`\.<details class="citations"><summary>Evidence (2)</summary><span class="citation-list">[s28](#evidence-319), [s135](#evidence-240)</span></details>

**Exact source check:** The method queries for a cache row before applying the freshness condition\.<details class="citations"><summary>Evidence (2)</summary><span class="citation-list">[s122](#evidence-231), [s135](#evidence-240)</span></details>

**Evaluation behavior:** The \`&amp;&amp;\` checks \`cached \!= null\` first; only when true does it cast \`expires\_at\` and compare it with \`Instant\.now\(\)\`\. A true result returns early\. A missing or expired cache entry continues to acquisition\.<details class="citations"><summary>Evidence (2)</summary><span class="citation-list">[s28](#evidence-319), [s135](#evidence-240)</span></details>

</details>

<details>
<summary id="predicate-agent_ready">Provider user agent is nonblank</summary>

**Condition meaning:** \`System\.getenv\("MET\_USER\_AGENT"\)?\.takeIf \{ it\.isNotBlank\(\) \}\` yields a value for \`agent\` only when the environment value is non\-null and nonblank\.<details class="citations"><summary>Evidence (2)</summary><span class="citation-list">[s123](#evidence-232), [s132](#evidence-238)</span></details>

**Exact source check:** The method applies the null\-safe \`takeIf\` and uses \`error\("MET\_USER\_AGENT\_REQUIRED"\)\` as the Elvis fallback\.<details class="citations"><summary>Evidence (2)</summary><span class="citation-list">[s9](#evidence-428), [s132](#evidence-238)</span></details>

**Evaluation behavior:** A non\-null, nonblank environment value is bound as \`agent\`\. A null or blank value reaches \`error\("MET\_USER\_AGENT\_REQUIRED"\)\` before backoff checking and the request\.<details class="citations"><summary>Evidence (3)</summary><span class="citation-list">[s9](#evidence-428), [s123](#evidence-232), [s132](#evidence-238)</span></details>

</details>

<details>
<summary id="predicate-has_modified">Cached Last\-Modified value exists</summary>

**Condition meaning:** The source tests \`modified \!= null\`\.<details class="citations"><summary>Evidence (1)</summary><span class="citation-list">[s174](#evidence-261)</span></details>

**Exact source check:** \`modified\` comes from the cached row's \`last\_modified\` value, and the header is added only when it is non\-null\.<details class="citations"><summary>Evidence (2)</summary><span class="citation-list">[s203](#evidence-275), [s335](#evidence-354)</span></details>

**Evaluation behavior:** True adds the \`If\-Modified\-Since\` header with \`modified\`; false omits that header and continues building the request\.<details class="citations"><summary>Evidence (3)</summary><span class="citation-list">[s174](#evidence-261), [s203](#evidence-275), [s335](#evidence-354)</span></details>

</details>

<details>
<summary id="predicate-status_429">Response status is 429</summary>

**Condition meaning:** The source tests \`response\.statusCode\(\) == 429\`\.<details class="citations"><summary>Evidence (1)</summary><span class="citation-list">[s201](#evidence-274)</span></details>

**Exact source check:** The status check selects between the Retry\-After calculation and assigning \`expires\`\.<details class="citations"><summary>Evidence (2)</summary><span class="citation-list">[s26](#evidence-307), [s201](#evidence-274)</span></details>

**Evaluation behavior:** True reads \`Retry\-After\`, uses \`"60"\` when absent, uses \`60L\` when parsing returns null, clamps the seconds to at least 60, then assigns the resulting time to \`nextAttempt\[id\]\`\. False assigns \`expires\` to \`nextAttempt\[id\]\`\.<details class="citations"><summary>Evidence (5)</summary><span class="citation-list">[s26](#evidence-307), [s71](#evidence-416), [s113](#evidence-227), [s201](#evidence-274), [s120](#evidence-230)</span></details>

</details>

<details>
<summary id="predicate-not_modified_with_cache">Response is 304 and a cache row exists</summary>

**Condition meaning:** The source condition is \`response\.statusCode\(\) == 304 &amp;&amp; cached \!= null\`\.<details class="citations"><summary>Evidence (2)</summary><span class="citation-list">[s111](#evidence-225), [s171](#evidence-260)</span></details>

**Exact source check:** On the true branch, the source updates the cached row's expiry and returns before the later accepted\-status check\.<details class="citations"><summary>Evidence (3)</summary><span class="citation-list">[s111](#evidence-225), [s271](#evidence-313), [s326](#evidence-347)</span></details>

**Evaluation behavior:** The \`&amp;&amp;\` checks status 304 first and checks \`cached \!= null\` only when that status matches\. True updates only \`expires\_at\` for the place and returns\. False continues to the accepted\-status requirement; a 304 without a cached row therefore reaches that requirement\.<details class="citations"><summary>Evidence (3)</summary><span class="citation-list">[s111](#evidence-225), [s171](#evidence-260), [s271](#evidence-313)</span></details>

</details>

<details>
<summary id="predicate-accepted_status">Response status is 200 or 203</summary>

**Condition meaning:** The source accepts \`response\.statusCode\(\) == 200 \|\| response\.statusCode\(\) == 203\`\.<details class="citations"><summary>Evidence (2)</summary><span class="citation-list">[s69](#evidence-414), [s385](#evidence-386)</span></details>

**Exact source check:** The accepted\-status \`require\` follows the 304\-with\-cache return branch\.<details class="citations"><summary>Evidence (2)</summary><span class="citation-list">[s288](#evidence-326), [s385](#evidence-386)</span></details>

**Evaluation behavior:** The \`\|\|\` checks for status 200 first and checks for 203 only if the first comparison is false\. True continues to read \`Last\-Modified\` and the response body\. False makes \`require\` fail with the source message \`PROVIDER\_HTTP\_\` followed by the status code\.<details class="citations"><summary>Evidence (3)</summary><span class="citation-list">[s69](#evidence-414), [s288](#evidence-326), [s385](#evidence-386)</span></details>

</details>

<details>
<summary id="predicate-gzip_encoding">Content\-Encoding is gzip</summary>

**Condition meaning:** The source compares the first \`Content\-Encoding\` value, or an empty string, with \`gzip\` ignoring case\.<details class="citations"><summary>Evidence (2)</summary><span class="citation-list">[s353](#evidence-364), [s380](#evidence-383)</span></details>

**Exact source check:** The true and false branches respectively read through \`GZIPInputStream\` or convert the response body to a UTF\-8 string\.<details class="citations"><summary>Evidence (5)</summary><span class="citation-list">[s102](#evidence-219), [s220](#evidence-285), [s233](#evidence-291), [s352](#evidence-363), [s353](#evidence-364)</span></details>

**Evaluation behavior:** The header lookup defaults to an empty string\. A case\-insensitive match for \`gzip\` passes the response bytes through \`GZIPInputStream\` and a buffered reader's \`readText\`; otherwise the response bytes are converted with UTF\-8\.<details class="citations"><summary>Evidence (3)</summary><span class="citation-list">[s102](#evidence-219), [s353](#evidence-364), [s380](#evidence-383)</span></details>

</details>

<details>
<summary id="predicate-temperature_valid">Temperature exists and is numeric</summary>

**Condition meaning:** The source requires \`temperature \!= null &amp;&amp; temperature\.isNumber\`\.<details class="citations"><summary>Evidence (2)</summary><span class="citation-list">[s5](#evidence-403), [s222](#evidence-286)</span></details>

**Exact source check:** The numeric\-temperature requirement is inside the loop and precedes period construction\.<details class="citations"><summary>Evidence (2)</summary><span class="citation-list">[s117](#evidence-228), [s362](#evidence-373)</span></details>

**Evaluation behavior:** The \`&amp;&amp;\` checks \`temperature \!= null\` first and reads \`isNumber\` only when non\-null\. True proceeds to form the period; false makes \`require\` fail before that point is added\.<details class="citations"><summary>Evidence (3)</summary><span class="citation-list">[s5](#evidence-403), [s222](#evidence-286), [s362](#evidence-373)</span></details>

</details>

<details>
<summary id="predicate-rain_missing_or_nonnumeric">Rain is missing or nonnumeric</summary>

**Condition meaning:** The source condition is \`rain == null \|\| \!rain\.isNumber\`\.<details class="citations"><summary>Evidence (2)</summary><span class="citation-list">[s16](#evidence-254), [s30](#evidence-331)</span></details>

**Exact source check:** The source writes JSON null for the true branch and \`rain\.asDouble\(\)\` for the false branch\.<details class="citations"><summary>Evidence (3)</summary><span class="citation-list">[s55](#evidence-406), [s259](#evidence-306), [s273](#evidence-314)</span></details>

**Evaluation behavior:** The \`\|\|\` checks \`rain == null\` first and tests \`\!rain\.isNumber\` only when rain is non\-null\. True puts JSON null in \`precipitationMm\`; false converts rain with \`asDouble\(\)\` and puts that value\.<details class="citations"><summary>Evidence (3)</summary><span class="citation-list">[s16](#evidence-254), [s30](#evidence-331), [s55](#evidence-406)</span></details>

</details>

<details>
<summary id="predicate-periods_nonempty">At least one period was built</summary>

**Condition meaning:** The source requires \`periods\.size\(\) &gt; 0\`\.<details class="citations"><summary>Evidence (1)</summary><span class="citation-list">[s25](#evidence-300)</span></details>

**Exact source check:** The nonempty check follows creation and population of the periods array\.<details class="citations"><summary>Evidence (2)</summary><span class="citation-list">[s25](#evidence-300), [s192](#evidence-268)</span></details>

**Evaluation behavior:** True continues to extract and parse \`updated\_at\`; false makes \`require\` fail before forecast construction and the SQL calls\.<details class="citations"><summary>Evidence (2)</summary><span class="citation-list">[s25](#evidence-300), [s176](#evidence-262)</span></details>

</details>

<a id="preparations"></a>
## Prepared values and checks

<a id="preparation-prep_inputs"></a>
### Resolve the place key and cache candidate

The method takes \`place\` as a \`JsonNode\`, derives its id, and queries for a cache candidate before checking expiry\.<details class="citations"><summary>Evidence (3)</summary><span class="citation-list">[s320](#evidence-344), [s355](#evidence-366), [s122](#evidence-231)</span></details>

**Uncertainty:** The actual input and query result are unknown\.

<a id="block-prep_place_id"></a>1. **action:** Read \`place\["id"\]\.asText\(\)\` into \`id\`\.
<a id="block-prep_cache_query"></a>2. **action:** Call the cache query for \`payload::text,expires\_at,last\_modified\` using \`id\`, then take \`firstOrNull\(\)\` of its returned list\. This selects the first nullable row; it does not filter the list for a fresh row or retry for another\.
  - **Uncertainty:** The query result and runtime completion are unknown\.

<details id="summary" class="full-summary">
<summary>Full summary</summary>

```text
In the retained `refresh(place)` source, the method derives a place id, selects the first cache query row, and returns early if it is unexpired. Otherwise it reads a fixture file or follows the guarded live-request path, maps at most six timeseries points into periods, and calls SQL statements for the forecast and outbox event. This describes source branches and calls, not a runtime trace or confirmed database outcome.
```

<details class="citations"><summary>Evidence (5)</summary><span class="citation-list">[d422](#evidence-182), [s320](#evidence-344), [s117](#evidence-228), [s364](#evidence-375), [s285](#evidence-323)</span></details>

  **Glossary:** [Forecast payload](#glossary-forecast_payload) · [Outbox event](#glossary-outbox_event)

**Uncertainty:** The actual place, mode, cache contents, provider response, invocation, and completion of HTTP or database operations are unknown\.

</details>

<details class="technical-details">
<summary>Technical reference</summary>

<a id="technical-reference"></a>
**Packet digest:** `sha256:483c8d30c979db6894d72359ec7f58191ab55a2f38746df8e1c28318b2f5c0af`

<details class="preparation-technical-reference">
<summary>Preparation source and technical metadata</summary>

### Resolve the place key and cache candidate

- **Source identity:** ``d422`` — d422 · callable:weather/Forecasts\.refresh\#jvm:\(Ltools/jackson/databind/JsonNode;\)V · class:weather/Forecasts · :/main
- **`prep_place_id`:**  (**From:** place: JsonNode parameter · **To:** id)
- **`prep_cache_query`:**  (**From:** id · **To:** cached)


</details>

### Evidence by block

| Meaning block | Block ID | Evidence |
|---|---|---|
| Summary | [``summary``](#summary) | [d422](#evidence-182), [s320](#evidence-344), [s117](#evidence-228), [s364](#evidence-375), [s285](#evidence-323) |
| Forecast payload | [``glossary-forecast_payload``](#glossary-forecast_payload) | [s224](#evidence-287), [s248](#evidence-298), [s321](#evidence-345), [s364](#evidence-375), [s68](#evidence-413) |
| Outbox event | [``glossary-outbox_event``](#glossary-outbox_event) | [s155](#evidence-251), [s200](#evidence-273), [s210](#evidence-279), [s242](#evidence-295), [s285](#evidence-323) |
| Cached entry is unexpired · meaning | [``predicate-cache_fresh-meaning``](#predicate-cache_fresh) | [s28](#evidence-319), [s135](#evidence-240) |
| Cached entry is unexpired · exact source check | [``predicate-cache_fresh-source-check``](#predicate-cache_fresh) | [s122](#evidence-231), [s135](#evidence-240) |
| Cached entry is unexpired · evaluation | [``predicate-cache_fresh-evaluation``](#predicate-cache_fresh) | [s28](#evidence-319), [s135](#evidence-240) |
| Provider user agent is nonblank · meaning | [``predicate-agent_ready-meaning``](#predicate-agent_ready) | [s123](#evidence-232), [s132](#evidence-238) |
| Provider user agent is nonblank · exact source check | [``predicate-agent_ready-source-check``](#predicate-agent_ready) | [s9](#evidence-428), [s132](#evidence-238) |
| Provider user agent is nonblank · evaluation | [``predicate-agent_ready-evaluation``](#predicate-agent_ready) | [s9](#evidence-428), [s123](#evidence-232), [s132](#evidence-238) |
| Cached Last\-Modified value exists · meaning | [``predicate-has_modified-meaning``](#predicate-has_modified) | [s174](#evidence-261) |
| Cached Last\-Modified value exists · exact source check | [``predicate-has_modified-source-check``](#predicate-has_modified) | [s203](#evidence-275), [s335](#evidence-354) |
| Cached Last\-Modified value exists · evaluation | [``predicate-has_modified-evaluation``](#predicate-has_modified) | [s174](#evidence-261), [s203](#evidence-275), [s335](#evidence-354) |
| Response status is 429 · meaning | [``predicate-status_429-meaning``](#predicate-status_429) | [s201](#evidence-274) |
| Response status is 429 · exact source check | [``predicate-status_429-source-check``](#predicate-status_429) | [s26](#evidence-307), [s201](#evidence-274) |
| Response status is 429 · evaluation | [``predicate-status_429-evaluation``](#predicate-status_429) | [s26](#evidence-307), [s71](#evidence-416), [s113](#evidence-227), [s201](#evidence-274), [s120](#evidence-230) |
| Response is 304 and a cache row exists · meaning | [``predicate-not_modified_with_cache-meaning``](#predicate-not_modified_with_cache) | [s111](#evidence-225), [s171](#evidence-260) |
| Response is 304 and a cache row exists · exact source check | [``predicate-not_modified_with_cache-source-check``](#predicate-not_modified_with_cache) | [s111](#evidence-225), [s271](#evidence-313), [s326](#evidence-347) |
| Response is 304 and a cache row exists · evaluation | [``predicate-not_modified_with_cache-evaluation``](#predicate-not_modified_with_cache) | [s111](#evidence-225), [s171](#evidence-260), [s271](#evidence-313) |
| Response status is 200 or 203 · meaning | [``predicate-accepted_status-meaning``](#predicate-accepted_status) | [s69](#evidence-414), [s385](#evidence-386) |
| Response status is 200 or 203 · exact source check | [``predicate-accepted_status-source-check``](#predicate-accepted_status) | [s288](#evidence-326), [s385](#evidence-386) |
| Response status is 200 or 203 · evaluation | [``predicate-accepted_status-evaluation``](#predicate-accepted_status) | [s69](#evidence-414), [s288](#evidence-326), [s385](#evidence-386) |
| Content\-Encoding is gzip · meaning | [``predicate-gzip_encoding-meaning``](#predicate-gzip_encoding) | [s353](#evidence-364), [s380](#evidence-383) |
| Content\-Encoding is gzip · exact source check | [``predicate-gzip_encoding-source-check``](#predicate-gzip_encoding) | [s102](#evidence-219), [s220](#evidence-285), [s233](#evidence-291), [s352](#evidence-363), [s353](#evidence-364) |
| Content\-Encoding is gzip · evaluation | [``predicate-gzip_encoding-evaluation``](#predicate-gzip_encoding) | [s102](#evidence-219), [s353](#evidence-364), [s380](#evidence-383) |
| Temperature exists and is numeric · meaning | [``predicate-temperature_valid-meaning``](#predicate-temperature_valid) | [s5](#evidence-403), [s222](#evidence-286) |
| Temperature exists and is numeric · exact source check | [``predicate-temperature_valid-source-check``](#predicate-temperature_valid) | [s117](#evidence-228), [s362](#evidence-373) |
| Temperature exists and is numeric · evaluation | [``predicate-temperature_valid-evaluation``](#predicate-temperature_valid) | [s5](#evidence-403), [s222](#evidence-286), [s362](#evidence-373) |
| Rain is missing or nonnumeric · meaning | [``predicate-rain_missing_or_nonnumeric-meaning``](#predicate-rain_missing_or_nonnumeric) | [s16](#evidence-254), [s30](#evidence-331) |
| Rain is missing or nonnumeric · exact source check | [``predicate-rain_missing_or_nonnumeric-source-check``](#predicate-rain_missing_or_nonnumeric) | [s55](#evidence-406), [s259](#evidence-306), [s273](#evidence-314) |
| Rain is missing or nonnumeric · evaluation | [``predicate-rain_missing_or_nonnumeric-evaluation``](#predicate-rain_missing_or_nonnumeric) | [s16](#evidence-254), [s30](#evidence-331), [s55](#evidence-406) |
| At least one period was built · meaning | [``predicate-periods_nonempty-meaning``](#predicate-periods_nonempty) | [s25](#evidence-300) |
| At least one period was built · exact source check | [``predicate-periods_nonempty-source-check``](#predicate-periods_nonempty) | [s25](#evidence-300), [s192](#evidence-268) |
| At least one period was built · evaluation | [``predicate-periods_nonempty-evaluation``](#predicate-periods_nonempty) | [s25](#evidence-300), [s176](#evidence-262) |
| Check whether the selected cache row has an expiry after the current time\. | [``step-check_cache_fresh``](#block-check_cache_fresh) | [s28](#evidence-319), [s135](#evidence-240) |
| When \`cache\_fresh\` is true, return from \`refresh\` before source acquisition, transformation, or the later SQL calls\. | [``step-return_fresh_cache``](#block-return_fresh_cache) | [s28](#evidence-319), [s135](#evidence-240) |
| After the cache miss or expiry, initialize \`expires\` to now plus 3600 seconds and \`lastModified\` to null\. | [``step-initialize_defaults``](#block-initialize_defaults) | [s327](#evidence-348), [s376](#evidence-381) |
| Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. | [``step-choose_fixture``](#block-choose_fixture) | [s7](#evidence-415), [s147](#evidence-246) |
| Read \`/app/fixtures/$id\.json\` into \`raw\`\. The file contents are not present in this packet\. | [``step-read_fixture``](#block-read_fixture) | [s7](#evidence-415), [s81](#evidence-423), [s371](#evidence-379) |
| Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. | [``step-check_backoff``](#block-check_backoff) | [s13](#evidence-237), [s80](#evidence-422), [s225](#evidence-288) |
| Require a non\-null, nonblank provider user\-agent value\. | [``step-check_agent``](#block-check_agent) | [s9](#evidence-428), [s132](#evidence-238) |
| Bind the nonblank environment value as \`agent\` for the request\. | [``step-use_agent``](#block-use_agent) | [s9](#evidence-428), [s123](#evidence-232), [s132](#evidence-238) |
| The source invokes \`error\("MET\_USER\_AGENT\_REQUIRED"\)\`; the exception type and dispatch are not established\. | [``step-missing_agent``](#block-missing_agent) | [s9](#evidence-428), [s132](#evidence-238), [s265](#evidence-309) |
| When the next\-attempt instant is after now, the source invokes \`error\("PROVIDER\_BACKOFF"\)\`\. | [``step-backoff_error``](#block-backoff_error) | [s13](#evidence-237), [s80](#evidence-422) |
| Assign \`nextAttempt\[id\] = Instant\.now\(\)\.plusSeconds\(60\)\` before the HTTP send call\. | [``step-seed_next_attempt``](#block-seed_next_attempt) | [s88](#evidence-426), [s225](#evidence-288) |
| Read latitude and longitude from \`place\`, convert each with \`asDouble\(\)\`, then use \`BigDecimal\.valueOf\(\.\.\.\)\.setScale\(4, RoundingMode\.DOWN\)\.toPlainString\(\)\` for the request coordinates\. | [``step-format_coordinates``](#block-format_coordinates) | [s50](#evidence-404), [s53](#evidence-405), [s281](#evidence-320), [s282](#evidence-321), [s289](#evidence-327), [s354](#evidence-365) |
| Build a GET request for the met\.no compact location forecast URL with those coordinates, a 20\-second timeout, \`User\-Agent: agent\`, and \`Accept\-Encoding: gzip\`\. | [``step-build_request``](#block-build_request) | [s14](#evidence-243), [s18](#evidence-265), [s178](#evidence-264), [s340](#evidence-355), [s361](#evidence-372) |
| Read the cached row's \`last\_modified\` value as nullable \`modified\`\. | [``step-read_modified``](#block-read_modified) | [s203](#evidence-275), [s239](#evidence-294), [s351](#evidence-362) |
| Add the conditional request header only when the cached value is non\-null\. | [``step-conditional_header``](#block-conditional_header) | [s87](#evidence-425), [s174](#evidence-261) |
| Add \`If\-Modified\-Since\` with \`modified\`\. | [``step-add_modified_header``](#block-add_modified_header) | [s87](#evidence-425), [s174](#evidence-261), [s335](#evidence-354) |
| Leave \`If\-Modified\-Since\` off the request builder\. | [``step-omit_modified_header``](#block-omit_modified_header) | [s87](#evidence-425), [s174](#evidence-261) |
| Call \`http\.send\(builder\.GET\(\)\.build\(\), HttpResponse\.BodyHandlers\.ofByteArray\(\)\)\`\. The request's runtime outcome is unknown\. | [``step-send_request``](#block-send_request) | [s12](#evidence-229), [s193](#evidence-269), [s306](#evidence-334), [s359](#evidence-370) |
| Set \`expires\` from an \`Expires\` header parsed with \`RFC\_1123\_DATE\_TIME\` and converted to an instant; if the header is absent, use now plus 3600 seconds\. A parse failure is not handled in this source path\. | [``step-derive_expiry``](#block-derive_expiry) | [s150](#evidence-249), [s167](#evidence-258), [s276](#evidence-317), [s398](#evidence-394) |
| Set a minimum retry time for status 429; for other statuses, set the next attempt to \`expires\`\. | [``step-check_429``](#block-check_429) | [s26](#evidence-307), [s78](#evidence-420), [s201](#evidence-274) |
| Use the Retry\-After value or \`"60"\`; if \`toLongOrNull\(\)\` returns null use \`60L\`, clamp to at least \`60L\`, then assign now plus that many seconds to \`nextAttempt\[id\]\`\. | [``step-set_retry_delay``](#block-set_retry_delay) | [s26](#evidence-307), [s71](#evidence-416), [s113](#evidence-227), [s120](#evidence-230), [s134](#evidence-239), [s201](#evidence-274) |
| Assign \`expires\` to \`nextAttempt\[id\]\`\. | [``step-set_expiry_retry``](#block-set_expiry_retry) | [s26](#evidence-307), [s78](#evidence-420) |
| On status 304 with a cached row, update only its expiry and return; otherwise check whether the response status is accepted\. | [``step-check_not_modified``](#block-check_not_modified) | [s111](#evidence-225), [s171](#evidence-260), [s207](#evidence-276) |
| Call \`jdbc\.update\("UPDATE forecasts SET expires\_at=? WHERE place\_id=?", Timestamp\.from\(expires\), id\)\`, then return from \`refresh\`\. The source does not show the database outcome\. | [``step-refresh_cached_expiry``](#block-refresh_cached_expiry) | [s111](#evidence-225), [s271](#evidence-313), [s326](#evidence-347) |
| Only statuses 200 and 203 proceed to capture Last\-Modified and read the response body\. | [``step-check_http_status``](#block-check_http_status) | [s69](#evidence-414), [s288](#evidence-326), [s385](#evidence-386) |
| Read \`raw\` from the response body using the gzip path when the content\-encoding value matches gzip, or UTF\-8 conversion otherwise\. | [``step-check_gzip``](#block-check_gzip) | [s102](#evidence-219), [s353](#evidence-364), [s380](#evidence-383) |
| Set \`lastModified\` from the \`Last\-Modified\` header, using null if absent\. | [``step-read_last_modified``](#block-read_last_modified) | [s4](#evidence-395), [s21](#evidence-278), [s63](#evidence-411) |
| Convert the response body bytes to a string with UTF\-8 and assign it to \`raw\`\. | [``step-decode_utf8``](#block-decode_utf8) | [s102](#evidence-219), [s314](#evidence-339), [s352](#evidence-363) |
| The source's \`require\` failure message is \`PROVIDER\_HTTP\_\` plus the response status code; exception type and runtime dispatch are not established\. | [``step-reject_http_status``](#block-reject_http_status) | [s64](#evidence-412), [s89](#evidence-427), [s288](#evidence-326) |
| Parse \`raw\` with \`json\.readTree\` into \`document\`\. | [``step-parse_document``](#block-parse_document) | [s128](#evidence-236), [s245](#evidence-296) |
| Create an empty JSON array named \`periods\`\. | [``step-create_periods``](#block-create_periods) | [s192](#evidence-268), [s286](#evidence-324) |
| Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. | [``step-check_cache_fresh_repeated_source``](#block-check_cache_fresh_repeated_source) | [s28](#evidence-319), [s135](#evidence-240) |
| Visit \`document\["properties"\]\["timeseries"\]\.take\(6\)\`, so the source builds periods from at most the first six points\. | [``step-map_first_six_points``](#block-map_first_six_points) | [s47](#evidence-400), [s117](#evidence-228), [s365](#evidence-376) |
| Require each visited point to have a non\-null numeric air temperature before constructing its period\. | [``step-check_temperature``](#block-check_temperature) | [s5](#evidence-403), [s222](#evidence-286), [s362](#evidence-373) |
| After the required temperature check, read \`next\` from \`point\["data"\]\["next\_1\_hours"\]\` and create a period with \`time\` from \`point\["time"\]\.asText\(\)\`, \`temperatureC\` from \`temperature\.asDouble\(\)\`, and \`symbol\` from the optional summary symbol\-code chain or \`"unknown"\`\. | [``step-construct_period``](#block-construct_period) | [s33](#evidence-350), [s43](#evidence-398), [s117](#evidence-228), [s194](#evidence-270), [s235](#evidence-293), [s307](#evidence-335), [s350](#evidence-361) |
| The source's \`require\(temperature \!= null &amp;&amp; temperature\.isNumber\)\` fails; the exception type is not established here\. | [``step-reject_temperature``](#block-reject_temperature) | [s5](#evidence-403), [s362](#evidence-373) |
| Use JSON null when precipitation is missing or nonnumeric\. | [``step-check_rain``](#block-check_rain) | [s16](#evidence-254), [s30](#evidence-331), [s55](#evidence-406) |
| Set \`period\["precipitationMm"\]\` to JSON null\. | [``step-put_null_rain``](#block-put_null_rain) | [s16](#evidence-254), [s55](#evidence-406), [s259](#evidence-306) |
| Set \`period\["precipitationMm"\]\` from \`rain\.asDouble\(\)\`\. | [``step-put_numeric_rain``](#block-put_numeric_rain) | [s48](#evidence-401), [s55](#evidence-406), [s273](#evidence-314) |
| Append the completed period to \`periods\`\. | [``step-append_period``](#block-append_period) | [s117](#evidence-228), [s277](#evidence-318), [s365](#evidence-376) |
| Require at least one period before reading and validating \`updated\_at\` or making the forecast and outbox SQL calls\. | [``step-check_periods_nonempty``](#block-check_periods_nonempty) | [s25](#evidence-300), [s176](#evidence-262) |
| Read \`updated\_at\` as text into \`updatedAt\`, then call \`Instant\.parse\(updatedAt\)\` before constructing the forecast\. | [``step-parse_updated_at``](#block-parse_updated_at) | [s105](#evidence-221), [s187](#evidence-266), [s261](#evidence-308), [s317](#evidence-341) |
| Construct \`forecast\` with \`updatedAt\`, \`Instant\.now\(\)\.toString\(\)\` as \`fetchedAt\`, and \`mode\`; attach \`periods\` under \`periods\`\. | [``step-build_forecast``](#block-build_forecast) | [s60](#evidence-408), [s224](#evidence-287), [s248](#evidence-298) |
| Serialize \`forecast\` with \`json\.writeValueAsString\` into \`payload\`\. | [``step-serialize_forecast``](#block-serialize_forecast) | [s127](#evidence-235), [s321](#evidence-345) |
| Call the \`forecasts\` INSERT/ON CONFLICT statement with the place id, parsed update time, payload, expiry, and last\-modified value\. On a \`place\_id\` conflict, its UPDATE clause is guarded by \`EXCLUDED\.updated\_at&gt;=forecasts\.updated\_at\`\. The source records the call, not the database result or transaction completion\. | [``step-upsert_forecast``](#block-upsert_forecast) | [s364](#evidence-375) |
| After the forecast update call, form \`eventId\` as \`$id:$updatedAt\`; create an event with that id, type \`forecast\.updated\`, version 1, and set its \`place\` and \`forecast\` values\. | [``step-build_event``](#block-build_event) | [s155](#evidence-251), [s200](#evidence-273), [s210](#evidence-279), [s242](#evidence-295), [s296](#evidence-329), [s68](#evidence-413) |
| Serialize \`event\` and call the \`forecast\_outbox\` INSERT statement with \`ON CONFLICT DO NOTHING\`\. This source does not establish delivery, publication, or database completion\. | [``step-insert_outbox``](#block-insert_outbox) | [s285](#evidence-323), [s368](#evidence-378) |
| The source's \`require\(periods\.size\(\) &gt; 0\)\` fails; the exception type is not established here\. | [``step-reject_empty_periods``](#block-reject_empty_periods) | [s25](#evidence-300) |
| A fresh cache entry causes an early return before the later work in this method\. | [``step-return_fresh_cache_repeated_source``](#block-return_fresh_cache_repeated_source) | [s28](#evidence-319), [s135](#evidence-240) |
| Resolve the place key and cache candidate | [``preparation-prep_inputs``](#preparation-prep_inputs) | [s320](#evidence-344), [s355](#evidence-366), [s122](#evidence-231) |
| Read \`place\["id"\]\.asText\(\)\` into \`id\`\. | [``step-prep_place_id``](#block-prep_place_id) | [s320](#evidence-344), [s355](#evidence-366) |
| Call the cache query for \`payload::text,expires\_at,last\_modified\` using \`id\`, then take \`firstOrNull\(\)\` of its returned list\. This selects the first nullable row; it does not filter the list for a fresh row or retry for another\. | [``step-prep_cache_query``](#block-prep_cache_query) | [s122](#evidence-231), [s320](#evidence-344), [d334](#evidence-149) |

<a id="data-movement"></a>
## Data movement stated in steps

This view contains only explicit from/to values in authored steps; matching names do not create a link\.

| Context | From | To | Step | Evidence | Uncertainty |
|---|---|---|---|---|---|
| Operation | cached | return or acquisition | [decision](#block-check_cache_fresh) — Check whether the selected cache row has an expiry after the current time\. | [s28](#evidence-319), [s135](#evidence-240) | — |
| Operation → When the condition holds: Check whether the selected cache row has an expiry after the current time\. | cached | Unknown | [return](#block-return_fresh_cache) — When \`cache\_fresh\` is true, return from \`refresh\` before source acquisition, transformation, or the later SQL calls\. | [s28](#evidence-319), [s135](#evidence-240) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. | current time | expires; lastModified | [action](#block-initialize_defaults) — After the cache miss or expiry, initialize \`expires\` to now plus 3600 seconds and \`lastModified\` to null\. | [s327](#evidence-348), [s376](#evidence-381) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. | mode | return or acquisition | [decision](#block-choose_fixture) — Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. | [s7](#evidence-415), [s147](#evidence-246) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition holds: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. | id | raw | [action](#block-read_fixture) — Read \`/app/fixtures/$id\.json\` into \`raw\`\. The file contents are not present in this packet\. | [s7](#evidence-415), [s81](#evidence-423), [s371](#evidence-379) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. | nextAttempt\[id\] | nextAttempt\[id\] | [decision](#block-check_backoff) — Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. | [s13](#evidence-237), [s80](#evidence-422), [s225](#evidence-288) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. | System\.getenv\("MET\_USER\_AGENT"\) | agent or error | [decision](#block-check_agent) — Require a non\-null, nonblank provider user\-agent value\. | [s9](#evidence-428), [s132](#evidence-238) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. → When the condition holds: Require a non\-null, nonblank provider user\-agent value\. | MET\_USER\_AGENT | agent | [action](#block-use_agent) — Bind the nonblank environment value as \`agent\` for the request\. | [s9](#evidence-428), [s123](#evidence-232), [s132](#evidence-238) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. → When the condition does not hold: Require a non\-null, nonblank provider user\-agent value\. | environment lookup | Unknown | [throw](#block-missing_agent) — The source invokes \`error\("MET\_USER\_AGENT\_REQUIRED"\)\`; the exception type and dispatch are not established\. | [s9](#evidence-428), [s132](#evidence-238), [s265](#evidence-309) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. | nextAttempt\[id\] | Unknown | [throw](#block-backoff_error) — When the next\-attempt instant is after now, the source invokes \`error\("PROVIDER\_BACKOFF"\)\`\. | [s13](#evidence-237), [s80](#evidence-422) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. | current time | nextAttempt\[id\] | [action](#block-seed_next_attempt) — Assign \`nextAttempt\[id\] = Instant\.now\(\)\.plusSeconds\(60\)\` before the HTTP send call\. | [s88](#evidence-426), [s225](#evidence-288) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. | place\["latitude"\], place\["longitude"\] | lat, lon | [action](#block-format_coordinates) — Read latitude and longitude from \`place\`, convert each with \`asDouble\(\)\`, then use \`BigDecimal\.valueOf\(\.\.\.\)\.setScale\(4, RoundingMode\.DOWN\)\.toPlainString\(\)\` for the request coordinates\. | [s50](#evidence-404), [s53](#evidence-405), [s281](#evidence-320), [s282](#evidence-321), [s289](#evidence-327), [s354](#evidence-365) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. | lat, lon, agent | HttpRequest\.Builder | [action](#block-build_request) — Build a GET request for the met\.no compact location forecast URL with those coordinates, a 20\-second timeout, \`User\-Agent: agent\`, and \`Accept\-Encoding: gzip\`\. | [s14](#evidence-243), [s18](#evidence-265), [s178](#evidence-264), [s340](#evidence-355), [s361](#evidence-372) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. | cached\["last\_modified"\] | modified | [action](#block-read_modified) — Read the cached row's \`last\_modified\` value as nullable \`modified\`\. | [s203](#evidence-275), [s239](#evidence-294), [s351](#evidence-362) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. | modified | request builder | [decision](#block-conditional_header) — Add the conditional request header only when the cached value is non\-null\. | [s87](#evidence-425), [s174](#evidence-261) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. → When the condition holds: Add the conditional request header only when the cached value is non\-null\. | modified | request builder | [action](#block-add_modified_header) — Add \`If\-Modified\-Since\` with \`modified\`\. | [s87](#evidence-425), [s174](#evidence-261), [s335](#evidence-354) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. → When the condition does not hold: Add the conditional request header only when the cached value is non\-null\. | modified | request builder | [action](#block-omit_modified_header) — Leave \`If\-Modified\-Since\` off the request builder\. | [s87](#evidence-425), [s174](#evidence-261) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. | request builder | response | [action](#block-send_request) — Call \`http\.send\(builder\.GET\(\)\.build\(\), HttpResponse\.BodyHandlers\.ofByteArray\(\)\)\`\. The request's runtime outcome is unknown\. | [s12](#evidence-229), [s193](#evidence-269), [s306](#evidence-334), [s359](#evidence-370) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. | response\.headers\(\)\.firstValue\("Expires"\) | expires | [action](#block-derive_expiry) — Set \`expires\` from an \`Expires\` header parsed with \`RFC\_1123\_DATE\_TIME\` and converted to an instant; if the header is absent, use now plus 3600 seconds\. A parse failure is not handled in this source path\. | [s150](#evidence-249), [s167](#evidence-258), [s276](#evidence-317), [s398](#evidence-394) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. | response\.statusCode\(\) | nextAttempt\[id\] | [decision](#block-check_429) — Set a minimum retry time for status 429; for other statuses, set the next attempt to \`expires\`\. | [s26](#evidence-307), [s78](#evidence-420), [s201](#evidence-274) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. → When the condition holds: Set a minimum retry time for status 429; for other statuses, set the next attempt to \`expires\`\. | response\.headers\(\)\.firstValue\("Retry\-After"\) | nextAttempt\[id\] | [action](#block-set_retry_delay) — Use the Retry\-After value or \`"60"\`; if \`toLongOrNull\(\)\` returns null use \`60L\`, clamp to at least \`60L\`, then assign now plus that many seconds to \`nextAttempt\[id\]\`\. | [s26](#evidence-307), [s71](#evidence-416), [s113](#evidence-227), [s120](#evidence-230), [s134](#evidence-239), [s201](#evidence-274) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. → When the condition does not hold: Set a minimum retry time for status 429; for other statuses, set the next attempt to \`expires\`\. | expires | nextAttempt\[id\] | [action](#block-set_expiry_retry) — Assign \`expires\` to \`nextAttempt\[id\]\`\. | [s26](#evidence-307), [s78](#evidence-420) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. | response\.statusCode\(\), cached | return or status check | [decision](#block-check_not_modified) — On status 304 with a cached row, update only its expiry and return; otherwise check whether the response status is accepted\. | [s111](#evidence-225), [s171](#evidence-260), [s207](#evidence-276) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. → When the condition holds: On status 304 with a cached row, update only its expiry and return; otherwise check whether the response status is accepted\. | response, cached, expires | return | [action](#block-refresh_cached_expiry) — Call \`jdbc\.update\("UPDATE forecasts SET expires\_at=? WHERE place\_id=?", Timestamp\.from\(expires\), id\)\`, then return from \`refresh\`\. The source does not show the database outcome\. | [s111](#evidence-225), [s271](#evidence-313), [s326](#evidence-347) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. → When the condition does not hold: On status 304 with a cached row, update only its expiry and return; otherwise check whether the response status is accepted\. | response\.statusCode\(\) | raw | [decision](#block-check_http_status) — Only statuses 200 and 203 proceed to capture Last\-Modified and read the response body\. | [s69](#evidence-414), [s288](#evidence-326), [s385](#evidence-386) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. → When the condition does not hold: On status 304 with a cached row, update only its expiry and return; otherwise check whether the response status is accepted\. → When the condition holds: Only statuses 200 and 203 proceed to capture Last\-Modified and read the response body\. | response\.headers\(\)\.firstValue\("Content\-Encoding"\) | raw | [decision](#block-check_gzip) — Read \`raw\` from the response body using the gzip path when the content\-encoding value matches gzip, or UTF\-8 conversion otherwise\. | [s102](#evidence-219), [s353](#evidence-364), [s380](#evidence-383) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. → When the condition does not hold: On status 304 with a cached row, update only its expiry and return; otherwise check whether the response status is accepted\. → When the condition holds: Only statuses 200 and 203 proceed to capture Last\-Modified and read the response body\. → When the condition holds: Read \`raw\` from the response body using the gzip path when the content\-encoding value matches gzip, or UTF\-8 conversion otherwise\. | response\.headers\(\)\.firstValue\("Last\-Modified"\) | lastModified | [action](#block-read_last_modified) — Set \`lastModified\` from the \`Last\-Modified\` header, using null if absent\. | [s4](#evidence-395), [s21](#evidence-278), [s63](#evidence-411) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. → When the condition does not hold: On status 304 with a cached row, update only its expiry and return; otherwise check whether the response status is accepted\. → When the condition holds: Only statuses 200 and 203 proceed to capture Last\-Modified and read the response body\. → When the condition does not hold: Read \`raw\` from the response body using the gzip path when the content\-encoding value matches gzip, or UTF\-8 conversion otherwise\. | response\.body\(\) | raw | [action](#block-decode_utf8) — Convert the response body bytes to a string with UTF\-8 and assign it to \`raw\`\. | [s102](#evidence-219), [s314](#evidence-339), [s352](#evidence-363) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\. → When the condition does not hold: On status 304 with a cached row, update only its expiry and return; otherwise check whether the response status is accepted\. → When the condition does not hold: Only statuses 200 and 203 proceed to capture Last\-Modified and read the response body\. | response\.statusCode\(\) | Unknown | [throw](#block-reject_http_status) — The source's \`require\` failure message is \`PROVIDER\_HTTP\_\` plus the response status code; exception type and runtime dispatch are not established\. | [s64](#evidence-412), [s89](#evidence-427), [s288](#evidence-326) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. | raw | document | [action](#block-parse_document) — Parse \`raw\` with \`json\.readTree\` into \`document\`\. | [s128](#evidence-236), [s245](#evidence-296) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. | document | periods | [action](#block-create_periods) — Create an empty JSON array named \`periods\`\. | [s192](#evidence-268), [s286](#evidence-324) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. | cached | return or acquisition | [decision](#block-check_cache_fresh_repeated_source) — Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. | [s28](#evidence-319), [s135](#evidence-240) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. | document\["properties"\]\["timeseries"\] | periods | [loop](#block-map_first_six_points) — Visit \`document\["properties"\]\["timeseries"\]\.take\(6\)\`, so the source builds periods from at most the first six points\. | [s47](#evidence-400), [s117](#evidence-228), [s365](#evidence-376) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. → Loop body: Visit \`document\["properties"\]\["timeseries"\]\.take\(6\)\`, so the source builds periods from at most the first six points\. | point\["data"\]\["instant"\]\["details"\]\["air\_temperature"\] | period or failure | [decision](#block-check_temperature) — Require each visited point to have a non\-null numeric air temperature before constructing its period\. | [s5](#evidence-403), [s222](#evidence-286), [s362](#evidence-373) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. → Loop body: Visit \`document\["properties"\]\["timeseries"\]\.take\(6\)\`, so the source builds periods from at most the first six points\. → When the condition holds: Require each visited point to have a non\-null numeric air temperature before constructing its period\. | point | period | [action](#block-construct_period) — After the required temperature check, read \`next\` from \`point\["data"\]\["next\_1\_hours"\]\` and create a period with \`time\` from \`point\["time"\]\.asText\(\)\`, \`temperatureC\` from \`temperature\.asDouble\(\)\`, and \`symbol\` from the optional summary symbol\-code chain or \`"unknown"\`\. | [s33](#evidence-350), [s43](#evidence-398), [s117](#evidence-228), [s194](#evidence-270), [s235](#evidence-293), [s307](#evidence-335), [s350](#evidence-361) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. → Loop body: Visit \`document\["properties"\]\["timeseries"\]\.take\(6\)\`, so the source builds periods from at most the first six points\. → When the condition does not hold: Require each visited point to have a non\-null numeric air temperature before constructing its period\. | temperature | Unknown | [throw](#block-reject_temperature) — The source's \`require\(temperature \!= null &amp;&amp; temperature\.isNumber\)\` fails; the exception type is not established here\. | [s5](#evidence-403), [s362](#evidence-373) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. → Loop body: Visit \`document\["properties"\]\["timeseries"\]\.take\(6\)\`, so the source builds periods from at most the first six points\. | rain | period | [decision](#block-check_rain) — Use JSON null when precipitation is missing or nonnumeric\. | [s16](#evidence-254), [s30](#evidence-331), [s55](#evidence-406) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. → Loop body: Visit \`document\["properties"\]\["timeseries"\]\.take\(6\)\`, so the source builds periods from at most the first six points\. → When the condition holds: Use JSON null when precipitation is missing or nonnumeric\. | next\["details"\]\["precipitation\_amount"\] | period | [action](#block-put_null_rain) — Set \`period\["precipitationMm"\]\` to JSON null\. | [s16](#evidence-254), [s55](#evidence-406), [s259](#evidence-306) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. → Loop body: Visit \`document\["properties"\]\["timeseries"\]\.take\(6\)\`, so the source builds periods from at most the first six points\. → When the condition does not hold: Use JSON null when precipitation is missing or nonnumeric\. | rain | period | [action](#block-put_numeric_rain) — Set \`period\["precipitationMm"\]\` from \`rain\.asDouble\(\)\`\. | [s48](#evidence-401), [s55](#evidence-406), [s273](#evidence-314) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. → Loop body: Visit \`document\["properties"\]\["timeseries"\]\.take\(6\)\`, so the source builds periods from at most the first six points\. | period | periods | [action](#block-append_period) — Append the completed period to \`periods\`\. | [s117](#evidence-228), [s277](#evidence-318), [s365](#evidence-376) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. | periods | forecast and outbox SQL calls | [decision](#block-check_periods_nonempty) — Require at least one period before reading and validating \`updated\_at\` or making the forecast and outbox SQL calls\. | [s25](#evidence-300), [s176](#evidence-262) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. → When the condition holds: Require at least one period before reading and validating \`updated\_at\` or making the forecast and outbox SQL calls\. | document\["properties"\]\["meta"\]\["updated\_at"\] | updatedAt | [action](#block-parse_updated_at) — Read \`updated\_at\` as text into \`updatedAt\`, then call \`Instant\.parse\(updatedAt\)\` before constructing the forecast\. | [s105](#evidence-221), [s187](#evidence-266), [s261](#evidence-308), [s317](#evidence-341) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. → When the condition holds: Require at least one period before reading and validating \`updated\_at\` or making the forecast and outbox SQL calls\. | updatedAt, periods, mode, current time | forecast | [action](#block-build_forecast) — Construct \`forecast\` with \`updatedAt\`, \`Instant\.now\(\)\.toString\(\)\` as \`fetchedAt\`, and \`mode\`; attach \`periods\` under \`periods\`\. | [s60](#evidence-408), [s224](#evidence-287), [s248](#evidence-298) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. → When the condition holds: Require at least one period before reading and validating \`updated\_at\` or making the forecast and outbox SQL calls\. | forecast | payload | [action](#block-serialize_forecast) — Serialize \`forecast\` with \`json\.writeValueAsString\` into \`payload\`\. | [s127](#evidence-235), [s321](#evidence-345) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. → When the condition holds: Require at least one period before reading and validating \`updated\_at\` or making the forecast and outbox SQL calls\. | id, updatedAt, payload, expires, lastModified | forecasts row operation | [action](#block-upsert_forecast) — Call the \`forecasts\` INSERT/ON CONFLICT statement with the place id, parsed update time, payload, expiry, and last\-modified value\. On a \`place\_id\` conflict, its UPDATE clause is guarded by \`EXCLUDED\.updated\_at&gt;=forecasts\.updated\_at\`\. The source records the call, not the database result or transaction completion\. | [s364](#evidence-375) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. → When the condition holds: Require at least one period before reading and validating \`updated\_at\` or making the forecast and outbox SQL calls\. | id, updatedAt, place, forecast | event | [action](#block-build_event) — After the forecast update call, form \`eventId\` as \`$id:$updatedAt\`; create an event with that id, type \`forecast\.updated\`, version 1, and set its \`place\` and \`forecast\` values\. | [s155](#evidence-251), [s200](#evidence-273), [s210](#evidence-279), [s242](#evidence-295), [s296](#evidence-329), [s68](#evidence-413) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. → When the condition holds: Require at least one period before reading and validating \`updated\_at\` or making the forecast and outbox SQL calls\. | event | outbox row operation | [action](#block-insert_outbox) — Serialize \`event\` and call the \`forecast\_outbox\` INSERT statement with \`ON CONFLICT DO NOTHING\`\. This source does not establish delivery, publication, or database completion\. | [s285](#evidence-323), [s368](#evidence-378) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition holds: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. → When the condition does not hold: Require at least one period before reading and validating \`updated\_at\` or making the forecast and outbox SQL calls\. | periods | Unknown | [throw](#block-reject_empty_periods) — The source's \`require\(periods\.size\(\) &gt; 0\)\` fails; the exception type is not established here\. | [s25](#evidence-300) | — |
| Operation → When the condition does not hold: Check whether the selected cache row has an expiry after the current time\. → When the condition does not hold: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\. → When the condition does not hold: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\. | cached | Unknown | [return](#block-return_fresh_cache_repeated_source) — A fresh cache entry causes an early return before the later work in this method\. | [s28](#evidence-319), [s135](#evidence-240) | — |
| Prepared values and checks: Resolve the place key and cache candidate \[Uncertainty: The actual input and query result are unknown\.\] | place: JsonNode parameter | id | [action](#block-prep_place_id) — Read \`place\["id"\]\.asText\(\)\` into \`id\`\. | [s320](#evidence-344), [s355](#evidence-366) | — |
| Prepared values and checks: Resolve the place key and cache candidate \[Uncertainty: The actual input and query result are unknown\.\] | id | cached | [action](#block-prep_cache_query) — Call the cache query for \`payload::text,expires\_at,last\_modified\` using \`id\`, then take \`firstOrNull\(\)\` of its returned list\. This selects the first nullable row; it does not filter the list for a fresh row or retry for another\. | [s122](#evidence-231), [s320](#evidence-344), [d334](#evidence-149) | **Uncertainty:** The query result and runtime completion are unknown\. |

<a id="cited-evidence"></a>
## Cited evidence

<a id="evidence-149"></a>- **d334** — retained callsite evidence  _(source: [`src/main/kotlin/weather/Forecasts.kt`:72–72](#source-82))_
<a id="evidence-182"></a>- **d422** — exact internal process root  _(source: [`src/main/kotlin/weather/Forecasts.kt`:70–125](#source-69))_
<a id="evidence-219"></a>- **s102** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:100–100](#source-1))_
<a id="evidence-221"></a>- **s105** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:119–119](#source-2))_
<a id="evidence-225"></a>- **s111** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:94–94](#source-3))_
<a id="evidence-227"></a>- **s113** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:92–92](#source-4))_
<a id="evidence-228"></a>- **s117** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:104–112](#source-5))_
<a id="evidence-229"></a>- **s12** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:88–88](#source-6))_
<a id="evidence-230"></a>- **s120** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:91–91](#source-7))_
<a id="evidence-231"></a>- **s122** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:72–72](#source-8))_
<a id="evidence-232"></a>- **s123** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:80–80](#source-9))_
<a id="evidence-235"></a>- **s127** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:118–118](#source-10))_
<a id="evidence-236"></a>- **s128** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:102–102](#source-11))_
<a id="evidence-237"></a>- **s13** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:81–81](#source-12))_
<a id="evidence-238"></a>- **s132** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:80–80](#source-13))_
<a id="evidence-239"></a>- **s134** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:92–92](#source-14))_
<a id="evidence-240"></a>- **s135** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:73–73](#source-15))_
<a id="evidence-243"></a>- **s14** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:85–85](#source-16))_
<a id="evidence-246"></a>- **s147** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:76–101](#source-17))_
<a id="evidence-249"></a>- **s150** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:89–89](#source-18))_
<a id="evidence-251"></a>- **s155** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:122–122](#source-19))_
<a id="evidence-254"></a>- **s16** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:110–110](#source-20))_
<a id="evidence-258"></a>- **s167** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:89–89](#source-21))_
<a id="evidence-260"></a>- **s171** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:94–94](#source-22))_
<a id="evidence-261"></a>- **s174** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:87–87](#source-23))_
<a id="evidence-262"></a>- **s176** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:113–113](#source-24))_
<a id="evidence-264"></a>- **s178** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:85–85](#source-25))_
<a id="evidence-265"></a>- **s18** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:85–85](#source-26))_
<a id="evidence-266"></a>- **s187** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:114–114](#source-27))_
<a id="evidence-268"></a>- **s192** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:103–103](#source-28))_
<a id="evidence-269"></a>- **s193** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:88–88](#source-29))_
<a id="evidence-270"></a>- **s194** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:108–108](#source-30))_
<a id="evidence-273"></a>- **s200** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:121–121](#source-31))_
<a id="evidence-274"></a>- **s201** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:90–90](#source-32))_
<a id="evidence-275"></a>- **s203** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:86–86](#source-33))_
<a id="evidence-276"></a>- **s207** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:94–94](#source-34))_
<a id="evidence-278"></a>- **s21** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:99–99](#source-35))_
<a id="evidence-279"></a>- **s210** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:120–120](#source-36))_
<a id="evidence-285"></a>- **s220** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:100–100](#source-37))_
<a id="evidence-286"></a>- **s222** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:106–106](#source-38))_
<a id="evidence-287"></a>- **s224** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:116–116](#source-39))_
<a id="evidence-288"></a>- **s225** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:82–82](#source-40))_
<a id="evidence-291"></a>- **s233** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:100–100](#source-41))_
<a id="evidence-293"></a>- **s235** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:105–105](#source-42))_
<a id="evidence-294"></a>- **s239** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:86–86](#source-43))_
<a id="evidence-295"></a>- **s242** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:121–121](#source-44))_
<a id="evidence-296"></a>- **s245** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:102–102](#source-45))_
<a id="evidence-298"></a>- **s248** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:117–117](#source-46))_
<a id="evidence-300"></a>- **s25** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:113–113](#source-47))_
<a id="evidence-306"></a>- **s259** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:110–110](#source-48))_
<a id="evidence-307"></a>- **s26** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:90–93](#source-49))_
<a id="evidence-308"></a>- **s261** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:115–115](#source-50))_
<a id="evidence-309"></a>- **s265** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:80–80](#source-51))_
<a id="evidence-313"></a>- **s271** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:95–95](#source-52))_
<a id="evidence-314"></a>- **s273** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:110–110](#source-53))_
<a id="evidence-317"></a>- **s276** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:89–89](#source-54))_
<a id="evidence-318"></a>- **s277** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:111–111](#source-55))_
<a id="evidence-319"></a>- **s28** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:73–73](#source-56))_
<a id="evidence-320"></a>- **s281** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:84–84](#source-57))_
<a id="evidence-321"></a>- **s282** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:84–84](#source-58))_
<a id="evidence-323"></a>- **s285** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:124–124](#source-59))_
<a id="evidence-324"></a>- **s286** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:103–103](#source-60))_
<a id="evidence-326"></a>- **s288** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:98–98](#source-61))_
<a id="evidence-327"></a>- **s289** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:84–84](#source-62))_
<a id="evidence-329"></a>- **s296** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:121–121](#source-63))_
<a id="evidence-331"></a>- **s30** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:110–110](#source-64))_
<a id="evidence-334"></a>- **s306** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:88–88](#source-65))_
<a id="evidence-335"></a>- **s307** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:108–108](#source-66))_
<a id="evidence-339"></a>- **s314** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:100–100](#source-67))_
<a id="evidence-341"></a>- **s317** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:114–114](#source-68))_
<a id="evidence-344"></a>- **s320** — retained callable source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:70–125](#source-69))_
<a id="evidence-345"></a>- **s321** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:118–118](#source-70))_
<a id="evidence-347"></a>- **s326** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:94–97](#source-71))_
<a id="evidence-348"></a>- **s327** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:74–74](#source-72))_
<a id="evidence-350"></a>- **s33** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:108–108](#source-73))_
<a id="evidence-354"></a>- **s335** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:87–87](#source-74))_
<a id="evidence-355"></a>- **s340** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:85–85](#source-75))_
<a id="evidence-361"></a>- **s350** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:108–108](#source-76))_
<a id="evidence-362"></a>- **s351** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:86–86](#source-77))_
<a id="evidence-363"></a>- **s352** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:100–100](#source-78))_
<a id="evidence-364"></a>- **s353** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:100–100](#source-79))_
<a id="evidence-365"></a>- **s354** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:83–83](#source-80))_
<a id="evidence-366"></a>- **s355** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:71–71](#source-81))_
<a id="evidence-370"></a>- **s359** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:88–88](#source-83))_
<a id="evidence-372"></a>- **s361** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:85–85](#source-84))_
<a id="evidence-373"></a>- **s362** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:106–106](#source-85))_
<a id="evidence-375"></a>- **s364** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:119–119](#source-86))_
<a id="evidence-376"></a>- **s365** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:104–112](#source-87))_
<a id="evidence-378"></a>- **s368** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:124–124](#source-88))_
<a id="evidence-379"></a>- **s371** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:77–77](#source-89))_
<a id="evidence-381"></a>- **s376** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:75–75](#source-90))_
<a id="evidence-383"></a>- **s380** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:100–100](#source-91))_
<a id="evidence-386"></a>- **s385** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:98–98](#source-92))_
<a id="evidence-394"></a>- **s398** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:89–89](#source-93))_
<a id="evidence-395"></a>- **s4** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:99–99](#source-94))_
<a id="evidence-398"></a>- **s43** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:108–108](#source-95))_
<a id="evidence-400"></a>- **s47** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:104–104](#source-96))_
<a id="evidence-401"></a>- **s48** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:110–110](#source-97))_
<a id="evidence-403"></a>- **s5** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:106–106](#source-98))_
<a id="evidence-404"></a>- **s50** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:83–83](#source-99))_
<a id="evidence-405"></a>- **s53** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:83–83](#source-100))_
<a id="evidence-406"></a>- **s55** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:110–110](#source-101))_
<a id="evidence-408"></a>- **s60** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:116–116](#source-102))_
<a id="evidence-411"></a>- **s63** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:99–99](#source-103))_
<a id="evidence-412"></a>- **s64** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:98–98](#source-104))_
<a id="evidence-413"></a>- **s68** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:123–123](#source-105))_
<a id="evidence-414"></a>- **s69** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:98–98](#source-106))_
<a id="evidence-415"></a>- **s7** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:76–76](#source-107))_
<a id="evidence-416"></a>- **s71** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:91–91](#source-108))_
<a id="evidence-420"></a>- **s78** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:90–93](#source-109))_
<a id="evidence-422"></a>- **s80** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:81–81](#source-110))_
<a id="evidence-423"></a>- **s81** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:77–77](#source-111))_
<a id="evidence-425"></a>- **s87** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:87–87](#source-112))_
<a id="evidence-426"></a>- **s88** — retained callsite source  _(source: [`src/main/kotlin/weather/Forecasts.kt`:82–82](#source-113))_
<a id="evidence-427"></a>- **s89** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:98–98](#source-114))_
<a id="evidence-428"></a>- **s9** — Retained source data  _(source: [`src/main/kotlin/weather/Forecasts.kt`:80–80](#source-115))_

<a id="source-locations"></a>
## Retained source locations

<a id="source-1"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 100–100 _(s102)_

<details>
<summary>View retained excerpt</summary>

```text
if (response.headers().firstValue("Content-Encoding").orElse("").equals("gzip", ignoreCase = true)) GZIPInputStream(ByteArrayInputStream(response.body())).bufferedReader().use { it.readText() } else response.body().toString(Charsets.UTF_8)
```
</details>


**Process blocks citing this excerpt:** [decision: Read \`raw\` from the response body using the gzip path when the content\-encoding value matches gzip, or UTF\-8 conversion otherwise\.](#block-check_gzip) · [action: Convert the response body bytes to a string with UTF\-8 and assign it to \`raw\`\.](#block-decode_utf8) · [Content\-Encoding is gzip](#predicate-gzip_encoding)
<a id="source-2"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 119–119 _(s105)_

<details>
<summary>View retained excerpt</summary>

```text
Instant.parse(updatedAt)
```
</details>


**Process blocks citing this excerpt:** [action: Read \`updated\_at\` as text into \`updatedAt\`, then call \`Instant\.parse\(updatedAt\)\` before constructing the forecast\.](#block-parse_updated_at)
<a id="source-3"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 94–94 _(s111)_

<details>
<summary>View retained excerpt</summary>

```text
response.statusCode() == 304 && cached != null
```
</details>


**Process blocks citing this excerpt:** [decision: On status 304 with a cached row, update only its expiry and return; otherwise check whether the response status is accepted\.](#block-check_not_modified) · [action: Call \`jdbc\.update\("UPDATE forecasts SET expires\_at=? WHERE place\_id=?", Timestamp\.from\(expires\), id\)\`, then return from \`refresh\`\. The source does not show the database outcome\.](#block-refresh_cached_expiry) · [Response is 304 and a cache row exists](#predicate-not_modified_with_cache)
<a id="source-4"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 92–92 _(s113)_

<details>
<summary>View retained excerpt</summary>

```text
seconds.coerceAtLeast(60L)
```
</details>


**Process blocks citing this excerpt:** [action: Use the Retry\-After value or \`"60"\`; if \`toLongOrNull\(\)\` returns null use \`60L\`, clamp to at least \`60L\`, then assign now plus that many seconds to \`nextAttempt\[id\]\`\.](#block-set_retry_delay) · [Response status is 429](#predicate-status_429)
<a id="source-5"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 104–112 _(s117)_

<details>
<summary>View retained excerpt</summary>

```text
for (point in document["properties"]["timeseries"].take(6)) {
            val temperature = point["data"]["instant"]["details"]["air_temperature"]
            require(temperature != null && temperature.isNumber)
            val next = point["data"]["next_1_hours"]
            val period = json.createObjectNode().put("time", point["time"].asText()).put("temperatureC", temperature.asDouble()).put("symbol", next?.get("summary")?.get("symbol_code")?.asText() ?: "unknown")
            val rain = next?.get("details")?.get("precipitation_amount")
            if (rain == null || !rain.isNumber) period.putNull("precipitationMm") else period.put("precipitationMm", rain.asDouble())
            periods.add(period)
        }
```
</details>


**Process blocks citing this excerpt:** [action: Append the completed period to \`periods\`\.](#block-append_period) · [action: After the required temperature check, read \`next\` from \`point\["data"\]\["next\_1\_hours"\]\` and create a period with \`time\` from \`point\["time"\]\.asText\(\)\`, \`temperatureC\` from \`temperature\.asDouble\(\)\`, and \`symbol\` from the optional summary symbol\-code chain or \`"unknown"\`\.](#block-construct_period) · [loop: Visit \`document\["properties"\]\["timeseries"\]\.take\(6\)\`, so the source builds periods from at most the first six points\.](#block-map_first_six_points) · [Temperature exists and is numeric](#predicate-temperature_valid) · [Summary](#summary)
<a id="source-6"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 88–88 _(s12)_

<details>
<summary>View retained excerpt</summary>

```text
builder.GET().build()
```
</details>


**Process blocks citing this excerpt:** [action: Call \`http\.send\(builder\.GET\(\)\.build\(\), HttpResponse\.BodyHandlers\.ofByteArray\(\)\)\`\. The request's runtime outcome is unknown\.](#block-send_request)
<a id="source-7"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 91–91 _(s120)_

<details>
<summary>View retained excerpt</summary>

```text
response.headers().firstValue("Retry-After").orElse("60").toLongOrNull() ?: 60L
```
</details>


**Process blocks citing this excerpt:** [action: Use the Retry\-After value or \`"60"\`; if \`toLongOrNull\(\)\` returns null use \`60L\`, clamp to at least \`60L\`, then assign now plus that many seconds to \`nextAttempt\[id\]\`\.](#block-set_retry_delay) · [Response status is 429](#predicate-status_429)
<a id="source-8"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 72–72 _(s122)_

<details>
<summary>View retained excerpt</summary>

```text
val cached = jdbc.queryForList("SELECT payload::text,expires_at,last_modified FROM forecasts WHERE place_id=?", id).firstOrNull()
```
</details>


**Process blocks citing this excerpt:** [action: Call the cache query for \`payload::text,expires\_at,last\_modified\` using \`id\`, then take \`firstOrNull\(\)\` of its returned list\. This selects the first nullable row; it does not filter the list for a fresh row or retry for another\.](#block-prep_cache_query) · [Cached entry is unexpired](#predicate-cache_fresh) · [Resolve the place key and cache candidate](#preparation-prep_inputs)
<a id="source-9"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 80–80 _(s123)_

<details>
<summary>View retained excerpt</summary>

```text
System.getenv("MET_USER_AGENT")?.takeIf { it.isNotBlank() }
```
</details>


**Process blocks citing this excerpt:** [action: Bind the nonblank environment value as \`agent\` for the request\.](#block-use_agent) · [Provider user agent is nonblank](#predicate-agent_ready)
<a id="source-10"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 118–118 _(s127)_

<details>
<summary>View retained excerpt</summary>

```text
json.writeValueAsString(forecast)
```
</details>


**Process blocks citing this excerpt:** [action: Serialize \`forecast\` with \`json\.writeValueAsString\` into \`payload\`\.](#block-serialize_forecast)
<a id="source-11"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 102–102 _(s128)_

<details>
<summary>View retained excerpt</summary>

```text
json.readTree(raw)
```
</details>


**Process blocks citing this excerpt:** [action: Parse \`raw\` with \`json\.readTree\` into \`document\`\.](#block-parse_document)
<a id="source-12"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 81–81 _(s13)_

<details>
<summary>View retained excerpt</summary>

```text
nextAttempt[id]?.isAfter(Instant.now())
```
</details>


**Process blocks citing this excerpt:** [throw: When the next\-attempt instant is after now, the source invokes \`error\("PROVIDER\_BACKOFF"\)\`\.](#block-backoff_error) · [decision: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\.](#block-check_backoff)
<a id="source-13"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 80–80 _(s132)_

<details>
<summary>View retained excerpt</summary>

```text
System.getenv("MET_USER_AGENT")?.takeIf { it.isNotBlank() } ?: error("MET_USER_AGENT_REQUIRED")
```
</details>


**Process blocks citing this excerpt:** [decision: Require a non\-null, nonblank provider user\-agent value\.](#block-check_agent) · [throw: The source invokes \`error\("MET\_USER\_AGENT\_REQUIRED"\)\`; the exception type and dispatch are not established\.](#block-missing_agent) · [action: Bind the nonblank environment value as \`agent\` for the request\.](#block-use_agent) · [Provider user agent is nonblank](#predicate-agent_ready)
<a id="source-14"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 92–92 _(s134)_

<details>
<summary>View retained excerpt</summary>

```text
Instant.now().plusSeconds(seconds.coerceAtLeast(60L))
```
</details>


**Process blocks citing this excerpt:** [action: Use the Retry\-After value or \`"60"\`; if \`toLongOrNull\(\)\` returns null use \`60L\`, clamp to at least \`60L\`, then assign now plus that many seconds to \`nextAttempt\[id\]\`\.](#block-set_retry_delay)
<a id="source-15"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 73–73 _(s135)_

<details>
<summary>View retained excerpt</summary>

```text
cached != null && (cached["expires_at"] as java.sql.Timestamp).toInstant().isAfter(Instant.now())
```
</details>


**Process blocks citing this excerpt:** [decision: Check whether the selected cache row has an expiry after the current time\.](#block-check_cache_fresh) · [decision: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\.](#block-check_cache_fresh_repeated_source) · [return: When \`cache\_fresh\` is true, return from \`refresh\` before source acquisition, transformation, or the later SQL calls\.](#block-return_fresh_cache) · [return: A fresh cache entry causes an early return before the later work in this method\.](#block-return_fresh_cache_repeated_source) · [Cached entry is unexpired](#predicate-cache_fresh)
<a id="source-16"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 85–85 _(s14)_

<details>
<summary>View retained excerpt</summary>

```text
HttpRequest.newBuilder(URI.create("https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=$lat&lon=$lon")).timeout(Duration.ofSeconds(20))
```
</details>


**Process blocks citing this excerpt:** [action: Build a GET request for the met\.no compact location forecast URL with those coordinates, a 20\-second timeout, \`User\-Agent: agent\`, and \`Accept\-Encoding: gzip\`\.](#block-build_request)
<a id="source-17"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 76–101 _(s147)_

<details>
<summary>View retained excerpt</summary>

```text
if (mode == "fixture") {
            Files.readString(Path.of("/app/fixtures/$id.json"))
        } else {
            require(mode == "live")
            val agent = System.getenv("MET_USER_AGENT")?.takeIf { it.isNotBlank() } ?: error("MET_USER_AGENT_REQUIRED")
            if (nextAttempt[id]?.isAfter(Instant.now()) == true) error("PROVIDER_BACKOFF")
            nextAttempt[id] = Instant.now().plusSeconds(60)
            val lat = BigDecimal.valueOf(place["latitude"].asDouble()).setScale(4, RoundingMode.DOWN).toPlainString()
            val lon = BigDecimal.valueOf(place["longitude"].asDouble()).setScale(4, RoundingMode.DOWN).toPlainString()
            val builder = HttpRequest.newBuilder(URI.create("https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=$lat&lon=$lon")).timeout(Duration.ofSeconds(20)).header("User-Agent", agent).header("Accept-Encoding", "gzip")
            val modified = cached?.get("last_modified") as String?
            if (modified != null) builder.header("If-Modified-Since", modified)
            val response = http.send(builder.GET().build(), HttpResponse.BodyHandlers.ofByteArray())
            expires = response.headers().firstValue("Expires").map { ZonedDateTime.parse(it, DateTimeFormatter.RFC_1123_DATE_TIME).toInstant() }.orElse(Instant.now().plusSeconds(3600))
            nextAttempt[id] = if (response.statusCode() == 429) {
                val seconds = response.headers().firstValue("Retry-After").orElse("60").toLongOrNull() ?: 60L
                Instant.now().plusSeconds(seconds.coerceAtLeast(60L))
            } else expires
            if (response.statusCode() == 304 && cached != null) {
                jdbc.update("UPDATE forecasts SET expires_at=? WHERE place_id=?", java.sql.Timestamp.from(expires), id)
                return
            }
            require(response.statusCode() == 200 || response.statusCode() == 203) { "PROVIDER_HTTP_" + response.statusCode() }
            lastModified = response.headers().firstValue("Last-Modified").orElse(null)
            if (response.headers().firstValue("Content-Encoding").orElse("").equals("gzip", ignoreCase = true)) GZIPInputStream(ByteArrayInputStream(response.body())).bufferedReader().use { it.readText() } else response.body().toString(Charsets.UTF_8)
        }
```
</details>


**Process blocks citing this excerpt:** [decision: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\.](#block-choose_fixture)
<a id="source-18"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 89–89 _(s150)_

<details>
<summary>View retained excerpt</summary>

```text
response.headers().firstValue("Expires").map { ZonedDateTime.parse(it, DateTimeFormatter.RFC_1123_DATE_TIME).toInstant() }.orElse(Instant.now().plusSeconds(3600))
```
</details>


**Process blocks citing this excerpt:** [action: Set \`expires\` from an \`Expires\` header parsed with \`RFC\_1123\_DATE\_TIME\` and converted to an instant; if the header is absent, use now plus 3600 seconds\. A parse failure is not handled in this source path\.](#block-derive_expiry)
<a id="source-19"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 122–122 _(s155)_

<details>
<summary>View retained excerpt</summary>

```text
event.set("place", place)
```
</details>


**Process blocks citing this excerpt:** [action: After the forecast update call, form \`eventId\` as \`$id:$updatedAt\`; create an event with that id, type \`forecast\.updated\`, version 1, and set its \`place\` and \`forecast\` values\.](#block-build_event)
<a id="source-20"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 110–110 _(s16)_

<details>
<summary>View retained excerpt</summary>

```text
rain == null || !rain.isNumber
```
</details>


**Process blocks citing this excerpt:** [decision: Use JSON null when precipitation is missing or nonnumeric\.](#block-check_rain) · [action: Set \`period\["precipitationMm"\]\` to JSON null\.](#block-put_null_rain) · [Rain is missing or nonnumeric](#predicate-rain_missing_or_nonnumeric)
<a id="source-21"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 89–89 _(s167)_

<details>
<summary>View retained excerpt</summary>

```text
expires = response.headers().firstValue("Expires").map { ZonedDateTime.parse(it, DateTimeFormatter.RFC_1123_DATE_TIME).toInstant() }.orElse(Instant.now().plusSeconds(3600))
```
</details>


**Process blocks citing this excerpt:** [action: Set \`expires\` from an \`Expires\` header parsed with \`RFC\_1123\_DATE\_TIME\` and converted to an instant; if the header is absent, use now plus 3600 seconds\. A parse failure is not handled in this source path\.](#block-derive_expiry)
<a id="source-22"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 94–94 _(s171)_

<details>
<summary>View retained excerpt</summary>

```text
response.statusCode() == 304 && cached != null
```
</details>


**Process blocks citing this excerpt:** [decision: On status 304 with a cached row, update only its expiry and return; otherwise check whether the response status is accepted\.](#block-check_not_modified) · [Response is 304 and a cache row exists](#predicate-not_modified_with_cache)
<a id="source-23"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 87–87 _(s174)_

<details>
<summary>View retained excerpt</summary>

```text
modified != null
```
</details>


**Process blocks citing this excerpt:** [action: Add \`If\-Modified\-Since\` with \`modified\`\.](#block-add_modified_header) · [decision: Add the conditional request header only when the cached value is non\-null\.](#block-conditional_header) · [action: Leave \`If\-Modified\-Since\` off the request builder\.](#block-omit_modified_header) · [Cached Last\-Modified value exists](#predicate-has_modified)
<a id="source-24"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 113–113 _(s176)_

<details>
<summary>View retained excerpt</summary>

```text
periods.size()
```
</details>


**Process blocks citing this excerpt:** [decision: Require at least one period before reading and validating \`updated\_at\` or making the forecast and outbox SQL calls\.](#block-check_periods_nonempty) · [At least one period was built](#predicate-periods_nonempty)
<a id="source-25"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 85–85 _(s178)_

<details>
<summary>View retained excerpt</summary>

```text
Duration.ofSeconds(20)
```
</details>


**Process blocks citing this excerpt:** [action: Build a GET request for the met\.no compact location forecast URL with those coordinates, a 20\-second timeout, \`User\-Agent: agent\`, and \`Accept\-Encoding: gzip\`\.](#block-build_request)
<a id="source-26"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 85–85 _(s18)_

<details>
<summary>View retained excerpt</summary>

```text
URI.create("https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=$lat&lon=$lon")
```
</details>


**Process blocks citing this excerpt:** [action: Build a GET request for the met\.no compact location forecast URL with those coordinates, a 20\-second timeout, \`User\-Agent: agent\`, and \`Accept\-Encoding: gzip\`\.](#block-build_request)
<a id="source-27"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 114–114 _(s187)_

<details>
<summary>View retained excerpt</summary>

```text
document["properties"]["meta"]["updated_at"].asText()
```
</details>


**Process blocks citing this excerpt:** [action: Read \`updated\_at\` as text into \`updatedAt\`, then call \`Instant\.parse\(updatedAt\)\` before constructing the forecast\.](#block-parse_updated_at)
<a id="source-28"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 103–103 _(s192)_

<details>
<summary>View retained excerpt</summary>

```text
val periods = json.createArrayNode()
```
</details>


**Process blocks citing this excerpt:** [action: Create an empty JSON array named \`periods\`\.](#block-create_periods) · [At least one period was built](#predicate-periods_nonempty)
<a id="source-29"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 88–88 _(s193)_

<details>
<summary>View retained excerpt</summary>

```text
HttpResponse.BodyHandlers.ofByteArray()
```
</details>


**Process blocks citing this excerpt:** [action: Call \`http\.send\(builder\.GET\(\)\.build\(\), HttpResponse\.BodyHandlers\.ofByteArray\(\)\)\`\. The request's runtime outcome is unknown\.](#block-send_request)
<a id="source-30"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 108–108 _(s194)_

<details>
<summary>View retained excerpt</summary>

```text
json.createObjectNode().put("time", point["time"].asText()).put("temperatureC", temperature.asDouble()).put("symbol", next?.get("summary")?.get("symbol_code")?.asText() ?: "unknown")
```
</details>


**Process blocks citing this excerpt:** [action: After the required temperature check, read \`next\` from \`point\["data"\]\["next\_1\_hours"\]\` and create a period with \`time\` from \`point\["time"\]\.asText\(\)\`, \`temperatureC\` from \`temperature\.asDouble\(\)\`, and \`symbol\` from the optional summary symbol\-code chain or \`"unknown"\`\.](#block-construct_period)
<a id="source-31"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 121–121 _(s200)_

<details>
<summary>View retained excerpt</summary>

```text
json.createObjectNode().put("id", eventId).put("type", "forecast.updated").put("version", 1)
```
</details>


**Process blocks citing this excerpt:** [action: After the forecast update call, form \`eventId\` as \`$id:$updatedAt\`; create an event with that id, type \`forecast\.updated\`, version 1, and set its \`place\` and \`forecast\` values\.](#block-build_event)
<a id="source-32"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 90–90 _(s201)_

<details>
<summary>View retained excerpt</summary>

```text
response.statusCode() == 429
```
</details>


**Process blocks citing this excerpt:** [decision: Set a minimum retry time for status 429; for other statuses, set the next attempt to \`expires\`\.](#block-check_429) · [action: Use the Retry\-After value or \`"60"\`; if \`toLongOrNull\(\)\` returns null use \`60L\`, clamp to at least \`60L\`, then assign now plus that many seconds to \`nextAttempt\[id\]\`\.](#block-set_retry_delay) · [Response status is 429](#predicate-status_429)
<a id="source-33"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 86–86 _(s203)_

<details>
<summary>View retained excerpt</summary>

```text
cached?.get("last_modified")
```
</details>


**Process blocks citing this excerpt:** [action: Read the cached row's \`last\_modified\` value as nullable \`modified\`\.](#block-read_modified) · [Cached Last\-Modified value exists](#predicate-has_modified)
<a id="source-34"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 94–94 _(s207)_

<details>
<summary>View retained excerpt</summary>

```text
response.statusCode() == 304 && cached != null
```
</details>


**Process blocks citing this excerpt:** [decision: On status 304 with a cached row, update only its expiry and return; otherwise check whether the response status is accepted\.](#block-check_not_modified)
<a id="source-35"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 99–99 _(s21)_

<details>
<summary>View retained excerpt</summary>

```text
response.headers().firstValue("Last-Modified").orElse(null)
```
</details>


**Process blocks citing this excerpt:** [action: Set \`lastModified\` from the \`Last\-Modified\` header, using null if absent\.](#block-read_last_modified)
<a id="source-36"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 120–120 _(s210)_

<details>
<summary>View retained excerpt</summary>

```text
val eventId = "$id:$updatedAt"
```
</details>


**Process blocks citing this excerpt:** [action: After the forecast update call, form \`eventId\` as \`$id:$updatedAt\`; create an event with that id, type \`forecast\.updated\`, version 1, and set its \`place\` and \`forecast\` values\.](#block-build_event)
<a id="source-37"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 100–100 _(s220)_

<details>
<summary>View retained excerpt</summary>

```text
GZIPInputStream(ByteArrayInputStream(response.body()))
```
</details>


**Process blocks citing this excerpt:** [Content\-Encoding is gzip](#predicate-gzip_encoding)
<a id="source-38"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 106–106 _(s222)_

<details>
<summary>View retained excerpt</summary>

```text
temperature != null && temperature.isNumber
```
</details>


**Process blocks citing this excerpt:** [decision: Require each visited point to have a non\-null numeric air temperature before constructing its period\.](#block-check_temperature) · [Temperature exists and is numeric](#predicate-temperature_valid)
<a id="source-39"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 116–116 _(s224)_

<details>
<summary>View retained excerpt</summary>

```text
json.createObjectNode().put("updatedAt", updatedAt).put("fetchedAt", Instant.now().toString()).put("mode", mode)
```
</details>


**Process blocks citing this excerpt:** [action: Construct \`forecast\` with \`updatedAt\`, \`Instant\.now\(\)\.toString\(\)\` as \`fetchedAt\`, and \`mode\`; attach \`periods\` under \`periods\`\.](#block-build_forecast)
<a id="source-40"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 82–82 _(s225)_

<details>
<summary>View retained excerpt</summary>

```text
nextAttempt[id] = Instant.now().plusSeconds(60)
```
</details>


**Process blocks citing this excerpt:** [decision: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\.](#block-check_backoff) · [action: Assign \`nextAttempt\[id\] = Instant\.now\(\)\.plusSeconds\(60\)\` before the HTTP send call\.](#block-seed_next_attempt)
<a id="source-41"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 100–100 _(s233)_

<details>
<summary>View retained excerpt</summary>

```text
GZIPInputStream(ByteArrayInputStream(response.body())).bufferedReader().use { it.readText() }
```
</details>


**Process blocks citing this excerpt:** [Content\-Encoding is gzip](#predicate-gzip_encoding)
<a id="source-42"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 105–105 _(s235)_

<details>
<summary>View retained excerpt</summary>

```text
val temperature = point["data"]["instant"]["details"]["air_temperature"]
```
</details>


**Process blocks citing this excerpt:** [action: After the required temperature check, read \`next\` from \`point\["data"\]\["next\_1\_hours"\]\` and create a period with \`time\` from \`point\["time"\]\.asText\(\)\`, \`temperatureC\` from \`temperature\.asDouble\(\)\`, and \`symbol\` from the optional summary symbol\-code chain or \`"unknown"\`\.](#block-construct_period)
<a id="source-43"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 86–86 _(s239)_

<details>
<summary>View retained excerpt</summary>

```text
val modified = cached?.get("last_modified") as String?
```
</details>


**Process blocks citing this excerpt:** [action: Read the cached row's \`last\_modified\` value as nullable \`modified\`\.](#block-read_modified)
<a id="source-44"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 121–121 _(s242)_

<details>
<summary>View retained excerpt</summary>

```text
val event = json.createObjectNode().put("id", eventId).put("type", "forecast.updated").put("version", 1)
```
</details>


**Process blocks citing this excerpt:** [action: After the forecast update call, form \`eventId\` as \`$id:$updatedAt\`; create an event with that id, type \`forecast\.updated\`, version 1, and set its \`place\` and \`forecast\` values\.](#block-build_event)
<a id="source-45"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 102–102 _(s245)_

<details>
<summary>View retained excerpt</summary>

```text
val document = json.readTree(raw)
```
</details>


**Process blocks citing this excerpt:** [action: Parse \`raw\` with \`json\.readTree\` into \`document\`\.](#block-parse_document)
<a id="source-46"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 117–117 _(s248)_

<details>
<summary>View retained excerpt</summary>

```text
forecast.set("periods", periods)
```
</details>


**Process blocks citing this excerpt:** [action: Construct \`forecast\` with \`updatedAt\`, \`Instant\.now\(\)\.toString\(\)\` as \`fetchedAt\`, and \`mode\`; attach \`periods\` under \`periods\`\.](#block-build_forecast)
<a id="source-47"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 113–113 _(s25)_

<details>
<summary>View retained excerpt</summary>

```text
require(periods.size() > 0)
```
</details>


**Process blocks citing this excerpt:** [decision: Require at least one period before reading and validating \`updated\_at\` or making the forecast and outbox SQL calls\.](#block-check_periods_nonempty) · [throw: The source's \`require\(periods\.size\(\) &gt; 0\)\` fails; the exception type is not established here\.](#block-reject_empty_periods) · [At least one period was built](#predicate-periods_nonempty)
<a id="source-48"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 110–110 _(s259)_

<details>
<summary>View retained excerpt</summary>

```text
period.putNull("precipitationMm")
```
</details>


**Process blocks citing this excerpt:** [action: Set \`period\["precipitationMm"\]\` to JSON null\.](#block-put_null_rain) · [Rain is missing or nonnumeric](#predicate-rain_missing_or_nonnumeric)
<a id="source-49"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 90–93 _(s26)_

<details>
<summary>View retained excerpt</summary>

```text
if (response.statusCode() == 429) {
                val seconds = response.headers().firstValue("Retry-After").orElse("60").toLongOrNull() ?: 60L
                Instant.now().plusSeconds(seconds.coerceAtLeast(60L))
            } else expires
```
</details>


**Process blocks citing this excerpt:** [decision: Set a minimum retry time for status 429; for other statuses, set the next attempt to \`expires\`\.](#block-check_429) · [action: Assign \`expires\` to \`nextAttempt\[id\]\`\.](#block-set_expiry_retry) · [action: Use the Retry\-After value or \`"60"\`; if \`toLongOrNull\(\)\` returns null use \`60L\`, clamp to at least \`60L\`, then assign now plus that many seconds to \`nextAttempt\[id\]\`\.](#block-set_retry_delay) · [Response status is 429](#predicate-status_429)
<a id="source-50"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 115–115 _(s261)_

<details>
<summary>View retained excerpt</summary>

```text
Instant.parse(updatedAt)
```
</details>


**Process blocks citing this excerpt:** [action: Read \`updated\_at\` as text into \`updatedAt\`, then call \`Instant\.parse\(updatedAt\)\` before constructing the forecast\.](#block-parse_updated_at)
<a id="source-51"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 80–80 _(s265)_

<details>
<summary>View retained excerpt</summary>

```text
error("MET_USER_AGENT_REQUIRED")
```
</details>


**Process blocks citing this excerpt:** [throw: The source invokes \`error\("MET\_USER\_AGENT\_REQUIRED"\)\`; the exception type and dispatch are not established\.](#block-missing_agent)
<a id="source-52"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 95–95 _(s271)_

<details>
<summary>View retained excerpt</summary>

```text
jdbc.update("UPDATE forecasts SET expires_at=? WHERE place_id=?", java.sql.Timestamp.from(expires), id)
```
</details>


**Process blocks citing this excerpt:** [action: Call \`jdbc\.update\("UPDATE forecasts SET expires\_at=? WHERE place\_id=?", Timestamp\.from\(expires\), id\)\`, then return from \`refresh\`\. The source does not show the database outcome\.](#block-refresh_cached_expiry) · [Response is 304 and a cache row exists](#predicate-not_modified_with_cache)
<a id="source-53"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 110–110 _(s273)_

<details>
<summary>View retained excerpt</summary>

```text
period.put("precipitationMm", rain.asDouble())
```
</details>


**Process blocks citing this excerpt:** [action: Set \`period\["precipitationMm"\]\` from \`rain\.asDouble\(\)\`\.](#block-put_numeric_rain) · [Rain is missing or nonnumeric](#predicate-rain_missing_or_nonnumeric)
<a id="source-54"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 89–89 _(s276)_

<details>
<summary>View retained excerpt</summary>

```text
Instant.now().plusSeconds(3600)
```
</details>


**Process blocks citing this excerpt:** [action: Set \`expires\` from an \`Expires\` header parsed with \`RFC\_1123\_DATE\_TIME\` and converted to an instant; if the header is absent, use now plus 3600 seconds\. A parse failure is not handled in this source path\.](#block-derive_expiry)
<a id="source-55"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 111–111 _(s277)_

<details>
<summary>View retained excerpt</summary>

```text
periods.add(period)
```
</details>


**Process blocks citing this excerpt:** [action: Append the completed period to \`periods\`\.](#block-append_period)
<a id="source-56"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 73–73 _(s28)_

<details>
<summary>View retained excerpt</summary>

```text
if (cached != null && (cached["expires_at"] as java.sql.Timestamp).toInstant().isAfter(Instant.now())) return
```
</details>


**Process blocks citing this excerpt:** [decision: Check whether the selected cache row has an expiry after the current time\.](#block-check_cache_fresh) · [decision: Return on a fresh cache entry; otherwise continue in source order through acquisition, period construction, and the two SQL calls\.](#block-check_cache_fresh_repeated_source) · [return: When \`cache\_fresh\` is true, return from \`refresh\` before source acquisition, transformation, or the later SQL calls\.](#block-return_fresh_cache) · [return: A fresh cache entry causes an early return before the later work in this method\.](#block-return_fresh_cache_repeated_source) · [Cached entry is unexpired](#predicate-cache_fresh)
<a id="source-57"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 84–84 _(s281)_

<details>
<summary>View retained excerpt</summary>

```text
place["longitude"].asDouble()
```
</details>


**Process blocks citing this excerpt:** [action: Read latitude and longitude from \`place\`, convert each with \`asDouble\(\)\`, then use \`BigDecimal\.valueOf\(\.\.\.\)\.setScale\(4, RoundingMode\.DOWN\)\.toPlainString\(\)\` for the request coordinates\.](#block-format_coordinates)
<a id="source-58"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 84–84 _(s282)_

<details>
<summary>View retained excerpt</summary>

```text
BigDecimal.valueOf(place["longitude"].asDouble()).setScale(4, RoundingMode.DOWN).toPlainString()
```
</details>


**Process blocks citing this excerpt:** [action: Read latitude and longitude from \`place\`, convert each with \`asDouble\(\)\`, then use \`BigDecimal\.valueOf\(\.\.\.\)\.setScale\(4, RoundingMode\.DOWN\)\.toPlainString\(\)\` for the request coordinates\.](#block-format_coordinates)
<a id="source-59"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 124–124 _(s285)_

<details>
<summary>View retained excerpt</summary>

```text
jdbc.update("INSERT INTO forecast_outbox(id,payload) VALUES(?,?::jsonb) ON CONFLICT DO NOTHING", eventId, json.writeValueAsString(event))
```
</details>


**Process blocks citing this excerpt:** [action: Serialize \`event\` and call the \`forecast\_outbox\` INSERT statement with \`ON CONFLICT DO NOTHING\`\. This source does not establish delivery, publication, or database completion\.](#block-insert_outbox) · [Summary](#summary)
<a id="source-60"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 103–103 _(s286)_

<details>
<summary>View retained excerpt</summary>

```text
json.createArrayNode()
```
</details>


**Process blocks citing this excerpt:** [action: Create an empty JSON array named \`periods\`\.](#block-create_periods)
<a id="source-61"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 98–98 _(s288)_

<details>
<summary>View retained excerpt</summary>

```text
require(response.statusCode() == 200 || response.statusCode() == 203) { "PROVIDER_HTTP_" + response.statusCode() }
```
</details>


**Process blocks citing this excerpt:** [decision: Only statuses 200 and 203 proceed to capture Last\-Modified and read the response body\.](#block-check_http_status) · [throw: The source's \`require\` failure message is \`PROVIDER\_HTTP\_\` plus the response status code; exception type and runtime dispatch are not established\.](#block-reject_http_status) · [Response status is 200 or 203](#predicate-accepted_status)
<a id="source-62"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 84–84 _(s289)_

<details>
<summary>View retained excerpt</summary>

```text
val lon = BigDecimal.valueOf(place["longitude"].asDouble()).setScale(4, RoundingMode.DOWN).toPlainString()
```
</details>


**Process blocks citing this excerpt:** [action: Read latitude and longitude from \`place\`, convert each with \`asDouble\(\)\`, then use \`BigDecimal\.valueOf\(\.\.\.\)\.setScale\(4, RoundingMode\.DOWN\)\.toPlainString\(\)\` for the request coordinates\.](#block-format_coordinates)
<a id="source-63"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 121–121 _(s296)_

<details>
<summary>View retained excerpt</summary>

```text
json.createObjectNode().put("id", eventId).put("type", "forecast.updated")
```
</details>


**Process blocks citing this excerpt:** [action: After the forecast update call, form \`eventId\` as \`$id:$updatedAt\`; create an event with that id, type \`forecast\.updated\`, version 1, and set its \`place\` and \`forecast\` values\.](#block-build_event)
<a id="source-64"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 110–110 _(s30)_

<details>
<summary>View retained excerpt</summary>

```text
rain == null || !rain.isNumber
```
</details>


**Process blocks citing this excerpt:** [decision: Use JSON null when precipitation is missing or nonnumeric\.](#block-check_rain) · [Rain is missing or nonnumeric](#predicate-rain_missing_or_nonnumeric)
<a id="source-65"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 88–88 _(s306)_

<details>
<summary>View retained excerpt</summary>

```text
http.send(builder.GET().build(), HttpResponse.BodyHandlers.ofByteArray())
```
</details>


**Process blocks citing this excerpt:** [action: Call \`http\.send\(builder\.GET\(\)\.build\(\), HttpResponse\.BodyHandlers\.ofByteArray\(\)\)\`\. The request's runtime outcome is unknown\.](#block-send_request)
<a id="source-66"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 108–108 _(s307)_

<details>
<summary>View retained excerpt</summary>

```text
next?.get("summary")?.get("symbol_code")?.asText() ?: "unknown"
```
</details>


**Process blocks citing this excerpt:** [action: After the required temperature check, read \`next\` from \`point\["data"\]\["next\_1\_hours"\]\` and create a period with \`time\` from \`point\["time"\]\.asText\(\)\`, \`temperatureC\` from \`temperature\.asDouble\(\)\`, and \`symbol\` from the optional summary symbol\-code chain or \`"unknown"\`\.](#block-construct_period)
<a id="source-67"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 100–100 _(s314)_

<details>
<summary>View retained excerpt</summary>

```text
response.body().toString(Charsets.UTF_8)
```
</details>


**Process blocks citing this excerpt:** [action: Convert the response body bytes to a string with UTF\-8 and assign it to \`raw\`\.](#block-decode_utf8)
<a id="source-68"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 114–114 _(s317)_

<details>
<summary>View retained excerpt</summary>

```text
val updatedAt = document["properties"]["meta"]["updated_at"].asText()
```
</details>


**Process blocks citing this excerpt:** [action: Read \`updated\_at\` as text into \`updatedAt\`, then call \`Instant\.parse\(updatedAt\)\` before constructing the forecast\.](#block-parse_updated_at)
<a id="source-69"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 70–125 _(s320)_

<details>
<summary>View retained excerpt</summary>

```text
fun refresh(place: JsonNode) {
        val id = place["id"].asText()
        val cached = jdbc.queryForList("SELECT payload::text,expires_at,last_modified FROM forecasts WHERE place_id=?", id).firstOrNull()
        if (cached != null && (cached["expires_at"] as java.sql.Timestamp).toInstant().isAfter(Instant.now())) return
        var expires = Instant.now().plusSeconds(3600)
        var lastModified: String? = null
        val raw = if (mode == "fixture") {
            Files.readString(Path.of("/app/fixtures/$id.json"))
        } else {
            require(mode == "live")
            val agent = System.getenv("MET_USER_AGENT")?.takeIf { it.isNotBlank() } ?: error("MET_USER_AGENT_REQUIRED")
            if (nextAttempt[id]?.isAfter(Instant.now()) == true) error("PROVIDER_BACKOFF")
            nextAttempt[id] = Instant.now().plusSeconds(60)
            val lat = BigDecimal.valueOf(place["latitude"].asDouble()).setScale(4, RoundingMode.DOWN).toPlainString()
            val lon = BigDecimal.valueOf(place["longitude"].asDouble()).setScale(4, RoundingMode.DOWN).toPlainString()
            val builder = HttpRequest.newBuilder(URI.create("https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=$lat&lon=$lon")).timeout(Duration.ofSeconds(20)).header("User-Agent", agent).header("Accept-Encoding", "gzip")
            val modified = cached?.get("last_modified") as String?
            if (modified != null) builder.header("If-Modified-Since", modified)
            val response = http.send(builder.GET().build(), HttpResponse.BodyHandlers.ofByteArray())
            expires = response.headers().firstValue("Expires").map { ZonedDateTime.parse(it, DateTimeFormatter.RFC_1123_DATE_TIME).toInstant() }.orElse(Instant.now().plusSeconds(3600))
            nextAttempt[id] = if (response.statusCode() == 429) {
                val seconds = response.headers().firstValue("Retry-After").orElse("60").toLongOrNull() ?: 60L
                Instant.now().plusSeconds(seconds.coerceAtLeast(60L))
            } else expires
            if (response.statusCode() == 304 && cached != null) {
                jdbc.update("UPDATE forecasts SET expires_at=? WHERE place_id=?", java.sql.Timestamp.from(expires), id)
                return
            }
            require(response.statusCode() == 200 || response.statusCode() == 203) { "PROVIDER_HTTP_" + response.statusCode() }
            lastModified = response.headers().firstValue("Last-Modified").orElse(null)
            if (response.headers().firstValue("Content-Encoding").orElse("").equals("gzip", ignoreCase = true)) GZIPInputStream(ByteArrayInputStream(response.body())).bufferedReader().use { it.readText() } else response.body().toString(Charsets.UTF_8)
        }
        val document = json.readTree(raw)
        val periods = json.createArrayNode()
        for (point in document["properties"]["timeseries"].take(6)) {
            val temperature = point["data"]["instant"]["details"]["air_temperature"]
            require(temperature != null && temperature.isNumber)
            val next = point["data"]["next_1_hours"]
            val period = json.createObjectNode().put("time", point["time"].asText()).put("temperatureC", temperature.asDouble()).put("symbol", next?.get("summary")?.get("symbol_code")?.asText() ?: "unknown")
            val rain = next?.get("details")?.get("precipitation_amount")
            if (rain == null || !rain.isNumber) period.putNull("precipitationMm") else period.put("precipitationMm", rain.asDouble())
            periods.add(period)
        }
        require(periods.size() > 0)
        val updatedAt = document["properties"]["meta"]["updated_at"].asText()
        Instant.parse(updatedAt)
        val forecast = json.createObjectNode().put("updatedAt", updatedAt).put("fetchedAt", Instant.now().toString()).put("mode", mode)
        forecast.set("periods", periods)
        val payload = json.writeValueAsString(forecast)
        jdbc.update("INSERT INTO forecasts(place_id,updated_at,payload,expires_at,last_modified) VALUES(?,?,?::jsonb,?,?) ON CONFLICT(place_id) DO UPDATE SET updated_at=EXCLUDED.updated_at,payload=EXCLUDED.payload,expires_at=EXCLUDED.expires_at,last_modified=EXCLUDED.last_modified WHERE EXCLUDED.updated_at>=forecasts.updated_at", id, java.sql.Timestamp.from(Instant.parse(updatedAt)), payload, java.sql.Timestamp.from(expires), lastModified)
        val eventId = "$id:$updatedAt"
        val event = json.createObjectNode().put("id", eventId).put("type", "forecast.updated").put("version", 1)
        event.set("place", place)
        event.set("forecast", forecast)
        jdbc.update("INSERT INTO forecast_outbox(id,payload) VALUES(?,?::jsonb) ON CONFLICT DO NOTHING", eventId, json.writeValueAsString(event))
    }
```
</details>


**Process blocks citing this excerpt:** [action: Call the cache query for \`payload::text,expires\_at,last\_modified\` using \`id\`, then take \`firstOrNull\(\)\` of its returned list\. This selects the first nullable row; it does not filter the list for a fresh row or retry for another\.](#block-prep_cache_query) · [action: Read \`place\["id"\]\.asText\(\)\` into \`id\`\.](#block-prep_place_id) · [Resolve the place key and cache candidate](#preparation-prep_inputs) · [Summary](#summary)
<a id="source-70"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 118–118 _(s321)_

<details>
<summary>View retained excerpt</summary>

```text
val payload = json.writeValueAsString(forecast)
```
</details>


**Process blocks citing this excerpt:** [action: Serialize \`forecast\` with \`json\.writeValueAsString\` into \`payload\`\.](#block-serialize_forecast)
<a id="source-71"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 94–97 _(s326)_

<details>
<summary>View retained excerpt</summary>

```text
if (response.statusCode() == 304 && cached != null) {
                jdbc.update("UPDATE forecasts SET expires_at=? WHERE place_id=?", java.sql.Timestamp.from(expires), id)
                return
            }
```
</details>


**Process blocks citing this excerpt:** [action: Call \`jdbc\.update\("UPDATE forecasts SET expires\_at=? WHERE place\_id=?", Timestamp\.from\(expires\), id\)\`, then return from \`refresh\`\. The source does not show the database outcome\.](#block-refresh_cached_expiry) · [Response is 304 and a cache row exists](#predicate-not_modified_with_cache)
<a id="source-72"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 74–74 _(s327)_

<details>
<summary>View retained excerpt</summary>

```text
var expires = Instant.now().plusSeconds(3600)
```
</details>


**Process blocks citing this excerpt:** [action: After the cache miss or expiry, initialize \`expires\` to now plus 3600 seconds and \`lastModified\` to null\.](#block-initialize_defaults)
<a id="source-73"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 108–108 _(s33)_

<details>
<summary>View retained excerpt</summary>

```text
json.createObjectNode().put("time", point["time"].asText()).put("temperatureC", temperature.asDouble())
```
</details>


**Process blocks citing this excerpt:** [action: After the required temperature check, read \`next\` from \`point\["data"\]\["next\_1\_hours"\]\` and create a period with \`time\` from \`point\["time"\]\.asText\(\)\`, \`temperatureC\` from \`temperature\.asDouble\(\)\`, and \`symbol\` from the optional summary symbol\-code chain or \`"unknown"\`\.](#block-construct_period)
<a id="source-74"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 87–87 _(s335)_

<details>
<summary>View retained excerpt</summary>

```text
builder.header("If-Modified-Since", modified)
```
</details>


**Process blocks citing this excerpt:** [action: Add \`If\-Modified\-Since\` with \`modified\`\.](#block-add_modified_header) · [Cached Last\-Modified value exists](#predicate-has_modified)
<a id="source-75"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 85–85 _(s340)_

<details>
<summary>View retained excerpt</summary>

```text
HttpRequest.newBuilder(URI.create("https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=$lat&lon=$lon")).timeout(Duration.ofSeconds(20)).header("User-Agent", agent).header("Accept-Encoding", "gzip")
```
</details>


**Process blocks citing this excerpt:** [action: Build a GET request for the met\.no compact location forecast URL with those coordinates, a 20\-second timeout, \`User\-Agent: agent\`, and \`Accept\-Encoding: gzip\`\.](#block-build_request)
<a id="source-76"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 108–108 _(s350)_

<details>
<summary>View retained excerpt</summary>

```text
next?.get("summary")?.get("symbol_code")?.asText() ?: "unknown"
```
</details>


**Process blocks citing this excerpt:** [action: After the required temperature check, read \`next\` from \`point\["data"\]\["next\_1\_hours"\]\` and create a period with \`time\` from \`point\["time"\]\.asText\(\)\`, \`temperatureC\` from \`temperature\.asDouble\(\)\`, and \`symbol\` from the optional summary symbol\-code chain or \`"unknown"\`\.](#block-construct_period)
<a id="source-77"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 86–86 _(s351)_

<details>
<summary>View retained excerpt</summary>

```text
cached?.get("last_modified")
```
</details>


**Process blocks citing this excerpt:** [action: Read the cached row's \`last\_modified\` value as nullable \`modified\`\.](#block-read_modified)
<a id="source-78"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 100–100 _(s352)_

<details>
<summary>View retained excerpt</summary>

```text
response.body().toString(Charsets.UTF_8)
```
</details>


**Process blocks citing this excerpt:** [action: Convert the response body bytes to a string with UTF\-8 and assign it to \`raw\`\.](#block-decode_utf8) · [Content\-Encoding is gzip](#predicate-gzip_encoding)
<a id="source-79"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 100–100 _(s353)_

<details>
<summary>View retained excerpt</summary>

```text
response.headers().firstValue("Content-Encoding").orElse("").equals("gzip", ignoreCase = true)
```
</details>


**Process blocks citing this excerpt:** [decision: Read \`raw\` from the response body using the gzip path when the content\-encoding value matches gzip, or UTF\-8 conversion otherwise\.](#block-check_gzip) · [Content\-Encoding is gzip](#predicate-gzip_encoding)
<a id="source-80"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 83–83 _(s354)_

<details>
<summary>View retained excerpt</summary>

```text
val lat = BigDecimal.valueOf(place["latitude"].asDouble()).setScale(4, RoundingMode.DOWN).toPlainString()
```
</details>


**Process blocks citing this excerpt:** [action: Read latitude and longitude from \`place\`, convert each with \`asDouble\(\)\`, then use \`BigDecimal\.valueOf\(\.\.\.\)\.setScale\(4, RoundingMode\.DOWN\)\.toPlainString\(\)\` for the request coordinates\.](#block-format_coordinates)
<a id="source-81"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 71–71 _(s355)_

<details>
<summary>View retained excerpt</summary>

```text
val id = place["id"].asText()
```
</details>


**Process blocks citing this excerpt:** [action: Read \`place\["id"\]\.asText\(\)\` into \`id\`\.](#block-prep_place_id) · [Resolve the place key and cache candidate](#preparation-prep_inputs)
<a id="source-82"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 72–72 _(s357)_

<details>
<summary>View retained excerpt</summary>

```text
jdbc.queryForList("SELECT payload::text,expires_at,last_modified FROM forecasts WHERE place_id=?", id).firstOrNull()
```
</details>


**Process blocks citing this excerpt:** [action: Call the cache query for \`payload::text,expires\_at,last\_modified\` using \`id\`, then take \`firstOrNull\(\)\` of its returned list\. This selects the first nullable row; it does not filter the list for a fresh row or retry for another\.](#block-prep_cache_query)
<a id="source-83"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 88–88 _(s359)_

<details>
<summary>View retained excerpt</summary>

```text
val response = http.send(builder.GET().build(), HttpResponse.BodyHandlers.ofByteArray())
```
</details>


**Process blocks citing this excerpt:** [action: Call \`http\.send\(builder\.GET\(\)\.build\(\), HttpResponse\.BodyHandlers\.ofByteArray\(\)\)\`\. The request's runtime outcome is unknown\.](#block-send_request)
<a id="source-84"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 85–85 _(s361)_

<details>
<summary>View retained excerpt</summary>

```text
val builder = HttpRequest.newBuilder(URI.create("https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=$lat&lon=$lon")).timeout(Duration.ofSeconds(20)).header("User-Agent", agent).header("Accept-Encoding", "gzip")
```
</details>


**Process blocks citing this excerpt:** [action: Build a GET request for the met\.no compact location forecast URL with those coordinates, a 20\-second timeout, \`User\-Agent: agent\`, and \`Accept\-Encoding: gzip\`\.](#block-build_request)
<a id="source-85"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 106–106 _(s362)_

<details>
<summary>View retained excerpt</summary>

```text
require(temperature != null && temperature.isNumber)
```
</details>


**Process blocks citing this excerpt:** [decision: Require each visited point to have a non\-null numeric air temperature before constructing its period\.](#block-check_temperature) · [throw: The source's \`require\(temperature \!= null &amp;&amp; temperature\.isNumber\)\` fails; the exception type is not established here\.](#block-reject_temperature) · [Temperature exists and is numeric](#predicate-temperature_valid)
<a id="source-86"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 119–119 _(s364)_

<details>
<summary>View retained excerpt</summary>

```text
jdbc.update("INSERT INTO forecasts(place_id,updated_at,payload,expires_at,last_modified) VALUES(?,?,?::jsonb,?,?) ON CONFLICT(place_id) DO UPDATE SET updated_at=EXCLUDED.updated_at,payload=EXCLUDED.payload,expires_at=EXCLUDED.expires_at,last_modified=EXCLUDED.last_modified WHERE EXCLUDED.updated_at>=forecasts.updated_at", id, java.sql.Timestamp.from(Instant.parse(updatedAt)), payload, java.sql.Timestamp.from(expires), lastModified)
```
</details>


**Process blocks citing this excerpt:** [action: Call the \`forecasts\` INSERT/ON CONFLICT statement with the place id, parsed update time, payload, expiry, and last\-modified value\. On a \`place\_id\` conflict, its UPDATE clause is guarded by \`EXCLUDED\.updated\_at&gt;=forecasts\.updated\_at\`\. The source records the call, not the database result or transaction completion\.](#block-upsert_forecast) · [Summary](#summary)
<a id="source-87"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 104–112 _(s365)_

<details>
<summary>View retained excerpt</summary>

```text
for (point in document["properties"]["timeseries"].take(6)) {
            val temperature = point["data"]["instant"]["details"]["air_temperature"]
            require(temperature != null && temperature.isNumber)
            val next = point["data"]["next_1_hours"]
            val period = json.createObjectNode().put("time", point["time"].asText()).put("temperatureC", temperature.asDouble()).put("symbol", next?.get("summary")?.get("symbol_code")?.asText() ?: "unknown")
            val rain = next?.get("details")?.get("precipitation_amount")
            if (rain == null || !rain.isNumber) period.putNull("precipitationMm") else period.put("precipitationMm", rain.asDouble())
            periods.add(period)
        }
```
</details>


**Process blocks citing this excerpt:** [action: Append the completed period to \`periods\`\.](#block-append_period) · [loop: Visit \`document\["properties"\]\["timeseries"\]\.take\(6\)\`, so the source builds periods from at most the first six points\.](#block-map_first_six_points)
<a id="source-88"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 124–124 _(s368)_

<details>
<summary>View retained excerpt</summary>

```text
json.writeValueAsString(event)
```
</details>


**Process blocks citing this excerpt:** [action: Serialize \`event\` and call the \`forecast\_outbox\` INSERT statement with \`ON CONFLICT DO NOTHING\`\. This source does not establish delivery, publication, or database completion\.](#block-insert_outbox)
<a id="source-89"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 77–77 _(s371)_

<details>
<summary>View retained excerpt</summary>

```text
Path.of("/app/fixtures/$id.json")
```
</details>


**Process blocks citing this excerpt:** [action: Read \`/app/fixtures/$id\.json\` into \`raw\`\. The file contents are not present in this packet\.](#block-read_fixture)
<a id="source-90"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 75–75 _(s376)_

<details>
<summary>View retained excerpt</summary>

```text
var lastModified: String? = null
```
</details>


**Process blocks citing this excerpt:** [action: After the cache miss or expiry, initialize \`expires\` to now plus 3600 seconds and \`lastModified\` to null\.](#block-initialize_defaults)
<a id="source-91"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 100–100 _(s380)_

<details>
<summary>View retained excerpt</summary>

```text
response.headers().firstValue("Content-Encoding").orElse("").equals("gzip", ignoreCase = true)
```
</details>


**Process blocks citing this excerpt:** [decision: Read \`raw\` from the response body using the gzip path when the content\-encoding value matches gzip, or UTF\-8 conversion otherwise\.](#block-check_gzip) · [Content\-Encoding is gzip](#predicate-gzip_encoding)
<a id="source-92"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 98–98 _(s385)_

<details>
<summary>View retained excerpt</summary>

```text
response.statusCode() == 200 || response.statusCode() == 203
```
</details>


**Process blocks citing this excerpt:** [decision: Only statuses 200 and 203 proceed to capture Last\-Modified and read the response body\.](#block-check_http_status) · [Response status is 200 or 203](#predicate-accepted_status)
<a id="source-93"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 89–89 _(s398)_

<details>
<summary>View retained excerpt</summary>

```text
response.headers().firstValue("Expires")
```
</details>


**Process blocks citing this excerpt:** [action: Set \`expires\` from an \`Expires\` header parsed with \`RFC\_1123\_DATE\_TIME\` and converted to an instant; if the header is absent, use now plus 3600 seconds\. A parse failure is not handled in this source path\.](#block-derive_expiry)
<a id="source-94"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 99–99 _(s4)_

<details>
<summary>View retained excerpt</summary>

```text
response.headers().firstValue("Last-Modified")
```
</details>


**Process blocks citing this excerpt:** [action: Set \`lastModified\` from the \`Last\-Modified\` header, using null if absent\.](#block-read_last_modified)
<a id="source-95"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 108–108 _(s43)_

<details>
<summary>View retained excerpt</summary>

```text
val period = json.createObjectNode().put("time", point["time"].asText()).put("temperatureC", temperature.asDouble()).put("symbol", next?.get("summary")?.get("symbol_code")?.asText() ?: "unknown")
```
</details>


**Process blocks citing this excerpt:** [action: After the required temperature check, read \`next\` from \`point\["data"\]\["next\_1\_hours"\]\` and create a period with \`time\` from \`point\["time"\]\.asText\(\)\`, \`temperatureC\` from \`temperature\.asDouble\(\)\`, and \`symbol\` from the optional summary symbol\-code chain or \`"unknown"\`\.](#block-construct_period)
<a id="source-96"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 104–104 _(s47)_

<details>
<summary>View retained excerpt</summary>

```text
document["properties"]["timeseries"].take(6)
```
</details>


**Process blocks citing this excerpt:** [loop: Visit \`document\["properties"\]\["timeseries"\]\.take\(6\)\`, so the source builds periods from at most the first six points\.](#block-map_first_six_points)
<a id="source-97"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 110–110 _(s48)_

<details>
<summary>View retained excerpt</summary>

```text
period.put("precipitationMm", rain.asDouble())
```
</details>


**Process blocks citing this excerpt:** [action: Set \`period\["precipitationMm"\]\` from \`rain\.asDouble\(\)\`\.](#block-put_numeric_rain)
<a id="source-98"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 106–106 _(s5)_

<details>
<summary>View retained excerpt</summary>

```text
temperature != null && temperature.isNumber
```
</details>


**Process blocks citing this excerpt:** [decision: Require each visited point to have a non\-null numeric air temperature before constructing its period\.](#block-check_temperature) · [throw: The source's \`require\(temperature \!= null &amp;&amp; temperature\.isNumber\)\` fails; the exception type is not established here\.](#block-reject_temperature) · [Temperature exists and is numeric](#predicate-temperature_valid)
<a id="source-99"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 83–83 _(s50)_

<details>
<summary>View retained excerpt</summary>

```text
BigDecimal.valueOf(place["latitude"].asDouble()).setScale(4, RoundingMode.DOWN).toPlainString()
```
</details>


**Process blocks citing this excerpt:** [action: Read latitude and longitude from \`place\`, convert each with \`asDouble\(\)\`, then use \`BigDecimal\.valueOf\(\.\.\.\)\.setScale\(4, RoundingMode\.DOWN\)\.toPlainString\(\)\` for the request coordinates\.](#block-format_coordinates)
<a id="source-100"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 83–83 _(s53)_

<details>
<summary>View retained excerpt</summary>

```text
BigDecimal.valueOf(place["latitude"].asDouble()).setScale(4, RoundingMode.DOWN)
```
</details>


**Process blocks citing this excerpt:** [action: Read latitude and longitude from \`place\`, convert each with \`asDouble\(\)\`, then use \`BigDecimal\.valueOf\(\.\.\.\)\.setScale\(4, RoundingMode\.DOWN\)\.toPlainString\(\)\` for the request coordinates\.](#block-format_coordinates)
<a id="source-101"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 110–110 _(s55)_

<details>
<summary>View retained excerpt</summary>

```text
if (rain == null || !rain.isNumber) period.putNull("precipitationMm") else period.put("precipitationMm", rain.asDouble())
```
</details>


**Process blocks citing this excerpt:** [decision: Use JSON null when precipitation is missing or nonnumeric\.](#block-check_rain) · [action: Set \`period\["precipitationMm"\]\` to JSON null\.](#block-put_null_rain) · [action: Set \`period\["precipitationMm"\]\` from \`rain\.asDouble\(\)\`\.](#block-put_numeric_rain) · [Rain is missing or nonnumeric](#predicate-rain_missing_or_nonnumeric)
<a id="source-102"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 116–116 _(s60)_

<details>
<summary>View retained excerpt</summary>

```text
val forecast = json.createObjectNode().put("updatedAt", updatedAt).put("fetchedAt", Instant.now().toString()).put("mode", mode)
```
</details>


**Process blocks citing this excerpt:** [action: Construct \`forecast\` with \`updatedAt\`, \`Instant\.now\(\)\.toString\(\)\` as \`fetchedAt\`, and \`mode\`; attach \`periods\` under \`periods\`\.](#block-build_forecast)
<a id="source-103"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 99–99 _(s63)_

<details>
<summary>View retained excerpt</summary>

```text
lastModified = response.headers().firstValue("Last-Modified").orElse(null)
```
</details>


**Process blocks citing this excerpt:** [action: Set \`lastModified\` from the \`Last\-Modified\` header, using null if absent\.](#block-read_last_modified)
<a id="source-104"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 98–98 _(s64)_

<details>
<summary>View retained excerpt</summary>

```text
{ "PROVIDER_HTTP_" + response.statusCode() }
```
</details>


**Process blocks citing this excerpt:** [throw: The source's \`require\` failure message is \`PROVIDER\_HTTP\_\` plus the response status code; exception type and runtime dispatch are not established\.](#block-reject_http_status)
<a id="source-105"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 123–123 _(s68)_

<details>
<summary>View retained excerpt</summary>

```text
event.set("forecast", forecast)
```
</details>


**Process blocks citing this excerpt:** [action: After the forecast update call, form \`eventId\` as \`$id:$updatedAt\`; create an event with that id, type \`forecast\.updated\`, version 1, and set its \`place\` and \`forecast\` values\.](#block-build_event)
<a id="source-106"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 98–98 _(s69)_

<details>
<summary>View retained excerpt</summary>

```text
response.statusCode() == 200 || response.statusCode() == 203
```
</details>


**Process blocks citing this excerpt:** [decision: Only statuses 200 and 203 proceed to capture Last\-Modified and read the response body\.](#block-check_http_status) · [Response status is 200 or 203](#predicate-accepted_status)
<a id="source-107"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 76–76 _(s7)_

<details>
<summary>View retained excerpt</summary>

```text
mode == "fixture"
```
</details>


**Process blocks citing this excerpt:** [decision: Choose the fixture source when \`mode == "fixture"\`; otherwise enter the branch that requires live mode\.](#block-choose_fixture) · [action: Read \`/app/fixtures/$id\.json\` into \`raw\`\. The file contents are not present in this packet\.](#block-read_fixture)
<a id="source-108"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 91–91 _(s71)_

<details>
<summary>View retained excerpt</summary>

```text
val seconds = response.headers().firstValue("Retry-After").orElse("60").toLongOrNull() ?: 60L
```
</details>


**Process blocks citing this excerpt:** [action: Use the Retry\-After value or \`"60"\`; if \`toLongOrNull\(\)\` returns null use \`60L\`, clamp to at least \`60L\`, then assign now plus that many seconds to \`nextAttempt\[id\]\`\.](#block-set_retry_delay) · [Response status is 429](#predicate-status_429)
<a id="source-109"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 90–93 _(s78)_

<details>
<summary>View retained excerpt</summary>

```text
nextAttempt[id] = if (response.statusCode() == 429) {
                val seconds = response.headers().firstValue("Retry-After").orElse("60").toLongOrNull() ?: 60L
                Instant.now().plusSeconds(seconds.coerceAtLeast(60L))
            } else expires
```
</details>


**Process blocks citing this excerpt:** [decision: Set a minimum retry time for status 429; for other statuses, set the next attempt to \`expires\`\.](#block-check_429) · [action: Assign \`expires\` to \`nextAttempt\[id\]\`\.](#block-set_expiry_retry)
<a id="source-110"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 81–81 _(s80)_

<details>
<summary>View retained excerpt</summary>

```text
if (nextAttempt[id]?.isAfter(Instant.now()) == true) error("PROVIDER_BACKOFF")
```
</details>


**Process blocks citing this excerpt:** [throw: When the next\-attempt instant is after now, the source invokes \`error\("PROVIDER\_BACKOFF"\)\`\.](#block-backoff_error) · [decision: Stop on an active backoff; otherwise assign a preliminary next\-attempt time before building and sending the request\.](#block-check_backoff)
<a id="source-111"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 77–77 _(s81)_

<details>
<summary>View retained excerpt</summary>

```text
Files.readString(Path.of("/app/fixtures/$id.json"))
```
</details>


**Process blocks citing this excerpt:** [action: Read \`/app/fixtures/$id\.json\` into \`raw\`\. The file contents are not present in this packet\.](#block-read_fixture)
<a id="source-112"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 87–87 _(s87)_

<details>
<summary>View retained excerpt</summary>

```text
if (modified != null) builder.header("If-Modified-Since", modified)
```
</details>


**Process blocks citing this excerpt:** [action: Add \`If\-Modified\-Since\` with \`modified\`\.](#block-add_modified_header) · [decision: Add the conditional request header only when the cached value is non\-null\.](#block-conditional_header) · [action: Leave \`If\-Modified\-Since\` off the request builder\.](#block-omit_modified_header)
<a id="source-113"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 82–82 _(s88)_

<details>
<summary>View retained excerpt</summary>

```text
Instant.now().plusSeconds(60)
```
</details>


**Process blocks citing this excerpt:** [action: Assign \`nextAttempt\[id\] = Instant\.now\(\)\.plusSeconds\(60\)\` before the HTTP send call\.](#block-seed_next_attempt)
<a id="source-114"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 98–98 _(s89)_

<details>
<summary>View retained excerpt</summary>

```text
{ "PROVIDER_HTTP_" + response.statusCode() }
```
</details>


**Process blocks citing this excerpt:** [throw: The source's \`require\` failure message is \`PROVIDER\_HTTP\_\` plus the response status code; exception type and runtime dispatch are not established\.](#block-reject_http_status)
<a id="source-115"></a>- **`src/main/kotlin/weather/Forecasts.kt`:** 80–80 _(s9)_

<details>
<summary>View retained excerpt</summary>

```text
System.getenv("MET_USER_AGENT")?.takeIf { it.isNotBlank() } ?: error("MET_USER_AGENT_REQUIRED")
```
</details>


**Process blocks citing this excerpt:** [decision: Require a non\-null, nonblank provider user\-agent value\.](#block-check_agent) · [throw: The source invokes \`error\("MET\_USER\_AGENT\_REQUIRED"\)\`; the exception type and dispatch are not established\.](#block-missing_agent) · [action: Bind the nonblank environment value as \`agent\` for the request\.](#block-use_agent) · [Provider user agent is nonblank](#predicate-agent_ready)

## Packet gaps and limits

### Captured gaps

- `\{"code":"CALL\_TARGET\_BODY\_NOT\_CAPTURED","count":63,"examples":\[\{"from":"callable:weather/Forecasts\.refresh\#jvm:\(Ltools/jackson/databind/JsonNode;\)V","scope":":/main","target":"callable:java/lang/System\.getenv\#jvm:\(Ljava/lang/String;\)Ljava/lang/String;"\},\{"from":"callable:weather/Forecasts\.refresh\#jvm:\(Ltools/jackson/databind/JsonNode;\)V","scope":":/main","target":"callable:java/math/BigDecimal\.setScale\#jvm:\(ILjava/math/RoundingMode;\)Ljava/math/BigDecimal;"\},\{"from":"callable:weather/Forecasts\.refresh\#jvm:\(Ltools/jackson/databind/JsonNode;\)V","scope":":/main","target":"callable:java/math/BigDecimal\.toPlainString\#jvm:\(\)Ljava/lang/String;"\},\{"from":"callable:weather/Forecasts\.refresh\#jvm:\(Ltools/jackson/databind/JsonNode;\)V","scope":":/main","target":"callable:java/math/BigDecimal\.valueOf\#jvm:\(D\)Ljava/math/BigDecimal;"\},\{"from":"callable:weather/Forecasts\.refresh\#jvm:\(Ltools/jackson/databind/JsonNode;\)V","scope":":/main","target":"callable:java/net/URI\.create\#jvm:\(Ljava/lang/String;\)Ljava/net/URI;"\},\{"from":"callable:weather/Forecasts\.refresh\#jvm:\(Ltools/jackson/databind/JsonNode;\)V","scope":":/main","target":"callable:java/net/http/HttpClient\.send\#jvm:\(Ljava/net/http/HttpRequest;Ljava/net/http/HttpResponse$BodyHandler;\)Ljava/net/http/HttpResponse;"\},\{"from":"callable:weather/Forecasts\.refresh\#jvm:\(Ltools/jackson/databind/JsonNode;\)V","scope":":/main","target":"callable:java/net/http/HttpHeaders\.firstValue\#jvm:\(Ljava/lang/String;\)Ljava/util/Optional;"\},\{"from":"callable:weather/Forecasts\.refresh\#jvm:\(Ltools/jackson/databind/JsonNode;\)V","scope":":/main","target":"callable:java/net/http/HttpRequest\.Builder\.GET\#jvm:\(\)Ljava/net/http/HttpRequest$Builder;"\}\]\}`
- `\{"code":"DIRECT\_DECLARED\_TYPES\_ONLY","count":1,"examples":\[null\]\}`
- `\{"code":"FLOW\_TARGET\_IDENTITY\_UNAVAILABLE","count":1,"examples":\[\{"factId":"forecasts:flow:20ff81788759c7859216858c","from":"callable:weather/Forecasts\.refresh\#jvm:\(Ltools/jackson/databind/JsonNode;\)V"\}\]\}`
- `\{"code":"METHOD\_BODY\_PARSE\_UNAVAILABLE","count":1,"examples":\[\{"symbol":"callable:weather/Forecasts\.refresh\#jvm:\(Ltools/jackson/databind/JsonNode;\)V"\}\]\}`
- `\{"code":"PROCESS\_TYPE\_DECLARATION\_NOT\_CAPTURED","count":1,"examples":\[\{"candidateCount":0,"identity":"class:weather/Forecasts","scope":":/main"\}\]\}`
- `\{"code":"SOURCE\_REFERENCE\_CANDIDATE\_AUTHORITY","count":1,"examples":\[null\]\}`
- `\{"code":"STRUCTURAL\_DATAFLOW\_NOT\_AVAILABLE","count":1,"examples":\[null\]\}`

### Interpretation limits

- `Retained FLOW and compiler relations preserve provider evidence, not runtime execution or statement timing\.`
- `SOURCE\_REFERENCE\_CANDIDATE edges identify same\-scope source\-context candidates only; they do not establish executed calls, receiver identity, inheritance dispatch, or order\.`
- `Only the supplied root, selected declarations, retained method source, fields, types, and listed frontiers support claims; missing context remains unknown\.`
- `A field type or superclass declaration does not establish the runtime object or selected override\.`

### Coverage boundaries

- `CALLBACK\_INVOCATION\_ORDER\_AND\_COUNT\_NOT\_ESTABLISHED`
- `DOCUMENTATION\_CALL\_TARGET\_UNRESOLVED`
- `EXCEPTION\_TYPES\_AND\_DISPATCH\_NOT\_ESTABLISHED`
- `EXTERNAL\_OR\_LOCAL\_ARGUMENT\_TARGET`
- `IMPLICIT\_OR\_MISSING\_RETURN\_SOURCE`
- `IMPLICIT\_RETURN\_UNSUPPORTED`
- `KOTLIN\_ANALYSIS\_USES\_DIFFERENT\_COMPILER`
- `KOTLIN\_CALL\_RELATION\_PARTIAL`
- `LOCAL\_CFG\_NORMALIZATION\_FAILED`
- `LOCAL\_GENERATED\_OR\_UNRESOLVED\_RETURN\_VALUE`
- `MAVEN\_CLASSPATH\_ARTIFACT\_TO\_COORDINATE\_BIJECTION\_UNAVAILABLE`
- `MAVEN\_TOOLCHAIN\_SELECTION\_USES\_BUILD\_JVM`
- `MULTIPLE\_OR\_AMBIGUOUS\_RETURN\_VALUE\_OCCURRENCES`
- `NON\_EXPLICIT\_CALL\_RECEIVER\_UNSUPPORTED`
- `NON\_LINEAR\_OR\_MULTIPLE\_RETURN\_FLOW`
- `NO\_COMPILER\_CALLABLE\_ID`
- `NO\_SOURCE\_FUNCTION`
- `SAFE\_CALL\_POLICY\_UNSUPPORTED`
- `UNRESOLVED\_CALLABLE\_TARGET`
- `UNRESOLVED\_DESCRIPTOR\_TYPE`
- `UNRESOLVED\_FALLBACK\_OCCURRENCE`
- `UNRESOLVED\_NULLABLE\_SOURCE\_OCCURRENCE`
- `UNRESOLVED\_RELATION\_TYPE`

<details>
<summary>Full evidence inventory</summary>

<a id="evidence-1"></a>- **c1** — saved capture coverage
<a id="evidence-2"></a>- **d102** — Retained source data
<a id="evidence-3"></a>- **d104** — retained callsite evidence
<a id="evidence-4"></a>- **d105** — retained callsite evidence
<a id="evidence-5"></a>- **d107** — Retained source data
<a id="evidence-6"></a>- **d108** — retained callsite evidence
<a id="evidence-7"></a>- **d109** — Retained source data
<a id="evidence-8"></a>- **d110** — Retained source data
<a id="evidence-9"></a>- **d111** — retained callsite evidence
<a id="evidence-10"></a>- **d112** — retained callsite evidence
<a id="evidence-11"></a>- **d116** — Retained source data
<a id="evidence-12"></a>- **d119** — Retained source data
<a id="evidence-13"></a>- **d121** — Retained source data
<a id="evidence-14"></a>- **d122** — Retained source data
<a id="evidence-15"></a>- **d124** — retained callsite evidence
<a id="evidence-16"></a>- **d125** — retained callsite evidence
<a id="evidence-17"></a>- **d126** — retained callsite evidence
<a id="evidence-18"></a>- **d127** — retained callsite evidence
<a id="evidence-19"></a>- **d131** — Retained source data
<a id="evidence-20"></a>- **d133** — retained callsite evidence
<a id="evidence-21"></a>- **d134** — Retained source data
<a id="evidence-22"></a>- **d135** — retained callsite evidence
<a id="evidence-23"></a>- **d137** — retained callsite evidence
<a id="evidence-24"></a>- **d138** — Retained source data
<a id="evidence-25"></a>- **d14** — retained callsite evidence
<a id="evidence-26"></a>- **d141** — retained callsite evidence
<a id="evidence-27"></a>- **d145** — Retained source data
<a id="evidence-28"></a>- **d146** — retained callsite evidence
<a id="evidence-29"></a>- **d148** — retained callsite evidence
<a id="evidence-30"></a>- **d149** — retained callsite evidence
<a id="evidence-31"></a>- **d15** — retained callsite evidence
<a id="evidence-32"></a>- **d153** — retained callsite evidence
<a id="evidence-33"></a>- **d155** — Retained source data
<a id="evidence-34"></a>- **d156** — retained callsite evidence
<a id="evidence-35"></a>- **d158** — Retained source data
<a id="evidence-36"></a>- **d159** — retained callsite evidence
<a id="evidence-37"></a>- **d16** — Retained source data
<a id="evidence-38"></a>- **d162** — Retained source data
<a id="evidence-39"></a>- **d164** — Retained source data
<a id="evidence-40"></a>- **d165** — retained callsite evidence
<a id="evidence-41"></a>- **d168** — Retained source data
<a id="evidence-42"></a>- **d17** — retained callsite evidence
<a id="evidence-43"></a>- **d171** — Retained source data
<a id="evidence-44"></a>- **d173** — retained callsite evidence
<a id="evidence-45"></a>- **d174** — retained callsite evidence
<a id="evidence-46"></a>- **d175** — retained callsite evidence
<a id="evidence-47"></a>- **d18** — Retained source data
<a id="evidence-48"></a>- **d181** — retained callsite evidence
<a id="evidence-49"></a>- **d182** — retained callsite evidence
<a id="evidence-50"></a>- **d186** — Retained source data
<a id="evidence-51"></a>- **d187** — retained callsite evidence
<a id="evidence-52"></a>- **d188** — retained callsite evidence
<a id="evidence-53"></a>- **d189** — retained callsite evidence
<a id="evidence-54"></a>- **d190** — Retained source data
<a id="evidence-55"></a>- **d194** — retained callsite evidence
<a id="evidence-56"></a>- **d195** — Retained source data
<a id="evidence-57"></a>- **d197** — Retained source data
<a id="evidence-58"></a>- **d20** — Retained source data
<a id="evidence-59"></a>- **d201** — Retained source data
<a id="evidence-60"></a>- **d202** — retained callsite evidence
<a id="evidence-61"></a>- **d204** — Retained source data
<a id="evidence-62"></a>- **d206** — retained callsite evidence
<a id="evidence-63"></a>- **d207** — retained callsite evidence
<a id="evidence-64"></a>- **d210** — Retained source data
<a id="evidence-65"></a>- **d211** — retained callsite evidence
<a id="evidence-66"></a>- **d212** — Retained source data
<a id="evidence-67"></a>- **d214** — retained callsite evidence
<a id="evidence-68"></a>- **d216** — Retained source data
<a id="evidence-69"></a>- **d218** — retained callsite evidence
<a id="evidence-70"></a>- **d219** — Retained source data
<a id="evidence-71"></a>- **d224** — retained callsite evidence
<a id="evidence-72"></a>- **d226** — retained callsite evidence
<a id="evidence-73"></a>- **d227** — retained callsite evidence
<a id="evidence-74"></a>- **d228** — Retained source data
<a id="evidence-75"></a>- **d229** — Retained source data
<a id="evidence-76"></a>- **d23** — retained callsite evidence
<a id="evidence-77"></a>- **d232** — Retained source data
<a id="evidence-78"></a>- **d234** — Retained source data
<a id="evidence-79"></a>- **d236** — Retained source data
<a id="evidence-80"></a>- **d237** — retained callsite evidence
<a id="evidence-81"></a>- **d238** — retained callsite evidence
<a id="evidence-82"></a>- **d239** — Retained source data
<a id="evidence-83"></a>- **d24** — Retained source data
<a id="evidence-84"></a>- **d240** — Retained source data
<a id="evidence-85"></a>- **d241** — Retained source data
<a id="evidence-86"></a>- **d242** — retained callsite evidence
<a id="evidence-87"></a>- **d246** — Retained source data
<a id="evidence-88"></a>- **d247** — retained callsite evidence
<a id="evidence-89"></a>- **d248** — retained callsite evidence
<a id="evidence-90"></a>- **d249** — retained callsite evidence
<a id="evidence-91"></a>- **d25** — retained callsite evidence
<a id="evidence-92"></a>- **d253** — retained callsite evidence
<a id="evidence-93"></a>- **d254** — Retained source data
<a id="evidence-94"></a>- **d256** — retained callsite evidence
<a id="evidence-95"></a>- **d257** — retained callsite evidence
<a id="evidence-96"></a>- **d259** — retained callsite evidence
<a id="evidence-97"></a>- **d26** — retained callsite evidence
<a id="evidence-98"></a>- **d260** — Retained source data
<a id="evidence-99"></a>- **d261** — retained callsite evidence
<a id="evidence-100"></a>- **d262** — Retained source data
<a id="evidence-101"></a>- **d263** — retained callsite evidence
<a id="evidence-102"></a>- **d264** — retained callsite evidence
<a id="evidence-103"></a>- **d267** — retained callsite evidence
<a id="evidence-104"></a>- **d268** — retained callsite evidence
<a id="evidence-105"></a>- **d27** — Retained source data
<a id="evidence-106"></a>- **d270** — retained callsite evidence
<a id="evidence-107"></a>- **d271** — retained callsite evidence
<a id="evidence-108"></a>- **d272** — retained callsite evidence
<a id="evidence-109"></a>- **d273** — retained callsite evidence
<a id="evidence-110"></a>- **d274** — Retained source data
<a id="evidence-111"></a>- **d279** — retained callsite evidence
<a id="evidence-112"></a>- **d284** — Retained source data
<a id="evidence-113"></a>- **d286** — retained callsite evidence
<a id="evidence-114"></a>- **d287** — retained callsite evidence
<a id="evidence-115"></a>- **d288** — Retained source data
<a id="evidence-116"></a>- **d29** — retained callsite evidence
<a id="evidence-117"></a>- **d290** — retained callsite evidence
<a id="evidence-118"></a>- **d291** — Retained source data
<a id="evidence-119"></a>- **d292** — retained callsite evidence
<a id="evidence-120"></a>- **d295** — Retained source data
<a id="evidence-121"></a>- **d296** — retained callsite evidence
<a id="evidence-122"></a>- **d298** — Retained source data
<a id="evidence-123"></a>- **d299** — retained callsite evidence
<a id="evidence-124"></a>- **d300** — Retained source data
<a id="evidence-125"></a>- **d301** — Retained source data
<a id="evidence-126"></a>- **d303** — Retained source data
<a id="evidence-127"></a>- **d305** — Retained source data
<a id="evidence-128"></a>- **d306** — Retained source data
<a id="evidence-129"></a>- **d307** — retained callsite evidence
<a id="evidence-130"></a>- **d308** — retained callsite evidence
<a id="evidence-131"></a>- **d31** — retained callsite evidence
<a id="evidence-132"></a>- **d310** — retained callsite evidence
<a id="evidence-133"></a>- **d311** — Retained source data
<a id="evidence-134"></a>- **d313** — retained callsite evidence
<a id="evidence-135"></a>- **d317** — retained callsite evidence
<a id="evidence-136"></a>- **d318** — retained callsite evidence
<a id="evidence-137"></a>- **d320** — retained callsite evidence
<a id="evidence-138"></a>- **d322** — retained callsite evidence
<a id="evidence-139"></a>- **d323** — retained callsite evidence
<a id="evidence-140"></a>- **d326** — retained callsite evidence
<a id="evidence-141"></a>- **d327** — Retained source data
<a id="evidence-142"></a>- **d328** — Retained source data
<a id="evidence-143"></a>- **d329** — retained callsite evidence
<a id="evidence-144"></a>- **d33** — retained callsite evidence
<a id="evidence-145"></a>- **d330** — Retained source data
<a id="evidence-146"></a>- **d331** — Retained source data
<a id="evidence-147"></a>- **d332** — Retained source data
<a id="evidence-148"></a>- **d333** — Retained source data
<a id="evidence-150"></a>- **d335** — retained callsite evidence
<a id="evidence-151"></a>- **d336** — Retained source data
<a id="evidence-152"></a>- **d337** — retained callsite evidence
<a id="evidence-153"></a>- **d338** — Retained source data
<a id="evidence-154"></a>- **d339** — retained callsite evidence
<a id="evidence-155"></a>- **d34** — Retained source data
<a id="evidence-156"></a>- **d340** — retained callsite evidence
<a id="evidence-157"></a>- **d341** — retained callsite evidence
<a id="evidence-158"></a>- **d342** — Retained source data
<a id="evidence-159"></a>- **d343** — Retained source data
<a id="evidence-160"></a>- **d345** — retained callsite evidence
<a id="evidence-161"></a>- **d347** — retained callsite evidence
<a id="evidence-162"></a>- **d348** — retained callsite evidence
<a id="evidence-163"></a>- **d351** — Retained source data
<a id="evidence-164"></a>- **d355** — retained callsite evidence
<a id="evidence-165"></a>- **d357** — retained callsite evidence
<a id="evidence-166"></a>- **d358** — retained callsite evidence
<a id="evidence-167"></a>- **d359** — Retained source data
<a id="evidence-168"></a>- **d36** — Retained source data
<a id="evidence-169"></a>- **d360** — Retained source data
<a id="evidence-170"></a>- **d363** — retained callsite evidence
<a id="evidence-171"></a>- **d364** — retained callsite evidence
<a id="evidence-172"></a>- **d365** — retained callsite evidence
<a id="evidence-173"></a>- **d367** — retained callsite evidence
<a id="evidence-174"></a>- **d369** — Retained source data
<a id="evidence-175"></a>- **d37** — retained callsite evidence
<a id="evidence-176"></a>- **d372** — retained callsite evidence
<a id="evidence-177"></a>- **d374** — Retained source data
<a id="evidence-178"></a>- **d38** — Retained source data
<a id="evidence-179"></a>- **d40** — retained callsite evidence
<a id="evidence-180"></a>- **d408** — Retained source data
<a id="evidence-181"></a>- **d417** — Retained source data
<a id="evidence-183"></a>- **d45** — retained callsite evidence
<a id="evidence-184"></a>- **d46** — retained callsite evidence
<a id="evidence-185"></a>- **d47** — Retained source data
<a id="evidence-186"></a>- **d49** — retained callsite evidence
<a id="evidence-187"></a>- **d50** — Retained source data
<a id="evidence-188"></a>- **d52** — Retained source data
<a id="evidence-189"></a>- **d53** — Retained source data
<a id="evidence-190"></a>- **d54** — retained callsite evidence
<a id="evidence-191"></a>- **d55** — retained callsite evidence
<a id="evidence-192"></a>- **d56** — retained callsite evidence
<a id="evidence-193"></a>- **d59** — retained callsite evidence
<a id="evidence-194"></a>- **d61** — Retained source data
<a id="evidence-195"></a>- **d64** — Retained source data
<a id="evidence-196"></a>- **d65** — retained callsite evidence
<a id="evidence-197"></a>- **d66** — retained callsite evidence
<a id="evidence-198"></a>- **d67** — Retained source data
<a id="evidence-199"></a>- **d68** — Retained source data
<a id="evidence-200"></a>- **d71** — retained callsite evidence
<a id="evidence-201"></a>- **d72** — Retained source data
<a id="evidence-202"></a>- **d74** — Retained source data
<a id="evidence-203"></a>- **d77** — Retained source data
<a id="evidence-204"></a>- **d79** — retained callsite evidence
<a id="evidence-205"></a>- **d80** — Retained source data
<a id="evidence-206"></a>- **d81** — Retained source data
<a id="evidence-207"></a>- **d82** — retained callsite evidence
<a id="evidence-208"></a>- **d83** — Retained source data
<a id="evidence-209"></a>- **d84** — retained callsite evidence
<a id="evidence-210"></a>- **d88** — Retained source data
<a id="evidence-211"></a>- **d89** — Retained source data
<a id="evidence-212"></a>- **d90** — retained callsite evidence
<a id="evidence-213"></a>- **d91** — Retained source data
<a id="evidence-214"></a>- **d92** — Retained source data
<a id="evidence-215"></a>- **d93** — retained callsite evidence
<a id="evidence-216"></a>- **d95** — retained callsite evidence
<a id="evidence-217"></a>- **d96** — retained callsite evidence
<a id="evidence-218"></a>- **p1** — selected internal process context
<a id="evidence-220"></a>- **s104** — retained callsite source
<a id="evidence-222"></a>- **s108** — Retained source data
<a id="evidence-223"></a>- **s109** — retained callsite source
<a id="evidence-224"></a>- **s110** — Retained source data
<a id="evidence-226"></a>- **s112** — retained callsite source
<a id="evidence-233"></a>- **s125** — retained callsite source
<a id="evidence-234"></a>- **s126** — retained callsite source
<a id="evidence-241"></a>- **s136** — retained callsite source
<a id="evidence-242"></a>- **s139** — retained callsite source
<a id="evidence-244"></a>- **s140** — Retained source data
<a id="evidence-245"></a>- **s143** — retained callsite source
<a id="evidence-247"></a>- **s148** — retained callsite source
<a id="evidence-248"></a>- **s15** — retained callsite source
<a id="evidence-250"></a>- **s151** — retained callsite source
<a id="evidence-252"></a>- **s157** — Retained source data
<a id="evidence-253"></a>- **s158** — retained callsite source
<a id="evidence-255"></a>- **s160** — Retained source data
<a id="evidence-256"></a>- **s161** — retained callsite source
<a id="evidence-257"></a>- **s165** — Retained source data
<a id="evidence-259"></a>- **s168** — retained callsite source
<a id="evidence-263"></a>- **s177** — retained callsite source
<a id="evidence-267"></a>- **s188** — retained callsite source
<a id="evidence-271"></a>- **s195** — retained callsite source
<a id="evidence-272"></a>- **s196** — Retained source data
<a id="evidence-277"></a>- **s208** — retained callsite source
<a id="evidence-280"></a>- **s212** — retained callsite source
<a id="evidence-281"></a>- **s213** — retained callsite source
<a id="evidence-282"></a>- **s216** — Retained source data
<a id="evidence-283"></a>- **s217** — retained callsite source
<a id="evidence-284"></a>- **s218** — Retained source data
<a id="evidence-289"></a>- **s230** — retained callsite source
<a id="evidence-290"></a>- **s232** — retained callsite source
<a id="evidence-292"></a>- **s234** — Retained source data
<a id="evidence-297"></a>- **s247** — retained callsite source
<a id="evidence-299"></a>- **s249** — Retained source data
<a id="evidence-301"></a>- **s250** — Retained source data
<a id="evidence-302"></a>- **s251** — Retained source data
<a id="evidence-303"></a>- **s252** — retained callsite source
<a id="evidence-304"></a>- **s256** — Retained source data
<a id="evidence-305"></a>- **s257** — retained callsite source
<a id="evidence-310"></a>- **s266** — Retained source data
<a id="evidence-311"></a>- **s268** — retained callsite source
<a id="evidence-312"></a>- **s269** — retained callsite source
<a id="evidence-315"></a>- **s274** — retained callsite source
<a id="evidence-316"></a>- **s275** — Retained source data
<a id="evidence-322"></a>- **s283** — Retained source data
<a id="evidence-325"></a>- **s287** — retained callsite source
<a id="evidence-328"></a>- **s29** — retained callsite source
<a id="evidence-330"></a>- **s3** — retained callsite source
<a id="evidence-332"></a>- **s302** — Retained source data
<a id="evidence-333"></a>- **s305** — retained callsite source
<a id="evidence-336"></a>- **s309** — retained callsite source
<a id="evidence-337"></a>- **s310** — Retained source data
<a id="evidence-338"></a>- **s311** — retained callsite source
<a id="evidence-340"></a>- **s315** — retained callsite source
<a id="evidence-342"></a>- **s318** — retained callsite source
<a id="evidence-343"></a>- **s319** — Retained source data
<a id="evidence-346"></a>- **s323** — Retained source data
<a id="evidence-349"></a>- **s329** — retained callsite source
<a id="evidence-351"></a>- **s330** — retained callsite source
<a id="evidence-352"></a>- **s332** — retained callsite source
<a id="evidence-353"></a>- **s333** — Retained source data
<a id="evidence-356"></a>- **s341** — retained callsite source
<a id="evidence-357"></a>- **s343** — retained callsite source
<a id="evidence-358"></a>- **s345** — retained callsite source
<a id="evidence-359"></a>- **s346** — retained callsite source
<a id="evidence-360"></a>- **s349** — retained callsite source
<a id="evidence-367"></a>- **s356** — Retained source data
<a id="evidence-368"></a>- **s357** — retained callsite source
<a id="evidence-369"></a>- **s358** — retained callsite source
<a id="evidence-371"></a>- **s360** — retained callsite source
<a id="evidence-374"></a>- **s363** — retained callsite source
<a id="evidence-377"></a>- **s366** — Retained source data
<a id="evidence-380"></a>- **s372** — retained callsite source
<a id="evidence-382"></a>- **s38** — retained callsite source
<a id="evidence-384"></a>- **s383** — retained callsite source
<a id="evidence-385"></a>- **s384** — retained callsite source
<a id="evidence-387"></a>- **s386** — Retained source data
<a id="evidence-388"></a>- **s389** — retained callsite source
<a id="evidence-389"></a>- **s39** — retained callsite source
<a id="evidence-390"></a>- **s390** — retained callsite source
<a id="evidence-391"></a>- **s391** — retained callsite source
<a id="evidence-392"></a>- **s393** — retained callsite source
<a id="evidence-393"></a>- **s395** — Retained source data
<a id="evidence-396"></a>- **s40** — Retained source data
<a id="evidence-397"></a>- **s42** — retained callsite source
<a id="evidence-399"></a>- **s46** — Retained source data
<a id="evidence-402"></a>- **s49** — retained callsite source
<a id="evidence-407"></a>- **s6** — retained callsite source
<a id="evidence-409"></a>- **s61** — retained callsite source
<a id="evidence-410"></a>- **s62** — retained callsite source
<a id="evidence-417"></a>- **s74** — Retained source data
<a id="evidence-418"></a>- **s76** — retained callsite source
<a id="evidence-419"></a>- **s77** — Retained source data
<a id="evidence-421"></a>- **s79** — retained callsite source
<a id="evidence-424"></a>- **s86** — Retained source data
<a id="evidence-429"></a>- **s90** — Retained source data
<a id="evidence-430"></a>- **s91** — retained callsite source
<a id="evidence-431"></a>- **s93** — retained callsite source
<a id="evidence-432"></a>- **s94** — retained callsite source
<a id="evidence-433"></a>- **s98** — Retained source data

</details>
</details>

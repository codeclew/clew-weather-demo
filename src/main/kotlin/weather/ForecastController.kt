package weather
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RestController
import org.springframework.http.ResponseEntity
import java.nio.file.Files
import java.nio.file.Path

@RestController
class ForecastController(private val forecasts: Forecasts) {
    @GetMapping("/forecasts/{id}")
    fun get(@PathVariable id: String): ResponseEntity<String> {
        val payload = forecasts.get(id) ?: return ResponseEntity.notFound().build()
        return ResponseEntity.ok().header("Content-Type", "application/json").body(payload)
    }
    @GetMapping("/health")
    fun health(): Map<String, String> { forecasts.ping(); return mapOf("database" to "READY") }
    @GetMapping("/openapi.json")
    fun openApi(): ResponseEntity<String> = ResponseEntity.ok().header("Content-Type", "application/json").body(Files.readString(Path.of("/app/contracts/forecasts.openapi.json")))
}

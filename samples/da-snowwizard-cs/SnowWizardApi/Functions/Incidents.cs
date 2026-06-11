using System.Net;
using System.Text.Json;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using SnowWizardApi.Services;

namespace SnowWizardApi.Functions;

public class Incidents
{
    private readonly ILogger<Incidents> _logger;
    private readonly SnowIncidentsService _incidentsService;

    public Incidents(ILogger<Incidents> logger, SnowIncidentsService incidentsService)
    {
        _logger = logger;
        _incidentsService = incidentsService;
    }

    [Function("incidents")]
    public async Task<HttpResponseData> Run(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get", "post", Route = "incidents/{id?}")] HttpRequestData req,
        string? id)
    {
        // Need to implement authentication to get the address from context,
        // for now lets use Fred Luddy as the current user
        var email = "fred.luddy@example.com";

        try
        {
            if (req.Method.Equals("GET", StringComparison.OrdinalIgnoreCase))
            {
                if (!string.IsNullOrEmpty(id))
                {
                    _logger.LogInformation("➡️ GET /api/incidents/{Id}", id);
                    var incident = await _incidentsService.GetIncidentAsync(id);
                    _logger.LogInformation("   ✅ GET /api/incidents/{Id}: {Count} incidents returned", id, incident.Count);
                    return await CreateJsonResponse(req, new { results = incident });
                }

                _logger.LogInformation("➡️ GET /api/incidents");
                var incidents = await _incidentsService.GetIncidentsAsync();
                _logger.LogInformation("   ✅ GET /api/incidents: {Count} incidents returned", incidents.Count);
                return await CreateJsonResponse(req, new { results = incidents });
            }

            if (req.Method.Equals("POST", StringComparison.OrdinalIgnoreCase))
            {
                var body = await req.ReadAsStringAsync();
                if (string.IsNullOrEmpty(body))
                {
                    var errorResponse = req.CreateResponse(HttpStatusCode.BadRequest);
                    await errorResponse.WriteAsJsonAsync(new { error = "No body to process this request." });
                    return errorResponse;
                }

                var requestBody = JsonSerializer.Deserialize<JsonElement>(body);
                var shortDescription = requestBody.GetProperty("short_description").GetString() ?? "";
                var description = requestBody.GetProperty("description").GetString() ?? "";

                _logger.LogInformation("➡️ POST /api/incidents");
                var result = await _incidentsService.CreateIncidentAsync(email, shortDescription, description);
                _logger.LogInformation("   ✅ POST /api/incidents: incident created!");
                return await CreateJsonResponse(req, new { results = result });
            }

            var methodNotAllowed = req.CreateResponse(HttpStatusCode.MethodNotAllowed);
            await methodNotAllowed.WriteAsJsonAsync(new { error = $"Method not allowed: {req.Method}" });
            return methodNotAllowed;
        }
        catch (Exception ex)
        {
            _logger.LogError("   ❌ /api/incidents: {Error}", ex.Message);
            var errorResp = req.CreateResponse(HttpStatusCode.InternalServerError);
            await errorResp.WriteAsJsonAsync(new { error = ex.Message });
            return errorResp;
        }
    }

    private static async Task<HttpResponseData> CreateJsonResponse(HttpRequestData req, object data)
    {
        var response = req.CreateResponse(HttpStatusCode.OK);
        await response.WriteAsJsonAsync(data);
        return response;
    }
}

using System.Net;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using SnowWizardApi.Services;

namespace SnowWizardApi.Functions;

public class Me
{
    private readonly ILogger<Me> _logger;
    private readonly SnowProfilesService _profilesService;

    public Me(ILogger<Me> logger, SnowProfilesService profilesService)
    {
        _logger = logger;
        _profilesService = profilesService;
    }

    [Function("me")]
    public async Task<HttpResponseData> Run(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "me/{command?}")] HttpRequestData req,
        string? command)
    {
        // Need to implement authentication to get the address from context,
        // for now lets use Fred Luddy as the current user
        var email = "fred.luddy@example.com";

        try
        {
            _logger.LogInformation("➡️ GET /api/me");
            var profile = await _profilesService.GetProfileAsync(email);
            _logger.LogInformation("   ✅ GET /api/me: {Count} profiles returned", profile.Count);

            var response = req.CreateResponse(HttpStatusCode.OK);
            await response.WriteAsJsonAsync(new { results = profile });
            return response;
        }
        catch (Exception ex)
        {
            _logger.LogError("   ❌ GET /api/me: {Error}", ex.Message);
            var errorResp = req.CreateResponse(HttpStatusCode.InternalServerError);
            await errorResp.WriteAsJsonAsync(new { error = ex.Message });
            return errorResp;
        }
    }
}

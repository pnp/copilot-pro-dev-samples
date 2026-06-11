using System.Net;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using SnowWizardApi.Services;

namespace SnowWizardApi.Functions;

public class Profiles
{
    private readonly ILogger<Profiles> _logger;
    private readonly SnowProfilesService _profilesService;

    public Profiles(ILogger<Profiles> logger, SnowProfilesService profilesService)
    {
        _logger = logger;
        _profilesService = profilesService;
    }

    [Function("profiles")]
    public async Task<HttpResponseData> Run(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "profiles/{email?}")] HttpRequestData req,
        string? email)
    {
        try
        {
            var userEmail = email?.ToLower() ?? "";

            _logger.LogInformation("➡️ GET /api/profiles");
            var profile = await _profilesService.GetProfileAsync(userEmail);
            _logger.LogInformation("   ✅ GET /api/profiles: {Count} profiles returned", profile.Count);

            var response = req.CreateResponse(HttpStatusCode.OK);
            await response.WriteAsJsonAsync(new { results = profile });
            return response;
        }
        catch (Exception ex)
        {
            _logger.LogError("   ❌ GET /api/profiles: {Error}", ex.Message);
            var errorResp = req.CreateResponse(HttpStatusCode.InternalServerError);
            await errorResp.WriteAsJsonAsync(new { error = ex.Message });
            return errorResp;
        }
    }
}

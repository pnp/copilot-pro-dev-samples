using System.IdentityModel.Tokens.Jwt;
using System.Net;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.IdentityModel.Protocols.OpenIdConnect;
using Microsoft.IdentityModel.Tokens;
using TreyResearchApi.Models;
using TreyResearchApi.Services;

namespace TreyResearchApi.Middleware;

public class UserInfo
{
    public string? Id { get; set; }
    public string Name { get; set; } = "";
    public string Email { get; set; } = "";
}

public static class AuthMiddleware
{
    private static Microsoft.IdentityModel.Protocols.ConfigurationManager<OpenIdConnectConfiguration>? _configManager;
    private static readonly object _lock = new();

    private static Microsoft.IdentityModel.Protocols.ConfigurationManager<OpenIdConnectConfiguration> GetConfigManager(string tenantId)
    {
        if (_configManager == null)
        {
            lock (_lock)
            {
                _configManager ??= new Microsoft.IdentityModel.Protocols.ConfigurationManager<OpenIdConnectConfiguration>(
                    $"https://login.microsoftonline.com/{tenantId}/v2.0/.well-known/openid-configuration",
                    new OpenIdConnectConfigurationRetriever());
            }
        }
        return _configManager;
    }

    public static string? GetToken(HttpRequestData req)
    {
        if (req.Headers.TryGetValues("Authorization", out var values))
        {
            var authHeader = values.FirstOrDefault();
            if (authHeader?.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase) == true)
            {
                return authHeader["Bearer ".Length..];
            }
        }
        return null;
    }

    public static async Task<UserInfo?> ValidateTokenAsync(string token)
    {
        var clientId = Environment.GetEnvironmentVariable("ENTRA_APP_CLIENT_ID");
        var tenantId = Environment.GetEnvironmentVariable("ENTRA_APP_TENANT_ID");

        if (string.IsNullOrEmpty(clientId) || string.IsNullOrEmpty(tenantId))
        {
            Console.WriteLine("ENTRA_APP_CLIENT_ID or ENTRA_APP_TENANT_ID not configured");
            return null;
        }

        try
        {
            var configManager = GetConfigManager(tenantId);
            var config = await configManager.GetConfigurationAsync();

            var validationParams = new TokenValidationParameters
            {
                ValidateIssuer = true,
                ValidIssuer = $"https://login.microsoftonline.com/{tenantId}/v2.0",
                ValidateAudience = true,
                ValidAudience = clientId,
                ValidateLifetime = true,
                IssuerSigningKeys = config.SigningKeys,
                ValidateIssuerSigningKey = true
            };

            var handler = new JwtSecurityTokenHandler();
            handler.ValidateToken(token, validationParams, out var validatedToken);

            var jwtToken = (JwtSecurityToken)validatedToken;

            // Verify scope
            var scp = jwtToken.Claims.FirstOrDefault(c => c.Type == "scp")?.Value;
            if (scp == null || !scp.Contains("access_as_user"))
            {
                Console.WriteLine("Token does not contain required scope 'access_as_user'");
                return null;
            }

            // Verify it's not an app token
            var idtyp = jwtToken.Claims.FirstOrDefault(c => c.Type == "idtyp")?.Value;
            if (idtyp == "app")
            {
                Console.WriteLine("App tokens are not allowed");
                return null;
            }

            var name = jwtToken.Claims.FirstOrDefault(c => c.Type == "name")?.Value ?? "";
            var email = jwtToken.Claims.FirstOrDefault(c => c.Type == "preferred_username")?.Value ?? "";

            return new UserInfo { Name = name, Email = email };
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Token validation failed: {ex.Message}");
            return null;
        }
    }

    public static async Task<ApiConsultant?> EnsureConsultantAsync(UserInfo userInfo)
    {
        var consultantApi = new ConsultantApiService();
        var consultant = await consultantApi.GetApiConsultantByEmailAsync(userInfo.Email);

        if (consultant == null)
        {
            consultant = await consultantApi.CreateApiConsultantAsync(new Consultant
            {
                Name = userInfo.Name,
                Email = userInfo.Email,
                Phone = "1-555-456-7890",
                ConsultantPhotoUrl = "https://bobgerman.github.io/fictitiousAiGenerated/Unknown.jpg",
                Location = new Location
                {
                    Street = "5 Wayside Rd.",
                    City = "Burlington",
                    State = "MA",
                    Country = "USA",
                    PostalCode = "01803",
                    Latitude = 42.5048,
                    Longitude = -71.1956
                },
                Skills = new List<string> { "C#", "JavaScript", "TypeScript", "React", "Node.js" },
                Certifications = new List<string> { "MCSADA", "Azure Developer Associate", "MCAAF", "Azure AI Fundamentals" },
                Roles = new List<string> { "Project lead", "Developer", "Architect", "DevOps" }
            });
        }

        return consultant;
    }

    public static HttpResponseData CreateErrorResponse(HttpRequestData req, HttpStatusCode status, string error, string message)
    {
        var response = req.CreateResponse(status);
        response.Headers.Add("Content-Type", "application/json");
        response.Headers.Add("Access-Control-Allow-Origin", "*");
        response.Headers.Add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
        response.Headers.Add("Access-Control-Allow-Headers", "Content-Type, Authorization");
        response.WriteAsJsonAsync(new { error, message }).AsTask().Wait();
        return response;
    }

    public static void AddCorsHeaders(HttpResponseData response)
    {
        response.Headers.Add("Access-Control-Allow-Origin", "*");
        response.Headers.Add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
        response.Headers.Add("Access-Control-Allow-Headers", "Content-Type, Authorization");
    }
}

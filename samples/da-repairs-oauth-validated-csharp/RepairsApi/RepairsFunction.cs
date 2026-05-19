using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using Microsoft.IdentityModel.Protocols;
using Microsoft.IdentityModel.Protocols.OpenIdConnect;
using Microsoft.IdentityModel.Tokens;
using System.IdentityModel.Tokens.Jwt;
using System.Net;
using HttpRequestData = Microsoft.Azure.Functions.Worker.Http.HttpRequestData;
using HttpResponseData = Microsoft.Azure.Functions.Worker.Http.HttpResponseData;

namespace RepairsApi
{
    public class RepairsFunction
    {
        private readonly ILogger _logger;
        private static ConfigurationManager<OpenIdConnectConfiguration>? _configManager;

        public RepairsFunction(ILoggerFactory loggerFactory)
        {
            _logger = loggerFactory.CreateLogger<RepairsFunction>();
        }

        [Function("repairs")]
        public async Task<HttpResponseData> GetRepairsAsync(
            [HttpTrigger(AuthorizationLevel.Anonymous, "get")] HttpRequestData req)
        {
            _logger.LogInformation("C# HTTP trigger function processed a repairs request.");

            var clientId = Environment.GetEnvironmentVariable("AAD_APP_CLIENT_ID") ?? "";
            var tenantId = Environment.GetEnvironmentVariable("AAD_APP_TENANT_ID") ?? "";
            var authority = Environment.GetEnvironmentVariable("AAD_APP_OAUTH_AUTHORITY") ?? "";

            // Token validation
            try
            {
                string? authHeader = null;
                if (req.Headers.TryGetValues("Authorization", out var authValues))
                {
                    authHeader = authValues.FirstOrDefault();
                }

                var token = authHeader != null && authHeader.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase)
                    ? authHeader.Substring(7)
                    : null;

                if (string.IsNullOrEmpty(token))
                {
                    _logger.LogError("No token found in request");
                    return req.CreateResponse(HttpStatusCode.Unauthorized);
                }

                if (_configManager == null)
                {
                    var metadataUrl = $"https://login.microsoftonline.com/{tenantId}/v2.0/.well-known/openid-configuration";
                    _configManager = new ConfigurationManager<OpenIdConnectConfiguration>(
                        metadataUrl, new OpenIdConnectConfigurationRetriever());
                }

                var openIdConfig = await _configManager.GetConfigurationAsync();

                var validationParameters = new TokenValidationParameters
                {
                    ValidAudiences = new[] { clientId, $"api://{clientId}" },
                    ValidIssuer = $"{authority}/v2.0",
                    IssuerSigningKeys = openIdConfig.SigningKeys,
                    ValidateAudience = true,
                    ValidateIssuer = true,
                    ValidateIssuerSigningKey = true,
                    ValidateLifetime = true,
                };

                var handler = new JwtSecurityTokenHandler();
                var principal = handler.ValidateToken(token, validationParameters, out var validatedToken);

                // Verify required scope
                var scp = principal.FindFirst("scp")?.Value
                    ?? principal.FindFirst("http://schemas.microsoft.com/identity/claims/scope")?.Value
                    ?? "";
                if (!scp.Split(' ').Contains("repairs_read"))
                {
                    _logger.LogError("Token missing required scope 'repairs_read'");
                    return req.CreateResponse(HttpStatusCode.Unauthorized);
                }

                var userId = principal.FindFirst("oid")?.Value ?? "";
                var userName = principal.FindFirst("name")?.Value ?? "";
                _logger.LogInformation("Token is valid for user {UserName} ({UserId})", userName, userId);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Token validation failed");
                return req.CreateResponse(HttpStatusCode.Unauthorized);
            }

            // Get the assignedTo query parameter
            var assignedTo = req.Query["assignedTo"];
            var allRepairs = RepairsData.GetRepairs();
            IEnumerable<Models.Repair> results = allRepairs;

            if (!string.IsNullOrEmpty(assignedTo))
            {
                var query = assignedTo.Trim().ToLowerInvariant();
                results = allRepairs.Where(item =>
                {
                    var fullName = item.AssignedTo.ToLowerInvariant();
                    var parts = fullName.Split(' ');
                    var firstName = parts[0];
                    var lastName = parts.Length > 1 ? parts[1] : "";
                    return fullName == query || firstName == query || lastName == query;
                });
            }

            var response = req.CreateResponse(HttpStatusCode.OK);
            await response.WriteAsJsonAsync(new { results = results.ToList() });
            return response;
        }
    }
}

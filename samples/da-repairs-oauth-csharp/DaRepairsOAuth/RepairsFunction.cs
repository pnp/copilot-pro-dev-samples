using System.Net;
using System.Text;
using System.Text.Json;
using DaRepairsOAuth.Models;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;

namespace DaRepairsOAuth;

public class RepairsFunction
{
    private const string RequiredScope = "repairs_read";
    private readonly ILogger<RepairsFunction> _logger;

    public RepairsFunction(ILoggerFactory loggerFactory)
    {
        _logger = loggerFactory.CreateLogger<RepairsFunction>();
    }

    [Function("repairs")]
    public async Task<HttpResponseData> GetRepairsAsync(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "repairs")] HttpRequestData req)
    {
        _logger.LogInformation("C# HTTP trigger function processed a repairs request.");

        if (!HasRequiredScope(req, RequiredScope))
        {
            var forbidden = req.CreateResponse(HttpStatusCode.Forbidden);
            await forbidden.WriteStringAsync("Insufficient permissions");
            return forbidden;
        }

        IEnumerable<RepairRecord> results = RepairsData.GetRecords();
        var assignedTo = req.Query["assignedTo"];

        if (!string.IsNullOrWhiteSpace(assignedTo))
        {
            var query = assignedTo.Trim().ToLowerInvariant();
            results = results.Where(record => MatchesAssignedTo(record.AssignedTo, query)).ToArray();
        }

        var response = req.CreateResponse(HttpStatusCode.OK);
        await response.WriteAsJsonAsync(new { results });
        return response;
    }

    private static bool MatchesAssignedTo(string fullName, string query)
    {
        var normalizedName = fullName.Trim().ToLowerInvariant();
        var nameParts = normalizedName.Split(' ', StringSplitOptions.RemoveEmptyEntries);

        return normalizedName == query
            || nameParts.Any(part => part == query);
    }

    private static bool HasRequiredScope(HttpRequestData req, string requiredScope)
    {
        if (!TryGetBearerToken(req, out var token))
        {
            return false;
        }

        if (!TryGetScopes(token, out var scopes))
        {
            return false;
        }

        return scopes.Contains(requiredScope, StringComparer.Ordinal);
    }

    private static bool TryGetBearerToken(HttpRequestData req, out string token)
    {
        token = string.Empty;

        if (!req.Headers.TryGetValues("Authorization", out var authorizationValues))
        {
            return false;
        }

        var authorizationHeader = authorizationValues.FirstOrDefault();
        if (string.IsNullOrWhiteSpace(authorizationHeader))
        {
            return false;
        }

        var parts = authorizationHeader.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (parts.Length != 2 || !string.Equals(parts[0], "Bearer", StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }

        token = parts[1];
        return true;
    }

    private static bool TryGetScopes(string token, out IReadOnlyCollection<string> scopes)
    {
        scopes = Array.Empty<string>();

        var tokenParts = token.Split('.');
        if (tokenParts.Length < 2)
        {
            return false;
        }

        try
        {
            var payloadBytes = DecodeBase64Url(tokenParts[1]);
            using var document = JsonDocument.Parse(payloadBytes);

            if (!document.RootElement.TryGetProperty("scp", out var scopeElement)
                || scopeElement.ValueKind != JsonValueKind.String)
            {
                return false;
            }

            scopes = scopeElement
                .GetString()?
                .Split(' ', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
                ?? Array.Empty<string>();

            return true;
        }
        catch (FormatException)
        {
            return false;
        }
        catch (JsonException)
        {
            return false;
        }
    }

    private static byte[] DecodeBase64Url(string payload)
    {
        var normalized = payload.Replace('-', '+').Replace('_', '/');
        var padding = 4 - (normalized.Length % 4);

        if (padding is > 0 and < 4)
        {
            normalized = normalized.PadRight(normalized.Length + padding, '=');
        }

        return Convert.FromBase64String(normalized);
    }
}
using Microsoft.Identity.Web;
using PnP.Core.Services;
using System.Net.Http.Headers;
using Microsoft.Extensions.Logging;
using Microsoft.Identity.Client;

public class WebAPICustomPnPProvider : IAuthenticationProvider
{
    private readonly ITokenAcquisition _tokenAcquisition;
    private readonly ILogger<WebAPICustomPnPProvider> _logger;

   public WebAPICustomPnPProvider(ITokenAcquisition tokenAcquisition, ILogger<WebAPICustomPnPProvider> logger)
    {
        _tokenAcquisition = tokenAcquisition;
        _logger = logger;
    }

    /// <summary>
    /// Authenticates the request.
    /// </summary>
    /// <param name="resource"></param>
    /// <param name="request"></param>
    /// <returns></returns>
    public async Task AuthenticateRequestAsync(Uri resource, HttpRequestMessage request)
    {
        if (request == null)
        {
            _logger.LogError("Request is null.");
            throw new ArgumentNullException(nameof(request));
        }

        if (resource == null)
        {
            _logger.LogError("Resource is null.");
            throw new ArgumentNullException(nameof(resource));
        }

        try
        {
            var accessToken = await GetAccessTokenAsync(resource).ConfigureAwait(false);
            request.Headers.Authorization = new AuthenticationHeaderValue("bearer", accessToken);
            _logger.LogInformation("Request authenticated successfully for resource {Resource}.", resource);
        
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "An error occurred while authenticating the request for resource {Resource}.", resource);
            throw;
        }
    }

    /// <summary>
    /// Gets the access token.
    /// </summary>
    /// <param name="resource"></param>
    /// <param name="scopes"></param>
    /// <returns></returns>
    public async Task<string> GetAccessTokenAsync(Uri resource, string[] scopes)
    {
        if (resource == null)
        {
            _logger.LogError("Resource is null.");
            throw new ArgumentNullException(nameof(resource));
        }

        if (scopes == null)
        {
            _logger.LogError("Scopes are null.");
            throw new ArgumentNullException(nameof(scopes));
        }

        try
        {
            var accessToken = await _tokenAcquisition.GetAccessTokenForUserAsync(scopes).ConfigureAwait(false);
            _logger.LogInformation("Access token acquired successfully for resource {Resource}.", resource);
            return accessToken;
        }
        catch (MsalUiRequiredException ex)
        {
            _logger.LogError(ex, "Token expired or user interaction required while acquiring access token for resource {Resource}.", resource);
            throw new UnauthorizedAccessException("Token has expired or user re-authentication required.", ex);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "An error occurred while acquiring the access token for resource {Resource}.", resource);
            throw;
        }
    }

    /// <summary>
    /// Gets the access token.
    /// </summary>
    /// <param name="resource"></param>
    /// <returns></returns>
    public async Task<string> GetAccessTokenAsync(Uri resource)
    {
        try
        {
            var scopes = GetRelevantScopes(resource);
            var accessToken = await _tokenAcquisition.GetAccessTokenForUserAsync(scopes).ConfigureAwait(false);
            return accessToken;
        }
        catch (MsalUiRequiredException ex)
        {
            _logger.LogError(ex, "Token expired or user interaction required while acquiring access token for resource {Resource}.", resource);
            throw new UnauthorizedAccessException("Token has expired or user re-authentication required.", ex);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "An error occurred while acquiring the access token for resource {Resource}.", resource);
            throw;
        }
    }

    // Minimum permissions
    private const string MicrosoftGraphScope = "Sites.Selected";
    private const string SharePointOnlineScope = "AllSites.Write";

    private string[] GetRelevantScopes(Uri resourceUri)
    {
        var scopes = new List<string>();

        if (resourceUri.ToString() == "https://graph.microsoft.com")
        {
            scopes.Add($"{resourceUri}/{MicrosoftGraphScope}");
        }
        else
        {
            string resource = $"{resourceUri.Scheme}://{resourceUri.DnsSafeHost}";
            scopes.Add($"{resource}/{SharePointOnlineScope}");
        }

        // Add offline_access scope
        scopes.Add("offline_access");

        return scopes.ToArray();
    }

}
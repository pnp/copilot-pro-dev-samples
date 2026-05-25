using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.HttpOverrides;
using Microsoft.IdentityModel.Tokens;
using Microsoft.Net.Http.Headers;
using ModelContextProtocol.AspNetCore.Authentication;
using System.Net.Http.Headers;
using System.Security.Claims;
using Microsoft.Identity.Web;

// Create the WebApplication builder, which is used to configure services and middleware for the application.
var builder = WebApplication.CreateBuilder(args);

// Read security configuration from appsettings.json with a fallback default of enabled. This allows us to easily toggle security on and off for development and testing purposes without changing the code.
var securityEnabled = builder.Configuration.GetValue<bool?>("Security:Enabled") ?? true;

// Configure authentication and authorization if security is enabled. The server will validate incoming JWT tokens and enforce scope requirements.
if (securityEnabled)
{
    builder.Services.AddMicrosoftIdentityWebApiAuthentication(builder.Configuration);
}

// Load MCP configuration from appsettings.json with fallback defaults for development. In production, these values should be explicitly set in configuration.
var serverUrl = builder.Configuration.GetValue<string>("Mcp:ServerUrl")
    ?? "http://localhost:6200/";
var allowedOrigins = builder.Configuration.GetSection("Mcp:AllowedOrigins").Get<string[]>()
    ?? ["http://localhost:5173"];
var supportedScopes = builder.Configuration.GetSection("Mcp:ScopesSupported").Get<string[]>()
    ?? ["mcp:tools"];
var uniqueUri = builder.Configuration.GetValue<string>("Mcp:UniqueUri")
    ?? $"api://{builder.Configuration["AzureAd:ClientId"]}";
var qualifiedSupportedScopes = supportedScopes
    .Select(scope => $"{uniqueUri.TrimEnd('/')}/{scope.TrimStart('/')}")
    .ToArray();
var authority = $"https://login.microsoftonline.com/{builder.Configuration["AzureAd:TenantId"]!}/v2.0";

// Helper method to build the resource URL dynamically based on the incoming request. This is useful for scenarios where the server might be accessed through different URLs (e.g., localhost during development and a custom domain in production).
static string BuildResourceUrl(HttpRequest request)
{
    var pathBase = request.PathBase.HasValue ? request.PathBase.Value! : "/";
    if (!pathBase.EndsWith('/'))
    {
        pathBase += "/";
    }

    return $"{request.Scheme}://{request.Host}";
}

// Helper method to extract the Bearer token from the Authorization header of incoming requests. This is used for logging purposes to identify the token being presented by the client.
static string? ExtractBearerToken(HttpRequest request)
{
    if (!request.Headers.TryGetValue(HeaderNames.Authorization, out var authorizationHeaderValues))
    {
        return null;
    }

    if (!AuthenticationHeaderValue.TryParse(authorizationHeaderValues, out var headerValue))
    {
        return null;
    }

    if (!string.Equals(headerValue.Scheme, "Bearer", StringComparison.OrdinalIgnoreCase))
    {
        return null;
    }

    return headerValue.Parameter;
}

// Helper method to extract a user-friendly display name from the claims in the authenticated user's principal. It checks common claim types for the user's name and falls back to a default string if none are found.
static string GetDisplayName(ClaimsPrincipal user)
{
    return user.FindFirst("name")?.Value
        ?? user.FindFirst(ClaimTypes.Name)?.Value
        ?? user.FindFirst("preferred_username")?.Value
        ?? "(displayName not found)";
}

// Configure CORS to allow requests from the browser client with the appropriate headers and methods.
builder.Services.AddCors(options =>
{
    options.AddPolicy("McpBrowserClient", policy =>
    {
        policy.WithOrigins(allowedOrigins)
            .WithMethods("POST")
            .WithHeaders(HeaderNames.ContentType, HeaderNames.Authorization, "MCP-Protocol-Version")
            .WithExposedHeaders(HeaderNames.WWWAuthenticate);
    });
});

// Configure authentication and authorization services if security is enabled. The server will validate incoming JWT tokens against the configured Microsoft Entra app and enforce scope requirements for accessing the MCP tools.
if (securityEnabled)
{
    // Configure authentication to validate JWT tokens issued by the configured Microsoft Entra app.
    builder.Services.AddAuthentication()
    .AddMcp(options =>
    {
        // We could use static Resource Metadata if the server is always accessed through the same URL, but using the event allows us to dynamically build the Resource URL based on the incoming request, which is more flexible for different deployment scenarios.
        // options.ResourceMetadata = new()
        // {
        //     ResourceName = "Customers MCP Server",
        //     Resource = serverUrl,
        //     AuthorizationServers = [authority],
        //     ScopesSupported = qualifiedSupportedScopes,
        //     ResourceDocumentation = "https://docs.example.com/api/customers"
        // };

        // Dynamically build the Resource Metadata for each incoming request to support scenarios where the server might be accessed through different URLs (e.g., localhost during development and a custom domain in production).
        options.Events.OnResourceMetadataRequest = context =>
        {
            context.ResourceMetadata = new()
            {
                ResourceName = "Customers MCP Server",
                Resource = BuildResourceUrl(context.HttpContext.Request),
                AuthorizationServers = [authority],
                ScopesSupported = qualifiedSupportedScopes,
                ResourceDocumentation = "https://docs.example.com/api/customers"
            };

            return Task.CompletedTask;
        };
    });

    // Configure an authorization policy that requires the presence of the specified scopes in the incoming JWT token for access to the MCP tools.
    builder.Services.AddAuthorizationBuilder()
      .AddPolicy("mcp_tools_policy", policy =>
        {
            foreach (var scope in supportedScopes)
            {
                policy.RequireClaim("http://schemas.microsoft.com/identity/claims/scope", scope);
            }
        });
}

// Add support for accessing the HttpContext in MCP tools, which can be useful for scenarios where the tool needs to access request-specific information such as headers, user claims, etc.
builder.Services.AddHttpContextAccessor();

// Configure the application to process forwarded headers from the Dev Tunnel proxy. This is necessary for the server to correctly understand the original request information (e.g., scheme, host, client IP) when requests are proxied through the Dev Tunnel.
builder.Services.Configure<ForwardedHeadersOptions>(options =>
{
    // Configure the application to forward the X-Forwarded-For, X-Forwarded-Proto, and X-Forwarded-Host headers
    options.ForwardedHeaders =
        ForwardedHeaders.XForwardedFor |
        ForwardedHeaders.XForwardedProto |
        ForwardedHeaders.XForwardedHost;

    // Dev Tunnel proxy addresses are dynamic, so trust forwarded headers explicitly.
    options.KnownIPNetworks.Clear();
    options.KnownProxies.Clear();
});

// Add the MCP services: the transport to use (http) and the tools to register.
builder.Services
    .AddMcpServer()
    .WithHttpTransport(options =>
    {
        // Stateless mode is recommended for servers that don't need
        // server-to-client requests like sampling or elicitation.
        // See https://csharp.sdk.modelcontextprotocol.io/concepts/transports/transports.html for details.
        options.Stateless = true;
    })
    .WithTools<CustomersTools>();

var app = builder.Build();

// Enable processing of forwarded headers to correctly handle requests coming through the Dev Tunnel proxy.
app.UseForwardedHeaders();

// Configure the HTTP request pipeline to force HTTPS
// app.UseHttpsRedirection();

// Enable CORS
app.UseCors();

// Enable authentication and authorization middleware
if (securityEnabled)
{
    app.UseAuthentication();
    app.UseAuthorization();
}

// Middleware to log incoming requests along with the authenticated user's display name and the Bearer token being presented. This is useful for debugging and monitoring purposes to see who is making requests to the server and with which tokens.
if (securityEnabled)
{
    app.Use(async (context, next) =>
    {
        var token = ExtractBearerToken(context.Request);
        var displayName = context.User?.Identity?.IsAuthenticated == true
            ? GetDisplayName(context.User)
            : "(anonymous)";

        Console.WriteLine($"Request by: {displayName}");
        Console.WriteLine(token is null ? "Bearer token: (none)" : $"Bearer token: {token}");

        await next();
    });
}

// Map the MCP endpoint and apply the CORS policy. If security is enabled, also require authorization with the specified policy to access the MCP tools.
var mcpEndpoint = app.MapMcp().RequireCors("McpBrowserClient");

// If security is enabled, require authorization
if (securityEnabled)
{
    mcpEndpoint.RequireAuthorization("mcp_tools_policy");
}

// Add the server URL to the application configuration. This is used by the MCP tools to identify the Resource URL of the server, which is important for token validation and scope enforcement.
app.Urls.Add(serverUrl);

// Start the application and listen for incoming requests.
app.Run();

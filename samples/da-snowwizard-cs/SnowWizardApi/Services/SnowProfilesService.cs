// Uses the ServiceNow Rest API to deal with profile information

using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace SnowWizardApi.Services;

public class SnowProfilesService
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<SnowProfilesService> _logger;
    private readonly string _snInstance;
    private readonly string _snUsername;
    private readonly string _snPassword;

    public SnowProfilesService(IHttpClientFactory httpClientFactory, ILogger<SnowProfilesService> logger, IConfiguration configuration)
    {
        _httpClientFactory = httpClientFactory;
        _logger = logger;
        _snInstance = configuration["SN_INSTANCE"] ?? "";
        _snUsername = configuration["SN_USERNAME"] ?? "";
        _snPassword = configuration["SN_PASSWORD"] ?? "";
    }

    private string BaseUrl => $"https://{_snInstance}.service-now.com/api/now/table";

    private HttpClient CreateClient()
    {
        var client = _httpClientFactory.CreateClient();
        var credentials = Convert.ToBase64String(Encoding.ASCII.GetBytes($"{_snUsername}:{_snPassword}"));
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Basic", credentials);
        client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
        return client;
    }

    public async Task<List<JsonElement>> GetProfileAsync(string email)
    {
        var client = CreateClient();
        var url = $"{BaseUrl}/sys_user?sysparm_limit=10&sysparm_query=email={email}";

        var response = await client.GetAsync(url);
        response.EnsureSuccessStatusCode();

        var content = await response.Content.ReadAsStringAsync();
        var json = JsonSerializer.Deserialize<JsonElement>(content);
        var result = json.GetProperty("result");

        _logger.LogInformation("Profile fetched successfully from ServiceNow");
        return JsonSerializer.Deserialize<List<JsonElement>>(result.GetRawText()) ?? new List<JsonElement>();
    }
}

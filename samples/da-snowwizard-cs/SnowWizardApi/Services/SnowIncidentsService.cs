// Uses the ServiceNow Rest API to deal with incidents

using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace SnowWizardApi.Services;

public class SnowIncidentsService
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<SnowIncidentsService> _logger;
    private readonly string _snInstance;
    private readonly string _snUsername;
    private readonly string _snPassword;

    public SnowIncidentsService(IHttpClientFactory httpClientFactory, ILogger<SnowIncidentsService> logger, IConfiguration configuration)
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

    public async Task<List<JsonElement>> GetIncidentAsync(string id)
    {
        var client = CreateClient();
        var url = $"{BaseUrl}/incident?sysparm_limit=1&sysparm_fields=number,made_sla,short_description,description,priority,opened_at&sysparm_query=number={id}";

        var response = await client.GetAsync(url);
        response.EnsureSuccessStatusCode();

        var content = await response.Content.ReadAsStringAsync();
        var json = JsonSerializer.Deserialize<JsonElement>(content);
        var result = json.GetProperty("result");

        _logger.LogInformation("Incidents fetched successfully from ServiceNow");
        return JsonSerializer.Deserialize<List<JsonElement>>(result.GetRawText()) ?? new List<JsonElement>();
    }

    public async Task<List<JsonElement>> GetIncidentsAsync()
    {
        var client = CreateClient();
        var url = $"{BaseUrl}/incident?sysparm_limit=10&sysparm_fields=number,made_sla,short_description,description,priority,opened_at&sysparm_query=ORDERBYDESCsys_created_on";

        var response = await client.GetAsync(url);
        response.EnsureSuccessStatusCode();

        var content = await response.Content.ReadAsStringAsync();
        var json = JsonSerializer.Deserialize<JsonElement>(content);
        var result = json.GetProperty("result");

        _logger.LogInformation("Incidents fetched successfully from ServiceNow");
        return JsonSerializer.Deserialize<List<JsonElement>>(result.GetRawText()) ?? new List<JsonElement>();
    }

    public async Task<List<JsonElement>> GetUserIncidentsAsync(string username)
    {
        var sysId = await GetUserSysIdAsync(username);
        var client = CreateClient();
        var url = $"{BaseUrl}/incident?sysparm_limit=10&sysparm_fields=number,made_sla,short_description,description,priority,opened_at&sysparm_query=ORDERBYDESCsys_created_on^assigned_to={sysId}";

        var response = await client.GetAsync(url);
        response.EnsureSuccessStatusCode();

        var content = await response.Content.ReadAsStringAsync();
        var json = JsonSerializer.Deserialize<JsonElement>(content);
        var result = json.GetProperty("result");

        _logger.LogInformation("Incidents fetched successfully from ServiceNow");
        return JsonSerializer.Deserialize<List<JsonElement>>(result.GetRawText()) ?? new List<JsonElement>();
    }

    public async Task<JsonElement> CreateIncidentAsync(string email, string shortDescription, string description)
    {
        var sysId = await GetUserSysIdAsync(email);
        var client = CreateClient();

        var payload = new
        {
            short_description = shortDescription,
            description = description,
            caller_id = sysId
        };

        var jsonContent = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");
        var response = await client.PostAsync($"{BaseUrl}/incident", jsonContent);
        response.EnsureSuccessStatusCode();

        var content = await response.Content.ReadAsStringAsync();
        var json = JsonSerializer.Deserialize<JsonElement>(content);

        _logger.LogInformation("Incident created successfully in ServiceNow");
        return json.GetProperty("result");
    }

    private async Task<string> GetUserSysIdAsync(string username)
    {
        var client = CreateClient();
        var url = $"{BaseUrl}/sys_user?sysparm_limit=10&sysparm_query=email={username}";

        var response = await client.GetAsync(url);
        response.EnsureSuccessStatusCode();

        var content = await response.Content.ReadAsStringAsync();
        var json = JsonSerializer.Deserialize<JsonElement>(content);
        var result = json.GetProperty("result");

        _logger.LogInformation("User fetched successfully from ServiceNow");
        return result[0].GetProperty("sys_id").GetString() ?? "";
    }
}

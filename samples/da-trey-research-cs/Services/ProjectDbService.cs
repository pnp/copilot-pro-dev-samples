using System.Text.Json;
using Azure.Data.Tables;
using TreyResearch.Models;

namespace TreyResearch.Services;

public class ProjectDbService
{
    private static readonly ProjectDbService _instance = new();
    public static ProjectDbService Instance => _instance;

    private const string TableName = "Project";
    private readonly DbService _dbService = new(true);

    public async Task<Project> GetProjectByIdAsync(string id)
    {
        var entity = await _dbService.GetEntityByRowKeyAsync(TableName, id);
        return MapToProject(entity);
    }

    public async Task<List<Project>> GetProjectsAsync()
    {
        var entities = await _dbService.GetEntitiesAsync(TableName);
        return entities.Select(MapToProject).ToList();
    }

    private static Project MapToProject(TableEntity entity)
    {
        var project = new Project
        {
            Id = entity.GetString("id") ?? entity.RowKey ?? "",
            Name = entity.GetString("name") ?? "",
            Description = entity.GetString("description") ?? "",
            ClientName = entity.GetString("clientName") ?? "",
            ClientContact = entity.GetString("clientContact") ?? "",
            ClientEmail = entity.GetString("clientEmail") ?? "",
            Location = DeserializeProperty<Location>(entity, "location") ?? new Location()
        };
        project.MapUrl = GetMapUrl(project);
        return project;
    }

    private static string GetMapUrl(Project project)
    {
        var companyNameKebab = project.ClientName.ToLower().Replace(" ", "-");
        return $"https://microsoft.github.io/copilot-camp/demo-assets/images/maps/{companyNameKebab}.jpg";
    }

    private static T? DeserializeProperty<T>(TableEntity entity, string key)
    {
        var value = entity[key];
        if (value is JsonElement jsonElement)
        {
            return JsonSerializer.Deserialize<T>(jsonElement.GetRawText(), new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
        }
        if (value is string str && !string.IsNullOrEmpty(str))
        {
            return JsonSerializer.Deserialize<T>(str, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
        }
        return default;
    }
}

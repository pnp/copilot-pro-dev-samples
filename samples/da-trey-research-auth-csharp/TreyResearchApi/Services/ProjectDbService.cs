using System.Text.Json;
using TreyResearchApi.Models;

namespace TreyResearchApi.Services;

public class ProjectDbService
{
    private const string TableName = "Project";
    private readonly DbService _dbService = new(true);

    public async Task<Project> GetProjectByIdAsync(string id)
    {
        var entity = await _dbService.GetEntityByRowKeyAsync(TableName, id);
        return ConvertDbProject(entity!);
    }

    public async Task<List<Project>> GetProjectsAsync()
    {
        var entities = await _dbService.GetEntitiesAsync(TableName);
        return entities.Select(ConvertDbProject).ToList();
    }

    private static Project ConvertDbProject(Dictionary<string, object> entity)
    {
        var project = new Project
        {
            Id = ConsultantDbService.GetString(entity, "id"),
            Name = ConsultantDbService.GetString(entity, "name"),
            Description = ConsultantDbService.GetString(entity, "description"),
            ClientName = ConsultantDbService.GetString(entity, "clientName"),
            ClientContact = ConsultantDbService.GetString(entity, "clientContact"),
            ClientEmail = ConsultantDbService.GetString(entity, "clientEmail"),
            Location = ConsultantDbService.GetLocation(entity, "location"),
        };
        project.MapUrl = GetMapUrl(project);
        return project;
    }

    private static string GetMapUrl(Project project)
    {
        var companyNameKebabCase = project.ClientName.ToLowerInvariant().Replace(" ", "-");
        return $"https://microsoft.github.io/copilot-camp/demo-assets/images/maps/{companyNameKebabCase}.jpg";
    }
}

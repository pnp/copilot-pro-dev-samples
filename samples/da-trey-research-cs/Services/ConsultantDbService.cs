using System.Text.Json;
using Azure.Data.Tables;
using TreyResearch.Models;

namespace TreyResearch.Services;

public class ConsultantDbService
{
    private static readonly ConsultantDbService _instance = new();
    public static ConsultantDbService Instance => _instance;

    private const string TableName = "Consultant";
    private readonly DbService _dbService = new(true);

    public async Task<Consultant> GetConsultantByIdAsync(string id)
    {
        var entity = await _dbService.GetEntityByRowKeyAsync(TableName, id);
        return MapToConsultant(entity);
    }

    public async Task<List<Consultant>> GetConsultantsAsync()
    {
        var entities = await _dbService.GetEntitiesAsync(TableName);
        return entities.Select(MapToConsultant).ToList();
    }

    public async Task CreateConsultantAsync(Consultant consultant)
    {
        var properties = new Dictionary<string, object>
        {
            ["id"] = consultant.Id,
            ["name"] = consultant.Name,
            ["email"] = consultant.Email,
            ["phone"] = consultant.Phone,
            ["consultantPhotoUrl"] = consultant.ConsultantPhotoUrl,
            ["location"] = JsonSerializer.Serialize(consultant.Location),
            ["skills"] = JsonSerializer.Serialize(consultant.Skills),
            ["certifications"] = JsonSerializer.Serialize(consultant.Certifications),
            ["roles"] = JsonSerializer.Serialize(consultant.Roles)
        };
        await _dbService.CreateEntityAsync(TableName, consultant.Id, properties);
    }

    private static Consultant MapToConsultant(TableEntity entity)
    {
        return new Consultant
        {
            Id = entity.GetString("id") ?? entity.RowKey ?? "",
            Name = entity.GetString("name") ?? "",
            Email = entity.GetString("email") ?? "",
            Phone = entity.GetString("phone") ?? "",
            ConsultantPhotoUrl = entity.GetString("consultantPhotoUrl") ?? "",
            Location = DeserializeProperty<Location>(entity, "location") ?? new Location(),
            Skills = DeserializeProperty<List<string>>(entity, "skills") ?? new List<string>(),
            Certifications = DeserializeProperty<List<string>>(entity, "certifications") ?? new List<string>(),
            Roles = DeserializeProperty<List<string>>(entity, "roles") ?? new List<string>()
        };
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

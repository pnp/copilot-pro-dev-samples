using System.Text.Json;
using TreyResearchApi.Models;

namespace TreyResearchApi.Services;

public class ConsultantDbService
{
    private const string TableName = "Consultant";
    private readonly DbService _dbService = new(true);

    public async Task<Consultant> GetConsultantByIdAsync(string id)
    {
        var entity = await _dbService.GetEntityByRowKeyAsync(TableName, id);
        return MapToConsultant(entity!);
    }

    public async Task<List<Consultant>> GetConsultantsAsync()
    {
        var entities = await _dbService.GetEntitiesAsync(TableName);
        return entities.Select(MapToConsultant).ToList();
    }

    public async Task<Consultant?> CreateConsultantAsync(Consultant consultant)
    {
        if (string.IsNullOrEmpty(consultant.Id))
        {
            var consultants = await GetConsultantsAsync();
            var maxId = consultants.Any()
                ? consultants.Max(c => int.TryParse(c.Id, out var id) ? id : 0)
                : 0;
            consultant.Id = (maxId + 1).ToString();
        }

        var entity = ConsultantToEntity(consultant);
        await _dbService.CreateEntityAsync(TableName, consultant.Id, entity);

        Console.WriteLine($"Added new consultant {consultant.Name} ({consultant.Id}) to the Consultant table");
        return null;
    }

    private static Consultant MapToConsultant(Dictionary<string, object> entity)
    {
        return new Consultant
        {
            Id = GetString(entity, "id"),
            Name = GetString(entity, "name"),
            Email = GetString(entity, "email"),
            Phone = GetString(entity, "phone"),
            ConsultantPhotoUrl = GetString(entity, "consultantPhotoUrl"),
            Location = GetLocation(entity, "location"),
            Skills = GetStringList(entity, "skills"),
            Certifications = GetStringList(entity, "certifications"),
            Roles = GetStringList(entity, "roles")
        };
    }

    private static Dictionary<string, object> ConsultantToEntity(Consultant c)
    {
        return new Dictionary<string, object>
        {
            ["id"] = c.Id ?? "",
            ["name"] = c.Name,
            ["email"] = c.Email,
            ["phone"] = c.Phone,
            ["consultantPhotoUrl"] = c.ConsultantPhotoUrl,
            ["location"] = c.Location,
            ["skills"] = c.Skills,
            ["certifications"] = c.Certifications,
            ["roles"] = c.Roles
        };
    }

    internal static string GetString(Dictionary<string, object> entity, string key)
    {
        if (entity.TryGetValue(key, out var val))
        {
            if (val is JsonElement je) return je.GetString() ?? "";
            return val?.ToString() ?? "";
        }
        return "";
    }

    internal static Location GetLocation(Dictionary<string, object> entity, string key)
    {
        if (entity.TryGetValue(key, out var val))
        {
            if (val is JsonElement je)
            {
                return JsonSerializer.Deserialize<Location>(je.GetRawText()) ?? new Location();
            }
            if (val is string s)
            {
                return JsonSerializer.Deserialize<Location>(s) ?? new Location();
            }
        }
        return new Location();
    }

    internal static List<string> GetStringList(Dictionary<string, object> entity, string key)
    {
        if (entity.TryGetValue(key, out var val))
        {
            if (val is JsonElement je && je.ValueKind == JsonValueKind.Array)
            {
                return je.EnumerateArray().Select(e => e.GetString() ?? "").ToList();
            }
            if (val is string s)
            {
                try { return JsonSerializer.Deserialize<List<string>>(s) ?? new(); }
                catch { return new(); }
            }
        }
        return new();
    }

    internal static List<HoursEntry> GetHoursEntryList(Dictionary<string, object> entity, string key)
    {
        if (entity.TryGetValue(key, out var val))
        {
            if (val is JsonElement je && je.ValueKind == JsonValueKind.Array)
            {
                return JsonSerializer.Deserialize<List<HoursEntry>>(je.GetRawText()) ?? new();
            }
            if (val is string s)
            {
                try { return JsonSerializer.Deserialize<List<HoursEntry>>(s) ?? new(); }
                catch { return new(); }
            }
        }
        return new();
    }

    internal static bool GetBool(Dictionary<string, object> entity, string key)
    {
        if (entity.TryGetValue(key, out var val))
        {
            if (val is JsonElement je) return je.GetBoolean();
            if (val is bool b) return b;
            if (val is string s) return bool.TryParse(s, out var result) && result;
        }
        return false;
    }

    internal static double GetDouble(Dictionary<string, object> entity, string key)
    {
        if (entity.TryGetValue(key, out var val))
        {
            if (val is JsonElement je) return je.GetDouble();
            if (val is double d) return d;
            if (val is int i) return i;
            if (val is long l) return l;
            if (val is string s) return double.TryParse(s, out var result) ? result : 0;
        }
        return 0;
    }
}

using System.Text.Json;
using Azure.Data.Tables;
using TreyResearch.Models;

namespace TreyResearch.Services;

public class AssignmentDbService
{
    private static readonly AssignmentDbService _instance = new();
    public static AssignmentDbService Instance => _instance;

    private const string TableName = "Assignment";
    private readonly DbService _dbService = new(false);

    public async Task<List<Assignment>> GetAssignmentsAsync()
    {
        var entities = await _dbService.GetEntitiesAsync(TableName);
        return entities.Select(MapToAssignment).ToList();
    }

    public async Task<double> ChargeHoursToProjectAsync(string projectId, string consultantId, int month, int year, double hours)
    {
        try
        {
            var rowKey = $"{projectId},{consultantId}";
            var entity = await _dbService.GetEntityByRowKeyAsync(TableName, rowKey);

            var delivered = DeserializeProperty<List<HoursEntry>>(entity, "delivered") ?? new List<HoursEntry>();
            var forecast = DeserializeProperty<List<HoursEntry>>(entity, "forecast") ?? new List<HoursEntry>();

            // Add hours delivered
            var deliveredEntry = delivered.FirstOrDefault(d => d.Month == month && d.Year == year);
            if (deliveredEntry != null)
            {
                deliveredEntry.Hours += hours;
            }
            else
            {
                delivered.Add(new HoursEntry { Month = month, Year = year, Hours = hours });
            }
            delivered.Sort((a, b) => a.Year != b.Year ? a.Year.CompareTo(b.Year) : a.Month.CompareTo(b.Month));

            // Subtract from forecast
            double remainingForecast = -hours;
            var forecastEntry = forecast.FirstOrDefault(f => f.Month == month && f.Year == year);
            if (forecastEntry != null)
            {
                forecastEntry.Hours -= hours;
                remainingForecast = forecastEntry.Hours;
            }
            else
            {
                forecast.Add(new HoursEntry { Month = month, Year = year, Hours = -hours });
            }
            forecast.Sort((a, b) => a.Year != b.Year ? a.Year.CompareTo(b.Year) : a.Month.CompareTo(b.Month));

            entity["delivered"] = JsonSerializer.Serialize(delivered);
            entity["forecast"] = JsonSerializer.Serialize(forecast);

            await _dbService.UpdateEntityAsync(TableName, entity);
            return remainingForecast;
        }
        catch
        {
            throw new HttpError(404, "Assignment not found");
        }
    }

    public async Task<double> AddConsultantToProjectAsync(string projectId, string consultantId, string role, double hours)
    {
        var month = DateTime.Now.Month;
        var year = DateTime.Now.Year;
        var rowKey = $"{projectId},{consultantId}";

        try
        {
            await _dbService.GetEntityByRowKeyAsync(TableName, rowKey);
            throw new HttpError(403, "Assignment already exists");
        }
        catch (HttpError ex) when (ex.Status == 404)
        {
            // Expected - assignment doesn't exist yet
        }

        try
        {
            var properties = new Dictionary<string, object>
            {
                ["id"] = rowKey,
                ["projectId"] = projectId,
                ["consultantId"] = consultantId,
                ["role"] = role,
                ["billable"] = true,
                ["rate"] = 100.0,
                ["forecast"] = JsonSerializer.Serialize(new List<HoursEntry> { new() { Month = month, Year = year, Hours = hours } }),
                ["delivered"] = JsonSerializer.Serialize(new List<HoursEntry>())
            };

            await _dbService.CreateEntityAsync(TableName, rowKey, properties);
            return hours;
        }
        catch
        {
            throw new HttpError(500, "Unable to add assignment");
        }
    }

    private static Assignment MapToAssignment(TableEntity entity)
    {
        return new Assignment
        {
            Id = entity.GetString("id") ?? entity.RowKey ?? "",
            ProjectId = entity.GetString("projectId") ?? "",
            ConsultantId = entity.GetString("consultantId") ?? "",
            Role = entity.GetString("role") ?? "",
            Billable = entity.GetBoolean("billable") ?? true,
            Rate = entity.GetDouble("rate") ?? 100,
            Forecast = DeserializeProperty<List<HoursEntry>>(entity, "forecast") ?? new List<HoursEntry>(),
            Delivered = DeserializeProperty<List<HoursEntry>>(entity, "delivered") ?? new List<HoursEntry>()
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

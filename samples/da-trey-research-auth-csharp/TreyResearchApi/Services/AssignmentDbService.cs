using System.Text.Json;
using TreyResearchApi.Models;

namespace TreyResearchApi.Services;

public class AssignmentDbService
{
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
            var entity = await _dbService.GetEntityByRowKeyAsync(TableName, $"{projectId},{consultantId}");
            if (entity == null)
            {
                throw new HttpError(404, "Assignment not found");
            }

            var delivered = ConsultantDbService.GetHoursEntryList(entity, "delivered");
            var forecast = ConsultantDbService.GetHoursEntryList(entity, "forecast");

            // Add hours delivered
            var existingDelivered = delivered.FirstOrDefault(d => d.Month == month && d.Year == year);
            if (existingDelivered != null)
            {
                existingDelivered.Hours += hours;
            }
            else
            {
                delivered.Add(new HoursEntry { Month = month, Year = year, Hours = hours });
            }
            delivered.Sort((a, b) => a.Year != b.Year ? a.Year.CompareTo(b.Year) : a.Month.CompareTo(b.Month));

            // Subtract hours from forecast
            double remainingForecast = -hours;
            var existingForecast = forecast.FirstOrDefault(f => f.Month == month && f.Year == year);
            if (existingForecast != null)
            {
                existingForecast.Hours -= hours;
                remainingForecast = existingForecast.Hours;
            }
            else
            {
                forecast.Add(new HoursEntry { Month = month, Year = year, Hours = -hours });
            }
            forecast.Sort((a, b) => a.Year != b.Year ? a.Year.CompareTo(b.Year) : a.Month.CompareTo(b.Month));

            entity["delivered"] = delivered;
            entity["forecast"] = forecast;

            await _dbService.UpdateEntityAsync(TableName, entity);
            return remainingForecast;
        }
        catch (HttpError)
        {
            throw;
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

        try
        {
            var existing = await _dbService.GetEntityByRowKeyAsync(TableName, $"{projectId},{consultantId}");
            if (existing != null)
            {
                throw new HttpError(403, "Assignment already exists");
            }
        }
        catch (HttpError ex) when (ex.Status == 403)
        {
            throw;
        }
        catch
        {
            // Entity not found - this is expected, continue
        }

        try
        {
            var newEntity = new Dictionary<string, object>
            {
                ["id"] = $"{projectId},{consultantId}",
                ["projectId"] = projectId,
                ["consultantId"] = consultantId,
                ["role"] = role,
                ["billable"] = true,
                ["rate"] = 100.0,
                ["forecast"] = new List<HoursEntry> { new() { Month = month, Year = year, Hours = hours } },
                ["delivered"] = new List<HoursEntry>()
            };

            await _dbService.CreateEntityAsync(TableName, $"{projectId},{consultantId}", newEntity);
            return hours;
        }
        catch (HttpError)
        {
            throw;
        }
        catch
        {
            throw new HttpError(500, "Unable to add assignment");
        }
    }

    private static Assignment MapToAssignment(Dictionary<string, object> entity)
    {
        return new Assignment
        {
            Id = ConsultantDbService.GetString(entity, "id"),
            ProjectId = ConsultantDbService.GetString(entity, "projectId"),
            ConsultantId = ConsultantDbService.GetString(entity, "consultantId"),
            Role = ConsultantDbService.GetString(entity, "role"),
            Billable = ConsultantDbService.GetBool(entity, "billable"),
            Rate = ConsultantDbService.GetDouble(entity, "rate"),
            Forecast = ConsultantDbService.GetHoursEntryList(entity, "forecast"),
            Delivered = ConsultantDbService.GetHoursEntryList(entity, "delivered")
        };
    }
}

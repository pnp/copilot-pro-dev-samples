using TreyResearchApi.Models;

namespace TreyResearchApi.Services;

public class ConsultantApiService
{
    private const int AvailableHoursPerMonth = 160;

    private readonly ConsultantDbService _consultantDb = new();
    private readonly ProjectDbService _projectDb = new();
    private readonly AssignmentDbService _assignmentDb = new();

    public async Task<ApiConsultant?> GetApiConsultantByIdAsync(string consultantId)
    {
        var consultant = await _consultantDb.GetConsultantByIdAsync(consultantId);
        if (consultant == null) return null;

        var assignments = await _assignmentDb.GetAssignmentsAsync();
        return await GetApiConsultantForBaseConsultantAsync(consultant, assignments);
    }

    public async Task<ApiConsultant?> GetApiConsultantByEmailAsync(string email)
    {
        var consultants = await _consultantDb.GetConsultantsAsync();
        var consultant = consultants.FirstOrDefault(c =>
            c.Email.Equals(email, StringComparison.OrdinalIgnoreCase));

        if (consultant == null) return null;

        var assignments = await _assignmentDb.GetAssignmentsAsync();
        return await GetApiConsultantForBaseConsultantAsync(consultant, assignments);
    }

    public async Task<List<ApiConsultant>> GetApiConsultantsAsync(
        string consultantName, string projectName, string skill,
        string certification, string role, string hoursAvailable)
    {
        var consultants = await _consultantDb.GetConsultantsAsync();
        var assignments = await _assignmentDb.GetAssignmentsAsync();

        // Filter on base properties
        if (!string.IsNullOrEmpty(consultantName))
        {
            consultants = consultants.Where(c =>
                c.Name.Contains(consultantName, StringComparison.OrdinalIgnoreCase)).ToList();
        }
        if (!string.IsNullOrEmpty(skill))
        {
            consultants = consultants.Where(c =>
                c.Skills.Any(s => s.Contains(skill, StringComparison.OrdinalIgnoreCase))).ToList();
        }
        if (!string.IsNullOrEmpty(certification))
        {
            consultants = consultants.Where(c =>
                c.Certifications.Any(s => s.Contains(certification, StringComparison.OrdinalIgnoreCase))).ToList();
        }
        if (!string.IsNullOrEmpty(role))
        {
            consultants = consultants.Where(c =>
                c.Roles.Any(s => s.Contains(role, StringComparison.OrdinalIgnoreCase))).ToList();
        }

        // Augment with assignment info
        var result = new List<ApiConsultant>();
        foreach (var c in consultants)
        {
            result.Add(await GetApiConsultantForBaseConsultantAsync(c, assignments));
        }

        // Filter on project name
        if (!string.IsNullOrEmpty(projectName))
        {
            result = result.Where(c =>
                c.Projects.Any(p =>
                    (p.ProjectName.ToLowerInvariant() + p.ClientName.ToLowerInvariant())
                        .Contains(projectName.ToLowerInvariant()))).ToList();
        }

        // Filter on available hours
        if (!string.IsNullOrEmpty(hoursAvailable) && int.TryParse(hoursAvailable, out var minHours))
        {
            result = result.Where(c =>
            {
                var available = AvailableHoursPerMonth * 2 - c.ForecastThisMonth - c.ForecastNextMonth;
                return available >= minHours;
            }).ToList();
        }

        return result;
    }

    public async Task<ApiConsultant?> CreateApiConsultantAsync(Consultant consultant)
    {
        await _consultantDb.CreateConsultantAsync(consultant);
        var assignments = await _assignmentDb.GetAssignmentsAsync();
        return await GetApiConsultantForBaseConsultantAsync(consultant, assignments);
    }

    public async Task<ApiConsultant> GetApiConsultantForBaseConsultantAsync(Consultant consultant, List<Assignment> assignments)
    {
        var result = new ApiConsultant
        {
            Id = consultant.Id,
            Name = consultant.Name,
            Email = consultant.Email,
            Phone = consultant.Phone,
            ConsultantPhotoUrl = consultant.ConsultantPhotoUrl,
            Location = consultant.Location,
            Skills = consultant.Skills,
            Certifications = consultant.Certifications,
            Roles = consultant.Roles,
            Projects = new(),
            ForecastThisMonth = 0,
            ForecastNextMonth = 0,
            DeliveredLastMonth = 0,
            DeliveredThisMonth = 0
        };

        var consultantAssignments = assignments.Where(a => a.ConsultantId == consultant.Id).ToList();

        foreach (var assignment in consultantAssignments)
        {
            var project = await _projectDb.GetProjectByIdAsync(assignment.ProjectId);
            var (forecastLastMonth, forecastThisMonth, forecastNextMonth) = FindHours(assignment.Forecast);
            var (deliveredLastMonth, deliveredThisMonth, deliveredNextMonth) = FindHours(assignment.Delivered);

            result.Projects.Add(new ApiConsultantAssignment
            {
                ProjectName = project.Name,
                ProjectDescription = project.Description,
                ProjectLocation = project.Location,
                ClientName = project.ClientName,
                ClientContact = project.ClientContact,
                ClientEmail = project.ClientEmail,
                Role = assignment.Role,
                ForecastThisMonth = forecastThisMonth,
                ForecastNextMonth = forecastNextMonth,
                DeliveredLastMonth = deliveredLastMonth,
                DeliveredThisMonth = deliveredThisMonth
            });

            result.ForecastThisMonth += forecastThisMonth;
            result.ForecastNextMonth += forecastNextMonth;
            result.DeliveredLastMonth += deliveredLastMonth;
            result.DeliveredThisMonth += deliveredThisMonth;
        }

        return result;
    }

    public async Task<ApiChargeTimeResponse> ChargeTimeToProjectAsync(string projectName, string consultantId, double hours)
    {
        var projectApiService = new ProjectApiService();
        var projects = await projectApiService.GetApiProjectsAsync(projectName, "");

        if (projects.Count == 0)
        {
            throw new HttpError(404, $"Project not found: {projectName}");
        }
        if (projects.Count > 1)
        {
            throw new HttpError(406, $"Multiple projects found with the name: {projectName}");
        }

        var project = projects[0];
        var month = DateTime.Now.Month;
        var year = DateTime.Now.Year;
        var remainingForecast = await _assignmentDb.ChargeHoursToProjectAsync(project.Id, consultantId, month, year, hours);

        string message;
        if (remainingForecast < 0)
        {
            message = $"Charged {hours} hours to {project.ClientName} on project \"{project.Name}\". You are {-remainingForecast} hours over your forecast this month.";
        }
        else
        {
            message = $"Charged {hours} hours to {project.ClientName} on project \"{project.Name}\". You have {remainingForecast} hours remaining this month.";
        }

        return new ApiChargeTimeResponse
        {
            ClientName = project.ClientName,
            ProjectName = project.Name,
            RemainingForecast = remainingForecast,
            Message = message
        };
    }

    internal static (double lastMonth, double thisMonth, double nextMonth) FindHours(List<HoursEntry> hours)
    {
        var now = DateTime.Now;
        var thisMonth = now.Month;
        var thisYear = now.Year;

        var lastMonth = thisMonth == 1 ? 12 : thisMonth - 1;
        var lastYear = thisMonth == 1 ? thisYear - 1 : thisYear;

        var nextMonth = thisMonth == 12 ? 1 : thisMonth + 1;
        var nextYear = thisMonth == 12 ? thisYear + 1 : thisYear;

        var lastMonthHours = hours.FirstOrDefault(h => h.Month == lastMonth && h.Year == lastYear)?.Hours ?? 0;
        var thisMonthHours = hours.FirstOrDefault(h => h.Month == thisMonth && h.Year == thisYear)?.Hours ?? 0;
        var nextMonthHours = hours.FirstOrDefault(h => h.Month == nextMonth && h.Year == nextYear)?.Hours ?? 0;

        return (lastMonthHours, thisMonthHours, nextMonthHours);
    }
}

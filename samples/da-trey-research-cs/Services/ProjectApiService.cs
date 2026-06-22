using TreyResearch.Models;

namespace TreyResearch.Services;

public class ProjectApiService
{
    private static readonly ProjectApiService _instance = new();
    public static ProjectApiService Instance => _instance;

    public async Task<ApiProject> GetApiProjectByIdAsync(string projectId)
    {
        var project = await ProjectDbService.Instance.GetProjectByIdAsync(projectId);
        var assignments = await AssignmentDbService.Instance.GetAssignmentsAsync();
        return await GetApiProjectAsync(project, assignments);
    }

    public async Task<List<ApiProject>> GetApiProjectsAsync(string projectOrClientName, string consultantName)
    {
        var projects = await ProjectDbService.Instance.GetProjectsAsync();
        var assignments = await AssignmentDbService.Instance.GetAssignmentsAsync();

        // Filter on base properties
        if (!string.IsNullOrEmpty(projectOrClientName))
        {
            projects = projects.Where(p =>
                p.Name.Contains(projectOrClientName, StringComparison.OrdinalIgnoreCase) ||
                p.ClientName.Contains(projectOrClientName, StringComparison.OrdinalIgnoreCase)
            ).ToList();
        }

        // Remove duplicates
        projects = projects.DistinctBy(p => p.Id).ToList();

        // Augment with assignment information
        var result = new List<ApiProject>();
        foreach (var p in projects)
        {
            result.Add(await GetApiProjectAsync(p, assignments));
        }

        // Filter on consultant name
        if (!string.IsNullOrEmpty(consultantName))
        {
            result = result.Where(p =>
                p.Consultants.Any(c => c.ConsultantName.Contains(consultantName, StringComparison.OrdinalIgnoreCase))
            ).ToList();
        }

        return result;
    }

    private async Task<ApiProject> GetApiProjectAsync(Project project, List<Assignment> assignments)
    {
        var result = new ApiProject
        {
            Id = project.Id,
            Name = project.Name,
            Description = project.Description,
            ClientName = project.ClientName,
            ClientContact = project.ClientContact,
            ClientEmail = project.ClientEmail,
            Location = project.Location,
            MapUrl = project.MapUrl
        };

        var projectAssignments = assignments.Where(a => a.ProjectId == project.Id).ToList();

        foreach (var assignment in projectAssignments)
        {
            var consultant = await ConsultantDbService.Instance.GetConsultantByIdAsync(assignment.ConsultantId);
            var (forecastLastMonth, forecastThisMonth, forecastNextMonth) = FindHours(assignment.Forecast);
            var (deliveredLastMonth, deliveredThisMonth, deliveredNextMonth) = FindHours(assignment.Delivered);

            result.Consultants.Add(new ApiProjectAssignment
            {
                ConsultantName = consultant.Name,
                ConsultantLocation = consultant.Location,
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

    private static (double lastMonth, double thisMonth, double nextMonth) FindHours(List<HoursEntry> hours)
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

    public async Task<ApiAddConsultantToProjectResponse> AddConsultantToProjectAsync(
        string projectName, string consultantName, string role, double hours)
    {
        var projects = await GetApiProjectsAsync(projectName, "");
        var consultants = await ConsultantApiService.Instance.GetApiConsultantsAsync(consultantName, "", "", "", "", "");

        if (projects.Count == 0)
            throw new HttpError(404, $"Project not found: {projectName}");
        if (projects.Count > 1)
            throw new HttpError(406, $"Multiple projects found with the name: {projectName}");
        if (consultants.Count == 0)
            throw new HttpError(404, $"Consultant not found: {consultantName}");
        if (consultants.Count > 1)
            throw new HttpError(406, $"Multiple consultants found with the name: {consultantName}");

        var project = projects[0];
        var consultant = consultants[0];

        var remainingForecast = await AssignmentDbService.Instance.AddConsultantToProjectAsync(
            project.Id, consultant.Id, role, hours);

        var message = $"Added consultant {consultant.Name} to {project.ClientName} on project \"{project.Name}\" with {remainingForecast} hours forecast this month.";

        return new ApiAddConsultantToProjectResponse
        {
            ClientName = project.ClientName,
            ProjectName = project.Name,
            ConsultantName = consultant.Name,
            RemainingForecast = remainingForecast,
            Message = message
        };
    }
}

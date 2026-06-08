using TreyResearchApi.Models;

namespace TreyResearchApi.Services;

public class ProjectApiService
{
    private readonly ProjectDbService _projectDb = new();
    private readonly AssignmentDbService _assignmentDb = new();
    private readonly ConsultantDbService _consultantDb = new();

    public async Task<ApiProject?> GetApiProjectByIdAsync(string projectId)
    {
        var project = await _projectDb.GetProjectByIdAsync(projectId);
        var assignments = await _assignmentDb.GetAssignmentsAsync();
        return await GetApiProjectAsync(project, assignments);
    }

    public async Task<List<ApiProject>> GetApiProjectsAsync(string projectOrClientName, string consultantName)
    {
        var projects = await _projectDb.GetProjectsAsync();
        var assignments = await _assignmentDb.GetAssignmentsAsync();

        // Filter on base properties
        if (!string.IsNullOrEmpty(projectOrClientName))
        {
            projects = projects.Where(p =>
                (p.Name?.ToLowerInvariant().Contains(projectOrClientName.ToLowerInvariant()) ?? false) ||
                (p.ClientName?.ToLowerInvariant().Contains(projectOrClientName.ToLowerInvariant()) ?? false)
            ).ToList();
        }

        // Remove duplicates
        projects = projects.DistinctBy(p => p.Id).ToList();

        // Augment with assignment info
        var result = new List<ApiProject>();
        foreach (var p in projects)
        {
            result.Add(await GetApiProjectAsync(p, assignments));
        }

        // Filter on consultant name
        if (!string.IsNullOrEmpty(consultantName))
        {
            result = result.Where(p =>
                p.Consultants.Any(c =>
                    c.ConsultantName.Contains(consultantName, StringComparison.OrdinalIgnoreCase))
            ).ToList();
        }

        return result;
    }

    public async Task<ApiAddConsultantToProjectResponse> AddConsultantToProjectAsync(
        string projectName, string consultantName, string role, double hours)
    {
        var projects = await GetApiProjectsAsync(projectName, "");
        var consultantApiService = new ConsultantApiService();
        var consultants = await consultantApiService.GetApiConsultantsAsync(consultantName, "", "", "", "", "");

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

        var remainingForecast = await _assignmentDb.AddConsultantToProjectAsync(
            project.Id, consultant.Id!, role, hours);

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
            MapUrl = project.MapUrl,
            Consultants = new(),
            ForecastThisMonth = 0,
            ForecastNextMonth = 0,
            DeliveredLastMonth = 0,
            DeliveredThisMonth = 0
        };

        var projectAssignments = assignments.Where(a => a.ProjectId == project.Id).ToList();

        foreach (var assignment in projectAssignments)
        {
            var consultant = await _consultantDb.GetConsultantByIdAsync(assignment.ConsultantId);
            var (forecastLastMonth, forecastThisMonth, forecastNextMonth) = ConsultantApiService.FindHours(assignment.Forecast);
            var (deliveredLastMonth, deliveredThisMonth, deliveredNextMonth) = ConsultantApiService.FindHours(assignment.Delivered);

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
}

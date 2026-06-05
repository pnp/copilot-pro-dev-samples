using System.Text.Json;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using TreyResearch.Models;
using TreyResearch.Services;

namespace TreyResearch.Functions;

public class ProjectsFunction
{
    private readonly ILogger<ProjectsFunction> _logger;

    public ProjectsFunction(ILogger<ProjectsFunction> logger)
    {
        _logger = logger;
    }

    [Function("projects")]
    public async Task<HttpResponseData> Run(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get", "post", Route = "projects/{id?}")] HttpRequestData req,
        string? id)
    {
        _logger.LogInformation("HTTP trigger function projects processed a request.");

        try
        {
            var userInfo = await IdentityService.Instance.ValidateRequestAsync();

            switch (req.Method.ToUpper())
            {
                case "GET":
                {
                    var projectName = GetQueryParam(req, "projectName");
                    var consultantName = GetQueryParam(req, "consultantName");

                    Console.WriteLine($"➡️ GET /api/projects: request for projectName={projectName}, consultantName={consultantName}, id={id}");

                    projectName = Utilities.CleanUpParameter("projectName", projectName);
                    consultantName = Utilities.CleanUpParameter("consultantName", consultantName);

                    if (!string.IsNullOrEmpty(id))
                    {
                        var project = await ProjectApiService.Instance.GetApiProjectByIdAsync(id.ToLower());
                        Console.WriteLine("   ✅ GET /api/projects: 1 project returned");
                        return await CreateResponse(req, 200, new { results = new[] { project } });
                    }

                    // Use current user if the project name is user_profile
                    if (projectName.Contains("user_profile"))
                    {
                        var result = await ProjectApiService.Instance.GetApiProjectsAsync("", userInfo.Name);
                        Console.WriteLine($"   ✅ GET /api/projects for current user; {result.Count} projects returned");
                        return await CreateResponse(req, 200, new { results = result });
                    }

                    var projects = await ProjectApiService.Instance.GetApiProjectsAsync(projectName, consultantName);
                    Console.WriteLine($"   ✅ GET /api/projects: {projects.Count} projects returned");
                    return await CreateResponse(req, 200, new { results = projects });
                }
                case "POST":
                {
                    switch (id?.ToLower())
                    {
                        case "assignconsultant":
                        {
                            var body = await ReadBodyAsync(req);
                            if (body == null)
                            {
                                throw new HttpError(400, "No body to process this request.");
                            }

                            var projectName = Utilities.CleanUpParameter("projectName",
                                GetJsonProperty(body.Value, "projectName"));
                            if (string.IsNullOrEmpty(projectName))
                            {
                                throw new HttpError(400, "Missing project name");
                            }

                            var consultantName = Utilities.CleanUpParameter("consultantName",
                                GetJsonProperty(body.Value, "consultantName"));
                            if (string.IsNullOrEmpty(consultantName))
                            {
                                throw new HttpError(400, "Missing consultant name");
                            }

                            var role = Utilities.CleanUpParameter("Role",
                                GetJsonProperty(body.Value, "role"));
                            if (string.IsNullOrEmpty(role))
                            {
                                throw new HttpError(400, "Missing role");
                            }

                            var forecastStr = GetJsonProperty(body.Value, "forecast");
                            double forecast = 0;
                            if (!string.IsNullOrEmpty(forecastStr))
                            {
                                double.TryParse(forecastStr, out forecast);
                            }

                            Console.WriteLine($"➡️ POST /api/projects: assignconsultant request, projectName={projectName}, consultantName={consultantName}, role={role}, forecast={forecast}");
                            var result = await ProjectApiService.Instance.AddConsultantToProjectAsync(
                                projectName, consultantName, role, forecast);

                            Console.WriteLine($"   ✅ POST /api/projects: {result.Message}");
                            return await CreateResponse(req, 200, new
                            {
                                results = new
                                {
                                    status = 200,
                                    clientName = result.ClientName,
                                    projectName = result.ProjectName,
                                    consultantName = result.ConsultantName,
                                    remainingForecast = result.RemainingForecast,
                                    message = result.Message
                                }
                            });
                        }
                        default:
                            throw new HttpError(400, $"Invalid command: {id}");
                    }
                }
                default:
                    throw new HttpError(405, $"Method not allowed: {req.Method}");
            }
        }
        catch (HttpError ex)
        {
            Console.WriteLine($"   ⛔ Returning error status code {ex.Status}: {ex.Message}");
            return await CreateResponse(req, ex.Status, new { results = new ErrorResult { Status = ex.Status, Message = ex.Message } });
        }
        catch (Exception ex)
        {
            Console.WriteLine($"   ⛔ Returning error status code 500: {ex.Message}");
            return await CreateResponse(req, 500, new { results = new ErrorResult { Status = 500, Message = ex.Message } });
        }
    }

    private static string GetQueryParam(HttpRequestData req, string name)
    {
        var query = System.Web.HttpUtility.ParseQueryString(req.Url.Query);
        return query[name]?.ToLower() ?? "";
    }

    private static async Task<JsonElement?> ReadBodyAsync(HttpRequestData req)
    {
        try
        {
            var bodyStr = await new StreamReader(req.Body).ReadToEndAsync();
            if (string.IsNullOrWhiteSpace(bodyStr)) return null;
            return JsonSerializer.Deserialize<JsonElement>(bodyStr);
        }
        catch
        {
            return null;
        }
    }

    private static string GetJsonProperty(JsonElement element, string propertyName)
    {
        if (element.TryGetProperty(propertyName, out var prop))
        {
            return prop.ValueKind == JsonValueKind.Number ? prop.GetRawText() : prop.GetString() ?? "";
        }
        return "";
    }

    private static async Task<HttpResponseData> CreateResponse(HttpRequestData req, int statusCode, object body)
    {
        var response = req.CreateResponse((System.Net.HttpStatusCode)statusCode);
        response.Headers.Add("Content-Type", "application/json");
        await response.WriteStringAsync(JsonSerializer.Serialize(body, new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        }));
        return response;
    }
}

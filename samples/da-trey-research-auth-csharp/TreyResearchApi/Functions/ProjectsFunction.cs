using System.Net;
using System.Text.Json;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using TreyResearchApi.Middleware;
using TreyResearchApi.Models;
using TreyResearchApi.Services;

namespace TreyResearchApi.Functions;

public class ProjectsFunction
{
    private readonly ILogger _logger;

    public ProjectsFunction(ILoggerFactory loggerFactory)
    {
        _logger = loggerFactory.CreateLogger<ProjectsFunction>();
    }

    [Function("projects")]
    public async Task<HttpResponseData> RunAsync(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get", "post", Route = "projects/{id?}")] HttpRequestData req,
        string? id)
    {
        _logger.LogInformation("HTTP trigger function projects processed a request.");

        // Auth validation
        var token = AuthMiddleware.GetToken(req);
        if (token == null)
        {
            return AuthMiddleware.CreateErrorResponse(req, HttpStatusCode.Unauthorized, "Unauthorized", "Authentication token is required");
        }

        var userInfo = await AuthMiddleware.ValidateTokenAsync(token);
        if (userInfo == null)
        {
            return AuthMiddleware.CreateErrorResponse(req, HttpStatusCode.Unauthorized, "Unauthorized", "Invalid or expired authentication token");
        }

        var consultant = await AuthMiddleware.EnsureConsultantAsync(userInfo);
        userInfo.Id = consultant?.Id ?? userInfo.Id;

        try
        {
            var projectApi = new ProjectApiService();

            switch (req.Method.ToUpperInvariant())
            {
                case "GET":
                {
                    var projectName = req.Query["projectName"]?.ToLowerInvariant() ?? "";
                    var consultantName = req.Query["consultantName"]?.ToLowerInvariant() ?? "";

                    Console.WriteLine($"➡️ GET /api/projects: request for projectName={projectName}, consultantName={consultantName}, id={id}");

                    projectName = Utilities.CleanUpParameter("projectName", projectName);
                    consultantName = Utilities.CleanUpParameter("consultantName", consultantName);

                    if (!string.IsNullOrEmpty(id))
                    {
                        var result = await projectApi.GetApiProjectByIdAsync(id.ToLowerInvariant());
                        var response = req.CreateResponse(HttpStatusCode.OK);
                        AuthMiddleware.AddCorsHeaders(response);
                        await response.WriteAsJsonAsync(new { results = new[] { result } });
                        Console.WriteLine($"   ✅ GET /api/projects: response status 200; 1 project returned");
                        return response;
                    }

                    // Use current user if project name contains user_profile
                    if (projectName.Contains("user_profile"))
                    {
                        var currentUserName = userInfo.Name ?? "Unknown User";
                        var results = await projectApi.GetApiProjectsAsync("", currentUserName);
                        var response = req.CreateResponse(HttpStatusCode.OK);
                        AuthMiddleware.AddCorsHeaders(response);
                        await response.WriteAsJsonAsync(new { results });
                        Console.WriteLine($"   ✅ GET /api/projects for current user response status 200; {results.Count} projects returned");
                        return response;
                    }

                    {
                        var results = await projectApi.GetApiProjectsAsync(projectName, consultantName);
                        var response = req.CreateResponse(HttpStatusCode.OK);
                        AuthMiddleware.AddCorsHeaders(response);
                        await response.WriteAsJsonAsync(new { results });
                        Console.WriteLine($"   ✅ GET /api/projects: response status 200; {results.Count} projects returned");
                        return response;
                    }
                }
                case "POST":
                {
                    switch (id?.ToLowerInvariant())
                    {
                        case "assignconsultant":
                        {
                            var bodyStr = await new StreamReader(req.Body).ReadToEndAsync();
                            if (string.IsNullOrEmpty(bodyStr))
                            {
                                throw new HttpError(400, "No body to process this request.");
                            }

                            var body = JsonSerializer.Deserialize<JsonElement>(bodyStr);

                            var projectName = body.TryGetProperty("projectName", out var pn) ? pn.GetString() ?? "" : "";
                            projectName = Utilities.CleanUpParameter("projectName", projectName);
                            if (string.IsNullOrEmpty(projectName))
                            {
                                throw new HttpError(400, "Missing project name");
                            }

                            var consultantName = body.TryGetProperty("consultantName", out var cn) ? cn.GetString() ?? "" : "";
                            consultantName = Utilities.CleanUpParameter("consultantName", consultantName);
                            if (string.IsNullOrEmpty(consultantName))
                            {
                                throw new HttpError(400, "Missing consultant name");
                            }

                            var role = body.TryGetProperty("role", out var r) ? r.GetString() ?? "" : "";
                            role = Utilities.CleanUpParameter("Role", role);
                            if (string.IsNullOrEmpty(role))
                            {
                                throw new HttpError(400, "Missing role");
                            }

                            var forecast = body.TryGetProperty("forecast", out var f) ? f.GetDouble() : 0;

                            Console.WriteLine($"➡️ POST /api/projects: assignconsultant request, projectName={projectName}, consultantName={consultantName}, role={role}, forecast={forecast}");
                            var result = await projectApi.AddConsultantToProjectAsync(projectName, consultantName, role, forecast);

                            var response = req.CreateResponse(HttpStatusCode.OK);
                            AuthMiddleware.AddCorsHeaders(response);
                            await response.WriteAsJsonAsync(new
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
                            Console.WriteLine($"   ✅ POST /api/projects: response status 200 - {result.Message}");
                            return response;
                        }
                        default:
                            throw new HttpError(400, $"Invalid command: {id}");
                    }
                }
                default:
                    throw new HttpError(405, $"Method not allowed: {req.Method}");
            }
        }
        catch (Exception error)
        {
            var status = error is HttpError he ? he.Status : 500;
            Console.WriteLine($"   ⛔ Returning error status code {status}: {error.Message}");

            var resp = req.CreateResponse((HttpStatusCode)status);
            AuthMiddleware.AddCorsHeaders(resp);
            await resp.WriteAsJsonAsync(new { results = new ErrorResult { Status = status, Message = error.Message } });
            return resp;
        }
    }
}

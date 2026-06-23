using System.Net;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using TreyResearchApi.Middleware;
using TreyResearchApi.Models;
using TreyResearchApi.Services;

namespace TreyResearchApi.Functions;

public class ConsultantsFunction
{
    private readonly ILogger _logger;

    public ConsultantsFunction(ILoggerFactory loggerFactory)
    {
        _logger = loggerFactory.CreateLogger<ConsultantsFunction>();
    }

    [Function("consultants")]
    public async Task<HttpResponseData> RunAsync(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "consultants/{id?}")] HttpRequestData req,
        string? id)
    {
        _logger.LogInformation("HTTP trigger function consultants processed a request.");

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
            var consultantApi = new ConsultantApiService();

            if (!string.IsNullOrEmpty(id))
            {
                Console.WriteLine($"➡️ GET /api/consultants/{id}: request for consultant {id}");
                var result = await consultantApi.GetApiConsultantByIdAsync(id.ToLowerInvariant());
                var response = req.CreateResponse(HttpStatusCode.OK);
                AuthMiddleware.AddCorsHeaders(response);
                await response.WriteAsJsonAsync(new { results = new[] { result } });
                Console.WriteLine($"   ✅ GET /api/consultants/{id}: response status 1 consultant returned");
                return response;
            }

            var consultantName = req.Query["consultantName"]?.ToLowerInvariant() ?? "";
            var projectName = req.Query["projectName"]?.ToLowerInvariant() ?? "";
            var skill = req.Query["skill"]?.ToLowerInvariant() ?? "";
            var certification = req.Query["certification"]?.ToLowerInvariant() ?? "";
            var role = req.Query["role"]?.ToLowerInvariant() ?? "";
            var hoursAvailable = req.Query["hoursAvailable"]?.ToLowerInvariant() ?? "";

            Console.WriteLine($"➡️ GET /api/consultants: request for consultantName={consultantName}, projectName={projectName}, skill={skill}, certification={certification}, role={role}, hoursAvailable={hoursAvailable}");

            consultantName = Utilities.CleanUpParameter("consultantName", consultantName);
            projectName = Utilities.CleanUpParameter("projectName", projectName);
            skill = Utilities.CleanUpParameter("skill", skill);
            certification = Utilities.CleanUpParameter("certification", certification);
            role = Utilities.CleanUpParameter("role", role);
            hoursAvailable = Utilities.CleanUpParameter("hoursAvailable", hoursAvailable);

            var results = await consultantApi.GetApiConsultantsAsync(
                consultantName, projectName, skill, certification, role, hoursAvailable);

            var resp = req.CreateResponse(HttpStatusCode.OK);
            AuthMiddleware.AddCorsHeaders(resp);
            await resp.WriteAsJsonAsync(new { results });
            Console.WriteLine($"   ✅ GET /api/consultants: response status 200; {results.Count} consultants returned");
            return resp;
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

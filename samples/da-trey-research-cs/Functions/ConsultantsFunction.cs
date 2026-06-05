using System.Text.Json;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using TreyResearch.Models;
using TreyResearch.Services;

namespace TreyResearch.Functions;

public class ConsultantsFunction
{
    private readonly ILogger<ConsultantsFunction> _logger;

    public ConsultantsFunction(ILogger<ConsultantsFunction> logger)
    {
        _logger = logger;
    }

    [Function("consultants")]
    public async Task<HttpResponseData> Run(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "consultants/{id?}")] HttpRequestData req,
        string? id)
    {
        _logger.LogInformation("HTTP trigger function consultants processed a request.");

        try
        {
            await IdentityService.Instance.ValidateRequestAsync();

            if (!string.IsNullOrEmpty(id))
            {
                Console.WriteLine($"➡️ GET /api/consultants/{id}: request for consultant {id}");
                var consultant = await ConsultantApiService.Instance.GetApiConsultantByIdAsync(id.ToLower());
                Console.WriteLine($"   ✅ GET /api/consultants/{id}: 1 consultant returned");
                return await CreateResponse(req, 200, new { results = new[] { consultant } });
            }

            var consultantName = GetQueryParam(req, "consultantName");
            var projectName = GetQueryParam(req, "projectName");
            var skill = GetQueryParam(req, "skill");
            var certification = GetQueryParam(req, "certification");
            var role = GetQueryParam(req, "role");
            var hoursAvailable = GetQueryParam(req, "hoursAvailable");

            Console.WriteLine($"➡️ GET /api/consultants: request for consultantName={consultantName}, projectName={projectName}, skill={skill}, certification={certification}, role={role}, hoursAvailable={hoursAvailable}");

            consultantName = Utilities.CleanUpParameter("consultantName", consultantName);
            projectName = Utilities.CleanUpParameter("projectName", projectName);
            skill = Utilities.CleanUpParameter("skill", skill);
            certification = Utilities.CleanUpParameter("certification", certification);
            role = Utilities.CleanUpParameter("role", role);
            hoursAvailable = Utilities.CleanUpParameter("hoursAvailable", hoursAvailable);

            var result = await ConsultantApiService.Instance.GetApiConsultantsAsync(
                consultantName, projectName, skill, certification, role, hoursAvailable);

            Console.WriteLine($"   ✅ GET /api/consultants: {result.Count} consultants returned");
            return await CreateResponse(req, 200, new { results = result });
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

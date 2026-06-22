using System.Text.Json;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using TreyResearch.Models;
using TreyResearch.Services;

namespace TreyResearch.Functions;

public class MeFunction
{
    private readonly ILogger<MeFunction> _logger;

    public MeFunction(ILogger<MeFunction> logger)
    {
        _logger = logger;
    }

    [Function("me")]
    public async Task<HttpResponseData> Run(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get", "post", Route = "me/{command?}")] HttpRequestData req,
        string? command)
    {
        _logger.LogInformation("HTTP trigger function me processed a request.");

        try
        {
            var me = await IdentityService.Instance.ValidateRequestAsync();

            switch (req.Method.ToUpper())
            {
                case "GET":
                {
                    if (!string.IsNullOrEmpty(command))
                    {
                        throw new HttpError(400, $"Invalid command: {command}");
                    }

                    Console.WriteLine("➡️ GET /api/me request");
                    var result = new[] { me };
                    Console.WriteLine($"   ✅ GET /me response; {result.Length} consultants returned");
                    return await CreateResponse(req, 200, new { results = result });
                }
                case "POST":
                {
                    switch (command?.ToLower())
                    {
                        case "chargetime":
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

                            var hoursStr = GetJsonProperty(body.Value, "hours");
                            if (string.IsNullOrEmpty(hoursStr) || !double.TryParse(hoursStr, out var hours))
                            {
                                throw new HttpError(400, "Missing hours");
                            }
                            if (hours < 0 || hours > 24)
                            {
                                throw new HttpError(400, $"Invalid hours: {hours}");
                            }

                            Console.WriteLine($"➡️ POST /api/me/chargetime request for project {projectName}, hours {hours}");
                            var result = await ConsultantApiService.Instance.ChargeTimeToProjectAsync(projectName, me.Id, hours);

                            Console.WriteLine($"   ✅ POST /api/me/chargetime response; {result.Message}");
                            return await CreateResponse(req, 200, new
                            {
                                results = new
                                {
                                    status = 200,
                                    clientName = result.ClientName,
                                    projectName = result.ProjectName,
                                    remainingForecast = result.RemainingForecast,
                                    message = result.Message
                                }
                            });
                        }
                        default:
                            throw new HttpError(400, $"Invalid command: {command}");
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

using System.Net;
using System.Text.Json;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using TreyResearchApi.Middleware;
using TreyResearchApi.Models;
using TreyResearchApi.Services;

namespace TreyResearchApi.Functions;

public class MeFunction
{
    private readonly ILogger _logger;

    public MeFunction(ILoggerFactory loggerFactory)
    {
        _logger = loggerFactory.CreateLogger<MeFunction>();
    }

    [Function("me")]
    public async Task<HttpResponseData> RunAsync(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get", "post", Route = "me/{command?}")] HttpRequestData req,
        string? command)
    {
        _logger.LogInformation("HTTP trigger function me processed a request.");

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
            var me = await consultantApi.GetApiConsultantByEmailAsync(userInfo.Email);

            switch (req.Method.ToUpperInvariant())
            {
                case "GET":
                {
                    if (!string.IsNullOrEmpty(command))
                    {
                        throw new HttpError(400, $"Invalid command: {command}");
                    }

                    Console.WriteLine("➡️ GET /api/me request");
                    var response = req.CreateResponse(HttpStatusCode.OK);
                    AuthMiddleware.AddCorsHeaders(response);
                    await response.WriteAsJsonAsync(new { results = new[] { me } });
                    Console.WriteLine($"   ✅ GET /me response status 200; 1 consultant returned");
                    return response;
                }
                case "POST":
                {
                    switch (command?.ToLowerInvariant())
                    {
                        case "chargetime":
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

                            var hours = body.TryGetProperty("hours", out var h) ? h.GetDouble() : 0;
                            if (hours <= 0 || hours > 24)
                            {
                                throw new HttpError(400, $"Invalid hours: {hours}");
                            }

                            Console.WriteLine($"➡️ POST /api/me/chargetime request for project {projectName}, hours {hours}");
                            var result = await consultantApi.ChargeTimeToProjectAsync(projectName, userInfo.Id!, hours);

                            var response = req.CreateResponse(HttpStatusCode.OK);
                            AuthMiddleware.AddCorsHeaders(response);
                            await response.WriteAsJsonAsync(new
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
                            Console.WriteLine($"   ✅ POST /api/me/chargetime response status 200; {result.Message}");
                            return response;
                        }
                        default:
                            throw new HttpError(400, $"Invalid command: {command}");
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

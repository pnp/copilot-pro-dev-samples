// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using AdaptiveCardInlineEdit.Models;
using System.Net;

namespace AdaptiveCardInlineEdit
{
    public class Repairs
    {
        private readonly ILogger _logger;
        private readonly IConfiguration _configuration;

        public Repairs(ILoggerFactory loggerFactory, IConfiguration configuration)
        {
            _logger = loggerFactory.CreateLogger<Repairs>();
            _configuration = configuration;
        }

        [Function("repairs")]
        public async Task<HttpResponseData> RunAsync([HttpTrigger(AuthorizationLevel.Anonymous, "get")] HttpRequestData req)
        {
            _logger.LogInformation("C# HTTP trigger function processed a request.");

            if (!IsApiKeyValid(req))
            {
                return req.CreateResponse(HttpStatusCode.Unauthorized);
            }

            try
            {
                var repairRecords = RepairData.GetRepairs();

                string assignedTo = req.Query["assignedTo"];
                if (string.IsNullOrEmpty(assignedTo))
                {
                    var res = req.CreateResponse();
                    await res.WriteAsJsonAsync(new { results = repairRecords });
                    return res;
                }

                var query = assignedTo.Trim().ToLowerInvariant();
                var repairs = repairRecords.Where(r =>
                {
                    var fullName = r.AssignedTo.ToLowerInvariant();
                    if (fullName == query) return true;
                    var nameParts = fullName.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    return nameParts.Any(part => part == query);
                });

                var response = req.CreateResponse();
                await response.WriteAsJsonAsync(new { results = repairs });
                return response;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error reading or parsing repairs data");
                var errorResponse = req.CreateResponse(HttpStatusCode.InternalServerError);
                await errorResponse.WriteAsJsonAsync(new { error = "Failed to retrieve repair records" });
                return errorResponse;
            }
        }

        [Function("updateRepair")]
        public async Task<HttpResponseData> UpdateAsync(
            [HttpTrigger(AuthorizationLevel.Anonymous, "patch", Route = "repairs/{id}")] HttpRequestData req, string id)
        {
            _logger.LogInformation("C# HTTP trigger function processed an update request.");

            if (!IsApiKeyValid(req))
            {
                return req.CreateResponse(HttpStatusCode.Unauthorized);
            }

            var body = await req.ReadFromJsonAsync<RepairUpdateModel>();

            // Validate input - match Node.js behavior
            if (body?.Title != null && (body.Title is not string || string.IsNullOrWhiteSpace(body.Title)))
            {
                var badReq = req.CreateResponse(HttpStatusCode.BadRequest);
                await badReq.WriteAsJsonAsync(new { error = "Title must be a non-empty string" });
                return badReq;
            }
            if (body?.AssignedTo != null && (body.AssignedTo is not string || string.IsNullOrWhiteSpace(body.AssignedTo)))
            {
                var badReq = req.CreateResponse(HttpStatusCode.BadRequest);
                await badReq.WriteAsJsonAsync(new { error = "AssignedTo must be a non-empty string" });
                return badReq;
            }

            try
            {
                var updatedRepair = RepairData.UpdateRepair(id, body?.Title, body?.AssignedTo);
                if (updatedRepair == null)
                {
                    return req.CreateResponse(HttpStatusCode.NotFound);
                }

                var response = req.CreateResponse();
                await response.WriteAsJsonAsync(new { updatedRepair });
                return response;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error updating repair record");
                var errorResponse = req.CreateResponse(HttpStatusCode.InternalServerError);
                await errorResponse.WriteAsJsonAsync(new { error = "Failed to update repair record" });
                return errorResponse;
            }
        }

        private bool IsApiKeyValid(HttpRequestData req)
        {
            // Try to get the value of the 'Authorization' header from the request.
            // If the header is not present, return false.
            if (!req.Headers.TryGetValues("X-API-Key", out var authValue))
            {
                return false;
            }

            // Get the api key value from the 'Authorization' header.
            var apiKey = authValue.FirstOrDefault().Trim();

            // Get the API key from the configuration.
            var configApiKey = _configuration["API_KEY"];

            // Check if the API key from the request matches the API key from the configuration.
            return apiKey == configApiKey;
        }
    }
}
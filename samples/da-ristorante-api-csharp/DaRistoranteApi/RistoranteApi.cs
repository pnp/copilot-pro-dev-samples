using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using System.Net;
using System.Text.Json;

namespace DaRistoranteApi
{
    public class RistoranteApi
    {
        private readonly ILogger _logger;

        public RistoranteApi(ILoggerFactory loggerFactory)
        {
            _logger = loggerFactory.CreateLogger<RistoranteApi>();
        }

        [Function("dishes")]
        public async Task<HttpResponseData> GetDishesAsync(
            [HttpTrigger(AuthorizationLevel.Anonymous, "get")] HttpRequestData req)
        {
            _logger.LogInformation("C# HTTP trigger function processed a dishes request.");

            var allDishes = MenuData.GetDishes();
            var filtered = allDishes.AsEnumerable();

            var name = req.Query["name"];
            if (!string.IsNullOrEmpty(name))
            {
                filtered = filtered.Where(d => d.Name.Contains(name, StringComparison.OrdinalIgnoreCase));
            }

            var course = req.Query["course"];
            if (!string.IsNullOrEmpty(course))
            {
                filtered = filtered.Where(d => d.Course == course);
            }

            var type = req.Query["type"];
            if (!string.IsNullOrEmpty(type))
            {
                filtered = filtered.Where(d => d.Type == type);
            }

            var allergensParam = req.Query["allergens"];
            if (!string.IsNullOrEmpty(allergensParam))
            {
                var allergens = allergensParam.Split(',', StringSplitOptions.RemoveEmptyEntries);
                filtered = filtered.Where(d => allergens.All(a => !d.Allergens.Contains(a)));
            }

            var response = req.CreateResponse(HttpStatusCode.OK);
            await response.WriteAsJsonAsync(new { dishes = filtered.ToList() });
            return response;
        }

        [Function("orders")]
        public async Task<HttpResponseData> PlaceOrderAsync(
            [HttpTrigger(AuthorizationLevel.Anonymous, "post")] HttpRequestData req)
        {
            _logger.LogInformation("C# HTTP trigger function processed an orders request.");

            Models.Order order;
            try
            {
                order = await JsonSerializer.DeserializeAsync<Models.Order>(req.Body);
            }
            catch (JsonException)
            {
                var badResponse = req.CreateResponse(HttpStatusCode.BadRequest);
                await badResponse.WriteAsJsonAsync(new { message = "Invalid JSON format" });
                return badResponse;
            }

            if (order?.Dishes == null || order.Dishes.Count == 0)
            {
                var badResponse = req.CreateResponse(HttpStatusCode.BadRequest);
                await badResponse.WriteAsJsonAsync(new { message = "Invalid order format" });
                return badResponse;
            }

            var allDishes = MenuData.GetDishes();
            double totalPrice = 0;

            foreach (var orderedDish in order.Dishes)
            {
                var match = allDishes.FirstOrDefault(d =>
                    d.Name.Contains(orderedDish.Name, StringComparison.OrdinalIgnoreCase));

                if (match == null)
                {
                    _logger.LogError("Invalid dish: {DishName}", orderedDish.Name);
                    var badResponse = req.CreateResponse(HttpStatusCode.BadRequest);
                    await badResponse.WriteAsJsonAsync(new { message = "One or more invalid dishes" });
                    return badResponse;
                }

                totalPrice += match.Price * orderedDish.Quantity;
            }

            var orderId = Random.Shared.Next(0, 10000);

            var response = req.CreateResponse(HttpStatusCode.Created);
            await response.WriteAsJsonAsync(new
            {
                order_id = orderId,
                status = "confirmed",
                total_price = totalPrice
            });
            return response;
        }
    }
}

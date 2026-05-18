using System.Text.Json.Serialization;

namespace DaRistoranteApi.Models
{
    public class Dish
    {
        [JsonPropertyName("id")]
        public int Id { get; set; }

        [JsonPropertyName("name")]
        public string Name { get; set; }

        [JsonPropertyName("description")]
        public string Description { get; set; }

        [JsonPropertyName("image_url")]
        public string ImageUrl { get; set; }

        [JsonPropertyName("price")]
        public double Price { get; set; }

        [JsonPropertyName("allergens")]
        public List<string> Allergens { get; set; } = new();

        [JsonPropertyName("type")]
        public string Type { get; set; }

        [JsonPropertyName("course")]
        public string Course { get; set; }
    }

    public class OrderedDish
    {
        [JsonPropertyName("name")]
        public string Name { get; set; }

        [JsonPropertyName("quantity")]
        public int Quantity { get; set; }
    }

    public class Order
    {
        [JsonPropertyName("dishes")]
        public List<OrderedDish> Dishes { get; set; }
    }
}

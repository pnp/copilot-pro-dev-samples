using System.Text.Json.Serialization;

namespace AdaptiveCardInlineEdit.Models
{
    public class RepairModel
    {
        [JsonPropertyName("id")]
        public required string Id { get; set; }

        [JsonPropertyName("title")]
        public required string Title { get; set; }

        [JsonPropertyName("description")]
        public required string Description { get; set; }

        [JsonPropertyName("assignedTo")]
        public required string AssignedTo { get; set; }

        [JsonPropertyName("date")]
        public required string Date { get; set; }

        [JsonPropertyName("image")]
        public required string Image { get; set; }
    }
}

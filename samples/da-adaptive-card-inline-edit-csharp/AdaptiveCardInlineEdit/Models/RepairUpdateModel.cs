using System.Text.Json.Serialization;

namespace AdaptiveCardInlineEdit.Models
{
    public class RepairUpdateModel
    {
        [JsonPropertyName("title")]
        public string? Title { get; set; }

        [JsonPropertyName("assignedTo")]
        public string? AssignedTo { get; set; }
    }
}

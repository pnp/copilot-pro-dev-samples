using Azure;
using Azure.Data.Tables;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace TreyResearchApi.Models;

public class DbEntity : ITableEntity
{
    public string PartitionKey { get; set; } = "";
    public string RowKey { get; set; } = "";
    public DateTimeOffset? Timestamp { get; set; }
    public ETag ETag { get; set; }
}

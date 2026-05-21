using System.Text.Json;
using DaRepairsOAuth.Models;

namespace DaRepairsOAuth;

internal static class RepairsData
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web);
    private static readonly IReadOnlyList<RepairRecord> Records = LoadRecords();

    public static IReadOnlyList<RepairRecord> GetRecords() => Records;

    private static IReadOnlyList<RepairRecord> LoadRecords()
    {
        var dataPath = Path.Combine(AppContext.BaseDirectory, "RepairsData.json");

        using var stream = File.OpenRead(dataPath);
        var repairs = JsonSerializer.Deserialize<List<RepairRecord>>(stream, SerializerOptions);

        return repairs ?? new List<RepairRecord>();
    }
}
using Azure.Data.Tables;
using System.Text.Json;
using TreyResearchApi.Models;

namespace TreyResearchApi.Services;

public class DbService
{
    private readonly string _connectionString;
    private readonly bool _okToCacheLocally;
    private Dictionary<string, object>? _entityCache;

    public DbService(bool okToCacheLocally)
    {
        _connectionString = Environment.GetEnvironmentVariable("STORAGE_ACCOUNT_CONNECTION_STRING")
            ?? throw new InvalidOperationException("STORAGE_ACCOUNT_CONNECTION_STRING is not set");
        _okToCacheLocally = okToCacheLocally;
    }

    public async Task<Dictionary<string, object>?> GetEntityByRowKeyAsync(string tableName, string rowKey)
    {
        if (!_okToCacheLocally)
        {
            var tableClient = new TableClient(_connectionString, tableName);
            var response = await tableClient.GetEntityAsync<TableEntity>(tableName, rowKey);
            return ExpandPropertyValues(response.Value);
        }

        var entities = await GetEntitiesAsync(tableName);
        var result = entities.FirstOrDefault(e =>
            e.TryGetValue("RowKey", out var rk) && rk?.ToString() == rowKey);

        if (result == null)
        {
            throw new HttpError(404, $"Entity {rowKey} not found");
        }

        return result;
    }

    public async Task<List<Dictionary<string, object>>> GetEntitiesAsync(string tableName)
    {
        if (_okToCacheLocally && _entityCache != null)
        {
            return (List<Dictionary<string, object>>)_entityCache["entities"];
        }

        var tableClient = new TableClient(_connectionString, tableName);
        var entities = new List<Dictionary<string, object>>();

        await foreach (var entity in tableClient.QueryAsync<TableEntity>())
        {
            // Remove duplicates
            if (!entities.Any(e => e.TryGetValue("RowKey", out var rk) && rk?.ToString() == entity.RowKey))
            {
                entities.Add(ExpandPropertyValues(entity));
            }
        }

        if (_okToCacheLocally)
        {
            _entityCache = new Dictionary<string, object> { ["entities"] = entities };
        }

        return entities;
    }

    public async Task CreateEntityAsync(string tableName, string rowKey, Dictionary<string, object> entity)
    {
        _entityCache = null;
        var tableEntity = CompressPropertyValues(entity);
        tableEntity["PartitionKey"] = tableName;
        tableEntity["RowKey"] = rowKey;

        var tableClient = new TableClient(_connectionString, tableName);
        var te = new TableEntity(tableEntity.ToDictionary(kvp => kvp.Key, kvp => kvp.Value));

        try
        {
            await tableClient.AddEntityAsync(te);
        }
        catch (Azure.RequestFailedException ex) when (ex.Status == 409)
        {
            // Entity already exists, ignore
        }
        catch (Exception ex)
        {
            throw new HttpError(500, ex.Message);
        }
    }

    public async Task UpdateEntityAsync(string tableName, Dictionary<string, object> entity)
    {
        _entityCache = null;
        var compressed = CompressPropertyValues(entity);
        var te = new TableEntity(compressed.ToDictionary(kvp => kvp.Key, kvp => kvp.Value));

        var tableClient = new TableClient(_connectionString, tableName);
        await tableClient.UpdateEntityAsync(te, Azure.ETag.All, TableUpdateMode.Replace);
    }

    private Dictionary<string, object> ExpandPropertyValues(TableEntity entity)
    {
        var result = new Dictionary<string, object>();
        foreach (var kvp in entity)
        {
            result[kvp.Key] = ExpandPropertyValue(kvp.Value);
        }
        // Ensure standard keys are present
        result["PartitionKey"] = entity.PartitionKey;
        result["RowKey"] = entity.RowKey;
        return result;
    }

    private object ExpandPropertyValue(object value)
    {
        if (value is string s && s.Length > 0 && (s[0] == '{' || s[0] == '['))
        {
            try
            {
                return JsonSerializer.Deserialize<JsonElement>(s);
            }
            catch
            {
                return value;
            }
        }
        return value;
    }

    private Dictionary<string, object> CompressPropertyValues(Dictionary<string, object> entity)
    {
        var result = new Dictionary<string, object>();
        foreach (var kvp in entity)
        {
            result[kvp.Key] = CompressPropertyValue(kvp.Value);
        }
        return result;
    }

    private object CompressPropertyValue(object value)
    {
        if (value is JsonElement je)
        {
            return je.ToString();
        }
        if (value is List<string> list)
        {
            return JsonSerializer.Serialize(list);
        }
        if (value is List<HoursEntry> hours)
        {
            return JsonSerializer.Serialize(hours);
        }
        if (value is Location loc)
        {
            return JsonSerializer.Serialize(loc);
        }
        return value;
    }
}

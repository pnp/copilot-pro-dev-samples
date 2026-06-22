using System.Text.Json;
using Azure.Data.Tables;

namespace TreyResearch.Services;

public class DbService
{
    private readonly string _connectionString;
    private readonly bool _okToCacheLocally;
    private List<TableEntity>? _entityCache;

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    public DbService(bool okToCacheLocally)
    {
        _connectionString = Environment.GetEnvironmentVariable("STORAGE_ACCOUNT_CONNECTION_STRING")
            ?? throw new InvalidOperationException("STORAGE_ACCOUNT_CONNECTION_STRING is not set");
        _okToCacheLocally = okToCacheLocally;
    }

    public async Task<TableEntity> GetEntityByRowKeyAsync(string tableName, string rowKey)
    {
        if (!_okToCacheLocally)
        {
            var tableClient = new TableClient(_connectionString, tableName);
            var entity = await tableClient.GetEntityAsync<TableEntity>(tableName, rowKey);
            return ExpandPropertyValues(entity.Value);
        }

        var entities = await GetEntitiesAsync(tableName);
        var result = entities.FirstOrDefault(e => e.RowKey == rowKey);
        if (result == null)
        {
            throw new HttpError(404, $"Entity {rowKey} not found");
        }
        return result;
    }

    public async Task<List<TableEntity>> GetEntitiesAsync(string tableName)
    {
        if (!_okToCacheLocally || _entityCache == null || _entityCache.Count == 0)
        {
            var tableClient = new TableClient(_connectionString, tableName);
            var entities = tableClient.QueryAsync<TableEntity>();
            _entityCache = new List<TableEntity>();
            await foreach (var entity in entities)
            {
                if (!_entityCache.Any(e => e.RowKey == entity.RowKey))
                {
                    _entityCache.Add(ExpandPropertyValues(entity));
                }
            }
        }
        return _entityCache;
    }

    public async Task CreateEntityAsync(string tableName, string rowKey, Dictionary<string, object> properties)
    {
        _entityCache = null;
        var tableClient = new TableClient(_connectionString, tableName);
        var entity = new TableEntity(tableName, rowKey);
        foreach (var kvp in properties)
        {
            entity[kvp.Key] = CompressPropertyValue(kvp.Value);
        }

        try
        {
            await tableClient.AddEntityAsync(entity);
        }
        catch (Azure.RequestFailedException ex) when (ex.Status == 409)
        {
            // Entity already exists, ignore
        }
    }

    public async Task UpdateEntityAsync(string tableName, TableEntity entity)
    {
        _entityCache = null;
        var compressed = CompressPropertyValues(entity);
        var tableClient = new TableClient(_connectionString, tableName);
        await tableClient.UpdateEntityAsync(compressed, compressed.ETag, TableUpdateMode.Replace);
    }

    private TableEntity ExpandPropertyValues(TableEntity entity)
    {
        var result = new TableEntity(entity.PartitionKey, entity.RowKey)
        {
            ETag = entity.ETag,
            Timestamp = entity.Timestamp
        };

        foreach (var key in entity.Keys)
        {
            if (key is "odata.etag" or "PartitionKey" or "RowKey" or "Timestamp")
                continue;
            result[key] = ExpandPropertyValue(entity[key]);
        }
        return result;
    }

    private object? ExpandPropertyValue(object? value)
    {
        if (value is string str && str.Length > 0 && (str[0] == '{' || str[0] == '['))
        {
            try
            {
                return JsonSerializer.Deserialize<JsonElement>(str);
            }
            catch
            {
                return value;
            }
        }
        return value;
    }

    private TableEntity CompressPropertyValues(TableEntity entity)
    {
        var result = new TableEntity(entity.PartitionKey, entity.RowKey)
        {
            ETag = entity.ETag,
            Timestamp = entity.Timestamp
        };
        foreach (var key in entity.Keys)
        {
            if (key is "odata.etag" or "PartitionKey" or "RowKey" or "Timestamp")
                continue;
            result[key] = CompressPropertyValue(entity[key]);
        }
        return result;
    }

    private object? CompressPropertyValue(object? value)
    {
        if (value is JsonElement jsonElement)
        {
            return jsonElement.GetRawText();
        }
        return value;
    }
}

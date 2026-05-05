#nullable enable
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol;

namespace cea_techPulse_csharp.Services;

/// <summary>
/// MCP client that spawns and connects to the Tech News MCP server via stdio.
/// Mirrors TechNewsMcpService in the TypeScript and Python samples.
/// </summary>
public class TechNewsMcpService : IAsyncDisposable
{
    private readonly string _mcpServerPath;
    private readonly string _newsApiKey;
    private readonly SemaphoreSlim _connectLock = new(1, 1);
    private McpClient? _client;
    private bool _isConnected;

    public TechNewsMcpService(string mcpServerPath, string newsApiKey)
    {
        _mcpServerPath = mcpServerPath;
        _newsApiKey = newsApiKey;
    }

    public bool IsConnected => _isConnected;

    public async Task ConnectAsync()
    {
        if (_isConnected) return;

        await _connectLock.WaitAsync();
        try
        {
            if (_isConnected) return;

            var transport = new StdioClientTransport(new StdioClientTransportOptions
            {
                Command = "dotnet",
                Arguments = ["run", "--project", _mcpServerPath],
                EnvironmentVariables = new Dictionary<string, string>
                {
                    ["NEWS_API_KEY"] = _newsApiKey,
                },
            });

            _client = await McpClient.CreateAsync(transport);
            _isConnected = true;
        }
        finally
        {
            _connectLock.Release();
        }
    }

    public async ValueTask DisposeAsync()
    {
        await _connectLock.WaitAsync();
        try
        {
            if (_client is not null)
            {
                await _client.DisposeAsync();
            }
            _client = null;
            _isConnected = false;
        }
        finally
        {
            _connectLock.Release();
        }
        _connectLock.Dispose();
    }

    private async Task<string> CallToolAsync(string name, Dictionary<string, object?> arguments)
    {
        if (_client is null || !_isConnected)
            throw new InvalidOperationException("Tech News MCP client not connected");

        var result = await _client.CallToolAsync(name, arguments);

        if (result.Content is { Count: > 0 } && result.Content[0] is TextContentBlock textBlock)
        {
            return textBlock.Text ?? "No data available";
        }

        return "No results found";
    }

    public Task<string> GetTechNewsAsync(string category = "general", int limit = 10)
        => CallToolAsync("get_tech_news", new Dictionary<string, object?>
        {
            ["category"] = category,
            ["limit"] = limit,
        });

    public Task<string> SearchTechNewsAsync(string keyword, int limit = 10, string timeframe = "week")
        => CallToolAsync("search_tech_news", new Dictionary<string, object?>
        {
            ["keyword"] = keyword,
            ["limit"] = limit,
            ["timeframe"] = timeframe,
        });

    public Task<string> GetTrendingTechAsync(string region = "us", int limit = 10)
        => CallToolAsync("get_trending_tech", new Dictionary<string, object?>
        {
            ["region"] = region,
            ["limit"] = limit,
        });

    public Task<string> GetCompanyNewsAsync(string company, int limit = 8, string timeframe = "week")
        => CallToolAsync("get_company_news", new Dictionary<string, object?>
        {
            ["company"] = company,
            ["limit"] = limit,
            ["timeframe"] = timeframe,
        });
}

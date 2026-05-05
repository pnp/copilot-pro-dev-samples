using System.ComponentModel;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json.Serialization;
using System.Web;
using ModelContextProtocol.Server;

namespace TechNewsMcpServer;

/// <summary>
/// MCP tools for fetching tech news from NewsAPI.
/// Mirrors the tools in the TypeScript (tech-news.js) and Python (tech_news.py) MCP servers.
/// </summary>
[McpServerToolType]
public static class TechNewsTools
{
    private const string NewsApiBase = "https://newsapi.org/v2";

    private static readonly Dictionary<string, string> TechQueries = new()
    {
        ["general"] = "technology OR tech OR software OR hardware OR startup",
        ["ai"] = "artificial intelligence OR machine learning OR AI OR ChatGPT OR OpenAI",
        ["startups"] = "startup OR venture capital OR funding OR IPO OR tech company",
        ["cybersecurity"] = "cybersecurity OR hacking OR data breach OR security OR malware",
        ["mobile"] = "smartphone OR iPhone OR Android OR mobile app OR tablet",
        ["gaming"] = "gaming OR video games OR esports OR PlayStation OR Xbox OR Nintendo",
    };

    private const string TechDomains =
        "techcrunch.com,theverge.com,arstechnica.com,wired.com," +
        "engadget.com,venturebeat.com,zdnet.com,cnet.com,recode.net,mashable.com";

    private const string SearchDomains = TechDomains + ",reuters.com,bloomberg.com";
    private const string CompanyDomains = SearchDomains + ",cnbc.com";

    [McpServerTool(Name = "get_tech_news"), Description("Get latest technology news headlines")]
    public static async Task<string> GetTechNews(
        [Description("Tech category: general, ai, startups, cybersecurity, mobile, or gaming")] string category = "general",
        [Description("Number of articles (1-20)")] int limit = 10)
    {
        limit = Math.Clamp(limit, 1, 20);
        var query = TechQueries.GetValueOrDefault(category, TechQueries["general"]);

        var data = await MakeRequestAsync("everything", new Dictionary<string, string>
        {
            ["q"] = query,
            ["language"] = "en",
            ["sortBy"] = "publishedAt",
            ["pageSize"] = limit.ToString(),
            ["domains"] = TechDomains,
        });

        if (data?.ErrorMessage is not null)
            return $"Unable to fetch tech news: {data.ErrorMessage}";

        var articles = data?.Articles;
        if (articles == null || articles.Count == 0)
            return $"No tech news found for category: {category}";

        return $"Latest Tech News - {category.ToUpperInvariant()} ({articles.Count} articles):\n\n{FormatArticles(articles, limit)}";
    }

    [McpServerTool(Name = "search_tech_news"), Description("Search for specific tech news by keyword")]
    public static async Task<string> SearchTechNews(
        [Description("Keyword to search for in tech news")] string keyword,
        [Description("Number of articles (1-20)")] int limit = 10,
        [Description("Time range: today, week, or month")] string timeframe = "week")
    {
        limit = Math.Clamp(limit, 1, 20);
        var fromDate = DateFromTimeframe(timeframe);
        var toDate = DateTime.UtcNow.ToString("yyyy-MM-dd");
        var enhancedQuery = $"({keyword}) AND (technology OR tech OR software OR startup OR AI OR cybersecurity)";

        var data = await MakeRequestAsync("everything", new Dictionary<string, string>
        {
            ["q"] = enhancedQuery,
            ["language"] = "en",
            ["sortBy"] = "relevancy",
            ["pageSize"] = limit.ToString(),
            ["from"] = fromDate,
            ["to"] = toDate,
            ["domains"] = SearchDomains,
        });

        if (data?.ErrorMessage is not null)
            return $"Unable to search tech news: {data.ErrorMessage}";

        var articles = data?.Articles;
        if (articles == null || articles.Count == 0)
            return $"No tech news found for keyword: {keyword} in timeframe: {timeframe}";

        return $"Tech News Search Results for \"{keyword}\" ({timeframe}):\nFound {articles.Count} articles\n\n{FormatArticles(articles, limit)}";
    }

    [McpServerTool(Name = "get_trending_tech"), Description("Get trending technology topics and headlines")]
    public static async Task<string> GetTrendingTech(
        [Description("Region code: us, gb, ca, or au")] string region = "us",
        [Description("Number of trending articles (1-15)")] int limit = 10)
    {
        limit = Math.Clamp(limit, 1, 15);

        var data = await MakeRequestAsync("top-headlines", new Dictionary<string, string>
        {
            ["category"] = "technology",
            ["country"] = region,
            ["pageSize"] = limit.ToString(),
        });

        if (data?.ErrorMessage is not null)
            return $"Unable to fetch trending tech: {data.ErrorMessage}";

        var articles = data?.Articles;
        if (articles == null || articles.Count == 0)
            return $"No trending tech topics found for region: {region}";

        return $"Trending Tech Topics ({region.ToUpperInvariant()}) - {articles.Count} articles:\n\n{FormatArticles(articles, limit)}";
    }

    [McpServerTool(Name = "get_company_news"), Description("Get news about specific tech companies")]
    public static async Task<string> GetCompanyNews(
        [Description("Company name (e.g. Microsoft, Apple, Google)")] string company,
        [Description("Number of articles (1-15)")] int limit = 8,
        [Description("Time range: today, week, or month")] string timeframe = "week")
    {
        limit = Math.Clamp(limit, 1, 15);
        var fromDate = DateFromTimeframe(timeframe);

        var data = await MakeRequestAsync("everything", new Dictionary<string, string>
        {
            ["q"] = $"\"{company}\"",
            ["language"] = "en",
            ["sortBy"] = "relevancy",
            ["pageSize"] = limit.ToString(),
            ["from"] = fromDate,
            ["domains"] = CompanyDomains,
        });

        if (data?.ErrorMessage is not null)
            return $"Unable to fetch company news: {data.ErrorMessage}";

        var articles = data?.Articles;
        if (articles == null || articles.Count == 0)
            return $"No recent news found for company: {company} in timeframe: {timeframe}";

        return $"{company} News ({timeframe}) - {articles.Count} articles:\n\n{FormatArticles(articles, limit)}";
    }

    // ── Helpers ──────────────────────────────────────────────────────

    private static readonly HttpClient SharedHttpClient = CreateHttpClient();

    private static HttpClient CreateHttpClient()
    {
        var client = new HttpClient();
        client.DefaultRequestHeaders.Add("User-Agent", "tech-news-mcp-server/1.0");
        client.DefaultRequestHeaders.Add("Accept", "application/json");
        return client;
    }

    private static async Task<NewsApiResponse?> MakeRequestAsync(string endpoint, Dictionary<string, string> parameters)
    {
        var apiKey = Environment.GetEnvironmentVariable("NEWS_API_KEY")
                  ?? Environment.GetEnvironmentVariable("SECRET_NEWS_API_KEY")
                  ?? "DEMO_KEY";

        var queryString = HttpUtility.ParseQueryString(string.Empty);
        queryString["apiKey"] = apiKey;

        foreach (var (key, value) in parameters)
        {
            if (!string.IsNullOrEmpty(value))
                queryString[key] = value;
        }

        var url = $"{NewsApiBase}/{endpoint}?{queryString}";

        HttpResponseMessage response;
        try
        {
            response = await SharedHttpClient.GetAsync(url);
        }
        catch (HttpRequestException ex)
        {
            return new NewsApiResponse
            {
                Status = "error",
                Articles = [],
                ErrorMessage = $"Network error contacting NewsAPI: {ex.Message}",
            };
        }

        if (!response.IsSuccessStatusCode)
        {
            var body = await response.Content.ReadAsStringAsync();
            return new NewsApiResponse
            {
                Status = "error",
                Articles = [],
                ErrorMessage = $"NewsAPI returned {(int)response.StatusCode} {response.ReasonPhrase}: {body}",
            };
        }

        return await response.Content.ReadFromJsonAsync<NewsApiResponse>();
    }

    private static string FormatArticles(List<NewsArticle> articles, int limit)
    {
        var sb = new StringBuilder();
        var count = Math.Min(articles.Count, limit);

        for (int i = 0; i < count; i++)
        {
            var article = articles[i];
            var publishedStr = "Unknown";
            if (DateTime.TryParse(article.PublishedAt, out var published))
            {
                publishedStr = published.ToString("ddd, MMM dd, yyyy hh:mm tt");
            }

            sb.AppendLine($"{i + 1}. {article.Title ?? "No title"}");
            sb.AppendLine($"Source: {article.Source?.Name ?? "Unknown"}");
            sb.AppendLine($"Published: {publishedStr}");
            sb.AppendLine($"Description: {article.Description ?? "No description available"}");
            sb.AppendLine($"URL: {article.Url ?? ""}");
            sb.AppendLine("---");
        }

        return sb.ToString();
    }

    private static string DateFromTimeframe(string timeframe)
    {
        var now = DateTime.UtcNow;
        var from = timeframe switch
        {
            "today" => now.AddDays(-1),
            "month" => now.AddDays(-30),
            _ => now.AddDays(-7),
        };
        return from.ToString("yyyy-MM-dd");
    }
}

// ── NewsAPI response models ─────────────────────────────────────────

public class NewsApiResponse
{
    [JsonPropertyName("status")]
    public string? Status { get; set; }

    [JsonPropertyName("totalResults")]
    public int TotalResults { get; set; }

    [JsonPropertyName("articles")]
    public List<NewsArticle>? Articles { get; set; }

    /// <summary>
    /// Populated locally when the HTTP request fails or returns a non-success status.
    /// </summary>
    [JsonIgnore]
    public string? ErrorMessage { get; set; }
}

public class NewsArticle
{
    [JsonPropertyName("source")]
    public NewsSource? Source { get; set; }

    [JsonPropertyName("title")]
    public string? Title { get; set; }

    [JsonPropertyName("description")]
    public string? Description { get; set; }

    [JsonPropertyName("url")]
    public string? Url { get; set; }

    [JsonPropertyName("publishedAt")]
    public string? PublishedAt { get; set; }
}

public class NewsSource
{
    [JsonPropertyName("id")]
    public string? Id { get; set; }

    [JsonPropertyName("name")]
    public string? Name { get; set; }
}

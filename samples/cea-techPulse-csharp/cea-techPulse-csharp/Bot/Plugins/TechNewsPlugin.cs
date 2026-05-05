using cea_techPulse_csharp.Services;
using Microsoft.SemanticKernel;
using System.ComponentModel;

namespace cea_techPulse_csharp.Bot.Plugins;

public class TechNewsPlugin
{
    private readonly TechNewsMcpService _mcpService;

    public TechNewsPlugin(TechNewsMcpService mcpService)
    {
        _mcpService = mcpService;
    }

    [KernelFunction, Description("Get latest technology news headlines by category (general, ai, startups, cybersecurity, mobile, gaming)")]
    public async Task<string> GetTechNews(
        [Description("Tech category: general, ai, startups, cybersecurity, mobile, or gaming")] string category = "general",
        [Description("Number of articles (1-20)")] int limit = 10)
    {
        return await _mcpService.GetTechNewsAsync(category, limit);
    }

    [KernelFunction, Description("Search for specific tech news by keyword")]
    public async Task<string> SearchTechNews(
        [Description("Keyword to search for")] string keyword,
        [Description("Number of articles (1-20)")] int limit = 10,
        [Description("Time range: today, week, or month")] string timeframe = "week")
    {
        return await _mcpService.SearchTechNewsAsync(keyword, limit, timeframe);
    }

    [KernelFunction, Description("Get trending technology topics and headlines")]
    public async Task<string> GetTrendingTech(
        [Description("Region code: us, gb, ca, or au")] string region = "us",
        [Description("Number of articles (1-15)")] int limit = 10)
    {
        return await _mcpService.GetTrendingTechAsync(region, limit);
    }

    [KernelFunction, Description("Get news about a specific tech company")]
    public async Task<string> GetCompanyNews(
        [Description("Company name (e.g. Microsoft, Apple, Google)")] string company,
        [Description("Number of articles (1-15)")] int limit = 8,
        [Description("Time range: today, week, or month")] string timeframe = "week")
    {
        return await _mcpService.GetCompanyNewsAsync(company, limit, timeframe);
    }
}

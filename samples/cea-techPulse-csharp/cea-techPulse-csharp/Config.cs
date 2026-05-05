namespace cea_techPulse_csharp
{
    public class ConfigOptions
    {
        public required OpenAIConfigOptions OpenAI { get; set; }
        public required NewsApiConfigOptions NewsApi { get; set; }
    }

    /// <summary>
    /// Options for OpenAI
    /// </summary>
    public class OpenAIConfigOptions
    {
        public required string ApiKey { get; set; }
        public string DefaultModel { get; set; } = "gpt-4o";
    }

    /// <summary>
    /// Options for the News API
    /// </summary>
    public class NewsApiConfigOptions
    {
        public required string ApiKey { get; set; }
    }
}
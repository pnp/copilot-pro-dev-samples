using cea_techPulse_csharp;
using cea_techPulse_csharp.Services;
using Microsoft.SemanticKernel;
using Microsoft.Agents.Hosting.AspNetCore;
using Microsoft.Agents.Builder.App;
using Microsoft.Agents.Builder;
using Microsoft.Agents.Storage;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddHttpContextAccessor();
builder.Logging.AddConsole();

// Register Semantic Kernel
builder.Services.AddKernel();

// Validate and register the AI service of your choice.
var openAiSection = builder.Configuration.GetRequiredSection("OpenAI");
var openAiModel = openAiSection["DefaultModel"] ?? "gpt-4o";
var openAiApiKey = openAiSection["ApiKey"];
if (string.IsNullOrWhiteSpace(openAiApiKey))
{
    throw new InvalidOperationException("Configuration value 'OpenAI:ApiKey' is required.");
}

builder.Services.AddOpenAIChatCompletion(
   modelId: openAiModel,
   apiKey: openAiApiKey
);

// Register the TechNewsMcpService
var isLocalMcpDevelopment = builder.Environment.IsDevelopment() || builder.Environment.EnvironmentName == "Playground";
var configuredMcpServerPath = builder.Configuration["TechNewsMcpServer:Path"];
var mcpServerPath = isLocalMcpDevelopment
    ? Path.GetFullPath(Path.Combine(builder.Environment.ContentRootPath, "McpServer"))
    : string.IsNullOrWhiteSpace(configuredMcpServerPath)
        ? throw new InvalidOperationException(
            "TechNews MCP server path is not configured for this environment. " +
            "Set configuration key 'TechNewsMcpServer:Path' to the deployed MCP server artifact " +
            "(or connect to the MCP server via a separately hosted supported transport).")
        : Path.GetFullPath(configuredMcpServerPath);
if (!Directory.Exists(mcpServerPath) && !File.Exists(mcpServerPath))
{
    throw new InvalidOperationException(
        $"TechNews MCP server path '{mcpServerPath}' does not exist. " +
        "Ensure the MCP server is packaged with the deployment artifact for local execution, " +
        "or configure 'TechNewsMcpServer:Path' to a valid deployed location.");
}
var newsApiKey = builder.Configuration.GetSection("NewsApi")["ApiKey"];
if (string.IsNullOrWhiteSpace(newsApiKey))
{
    throw new InvalidOperationException("Configuration value 'NewsApi:ApiKey' is required.");
}
builder.Services.AddSingleton(new TechNewsMcpService(mcpServerPath, newsApiKey));

// Add AspNet token validation
builder.Services.AddBotAspNetAuthentication(builder.Configuration);

builder.Services.AddSingleton<IStorage, MemoryStorage>();

// Add AgentApplicationOptions from config.
builder.AddAgentApplicationOptions();

// Add AgentApplicationOptions.  This will use DI'd services and IConfiguration for construction.
builder.Services.AddTransient<AgentApplicationOptions>();

// Add the bot (which is transient)
builder.AddAgent<cea_techPulse_csharp.Bot.TechNewsBot>();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseDeveloperExceptionPage();
}
app.UseStaticFiles();

app.UseRouting();

app.UseAuthentication();
app.UseAuthorization();

app.MapPost("/api/messages", async (HttpRequest request, HttpResponse response, IAgentHttpAdapter adapter, IAgent agent, CancellationToken cancellationToken) =>
{
    await adapter.ProcessAsync(request, response, agent, cancellationToken);
});

if (app.Environment.IsDevelopment() || app.Environment.EnvironmentName == "Playground")
{
    app.MapGet("/", () => "TechPulse News Agent");
    app.UseDeveloperExceptionPage();
    app.MapControllers().AllowAnonymous();
}
else
{
    app.MapControllers();
}

app.Run();


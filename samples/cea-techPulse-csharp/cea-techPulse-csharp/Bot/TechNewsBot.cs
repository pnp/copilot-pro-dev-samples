using cea_techPulse_csharp.Bot.Plugins;
using cea_techPulse_csharp.Services;
using Microsoft.Agents.Builder;
using Microsoft.Agents.Builder.App;
using Microsoft.Agents.Builder.State;
using Microsoft.Agents.Core.Models;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace cea_techPulse_csharp.Bot;

public class TechNewsBot : AgentApplication
{
    private readonly Kernel _kernel;
    private readonly TechNewsMcpService _mcpService;

    private const string SystemPrompt = """
        You are an AI agent that can chat with users and provide tech news.
        You can help users with:
        1. Getting tech news from various categories (general tech, AI/ML, startups, cybersecurity, mobile, gaming)
        2. Searching for specific tech news topics
        3. Getting trending tech stories
        4. Finding news about specific companies

        When users ask about tech news, use the available tools to fetch real-time news data.
        Format the results in a clear, readable way for the user.
        For non-news questions, respond conversationally as a helpful AI assistant.
        """;

    public TechNewsBot(AgentApplicationOptions options, Kernel kernel, TechNewsMcpService mcpService) : base(options)
    {
        _kernel = kernel ?? throw new ArgumentNullException(nameof(kernel));
        _mcpService = mcpService ?? throw new ArgumentNullException(nameof(mcpService));

        OnConversationUpdate(ConversationUpdateEvents.MembersAdded, WelcomeMessageAsync);
        OnActivity(ActivityTypes.Message, MessageActivityAsync, rank: RouteRank.Last);
    }

    protected async Task MessageActivityAsync(ITurnContext turnContext, ITurnState turnState, CancellationToken cancellationToken)
    {
        var userMessage = turnContext.Activity.Text ?? string.Empty;

        await turnContext.StreamingResponse.QueueInformativeUpdateAsync("Working on a response for you");

        var chatHistory = turnState.GetValue("conversation.chatHistory", () => new ChatHistory(SystemPrompt));
        chatHistory.AddUserMessage(userMessage);

        // Ensure MCP client is connected
        if (!_mcpService.IsConnected)
        {
            await _mcpService.ConnectAsync();
        }

        // Register the TechNews plugin with the kernel
        var kernelClone = _kernel.Clone();
        kernelClone.Plugins.Add(KernelPluginFactory.CreateFromObject(new TechNewsPlugin(_mcpService)));

        var chatCompletion = kernelClone.GetRequiredService<IChatCompletionService>();

        var executionSettings = new OpenAIPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        var response = await chatCompletion.GetChatMessageContentAsync(
            chatHistory,
            executionSettings,
            kernelClone,
            cancellationToken);

        chatHistory.Add(response);
        turnState.SetValue("conversation.chatHistory", chatHistory);

        turnContext.StreamingResponse.QueueTextChunk(response.Content ?? "Sorry, I couldn't generate a response.");
        await turnContext.StreamingResponse.EndStreamAsync(cancellationToken);
    }

    protected async Task WelcomeMessageAsync(ITurnContext turnContext, ITurnState turnState, CancellationToken cancellationToken)
    {
        foreach (ChannelAccount member in turnContext.Activity.MembersAdded)
        {
            if (member.Id != turnContext.Activity.Recipient.Id)
            {
                await turnContext.SendActivityAsync(
                    MessageFactory.Text(
                        "Hi there! I'm an AI agent that can chat with you and provide tech news. " +
                        "I can help you get tech news from various categories, search tech topics, " +
                        "and find company news."),
                    cancellationToken);
            }
        }
    }
}

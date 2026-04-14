# TechPulse News Agent (C#)

## Summary

TechPulse is an intelligent tech news companion that delivers the latest technology news, trends, and insights from trusted sources in the industry. Built with Microsoft 365 Agents SDK and Semantic Kernel, this agent provides real-time access to tech news across multiple categories including AI/ML, startups, cybersecurity, mobile technology, and gaming. The agent understands natural language queries and can search for specific topics, provide trending tech news, and deliver company-specific updates from major tech players like Microsoft, Apple, Google, and more.

![Tech Pulse News](./assets/techPulse.gif)

## Version history

Version|Date|Comments
-------|----|--------
1.0|September 26, 2025|Initial release

## Prerequisites

* Microsoft 365 tenant with Microsoft 365 Copilot
* [.NET 10 SDK](https://dotnet.microsoft.com/download)
* [Visual Studio 2022](https://visualstudio.microsoft.com/) or later with the ASP.NET and web development workload
* A [Microsoft 365 account for development](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts)
* [Microsoft 365 Agents Toolkit for Visual Studio](https://learn.microsoft.com/en-us/microsoft-365/agents-sdk/create-new-toolkit-project-vs) latest version
* [Microsoft 365 Copilot license](https://learn.microsoft.com/microsoft-365-copilot/extensibility/prerequisites#prerequisites)
* An [OpenAI API key](https://platform.openai.com/) for general chat functionality
* A [NewsAPI key](https://newsapi.org/) for real-time tech news data

## Quick Start

### Debug agent in Microsoft 365 Agents Playground
1. Ensure your API keys are filled in `cea-techPulse-csharp/appsettings.Playground.json`:
    ```json
    "OpenAI": {
      "ApiKey": "<your-openai-api-key>"
    },
    "NewsApi": {
      "ApiKey": "<your-newsapi-key>"
    }
    ```
2. Set `Startup Item` as `Microsoft 365 Agents Playground (browser)`.
3. Press F5, or select the Debug > Start Debugging menu in Visual Studio.
4. In Microsoft 365 Agents Playground from the launched browser, try asking:
   * "Latest AI news"
   * "What's trending in tech?"
   * "News about Microsoft"
   * "Search for cybersecurity updates"

### Debug agent in Teams Web Client
1. Ensure your API keys are filled in `M365Agent/env/.env.local.user`:
    ```
    SECRET_OPENAI_API_KEY="<your-openai-api-key>"
    SECRET_NEWS_API_KEY="<your-newsapi-key>"
    ```
2. In the debug dropdown menu, select Dev Tunnels > Create A Tunnel (set authentication type to Public) or select an existing public dev tunnel.
3. Right-click the 'M365Agent' project in Solution Explorer and select **Microsoft 365 Agents Toolkit > Select Microsoft 365 Account**
4. Sign in to Microsoft 365 Agents Toolkit with a **Microsoft 365 work or school account**
5. Set `Startup Item` as `Microsoft Teams (browser)`.
6. Press F5, or select Debug > Start Debugging menu in Visual Studio to start your app
7. In the opened web browser, select Add button to install the app in Teams
8. In the chat bar, ask about tech news to get real-time results.

## Features

Using this sample you can extend Microsoft 365 Copilot with an agent that:

* Provides real-time tech news from trusted sources across multiple categories (AI, startups, cybersecurity, mobile, gaming)
* Searches for specific tech topics and keywords using natural language queries
* Delivers company-specific news about major tech companies (Microsoft, Apple, Google, Tesla, etc.)
* Shows trending topics in technology
* Uses Semantic Kernel plugins for intelligent news data retrieval
* Understands various natural language ways of asking for news

### Example Queries

#### Category-based News

* "Latest AI news" or "AI updates"
* "Startup news" or "venture capital news"
* "Cybersecurity headlines"
* "Mobile technology news"
* "Gaming news" or "esports updates"

#### Company-specific News

* "News about Microsoft"
* "Apple updates"
* "What's happening with Google?"
* "Tesla news"

#### Search & Trending

* "Search for blockchain news"
* "What's trending in tech?"
* "Popular tech topics"
* "Find news about machine learning"

## What's included in the template

| Folder       | Contents                                            |
| - | - |
| `.vscode/`   | VS Code files for debugging                         |
| `M365Agent/appPackage/` | Templates for the Teams application manifest |
| `M365Agent/env/`       | Environment files                             |
| `M365Agent/infra/`     | Templates for provisioning Azure resources    |
| `cea-techPulse-csharp/` | The source code for the application           |

The following files can be customized and demonstrate an example implementation to get you started.

| File                                 | Contents                                           |
| - | - |
|`cea-techPulse-csharp/Bot/TechNewsBot.cs`| Handles the agent app logic with tech news integration, built with Microsoft 365 Agents SDK and Semantic Kernel.|
|`cea-techPulse-csharp/Bot/Plugins/TechNewsPlugin.cs`| Semantic Kernel plugin exposing tech news tools.|
|`cea-techPulse-csharp/Services/TechNewsService.cs`| Service for fetching tech news from NewsAPI.|
|`cea-techPulse-csharp/Config.cs`| Defines configuration options.|
|`cea-techPulse-csharp/Program.cs`| Hosts the agent using ASP.NET Core.|

## Help

We do not support samples, but this community is always willing to help, and we want to improve these samples. We use GitHub to track issues, which makes it easy for community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues?q=label%3A%22sample%3A%20cea-techPulse-csharp%22) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

## Additional information and references

- [Microsoft 365 Agents SDK](https://github.com/microsoft/Agents)
- [Microsoft 365 Agents Toolkit Documentations](https://docs.microsoft.com/microsoftteams/platform/toolkit/teams-toolkit-fundamentals)
- [Microsoft 365 Agents Toolkit CLI](https://aka.ms/teamsfx-toolkit-cli)
- [Microsoft 365 Agents Toolkit Samples](https://github.com/OfficeDev/TeamsFx-Samples)
- [Semantic Kernel](https://github.com/microsoft/semantic-kernel)

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

![visitor stats](https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/samples/cea-techpulse-csharp)

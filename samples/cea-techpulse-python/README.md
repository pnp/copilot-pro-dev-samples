# TechPulse News Agent (Python)

## Summary

TechPulse is an intelligent tech news companion that delivers the latest technology news, trends, and insights from trusted sources in the industry. Built with Microsoft 365 Agents SDK and powered by Model Context Protocol (MCP), this agent provides real-time access to tech news across multiple categories including AI/ML, startups, cybersecurity, mobile technology, and gaming. The agent understands natural language queries and can search for specific topics, provide trending tech news, and deliver company-specific updates from major tech players like Microsoft, Apple, Google, and more.

![Tech Pulse News](./assets/techPulse.gif)

## Version history

Version|Date|Comments
-------|----|--------
1.0|September 26, 2025|Initial release

## Prerequisites

* Microsoft 365 tenant with Microsoft 365 Copilot
* [Python](https://www.python.org/), version 3.10 or higher
* [Python extension](https://code.visualstudio.com/docs/languages/python), version v2024.0.1 or higher
* A [Microsoft 365 account for development](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts)
* [Microsoft 365 Agents Toolkit Visual Studio Code Extension](https://aka.ms/teams-toolkit) latest version or [Microsoft 365 Agents Toolkit CLI](https://aka.ms/teams-toolkit-cli)
* [Microsoft 365 Copilot license](https://learn.microsoft.com/microsoft-365-copilot/extensibility/prerequisites#prerequisites)
* An [OpenAI API key](https://platform.openai.com/) for general chat functionality
* A [NewsAPI key](https://newsapi.org/) for real-time tech news data

## Minimal path to awesome

* Clone this repository (or [download this solution as a .ZIP file](https://pnp.github.io/download-partial/?url=https://github.com/pnp/copilot-pro-dev-samples/tree/main/samples/cea-techpulse-python) then unzip it)
* Open the command box and enter `Python: Create Environment` to create and activate your desired virtual environment. Remember to select `src/requirements.txt` as dependencies to install when creating the virtual environment.
* Select the Microsoft 365 Agents Toolkit icon on the left in the VS Code toolbar
* In the Account section, sign in with your [Microsoft 365 account](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts) if you haven't already
* In file `env/.env.local.user`, fill in your API keys:
  * `SECRET_OPENAI_API_KEY=<your-openai-key>`
  * `SECRET_NEWS_API_KEY=<your-newsapi-key>`
* Create Teams app by selecting **Provision** in "Lifecycle" section
* Select **Preview in Copilot (Edge)** or **Preview in Copilot (Chrome)** from the launch configuration dropdown, or use **Debug in Microsoft 365 Agents Playground** for local testing
* Once the agent is loaded, you can ask questions like:
  * "Latest AI news"
  * "What's trending in tech?"
  * "News about Microsoft"
  * "Search for cybersecurity updates"
* The agent will respond with real-time tech news data and can handle both specific news requests and general conversations

## Features

Using this sample you can extend Microsoft 365 Copilot with an agent that:

* Provides real-time tech news from trusted sources across multiple categories (AI, startups, cybersecurity, mobile, gaming)
* Searches for specific tech topics and keywords using natural language queries
* Delivers company-specific news about major tech companies (Microsoft, Apple, Google, Tesla, etc.)
* Shows trending topics in technology
* Uses Model Context Protocol (MCP) for efficient news data retrieval
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
| `appPackage/` | Templates for the Teams application manifest        |
| `env/`       | Environment files                                   |
| `infra/`     | Templates for provisioning Azure resources          |
| `src/`       | The source code for the application                 |

The following files can be customized and demonstrate an example implementation to get you started.

| File                                 | Contents                                           |
| - | - |
|`src/agent.py`| Handles the agent app logic with tech news MCP integration, built with Microsoft 365 Agents SDK.|
|`src/config.py`| Defines the environment variables.|
|`src/app.py`| Hosts the agent using aiohttp.|
|`src/tech_news_mcp_service.py`| MCP client service that connects to the tech news MCP server.|
|`src/mcpserver/tech_news.py`| MCP server providing tech news tools (get news, search, trending, company news).|

## Help

We do not support samples, but this community is always willing to help, and we want to improve these samples. We use GitHub to track issues, which makes it easy for community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues?q=label%3A%22sample%3A%20cea-techpulse-python%22) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

## Additional information and references

- [Microsoft 365 Agents Toolkit Documentations](https://docs.microsoft.com/microsoftteams/platform/toolkit/teams-toolkit-fundamentals)
- [Microsoft 365 Agents Toolkit CLI](https://aka.ms/teamsfx-toolkit-cli)
- [Microsoft 365 Agents Toolkit Samples](https://github.com/OfficeDev/TeamsFx-Samples)
- [Microsoft 365 Agents SDK](https://github.com/microsoft/Agents)
- [Microsoft 365 Agents for Python](https://github.com/microsoft/Agents-for-python)
- [Microsoft 365 Agents SDK QuickStart](https://github.com/microsoft/Agents/tree/main/samples/python/quickstart)

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

![visitor stats](https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/samples/cea-techpulse-python)

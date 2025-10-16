# Overview of the Custom Engine Agent "TechPulseNews"

The custom engine agent "TechPulse" acts as your intelligent tech news companion, delivering the latest technology news, trends, and insights from the most trusted sources in the industry. Built with Microsoft 365 Agents SDK and powered by Model Context Protocol (MCP), this agent provides real-time access to tech news across multiple categories including AI/ML, startups, cybersecurity, mobile technology, and gaming. The agent understands natural language queries and can search for specific topics, provide trending tech news, and deliver company-specific updates from major tech players like Microsoft, Apple, Google, and more.

![Tech Pulse News](./assets/techPulse.gif)

> **Prerequisites**
>
> To run this app template in your local dev machine, you will need:
>
> - [Node.js](https://nodejs.org/), supported versions: 18, 20, 22
> - A [Microsoft 365 account for development](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts).
> - [Microsoft 365 Agents Toolkit Visual Studio Code Extension](https://aka.ms/teams-toolkit) version 5.0.0 and higher
> - [Microsoft 365 Copilot license](https://learn.microsoft.com/microsoft-365-copilot/extensibility/prerequisites#prerequisites) (for Copilot integration)
> - An [OpenAI API key](https://platform.openai.com/) for general chat functionality
> - A [NewsAPI key](https://newsapi.org/) for real-time tech news data

1. First, select the Microsoft 365 Agents Toolkit icon on the left in the VS Code toolbar.
2. In the Account section, sign in with your [Microsoft 365 account](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts) if you haven't already.
3. In file *env/.env.local.user*, fill in your API keys:
   - `SECRET_OPENAI_API_KEY=<your-openai-key>`
   - `SECRET_NEWS_API_KEY=<your-newsapi-key>`
4. Create Teams app by clicking `Provision` in "Lifecycle" section.
5. Select `Preview in Copilot (Edge)` or `Preview in Copilot (Chrome)` from the launch configuration dropdown, or use `Debug in Microsoft 365 Agents Playground` for local testing.
6. Once the agent is loaded, you can ask questions like:
   - "Latest AI news"
   - "What's trending in tech?"
   - "News about Microsoft"
   - "Search for cybersecurity updates"
7. The agent will respond with real-time tech news data and can handle both specific news requests and general conversations.

## Tech News Commands

Users can interact with the agent using natural language for various tech news queries:

### Category-based News

- "Latest AI news" or "AI updates"
- "Startup news" or "venture capital news"
- "Cybersecurity headlines"
- "Mobile technology news"
- "Gaming news" or "esports updates"

### Company-specific News

- "News about Microsoft"
- "Apple updates"
- "What's happening with Google?"
- "Tesla news"

### Search & Trending

- "Search for blockchain news"
- "What's trending in tech?"
- "Popular tech topics"
- "Find news about machine learning"

### General Queries

- "Latest tech headlines"
- "Tech industry updates"
- "Innovation news"
- "Technology breakthroughs"

## Features

- **Real-time Tech News**: Latest technology news from trusted sources
- **Category Filtering**: AI, startups, cybersecurity, mobile, gaming
- **Company News**: Specific news about major tech companies
- **Search Functionality**: Search for specific tech topics and keywords
- **Trending Topics**: Get what's currently trending in technology
- **MCP Integration**: Uses Model Context Protocol for efficient news data retrieval
- **Natural Language Processing**: Understands various ways of asking for news

## Addition information and references

- [Microsoft 365 Agents SDK](https://github.com/Microsoft/Agents)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Microsoft 365 Agents Toolkit](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/overview-custom-engine-agent)
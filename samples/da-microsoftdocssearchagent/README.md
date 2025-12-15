# Declarative Agent + MCP in VS Code 

This agent assists users in finding technical information on Microsoft Learn Documentation.

Microsoft Learn Search Agent - a declarative Microsoft 365 agent that helps users query Microsoft Learn and MCP servers, answer developer questions (SPFx, Microsoft Graph, etc.),  I have added CodeInterpreter and GraphicArt capabilities to do creative options performing code/graphics tasks. 

## Example

![Preview of the agent](/assets/preview.png)

## Version history

Version|Date|Comments|Author|
-------|----|--------|------|
1.0|15th December 2025| Initial release | Paul Bullock |

## Get started

> **Prerequisites**
>
> To run this app template in your local dev machine, you will need:
>
> - [Node.js](https://nodejs.org/), supported versions: 18, 20, 22
> - A [Microsoft 365 account for development](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts).
> - [Microsoft 365 Agents Toolkit Visual Studio Code Extension](https://aka.ms/teams-toolkit) version 5.0.0 and higher or [Microsoft 365 Agents Toolkit CLI](https://aka.ms/teamsfx-toolkit-cli)
> - [Microsoft 365 Copilot license](https://learn.microsoft.com/microsoft-365-copilot/extensibility/prerequisites#prerequisites)

1. Open ATK in VS Code

    Click the Microsoft 365 Agents Toolkit icon in the Activity Bar. 

2. Sign in

    Open the Agents Toolkit by click on the toolkit icon in the VS Code sidebar. Under Account, authenticate with your dev M365 account.

3. Provision & debug

    Use the Provision button in ATK to create resources. ATK will detect if your MCP server requires OAuth2 or API‐Key. Provide your Client ID/Secret or Key when prompted. Then Start Debugging to Preview agent in Copilot in Edge/Chrome. Your DA will appear under Copilot chats.

4. Test your MCP‑powered agent 

    Open the Copilot pane, select your agent and invoke any of the MCP tools with natural‑language prompts. 


## Learn More

- [Build Declarative Agents (official docs)](https://learn.microsoft.com/microsoft-365-copilot/extensibility/build-declarative-agents)

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)

- [Agents Toolkit guide on GitHub](https://github.com/OfficeDev/TeamsFx/wiki/Teams-Toolkit-Visual-Studio-Code-v5-Guide#overview)

## Help

We do not support samples, but this community is always willing to help, and we want to improve these samples. We use GitHub to track issues, which makes it easy for community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

![visitor stats](https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/samples/da-microsoftdocssearchagent)

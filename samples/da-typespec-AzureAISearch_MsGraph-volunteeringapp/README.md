# Declarative Agent with TypeSpec connecting to Azure AI Search and Ms Graph with Volunteering App as an example

![Declarative Agent - Volunteering App](./assets/example.gif)

## Summary

This declarative agent is replicating existing sample [Declarative Agent - Volunteering App](https://pnp.github.io/download-partial/?url=https://github.com/pnp/copilot-pro-dev-samples/tree/main/samples/da-da-volunteeringapp) showcasing how to use multi API plugins with OAuth 2 and APIKey authentication using TypeSpec to strealine the development process. The sample covers a sample volunteering app that can be used to automate the process of finding and applying for volunteer opportunities. The agent will first ask what kind of volunteering you wish to do. Once decided it will submit your application to the selected opportunity. A key point of emphasis on this agent was making use of multiple Microsoft services using different APIs. The agent uses Microsoft Graph API to get the list of tasks assigned to the user and Azure AI Search to get the list of volunteer opportunities.

View these two blogs for more info how to set up Azure AI Search API plugin and Ms Graph API plugin.

- [Build Microsoft 365 Copilot Agents That Connect to SharePoint with TypeSpec and OAuth](https://reshmeeauckloo.com/posts/declarativeagents-msgraph-typespec-createandlist-sp-items/)
- [Declarative Agents: Azure OpenAI API Key Auth with TypeSpec](https://reshmeeauckloo.com/posts/declarativeagents-azure-open-ai-apikey-typespec/)

## Contributors

* [Reshmee Auckloo](https://github.com/reshmee011) - M365 Development MVP

## Version history

Version|Date|Comments
-------|----|--------
1.0 | October 01, 2025 | Initial solution

> **Prerequisites**
>
> To run this app template in your local dev machine, you will need:
>
> - [Node.js](https://nodejs.org/), supported versions: 18, 20, 22
> - A [Microsoft 365 account for development](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts).
> - [Microsoft 365 Agents Toolkit Visual Studio Code Extension](https://aka.ms/teams-toolkit) version 5.0.0 and higher or [Microsoft 365 Agents Toolkit CLI](https://aka.ms/teamsfx-toolkit-cli)
> * [Azure AI Search](https://learn.microsoft.com/azure/search/search-what-is-azure-search) service with indexed data from the assets folder.
> * A SharePoint site with a list using the **Issue Tracker** template


1. First, select the Microsoft 365 Agents Toolkit icon on the left in the VS Code toolbar.
2. In the Account section, sign in with your [Microsoft 365 account](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts) if you haven't already.
3. Run `npm install` to install dependencies before working with TypeSpec files.
4. Update the [`main.tsp`](./main.tsp), [`AISearchActions.tsp`](./aiSearchactions.tsp),[`msGraphactions.tsp`](./msGraphactions.tsp) following the instructions from minimal path to awesome to configure your agent and instructions. These are the TypeSpec files. 
5. Create app by clicking `Provision` in "Lifecycle" section.
6. Select `Preview in Copilot (Edge)` or `Preview in Copilot (Chrome)` from the launch configuration dropdown.
7. Once the Copilot agent is loaded in the browser, click on the "…" menu and select "Copilot chats". You will see your declarative agent on the right rail. Clicking on it will change the experience to showcase the logo and name of your declarative agent.
8. Ask a question to your declarative agent and it should respond based on the instructions provided.


![image](./assets/image.png)

## Minimal path to awesome

1. Clone this repository (or [download this solution as a .ZIP file](https://pnp.github.io/download-partial/?url=https://github.com/pnp/copilot-pro-dev-samples/tree/main/samples/da-typespec-AzureAISearch_MsGraph-volunteeringapp) then unzip it)

2. Register an EntraID application in Azure:

    1. Go to [Azure portal](https://portal.azure.com/)
    2. Select **Microsoft Entra ID** > **Manage** > **App registrations** > **New registration**
    3. Enter a name for the app (e.g., Volunteering App)
    4. Select **Accounts in this organizational directory only**
    5. Under **Redirect URI**, select **Web** and enter `https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect`
    6. Select **Register**
    7. In the app registration, go to **Certificates & secrets** and create a new client secret
    8. Copy the client secret value
    9. In the app registration, go to **API permissions** and add the following permissions:
        * **Microsoft Graph** > **Delegated permissions** > `Directory.Read.All`, `Sites.ReadWrite.All`, `User.Read`
    10. Select **Grant admin consent for <your organization>** to grant the permissions

3. Get a copy your Endpoint URL from the Azure AI Search service:

   1. Go to [Azure portal](https://portal.azure.com/)
   2. Find or create your instance under **Azure AI Search**
   3. Under **Overview**, copy the **URL** value. It should look like `https://<your-search-service-name>.search.windows.net/`
   4. Under **Keys**, copy the **Primary Key** value

4. In the [Teams developer portal](https://dev.teams.microsoft.com/) under **Tools**, create a new **OAuth client registration** with the following information (replace `tenantid` with your own value):

    **App settings**

    * **Registration name**: Volunteering App
    * **Base URL**: `https://graph.microsoft.com/v1.0`
    * **Restrict usage by org**: My organization only
    * **Restrict usage by app**: Any Teams app (when agent is deployed, use the Teams app ID)

    **OAuth settings**
    * **Client ID**: &lt;Entra ID App registration client ID&gt;
    * **Client secret**: &lt;Entra ID App registration client secret&gt;
    * **Authorization endpoint**: <https://login.microsoftonline.com/tenantid/oauth2/v2.0/authorize>
    * **Token endpoint**: <https://login.microsoftonline.com/tenantid/oauth2/v2.0/token>
    * **Refresh endpoint**: <https://login.microsoftonline.com/tenantid/oauth2/v2.0/refresh>
    * **Scope**: `Directory.Read.All`, `Sites.ReadWrite.All`, `User.Read`

    Save the information. A new **OAuth client registration key** will be generated. Copy the key.

5. Staying in the [Teams developer portal](https://dev.teams.microsoft.com/) under **Tools**, create a new **API key registration** with the following information:

    * **API key**: Add a secret with the Azure AI Primary Key you copied in step 3.4
    * **API key name**: e.g., Azure AI Search Key
    * **Base URL**: The Azure AI Search URL you copied in step 3.3
    * **Target tenant**: Home tenant
    * **Restrict usage by app**: Any Teams app (when agent is deployed, use the Teams app ID)

    Save the information. A new **API key registration ID** will be generated. Copy the key.

6. Rename the `.env.dev.example` file to `.env.dev` and update the following values:

    ```bash
    # Built-in environment variables
    TEAMSFX_ENV=dev
    APP_NAME_SUFFIX=dev

    TEAMS_APP_ID=082eb662-19a0-40a0-801a-4eeeae8ecac3
    TEAMS_APP_TENANT_ID=<your-tenant-id>
    M365_TITLE_ID=
    M365_APP_ID=

    TASKITEMSAGENTAUTH_REGISTRATION_ID=<oauth-client-registration-id-from-teams-developer-portal>
    APIKEYAUTH_REGISTRATION_ID=<api-key-registration-id-from-teams-developer-portal>
    ```

7. Update those within file [`msGraphactions.tsp`](./msGraphactions.tsp) 

```
  const SITE_ID = "contoso.sharepoint.com,000d0ad0-000f-000d-0000-0000a000c0cf0,0b00c000-000a-0f0a-00dc-00000000ebe0
";
  const LIST_ID = "cb000b0f-0af0-00ad-ec00d0ae0";
```


8. Update the server_URL [`aiSearchactions.tsp`](./msGraphactions.tsp)

```dotnetcli
   const SERVER_URL = "https://<AI_SEARCH_ENDPOINT>.windows.net";
```

9. From Teams Toolkit, sign-in to your Microsoft 365 account.

10. From Teams Toolkit, provision the solution to create the Teams app.

11. Go to [https://www.office.com/chat?auth=2](https://www.office.com/chat?auth=2) URL and enable the developer mode by using the `-developer on` prompt.

12. Use one of the conversation starters to start the agent.

## Features

The following sample demonstrates the following concepts:

* Query the Microsoft Graph API to get the list of tasks assigned to the user
* Query Azure AI Search to get the list of volunteer opportunities
* Register the user to the selected opportunity

## Demo 

[![Demo Video](./assets/video-thumbnail.jpg)](https://www.youtube.com/watch?v=h8wPL_ZUmC0 "Declarative agent for volunteering app")

<!--
RESERVED FOR REPO MAINTAINERS

We'll add the video from the community call recording here

## Video

[![YouTube video title](./assets/video-thumbnail.jpg)](https://www.youtube.com/watch?v=XXXXX "YouTube video title")
-->

## What's included in the template

| Folder       | Contents                                                                                 |
| ------------ | ---------------------------------------------------------------------------------------- |
| `.vscode`    | VSCode files for debugging                                                               |
| `appPackage` | Templates for the application manifest, the GPT manifest and the API specification |
| `env`        | Environment files                                                                        |


The following are Microsoft 365 Agents Toolkit specific project files. You can [visit a complete guide on Github](https://github.com/OfficeDev/TeamsFx/wiki/Teams-Toolkit-Visual-Studio-Code-v5-Guide#overview) to understand how Microsoft 365 Agents Toolkit works.

| File           | Contents                                                                                                                                  |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `m365agents.yml` | This is the main Microsoft 365 Agents Toolkit project file. The project file defines two primary things: Properties and configuration Stage definitions. |

The following are TypeSpec template files. You need to customize these files to configure your agent.

| File          | Contents                                                                                    |
| ------------- | ------------------------------------------------------------------------------------------- |
| `main.tsp`    | This is the root file of TSP files. Please manually update this file to add your own agent. |
| `aiSearchactions.tsp` | This is the actions file containing API endpoints for Azure AI Search to extend your declarative agent. |
| `msGraphactions.tsp` | This is the actions file containing API endpoints for Ms Graph API to extend your declarative agent. |

## Extend the template

- [Add conversation starters](https://learn.microsoft.com/microsoft-365-copilot/extensibility/build-declarative-agents?tabs=ttk&tutorial-step=3): Conversation starters are hints that are displayed to the user to demonstrate how they can get started using the declarative agent.
- [Add web content](https://learn.microsoft.com/microsoft-365-copilot/extensibility/build-declarative-agents?tabs=ttk&tutorial-step=4) for the ability to search web information.
- [Add OneDrive and SharePoint content](https://learn.microsoft.com/microsoft-365-copilot/extensibility/build-declarative-agents?tabs=ttk&tutorial-step=5) as grounding knowledge for the agent.
- [Add Microsoft Copilot Connectors content](https://learn.microsoft.com/microsoft-365-copilot/extensibility/build-declarative-agents?tabs=ttk&tutorial-step=6) to ground agent with enterprise knowledge.

## Addition information and references

- [Declarative agents for Microsoft 365](https://aka.ms/teams-toolkit-declarative-agent)

## Help

We do not support samples, but this community is always willing to help, and we want to improve these samples. We use GitHub to track issues, which makes it easy for  community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues?q=label%3A%22sample%3A%20da-volunteeringapp%22) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

<img src="https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/samples/da-typespec-AzureAISearch_MsGraph-volunteeringapp" />

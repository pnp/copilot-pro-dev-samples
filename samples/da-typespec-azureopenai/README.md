# Azure Open API Agent using TypeSpec for Microsoft 365 Copilot

## Summary

The sample is designed to demonstrate how to integrate Azure OpenAI services using TypeSpec. It provides a template for building conversational agents or plugins that leverage Azure OpenAI's capabilities, such as natural language processing and generative AI, within Microsoft Teams or other environments. 

## Get started with the template

> **Prerequisites**
>
> To run this app template in your local dev machine, you will need:
>
> - [Node.js](https://nodejs.org/), supported versions: 18, 20, 22
> - A [Microsoft 365 account for development](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts).
> - [Microsoft 365 Agents Toolkit Visual Studio Code Extension](https://aka.ms/teams-toolkit) version 5.0.0 and higher or [Microsoft 365 Agents Toolkit CLI](https://aka.ms/teamsfx-toolkit-cli)
> - [Microsoft 365 Copilot license](https://learn.microsoft.com/microsoft-365-copilot/extensibility/prerequisites#prerequisites)


## Minimal path to awesome

1. Clone this repository or [download this solution as a .ZIP file](https://pnp.github.io/download-partial/?url=https://github.com/pnp/copilot-pro-dev-samples/tree/main/samples/da-typespec-azureopenai) then unzip it.

2. Get a copy your Endpoint URL and KEY from the Azure OpenAI resource:

   - Go to [Azure portal](https://portal.azure.com/)
   - Find or create your instance under **Azure OpenAI** resource
   - Create a deployment, e.g 'gpt-4o'
   - Under **Overview**, copy the **Azure OpenAI** endpoint value. It should look like `https://<your-azure-openai-service>.openai.azure.com//`
   - Under **Keys and Endpoint**, copy the **KEY 1** value

3. In the [Teams developer portal](https://dev.teams.microsoft.com/) under **Tools**, create a new **API Key registration** with the following information:

    * **API key**: Add a secret with the Azure OpenAI Key you copied in step 2
    * **API key name**: e.g., Azure OpenAI Key Name
    * **Base URL**: The Azure OpenAI Endpoint URL you copied in step 2
    * **Target tenant**: Home tenant
    * **Restrict usage by app**: Any Teams app (when agent is deployed, use the Teams app ID)

Save the information. A new **API key registration ID** will be generated. Copy the key.

4. Rename the `.env.dev.example` file to `.env.dev` and update the following values:

Replace {keyAPIRegistration} with the key copied in previous step

    ```bash
    # Built-in environment variables
    TEAMSFX_ENV=dev
    APP_NAME_SUFFIX=dev

    # Generated during provision, you can also add your own variables.
    TEAMS_APP_ID=
    TEAMS_APP_TENANT_ID=
    M365_TITLE_ID=
    M365_APP_ID=

    # Update own variables.
    APIKEYAUTH_REGISTRATION_ID={keyAPIRegistration}
    ```
5. Update the instructions and agent details within the `main.tsp` as appropriate for your use case.
6. Update SERVER_URL, MODEL and other hard coded parameters in `actions.tsp`


7. From Teams Toolkit, sign-in to your Microsoft 365 account.
8. From Teams Toolkit, provision the solution to create the Teams app.
9. Go to [https://www.office.com/chat?auth=2](https://www.office.com/chat?auth=2) URL and enable the developer mode by using the `-developer on` prompt.
10. Use one of the conversation starters to start the agent.

![solution](./assets/action_queryOpenAI.gif)

## What's included in the template

| Folder       | Contents                                                                                 |
| ------------ | ---------------------------------------------------------------------------------------- |
| `.vscode`    | VSCode files for debugging                                                               |
| `appPackage` | Templates for the application manifest, the GPT manifest and the API specification |
| `env`        | Environment files                                                                        |

The following files can be customized and demonstrate an example implementation to get you started.

| File                               | Contents                                                                     |
| ---------------------------------- | ---------------------------------------------------------------------------- |
| `appPackage/manifest.json`         | application manifest that defines metadata for your declarative agent. |

The following are Microsoft 365 Agents Toolkit specific project files. You can [visit a complete guide on Github](https://github.com/OfficeDev/TeamsFx/wiki/Teams-Toolkit-Visual-Studio-Code-v5-Guide#overview) to understand how Microsoft 365 Agents Toolkit works.

| File           | Contents                                                                                                                                  |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `m365agents.yml` | This is the main Microsoft 365 Agents Toolkit project file. The project file defines two primary things: Properties and configuration Stage definitions. |

The following are TypeSpec template files. You need to customize these files to configure your agent.

| File          | Contents                                                                                    |
| ------------- | ------------------------------------------------------------------------------------------- |
| `main.tsp`    | This is the root file of TSP files. Please manually update this file to add your own agent. |
| `actions.tsp` | This is the actions file containing API endpoints to extend your declarative agent.         |

## Extend the template

- [Add conversation starters](https://learn.microsoft.com/microsoft-365-copilot/extensibility/build-declarative-agents?tabs=ttk&tutorial-step=3): Conversation starters are hints that are displayed to the user to demonstrate how they can get started using the declarative agent.
- [Add web content](https://learn.microsoft.com/microsoft-365-copilot/extensibility/build-declarative-agents?tabs=ttk&tutorial-step=4) for the ability to search web information.
- [Add OneDrive and SharePoint content](https://learn.microsoft.com/microsoft-365-copilot/extensibility/build-declarative-agents?tabs=ttk&tutorial-step=5) as grounding knowledge for the agent.
- [Add Microsoft Copilot Connectors content](https://learn.microsoft.com/microsoft-365-copilot/extensibility/build-declarative-agents?tabs=ttk&tutorial-step=6) to ground agent with enterprise knowledge.

## Help

We do not support samples, but this community is always willing to help, and we want to improve these samples. We use GitHub to track issues, which makes it easy for  community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues?q=label%3A%22sample%3A%20da-typespec-github%22) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

## Addition information and references

- [Declarative agents for Microsoft 365](https://aka.ms/teams-toolkit-declarative-agent)

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

![](https://m365-visitor-stats.azurewebsites.net/SamplesGallery/da-typespec-azureopenai)
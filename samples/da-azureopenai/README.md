# Overview of the basic declarative agent with API plugin template

## Build a basic declarative agent with API plugin

With the declarative agent, you can build a custom version of Copilot that can be used for specific scenarios, such as for specialized knowledge, implementing specific processes, or simply to save time by reusing a set of AI prompts. For example, a grocery shopping Copilot declarative agent can be used to create a grocery list based on a meal plan that you send to Copilot.

You can extend declarative agents using plugins to retrieve data and execute tasks on external systems. A declarative agent can utilize multiple plugins at the same time.

![image](https://github.com/user-attachments/assets/9939972e-0449-410c-b237-d9d748cd6628)


## Get started with the template

> **Prerequisites**
>
> To run this app template in your local dev machine, you will need:
>
> - [Node.js](https://nodejs.org/), supported versions: 18, 20, 22
> - A [Microsoft 365 account for development](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts).
> - [Teams Toolkit Visual Studio Code Extension](https://aka.ms/teams-toolkit) version 5.0.0 and higher or [Teams Toolkit CLI](https://aka.ms/teamsfx-toolkit-cli)
> - [Microsoft 365 Copilot license](https://learn.microsoft.com/microsoft-365-copilot/extensibility/prerequisites#prerequisites)
> - [Azure AI Services]

## Minimal path to awesome

1. Clone this repository (or [download this solution as a .ZIP file](https://pnp.github.io/download-partial/?url=https://github.com/pnp/copilot-pro-dev-samples/tree/main/samples/da-da-azureopenai) then unzip it)

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
    MODEL=gpt-4o
    API_VERSION=2025-01-01-preview
    TEMPERATURE=0.7
    MAX_TOKENS=800
    TOP_P=0.95
    FREQUENCY_PENALTY=0
    PRESENCE_PENALTY=0
    ```
5. Update the instruction.txt as appropriate for your use case.
6. Update OpenAI Spec Server API URL in `appPackage\apiSpecificationFile\openapi.yaml`

To ensure the OpenAPI specification correctly references your Azure OpenAI resource, update the server URL in the OpenAPI spec. This step is crucial for aligning the API calls with your deployed model and endpoint configuration.

Replace the placeholder server URL with the actual endpoint URL of your Azure OpenAI resource. For example:

```yaml
servers:
  - url: https://<your-resource-name>.openai.azure.com
    description: Azure OpenAI service endpoint
```

7. From Teams Toolkit, sign-in to your Microsoft 365 account.
8. From Teams Toolkit, provision the solution to create the Teams app.
9. Go to [https://www.office.com/chat?auth=2](https://www.office.com/chat?auth=2) URL and enable the developer mode by using the `-developer on` prompt.
10. Use one of the conversation starters to start the agent.

## What's included in the template

| Folder       | Contents                                     |
| ------------ | -------------------------------------------- |
| `.vscode`    | VSCode files for debugging                   |
| `appPackage` | Templates for the Teams application manifest, the plugin manifest and the API specification |
| `env`        | Environment files                            |

The following files can be customized and demonstrate an example implementation to get you started.

| File                                 | Contents                                                                       |
| ------------------------------------ | ------------------------------------------------------------------------------ |
| `appPackage/declarativeCopilot.json` | Define the behaviour and configurations of the declarative agent.            |
| `appPackage/manifest.json`           | Teams application manifest that defines metadata for your declarative agent. |

The following are Teams Toolkit specific project files. You can [visit a complete guide on Github](https://github.com/OfficeDev/TeamsFx/wiki/Teams-Toolkit-Visual-Studio-Code-v5-Guide#overview) to understand how Teams Toolkit works.

| File                 | Contents                                                                                                                                  |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `teamsapp.yml`       | This is the main Teams Toolkit project file. The project file defines two primary things: Properties and configuration Stage definitions. |

## Addition information and references

- [Declarative agents for Microsoft 365](https://aka.ms/teams-toolkit-declarative-agent)
- [Extend Microsoft 365 Copilot](https://aka.ms/teamsfx-copilot-plugin)
- [Message extensions for Microsoft 365 Copilot](https://learn.microsoft.com/microsoft-365-copilot/extensibility/overview-message-extension-bot)
- [Microsoft Graph Connectors for Microsoft 365 Copilot](https://learn.microsoft.com/microsoft-365-copilot/extensibility/overview-graph-connector)
- [Microsoft 365 Copilot extensibility samples](https://learn.microsoft.com/microsoft-365-copilot/extensibility/samples)
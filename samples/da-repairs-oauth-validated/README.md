# Instructions for local authentication setup

1. Provision the application for Dev; this will cause TTK to register an Entra ID application.

2. In **.vscode/tasks.json** comment out the tunnel URL generation so it looks like this:

~~~json
"version": "2.0.0",
"tasks": [
    {
        "label": "Start Teams App Locally",
        "dependsOn": [
            "Validate prerequisites",
            //"Start local tunnel",
            "Create resources",
            "Build project",
            "Start application"
        ],
        "dependsOrder": "sequence"
    },
    ...
~~~

3. Create a persistent tunnel and note the URL. In your **env/.env.local** file, replace the auto-generated value for OPENAPI_SERVER_URL with your persistent URL. It should look like this:

    ~~~text
    OPENAPI_SERVER_URL=https://your-url-here-7071.use.devtunnels.ms
    ~~~


4. In [Teams Developer Portal](https://dev.teams.microsoft.com) under "Tools" / "OAuth client registrations", find your new client registration and make a copy of it for local use. Using the copy:

    - Replace the Base URL with your persistent tunnel URL
    - Find the Client ID and copy it to your **env/.env.local** file
    - Find the tenant ID (it's the GUID in the Token endpoint field) and copy it into your **env/.env.local** file
    - Copy the OAuth client registration ID into your **env/.env.local** file
    - Add a line to **env/.env.local** and set API_SCOPE to "repairs_read"

    Your **env/.env.local** file should now contain these added lines (with your ID's in place)

    ~~~text
    # Values used not provided by TTK
    API_APPLICATION_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    API_TENANT_ID=yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
    API_SCOPE=repairs_read
    OAUTH2AUTHCODE_CONFIGURATION_ID=ODgzxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx=
    ~~~

5. In your project folder run this command:

    ~~~sh
    npm i jwt-validate
    ~~~

6. Add validation code to your Azure function (**src/functions/repairs.ts**):

    a. Near the top of the file, add these lines:

    ~~~typescript
    import { TokenValidator, ValidateTokenOptions, getEntraJwksUri } from 'jwt-validate';
    let validator: TokenValidator;
    ~~~


    b. Add the following code after the line `const assignedTo = req.query.get("assignedTo");`:

    ~~~typescript
    // Try to validate the token and get user's basic information
    try {
        const { API_APPLICATION_ID, API_TENANT_ID, API_SCOPE } = process.env;
        const token = req.headers.get("Authorization")?.split(" ")[1];
        if (token) {

            if (!validator) {
                const entraJwksUri = await getEntraJwksUri(API_TENANT_ID);
                validator = new TokenValidator({
                    jwksUri: entraJwksUri
                });
                console.log("Token validator created");
            }

            const options: ValidateTokenOptions = {
                audience: `${API_APPLICATION_ID}`,
                issuer: `https://login.microsoftonline.com/${API_TENANT_ID}/v2.0`,
                scp: [API_SCOPE]
            };

            const validToken = await validator.validateToken(token, options);

            const userId = validToken.oid;
            const userName = validToken.name;
            console.log(`Token is valid for user ${userName} (${userId})`);
        } else {
            console.error("No token found in request");
            throw (new Error("No token found in request"));
        }
    }
    catch (ex) {
        console.error(ex);
        return  {
            status: 401
        };
    }
    ~~~

# Overview of the declarative agent with API plugin template

## Build a declarative agent with an API Plugin from a new API with Azure Functions

With the declarative agent, you can build a custom version of Copilot that can be used for specific scenarios, such as for specialized knowledge, implementing specific processes, or simply to save time by reusing a set of AI prompts. For example, a grocery shopping Copilot declarative agent can be used to create a grocery list based on a meal plan that you send to Copilot.

You can extend declarative agents using plugins to retrieve data and execute tasks on external systems. A declarative agent can utilize multiple plugins at the same time.
![image](https://github.com/user-attachments/assets/9939972e-0449-410c-b237-d9d748cd6628)

## Get started with the template

> **Prerequisites**
>
> To run this app template in your local dev machine, you will need:
>
> - [Node.js](https://nodejs.org/), supported versions: 18
> - A [Microsoft 365 account for development](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts)
> - [Teams Toolkit Visual Studio Code Extension](https://aka.ms/teams-toolkit) version 5.0.0 and higher or [Teams Toolkit CLI](https://aka.ms/teams-toolkit-cli)
> - [Microsoft 365 Copilot license](https://learn.microsoft.com/microsoft-365-copilot/extensibility/prerequisites#prerequisites)

1. First, select the Teams Toolkit icon on the left in the VS Code toolbar.
2. In the Account section, sign in with your [Microsoft 365 account](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts) if you haven't already.
3. Select `Debug in Copilot (Edge)` or `Debug in Copilot (Chrome)` from the launch configuration dropdown.
4. Select your declarative agent from the `Copilot` app.
5. Send a message to Copilot to find a repair record.

## What's included in the template

| Folder       | Contents                                                                                    |
| ------------ | ------------------------------------------------------------------------------------------- |
| `.vscode`    | VSCode files for debugging                                                                  |
| `appPackage` | Templates for the Teams application manifest, the plugin manifest and the API specification |
| `env`        | Environment files                                                                           |
| `infra`      | Templates for provisioning Azure resources                                                  |
| `src`        | The source code for the repair API                                                          |

The following files can be customized and demonstrate an example implementation to get you started.

| File                                               | Contents                                                                                              |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `src/functions/repairs.ts`                         | The main file of a function in Azure Functions.                                                       |
| `src/repairsData.json`                             | The data source for the repair API.                                                                   |
| `appPackage/apiSpecificationFile/repair.dev.yml`   | A file that describes the structure and behavior of the repair API.                                   |
| `appPackage/apiSpecificationFile/repair.local.yml` | A file that describes the structure and behavior of the repair API for local execution and debugging. |
| `appPackage/manifest.json`                         | Teams application manifest that defines metadata for your plugin inside Microsoft Teams.              |
| `appPackage/ai-plugin.dev.json`                    | The manifest file for your API plugin that contains information for your API and used by LLM.     |
| `appPackage/ai-plugin.local.json`                  | The manifest file for your API plugin for local execution and debugging.                          |
| `appPackage/repairDeclarativeAgent.json` | Define the behaviour and configurations of the declarative agent. |

The following are Teams Toolkit specific project files. You can [visit a complete guide on Github](https://github.com/OfficeDev/TeamsFx/wiki/Teams-Toolkit-Visual-Studio-Code-v5-Guide#overview) to understand how Teams Toolkit works.

| File                 | Contents                                                                                                                                                                                                                                                |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `teamsapp.yml`       | This is the main Teams Toolkit project file. The project file defines two primary things: Properties and configuration Stage definitions.                                                                                                               |
| `teamsapp.local.yml` | This overrides `teamsapp.yml` with actions that enable local execution and debugging.                                                                                                                                                                   |
| `aad.manifest.json`  | This file defines the configuration of Microsoft Entra app. This template will only provision [single tenant](https://learn.microsoft.com/azure/active-directory/develop/single-and-multi-tenant-apps#who-can-sign-in-to-your-app) Microsoft Entra app. |

## How OAuth works in the API plugin

![oauth-flow](https://github.com/OfficeDev/teams-toolkit/assets/107838226/f074abbe-d9e3-4a46-8e08-feb66b17a539)

> **Note**: The OAuth flow is only functional in remote environments. It cannot be tested in a local environment due to the lack of authentication support in Azure Function core tools.

## Addition information and references

- [Declarative agents for Microsoft 365](https://aka.ms/teams-toolkit-declarative-agent)
- [Extend Microsoft 365 Copilot](https://aka.ms/teamsfx-copilot-plugin)
- [Message extensions for Microsoft 365 Copilot](https://learn.microsoft.com/microsoft-365-copilot/extensibility/overview-message-extension-bot)
- [Microsoft Graph Connectors for Microsoft 365 Copilot](https://learn.microsoft.com/microsoft-365-copilot/extensibility/overview-graph-connector)
- [Microsoft 365 Copilot extensibility samples](https://learn.microsoft.com/microsoft-365-copilot/extensibility/samples)

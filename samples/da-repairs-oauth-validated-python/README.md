# Declarative Agent with an API plugin connected to an OAuth-secured API with validation (Python)

## Summary

This sample demonstrates how to build a declarative agent for Microsoft 365 Copilot that answers questions about repairs. The agent uses an API plugin to connect to an API that is secured with Entra ID.

![picture of the app in action](./assets/screenshot.gif)

Key aspects of the sample:

- Shows how to configure Microsoft 365 Agents Toolkit to make a declarative agent with an API plugin that is secured with Entra ID with just F5 to run locally.

- Shows how to validate an Entra ID access token in **Python** using [PyJWT](https://pyjwt.readthedocs.io/) rather than rely on an external service. This differs from the Teams Toolkit scaffolding, which doesn't authenticate users locally but instead relies on [Azure App Services authentication (EasyAuth)](https://learn.microsoft.com/azure/app-service/overview-authentication-authorization) for security in Azure only.

Here are some advantages of validating the token in your code instead of using Easy Auth:

- Since Easy Auth doesn't work locally, local requests are not authenticated. By handling in code, local requests are authenticated and the packaging source files are the same for all environments.

- If the code is deployed outside of Azure App Services, and if the included Bicep files aren't used, the code will appear to work but will do no token validation at all.

- With the Easy Auth scenario, if something goes wrong there is no way to inspect the OAuth token. In this sample you can set a breakpoint to inspect the token and walk through the validation.

- Easy Auth does not check the scope, or check to see if the token is an app token.

## Prerequisites

![drop](https://img.shields.io/badge/Microsoft%20365%20Agents%20Toolkit-5.10-green.svg)

* Microsoft 365 tenant with Microsoft 365 Copilot
* [Visual Studio Code](https://code.visualstudio.com/) with [Microsoft 365 Agents Toolkit](https://marketplace.visualstudio.com/items?itemName=TeamsDevApp.ms-teams-vscode-extension) v5.10 or greater
* [Python](https://www.python.org/downloads/) version 3.10 or later
* [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local) v4

## Version history

Version|Date|Author|Comments
-------|----|----|--------
1.0|May 7, 2026|[YugalPradhan31](https://github.com/YugalPradhan31)|Initial release (Python port)

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

---

## Minimal Path to Awesome

* Clone this repository
* Open the cloned copy of this folder with Visual Studio Code
* Install required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

* Press F5 to run the application. A browser window should open offering to add your application to Microsoft Teams.

## Features

This sample illustrates the following concepts:

- Building a declarative agent for Microsoft 365 Copilot with an API plugin
- Connecting an API plugin to an API secured with OAuth
- Using Python Azure Functions to build an API secured with Entra ID
- Validating Entra ID tokens in code using PyJWT (without Easy Auth)
- Using dev tunnels to test the API plugin locally

## Further reading

- [Build declarative agents for Microsoft 365 Copilot](https://learn.microsoft.com/microsoft-365-copilot/extensibility/overview-declarative-agent)
- [API Plugins for Microsoft 365 Copilot](https://learn.microsoft.com/microsoft-365-copilot/extensibility/overview-api-plugins)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [Azure Functions Python developer guide](https://learn.microsoft.com/azure/azure-functions/functions-reference-python)

<img src="https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/samples/da-repairs-oauth-validated-python" />
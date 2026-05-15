# Declarative Agent with an API plugin connected to an OAuth-secured API with validation (C#)

## Summary

This sample demonstrates how to build a declarative agent for Microsoft 365 Copilot that answers questions about repairs. The agent uses an API plugin to connect to an API that is secured with Entra ID.

![picture of the app in action](./assets/screenshot.gif)

Key aspects of the sample:

- Shows how to configure Microsoft 365 Agents Toolkit to make a declarative agent with an API plugin that is secured with Entra ID.

- Shows how to validate an Entra ID access token in **C#** using `Microsoft.IdentityModel` libraries rather than rely on an external service. This differs from the Teams Toolkit scaffolding, which doesn't authenticate users locally but instead relies on [Azure App Services authentication (EasyAuth)](https://learn.microsoft.com/azure/app-service/overview-authentication-authorization) for security in Azure only.

Here are some advantages of validating the token in your code instead of using Easy Auth:

- Since Easy Auth doesn't work locally, local requests are not authenticated. By handling in code, local requests are authenticated and the packaging source files are the same for all environments.

- If the code is deployed outside of Azure App Services, and if the included Bicep files aren't used, the code will appear to work but will do no token validation at all.

- With the Easy Auth scenario, if something goes wrong there is no way to inspect the OAuth token. In this sample you can set a breakpoint to inspect the token and walk through the validation.

- Easy Auth does not check the scope, or check to see if the token is an app token.

## Features

This sample illustrates the following concepts:

- Building a declarative agent for Microsoft 365 Copilot with an API plugin
- Connecting an API plugin to an API secured with OAuth
- Using C# Azure Functions (.NET 10 isolated worker) as the API backend
- Validating Entra ID tokens in code using Microsoft.IdentityModel (without Easy Auth)
- Using [dev tunnels](https://learn.microsoft.com/azure/developer/dev-tunnels/overview) to test the API plugin locally

## Contributors

* [Yugal Pradhan](https://github.com/YugalPradhan31)

## Version history

Version|Date|Comments
-------|----|--------
1.0|May 15, 2026|Initial release

## Prerequisites

* Microsoft 365 tenant with Microsoft 365 Copilot
* [.NET 10 SDK](https://dotnet.microsoft.com/download/dotnet/10.0)
* [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local#install-the-azure-functions-core-tools)
* [Visual Studio 2022](https://aka.ms/vs) 17.11 or higher
* [Microsoft 365 Agents Toolkit for Visual Studio](https://aka.ms/install-teams-toolkit-vs)

## Minimal Path to Awesome

* Clone this repository
* Open **RepairsApi.slnx** in Visual Studio 2022
* In the debug dropdown menu, select **Dev Tunnels > Create a Tunnel** (set authentication type to Public) or select an existing public dev tunnel
* Right-click the **M365Agent** project in Solution Explorer and select **Microsoft 365 Agents Toolkit > Select Microsoft 365 Account**
* Sign in to Microsoft 365 Agents Toolkit with a **Microsoft 365 work or school account**
* Press **F5**, or select **Debug > Start Debugging** in Visual Studio to start your app

> **Note:** Please make sure to switch to New Teams when Teams web client has launched.

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

## Further reading

- [Build declarative agents for Microsoft 365 Copilot](https://learn.microsoft.com/microsoft-365-copilot/extensibility/overview-declarative-agent)
- [API Plugins for Microsoft 365 Copilot](https://learn.microsoft.com/microsoft-365-copilot/extensibility/overview-api-plugins)
- [Azure Functions C# developer guide](https://learn.microsoft.com/azure/azure-functions/functions-dotnet-class-library)

<img src="https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/samples/da-repairs-oauth-validated-csharp" />

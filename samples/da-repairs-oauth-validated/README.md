# Declarative Agent with an API plugin connected to an API secured with OAuth with validation

## Summary

This sample demonstrates how to build a declarative agent for Microsoft 365 Copilot that answers questions about repairs. The agent uses an API plugin to connect to an API that is secured with Entra ID.

![picture of the app in action](./assets/screenshot.gif)

Key aspects of the sample:

 - Shows how to configure Teams Toolkit make a declarative agent with an API plugin that is secured with Entra ID with just F5 to run locally.

 - Shows how to validate an Entra ID access token in NodeJS (JavaScript/TypeScript) rather than rely on an external service. This differs from the Teams Toolkit scaffolding, which doesn't authenticate users locally but instead relies on use of [Azure App Services authentication (EasyAuth)](https://learn.microsoft.com/azure/app-service/overview-authentication-authorization) for security in Azure only.

 Here are some advantages of validating the token in your code instead of using Easy Auth

 - Since Easy Auth doesn't work locally, local requests are not authenticated. In addition to a small security opening, this causes the app to have 2 plugin files, including an anonymous one for local debugging. By handling in code, local requests are authenticated and the packaging source files are the same for all environments.

 - If the code is deployed outside of Azure app services, and if the included Bicep files aren't used, the code will appear to work but will do no token validation at all, thus wide open to anonymous requests.

 - With the Easy Auth scenario, Copilot is sending the access token directly to Azure App Services authentication. If something goes wrong there is no way to inspect the OAuth token, and debugging options are limited. In this sample you can set a breakpoint to inspect the token and walk through the validation to see what went wrong.

 - Easy Auth does not check the scope, or check to see if the token is an app token

 For these reasons, developers may choose to follow the approach used in this sample. 
 
 Microsoft does not currently provide a library for validating OAuth tokens in NodeJS; the [official documentation is here](https://learn.microsoft.com/entra/identity-platform/claims-validation). So this sample uses an open source library ([jwt-validate](https://www.npmjs.com/package/jwt-validate)) by [Waldek Mastykarz](https://github.com/waldekmastykarz), which aims to follow the documented practices. This library is not a Microsoft product, and is subject to an MIT license (i.e. use at your own risk). Many thanks to Waldek for creating the library.

## Prerequisites
![drop](https://img.shields.io/badge/Teams&nbsp;Toolkit&nbsp;for&nbsp;VS&nbsp;Code-5.10-green.svg)

 * Microsoft 365 tenant with Microsoft 365 Copilot
 * [Visual Studio Code](https://code.visualstudio.com/) with [Teams Toolkit](https://marketplace.visualstudio.com/items?itemName=TeamsDevApp.ms-teams-vscode-extension) v5.10 or greater
 * [NodeJS v18](https://nodejs.org/en/download/package-manager)
 * [Azure Functions core tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local#install-the-azure-functions-core-tools)

## Version history

Version|Date|Author|Comments
-------|----|----|--------
1.1|October 11, 2024|Waldek Mastykarz|Updated OAuth configuration and project setup
1.0|October 9, 2024|Bob German|Initial release

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

---

## Minimal Path to Awesome

* Clone this repository
* Open the cloned copy of this folder with Visual Studio Code
* Install required npm packages

```shell
  npm install
```

* Press F5 to run the application. A browser window should open offering to add your application to Microsoft Teams.

## Features

This sample illustrates the following concepts:

- Building a declarative agent for Microsoft 365 Copilot with an API plugin
- Connecting an API plugin to an API secured with OAuth
- Using Azure Functions to build an API secured with Azure App
- Service authentication and authorization without Easy Auth
- Using dev tunnels to test the API plugin locally

<img src="https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/samples/da-repairs-oauth-validated" />
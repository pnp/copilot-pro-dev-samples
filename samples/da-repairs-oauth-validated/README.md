# Declarative Agent with an API plugin connected to an API secured with OAuth with validation

## Summary

This sample demonstrates how to build a declarative agent for Microsoft 365 Copilot that answers questions about repairs. The agent uses an API plugin to connect to an API secured with Entra ID. 

![picture of the app in action](./assets/screenshot.gif)

The project contains an Azure Function, but unlike the [da-repairs-oauth sample](../da-repairs-oauth/) relies on Azure App Services authentication ("Easy Auth") for authentication, this sample validates access tokens in code. Teams Toolkit currently uses Easy Auth as shown in this sample. Here are some advantages of validating the token in your code instead:

 - Since Easy Auth doesn't work locally, local requests are not authenticated. In addition to a small security opening, this causes the app to have 2 plugin files, including an anonymous one for local debugging. In this sample, local requests are authenticated and the packaging source files are the same for all environments.

 - If the code is deployed outside of Azure app services, and if the included Bicep files aren't used, the code will appear to work but will do no token validation at all, thus wide open to anonymous requests.

 - With the Easy Auth scenario, Copilot is sending the access token directly to Azure App Services authentication. If something goes wrong there is no way to inspect the access token and debugging options are limited. In this sample you can set a breakpoint to inspect the token and walk through the validation to see what went wrong.

 - Easy Auth does not check the scope, or if the token is an app token

 For these reasons, developers may choose to follow this approach, which is made possible by an open source library ([jwt-validate](https://www.npmjs.com/package/jwt-validate)) by [Waldek Mastykarz](https://github.com/waldekmastykarz). This library is not a Microsoft product, and is subject to an MIT license (i.e. use at your own risk). Many thanks to Waldek for creating this library since Microsoft does not currently provide a token validation library for NodeJS.


## Prerequisites
![drop](https://img.shields.io/badge/Teams&nbsp;Toolkit&nbsp;for&nbsp;VS&nbsp;Code-5.10-green.svg)

 * Microsoft 365 tenant with Microsoft 365 Copilot
 * [Visual Studio Code](https://code.visualstudio.com/) with [Teams Toolkit](https://marketplace.visualstudio.com/items?itemName=TeamsDevApp.ms-teams-vscode-extension) v5.10 or greater
 * [NodeJS v18](https://nodejs.org/en/download/package-manager)
 * [Azure Functions core tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local#install-the-azure-functions-core-tools)

_Please list any portions of the toolchain required to build and use the sample, along with download links_

## Version history

Version|Date|Author|Comments
-------|----|----|--------
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

Building a declarative agent for Microsoft 365 Copilot with an API plugin
Connecting an API plugin to an API secured with OAuth
Using Azure Functions to build an API secured with Azure App Service authentication and authorization (Easy Auth)
Using dev tunnels to test the API plugin locally

<img src="https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/samples/da-repairs-oauth-validated" />
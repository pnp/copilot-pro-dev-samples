# Declarative for Microsoft 365 Copilot with an API plugin connected to an API secured with OAuth

## Summary

This sample has been removed because you can get the same results by just creating a new project with Teams Toolkit. 

At the time of this sample, Teams Toolkit generated different plugin files for local vs. dev environments, and did not protect the local tunnel at all. This was fixed in Teams Toolkit v5.12.0, rendering this sample unnecessary.

![Declarative agent answering questions about repairs using the information from an API secured with OAuth](./assets/screenshot.png)

## Contributors

* [Waldek Mastykarz](https://github.com/waldekmastykarz)

## Version history

Version|Date|Comments
-------|----|--------
1.2|January 16, 2025|Removed sample code as the same can be achieved with Teams Toolkit out of the box
1.1|October 11, 2024|Updated OAuth configuration and project setup
1.0|October 4, 2024|Initial release

## Prerequisites

* Microsoft 365 tenant with Microsoft 365 Copilot
* [Visual Studio Code](https://code.visualstudio.com/) with the [Teams Toolkit](https://marketplace.visualstudio.com/items?itemName=TeamsDevApp.ms-teams-vscode-extension) extension
* [Node.js v18](https://nodejs.org/en/download/package-manager)
* [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local#install-the-azure-functions-core-tools)

## Minimal path to awesome

Here's how to create the Repairs agent without using a sample.

![Teams toolkit](./assets/TTK-create-da-oauth.png)

* Open Teams Toolkit 1️⃣ and select "Create a New App" 2️⃣. Then choose "Declarative Agent" 3️⃣.
* In the prompts that follow, select "Add plugin", then "Start with a new API", then "OAuth".
* Then select your language (JavaScript or TypeScript) and choose a folder and application name
* Press F5 to provision the Entra ID app registration, and build, deploy, and run the agent

## Features

This application illustrates the following concepts:

* Building a declarative agent for Microsoft 365 Copilot with an API plugin
* Connecting an API plugin to an API secured with OAuth
* Using Azure Functions to build an API secured with Azure App Service authentication and authorization (Easy Auth)
* Using [dev tunnels](https://learn.microsoft.com/azure/developer/dev-tunnels/overview) to test the API plugin locally

## Help

We do not support samples, but this community is always willing to help, and we want to improve these samples. We use GitHub to track issues, which makes it easy for  community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues?q=label%3A%22sample%3A%20da-repairs-oauth%22) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

![](https://m365-visitor-stats.azurewebsites.net/SamplesGallery/da-repairs-oauth)

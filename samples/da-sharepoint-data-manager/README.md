# Overview of the Data Manager Agent

With the Data Manager agent, you can build a custom version of Copilot that helps users manage and organize their SharePoint sites and Microsoft 365 content. This agent leverages OneDrive and SharePoint access along with web search capabilities to provide guidance and information based on your content.

## Get started with the Data Manager

## Features

### Document Search
- Search across SharePoint sites and libraries
- Filter by content and metadata
- Discover relevant documents 

### File Organization
- Smart folder structure suggestions
- Metadata tagging and classification advice
- Content type recommendations

### Document Management Guidance
- Best practices for document organization
- SharePoint organization strategies
- Content classification recommendations

### Web Search Integration
- Access to relevant documentation and guidelines
- Search for information from trusted sources
- Up-to-date guidance from official documentation

### Pharmaceutical Manufacturing Intelligence
- Guidance on FDA, EMA, WHO, and ICH regulatory requirements
- Pharmaceutical documentation management according to industry standards
- GxP data integrity, traceability, and audit readiness recommendations
- Access to regulatory information from official sources

> **Note**: All required environment variables (TEAMS_APP_ID, TEAMS_APP_TENANT_ID, etc.) are automatically generated during the provisioning step. You don't need to set up any environment files manually.

> **Prerequisites**
>
> To run this Data Manager Agent in your local dev machine, you will need:
>
> - [Node.js](https://nodejs.org/), supported versions: 18, 20, 22
> - A [Microsoft 365 account for development](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts).
> - [Teams Toolkit Visual Studio Code Extension](https://aka.ms/teams-toolkit) version 5.0.0 and higher or [Teams Toolkit CLI](https://aka.ms/teamsfx-toolkit-cli)
> - [Microsoft 365 Copilot license](https://learn.microsoft.com/microsoft-365-copilot/extensibility/prerequisites#prerequisites)

![image](https://github.com/user-attachments/assets/e1c2a3b3-2e59-4e9b-8335-19315e92ba30)

1. First, select the Teams Toolkit icon on the left in the VS Code toolbar.
2. In the Account section, sign in with your [Microsoft 365 account](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts) if you haven't already.
3. Create Teams app by clicking `Provision` in "Lifecycle" section.
4. Select `Preview in Copilot (Edge)` or `Preview in Copilot (Chrome)` from the launch configuration dropdown.
5. Once the Copilot app is loaded in the browser, click on the "…" menu and select "Copilot chats". You will see your Data Manager agent on the right rail. Clicking on it will change the experience to showcase the logo and name of your data management agent.
6. Ask questions about your SharePoint content, and the agent will help you manage and organize your data.


## Version history

Version|Date|Comments
-------|----|--------
1.0|May 2025|Initial release

## Contributors

* [Kateryna Turuntseva](https://github.com/KatyaT27)

## Help

We do not support samples, but this community is always willing to help, and we want to improve these samples. We use GitHub to track issues, which makes it easy for  community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues?q=label%3A%22sample%3A%20da-qna-graphapi-plugin%22) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).


## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

<img src="https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/da-sharepoint-data-manager" />

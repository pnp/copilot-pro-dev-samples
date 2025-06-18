# Trey Research Copilot Declarative Agent (OAuth 2.0)

## Summary

Trey Research is a fictitious consulting company that supplies talent in the software and pharmaceuticals industries.

The solution consists of an API plugin that calls a set of Azure functions, which store the consulting data in a Azure Table storage (it uses the Azurite storage emulator when running locally).

A declarative agent is provided to converse with users and to call the API plugin, as well as to reference the correct SharePoint document library.

![Trey Research](./assets/preview.gif)

## Features

The sample showcases the following features:

1. Declarative agent with branding and instructions, with access to relevant documents and an API
2. API based plugin works with any platform that supports REST requests
3. Copilot will construct queries for specific data using GET requests
4. Copilot updates and adds data using POST requests
5. Multi-parameter queries to filter results
6. Show a confirmation card before POSTing data; capture missing parameters
7. Display rich adaptive cards
8. Authenticate the user using Entra ID and OAuth 2.0

## Contributors

* [Bob German](https://github.com/bobgerman)
* [Garry Trinder](https://github.com/garrytrinder)

## Version history

| Version | Date | Comments |
|--|--|--|
| 1.1 | June 11, 2025 | Maintenance release |
| 1.0 | April 16, 2025 | Initial release |

## Prerequisites

* [Node.js](https://nodejs.org/)
* A [Microsoft 365 tenant](https://learn.microsoft.com/en-us/microsoftteams/platform/concepts/build-and-test/prepare-your-o365-tenant) prepared for development
* [Microsoft 365 Agents Toolkit](https://aka.ms/teams-toolkit) Visual Studio Code extension
* A Microsoft 365 Copilot licence

## Minimal path to awesome

### 1. Setup document repository

For this sample, we will use OneDrive to store the documents that the agent will reference.

> ![NOTE]
> You can also use SharePoint document libraries, the URL will be slightly different, but the process is the same.

1. Go to [OneDrive](https://www.microsoft365.com/onedrive)
1. Go to **My files**
1. Create a new folder called **Legal**
1. Upload documents from the **sampleDocs** folder in this repository to the **Legal** folder
1. Navigate to the **Legal** folder
1. Expand the **Details** tab on the right
1. Expand the **More details** tab
1. Copy the Path to the Products folder using the **Copy** button

### 2. Test the agent

1. In the .env folder, create a new file called **.env.local**.
2. Add the following line to the **.env.local** file:

   ```plaintext
   DOCUMENTS_URL=<paste the path you copied from OneDrive>
   ```

   For example, if you copied the path `https://contoso-my.sharepoint.com/personal/user_contoso_com/Documents/Legal`, it should look like this:

   ```plaintext
   DOCUMENTS_URL=https://contoso-my.sharepoint.com/personal/user_contoso_com/Documents/Legal
   ```

3. Press **F5** to start a debug session. If prompted, sign in with your [Microsoft 365 account](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts). Wait for the provisioning to complete and the browser to open.
4. In the browser, if prompted, sign in with your Microsoft 365 account. The browser will open the declarative agent in Microsoft 365 Copilot after signing in.

> ![IMPORTANT]
> Microsoft 365 Copilot can cache the agent definition, so if you make changes to the agent, you may need to clear the browser cache for changes to be persisted. After the agent is loaded, use Hard Refresh (Ctrl+Shift+R) to ensure the latest version is loaded.

Try the following prompts:

* do we have any consultants with azure certifications?
* what projects are we doing for relecloud?
* which consultants are working with woodgrove bank?
* how many hours has avery delivered this month?
* please find a consultant with python skills who is available immediately
* are any consultants available who are AWS certified?
* does trey research have any architects with javascript skills?
* what designers are working at woodgrove bank?
* please charge 10 hours to woodgrove bank
* please add sanjay to the contoso project
* find my hours spreadsheet and get the hours for woodgrove, then bill the client
* make a list of my projects, then write a summary of each based on the statement of work.

## Troubleshooting and feature requests

We do not support samples, but this community is always willing to help, and we want to improve these samples. We use GitHub to track issues, which makes it easy for community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues?q=label%3A%22sample%3A%20da-trey-resarch%22) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

![](https://m365-visitor-stats.azurewebsites.net/SamplesGallery/da-trey-research-auth)

# Product support declarative agent

## Summary

This sample demonstrates how to extend Microsoft 365 Copilot with a declarative agent to help with product support scenarios. The agent is designed to assist customer support employees by answering questions related to a range of products.

It uses content from the product's documentation stored in Microsoft 365 to provide accurate and relevant answers.

![Product support declarative agent](./assets/preview.gif)

## Contributors

* [Garry Trinder](https://github.com/garrytrinder)

## Version history

| Version | Date | Comments |
|--|--|--|
| 1.1 | June 10, 2025 | Maintenance release |
| 1.0 | April 16, 2025 | Initial release |

## Prerequisites

* [Node.js](https://nodejs.org/)
* A [Microsoft 365 tenant](https://learn.microsoft.com/en-us/microsoftteams/platform/concepts/build-and-test/prepare-your-o365-tenant) prepared for development
* [Microsoft 365 Agents Toolkit](https://aka.ms/teams-toolkit) Visual Studio Code extension
* Microsoft 365 Copilot license

## Minimal path to awesome

### 1. Setup document repository

1. Go to [OneDrive](https://www.microsoft365.com/onedrive)
1. Go to **My files**
1. Create a new folder called **Products**
1. Upload documents from the **docs** folder in this repository to the **Products** folder
1. Navigate to the **Products** folder
1. Expand the **Details** tab on the right
1. Expand the **More details** tab
1. Copy the Path to the Products folder using the **Copy** button

### 2. Provision agent

1. Open the project in Visual Studio Code
1. Open **env/.env.dev**
1. Set the value of the **DOCUMENTS_URL** variable to the path you copied from OneDrive.
1. On the primary sidebar, select the **Microsoft 365 Agents Toolkit icon**
1. In the LIFECYCLE section, select **Provision**
1. If prompted, **sign in** with your [Microsoft 365 account](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts)
1. Wait for the provisioning to complete

### 3. Test the agent

1. Press **F5** to launch a browser that navigates that opens the declarative agent in Microsoft 365 Copilot. If prompted, sign in with your Microsoft 365 account.

Try the following prompts:

* What can you do?
* Tell me about Eagle Air?
* Recommend a product for a farmer.
* What is the difference between Eagle Air and Contoso Quad? Show your answer in a table.

## Troubleshooting and feature requests

We do not support samples, but this community is always willing to help, and we want to improve these samples. We use GitHub to track issues, which makes it easy for community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues?q=label%3A%22sample%3A%20da-product-support%22) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

![](https://m365-visitor-stats.azurewebsites.net/SamplesGallery/da-product-support)

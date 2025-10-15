## Summary

HR Helpdesk is a template Declarative Agent designed to help employees troubleshoot their issues using insights from ServiceNow KB, and if not successful create a case in the right Centre of Excellence/table without much burden on the end user.
  Goals:
1.	Help employees resolve their HR issues via self serve
2.	If necessary, help them create a ServiceNow case with minimal effort.

## Features

This sample illustrates the following concepts:

- 🧭 Guide employees through common HR issues with conversational, easy-to-follow resolutions that reduce downtime
- 💡 Help users self-resolve problems in Accounts, Payroll, Benefits, Tax, Leave, Onboarding, or any other general HR support needed
- 📝 Create service /incident tickets in the correct Centre of Excellence or ServiceNow table (auto classification) with a clear summary of the issue, and relevant first-level debug information — reducing back-and-forth and enabling faster, more accurate resolution by Support teams.


## Contributors

* [Sébastien Levert](https://github.com/sebastienlevert)
* [Akhil Sai Valluri](https://github.com/akhilsaivalluri)
* [Suryamanohar Mallela](https://github.com/SuryaMSFT)

## Version history

Version|Date|Comments
-------|----|--------
1.0|July 25, 2025|Initial release

## Prerequisites

* Microsoft 365 tenant with Microsoft 365 Copilot
* [Visual Studio Code](https://code.visualstudio.com/) with the [Microsoft 365 Agents Toolkit](https://marketplace.visualstudio.com/items?itemName=TeamsDevApp.ms-teams-vscode-extension) extension
* [Node.js v20](https://nodejs.org/en/download/package-manager)
* A ServiceNow account with API access

## Example Prompts

1. I didn’t get my salary credit for last month
   <img width="841" height="599" alt="image" src="https://github.com/user-attachments/assets/fcf90391-8728-4331-8ff8-633fa844135b" />
   <img width="840" height="536" alt="image" src="https://github.com/user-attachments/assets/27a4be9b-5756-43fd-9902-bf15187f30d1" />
   <img width="841" height="419" alt="image" src="https://github.com/user-attachments/assets/3ef28fb8-42e3-4f86-afa7-d6a59818be97" />

2. I’m travelling for work. However, the manager information in the Business Travel letter tool is incorrect.
   <img width="948" height="581" alt="image" src="https://github.com/user-attachments/assets/9cbd513e-7b26-4568-8ecf-6d0faf847928" />
   <img width="849" height="580" alt="image" src="https://github.com/user-attachments/assets/d7f8a19f-5c2c-4723-8398-cdc4b17fceee" />
   <img width="867" height="451" alt="image" src="https://github.com/user-attachments/assets/9e0c1930-0a67-47bd-a102-081c68ee922f" />
   <img width="851" height="468" alt="image" src="https://github.com/user-attachments/assets/d8525ca9-c21c-45cc-8788-49a320d9ef69" />

## Minimal path to awesome

* Clone this repository (or [download this solution as a .ZIP file](https://pnp.github.io/download-partial/?url=https://github.com/pnp/copilot-pro-dev-samples/tree/main/samples/da-ITHelpdesk) then unzip it)
* Open the Agents Toolkit extension and sign in to your Microsoft 365 tenant with Microsoft 365 Copilot
* Select **Preview in Copilot (Edge)** from the launch configuration dropdown

## Configuration

### ServiceNow Plugin Configuration 

In your OpenAPI spec [`appPackage/apiSpecificationFile/openapi.yaml`](appPackage/apiSpecificationFile/openapi.yaml):

* Update the server URL to point to your ServiceNow instance
<img width="738" height="175" alt="image" src="https://github.com/user-attachments/assets/f41af683-6257-41e5-af83-d5170f3ba749" />

* Point authorization, token and refresh urls to your ServiceNow instance
<img width="1034" height="272" alt="image" src="https://github.com/user-attachments/assets/77f37046-aff4-47f2-be6d-1995bec79c11" />

* In your [`ai-plugin.json`](ai-plugin.json) (plugin manifest), go to the `response_semantics` section for each function. You can customize the layout and data bindings to create richer, domain-specific views. Ensure all links point to your ServiceNow instance.
<img width="619" height="370" alt="image" src="https://github.com/user-attachments/assets/4b2751f9-b2ef-4322-ab10-6f310e254cd9" />


### ServiceNow Authentication Setup

1. Log into your ServiceNow account and go to Application Registry under System OAuth 
   <img width="842" height="432" alt="image" src="https://github.com/user-attachments/assets/e0da4532-556e-4099-994e-0b253d2e72cb" />
   <img width="904" height="288" alt="image" src="https://github.com/user-attachments/assets/54fa6f97-435c-4c6b-9998-491cfa11a5e4" />

2. Create a new registry. Select option “Create an OAuth API endpoint for external clients”
   <img width="1034" height="305" alt="image" src="https://github.com/user-attachments/assets/c258023e-d98b-45d8-9df0-e34027ecad43" />
   
3. Add callback URL as https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect. You can leave other settings as defaults or customize it as per your needs. Hit Submit.
   <img width="1034" height="513" alt="image" src="https://github.com/user-attachments/assets/3820b77a-f35d-4752-95a9-8ee2c46b1ec0" />

4. After Submit, your app will show in the list. Click on it to get access to Client secret
   <img width="1034" height="119" alt="image" src="https://github.com/user-attachments/assets/5f939dc7-7ce0-4064-8865-ae3f588ed8b8" />

5. Copy Client ID and Client Secret. You will require it in step 6.
   <img width="710" height="307" alt="image" src="https://github.com/user-attachments/assets/d33733f3-797b-4692-9952-48cab9067e81" />

6. Setup Microsoft Graph Connector to add ServiceNow knowledge – This will allow agent to provide troubleshooting guidance based on your ServiceNow KB articles. Follow the steps in https://learn.microsoft.com/en-us/microsoftsearch/servicenow-knowledge-connector . After you setup Microsoft Graph Connector to add ServiceNow knowledge, add the connection IDs in the Agent file.
   <img width="719" height="295" alt="image" src="https://github.com/user-attachments/assets/dae6d7ed-0b4d-44bc-9385-7de198f44c5f" />
   
7. Provision Key & Secret in Copilot: When provisioning the Declarative Agent via the Teams Toolkit, you’ll be prompted to enter the Client ID (Key) and Client Secret. Use the values from the ServiceNow OAuth app you created.
   <img width="940" height="627" alt="image" src="https://github.com/user-attachments/assets/41160786-6c83-4950-8452-029ca559d5df" />


## Help

We do not support samples, but this community is always willing to help, and we want to improve these samples. We use GitHub to track issues, which makes it easy for  community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues?q=label%3A%22sample%3A%20da-HRHelpdesk%22) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

![](https://m365-visitor-stats.azurewebsites.net/SamplesGallery/da-HRHelpdesk)

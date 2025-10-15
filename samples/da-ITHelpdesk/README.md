## Summary

IT Helpdesk Agent is a Declarative Agent designed to assist employees with IT issues through (a) guided, conversational troubleshooting, (b) outage detection, and ticket creation for escalation – powered through ServiceNow offerings (Knowledge, Catalogue and Tickets). 

Goals: IT helpdesk Agent has been created with two key objectives, 
1.	Reduce overall number of tickets raised by **offering easy-to-follow, self-serve troubleshooting guidance** to employees
2.	Improve SLA to ticket resolution by **capturing first-level debug information** up front, reducing back and forth

## Features

This sample illustrates the following concepts:

- 🧭 Guide employees through common IT issues with conversational, easy-to-follow resolutions that reduce downtime
- ⚠️ Proactively inform users about service outages, minimizing repeated tickets and unnecessary troubleshooting
- 💡 Help users self-resolve problems like VPN errors, login failures, password resets, and software installation using relevant resolutions from Service Now
- 📝 Create service /incident tickets with the correct category and subcategory (auto-classification), a clear summary of the issue, and relevant first-level debug information — reducing back-and-forth and enabling faster, more accurate resolution by IT teams.
- 🎫 Help users track the status of their support tickets, view recent updates, and stay informed — improving transparency and reducing the need to follow up manually 

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

1. Help me connect to VPN
<img width="898" height="307" alt="image" src="https://github.com/user-attachments/assets/9d1f890f-ca06-400b-b5e6-00df40597ee2" />
<img width="903" height="1078" alt="image" src="https://github.com/user-attachments/assets/3fd615f9-8a49-41c6-910f-310344802ce6" />

2. I can’t access internal portal
<img width="948" height="581" alt="image" src="https://github.com/user-attachments/assets/9cbd513e-7b26-4568-8ecf-6d0faf847928" />

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

* In your [`ai-plugin.json`](ai-plugin.json) (plugin manifest), go to the `response_semantics` section for each function. This sample comes with basic Adaptive Card views for rich representation. You can further customize the layout and data bindings to create richer, domain-specific views. Ensure all links point to your ServiceNow instance.
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

7. Add knowledge for incident autoclassification: This step is required if you want Copilot to perform autoclassification of an incident (Category and Subcategory fields) while creating the incident itself by matching issue description with the available choices.
    - Go to Choice Lists under System definition
      <img width="444" height="464" alt="image" src="https://github.com/user-attachments/assets/db35805a-bdbb-40b7-945d-77f2f1d8cc08" />
    - Click on the filter icon and select Table as the field, and “is” “ incident” as other query parameters to filter out just the choicelists for your incident table. Run the query.
      <img width="1034" height="138" alt="image" src="https://github.com/user-attachments/assets/ed0fe9cb-2838-46b3-bf0a-dbf46f43889f" />
    - Right click on the table header row and select export option. Select csv format.
      <img width="932" height="373" alt="image" src="https://github.com/user-attachments/assets/64a652b3-365b-4a3a-8666-5bc4702e9d88" />
    - Now add this file to your SharePoint folder and copy url of the location. Add the url in your Agent file as knowledge under Capabilities.
      <img width="1034" height="222" alt="image" src="https://github.com/user-attachments/assets/af5dc9c0-3e46-457f-966c-b2cdc854d4bc" />
    - Note: All users who you want this Agent to be available should also have access to this file for Copilot to use it during autoclassification.
      
8. Provision Key & Secret in Copilot: When provisioning the Declarative Agent via the Teams Toolkit, you’ll be prompted to enter the Client ID (Key) and Client Secret. Use the values from the ServiceNow OAuth app you created.
   <img width="940" height="627" alt="image" src="https://github.com/user-attachments/assets/41160786-6c83-4950-8452-029ca559d5df" />


## Help

We do not support samples, but this community is always willing to help, and we want to improve these samples. We use GitHub to track issues, which makes it easy for  community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues?q=label%3A%22sample%3A%20da-ITHelpdesk%22) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

![](https://m365-visitor-stats.azurewebsites.net/SamplesGallery/da-ITHelpdesk)

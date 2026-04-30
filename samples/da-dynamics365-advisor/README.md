# Dynamics 365 Advisor Agent

## Summary

An expert declarative agent for Microsoft 365 Copilot that provides guidance on Dynamics 365 CRM, Power Platform, and Copilot solutions. This agent helps users with CRM architecture decisions, entity design, security models, Power Automate workflows, and business process automation.

![Dynamics 365 Advisor in action](assets/screenshot.png)

## Tools and Frameworks

![drop](https://img.shields.io/badge/Teams&nbsp;Toolkit&nbsp;for&nbsp;VS&nbsp;Code-5.0+-green.svg)
![drop](https://img.shields.io/badge/Declarative&nbsp;Agent-v1.3-blue.svg)

## Prerequisites

* [Microsoft 365 Developer Account](https://developer.microsoft.com/microsoft-365/dev-program)
* [Teams Toolkit for Visual Studio Code](https://learn.microsoft.com/microsoftteams/platform/toolkit/install-teams-toolkit?tabs=vscode)
* [Node.js LTS](https://nodejs.org/)
* [Visual Studio Code](https://code.visualstudio.com/)

## Version history

Version|Date|Author|Comments
-------|----|----|--------
1.0.0|April 28, 2026|Muhammad Shahzad Shafique|Initial release

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

---

## Minimal Path to Awesome

* Clone this repository (or [download this solution as a .ZIP file](https://pnp.github.io/download-partial/?url=https://github.com/pnp/copilot-pro-dev-samples/tree/main/samples/da-dynamics365-advisor) then unzip it)
* Open the `samples/da-dynamics365-advisor` folder in Visual Studio Code
* Select the Teams Toolkit icon on the left in the VS Code toolbar
* In the Account section, sign in with your [Microsoft 365 account](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts) if you haven't already
* Create the Teams app by selecting **Provision** in the "Lifecycle" section
* Select `Preview in Copilot (Edge)` or `Preview in Copilot (Chrome)` from the launch configuration dropdown
* Once the Copilot app is loaded in the browser, select the "..." menu and select **Copilot chats**. You will see the Dynamics 365 Advisor agent on the right rail
* Select the agent and start asking questions about Dynamics 365 CRM, Power Platform, or Copilot Studio

## Features

This agent provides expert guidance on:

* **CRM Architecture Guidance** - Dynamics 365 CRM design and implementation
* **Entity & Table Design** - Data model design in Dynamics 365
* **Security Model Design** - Security roles, access levels, and multi-region deployment architecture
* **Power Automate Integration** - Workflow automation and business process recommendations
* **Copilot Studio Use Cases** - Customer service chatbot scenarios and implementations
* **Business Process Optimization** - Sales pipeline and customer service improvements
* **Plugin & Custom Code** - Custom development guidance and best practices

## Conversation Starters

The agent includes several conversation starters:

* **CRM Design** - "Help me design a case management solution in Dynamics 365."
* **Power Automate** - "Suggest a Power Automate flow for lead qualification."
* **Copilot Studio** - "Give me chatbot use cases for customer service."
* **Security Model** - "How should I design security roles for a 3-country CRM deployment?"

## File Structure

```
da-dynamics365-advisor/
+-- appPackage/
|   +-- declarativeAgent.json       # Agent configuration
|   +-- instruction.txt              # Agent instructions and behavior
|   +-- manifest.json               # Teams app manifest
|   +-- color.png                    # App color icon
|   +-- outline.png                  # App outline icon
+-- env/
|   +-- .env.dev                     # Environment variables for dev
+-- assets/
|   +-- screenshot.png               # Demo screenshot
|   +-- sample.json                  # Sample metadata
+-- .env.local.sample               # Environment variables template
+-- .gitignore
+-- README.md
```

## Setup Instructions

1. **Open in VS Code**
   - Open the `da-dynamics365-advisor` folder in Visual Studio Code
   - Ensure Teams Toolkit extension is installed

2. **Review the Configuration**
   - Check `appPackage/declarativeAgent.json` for agent settings
   - Review `appPackage/instruction.txt` for agent behavior

3. **Run the Agent**
   - Press F5 or use Teams Toolkit to start debugging
   - Sign in with your Microsoft 365 account
   - The agent will be deployed to your Copilot environment

4. **Test the Agent**
   - Open Microsoft 365 Copilot
   - Find "Dynamics 365 Advisor" in your agents
   - Try the conversation starters or ask your own questions about:
     - Dynamics 365 CRM architecture
     - Power Platform solutions
     - Security and access control
     - Business process automation

## Author

* **Muhammad Shahzad Shafique** - [GitHub Profile](https://github.com/MrShahzadShafique)

<img src="https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/samples/da-dynamics365-advisor" />

# Policy Agent — Declarative Agent

## Summary

A **SharePoint-grounded Declarative Agent (DA)** built in **Microsoft Copilot Studio** that provides quick, summary-level answers to policy-related questions across HR, IT, Finance, Legal & Compliance, and other departments. It leverages **Microsoft 365 grounding** for multi-file referencing across a SharePoint policy site.

> This sample is contributed in the same packaging format as [`mcs-BlogPostHelper`](https://github.com/pnp/copilot-pro-dev-samples/tree/main/samples/mcs-BlogPostHelper) — exported with the Power Platform CLI (`pac`) as an unmanaged Dataverse solution so it can be imported into any environment.

## Demo

<https://github.com/user-attachments/assets/2d68cfe9-1742-472a-ac77-f36d05d009b6>

## Problem Statement

Employees frequently need quick access to company policies across HR, IT, Finance, and other departments. Common challenges:

* Time wasted searching through multiple SharePoint sites and documents
* Inconsistent answers when policies are spread across different locations
* Inability to get quick summaries without reading entire policy documents
* Lack of multi-file referencing for comprehensive answers

## Solution Overview

A **Declarative Agent (DA)** in Copilot Studio with SharePoint as the primary knowledge source:

| Component | Description |
|-----------|-------------|
| **Declarative Agent** | Leverages M365 grounding capabilities for quick deployment and powerful retrieval |
| **SharePoint Knowledge** | Uses SharePoint site pages as the information source |
| **Enablement Portal** | SharePoint-based portal for policy documentation |

## Architecture

```
                    ┌─────────────────────────┐
                    │      User Query         │
                    │  "What is the IT usage  │
                    │       policy?"          │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │   Declarative Agent     │
                    │   (Policy Agent DA)     │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │   M365 Grounding        │
                    │   - SharePoint Sites    │
                    │   - Graph Knowledge     │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │   Summary Response      │
                    │   with Multi-File       │
                    │   References            │
                    └─────────────────────────┘
```

## Technical Details

| Aspect | Details |
|--------|---------|
| **Platform** | Microsoft Copilot Studio |
| **Agent Type** | Declarative Agent (DA) |
| **Knowledge Sources** | SharePoint site containing informational pages |
| **Integration Logic** | Declarative configurations using SharePoint site pages |

## Sample Prompts

* "What is the company's IT usage policy?"
* "What documents or evidence are required under the health insurance policy?"
* "Summarize the vacation policy for full-time employees"
* "What are the key points in our data protection policy?"

## Business Value

| Metric | Value |
|--------|-------|
| **Faster Go-Live** | Quick to build and deploy with minimal configuration |
| **Enhanced Retrieval** | Deep answers with multi-file referencing capabilities |
| **Scalability** | Ability to cover larger data sets for grounding |
| **M365 Integration** | Powerful grounding on organizational data via SharePoint and Graph |

## Contributors

* [Keshav Keshari](https://github.com/keshavk-msft)

## Version history

| Version | Date           | Comments         |
| ------- | -------------- | ---------------- |
| 1.0     | June 29, 2026  | Initial release  |

## Prerequisites

* Microsoft 365 tenant with **Microsoft 365 Copilot** and **Copilot Studio** licenses
* A **SharePoint site** containing the organization's policy documents
* [Microsoft Power Platform CLI (`pac`)](https://learn.microsoft.com/en-us/power-platform/developer/cli/introduction)
* (Optional) [VS Code Copilot Studio extension](https://marketplace.visualstudio.com/items?itemName=ms-CopilotStudio.vscode-copilotstudio) for source-control editing

## Minimal path to awesome

Import this sample into your Copilot Studio environment using the Power Platform CLI.

* Ensure you are authenticated with `pac auth`:

  ```powershell
  pac auth create --environment <your-env-id>
  pac auth who
  ```

* From this sample folder, package the unpacked solution into a zip:

  ```powershell
  cd samples/mcs-PolicyAgentDA

  # Package up the solution. The SRC folder is what gets packed.
  pac solution pack --zipfile PolicyAgentDA.zip --folder ./src
  ```

* Import into your chosen environment (omit `--environment` to use the default):

  ```powershell
  pac env list
  pac solution import --path ./PolicyAgentDA.zip --environment <your-env-id> --publish-changes --activate-plugins
  ```

* After import, in [Copilot Studio](https://copilotstudio.microsoft.com):
  1. Open the **Policy Agent (Declarative)** in your solution.
  2. Edit the **SharePoint** knowledge source `SharePointSearchSource.0` and point it at the URL of your policy site.
  3. Publish to your channel of choice (Microsoft 365 Copilot, Teams).

## Features

This sample extends Microsoft 365 Copilot with an agent that:

* Uses a **Declarative Agent** grounded on a SharePoint site of policy pages.
* Provides fast deployment with minimal configuration (no custom actions, no flows).
* Returns concise, action-oriented answers with multi-file references.

### Folder structure

```
mcs-PolicyAgentDA/
├── PolicyAgentDA.cdsproj          # MSBuild project (optional, for dotnet build / pipelines)
├── README.md
├── assets/
│   └── demo.mp4
└── src/                           # Produced by `pac solution unpack`
    ├── Other/
    │   ├── Solution.xml
    │   └── Customizations.xml
    ├── bots/
    │   └── cred8_kkEnterprisesPolicyAgent/   # Agent definition + topics, knowledge
    └── botcomponents/             # GPT config, knowledge & topic components
```

## Related resources

* [Copilot Studio documentation](https://learn.microsoft.com/en-us/microsoft-copilot-studio/)
* [Declarative agents in Microsoft 365 Copilot](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/overview-declarative-agent)
* [Move copilots between environments (Copilot Studio ALM)](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-export-import-bots)
* [Power Platform CLI `pac solution` reference](https://learn.microsoft.com/en-us/power-platform/developer/cli/reference/solution)
* [VS Code Copilot Studio extension](https://marketplace.visualstudio.com/items?itemName=ms-CopilotStudio.vscode-copilotstudio)

## Help

We do not support samples, but this community is always willing to help, and we want to improve these samples. We use GitHub to track issues, which makes it easy for community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues?q=label%3A%22sample%3A%20mcs-PolicyAgentDA%22) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new). Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

## Disclaimer

**THIS CODE IS PROVIDED AS IS WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

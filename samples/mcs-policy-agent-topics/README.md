# Policy Agent — Topic-Based Grounding

## Summary

A **Custom Engine Agent (CEA)** built in **Microsoft Copilot Studio** that uses a topic-based folder structure in SharePoint for deterministic, precise policy responses. Each agent topic (Finance, HR, IT & Security, Legal & Compliance, Operations & Administration) is mapped to its own SharePoint knowledge source, so the agent routes the user's query to the correct department folder.

> This sample is contributed in the same packaging format as [`mcs-BlogPostHelper`](https://github.com/pnp/copilot-pro-dev-samples/tree/main/samples/mcs-BlogPostHelper) — exported with the Power Platform CLI (`pac`) as an unmanaged Dataverse solution so it can be imported into any environment.

## Demo

<https://github.com/user-attachments/assets/e6c3d7d3-015e-4f67-ac9e-2f5d4a6c8294>

## Problem Statement

Organizations with policies spread across multiple departments need precise, targeted responses. Common challenges:

* Generic responses that don't address specific departmental policies
* Difficulty routing queries to the right knowledge source
* Lack of precision when policies overlap across departments
* Need for deterministic behavior in policy lookups

## Solution Overview

A **Custom Engine Agent (CEA)** in Copilot Studio with topic-based SharePoint folder mapping:

| Component | Description |
|-----------|-------------|
| **Custom Engine Agent** | Provides targeted responses based on topic classification |
| **Topic-Based Grounding** | SharePoint folders organized by department/topic |
| **Folder-to-Topic Mapping** | Each SharePoint folder maps to a specific agent topic |
| **Deterministic Routing** | Structured approach ensures precise, relevant answers |

## Architecture

```
                    ┌─────────────────────────┐
                    │      User Query         │
                    │  "What's the expense    │
                    │   claim process?"       │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │   Custom Engine Agent   │
                    │   (Topic Classifier)    │
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
    ┌─────────▼─────┐  ┌───────▼───────┐  ┌─────▼─────────┐
    │  HR Topic     │  │ Finance Topic │  │  IT Topic     │
    │               │  │               │  │               │
    │  SharePoint   │  │  SharePoint   │  │  SharePoint   │
    │  /HR Folder   │  │  /Finance     │  │  /IT Folder   │
    └───────────────┘  └───────┬───────┘  └───────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Targeted Response  │
                    │  from Finance       │
                    │  Policy Documents   │
                    └─────────────────────┘
```

## Technical Details

| Aspect | Details |
|--------|---------|
| **Platform** | Microsoft Copilot Studio |
| **Agent Type** | Custom Engine Agent (CEA) |
| **Knowledge Sources** | SharePoint folders organized by topic (Finance, HR, IT, etc.) |
| **Integration Logic** | Topic folders mapped to specific agent topics for targeted responses |
| **Routing Method** | Deterministic topic-based classification |

The agent ships with five built-in topics, each linked to its own SharePoint folder:

* Finance
* HR
* IT & Security
* Legal & Compliance
* Operations & Administration

## Sample Prompts

* "What's the code of conduct policy for new employees?"
* "Explain the step-by-step process for submitting expense claims"
* "What are the IT security guidelines for remote work?"
* "How do I request time off according to HR policy?"

## Business Value

| Metric | Value |
|--------|-------|
| **Faster Info Retrieval** | Direct routing to relevant policy folder |
| **Better Resolution Rate** | Improved user query resolution percentage |
| **Enhanced Precision** | Deterministic systems provide accurate, targeted answers |
| **Structured Organization** | Clear folder structure makes maintenance easier |

## Contributors

* [Keshav Keshari](https://github.com/keshavk-msft)

## Version history

| Version | Date           | Comments         |
| ------- | -------------- | ---------------- |
| 1.0     | June 29, 2026  | Initial release  |

## Prerequisites

* Microsoft 365 tenant with **Copilot Studio** license
* A **SharePoint site** with policy documents organized into one folder per topic (see [SharePoint setup](#sharepoint-setup))
* [Microsoft Power Platform CLI (`pac`)](https://learn.microsoft.com/en-us/power-platform/developer/cli/introduction)
* (Optional) [VS Code Copilot Studio extension](https://marketplace.visualstudio.com/items?itemName=ms-CopilotStudio.vscode-copilotstudio) for source-control editing

### SharePoint setup

Create one folder per policy domain on your SharePoint site:

```
/Policies
  ├── /Finance
  │   ├── expense-policy.docx
  │   └── travel-reimbursement.docx
  ├── /HR
  │   ├── code-of-conduct.docx
  │   └── leave-policy.docx
  ├── /IT-Security
  │   ├── security-guidelines.docx
  │   └── acceptable-use.docx
  ├── /Legal-Compliance
  └── /Operations-Administration
```

## Minimal path to awesome

Import this sample into your Copilot Studio environment using the Power Platform CLI.

* Ensure you are authenticated with `pac auth`:

  ```powershell
  pac auth create --environment <your-env-id>
  pac auth who
  ```

* From this sample folder, package the unpacked solution into a zip:

  ```powershell
  cd samples/mcs-PolicyAgentTopics

  # Package up the solution. The SRC folder is what gets packed.
  pac solution pack --zipfile PolicyAgentTopics.zip --folder ./src
  ```

* Import into your chosen environment (omit `--environment` to use the default):

  ```powershell
  pac env list
  pac solution import --path ./PolicyAgentTopics.zip --environment <your-env-id> --publish-changes --activate-plugins
  ```

* After import, in [Copilot Studio](https://copilotstudio.microsoft.com):
  1. Open the **Policy Agent (Topic-based)** in your solution.
  2. For each topic (Finance, HR, IT Security, Legal Compliance, Operations Administration), edit the linked SharePoint knowledge source and point it at the corresponding folder on your SharePoint site.
  3. Publish to your channel of choice (Microsoft Teams, M365 Copilot).

## Features

This sample extends Copilot Studio with an agent that:

* Uses **topic-based deterministic routing** — each agent topic owns its own SharePoint knowledge source.
* Includes five built-in topics, each mapped to its own SharePoint folder (Finance, HR, IT & Security, Legal & Compliance, Operations & Administration).
* Returns precise, department-scoped answers without cross-contamination from other domains.
* Easy to extend — adding a new policy domain is just adding a topic + a SharePoint folder.

### Folder structure

```
mcs-PolicyAgentTopics/
├── PolicyAgentTopics.cdsproj      # MSBuild project (optional, for dotnet build / pipelines)
├── README.md
├── assets/
│   └── demo.mp4
└── src/                           # Produced by `pac solution unpack`
    ├── Other/
    │   ├── Solution.xml
    │   └── Customizations.xml
    ├── bots/
    │   └── cred8_agent_Ai98b3/    # Agent definition + topic & knowledge configuration
    └── botcomponents/             # 5 topic-scoped knowledge sources + 13 topic components
```

## Related resources

* [Copilot Studio documentation](https://learn.microsoft.com/en-us/microsoft-copilot-studio/)
* [Create topics in Copilot Studio](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-create-edit-topics)
* [Move copilots between environments (Copilot Studio ALM)](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-export-import-bots)
* [Power Platform CLI `pac solution` reference](https://learn.microsoft.com/en-us/power-platform/developer/cli/reference/solution)
* [VS Code Copilot Studio extension](https://marketplace.visualstudio.com/items?itemName=ms-CopilotStudio.vscode-copilotstudio)

## Help

We do not support samples, but this community is always willing to help, and we want to improve these samples. We use GitHub to track issues, which makes it easy for community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues?q=label%3A%22sample%3A%20mcs-PolicyAgentTopics%22) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new). Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

## Disclaimer

**THIS CODE IS PROVIDED AS IS WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

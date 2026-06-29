# Policy Agent — Custom Engine Agent with Salesforce Escalation

## Summary

A **Custom Engine Agent (CEA)** built in **Microsoft Copilot Studio** that handles both summary-level and detailed clause-level policy queries. Quick / overview questions are answered from a **SharePoint** knowledge source; "give me the full details" requests are escalated to **Salesforce Knowledge** via an Agent Flow.

> This sample is contributed in the same packaging format as [`mcs-BlogPostHelper`](https://github.com/pnp/copilot-pro-dev-samples/tree/main/samples/mcs-BlogPostHelper) — exported with the Power Platform CLI (`pac`) as an unmanaged Dataverse solution so it can be imported into any environment.

## Demo

<https://github.com/user-attachments/assets/cc37e754-7ecd-4627-aa7e-3a8cf059467b>

## Problem Statement

Employees need varying levels of policy information — from quick summaries to detailed clause-level specifics. Common challenges:

* Simple queries require quick answers from SharePoint
* Complex queries need deeper investigation and expert assistance
* No seamless handoff between self-service and expert support
* Difficulty accessing detailed policy clauses and exceptions

## Solution Overview

A **Custom Engine Agent (CEA)** in Copilot Studio with SharePoint integration and Salesforce escalation:

| Component | Description |
|-----------|-------------|
| **Custom Engine Agent** | Handles both summary and detailed policy queries |
| **SharePoint Integration** | Primary knowledge source for policy documents |
| **Salesforce Escalation** | API-based escalation for detailed clause-level assistance |
| **Agent Flows** | Workflow automation for seamless escalation |

## Architecture

```
                    ┌─────────────────────────┐
                    │      User Query         │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │   Custom Engine Agent   │
                    │   (Policy Agent CEA)    │
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┴─────────────────┐
              │                                   │
    ┌─────────▼─────────┐             ┌──────────▼─────────┐
    │  Summary Query    │             │  Detail Query      │
    │                   │             │  "Give me more     │
    │  SharePoint       │             │   details..."      │
    │  Knowledge        │             │                    │
    └─────────┬─────────┘             └──────────┬─────────┘
              │                                   │
              │                       ┌──────────▼─────────┐
              │                       │  Salesforce API    │
              │                       │  (Agent Flows)     │
              │                       └──────────┬─────────┘
              │                                   │
              └─────────────────┬─────────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │   Response to User      │
                    └─────────────────────────┘
```

## Technical Details

| Aspect | Details |
|--------|---------|
| **Platform** | Microsoft Copilot Studio |
| **Agent Type** | Custom Engine Agent (CEA) |
| **Knowledge Sources** | SharePoint folders dedicated to policy documents |
| **Integration Logic** | SharePoint for primary queries, Salesforce API via Agent Flows for escalation |
| **Escalation Trigger** | Requests for in-depth information (e.g., "Give me more details") |

The agent maps user intent (e.g. *finance*, *leave*, *security*, *operations*) to one of four Salesforce Knowledge Article titles:

* `KK-Enterprises Finance Policy Handbook`
* `KK-Enterprises Human Resources Policy Handbook`
* `KK-Enterprises IT & Security Policy Handbook`
* `KK-Enterprises Operations & Administration Policy Handbook`

The **Salesforce Detail Flow** is triggered only when "detail intent" keywords are detected: *details, full policy, complete, clauses, exceptions, eligibility, step-by-step, examples, evidence required, documentation*.

## Sample Prompts

* "How many paid holidays do employees get per year?"
* "List the exceptions mentioned in the travel reimbursement policy"
* "What is the approval process for expense claims over $500?"
* "Give me more details about the parental leave policy" *(triggers Salesforce escalation)*

## Business Value

| Metric | Value |
|--------|-------|
| **Reduced Retrieval Time** | Quick access to policy information from SharePoint |
| **Faster Query Resolution** | Immediate answers for common questions |
| **Optimized Access** | Smart routing between short summaries and detailed info |
| **Seamless Escalation** | Automatic handoff to Salesforce for complex queries |

## Contributors

* [Keshav Keshari](https://github.com/keshavk-msft)

## Version history

| Version | Date           | Comments         |
| ------- | -------------- | ---------------- |
| 1.0     | June 29, 2026  | Initial release  |

## Prerequisites

* Microsoft 365 tenant with **Copilot Studio** license
* A **SharePoint site** containing the organization's policy documents
* A **Salesforce** instance with Knowledge articles and API access (used by the escalation flow)
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
  cd samples/mcs-PolicyAgentCEA

  # Package up the solution. The SRC folder is what gets packed.
  pac solution pack --zipfile PolicyAgentCEA.zip --folder ./src
  ```

* Import into your chosen environment (omit `--environment` to use the default):

  ```powershell
  pac env list
  pac solution import --path ./PolicyAgentCEA.zip --environment <your-env-id> --publish-changes --activate-plugins
  ```

* After import, in [Copilot Studio](https://copilotstudio.microsoft.com):
  1. Open the **Policy Agent (CEA)** in your solution.
  2. Configure the **SharePoint** knowledge source with the URL of your policy site.
  3. Configure the **Salesforce** connection used by the `SalesforceFlow` Agent Flow (Connector → Salesforce).
  4. Publish to your channel of choice (Microsoft Teams, M365 Copilot, custom).

## Features

This sample extends Copilot Studio with an agent that:

* Uses a **Custom Engine Agent** to handle two retrieval tiers: SharePoint for summaries, Salesforce for full policy text.
* Maps user intent to one of four Salesforce Knowledge Article titles for deterministic routing.
* Triggers a **Salesforce Agent Flow** only when detail-intent keywords are detected.
* Returns answers with a **citation footer** (`Source: SharePoint / Salesforce`) and includes `EffectiveDate` + `Version` when sourced from Salesforce.
* Redacts confidential / PII content and refuses out-of-scope queries.

### Folder structure

```
mcs-PolicyAgentCEA/
├── PolicyAgentCEA.cdsproj          # MSBuild project (optional, for dotnet build / pipelines)
├── README.md
├── assets/
│   └── demo.mp4
└── src/                            # Produced by `pac solution unpack`
    ├── Other/
    │   ├── Solution.xml
    │   └── Customizations.xml
    ├── Assets/
    │   └── botcomponent_workflowset.xml
    ├── bots/
    │   └── cred8_kkPolicyAgent/    # Agent definition + topics, knowledge, actions
    ├── botcomponents/              # Topics, GPT config, knowledge & action components
    └── Workflows/                  # SalesforceFlow Agent Flow
```

## Related resources

* [Copilot Studio documentation](https://learn.microsoft.com/en-us/microsoft-copilot-studio/)
* [Move copilots between environments (Copilot Studio ALM)](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-export-import-bots)
* [Power Platform CLI `pac solution` reference](https://learn.microsoft.com/en-us/power-platform/developer/cli/reference/solution)
* [VS Code Copilot Studio extension](https://marketplace.visualstudio.com/items?itemName=ms-CopilotStudio.vscode-copilotstudio)
* [Salesforce API documentation](https://developer.salesforce.com/docs/apis)

## Help

We do not support samples, but this community is always willing to help, and we want to improve these samples. We use GitHub to track issues, which makes it easy for community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues?q=label%3A%22sample%3A%20mcs-PolicyAgentCEA%22) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new). Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

## Disclaimer

**THIS CODE IS PROVIDED AS IS WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

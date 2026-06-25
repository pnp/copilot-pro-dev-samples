# Policy Agent - Custom Engine Agent with Escalation

A Custom Engine Agent built in Microsoft Copilot Studio that handles both summary-level and detailed clause-level policy queries, with Salesforce escalation for in-depth assistance.

## Demo

https://github.com/user-attachments/assets/cc37e754-7ecd-4627-aa7e-3a8cf059467b

## Problem Statement

Employees need varying levels of policy information - from quick summaries to detailed clause-level specifics. Common challenges include:
- Simple queries require quick answers from SharePoint
- Complex queries need deeper investigation and expert assistance
- No seamless handoff between self-service and expert support
- Difficulty accessing detailed policy clauses and exceptions

## Solution Overview

This solution uses a **Custom Engine Agent (CEA)** in Copilot Studio with SharePoint integration and Salesforce escalation:

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

## Sample Prompts

- "How many paid holidays do employees get per year?"
- "List the exceptions mentioned in the travel reimbursement policy"
- "What is the approval process for expense claims over $500?"
- "Give me more details about the parental leave policy" (triggers escalation)

## Business Value

| Metric | Value |
|--------|-------|
| **Reduced Retrieval Time** | Quick access to policy information from SharePoint |
| **Faster Query Resolution** | Immediate answers for common questions |
| **Optimized Access** | Smart routing between short summaries and detailed info |
| **Seamless Escalation** | Automatic handoff to Salesforce for complex queries |

## Deployment

### Prerequisites
- Microsoft Copilot Studio license
- SharePoint site with policy documentation
- Salesforce instance with API access
- VS Code with Copilot Studio extension (optional, for source control)

### Import Steps
1. Open Microsoft Copilot Studio
2. Import the agent source from the `src/` folder using the Copilot Studio extension for VS Code
3. Configure SharePoint knowledge sources with your policy documents (update the `site` URL in `src/knowledge/`)
4. Set up the Salesforce connection in your environment and update the workflow under `src/workflows/SalesforceFlow-*/`. Replace the `<YOUR_SALESFORCE_*>` placeholders in `workflow.json` (Consumer Key, Consumer Secret, Username, Security Token) and the `<YOUR_SALESFORCE_INSTANCE>` host with your org values.
5. Test the agent with sample prompts (both summary and detail queries)
6. Publish to your desired channel

## Folder Structure

```
mcs-policy-agent-cea/
├── README.md                    # This file
├── assets/
│   └── sample.json              # PnP sample gallery metadata
└── src/
    ├── agent.mcs.yml            # Agent definition
    ├── settings.mcs.yml         # Agent settings
    ├── icon.png                 # Agent icon
    ├── knowledge/               # Knowledge configuration
    ├── topics/                  # Conversation topics
    ├── actions/                 # API action definitions
    └── workflows/               # Agent flow workflows
```

## Related Resources

- [Copilot Studio Documentation](https://learn.microsoft.com/en-us/microsoft-copilot-studio/)
- [VS Code Copilot Studio Extension](https://marketplace.visualstudio.com/items?itemName=ms-CopilotStudio.vscode-copilotstudio)
- [Salesforce API Documentation](https://developer.salesforce.com/docs/apis)

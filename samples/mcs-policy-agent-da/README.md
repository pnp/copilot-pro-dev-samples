# Policy Agent - Declarative Agent

A SharePoint-grounded Declarative Agent built in Microsoft Copilot Studio that provides quick, summary-level answers to policy-related questions.

## Demo

https://github.com/user-attachments/assets/2d68cfe9-1742-472a-ac77-f36d05d009b6

## Problem Statement

Employees frequently need quick access to company policies across HR, IT, Finance, and other departments. Common challenges include:
- Time wasted searching through multiple SharePoint sites and documents
- Inconsistent answers when policies are spread across different locations
- Inability to get quick summaries without reading entire policy documents
- Lack of multi-file referencing for comprehensive answers

## Solution Overview

This solution uses a **Declarative Agent (DA)** in Copilot Studio with SharePoint as the primary knowledge source:

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

- "What is the company's IT usage policy?"
- "What documents or evidence are required under the health insurance policy?"
- "Summarize the vacation policy for full-time employees"
- "What are the key points in our data protection policy?"

## Business Value

| Metric | Value |
|--------|-------|
| **Faster Go-Live** | Quick to build and deploy with minimal configuration |
| **Enhanced Retrieval** | Deep answers with multi-file referencing capabilities |
| **Scalability** | Ability to cover larger data sets for grounding |
| **M365 Integration** | Powerful grounding on organizational data via SharePoint and Graph |

## Deployment

### Prerequisites
- Microsoft Copilot Studio license
- SharePoint site with policy documentation
- VS Code with Copilot Studio extension (optional, for source control)

### Import Steps
1. Open Microsoft Copilot Studio
2. Import the agent source from the `src/` folder using the Copilot Studio extension for VS Code
3. Configure SharePoint knowledge sources with your policy documents (update the `site` URL in `src/knowledge/SharePointSearchSource.0.mcs.yml`)
4. Test the agent with sample prompts
5. Publish to your desired channel

## Folder Structure

```
mcs-policy-agent-da/
├── README.md                    # This file
├── assets/
│   └── sample.json              # PnP sample gallery metadata
└── src/
    ├── agent.mcs.yml            # Agent definition
    ├── settings.mcs.yml         # Agent settings
    ├── icon.png                 # Agent icon
    ├── knowledge/               # Knowledge configuration
    └── topics/                  # Conversation topics
```

## Related Resources

- [Copilot Studio Documentation](https://learn.microsoft.com/en-us/microsoft-copilot-studio/)
- [VS Code Copilot Studio Extension](https://marketplace.visualstudio.com/items?itemName=ms-CopilotStudio.vscode-copilotstudio)

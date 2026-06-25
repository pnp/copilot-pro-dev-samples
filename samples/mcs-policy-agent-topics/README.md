# Policy Agent - Topic-Based Grounding

A Custom Engine Agent built in Microsoft Copilot Studio that uses topic-based folder structure in SharePoint for deterministic, precise policy responses.

## Demo

https://github.com/user-attachments/assets/e6c3d7d3-015e-4f67-ac9e-2f5d4a6c8294

## Problem Statement

Organizations with policies spread across multiple departments need precise, targeted responses. Common challenges include:
- Generic responses that don't address specific departmental policies
- Difficulty routing queries to the right knowledge source
- Lack of precision when policies overlap across departments
- Need for deterministic behavior in policy lookups

## Solution Overview

This solution uses a **Custom Engine Agent (CEA)** in Copilot Studio with topic-based SharePoint folder mapping:

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

## Sample Prompts

- "What's the code of conduct policy for new employees?"
- "Explain the step-by-step process for submitting expense claims"
- "What are the IT security guidelines for remote work?"
- "How do I request time off according to HR policy?"

## Business Value

| Metric | Value |
|--------|-------|
| **Faster Info Retrieval** | Direct routing to relevant policy folder |
| **Better Resolution Rate** | Improved user query resolution percentage |
| **Enhanced Precision** | Deterministic systems provide accurate, targeted answers |
| **Structured Organization** | Clear folder structure makes maintenance easier |

## Deployment

### Prerequisites
- Microsoft Copilot Studio license
- SharePoint site with topic-organized folder structure
- VS Code with Copilot Studio extension (optional, for source control)

### SharePoint Setup
Create folders for each policy domain:
```
/Policies
  ├── /Finance
  │   ├── expense-policy.docx
  │   └── travel-reimbursement.docx
  ├── /HR
  │   ├── code-of-conduct.docx
  │   └── leave-policy.docx
  └── /IT
      ├── security-guidelines.docx
      └── acceptable-use.docx
```

### Import Steps
1. Open Microsoft Copilot Studio
2. Import the agent source from the `src/` folder using the Copilot Studio extension for VS Code
3. Configure SharePoint knowledge sources with your topic folders (update the `site` URLs in `src/knowledge/`)
4. Map each folder to corresponding agent topics
5. Test the agent with sample prompts across different topics
6. Publish to your desired channel

## Folder Structure

```
mcs-policy-agent-topics/
├── README.md                    # This file
├── assets/
│   └── sample.json              # PnP sample gallery metadata
└── src/
    ├── agent.mcs.yml            # Agent definition
    ├── settings.mcs.yml         # Agent settings
    ├── knowledge/               # Topic-organized knowledge config
    └── topics/                  # Topic definitions (mapped to folders)
```

## Related Resources

- [Copilot Studio Documentation](https://learn.microsoft.com/en-us/microsoft-copilot-studio/)
- [VS Code Copilot Studio Extension](https://marketplace.visualstudio.com/items?itemName=ms-CopilotStudio.vscode-copilotstudio)

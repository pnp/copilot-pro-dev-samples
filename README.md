# My Security Agent

A Microsoft 365 Copilot declarative agent that empowers end users to efficiently manage identity-related tasks through natural language interactions. Available in Microsoft 365 Interfaces including but not limited to Copilot, Teams, and Outlook.

### Architecture Flow

```
manifest.json          declarativeAgent.json          ai-plugin.json              myagentall-openapi.yml
description      ──────> instructions            ──────> functions           ──────> Microsoft Graph API
app icons               capabilities                    authentication              identity operations
permissions            actions                         response semantics
```

## Prerequisites

- **Node.js** (versions 18, 20, or 22)
- **Microsoft 365 dev tenant account** for development
- **Microsoft 365 Agents Toolkit** (VS Code Extension v5.0.0+ or CLI)
- **Microsoft 365 Copilot license**
- **Enterprise Admin permissions** for deployment

> **Important Note**
>
> By design, the manifest file references the required resources but does not create or deploy them. To test the sample, you should download the source code and provision the DA using Agents Toolkit in VS Code (F5), which will automatically create the app registration and authentication configuration in Teams Developer Portal.

## Getting Started

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd MYSECURITYAGENT

# Install dependencies (if any)
npm install
```

### Local Development & Testing

1. **Open in VS Code**
   - Select the Microsoft 365 Agents Toolkit icon in the left toolbar
   - Sign in with your Microsoft 365 development account

2. **Provision the App**
   - Click `Provision` in the "Lifecycle" section
   - This automatically creates the app registration and authentication configuration in Teams Developer Portal

3. **Preview & Test**
   - Open Copilot interface of choice (Teams is ideal).
   - Once loaded, select "Copilot" tab
   - Find your declarative agent in the right rail
   - Test with sample queries like "What groups do I belong to?" or additional capabilities added by you

### Distributing to Other Users

To distribute this agent to other users in your organization, you have two options:

#### Option 1: Using the generated app package (Recommended)
- Use the generated `appPackage.dev.zip` from the build folder (created during provisioning)
- Upload the generated app package to the organisation store via the Integrated Apps section (https://admin.microsoft.com/#/Settings/IntegratedApps) in Microsoft 365 Admin Centre
- This will make the agent available in the marketplace and will reuse the app registration created when provisioning the agent from VS Code

#### Option 2: Manual configuration
- If you don't want to use the automation in Toolkit, you will need to manually create the app registration and auth configuration in Teams Developer Portal
- This will require you to generate an app package with the correct references

### Teams Admin Center Deployment

1. **Prepare App Package**
   - Use the generated `appPackage.dev.zip` from the build folder
   - Ensure all permissions align with your security policies

2. **Upload to Admin Center**
   ```bash
   # Navigate to Teams Admin Center
   # Teams apps → Manage apps → Upload
   # Select the .zip file from appPackage/build/
   ```

3. **Configure Permissions**
   - **Allow custom apps** under Teams apps → Permission policies
   - **Explicitly approve** "My Security Agent" if needed

4. **Setup Policies**
   - Navigate to Teams apps → Setup policies
   - Add "My Security Agent" under Installed apps
   - Create or edit policies for target user groups

5. **User Assignment**
   - Apply setup policy to target users or groups
   - Use bulk assignment for large deployments
   - **Note**: Policy propagation can take up to 24 hours

6. **Validation & Testing**
   - Test with pilot users to confirm functionality
   - Verify the agent appears in Teams and Copilot interfaces
   - Use **developer mode** for enhanced debugging: `-developer on`

## Configuration

The agent will extend as far as the delegated permissions that you allow (defined in `m365agents.yml`):

### Creating Custom OpenAPI Specifications

Use Microsoft's `hidi` tool to generate API specifications, or LLM of choice:

```bash
# Install hidi globally
dotnet tool install --global Microsoft.OpenApi.Hidi

# Generate specific endpoints from Microsoft Graph
hidi transform -d openapi.yaml -f yaml -o custom-endpoints.yml -v 3.0 --op me.ListOwnedDevices --co

# Example: Extract user profile operations
hidi transform -d msgraph-openapi.yaml -f yaml -o user-profile.yml -v 3.0 --op me.GetProfile --co
```

### Useful Resources

- [Microsoft 365 Agents Toolkit Guide](https://github.com/OfficeDev/TeamsFx/wiki/Teams-Toolkit-Visual-Studio-Code-v5-Guide#overview)
- [Declarative Agents Documentation](https://learn.microsoft.com/microsoft-365-copilot/extensibility/build-declarative-agents)
- [Microsoft Graph OpenAPI](https://github.com/microsoftgraph/msgraph-metadata/blob/master/openapi/beta/openapi.yaml)

## Extending the Agent

### Add New Capabilities

1. **Web Content Integration**
   - [Add web search capabilities](https://learn.microsoft.com/microsoft-365-copilot/extensibility/build-declarative-agents?tabs=ttk&tutorial-step=4)

2. **Knowledge Base Integration**
   - [OneDrive and SharePoint content](https://learn.microsoft.com/microsoft-365-copilot/extensibility/build-declarative-agents?tabs=ttk&tutorial-step=5)
   - [Microsoft Copilot connectors](https://learn.microsoft.com/microsoft-365-copilot/extensibility/build-declarative-agents?tabs=ttk&tutorial-step=6)

3. **API Plugin Extensions**
   - [Add custom REST APIs](https://learn.microsoft.com/microsoft-365-copilot/extensibility/build-declarative-agents?tabs=ttk&tutorial-step=7)

## Support & Contributing

For support or feedback:

- **Email**: [t-paagarwal@microsoft.com](mailto:t-paagarwal@microsoft.com), [Merill.F@microsoft.com](mailto:Merill.F@microsoft.com), [jasuri@microsoft.com](mailto:jasuri@microsoft.com)

---

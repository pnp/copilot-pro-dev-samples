# Retirement Radar for Copilot Cowork

## Summary

Retirement Radar helps you find retired and deprecated Microsoft technology before an old script fails in production.

Give Copilot Cowork a script, configuration file, package list, or architecture note. Retirement Radar checks every Microsoft API, SDK, PowerShell module, endpoint, and service it finds against live Microsoft Learn documentation, then returns:

- A clear supported, deprecated, or retired verdict
- Official retirement dates and Microsoft Learn sources
- Supported replacements
- Updated code based on official samples
- A prioritized migration checklist

## Contributors

* [Rabia Williams](https://github.com/rabwill)

## Version history

Version|Date|Comments
-------|----|--------
1.1.2|October 22, 2026|Initial community sample release

## Prerequisites

You need:

- Access to **Microsoft 365 Copilot Cowork**
- Copilot Credits for testing in Cowork
- Permission to upload custom plugins in your organization
- [Work IQ Dev Tools (WIQD) CLI](https://microsoft.github.io/wiqd/getting-started/installation/) with the `wiqd plugin` commands available (`wiqd plugin --help`)
- Permission to register and provision Microsoft 365 apps in your tenant

The plugin uses the public, read-only [Microsoft Learn MCP server](https://learn.microsoft.com/api/mcp). It does not require an API key or a connector sign-in. WIQD still requires Microsoft 365 sign-in to provision the app.

## Minimal path to awesome

### 1. Prepare the WIQD project

Clone or download this repository. From this sample's directory, enter `src` and create your local environment file.

macOS/Linux:

```sh
cd src
cp env/.env.local.sample env/.env.local
```

PowerShell:

```powershell
Set-Location src
Copy-Item env/.env.local.sample env/.env.local
```

Run all remaining WIQD commands from `src`, the project root containing `wiqd.plugin.json` and `m365agents.yml`.

### 2. Validate, provision, and package

```sh
wiqd auth login --interactive
wiqd plugin provision --env local
wiqd plugin package --env local
wiqd plugin validate --mode deep --env local
```

These commands provision the plugin in your signed-in Microsoft 365 tenant and create `src/appPackage/build/appPackage.local.zip`. The `local` environment still uses your tenant; it is not an offline deployment.

Do not commit generated ZIPs or environment files containing IDs or credentials.

### 3. Enable it in Cowork

1. Open **Microsoft 365 Copilot Cowork**.
2. Open the plugin inventory.
3. Find **Retirement Radar** and enable it for the current Cowork session.

If a custom upload is required, upload the generated `appPackage.local.zip`. You should see the **Retirement Radar** skill and **Microsoft Learn** connector. The connector needs no additional sign-in.

### 4. Run the demo

Paste the [legacy administration demo script](src/demo/legacy-admin-script%20copy.txt) into Cowork with this prompt. **Do not execute the script**; it intentionally uses retired technologies.

> Is this still safe to run tonight? Check it for retired Microsoft APIs.

Expect a risk-ranked report with Microsoft Learn sources and supported replacements. Results may change as Microsoft updates its documentation.

### 5. Ask for the migration

Continue in the same Cowork session:

> Rewrite the whole script with the supported replacements.

Review the generated code and test it in a non-production environment before use.

## More prompts to try

Try it with application code, dependency files, or architecture notes:

```text
Check this project for deprecated Microsoft SDKs and APIs. Cite an official source for every finding.
```

```text
Which dependencies in this package file need migration within the next 12 months?
```

Do not paste live secrets, access tokens, connection strings, or production webhook URLs into the chat. Replace them with redacted values first.

## Features

- Inventories Microsoft APIs, SDKs, PowerShell modules, endpoints, and services in supplied text.
- Uses live Microsoft Learn documentation to verify support status and dated claims.
- Produces a risk-ranked report with official sources and supported replacements.
- Uses official code samples to suggest migration changes.
- Demonstrates a Cowork plugin with an agent skill and an anonymous remote MCP connector, without a hosted backend.

Generated findings and migration code require human review. Test proposed changes in a non-production environment before using them.

### What is in the plugin

| Source | Purpose |
|---|---|
| [WIQD project](src/wiqd.plugin.json) | Identifies the plugin and its capabilities |
| [Lifecycle configuration](src/m365agents.yml) and [local configuration](src/m365agents.local.yml) | Provision and package the app |
| [App package source](src/appPackage/) | Manifest, icons, Microsoft Learn tools, and the Retirement Radar skill |
| [Environment templates](src/env/) | Starting configuration without generated IDs |

This is a standalone Cowork plugin with no declarative agent or hosted backend.

## Troubleshooting

| Problem | Try this |
|---|---|
| WIQD does not recognize the project | Run commands from `src` and check that WIQD is up to date. |
| Missing environment or app ID | Copy the environment template, then complete provisioning before packaging. |
| Plugin is missing in Cowork | Check the signed-in account, reopen the plugin inventory, and enable Retirement Radar. |
| Package upload fails | Re-run packaging and deep validation, then upload the generated ZIP without repackaging it. |
| Skill does not activate | Include **retired**, **deprecated**, or **still supported** in your prompt. |
| Microsoft Learn is unavailable | Check that your organization allows `https://learn.microsoft.com/api/mcp`. |

## Learn more

- [WIQD cookbooks](https://aka.ms/wiqd/cookbooks)
- [WIQD: Build a Plugin](https://microsoft.github.io/wiqd/getting-started/build-a-plugin/)
- [WIQD plugin authoring reference](https://microsoft.github.io/wiqd/getting-started/plugin-reference/)
- [Copilot Camp: Build your first Copilot Cowork plugin](https://aka.ms/copilotdevcamp/plugin)

<!--
RESERVED FOR REPO MAINTAINERS

We'll add the video from the community call recording here.
-->

## Help

We do not support samples, but this community is always willing to help, and we want to improve these samples. We use GitHub to track issues, which makes it easy for community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues?q=label%3A%22sample%3A%20plugin-retirement-radar%22) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

<img src="https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/samples/plugin-retirement-radar" />

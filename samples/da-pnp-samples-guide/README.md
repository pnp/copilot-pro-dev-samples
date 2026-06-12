# Discover and adopt PnP declarative agent samples with Microsoft 365 Copilot

## Summary

This sample is a **declarative agent** for Microsoft 365 Copilot that helps developers discover, understand, and adopt declarative agent samples from the [pnp/copilot-pro-dev-samples](https://github.com/pnp/copilot-pro-dev-samples) repository — and guides them on how to bootstrap their own agent inspired by those samples.

The agent uses an **API plugin** that calls a small, hand-stripped subset of the public, unauthenticated **GitHub REST API** to search code, list repo contents, and read READMEs. It also uses **WebSearch** scoped to the samples repo as a low-cost grounding fallback.

> No backend service is required. The agent talks directly to `api.github.com` with anonymous calls.

![Declarative agent discovering samples by capability](assets/screenshot-discovery.png)
![Declarative agent guiding through cloning a sample](assets/screenshot-clone.png)

## Features

This sample illustrates the following concepts:

* Building a **declarative agent** for Microsoft 365 Copilot using **v1.7** of the manifest
* Wiring an **API plugin** (v2.4) to an external, **unauthenticated** REST API (`auth.type: None`)
* Stripping a large public OpenAPI spec down to only the endpoints you need
* Using the **`WebSearch`** capability scoped to a single site (max 4 sites, max 2 path segments — per the v1.7 schema)
* Designing **`description_for_model`** so the LLM picks the right action with the right query
* Adaptive Cards for each operation (`searchRepositories`, `searchCode`, `getRepo`, `getRepoContent`, `getRepoReadme`)
* Documenting and gracefully handling **rate limits** (60 req/hour per IP for unauthenticated GitHub calls)

## Applies to

* [Microsoft 365 Copilot](https://learn.microsoft.com/en-us/microsoft-365/copilot/) tenants with the **Microsoft 365 Copilot license**
* [Declarative agent manifest **v1.7**](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-manifest-1.7)
* [API plugin manifest **v2.4**](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api-plugin-manifest)

## Solution

Solution | Author(s)
---------|----------
da-pnp-samples-guide | Microsoft engineers, MVPs, and community members

## Version history

Version | Date | Comments
--------|------|---------
1.0 | June 12, 2026 | Initial release

## Prerequisites

* A Microsoft 365 tenant with **Microsoft 365 Copilot** licensed and Copilot extensibility enabled
* [Node.js LTS](https://nodejs.org/) (only required if you use the `wiqd` CLI)
* One of:
  * [Microsoft 365 Agents Toolkit for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=TeamsDevApp.ms-teams-vscode-extension), or
  * The [`wiqd` CLI](https://aka.ms/wiqd) (`iex "& { $(irm 'https://aka.ms/wiqd/install.ps1') }"`)
* An internet connection from the runtime — the agent calls `api.github.com` directly

## Minimal permissions and data

This sample uses **anonymous** GitHub REST calls. **No GitHub token is stored, sent, or required.** The only data flowing out of the user's tenant is the search query and the path/owner/repo parameters passed to GitHub's public API.

The Teams app manifest declares `validDomains` of:

* `api.github.com`
* `raw.githubusercontent.com`
* `github.com`

These are needed for the API plugin runtime and for the `WebSearch` capability to follow links into the samples repo.

## Minimal Path to Awesome

1. **Clone this repository**
   ```bash
   git clone https://github.com/pnp/copilot-pro-dev-samples.git
   cd copilot-pro-dev-samples/samples/da-pnp-samples-guide
   ```
2. **Open the `M365Agent` folder** in Visual Studio Code with the Microsoft 365 Agents Toolkit extension installed, **or** continue with the `wiqd` CLI below.
3. **Sign in** to your Microsoft 365 tenant with the toolkit (Agents Toolkit panel → *Sign in to Microsoft 365*).
4. **Provision** the agent to your tenant:
   * **Toolkit:** *Provision* command from the Agents Toolkit panel.
   * **CLI:** from inside `M365Agent/`, run:
     ```powershell
     wiqd agent provision --env dev
     ```
5. **Open Microsoft 365 Copilot**, switch to the agent named **"Copilot PnP Samples Guide"**, and try one of the conversation starters:
   * *"Find me a sample that uses Code Interpreter"*
   * *"Show me samples that include an API plugin with authentication"*
   * *"How do I clone and run the da-ristorante-api-csharp sample?"*

> The first call against `api.github.com` may take a moment as Copilot warms up the plugin runtime. Subsequent calls are fast.

## Rate limits to be aware of

GitHub's REST API limits **unauthenticated** clients to roughly **60 requests/hour per IP**. If the agent returns an HTTP 403 with a rate-limit message:

* Tell the user to wait an hour, **or**
* Browse the samples directly at [github.com/pnp/copilot-pro-dev-samples](https://github.com/pnp/copilot-pro-dev-samples).

For higher limits, an authenticated variant would require swapping the API plugin's auth block to `OAuthPluginVault` with a GitHub OAuth app — out of scope for this sample by design.

## Project structure

```
da-pnp-samples-guide/
├── README.md
├── .gitignore
└── M365Agent/
    ├── m365agents.yml              # Provision pipeline (dev)
    ├── m365agents.local.yml        # Provision pipeline (local)
    ├── env/
    │   └── .env.dev                # Env vars (gitignored *.user overrides)
    └── appPackage/
        ├── manifest.json           # Teams app manifest (v1.24)
        ├── declarativeAgent.json   # Declarative agent manifest (v1.7)
        ├── instruction.txt         # Agent instructions
        ├── ai-plugin.json          # API plugin manifest (v2.4)
        ├── github-openapi.json     # Stripped GitHub REST OpenAPI spec
        ├── color.png               # 192x192 color icon
        ├── outline.png             # 32x32 outline icon
        └── large.png               # Optional larger icon
```

## Screenshots

> Add screenshots to `assets/` before publishing.

* `assets/screenshot-discovery.png` — Copilot returning a list of matching samples
* `assets/screenshot-clone.png` — Copilot walking through the clone-and-run steps

## Contributors

Microsoft engineers, MVPs, and community members.

## Help

We do not support samples, but the community is always willing to help and we want to improve these samples. We use GitHub to track issues, which makes it easy for community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues?q=label%3A%22sample%3A%20da-pnp-samples-guide%22) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

<img src="https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/samples/da-pnp-samples-guide" />

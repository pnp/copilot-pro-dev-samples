---
name: retirement-radar
description: Scans code, scripts, config files, package lists or architecture notes for Microsoft APIs, SDKs, PowerShell modules, endpoints and services that are deprecated or retired, verifies each one live against official Microsoft Learn documentation, and returns a dated risk table with the supported replacement and a rewritten snippet. Use when the user asks "is this still supported?", "what's deprecated in my code?", "why did my script/webhook stop working?", "check my dependencies for retirement", or pastes code that uses AzureAD, MSOnline, AzureRM, ADAL, Azure AD Graph, Office 365 connectors or other legacy Microsoft tech. Do not use for general coding help unrelated to deprecation or for non-Microsoft technologies.
license: MIT
compatibility: Requires the Microsoft Learn MCP server (https://learn.microsoft.com/api/mcp) with the tools microsoft_docs_search, microsoft_docs_fetch and microsoft_code_sample_search.
metadata:
  author: Contoso Cloud Advocacy
  version: "1.0.0"
---

# Retirement Radar

Turn "I think this still works" into "here is the official date, the replacement, and the fixed code".

## When to use
- The user pastes code, a script, `package.json`, `.csproj`, `requirements.txt`, an ARM/Bicep template, or a description of their architecture.
- The user asks whether something is deprecated, retired, still supported, or why it suddenly stopped working (401/403/410 errors from an old endpoint are a strong signal).

## Step 1 - Inventory the signals
Extract every Microsoft technology reference. Look for:

| Signal type | Examples |
|---|---|
| PowerShell modules / cmdlet prefixes | `Connect-AzureAD`, `*-AzureAD*`, `Connect-MsolService`, `*-Msol*`, `*-AzureRM*` |
| Packages | `Microsoft.IdentityModel.Clients.ActiveDirectory` (ADAL.NET), `adal` (Python/Node), `msrestazure`, `WindowsAzure.Storage`, `Microsoft.Azure.Management.*` |
| Endpoints | `graph.windows.net` (Azure AD Graph), `outlook.office.com/webhook`, `*.webhook.office.com/webhookb2` (Office 365 connectors), `login.windows.net` |
| Services / features | Office 365 connectors in Teams, basic auth for Exchange Online, classic (ASM) resources |

Record where each signal appears (line number or snippet) so the report can point to it.

## Step 2 - Verify every signal on Microsoft Learn
For each signal, in this order:
1. `microsoft_docs_search` with `"<technology> retirement date"` or `"<technology> deprecated migrate to"`.
2. If the excerpt does not contain a date or a named replacement, call `microsoft_docs_fetch` on the most relevant `learn.microsoft.com` URL from the search results.
3. Capture: status wording, the exact date(s), the named replacement, and the source URL.

Hard rule: never state a date, status or replacement you did not read in a tool result. If nothing is found, report "No retirement notice found on Learn".

## Step 3 - Classify against today's date
| Status | Rule |
|---|---|
| Broken now | Official retirement / end-of-support date is in the past |
| Breaking soon | Retirement date is within the next 12 months |
| Deprecated | Docs say deprecated / no new investment, but no firm date |
| OK | Verified current, or no retirement notice found |

## Step 4 - Build the fix
For every non-OK finding, call `microsoft_code_sample_search` for the replacement, passing `language` to match the user's code (for example `powershell`, `csharp`, `python`). Rewrite only the affected lines, preserve the user's variable names, and keep the result runnable.

## Step 5 - Report
Use the template in [references/report-template.md](references/report-template.md):
1. One-line verdict, for example: "3 of 5 Microsoft dependencies in this script are already retired."
2. Risk table: Finding | Where | Status | Official date | Replacement | Source.
3. Before -> After code blocks for the highest-risk findings.
4. Prioritized migration checklist (Broken now first, then Breaking soon, then Deprecated).

## Safety
- If the input contains secrets (keys, tokens, connection strings, webhook URLs) warn the user and redact them in the output.
- Do not invent cmdlets, packages or endpoints. If a replacement mapping is not in the docs, say so.

---
name: declarative-agent-sample-review
description: Review PRs for declarative agent samples (da-* folders) in pnp/copilot-pro-dev-samples. Use when reviewing da-* sample submissions, checking manifest versions, validating README format. Triggers on "review PR", "review this sample", or PR review requests for declarative agent samples.
---

# Declarative Agent Sample Review

Review declarative agent sample PRs (folders starting with `da-`) for compliance with repo guidelines.

## Workflow

1. Checkout PR: `gh pr checkout <number>`
2. Verify sample folder starts with `da-`
3. Run checks below, collecting comments (file, line, issue) 
4. Submit all comments in single API call (GitHub limitation)

## Checks

### 1. Manifest Schema Versions

Fetch latest versions from Microsoft Learn docs (never use other samples as reference):

| Manifest | File | Property | Docs |
|----------|------|----------|------|
| App | `appPackage/manifest.json` | `manifestVersion` | learn.microsoft.com/microsoft-365/extensibility/schema |
| Declarative Agent | `appPackage/*DeclarativeAgent.json` | `version` + `$schema` | learn.microsoft.com/microsoft-365-copilot/extensibility/declarative-agent-manifest |
| API Plugin | `appPackage/ai-plugin.json` | `schema_version` | learn.microsoft.com/microsoft-365-copilot/extensibility/api-plugin-manifest |

### 2. m365agents.yml

- **No `projectId`** - auto-generated on provision, must not be committed
- Check both `m365agents.yml` and `m365agents.local.yml`

### 3. README.md

Compare against `templates/README-template.md`:

- **Contributors section** present with actual author names
- **Version history** lists real author (not "Microsoft")
- **Tracking image** uses markdown format at end of file:
  ```
  ![](https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/<sample-folder>)
  ```
- **URLs** consistent (avoid mixed `en-us/` locales in same file)
- **No trailing `---`** at end

### 4. assets/sample.json

Compare against `templates/sample-template.json`:

- **name**: `pnp-copilot-pro-dev-<sample-folder>`
- **url/downloadUrl**: correct sample folder path
- **authors**: matches actual contributors (verify against PR author)
- **URLs**: consistent locale format

## Submitting Reviews

GitHub API cannot add comments to pending reviews after creation. Collect all comments first.

Get commit SHA:
```bash
gh pr view <PR> --json headRefOid
```

Create `review.json`:
```json
{
  "commit_id": "<sha>",
  "event": "REQUEST_CHANGES",
  "body": "Summary message",
  "comments": [
    {"path": "file/path", "line": 10, "body": "Issue description"}
  ]
}
```

Submit:
```bash
gh api repos/pnp/copilot-pro-dev-samples/pulls/<PR>/reviews --method POST --input review.json
```

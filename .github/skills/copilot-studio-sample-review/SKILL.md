---
name: copilot-studio-sample-review
description: Review PRs for Microsoft Copilot Studio samples (mcs-* folders) in pnp/copilot-pro-dev-samples.
---

# Copilot Studio Sample Review

Review Copilot Studio sample PRs (folders starting with `mcs-`) for compliance with repo guidelines.
Use when a request asks to review an `mcs-*` sample PR (e.g., "review PR" or "review this sample").

## Workflow

1. Checkout PR: `gh pr checkout <number>`
2. Verify sample folder starts with `mcs-`
3. Run checks below, collecting comments (file, line, issue)
4. Submit all comments in single API call (GitHub limitation)

## Checks

### 1. Folder and file structure

- Sample is under `samples/mcs-*`
- Required top-level files/folders are present: `README.md`, `assets/`, `src/`
- `assets/sample.json` exists and includes correct sample folder references

### 2. No packaged exports

- Request changes if any packaged `.zip` exports are committed under `samples/mcs-*` (e.g., `samples/mcs-example/export.zip`). Extracted source files are required, whether the contributor used `pac solution clone` or the VS Code clone method.
- Copilot Studio exports must be committed as extracted source files only

### 3. README and template alignment

- README is based on `/templates/mcs-copilot-studio/README.md`
- Setup steps include one of the supported contributor flows:
  - Solution export via Power Platform CLI (`pac solution clone`)
  - Copilot Studio Visual Studio Code clone method

### 4. Metadata consistency

- `assets/sample.json` `name` uses `pnp-copilot-pro-dev-<sample-folder>`
- `url` and `downloadUrl` target the correct `samples/mcs-*` path
- Author information and thumbnail paths match repository conventions

## Submitting Reviews

GitHub API does not support adding comments to a review after it has been created. Collect all comments first and submit them in one API call.

Get commit SHA:
```bash
gh pr view <PR> --json headRefOid
```

Create `review.json`:
```json
{
  "commit_id": "<sha>",
  "event": "<REQUEST_CHANGES|COMMENT|APPROVE>",
  "body": "Summary message",
  "comments": [
    {"path": "file/path", "line": 10, "body": "Issue description"}
  ]
}
```

Use the review event type based on findings:

- `REQUEST_CHANGES`: blocking issues (e.g., `.zip` files in `samples/mcs-*/`, missing required `mcs-*` structure, or incorrect sample metadata paths)
- `COMMENT`: non-blocking feedback (e.g., small README wording/template improvements)
- `APPROVE`: checks pass

Submit:
```bash
gh api repos/pnp/copilot-pro-dev-samples/pulls/<PR>/reviews --method POST --input review.json
```

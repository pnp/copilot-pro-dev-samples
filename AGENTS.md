# AGENTS.md
> Instructions for coding agents contributing samples to this repository.

## Purpose
Community sample repository for Microsoft 365 Copilot agents built using code-first approaches.
Read [CONTRIBUTING.md](CONTRIBUTING.md) for full human-oriented guidance.

## Repository layout
| Path | Purpose |
|------|---------|
| `samples/` | One subfolder per sample |
| `templates/` | Submission templates for declarative-agent, custom-engine-agent, and Copilot Studio samples |

## Sample folder naming
Prefix the folder name based on sample type:
| Prefix | Type |
|--------|------|
| `da-` | Declarative agent |
| `cea-` | Custom engine agent (Azure Bot Framework) |
| `msgext-` | Microsoft 365 message extension |
| `mcs-` | Microsoft Copilot Studio agent |

Rules: lowercase, hyphens only, no periods.

## Required files
| File | Notes |
|------|-------|
| `assets/sample.json` | Rename and complete `assets/template-sample.json` from the project template when one is available |
| `assets/<screenshot>` | Replace `assets/pending-image.png` with at least one `.png`, `.jpg`, or `.gif` showing the sample in action |
| `README.md` | Rename and complete `README-template.md` from the project template when one is available; otherwise follow `CONTRIBUTING.md` |
| `.gitignore` | Appropriate for toolchain |
| `.env.*.sample` | Redacted copies of all env files |

## Using a project template
For sample types with a project template:

1. Copy the entire template directory to `samples/<sample-folder>`.
2. Rename `README-template.md` to `README.md`.
3. Rename `assets/template-sample.json` to `assets/sample.json`.
4. Replace `assets/pending-image.png` with a screenshot of the sample in action.
5. Replace every `YOUR_*`, `YOUR-*`, and `YYYY-MM-DD` placeholder in `README.md` and `assets/sample.json`.
6. Remove the optional video entry from `assets/sample.json` when the sample has no video.
7. Remove contributor instructions and files that do not apply, but preserve comments marked as reserved for repository maintainers.

Do not submit unresolved placeholder values or the placeholder image.

## Project type rules
Detect the project type from its sample folder prefix before selecting a template or validating its contents.

| Prefix | Project template | Additional requirements |
|--------|------------------|-------------------------|
| `da-` | `templates/da-declarative-agent/` | Include a Teams/M365 app package containing `manifest.json` and a declarative agent manifest. |
| `cea-` | `templates/cea-custom-engine-agent/` | Include the agent source and a Teams/M365 app package containing `manifest.json`. |
| `msgext-` | None; follow `CONTRIBUTING.md` | Include the message extension source and a Teams/M365 app package containing `manifest.json`. |
| `mcs-` | `templates/mcs-copilot-studio/` | Include exported or cloned Copilot Studio source in `src/`. |

All project types must include `assets/sample.json`, at least one screenshot in `assets/`, and a completed `README.md`.

## Schema versions
Always use the latest published schema version. Use the links below to identify the current latest — the version number is in the URL and can be incremented to find newer versions.

| Schema | Reference |
|--------|-----------|
| Teams/M365 `manifest.json` | `$schema: https://developer.microsoft.com/json-schemas/teams/v1.25/MicrosoftTeams.schema.json` (replace `v1.25` with latest) |
| Declarative agent manifest | [declarative-agent-manifest-1.6](https://learn.microsoft.com/microsoft-365-copilot/extensibility/declarative-agent-manifest-1.6) — replace `1.6` with latest |
| API plugin manifest | [api-plugin-manifest-2.4](https://learn.microsoft.com/microsoft-365-copilot/extensibility/api-plugin-manifest-2.4) — replace `2.4` with latest |

## `m365agents.yml` metadata
If the sample includes an `m365agents.yml`, add the following property after `version`:
```yaml
additionalMetadata:
  sampleTag: pnp-copilot-pro-dev:<sample-folder-name>
```
Replace `<sample-folder-name>` with the name of your sample folder under `samples/`.

## Rules
- Add the sample to the samples table in the root `README.md`
- Include `additionalMetadata` with the correct `sampleTag` in `m365agents.yml`
- DO NOT include `projectId` in `m365agents.yml`
- DO NOT commit secrets, API keys, tenant IDs, or app IDs
- DO NOT leave template placeholders or `pending-image.png` in a submitted sample
- DO NOT reference assets from external URLs — all assets in `assets/`
- DO NOT modify files outside the new sample folder
- DO NOT submit more than one sample per pull request
- If the sample contains `teamsapp.yml` or `teamsapp.local.yml`, it was scaffolded with Teams Toolkit (now renamed Microsoft 365 Agents Toolkit) and is likely out of date — update accordingly
- One branch per sample, forked from `main`, PR targets `main`

## Checklist
- [ ] Sample in `/samples/<prefix>-<folder>/`
- [ ] Sample added to the table in root `README.md`
- [ ] Uses the project template when one is available and includes a complete `README.md` and `assets/sample.json`
- [ ] No unresolved template placeholders or `pending-image.png`
- [ ] All schema versions target latest (see links above)
- [ ] No `projectId` in `m365agents.yml`
- [ ] `additionalMetadata.sampleTag` set in `m365agents.yml` (format: `pnp-copilot-pro-dev:<sample-folder-name>`)
- [ ] No `teamsapp.yml` or `teamsapp.local.yml` (update if present)
- [ ] No secrets or external asset links
- [ ] One PR per sample

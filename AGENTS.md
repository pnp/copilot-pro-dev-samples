# AGENTS.md
> Instructions for coding agents contributing samples to this repository.

## Purpose
Community sample repository for Microsoft 365 Copilot agents built using code-first approaches.
Read [CONTRIBUTING.md](CONTRIBUTING.md) for full human-oriented guidance.

## Repository layout
| Path | Purpose |
|------|---------|
| `samples/` | One subfolder per sample |
| `samples/_SAMPLE_templates/` | Templates — copy, do not edit |
| `templates/` | Supporting templates |

## Sample folder naming
Prefix the folder name based on sample type:
| Prefix | Type |
|--------|------|
| `da-` | Declarative agent |
| `cea-` | Custom engine agent (Azure Bot Framework) |

Rules: lowercase, hyphens only, no periods.

## Required files
| File | Notes |
|------|-------|
| `assets/sample.json` | See example below |
| `assets/<screenshot>` | At least one `.png`, `.jpg`, or `.gif` |
| `README.md` | Copy correct template (see below) |
| `.gitignore` | Appropriate for toolchain |
| `.env.*.sample` | Redacted copies of all env files |

## sample.json example
```json
[
  {
    "name": "pnp-copilot-pro-dev-da-example",
    "source": "pnp",
    "title": "Declarative Agent Example",
    "shortDescription": "A declarative agent sample for Microsoft 365 Copilot.",
    "url": "https://github.com/pnp/copilot-pro-dev-samples/tree/main/samples/da-example",
    "downloadUrl": "https://pnp.github.io/download-partial/?url=https://github.com/pnp/copilot-pro-dev-samples/tree/main/samples/da-example",
    "longDescription": [
      "A sample project that demonstrates how to build a declarative agent for Microsoft 365 Copilot."
    ],
    "creationDateTime": "2026-01-01",
    "updateDateTime": "2026-01-01",
    "products": ["Microsoft 365 Copilot"],
    "metadata": [
      { "key": "PLATFORM", "value": "Node.js" },
      { "key": "LANGUAGE", "value": "TypeScript" },
      { "key": "AGENT-TYPE", "value": "Declarative Agent" },
      { "key": "API-PLUGIN", "value": "No" },
      { "key": "GRAPH-CONNECTOR", "value": "No" }
    ],
    "thumbnails": [
      {
        "type": "image",
        "order": 100,
        "url": "https://github.com/pnp/copilot-pro-dev-samples/raw/main/samples/da-example/assets/example.png",
        "alt": "Screenshot of the sample"
      }
    ],
    "authors": [
      {
        "gitHubAccount": "username",
        "pictureUrl": "https://github.com/username.png",
        "name": "Sample Author"
      }
    ],
    "references": [
      {
        "name": "Microsoft 365 Copilot extensibility",
        "description": "Learn more about extensibility.",
        "url": "https://learn.microsoft.com/microsoft-365-copilot/extensibility/"
      }
    ]
  }
]
```

## README template selection
| Toolchain | Template |
|-----------|----------|
| Teams Toolkit for VS Code | `samples/_SAMPLE_templates/ttk-vs-code-sample/README.md` |
| Teams Toolkit for Visual Studio | `samples/_SAMPLE_templates/ttk-vs-sample/README.md` |
| Other | `samples/_SAMPLE_templates/any-sample/README.md` |

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
- DO NOT reference assets from external URLs — all assets in `assets/`
- DO NOT modify files outside the new sample folder
- DO NOT submit more than one sample per pull request
- If the sample contains `teamsapp.yml` or `teamsapp.local.yml`, it was scaffolded with Teams Toolkit (now renamed Microsoft 365 Agents Toolkit) and is likely out of date — update accordingly
- One branch per sample, forked from `main`, PR targets `main`

## Checklist
- [ ] Sample in `/samples/<prefix>-<folder>/`
- [ ] Sample added to the table in root `README.md`
- [ ] Uses correct templates for `README.md` and `sample.json`
- [ ] All schema versions target latest (see links above)
- [ ] No `projectId` in `m365agents.yml`
- [ ] `additionalMetadata.sampleTag` set in `m365agents.yml` (format: `pnp-copilot-pro-dev:<sample-folder-name>`)
- [ ] No `teamsapp.yml` or `teamsapp.local.yml` (update if present)
- [ ] No secrets or external asset links
- [ ] One PR per sample

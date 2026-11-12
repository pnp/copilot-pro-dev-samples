# Copilot Pro Dev Samples gallery

Astro site for the [community gallery](https://pnp.github.io/copilot-pro-dev-samples/), built from the repository's sample metadata and READMEs.

## Development

Use Node.js >=22.12.0. From this directory:

```sh
npm ci
npm run dev
```

Development and production builds regenerate `public/samples.json` from `../samples/*/assets/sample.json`. After editing sample metadata while the dev server is running, run `npm run generate` and reload.

```sh
npm run check
npm run build
npm test
npm run preview
```

`npm test` checks the built output, so build first. Test the GitHub Pages base path and browser interactions with:

```sh
npm run build -- --base /copilot-pro-dev-samples
npx playwright install chromium
npm test
npm run test:e2e
```

The browser suite starts and stops its own preview server. It checks desktop/mobile navigation, search and type filtering, theme persistence, contribution links, responsive layouts, and tracking. External analytics requests are blocked during automated browser tests.

To browse that production-base build manually, run `npm run preview -- --base /copilot-pro-dev-samples` and open the URL with the `/copilot-pro-dev-samples/` prefix.

## Routes

| Route | Content |
| --- | --- |
| `/` | Gallery introduction, community calls, and searchable catalog ordered by latest update |
| `/samples/` | Full searchable catalog with sample type filtering |
| `/samples/<folder>/` | Preview, authors, source/download links, metadata, and rendered README |
| `/getting-started/` | How to choose and run a sample; official learning resources |
| `/contributors/` | Community recognition, contributor badge, and deduplicated sample authors with links to their samples |
| `/contributing/` | Templates, submission checklist, sample structure, and view tracker guidance |
| `/whats-new/` | Compact dated list of sample additions and updates, with links to their detail pages |
| `/contribute/` | Static redirect preserving the previous contribution URL |

Production routes are prefixed with `/copilot-pro-dev-samples/`. GitHub Pages deployment sets this automatically through `GITHUB_ACTIONS`; `--base` can be used to verify it locally.

## Structure and data

| Path | Responsibility |
| --- | --- |
| `src/layouts/SiteLayout.astro` | Shared navigation, theme, SEO, footer, contribution callout, and page tracker |
| `src/components/` | Shared catalog, sample cards, abstract backdrop, and contribution callout |
| `src/lib/` | Catalog loading, contributor aggregation, base-aware URLs, and safe README rendering |
| `src/pages/` | Static pages and generated sample detail routes |
| `src/scripts/` | Catalog generation, browser filtering, and existing Clarity integration |
| `src/styles/global.css` | Community design tokens, light/dark themes, and responsive styles |
| `src/assets/fonts/` | Locally hosted community typography |
| `public/images/` | Local brand, abstract background, and contribution badge assets |
| `tests/` | Built-output and Playwright regression checks |

Sample folders remain the source of truth; do not hand-edit `public/samples.json`. Existing samples with missing or malformed metadata remain visible with folder-based fallback information and an explicit build warning. Correct the source metadata to populate the full gallery card and contributor entry.

The preview uses the first image thumbnail by ascending `order`. Relative image URLs resolve against the sample source folder. The contributor directory groups GitHub accounts case-insensitively and counts each sample once. Profile images in the directory and on sample pages fall back to a local placeholder avatar when an image fails to load, including when a GitHub account no longer exists.

The homepage displays the full searchable catalog, ordered by sample update dates with titles used to break ties. It follows the other community galleries without a manually curated spotlight.

What's new follows the reference galleries' text-based activity list rather than repeating gallery cards. It lists dated samples newest first, showing the date, Added/Updated label, title, and short summary. A sample is marked Added when its creation and update dates fall on the same UTC day; otherwise it is Updated. Missing update dates fall back to creation dates. Samples with neither date stay in the gallery but are omitted from the activity list.

README HTML is sanitized, relative links and images resolve to their GitHub source, and embedded README view trackers are removed from rendered documentation. Each site page sends exactly one path-specific image request to `https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/<route>`. Sample pages use `samples/<folder>` to match sample README trackers; rendering a card does not count as a sample view. Query strings and the deployment base path are not part of tracker keys. Existing Clarity analytics are preserved.

## Shared design assets

Navigation, colour spectrum, theme switch, typography, and backgrounds follow [pnp/spfx-copilot-components](https://github.com/pnp/spfx-copilot-components) and [pnp/copilot-prompts](https://github.com/pnp/copilot-prompts).

The contributor badge is a local copy of the [community contributor badge](https://pnp.github.io/spfx/images/brand/contributor-badge.webp). Source revisions and licensing are recorded in [asset provenance](./public/images/ASSET-PROVENANCE.md).

The repository README links the [gallery screenshot](../assets/sample-gallery.png) to the live GitHub Pages gallery. To refresh it, capture the homepage in light mode at 1440 x 1180 after the local fonts and first row of images have loaded. Capture the viewport, not the entire catalog; use the unfiltered gallery without changing the displayed sample order.

## Deployment

The [GitHub Pages workflow](../.github/workflows/deploy-site.yml) installs locked dependencies, type-checks, builds and tests the gallery, then publishes `dist/`. No sample source code is moved or rebuilt as part of the gallery deployment.

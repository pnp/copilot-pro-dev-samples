# Copilot Samples Site

Astro-based multi-page catalog site for browsing sample projects in the repository-level `../samples` folder.

## Tech Stack

- Astro 7
- Tailwind CSS v4 (via `@tailwindcss/vite`)
- TypeScript (for data and browser logic modules)

## Routes

- `/` Home page with quick summary stats
- `/samples` Interactive sample browser with search and type filters
- `/about` Implementation notes and catalog overview

## Project Structure

```text
/
├── public/
├── src/
│   ├── components/
│   │   └── SampleBrowser.astro
│   ├── layouts/
│   │   └── SiteLayout.astro
│   ├── lib/
│   │   └── samples.ts
│   ├── pages/
│   │   ├── index.astro
│   │   ├── samples.astro
│   │   └── about.astro
│   ├── scripts/
│   │   └── sample-browser.ts
│   └── styles/
│       └── global.css
├── astro.config.mjs
└── package.json
```

## Responsibilities by Layer

- `src/layouts` provides the shared page frame (header, nav, footer, and global styles).
- `src/pages` is route-level composition only.
- `src/components` contains reusable UI blocks.
- `src/lib/samples.ts` reads local sample metadata and computes summary stats.
- `src/scripts/sample-browser.ts` contains client-side search/filter behavior.
- `src/styles/global.css` holds Tailwind import, theme tokens, and shared component classes.

## Data Source

The catalog reads directories from `../samples` and attempts to parse each sample's `assets/sample.json`.
If metadata is missing or invalid, fallback values are used.

## Local Development

Node.js `>=22.12.0` is required.

```sh
npm install
npm run dev
```

## Build

```sh
npm run build
npm run preview
```

## Notes

- This site is generated from the local repository structure.
- Add or modify sample folders under `../samples`, then refresh/rebuild the site.

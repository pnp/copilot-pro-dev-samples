/**
 * Widget build script.
 *
 * Builds each widget into a self-contained HTML file using Vite + vite-plugin-singlefile.
 * Output goes to ../assets/<widget-name>.html
 */
import { build, type InlineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ASSETS_DIR = resolve(__dirname, "..", "assets");

/**
 * Vite plugin that strips the `crossorigin` attribute from <script> tags.
 * Sandboxed iframes (M365 Copilot, ChatGPT) have a null origin, so the
 * crossorigin attribute triggers CORS failures on inline scripts.
 */
function stripCrossorigin(): Plugin {
  return {
    name: "strip-crossorigin",
    enforce: "post",
    transformIndexHtml(html) {
      return html.replace(/<script([^>]*)\s+crossorigin(?:="[^"]*")?/g, "<script$1");
    },
  };
}

const widgets = [
  { name: "hr-dashboard", entry: "src/dashboard/index.html" },
  { name: "bulk-editor", entry: "src/bulk-editor/index.html" },
  { name: "consultant-profile", entry: "src/consultant-profile/index.html" },
];

// Ensure assets dir
if (!fs.existsSync(ASSETS_DIR)) {
  fs.mkdirSync(ASSETS_DIR, { recursive: true });
}

for (const widget of widgets) {
  console.log(`\nBuilding widget: ${widget.name}…`);

  const config: InlineConfig = {
    root: __dirname,
    mode: "production",                 // eliminates eval / new Function() from HMR/dev code
    plugins: [react(), stripCrossorigin(), viteSingleFile()],
    define: {
      "process.env.NODE_ENV": JSON.stringify("production"),
    },
    build: {
      outDir: resolve(ASSETS_DIR, `_tmp_${widget.name}`),
      emptyOutDir: true,
      minify: "esbuild",
      rollupOptions: {
        input: resolve(__dirname, widget.entry),
      },
    },
    logLevel: "warn",
  };

  await build(config);

  // Find the produced HTML and move to assets/<name>.html
  const tmpDir = resolve(ASSETS_DIR, `_tmp_${widget.name}`);
  const htmlFiles = findHtmlFiles(tmpDir);

  if (htmlFiles.length > 0) {
    const dest = resolve(ASSETS_DIR, `${widget.name}.html`);
    fs.copyFileSync(htmlFiles[0], dest);
    console.log(`  → ${dest}`);
  }

  // Clean tmp
  fs.rmSync(tmpDir, { recursive: true, force: true });
}

console.log("\nAll widgets built ✓\n");

function findHtmlFiles(dir: string): string[] {
  const results: string[] = [];
  if (!fs.existsSync(dir)) return results;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = resolve(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...findHtmlFiles(full));
    } else if (entry.name.endsWith(".html")) {
      results.push(full);
    }
  }
  return results;
}

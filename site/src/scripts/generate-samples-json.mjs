import { mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const typeLabels = {
  da: "Declarative Agent",
  cea: "Custom Engine Agent",
  cext: "Copilot Extension",
  mcp: "MCP",
  mcs: "Copilot Studio",
};

const fallbackDescription = "Community sample for Microsoft 365 Copilot developers.";

function parseDate(value) {
  if (typeof value !== "string" || value.trim().length === 0) {
    return null;
  }

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed.toISOString();
}

async function generateSamplesJson() {
  const siteRoot = process.cwd();
  const samplesRoot = path.resolve(siteRoot, "..", "samples");
  const outputPath = path.resolve(siteRoot, "public", "samples.json");

  const entries = await readdir(samplesRoot, { withFileTypes: true });
  const folders = entries
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .filter((name) => !name.startsWith(".") && name !== "_SAMPLE_templates")
    .sort((a, b) => a.localeCompare(b));

  const samples = await Promise.all(
    folders.map(async (folder) => {
      const sampleJsonPath = path.join(samplesRoot, folder, "assets", "sample.json");
      let title = folder;
      let description = fallbackDescription;
      let updatedAt = null;

      try {
        const raw = await readFile(sampleJsonPath, "utf8");
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed[0]) {
          title = parsed[0].title || parsed[0].name || title;
          description = parsed[0].shortDescription || description;
          updatedAt = parseDate(parsed[0].updateDateTime) || parseDate(parsed[0].creationDateTime);
        }
      } catch {
        // Keep fallback metadata for samples missing or failing to parse sample.json.
      }

      const typeKey = folder.split("-")[0] || "other";
      const type = typeLabels[typeKey] || "Other";

      return {
        folder,
        title,
        description,
        type,
        href: `https://github.com/pnp/copilot-pro-dev-samples/tree/main/samples/${folder}`,
        updatedAt,
      };
    })
  );

  await mkdir(path.dirname(outputPath), { recursive: true });
  await writeFile(outputPath, JSON.stringify(samples, null, 2) + "\n", "utf8");

  console.log(`Generated ${samples.length} sample entries at ${outputPath}`);
}

generateSamplesJson().catch((error) => {
  console.error("Failed to generate samples.json", error);
  process.exitCode = 1;
});
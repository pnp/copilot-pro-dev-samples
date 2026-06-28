import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

export type SampleEntry = {
  folder: string;
  title: string;
  description: string;
  type: string;
  href: string;
};

export type SampleStats = {
  total: number;
  byType: Record<string, number>;
  topTypes: Array<[string, number]>;
};

const typeLabels: Record<string, string> = {
  da: "Declarative Agent",
  cea: "Custom Engine Agent",
  cext: "Copilot Extension",
  mcp: "MCP",
  mcs: "Copilot Studio",
};

const fallbackDescription = "Community sample for Microsoft 365 Copilot developers.";

function getSamplesRoot(): string {
  return path.resolve(process.cwd(), "..", "samples");
}

export async function getSamples(): Promise<SampleEntry[]> {
  const samplesRoot = getSamplesRoot();
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

      try {
        const raw = await readFile(sampleJsonPath, "utf8");
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed[0]) {
          title = parsed[0].title || parsed[0].name || title;
          description = parsed[0].shortDescription || description;
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
      };
    })
  );

  return samples;
}

export function getSampleStats(samples: SampleEntry[]): SampleStats {
  const byType = samples.reduce<Record<string, number>>((acc, sample) => {
    acc[sample.type] = (acc[sample.type] || 0) + 1;
    return acc;
  }, {});

  const topTypes = Object.entries(byType)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);

  return {
    total: samples.length,
    byType,
    topTypes,
  };
}

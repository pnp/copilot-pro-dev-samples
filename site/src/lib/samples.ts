import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

export type SampleEntry = {
  folder: string;
  title: string;
  description: string;
  type: string;
  href: string;
  updatedAt: Date | null;
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

function parseDate(value: unknown): Date | null {
  if (typeof value !== "string" || value.trim().length === 0) {
    return null;
  }

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

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
      let updatedAt: Date | null = null;

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

  return samples;
}

export function getLatestSamples(samples: SampleEntry[], months: number, now = new Date()): SampleEntry[] {
  const safeMonths = Number.isFinite(months) && months > 0 ? months : 1;
  const cutoff = new Date(now);
  cutoff.setMonth(cutoff.getMonth() - safeMonths);

  return samples
    .filter((sample) => sample.updatedAt && sample.updatedAt >= cutoff)
    .sort((a, b) => {
      const aTime = a.updatedAt?.getTime() ?? 0;
      const bTime = b.updatedAt?.getTime() ?? 0;
      return bTime - aTime;
    });
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

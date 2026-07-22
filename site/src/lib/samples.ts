import { readFile } from "node:fs/promises";
import path from "node:path";

export type SampleEntry = {
  folder: string;
  title: string;
  description: string;
  type: string;
  href: string;
  updatedAt: Date | null;
  longDescription: string[];
  metadata: Array<{ key: string; value: string }>;
  imageUrl: string | null;
  imageAlt: string;
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

type StoredSampleEntry = Omit<SampleEntry, "updatedAt"> & {
  updatedAt: string | null;
};

function getSamplesDataPath(): string {
  return path.resolve(process.cwd(), "public", "samples.json");
}

export async function getSamples(): Promise<SampleEntry[]> {
  const samplesDataPath = getSamplesDataPath();

  try {
    const raw = await readFile(samplesDataPath, "utf8");
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.map((item: Partial<StoredSampleEntry>) => {
      const folder = typeof item.folder === "string" ? item.folder : "unknown";
      const typeKey = folder.split("-")[0] || "other";

      return {
        folder,
        title: typeof item.title === "string" && item.title.trim().length > 0 ? item.title : folder,
        description:
          typeof item.description === "string" && item.description.trim().length > 0 ? item.description : fallbackDescription,
        type: typeof item.type === "string" && item.type.trim().length > 0 ? item.type : typeLabels[typeKey] || "Other",
        href:
          typeof item.href === "string" && item.href.trim().length > 0
            ? item.href
            : `https://github.com/pnp/copilot-pro-dev-samples/tree/main/samples/${folder}`,
        updatedAt: parseDate(item.updatedAt),
        longDescription: Array.isArray(item.longDescription)
          ? item.longDescription.filter((line): line is string => typeof line === "string" && line.trim().length > 0)
          : [],
        metadata: Array.isArray(item.metadata)
          ? item.metadata.filter(
              (entry): entry is { key: string; value: string } =>
                !!entry && typeof entry.key === "string" && typeof entry.value === "string"
            )
          : [],
        imageUrl: typeof item.imageUrl === "string" && item.imageUrl.trim().length > 0 ? item.imageUrl : null,
        imageAlt: typeof item.imageAlt === "string" ? item.imageAlt : "",
      };
    });
  } catch {
    return [];
  }
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

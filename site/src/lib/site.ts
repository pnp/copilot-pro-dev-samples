export const repositoryUrl = "https://github.com/pnp/copilot-pro-dev-samples";
export const visitorStatsBaseUrl = "https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples";

export function sitePath(path = ""): string {
  const base = import.meta.env.BASE_URL.replace(/\/?$/, "/");
  return `${base}${path.replace(/^\/+/, "")}`;
}

export function visitorStatsUrl(pathname: string): string {
  const base = sitePath().replace(/\/$/, "");
  const path = pathname.startsWith(`${base}/`) ? pathname.slice(base.length) : pathname;
  return `${visitorStatsBaseUrl}/${path.replace(/^\/+|\/+$/g, "")}`;
}

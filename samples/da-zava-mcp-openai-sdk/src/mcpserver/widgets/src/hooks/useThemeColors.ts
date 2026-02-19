import { useOpenAiGlobal } from "./useOpenAiGlobal";

export interface ThemeColors {
  /* Surfaces */
  background: string;
  surface: string;
  surfaceHover: string;
  surfaceRaised: string;
  /* Text */
  text: string;
  textSecondary: string;
  textTertiary: string;
  /* Borders & dividers */
  border: string;
  borderSubtle: string;
  /* Brand */
  primary: string;
  primaryHover: string;
  primarySubtle: string;   /* tinted backgrounds */
  primaryText: string;
  /* Semantic */
  success: string;
  successSubtle: string;
  warning: string;
  warningSubtle: string;
  error: string;
  errorSubtle: string;
  info: string;
  infoSubtle: string;
  /* Shadows */
  shadowCard: string;
  shadowElevated: string;
  /* Map */
  mapWater: string;
  mapLand: string;
  mapRoad: string;
  mapPark: string;
  mapBuilding: string;
  mapPin: string;
  mapLabel: string;
}

const lightColors: ThemeColors = {
  background: "#f8f9fb",
  surface: "#ffffff",
  surfaceHover: "#f0f2f5",
  surfaceRaised: "#ffffff",
  text: "#1a1a2e",
  textSecondary: "#5c6370",
  textTertiary: "#8b919a",
  border: "#e1e4e8",
  borderSubtle: "#eef0f3",
  primary: "#0066cc",
  primaryHover: "#0052a3",
  primarySubtle: "#e8f1fc",
  primaryText: "#ffffff",
  success: "#0e8a16",
  successSubtle: "#e6f9ed",
  warning: "#d4820c",
  warningSubtle: "#fff8e5",
  error: "#c93c37",
  errorSubtle: "#fef0ef",
  info: "#0066cc",
  infoSubtle: "#e8f1fc",
  shadowCard: "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
  shadowElevated: "0 4px 16px rgba(0,0,0,0.08), 0 1px 4px rgba(0,0,0,0.04)",
  mapWater: "#c8ddf0",
  mapLand: "#e8ede4",
  mapRoad: "#ffffff",
  mapPark: "#c5e1a5",
  mapBuilding: "#d5d5d5",
  mapPin: "#c93c37",
  mapLabel: "#4a4e54",
};

const darkColors: ThemeColors = {
  background: "#0d1117",
  surface: "#161b22",
  surfaceHover: "#1c2333",
  surfaceRaised: "#1c2333",
  text: "#e6edf3",
  textSecondary: "#8b949e",
  textTertiary: "#6e7681",
  border: "#30363d",
  borderSubtle: "#21262d",
  primary: "#58a6ff",
  primaryHover: "#79b8ff",
  primarySubtle: "#0d2240",
  primaryText: "#0d1117",
  success: "#56d364",
  successSubtle: "#0b2d13",
  warning: "#e3b341",
  warningSubtle: "#2d2200",
  error: "#f85149",
  errorSubtle: "#3d1014",
  info: "#58a6ff",
  infoSubtle: "#0d2240",
  shadowCard: "0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2)",
  shadowElevated: "0 4px 16px rgba(0,0,0,0.4), 0 1px 4px rgba(0,0,0,0.3)",
  mapWater: "#1a2637",
  mapLand: "#161b22",
  mapRoad: "#30363d",
  mapPark: "#1b3a1f",
  mapBuilding: "#21262d",
  mapPin: "#f85149",
  mapLabel: "#8b949e",
};

export function useThemeColors(): ThemeColors {
  const theme = useOpenAiGlobal("theme");
  return theme === "dark" ? darkColors : lightColors;
}

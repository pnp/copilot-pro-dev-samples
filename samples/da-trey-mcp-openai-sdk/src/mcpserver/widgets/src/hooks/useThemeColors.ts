/**
 * Returns a palette of semantic colours that adapts to the current ChatGPT
 * host theme ("light" | "dark") read from `window.openai.theme`.
 *
 * Uses the same poll-based detection as useOpenAiGlobal, plus a
 * `prefers-color-scheme` media-query fallback for non-ChatGPT hosts.
 */
import { useState, useEffect, useMemo } from "react";

type ThemeMode = "light" | "dark";

function detectTheme(): ThemeMode {
  // 1. ChatGPT host value
  const hostTheme = (window as any).openai?.theme;
  if (hostTheme === "dark") return "dark";
  if (hostTheme === "light") return "light";

  // 2. OS-level preference
  if (typeof window.matchMedia === "function") {
    if (window.matchMedia("(prefers-color-scheme: dark)").matches) return "dark";
  }

  return "light";
}

export function useThemeMode(): ThemeMode {
  const [mode, setMode] = useState<ThemeMode>(detectTheme);

  useEffect(() => {
    const id = setInterval(() => {
      const next = detectTheme();
      setMode((prev) => (prev !== next ? next : prev));
    }, 300);
    return () => clearInterval(id);
  }, []);

  return mode;
}

export interface ThemeColors {
  /* surfaces */
  surface: string;
  cardBg: string;
  /* text */
  textPrimary: string;
  textSecondary: string;
  textTertiary: string;
  /* brand */
  brand: string;
  brandLight: string;
  brandDark: string;
  /* semantic */
  green: string;
  greenBg: string;
  amber: string;
  amberBg: string;
  purple: string;
  purpleBg: string;
  /* borders / misc */
  divider: string;
  /* gradients */
  bannerGradient: string;
  bannerText: string;
}

const LIGHT: ThemeColors = {
  surface: "#f3f6f8",
  cardBg: "#ffffff",
  textPrimary: "#191919",
  textSecondary: "#666666",
  textTertiary: "#999999",
  brand: "#0a66c2",
  brandLight: "#e8f1fb",
  brandDark: "#004182",
  green: "#057642",
  greenBg: "#e6f4ea",
  amber: "#b24020",
  amberBg: "#fff3e0",
  purple: "#6d28d9",
  purpleBg: "#f3e8ff",
  divider: "#e8e8e8",
  bannerGradient: "linear-gradient(135deg, #0a66c2 0%, #004182 100%)",
  bannerText: "#ffffff",
};

const DARK: ThemeColors = {
  surface: "#1b1b1b",
  cardBg: "#292929",
  textPrimary: "#e8e8e8",
  textSecondary: "#a0a0a0",
  textTertiary: "#737373",
  brand: "#70b5f9",
  brandLight: "#1a3a5c",
  brandDark: "#a8d4ff",
  green: "#6ec89b",
  greenBg: "#1a3328",
  amber: "#f5a060",
  amberBg: "#3d2a1a",
  purple: "#b794f4",
  purpleBg: "#2d1f4e",
  divider: "#3a3a3a",
  bannerGradient: "linear-gradient(135deg, #1a3a5c 0%, #0d2240 100%)",
  bannerText: "#e8e8e8",
};

export function useThemeColors(): ThemeColors {
  const mode = useThemeMode();
  return useMemo(() => (mode === "dark" ? DARK : LIGHT), [mode]);
}

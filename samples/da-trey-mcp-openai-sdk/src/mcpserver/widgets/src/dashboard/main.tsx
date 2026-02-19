import React from "react";
import { createRoot } from "react-dom/client";
import { FluentProvider, webLightTheme, webDarkTheme } from "@fluentui/react-components";
import { Dashboard } from "./Dashboard";
import { useOpenAiGlobal } from "../hooks/useOpenAiGlobal";
import type { Theme } from "../types";

function App() {
  const theme = (useOpenAiGlobal<string>("theme") ?? "light") as Theme;
  return (
    <FluentProvider theme={theme === "dark" ? webDarkTheme : webLightTheme}>
      <Dashboard />
    </FluentProvider>
  );
}

createRoot(document.getElementById("root")!).render(<App />);

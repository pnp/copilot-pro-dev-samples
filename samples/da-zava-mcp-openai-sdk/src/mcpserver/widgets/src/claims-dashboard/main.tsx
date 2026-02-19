import React from "react";
import { createRoot } from "react-dom/client";
import { FluentProvider, webLightTheme, webDarkTheme } from "@fluentui/react-components";
import { useOpenAiGlobal } from "../hooks/useOpenAiGlobal";
import { ClaimsDashboard } from "./ClaimsDashboard";

function App() {
  const theme = useOpenAiGlobal("theme");
  return (
    <FluentProvider theme={theme === "dark" ? webDarkTheme : webLightTheme}>
      <ClaimsDashboard />
    </FluentProvider>
  );
}

createRoot(document.getElementById("root")!).render(<App />);

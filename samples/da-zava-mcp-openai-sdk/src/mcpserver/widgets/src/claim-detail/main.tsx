import React from "react";
import { createRoot } from "react-dom/client";
import { FluentProvider, webLightTheme, webDarkTheme } from "@fluentui/react-components";
import { useOpenAiGlobal } from "../hooks/useOpenAiGlobal";
import { ClaimDetail } from "./ClaimDetail";

function App() {
  const theme = useOpenAiGlobal("theme");
  return (
    <FluentProvider theme={theme === "dark" ? webDarkTheme : webLightTheme}>
      <ClaimDetail />
    </FluentProvider>
  );
}

createRoot(document.getElementById("root")!).render(<App />);

import React from "react";
import { createRoot } from "react-dom/client";
import { FluentProvider, webLightTheme, webDarkTheme } from "@fluentui/react-components";
import { useOpenAiGlobal } from "../hooks/useOpenAiGlobal";
import { ContractorsList } from "./ContractorsList";

function App() {
  const theme = useOpenAiGlobal("theme");
  return (
    <FluentProvider theme={theme === "dark" ? webDarkTheme : webLightTheme}>
      <ContractorsList />
    </FluentProvider>
  );
}

createRoot(document.getElementById("root")!).render(<App />);

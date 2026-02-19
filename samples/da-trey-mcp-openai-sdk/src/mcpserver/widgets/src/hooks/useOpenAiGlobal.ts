/**
 * Hook to read values from the ChatGPT / Apps SDK host via window.openai.
 *
 * window.openai is injected by ChatGPT when the widget is rendered in a
 * sandboxed iframe. Falls back gracefully when running outside of ChatGPT.
 */
import { useState, useEffect } from "react";

declare global {
  interface Window {
    openai?: {
      toolOutput?: unknown;
      toolInput?: unknown;
      toolResponseMetadata?: unknown;
      theme?: string;
      displayMode?: string;
      userAgent?: unknown;
      setWidgetState?: (state: unknown) => void;
      callTool?: (name: string, args?: unknown) => Promise<unknown>;
      requestDisplayMode?: (options: { mode: string }) => Promise<string>;
      openExternal?: (url: string) => void;
      sendFollowUpMessage?: (message: string) => void;
      requestModal?: () => void;
      requestClose?: () => void;
      addEventListener?: (event: string, handler: (data: unknown) => void) => void;
      removeEventListener?: (event: string, handler: (data: unknown) => void) => void;
    };
  }
}

type OpenAIKey =
  | "toolOutput"
  | "toolInput"
  | "toolResponseMetadata"
  | "theme"
  | "displayMode"
  | "userAgent";

export function useOpenAiGlobal<T = unknown>(key: OpenAIKey): T | undefined {
  const [value, setValue] = useState<T | undefined>(() => {
    return window.openai?.[key] as T | undefined;
  });

  useEffect(() => {
    // Poll for changes since the sandbox may set the value after mount
    const interval = setInterval(() => {
      const current = window.openai?.[key] as T | undefined;
      setValue((prev) => {
        if (JSON.stringify(prev) !== JSON.stringify(current)) return current;
        return prev;
      });
    }, 200);

    return () => clearInterval(interval);
  }, [key]);

  return value;
}

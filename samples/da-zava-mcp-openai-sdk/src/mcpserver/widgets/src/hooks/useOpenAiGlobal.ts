/**
 * Reactive hook that reads values from window.openai, matching the official
 * OpenAI Apps SDK pattern.  ChatGPT's sandbox dispatches a custom
 * "openai:set_globals" event every time it updates window.openai – this hook
 * subscribes to that event via useSyncExternalStore so the component
 * re‑renders automatically.
 */
import { useSyncExternalStore } from "react";

// ── Event contract used by the ChatGPT sandbox ────────────────────────
const SET_GLOBALS_EVENT_TYPE = "openai:set_globals";

type OpenAiGlobals = {
  theme: "light" | "dark";
  userAgent: Record<string, unknown>;
  locale: string;
  maxHeight: number;
  displayMode: "inline" | "fullscreen";
  safeArea: { top: number; bottom: number; left: number; right: number };
  toolInput: Record<string, unknown>;
  toolOutput: Record<string, unknown> | null;
  toolResponseMetadata: Record<string, unknown> | null;
  widgetState: Record<string, unknown> | null;
  setWidgetState: (state: Record<string, unknown>) => Promise<void>;
  view: { mode: string; params?: Record<string, unknown> } | null;
};

class SetGlobalsEvent extends CustomEvent<{
  globals: Partial<OpenAiGlobals>;
}> {
  readonly type = SET_GLOBALS_EVENT_TYPE;
}

declare global {
  interface Window {
    openai?: Partial<OpenAiGlobals> & {
      callTool?: (name: string, args: Record<string, unknown>) => Promise<unknown>;
      sendFollowUpMessage?: (args: { prompt: string }) => Promise<void>;
      openExternal?: (payload: { href: string }) => void;
      requestDisplayMode?: (args: { mode: string }) => Promise<{ mode: string }>;
      requestModal?: (args: { title?: string; params?: Record<string, unknown> }) => Promise<unknown>;
      requestClose?: () => void;
    };
  }

  interface WindowEventMap {
    [SET_GLOBALS_EVENT_TYPE]: SetGlobalsEvent;
  }
}

export function useOpenAiGlobal<K extends keyof OpenAiGlobals>(
  key: K
): OpenAiGlobals[K] | null {
  return useSyncExternalStore(
    (onChange) => {
      if (typeof window === "undefined") {
        return () => {};
      }

      const handleSetGlobal = (event: SetGlobalsEvent) => {
        const value = event.detail.globals[key];
        if (value === undefined) {
          return;
        }
        onChange();
      };

      window.addEventListener(SET_GLOBALS_EVENT_TYPE, handleSetGlobal, {
        passive: true,
      });

      return () => {
        window.removeEventListener(SET_GLOBALS_EVENT_TYPE, handleSetGlobal);
      };
    },
    () => (window.openai?.[key] as OpenAiGlobals[K]) ?? null,
    () => (window.openai?.[key] as OpenAiGlobals[K]) ?? null
  );
}

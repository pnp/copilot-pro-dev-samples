/**
 * Hook for persisting widget state via the Apps SDK host.
 *
 * window.openai.setWidgetState() saves state on the host so it survives
 * re-renders and even conversation turns.
 */
import { useState, useCallback, useEffect } from "react";

export function useWidgetState<T extends Record<string, unknown>>(
  initialState: T
): [T, (state: T) => void] {
  const [state, setLocalState] = useState<T>(() => {
    // Try to read existing widget state from host
    try {
      const hostState = (window.openai as any)?.widgetState;
      if (hostState && typeof hostState === "object") {
        return { ...initialState, ...hostState } as T;
      }
    } catch {
      // ignore – not running inside Apps SDK
    }
    return initialState;
  });

  const setState = useCallback(
    (newState: T) => {
      setLocalState(newState);
      try {
        window.openai?.setWidgetState?.(newState);
      } catch {
        // ignore – not running inside Apps SDK
      }
    },
    []
  );

  // Listen for external state changes
  useEffect(() => {
    const handler = (data: unknown) => {
      if (data && typeof data === "object") {
        setLocalState((prev) => ({ ...prev, ...(data as Record<string, unknown>) }) as T);
      }
    };
    try {
      window.openai?.addEventListener?.("widgetStateChanged", handler);
      return () => window.openai?.removeEventListener?.("widgetStateChanged", handler);
    } catch {
      return undefined;
    }
  }, []);

  return [state, setState];
}

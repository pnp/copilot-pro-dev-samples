/**
 * Centralized capability detection for window.openai.* APIs.
 *
 * Not all APIs are available on every platform or host version.
 * Unsupported APIs are `undefined` — a truthiness check is sufficient.
 *
 * **Rules**
 * - Always check before calling any window.openai.* API.
 * - Provide fallback UI when an API is missing.
 * - Re-detect on every render / initialization — do NOT cache across sessions,
 *   because the host can update between loads.
 */
import { useSyncExternalStore } from "react";

// ── Capability shape ───────────────────────────────────────────────────
export interface PlatformCapabilities {
  /** Whether `window.openai.callTool` is available */
  canCallTools: boolean;
  /** Whether `window.openai.requestDisplayMode` is available */
  canChangeDisplayMode: boolean;
  /** Whether `window.openai.sendFollowUpMessage` is available */
  canSendMessages: boolean;
  /** Whether `window.openai.openExternal` is available */
  canOpenExternal: boolean;
  /** Whether `window.openai.requestModal` is available */
  canRequestModal: boolean;
  /** Whether `window.openai.requestClose` is available */
  canRequestClose: boolean;
}

/**
 * Detect which window.openai.* APIs are available on the current platform.
 * Safe to call at any point — returns `false` for everything when
 * `window.openai` itself is undefined.
 */
export function detectCapabilities(): PlatformCapabilities {
  const oa = typeof window !== "undefined" ? window.openai : undefined;
  return {
    canCallTools: !!oa?.callTool,
    canChangeDisplayMode: !!oa?.requestDisplayMode,
    canSendMessages: !!oa?.sendFollowUpMessage,
    canOpenExternal: !!oa?.openExternal,
    canRequestModal: !!oa?.requestModal,
    canRequestClose: !!oa?.requestClose,
  };
}

// ── React hook ─────────────────────────────────────────────────────────
// Re-evaluates whenever the ChatGPT sandbox fires "openai:set_globals",
// so capabilities stay fresh without caching across sessions.
//
// IMPORTANT: useSyncExternalStore compares snapshots by reference (===).
// We must return the *same* object when nothing has changed, otherwise
// React re-renders infinitely.  We cache the last snapshot and only
// create a new object when a value actually flips.

const SET_GLOBALS_EVENT_TYPE = "openai:set_globals";

let _cached: PlatformCapabilities = detectCapabilities();

function getSnapshot(): PlatformCapabilities {
  const fresh = detectCapabilities();
  if (
    fresh.canCallTools === _cached.canCallTools &&
    fresh.canChangeDisplayMode === _cached.canChangeDisplayMode &&
    fresh.canSendMessages === _cached.canSendMessages &&
    fresh.canOpenExternal === _cached.canOpenExternal &&
    fresh.canRequestModal === _cached.canRequestModal &&
    fresh.canRequestClose === _cached.canRequestClose
  ) {
    return _cached;          // same reference → no re-render
  }
  _cached = fresh;           // values changed → new reference
  return _cached;
}

function subscribe(onChange: () => void) {
  if (typeof window === "undefined") return () => {};
  window.addEventListener(SET_GLOBALS_EVENT_TYPE, onChange, { passive: true });
  return () => window.removeEventListener(SET_GLOBALS_EVENT_TYPE, onChange);
}

/**
 * React hook that returns the current platform capabilities.
 * Re-evaluates on every `openai:set_globals` event so the component
 * adapts when the host updates.
 */
export function useCapabilities(): PlatformCapabilities {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}

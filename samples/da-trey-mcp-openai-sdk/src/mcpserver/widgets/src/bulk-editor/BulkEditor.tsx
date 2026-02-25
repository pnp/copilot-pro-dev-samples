import React, { useState, useCallback, useMemo, useEffect } from "react";
import {
  Save20Regular,
  ArrowUndo16Regular,
  Dismiss16Regular,
  Add16Regular,
  Checkmark16Regular,
  People24Regular,
  Mail20Regular,
  Phone20Regular,
  PersonBoard20Regular,
  Certificate20Regular,
  FullScreenMaximize24Regular,
  FullScreenMinimize24Regular,
} from "@fluentui/react-icons";
import { useOpenAiGlobal } from "../hooks/useOpenAiGlobal";
import { useThemeColors, type ThemeColors } from "../hooks/useThemeColors";
import type { BulkEditorData, Consultant } from "../types";

/* ── Helpers ── */
const AVATAR_COLORS = ["#0a66c2", "#7c3aed", "#0e7490", "#b45309", "#059669", "#dc2626", "#6d28d9", "#0284c7"];
function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  return (name[0] ?? "?").toUpperCase();
}
function avatarColor(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

/* ── Inline styles ── */
function cardStyle(t: ThemeColors, dirty: boolean) {
  return {
    background: t.cardBg,
    borderRadius: 12,
    border: `1px solid ${dirty ? t.amber + "66" : t.divider}`,
    boxShadow: dirty ? `0 0 0 2px ${t.amber}22` : "0 1px 3px rgba(0,0,0,0.06)",
    padding: "20px 24px",
    display: "flex",
    flexDirection: "column" as const,
    gap: 16,
    transition: "border-color 0.15s ease, box-shadow 0.15s ease",
  };
}
function inputStyle(t: ThemeColors) {
  return {
    padding: "8px 12px",
    borderRadius: 8,
    border: `1px solid ${t.divider}`,
    background: t.surface,
    color: t.textPrimary,
    fontSize: 16,
    fontFamily: "inherit",
    outline: "none",
    width: "100%",
    boxSizing: "border-box" as const,
    transition: "border-color 0.15s ease",
  };
}
function tagStyle(bg: string, color: string, border?: string) {
  return {
    padding: "4px 10px",
    borderRadius: 14,
    fontSize: 12,
    fontWeight: 500 as const,
    background: bg,
    color,
    border: border ?? "none",
    whiteSpace: "nowrap" as const,
    display: "inline-flex",
    alignItems: "center" as const,
    gap: 4,
  };
}
function btnStyle(t: ThemeColors, variant: "primary" | "ghost" | "danger" = "primary") {
  const base = {
    padding: "8px 16px",
    borderRadius: 8,
    fontSize: 13,
    fontWeight: 600 as const,
    fontFamily: "inherit",
    cursor: "pointer" as const,
    display: "inline-flex",
    alignItems: "center" as const,
    gap: 6,
    transition: "opacity 0.15s ease",
    border: "none",
    whiteSpace: "nowrap" as const,
  };
  if (variant === "primary") return { ...base, background: t.brand, color: "#fff" };
  if (variant === "danger") return { ...base, background: "transparent", color: t.amber, border: `1px solid ${t.amber}44`, padding: "6px 12px" };
  return { ...base, background: "transparent", color: t.textSecondary, border: `1px solid ${t.divider}` };
}

/* ── Avatar ── */
function Avatar({ src, name, size = 48 }: { src?: string; name: string; size?: number }) {
  const [broken, setBroken] = useState(false);
  const bg = avatarColor(name);
  const outer = { width: size, height: size, borderRadius: "50%", overflow: "hidden" as const, flexShrink: 0, display: "flex", alignItems: "center" as const, justifyContent: "center" as const };
  if (src && !broken) {
    return <span style={outer}><img src={src} alt={name} style={{ width: "100%", height: "100%", objectFit: "cover" }} onError={() => setBroken(true)} /></span>;
  }
  return <span style={{ ...outer, background: bg, color: "#fff", fontSize: size * 0.4, fontWeight: 700, letterSpacing: "0.5px", userSelect: "none" }}>{getInitials(name)}</span>;
}

/* ── Types ── */
interface EditedRow extends Consultant {
  _dirty?: boolean;
}

/* ═══════════════════════════════════════════════════════════════════ */
export function BulkEditor() {
  const t = useThemeColors();
  const toolOutput = useOpenAiGlobal<BulkEditorData>("toolOutput");
  const data = toolOutput ?? { consultants: [] };

  // Fullscreen toggle — starts inline, switches on button click
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const handler = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, []);

  const toggleFullscreen = useCallback(async () => {
    if (window.openai?.requestDisplayMode) {
      const current = window.openai.displayMode;
      await window.openai.requestDisplayMode({ mode: current === "fullscreen" ? "inline" : "fullscreen" });
      return;
    }
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
        return;
      } else {
        await document.exitFullscreen();
        return;
      }
    } catch { /* not supported */ }
    setIsFullscreen((prev) => !prev);
  }, [isFullscreen]);

  const [rows, setRows] = useState<EditedRow[]>(() =>
    data.consultants.map((c) => ({ ...c, _dirty: false }))
  );
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [newSkillInputs, setNewSkillInputs] = useState<Record<string, string>>({});
  const [newRoleInputs, setNewRoleInputs] = useState<Record<string, string>>({});

  useMemo(() => {
    if (data.consultants.length > 0)
      setRows(data.consultants.map((c) => ({ ...c, _dirty: false })));
  }, [data.consultants]);

  const dirtyCount = rows.filter((r) => r._dirty).length;

  const updateField = useCallback((id: string, field: keyof Consultant, value: unknown) => {
    setRows((prev) => prev.map((r) => (r.id === id ? { ...r, [field]: value, _dirty: true } : r)));
  }, []);

  const removeTag = useCallback((id: string, field: "skills" | "roles", tag: string) => {
    setRows((prev) =>
      prev.map((r) =>
        r.id === id
          ? { ...r, [field]: (r[field] as string[]).filter((t) => t !== tag), _dirty: true }
          : r
      )
    );
  }, []);

  const addTag = useCallback(
    (id: string, field: "skills" | "roles") => {
      const store = field === "skills" ? newSkillInputs : newRoleInputs;
      const setStore = field === "skills" ? setNewSkillInputs : setNewRoleInputs;
      const tag = (store[id] ?? "").trim();
      if (!tag) return;
      setRows((prev) =>
        prev.map((r) =>
          r.id === id && !(r[field] as string[]).includes(tag)
            ? { ...r, [field]: [...(r[field] as string[]), tag], _dirty: true }
            : r
        )
      );
      setStore((prev) => ({ ...prev, [id]: "" }));
    },
    [newSkillInputs, newRoleInputs]
  );

  const revertAll = () => {
    setRows(data.consultants.map((c) => ({ ...c, _dirty: false })));
    setMessage(null);
  };

  const handleSave = async () => {
    const dirty = rows.filter((r) => r._dirty);
    if (dirty.length === 0) return;
    if (!window.openai?.callTool) {
      setMessage({ type: "error", text: "Save is not available on this platform." });
      return;
    }
    setSaving(true);
    setMessage(null);
    try {
      for (const r of dirty) {
        await window.openai.callTool("update-consultant", {
          consultantId: r.id,
          name: r.name,
          email: r.email,
          phone: r.phone,
          skills: r.skills,
          roles: r.roles,
        });
      }
      setRows((prev) => prev.map((r) => ({ ...r, _dirty: false })));
      setMessage({ type: "success", text: `Saved ${dirty.length} record(s) successfully.` });
    } catch (err: any) {
      setMessage({ type: "error", text: `Save failed: ${err?.message ?? "Unknown error"}` });
    } finally {
      setSaving(false);
    }
  };

  /* ── Render ── */
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 20,
        padding: 24,
        fontFamily: '"Segoe Sans", "Segoe UI", "Segoe UI Web (West European)", -apple-system, BlinkMacSystemFont, Roboto, "Helvetica Neue", Arial, sans-serif',
        boxSizing: "border-box",
        width: "100%",
        background: t.surface,
        minHeight: "100%",
        color: t.textPrimary,
        ...(isFullscreen ? {
          position: "fixed" as const, top: 0, left: 0, right: 0, bottom: 0,
          zIndex: 9999, overflowY: "auto" as const,
        } : {}),
      }}
    >
      {/* ── Header ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.3px" }}>Bulk Editor</div>
          <div style={{ fontSize: 13, color: t.textSecondary, marginTop: 2 }}>
            {rows.length} consultant{rows.length !== 1 ? "s" : ""}{dirtyCount > 0 && (
              <span style={{ marginLeft: 8, color: t.amber, fontWeight: 600 }}>
                · {dirtyCount} unsaved
              </span>
            )}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            style={btnStyle(t, "ghost")}
            onClick={toggleFullscreen}
            title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
          >
            {isFullscreen ? <FullScreenMinimize24Regular /> : <FullScreenMaximize24Regular />}
          </button>
          <button style={btnStyle(t, "ghost")} disabled={dirtyCount === 0} onClick={revertAll}>
            <ArrowUndo16Regular /> Revert
          </button>
          <button
            style={{ ...btnStyle(t, "primary"), opacity: dirtyCount === 0 || saving ? 0.5 : 1 }}
            disabled={dirtyCount === 0 || saving}
            onClick={handleSave}
          >
            <Save20Regular /> {saving ? "Saving…" : "Save All"}
          </button>
        </div>
      </div>

      {/* ── Message ── */}
      {message && (
        <div
          style={{
            padding: "10px 16px",
            borderRadius: 8,
            fontSize: 13,
            fontWeight: 500,
            background: message.type === "success" ? t.greenBg : t.amberBg,
            color: message.type === "success" ? t.green : t.amber,
            border: `1px solid ${message.type === "success" ? t.green : t.amber}33`,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          {message.type === "success" ? <Checkmark16Regular /> : <Dismiss16Regular />}
          {message.text}
        </div>
      )}

      {/* ── Consultant Cards ── */}
      {rows.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {rows.map((row) => (
            <div key={row.id} style={cardStyle(t, !!row._dirty)}>
              {/* Top: avatar + basic info */}
              <div style={{ display: "flex", gap: 16, alignItems: "flex-start", flexWrap: "wrap" }}>
                <Avatar src={row.photoUrl} name={row.name} size={56} />
                <div style={{ flex: 1, minWidth: 200, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
                  {/* Name */}
                  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <label style={{ fontSize: 12, fontWeight: 500, color: t.textSecondary, display: "flex", alignItems: "center", gap: 4 }}>
                      <People24Regular style={{ fontSize: 14 }} /> Name
                    </label>
                    <input
                      style={inputStyle(t)}
                      value={row.name}
                      onChange={(e) => updateField(row.id, "name", e.target.value)}
                      onFocus={(e) => (e.target.style.borderColor = t.brand)}
                      onBlur={(e) => (e.target.style.borderColor = t.divider)}
                    />
                  </div>
                  {/* Email */}
                  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <label style={{ fontSize: 12, fontWeight: 500, color: t.textSecondary, display: "flex", alignItems: "center", gap: 4 }}>
                      <Mail20Regular style={{ fontSize: 14 }} /> Email
                    </label>
                    <input
                      style={inputStyle(t)}
                      value={row.email}
                      onChange={(e) => updateField(row.id, "email", e.target.value)}
                      onFocus={(e) => (e.target.style.borderColor = t.brand)}
                      onBlur={(e) => (e.target.style.borderColor = t.divider)}
                    />
                  </div>
                  {/* Phone */}
                  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <label style={{ fontSize: 12, fontWeight: 500, color: t.textSecondary, display: "flex", alignItems: "center", gap: 4 }}>
                      <Phone20Regular style={{ fontSize: 14 }} /> Phone
                    </label>
                    <input
                      style={inputStyle(t)}
                      value={row.phone}
                      onChange={(e) => updateField(row.id, "phone", e.target.value)}
                      onFocus={(e) => (e.target.style.borderColor = t.brand)}
                      onBlur={(e) => (e.target.style.borderColor = t.divider)}
                    />
                  </div>
                </div>
              </div>

              {/* Skills */}
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <label style={{ fontSize: 12, fontWeight: 500, color: t.textSecondary, display: "flex", alignItems: "center", gap: 4 }}>
                  <Certificate20Regular style={{ fontSize: 14 }} /> Skills
                </label>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
                  {row.skills.map((s) => (
                    <span
                      key={s}
                      style={{ ...tagStyle(t.brandLight, t.brandDark, `1px solid ${t.brand}26`), cursor: "pointer" }}
                      title={`Remove ${s}`}
                      onClick={() => removeTag(row.id, "skills", s)}
                    >
                      {s} <Dismiss16Regular style={{ fontSize: 10 }} />
                    </span>
                  ))}
                  <span style={{ display: "inline-flex", gap: 4, alignItems: "center" }}>
                    <input
                      style={{ ...inputStyle(t), width: 120, padding: "5px 10px", fontSize: 12 }}
                      placeholder="Add skill…"
                      value={newSkillInputs[row.id] ?? ""}
                      onChange={(e) => setNewSkillInputs((p) => ({ ...p, [row.id]: e.target.value }))}
                      onKeyDown={(e) => e.key === "Enter" && addTag(row.id, "skills")}
                      onFocus={(e) => (e.target.style.borderColor = t.brand)}
                      onBlur={(e) => (e.target.style.borderColor = t.divider)}
                    />
                    <button
                      style={{ ...btnStyle(t, "ghost"), padding: "4px 8px", fontSize: 12, border: `1px solid ${t.divider}` }}
                      onClick={() => addTag(row.id, "skills")}
                    >
                      <Add16Regular />
                    </button>
                  </span>
                </div>
              </div>

              {/* Roles */}
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <label style={{ fontSize: 12, fontWeight: 500, color: t.textSecondary, display: "flex", alignItems: "center", gap: 4 }}>
                  <PersonBoard20Regular style={{ fontSize: 14 }} /> Roles
                </label>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
                  {row.roles.map((r) => (
                    <span
                      key={r}
                      style={{ ...tagStyle(t.purpleBg, t.purple, `1px solid ${t.purple}26`), cursor: "pointer" }}
                      title={`Remove ${r}`}
                      onClick={() => removeTag(row.id, "roles", r)}
                    >
                      {r} <Dismiss16Regular style={{ fontSize: 10 }} />
                    </span>
                  ))}
                  <span style={{ display: "inline-flex", gap: 4, alignItems: "center" }}>
                    <input
                      style={{ ...inputStyle(t), width: 120, padding: "5px 10px", fontSize: 12 }}
                      placeholder="Add role…"
                      value={newRoleInputs[row.id] ?? ""}
                      onChange={(e) => setNewRoleInputs((p) => ({ ...p, [row.id]: e.target.value }))}
                      onKeyDown={(e) => e.key === "Enter" && addTag(row.id, "roles")}
                      onFocus={(e) => (e.target.style.borderColor = t.brand)}
                      onBlur={(e) => (e.target.style.borderColor = t.divider)}
                    />
                    <button
                      style={{ ...btnStyle(t, "ghost"), padding: "4px 8px", fontSize: 12, border: `1px solid ${t.divider}` }}
                      onClick={() => addTag(row.id, "roles")}
                    >
                      <Add16Regular />
                    </button>
                  </span>
                </div>
              </div>

              {/* Dirty indicator */}
              {row._dirty && (
                <div style={{ fontSize: 11, color: t.amber, fontWeight: 500, textAlign: "right" }}>
                  Modified — unsaved
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div style={{ ...cardStyle(t, false), padding: "48px 24px", textAlign: "center", color: t.textTertiary }}>
          <People24Regular style={{ fontSize: 40, display: "block", margin: "0 auto 12px" }} />
          <div style={{ fontSize: 16 }}>No consultant data loaded.</div>
          <div style={{ fontSize: 12, marginTop: 4 }}>Use the MCP tool to open the bulk editor.</div>
        </div>
      )}
    </div>
  );
}

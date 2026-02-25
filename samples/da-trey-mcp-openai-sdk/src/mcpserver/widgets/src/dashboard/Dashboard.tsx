import React, { useState, useMemo, useEffect, useCallback } from "react";
import { Body1, Caption1 } from "@fluentui/react-components";
import {
  People24Regular,
  Briefcase24Regular,
  Clock24Regular,
  MoneyHand20Regular,
  ArrowTrendingLines24Regular,
  DataUsage24Regular,
  FullScreenMaximize24Regular,
  FullScreenMinimize24Regular,
  PersonBoard20Regular,
  Open16Regular,
  Info16Regular,
} from "@fluentui/react-icons";
import { useOpenAiGlobal } from "../hooks/useOpenAiGlobal";
import { useThemeColors, type ThemeColors } from "../hooks/useThemeColors";
import type { DashboardData, Consultant, Assignment } from "../types";

/* ── Helpers ── */
const AVATAR_COLORS = ["#0a66c2", "#7c3aed", "#0e7490", "#b45309", "#059669", "#dc2626", "#6d28d9", "#0284c7"];
const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

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

/* ── Avatar ── */
function Avatar({ src, name, size = 36 }: { src?: string; name: string; size?: number }) {
  const [imgFailed, setImgFailed] = useState(false);
  const bg = avatarColor(name);
  const outer: React.CSSProperties = { width: size, height: size, borderRadius: "50%", overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 };
  if (src && !imgFailed) {
    return <span style={outer}><img src={src} alt={name} style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} onError={() => setImgFailed(true)} /></span>;
  }
  return <span style={{ ...outer, background: bg, color: "#fff", fontSize: size * 0.4, fontWeight: 700, letterSpacing: "0.5px", userSelect: "none" }}>{getInitials(name)}</span>;
}

/* ── Pill ── */
function Pill({ children, bg, color }: { children: React.ReactNode; bg: string; color: string }) {
  return <span style={{ padding: "3px 10px", borderRadius: 14, fontSize: 11, fontWeight: 500, background: bg, color, whiteSpace: "nowrap" }}>{children}</span>;
}

/* ── Mini bar chart ── */
function BarChart({ data, t, maxHeight = 110 }: { data: { label: string; value: number; color?: string }[]; t: ThemeColors; maxHeight?: number }) {
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 6, height: maxHeight, padding: "0 4px" }}>
      {data.map((d, i) => {
        const h = Math.max((d.value / max) * (maxHeight - 24), 4);
        return (
          <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", flex: 1, gap: 4 }}>
            <span style={{ fontSize: 10, fontWeight: 600, color: t.textSecondary }}>{d.value > 0 ? d.value : ""}</span>
            <div style={{ width: "100%", maxWidth: 28, height: h, borderRadius: "4px 4px 0 0", background: d.color ?? t.brand, transition: "height 0.3s ease" }} />
            <span style={{ fontSize: 9, color: t.textTertiary, whiteSpace: "nowrap" }}>{d.label}</span>
          </div>
        );
      })}
    </div>
  );
}

/* ── Donut chart ── */
function DonutChart({ segments, size = 100, t }: { segments: { label: string; value: number; color: string }[]; size?: number; t: ThemeColors }) {
  const total = segments.reduce((s, seg) => s + seg.value, 0);
  if (total === 0) return <div style={{ width: size, height: size, display: "flex", alignItems: "center", justifyContent: "center", color: t.textTertiary, fontSize: 12 }}>No data</div>;
  const r = size / 2 - 10;
  const cx = size / 2;
  const cy = size / 2;
  let cumulative = 0;
  const paths = segments.filter((s) => s.value > 0).map((seg) => {
    const start = cumulative;
    cumulative += seg.value;
    const startAngle = (start / total) * 2 * Math.PI - Math.PI / 2;
    const endAngle = (cumulative / total) * 2 * Math.PI - Math.PI / 2;
    const largeArc = endAngle - startAngle > Math.PI ? 1 : 0;
    const x1 = cx + r * Math.cos(startAngle);
    const y1 = cy + r * Math.sin(startAngle);
    const x2 = cx + r * Math.cos(endAngle);
    const y2 = cy + r * Math.sin(endAngle);
    return <path key={seg.label} d={`M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z`} fill={seg.color} />;
  });
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {paths}
        <circle cx={cx} cy={cy} r={r * 0.55} fill={t.cardBg} />
        <text x={cx} y={cy - 2} textAnchor="middle" fill={t.textPrimary} fontSize="16" fontWeight="700">{total}</text>
        <text x={cx} y={cy + 10} textAnchor="middle" fill={t.textSecondary} fontSize="8">TOTAL</text>
      </svg>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, justifyContent: "center" }}>
        {segments.filter((s) => s.value > 0).map((seg) => (
          <span key={seg.label} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 10, color: t.textSecondary }}>
            <span style={{ width: 7, height: 7, borderRadius: "50%", background: seg.color }} />
            {seg.label} ({seg.value})
          </span>
        ))}
      </div>
    </div>
  );
}

/* ── Prompt copy button (copies prompt text to clipboard) ── */
/* Uses a plain <span> (no <button> / SVG) and defers the clipboard
   write so the host platform's MutationObserver never sees a DOM
   change it can't handle. */
function PromptAction({ label, prompt, t }: {
  label: string;
  prompt: string;
  t: ThemeColors;
}) {
  const handlePointerDown = (e: React.PointerEvent) => {
    e.stopPropagation();
    e.preventDefault();
    // Defer clipboard write off the synchronous event / mutation stack
    setTimeout(() => {
      navigator.clipboard.writeText(prompt).catch(() => {
        /* fallback: execCommand */
        const ta = document.createElement("textarea");
        ta.value = prompt;
        ta.style.position = "fixed";
        ta.style.left = "-9999px";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
      });
    }, 0);
  };

  return (
    <span
      onPointerDown={handlePointerDown}
      style={{
        padding: "4px 10px", borderRadius: 6, fontSize: 11, fontWeight: 500,
        border: `1px solid ${t.brand}33`,
        background: t.brandLight,
        color: t.brand,
        cursor: "pointer", fontFamily: "inherit", display: "inline-flex",
        alignItems: "center", gap: 4, whiteSpace: "nowrap",
        userSelect: "none",
      }}
      title={"Copy prompt: " + prompt}
    >
      &#x2398;&#xFE0E; {label}
    </span>
  );
}

/* ── Types ── */
const fallback: DashboardData = { consultants: [], projects: [], assignments: [], summary: { totalConsultants: 0, totalProjects: 0, totalAssignments: 0, totalBillableHours: 0 } };

/* ═══════════════════════════════════════════════════════════════════
   DASHBOARD — read-only overview; actions are driven by user prompts
   ═══════════════════════════════════════════════════════════════════ */
export function Dashboard() {
  const t = useThemeColors();
  const toolOutput = useOpenAiGlobal<DashboardData>("toolOutput");
  const data = toolOutput ?? fallback;
  const allAssignments = data.assignments ?? [];

  /* ── Fullscreen toggle ── */
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
  }, []);

  /* ── Computed analytics ── */
  const analytics = useMemo(() => {
    const billable = allAssignments.filter((a) => a.billable);
    const nonBillable = allAssignments.filter((a) => !a.billable);
    const totalForecastHrs = allAssignments.reduce((sum, a) => sum + (a.forecast ?? []).reduce((x, f) => x + f.hours, 0), 0);
    const totalDeliveredHrs = allAssignments.reduce((sum, a) => sum + (a.delivered ?? []).reduce((x, d) => x + d.hours, 0), 0);
    const avgRate = allAssignments.length > 0 ? Math.round(allAssignments.reduce((sum, a) => sum + (a.rate ?? 0), 0) / allAssignments.length) : 0;
    const totalRevenue = billable.reduce((sum, a) => sum + (a.rate ?? 0) * (a.forecast ?? []).reduce((x, f) => x + f.hours, 0), 0);

    // Monthly forecast
    const monthMap = new Map<string, number>();
    allAssignments.forEach((a) => (a.forecast ?? []).forEach((f) => {
      const key = `${f.year}-${String(f.month).padStart(2, "0")}`;
      monthMap.set(key, (monthMap.get(key) ?? 0) + f.hours);
    }));
    const monthlyForecast = [...monthMap.entries()].sort().map(([key, hours]) => ({
      label: MONTH_NAMES[parseInt(key.split("-")[1]) - 1] + " " + key.split("-")[0].slice(2),
      value: hours,
    }));

    // Consultant summaries
    const consultantSummaries = data.consultants.map((c) => {
      const myAsn = allAssignments.filter((a) => a.consultantId === c.id);
      const forecastHrs = myAsn.reduce((sum, a) => sum + (a.forecast ?? []).reduce((x, f) => x + f.hours, 0), 0);
      const revenue = myAsn.filter((a) => a.billable).reduce((sum, a) => sum + (a.rate ?? 0) * (a.forecast ?? []).reduce((x, f) => x + f.hours, 0), 0);
      return { ...c, projectCount: myAsn.length, forecastHrs, revenue };
    });

    // Project summaries
    const projectSummaries = data.projects.map((p) => {
      const projAsn = allAssignments.filter((a) => a.projectId === p.id);
      const forecastHrs = projAsn.reduce((sum, a) => sum + (a.forecast ?? []).reduce((x, f) => x + f.hours, 0), 0);
      const revenue = projAsn.filter((a) => a.billable).reduce((sum, a) => sum + (a.rate ?? 0) * (a.forecast ?? []).reduce((x, f) => x + f.hours, 0), 0);
      return { ...p, teamSize: projAsn.length, forecastHrs, revenue };
    });

    // Role distribution
    const roleMap = new Map<string, number>();
    allAssignments.forEach((a) => roleMap.set(a.role, (roleMap.get(a.role) ?? 0) + 1));
    const roleDistribution = [...roleMap.entries()].sort((a, b) => b[1] - a[1]);

    return {
      billableCount: billable.length,
      nonBillableCount: nonBillable.length,
      totalForecastHrs,
      totalDeliveredHrs,
      avgRate,
      totalRevenue,
      monthlyForecast,
      consultantSummaries,
      projectSummaries,
      roleDistribution,
    };
  }, [data, allAssignments]);

  const cardStyle: React.CSSProperties = {
    background: t.cardBg, borderRadius: 12,
    boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
    border: `1px solid ${t.divider}`,
  };

  /* ── Filter banner (when server-side filters are active) ── */
  const hasFilters = data.filters && (
    data.filters.consultantName || data.filters.projectName || data.filters.skill || data.filters.role || data.filters.billable !== undefined
  );

  /* ═══════════════════════════════════════════════════════
     RENDER
     ═══════════════════════════════════════════════════════ */
  return (
    <div style={{
      display: "flex", flexDirection: "column", gap: 20, padding: 24,
      fontFamily: '"Segoe Sans", "Segoe UI", "Segoe UI Web (West European)", -apple-system, BlinkMacSystemFont, Roboto, "Helvetica Neue", Arial, sans-serif',
      boxSizing: "border-box", width: "100%", background: t.surface,
      minHeight: "100%", color: t.textPrimary,
      ...(isFullscreen ? { position: "fixed" as const, top: 0, left: 0, right: 0, bottom: 0, zIndex: 9999, overflowY: "auto" as const } : {}),
    }}>

      {/* ── Header ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 700, color: t.textPrimary, letterSpacing: "-0.3px", display: "flex", alignItems: "center", gap: 10 }}>
            <ArrowTrendingLines24Regular style={{ color: t.brand }} />
            HR Analytics
          </div>
          <div style={{ fontSize: 13, color: t.textSecondary, marginTop: 2 }}>
            {data.summary.totalConsultants} consultants &middot; {data.summary.totalProjects} projects &middot; {allAssignments.length} assignments
          </div>
        </div>
        <button
          onClick={toggleFullscreen}
          title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
          style={{
            padding: 8, borderRadius: 8, border: `1px solid ${t.divider}`,
            background: isFullscreen ? t.brandLight : t.cardBg, color: t.textPrimary,
            cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
            transition: "background 0.15s ease", lineHeight: 0,
          }}
        >
          {isFullscreen ? <FullScreenMinimize24Regular /> : <FullScreenMaximize24Regular />}
        </button>
      </div>

      {/* ── Active filter banner ── */}
      {hasFilters && (
        <div style={{ ...cardStyle, padding: "10px 16px", display: "flex", alignItems: "center", gap: 8, background: t.brandLight, border: `1px solid ${t.brand}33` }}>
          <Info16Regular style={{ color: t.brand, flexShrink: 0 }} />
          <span style={{ fontSize: 12, color: t.brand }}>
            Filtered view
            {data.filters?.consultantName && <> &middot; consultant: <strong>{data.filters.consultantName}</strong></>}
            {data.filters?.projectName && <> &middot; project: <strong>{data.filters.projectName}</strong></>}
            {data.filters?.skill && <> &middot; skill: <strong>{data.filters.skill}</strong></>}
            {data.filters?.role && <> &middot; role: <strong>{data.filters.role}</strong></>}
            {data.filters?.billable !== undefined && <> &middot; {data.filters.billable ? "billable only" : "non-billable only"}</>}
          </span>
        </div>
      )}

      {/* ── KPI Cards ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 14 }}>
        {[
          { icon: <People24Regular />, val: data.consultants.length, label: "Consultants", ibg: t.brandLight, ic: t.brand },
          { icon: <Briefcase24Regular />, val: data.projects.length, label: "Projects", ibg: t.purpleBg, ic: t.purple },
          { icon: <Clock24Regular />, val: data.summary.totalBillableHours.toLocaleString(), label: "Billable Hours", ibg: t.greenBg, ic: t.green },
          { icon: <MoneyHand20Regular />, val: `$${(analytics.totalRevenue / 1000).toFixed(0)}k`, label: "Forecast Revenue", ibg: t.amberBg, ic: t.amber },
        ].map(({ icon, val, label, ibg, ic }) => (
          <div key={label} style={{ ...cardStyle, padding: 16, display: "flex", flexDirection: "column", gap: 6 }}>
            <div style={{ width: 36, height: 36, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", background: ibg, color: ic }}>{icon}</div>
            <span style={{ fontSize: 24, fontWeight: 700, lineHeight: "1.1", color: t.textPrimary, letterSpacing: "-0.5px" }}>{val}</span>
            <span style={{ fontSize: 10, fontWeight: 500, color: t.textSecondary, textTransform: "uppercase", letterSpacing: "0.5px" }}>{label}</span>
          </div>
        ))}
      </div>

      {/* ── Charts ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 14 }}>
        {analytics.monthlyForecast.length > 0 && (
          <div style={{ ...cardStyle, padding: 16, display: "flex", flexDirection: "column", gap: 10 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: t.textPrimary, display: "flex", alignItems: "center", gap: 6 }}>
              <ArrowTrendingLines24Regular style={{ fontSize: 16, color: t.brand }} />Monthly Forecast
            </div>
            <BarChart data={analytics.monthlyForecast} t={t} />
          </div>
        )}

        <div style={{ ...cardStyle, padding: 16, display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: t.textPrimary, display: "flex", alignItems: "center", gap: 6 }}>
            <DataUsage24Regular style={{ fontSize: 16, color: t.purple }} />Assignments
          </div>
          <div style={{ display: "flex", justifyContent: "center" }}>
            <DonutChart
              segments={[
                { label: "Billable", value: analytics.billableCount, color: t.green },
                { label: "Non-Billable", value: analytics.nonBillableCount, color: t.amber },
              ]}
              t={t}
              size={100}
            />
          </div>
        </div>

        {analytics.roleDistribution.length > 0 && (
          <div style={{ ...cardStyle, padding: 16, display: "flex", flexDirection: "column", gap: 10 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: t.textPrimary, display: "flex", alignItems: "center", gap: 6 }}>
              <PersonBoard20Regular style={{ fontSize: 16, color: t.purple }} />Roles
            </div>
            <BarChart
              data={analytics.roleDistribution.slice(0, 6).map(([role, count], i) => ({
                label: role.length > 8 ? role.slice(0, 7) + "…" : role,
                value: count,
                color: [t.brand, t.purple, t.green, t.amber, "#0e7490", "#b45309"][i % 6],
              }))}
              t={t}
            />
          </div>
        )}
      </div>

      {/* ── Hours summary ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: 12 }}>
        {[
          { v: analytics.totalForecastHrs.toLocaleString(), l: "Forecast Hrs", c: t.brand },
          { v: analytics.totalDeliveredHrs.toLocaleString(), l: "Delivered Hrs", c: t.green },
          { v: `$${analytics.avgRate}/hr`, l: "Avg Rate", c: t.purple },
          { v: `${analytics.totalForecastHrs > 0 ? Math.round((analytics.totalDeliveredHrs / analytics.totalForecastHrs) * 100) : 0}%`, l: "Delivery Rate", c: t.amber },
        ].map(({ v, l, c }) => (
          <div key={l} style={{ ...cardStyle, padding: 14, display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}>
            <span style={{ fontSize: 22, fontWeight: 700, color: c, letterSpacing: "-0.5px" }}>{v}</span>
            <span style={{ fontSize: 10, fontWeight: 500, color: t.textSecondary, textTransform: "uppercase", letterSpacing: "0.3px", textAlign: "center" }}>{l}</span>
          </div>
        ))}
      </div>

      {/* ── Consultants ── */}
      {analytics.consultantSummaries.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ fontSize: 16, fontWeight: 600, color: t.textPrimary, display: "flex", alignItems: "center", gap: 8 }}>
            <People24Regular style={{ fontSize: 18, color: t.brand }} /> Consultants
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {analytics.consultantSummaries
              .sort((a, b) => b.forecastHrs - a.forecastHrs)
              .map((c) => (
                <div key={c.id} style={{ ...cardStyle, padding: "12px 16px", display: "flex", alignItems: "center", gap: 12 }}>
                  <Avatar src={c.photoUrl} name={c.name} size={36} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 16, fontWeight: 600, color: t.textPrimary }}>{c.name}</div>
                    <div style={{ fontSize: 11, color: t.textSecondary }}>
                      {c.location?.city}{c.location?.country ? `, ${c.location.country}` : ""} &middot; {c.projectCount} project{c.projectCount !== 1 ? "s" : ""} &middot; {c.forecastHrs.toLocaleString()} hrs
                    </div>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
                    {c.revenue > 0 && (
                      <span style={{ fontSize: 13, fontWeight: 600, color: t.green }}>${(c.revenue / 1000).toFixed(1)}k</span>
                    )}
                    <PromptAction label="Profile" prompt={"Show profile for " + c.name} t={t} />
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* ── Projects ── */}
      {analytics.projectSummaries.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ fontSize: 16, fontWeight: 600, color: t.textPrimary, display: "flex", alignItems: "center", gap: 8 }}>
            <Briefcase24Regular style={{ fontSize: 18, color: t.purple }} /> Projects
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {analytics.projectSummaries
              .sort((a, b) => b.forecastHrs - a.forecastHrs)
              .map((p) => (
                <div key={p.id} style={{ ...cardStyle, padding: "12px 16px", display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{ width: 36, height: 36, borderRadius: 8, background: t.purpleBg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, color: t.purple }}>
                    <Briefcase24Regular style={{ fontSize: 18 }} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 16, fontWeight: 600, color: t.textPrimary }}>{p.name}</div>
                    <div style={{ fontSize: 11, color: t.textSecondary }}>
                      {p.clientName} &middot; {p.teamSize} member{p.teamSize !== 1 ? "s" : ""} &middot; {p.forecastHrs.toLocaleString()} hrs
                    </div>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
                    {p.revenue > 0 && (
                      <span style={{ fontSize: 13, fontWeight: 600, color: t.green }}>${(p.revenue / 1000).toFixed(1)}k</span>
                    )}
                    <PromptAction label="Details" prompt={"Show details for project " + p.name} t={t} />
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* ── Empty state ── */}
      {data.consultants.length === 0 && data.projects.length === 0 && (
        <div style={{ ...cardStyle, padding: "48px 24px", textAlign: "center", color: t.textTertiary }}>
          <People24Regular style={{ fontSize: 40, color: t.textTertiary, display: "block", margin: "0 auto 12px" }} />
          <Body1>No data loaded yet.</Body1>
          <Caption1 style={{ marginTop: 4, color: t.textTertiary }}>Use the MCP tool to hydrate this dashboard with HR data.</Caption1>
        </div>
      )}

      {/* ── Prompt tips ── */}
      {data.consultants.length > 0 && (
        <div style={{
          ...cardStyle, padding: "12px 16px",
          background: t.surface, borderStyle: "dashed",
          display: "flex", alignItems: "flex-start", gap: 8,
        }}>
          <Info16Regular style={{ color: t.textTertiary, flexShrink: 0, marginTop: 2 }} />
          <div style={{ fontSize: 12, color: t.textSecondary, lineHeight: 1.5 }}>
            <strong>Tip:</strong> Use prompts to take action — e.g. <em>"Assign Sarah to Project Alpha"</em>,
            {" "}<em>"Show consultants with React skills"</em>, or <em>"Open bulk editor for all consultants"</em>.
            The dashboard will update to reflect any changes.
          </div>
        </div>
      )}
    </div>
  );
}

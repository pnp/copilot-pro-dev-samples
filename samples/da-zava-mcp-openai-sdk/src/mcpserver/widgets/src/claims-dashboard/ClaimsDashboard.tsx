import React, { useState, useCallback, useMemo } from "react";
import {
  makeStyles,
  Text,
  Button,
  Divider,
  tokens,
} from "@fluentui/react-components";
import {
  TaskListLtrRegular,
  CheckmarkCircleRegular,
  DismissCircleRegular,
  ClockRegular,
  AlertRegular,
  DocumentRegular,
  ArrowMaximizeRegular,
  ArrowMinimizeRegular,
  ArrowLeftRegular,
  PersonRegular,
  LocationRegular,
  CalendarRegular,
  ReceiptMoneyRegular,
  NoteRegular,
  ShieldCheckmarkRegular,
  ArrowSortRegular,
} from "@fluentui/react-icons";
import { useOpenAiGlobal } from "../hooks/useOpenAiGlobal";
import { useThemeColors } from "../hooks/useThemeColors";
import { FakeMap } from "./FakeMap";
import type { ClaimsDashboardData, Claim } from "../types";

/* ─── Styles ─────────────────────────────────────────────────────────── */
const useStyles = makeStyles({
  root: { fontFamily: tokens.fontFamilyBase, width: "100%", overflow: "auto" },

  header: {
    display: "flex", alignItems: "center", gap: "16px",
    padding: "24px 24px 0",
  },
  headerIcon: {
    display: "flex", alignItems: "center", justifyContent: "center",
    width: "48px", height: "48px", borderRadius: "14px", flexShrink: 0,
  },

  grid: {
    display: "grid", gridTemplateColumns: "repeat(3, 1fr)",
    gap: "16px", padding: "16px 24px 24px",
  },
  gridCard: {
    display: "flex", flexDirection: "column" as const, borderRadius: "12px",
    overflow: "hidden", cursor: "pointer",
    transition: "transform 0.18s ease, box-shadow 0.18s ease",
    ":hover": { transform: "translateY(-3px)" },
  },
  cardTop: {
    padding: "16px 16px 12px", display: "flex",
    flexDirection: "column" as const, gap: "8px", flex: 1,
  },
  cardTopRow: { display: "flex", justifyContent: "space-between", alignItems: "center" },
  damageRow: { display: "flex", gap: "4px", flexWrap: "wrap" as const, marginTop: "2px" },
  cardBottom: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "10px 16px",
  },

  detail: { padding: "20px", fontFamily: tokens.fontFamilyBase },
  detailHeader: {
    display: "flex", justifyContent: "space-between", alignItems: "flex-start",
    marginBottom: "20px",
  },
  detailBody: {
    display: "grid", gridTemplateColumns: "1fr 1fr",
    gap: "20px",
  },
  section: { marginBottom: "16px" },
  sectionHeader: {
    display: "flex", alignItems: "center", gap: "8px",
    marginBottom: "10px",
  },
  infoGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" },
  infoCard: {
    display: "flex", alignItems: "flex-start", gap: "12px",
    padding: "14px", borderRadius: "10px",
  },
  infoIconWrap: {
    display: "flex", alignItems: "center", justifyContent: "center",
    width: "36px", height: "36px", borderRadius: "10px", flexShrink: 0,
  },
  tags: { display: "flex", gap: "6px", flexWrap: "wrap" as const, marginTop: "4px" },
});

/* ─── Helpers ────────────────────────────────────────────────────────── */
function statusPillColors(s: string, colors: ReturnType<typeof useThemeColors>): { bg: string; fg: string } {
  const l = s.toLowerCase();
  if (l.includes("approved") || l.includes("completed")) return { bg: colors.successSubtle, fg: colors.success };
  if (l.includes("pending") || l.includes("scheduled")) return { bg: colors.warningSubtle, fg: colors.warning };
  if (l.includes("denied") || l.includes("rejected") || l.includes("cancelled")) return { bg: colors.errorSubtle, fg: colors.error };
  if (l.includes("closed")) return { bg: colors.infoSubtle, fg: colors.info };
  return { bg: colors.primarySubtle, fg: colors.primary };
}

function statusIcon(s: string) {
  const l = s.toLowerCase();
  if (l.includes("approved") || l.includes("completed")) return <CheckmarkCircleRegular />;
  if (l.includes("pending") || l.includes("scheduled")) return <ClockRegular />;
  if (l.includes("denied") || l.includes("cancelled")) return <DismissCircleRegular />;
  if (l.includes("closed")) return <DocumentRegular />;
  return <AlertRegular />;
}

function priorityColor(p: string): string {
  switch (p.toLowerCase()) {
    case "high": case "urgent": return "#d13438";
    case "medium": return "#ffb900";
    case "low": return "#107c10";
    default: return "#616161";
  }
}

function derivePriority(claim: Claim): string {
  if (claim.estimatedLoss >= 50000) return "high";
  if (claim.estimatedLoss >= 15000) return "medium";
  return "low";
}

function StatusPill({ label, status, icon, size = "small", colors }: {
  label: string;
  status: string;
  icon?: React.ReactNode;
  size?: "small" | "medium";
  colors: ReturnType<typeof useThemeColors>;
}) {
  const { bg, fg } = statusPillColors(status, colors);
  const isSmall = size === "small";
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: "4px",
      padding: isSmall ? "2px 8px" : "3px 10px",
      borderRadius: "999px",
      backgroundColor: bg, color: fg,
      border: `1px solid ${fg}30`,
      fontSize: isSmall ? "11px" : "12px",
      fontWeight: 600, lineHeight: "1.3",
      whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
      maxWidth: "100%", flexShrink: 0,
    }}>
      {icon && <span style={{ display: "inline-flex", fontSize: isSmall ? "12px" : "14px", flexShrink: 0 }}>{icon}</span>}
      {label}
    </span>
  );
}

/* ─── Grid Card ──────────────────────────────────────────────────────── */
function ClaimCard({ claim, colors, styles, onClick }: {
  claim: Claim;
  colors: ReturnType<typeof useThemeColors>;
  styles: ReturnType<typeof useStyles>;
  onClick: () => void;
}) {
  const pColor = priorityColor(derivePriority(claim));
  return (
    <div className={styles.gridCard} style={{
      backgroundColor: colors.surface,
      boxShadow: colors.shadowCard,
      border: `1px solid ${colors.borderSubtle}`,
    }} onClick={onClick}>
      <div style={{ height: "3px", background: pColor, borderRadius: "12px 12px 0 0" }} />
      <div className={styles.cardTop}>
        <div className={styles.cardTopRow}>
          <Text weight="semibold" size={300} style={{ fontFamily: "monospace", color: colors.textSecondary, letterSpacing: "0.02em" }}>
            {claim.claimNumber}
          </Text>
          <StatusPill label={claim.status.split(" - ")[0]} status={claim.status} icon={statusIcon(claim.status)} size="small" colors={colors} />
        </div>
        <div>
          <Text size={300} weight="semibold" style={{ display: "block", marginBottom: "2px" }}>{claim.policyHolderName}</Text>
          <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <LocationRegular style={{ fontSize: "12px", color: colors.textTertiary }} />
            <Text size={200} style={{ color: colors.textSecondary }}>{claim.property}</Text>
          </div>
        </div>
        <Text size={200} style={{ color: colors.textTertiary, lineHeight: "1.4" }}>
          {claim.description.length > 90 ? claim.description.slice(0, 90) + "…" : claim.description}
        </Text>
        <div className={styles.damageRow}>
          {claim.damageTypes.slice(0, 3).map((dt, i) => (
            <span key={i} style={{
              display: "inline-flex", padding: "1px 7px", borderRadius: "999px",
              fontSize: "10px", fontWeight: 500, whiteSpace: "nowrap",
              color: colors.textSecondary, border: `1px solid ${colors.borderSubtle}`,
              backgroundColor: colors.surfaceHover,
            }}>{dt}</span>
          ))}
          {claim.damageTypes.length > 3 && <span style={{
            display: "inline-flex", padding: "1px 7px", borderRadius: "999px",
            fontSize: "10px", fontWeight: 500, whiteSpace: "nowrap",
            color: colors.textTertiary, border: `1px solid ${colors.borderSubtle}`,
          }}>+{claim.damageTypes.length - 3}</span>}
        </div>
      </div>
      <div className={styles.cardBottom} style={{ borderTop: `1px solid ${colors.borderSubtle}`, backgroundColor: colors.surfaceHover + "44" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
          <CalendarRegular style={{ fontSize: "12px", color: colors.textTertiary }} />
          <Text size={200} style={{ color: colors.textTertiary }}>{new Date(claim.dateOfLoss).toLocaleDateString()}</Text>
        </div>
        <Text weight="bold" size={300} style={{ color: colors.primary }}>${claim.estimatedLoss.toLocaleString()}</Text>
      </div>
    </div>
  );
}

/* ═════════════════════════════════════════════════════════════════════
   MAIN COMPONENT
   Card grid → click a claim → read-only detail view with map.
   All edits (status changes, inspections, POs) are handled by
   prompting the AI in chat — the widget focuses on display.
   ═════════════════════════════════════════════════════════════════════ */
/* ─── Sort options ────────────────────────────────────────────────────── */
type SortField = "none" | "estimatedLoss" | "dateReported";
type SortOrder = "asc" | "desc";

const SORT_OPTIONS: { value: SortField; label: string }[] = [
  { value: "none", label: "Default" },
  { value: "estimatedLoss", label: "Estimated Loss" },
  { value: "dateReported", label: "Date Reported" },
];

function sortClaims(claims: Claim[], field: SortField, order: SortOrder): Claim[] {
  if (field === "none") return claims; // preserve server order
  return [...claims].sort((a, b) => {
    let va: any = (a as any)[field];
    let vb: any = (b as any)[field];
    if (va == null && vb == null) return 0;
    if (va == null) return 1;
    if (vb == null) return -1;
    if (typeof va === "string") va = va.toLowerCase();
    if (typeof vb === "string") vb = vb.toLowerCase();
    const dir = order === "asc" ? 1 : -1;
    if (va < vb) return -1 * dir;
    if (va > vb) return 1 * dir;
    return 0;
  });
}

export function ClaimsDashboard() {
  const styles = useStyles();
  const colors = useThemeColors();
  const data = useOpenAiGlobal("toolOutput") as ClaimsDashboardData | null;

  const rawClaims = data?.claims ?? [];

  // Sort state — defaults to "none" which preserves the server's order
  // (server already sorts when AI passes sortBy/sortOrder params via prompt)
  const [localSortBy, setLocalSortBy] = useState<SortField>("none");
  const [localSortOrder, setLocalSortOrder] = useState<SortOrder>("desc");

  const claims = useMemo(() => sortClaims(rawClaims, localSortBy, localSortOrder), [rawClaims, localSortBy, localSortOrder]);

  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const selectedClaim = useMemo(() =>
    claims.find(c => c.id === selectedClaimId) ?? null,
  [claims, selectedClaimId]);

  const openDetail = useCallback((claim: Claim) => {
    setSelectedClaimId(claim.id);
  }, []);

  const goBack = useCallback(() => {
    setSelectedClaimId(null);
  }, []);

  const toggleFullscreen = useCallback(async () => {
    if (window.openai?.requestDisplayMode) {
      const cur = window.openai.displayMode;
      await window.openai.requestDisplayMode({ mode: cur === "fullscreen" ? "inline" : "fullscreen" });
      setIsFullscreen(p => !p);
      return;
    }
    console.warn("requestDisplayMode is not available on this platform — falling back to native fullscreen.");
    try {
      if (!document.fullscreenElement) await document.documentElement.requestFullscreen();
      else await document.exitFullscreen();
    } catch {}
    setIsFullscreen(p => !p);
  }, []);

  /* ═══════════════════════════════════════════════════════════════════
     DETAIL VIEW — read-only claim overview + map
     ═══════════════════════════════════════════════════════════════════ */
  if (selectedClaim) {
    const claim = selectedClaim;
    return (
      <div className={styles.detail} style={{ backgroundColor: colors.background, color: colors.text }}>
        {/* Header */}
        <div className={styles.detailHeader}>
          <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
            <Button icon={<ArrowLeftRegular />} appearance="subtle" onClick={goBack} title="Back to Claims" size="small"
              style={{ borderRadius: "10px", width: "36px", height: "36px" }} />
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
                <Text size={600} weight="bold" style={{ letterSpacing: "-0.01em" }}>{claim.claimNumber}</Text>
                <StatusPill label={claim.status.split(" - ")[0]} status={claim.status} icon={statusIcon(claim.status)} size="medium" colors={colors} />
                <span style={{
                  display: "inline-flex", alignItems: "center",
                  padding: "2px 8px", borderRadius: "999px", fontSize: "11px", fontWeight: 600,
                  whiteSpace: "nowrap",
                  backgroundColor: priorityColor(derivePriority(claim)) + "18",
                  color: priorityColor(derivePriority(claim)),
                  border: `1px solid ${priorityColor(derivePriority(claim))}40`,
                }}>{derivePriority(claim)} priority</span>
              </div>
              <Text size={200} style={{ color: colors.textTertiary }}>{claim.status} &middot; Filed {new Date(claim.dateOfLoss).toLocaleDateString()}</Text>
            </div>
          </div>
          <Button icon={isFullscreen ? <ArrowMinimizeRegular /> : <ArrowMaximizeRegular />} appearance="subtle" onClick={toggleFullscreen}
            style={{ borderRadius: "10px" }} />
        </div>

        {/* Two-column body: info left, map right */}
        <div className={styles.detailBody}>
          {/* LEFT COLUMN — Info */}
          <div>
            {/* Info cards */}
            <div className={styles.infoGrid}>
              <div className={styles.infoCard} style={{ backgroundColor: colors.surface, border: `1px solid ${colors.borderSubtle}`, borderRadius: "12px" }}>
                <div className={styles.infoIconWrap} style={{ backgroundColor: colors.primarySubtle }}>
                  <PersonRegular style={{ color: colors.primary, fontSize: "18px" }} />
                </div>
                <div style={{ minWidth: 0 }}>
                  <Text size={200} style={{ color: colors.textTertiary }} block>Policy Holder</Text>
                  <Text weight="semibold" size={300}>{claim.policyHolderName}</Text>
                  <Text size={200} block style={{ color: colors.textSecondary }}>{claim.policyHolderEmail}</Text>
                </div>
              </div>
              <div className={styles.infoCard} style={{ backgroundColor: colors.surface, border: `1px solid ${colors.borderSubtle}`, borderRadius: "12px" }}>
                <div className={styles.infoIconWrap} style={{ backgroundColor: colors.primarySubtle }}>
                  <LocationRegular style={{ color: colors.primary, fontSize: "18px" }} />
                </div>
                <div style={{ minWidth: 0 }}>
                  <Text size={200} style={{ color: colors.textTertiary }} block>Property</Text>
                  <Text weight="semibold" size={300}>{claim.property}</Text>
                </div>
              </div>
              <div className={styles.infoCard} style={{ backgroundColor: colors.surface, border: `1px solid ${colors.borderSubtle}`, borderRadius: "12px" }}>
                <div className={styles.infoIconWrap} style={{ backgroundColor: colors.warningSubtle }}>
                  <CalendarRegular style={{ color: colors.warning, fontSize: "18px" }} />
                </div>
                <div style={{ minWidth: 0 }}>
                  <Text size={200} style={{ color: colors.textTertiary }} block>Date of Loss</Text>
                  <Text weight="semibold" size={300}>{new Date(claim.dateOfLoss).toLocaleDateString()}</Text>
                </div>
              </div>
              <div className={styles.infoCard} style={{ backgroundColor: colors.surface, border: `1px solid ${colors.borderSubtle}`, borderRadius: "12px" }}>
                <div className={styles.infoIconWrap} style={{ backgroundColor: colors.errorSubtle }}>
                  <ReceiptMoneyRegular style={{ color: colors.error, fontSize: "18px" }} />
                </div>
                <div style={{ minWidth: 0 }}>
                  <Text size={200} style={{ color: colors.textTertiary }} block>Estimated Loss</Text>
                  <Text weight="bold" size={400} style={{ color: colors.error }}>${claim.estimatedLoss.toLocaleString()}</Text>
                </div>
              </div>
            </div>

            {/* Description */}
            <div className={styles.section} style={{ marginTop: "16px" }}>
              <div className={styles.sectionHeader}>
                <Text weight="semibold" size={300}>Description</Text>
              </div>
              <div style={{ padding: "12px 14px", backgroundColor: colors.surface, borderRadius: "10px", border: `1px solid ${colors.borderSubtle}` }}>
                <Text size={200} style={{ lineHeight: "1.6", color: colors.textSecondary }}>{claim.description}</Text>
              </div>
            </div>

            {/* Damage Types & Policy */}
            <div style={{ display: "flex", gap: "16px", marginTop: "4px" }}>
              <div style={{ flex: 1 }}>
                <div className={styles.sectionHeader}>
                  <Text weight="semibold" size={300}>Damage Types</Text>
                </div>
                <div className={styles.tags}>
                  {claim.damageTypes.map((dt, i) => (
                    <span key={i} style={{
                      display: "inline-flex", padding: "3px 10px", borderRadius: "999px",
                      fontSize: "12px", fontWeight: 500, whiteSpace: "nowrap",
                      backgroundColor: colors.errorSubtle, color: colors.error,
                      border: `1px solid ${colors.error}30`,
                    }}>{dt}</span>
                  ))}
                </div>
              </div>
              <div>
                <div className={styles.sectionHeader}>
                  <ShieldCheckmarkRegular style={{ color: colors.primary, fontSize: "16px" }} />
                  <Text weight="semibold" size={300}>Policy</Text>
                </div>
                <Text size={200} style={{ fontFamily: "monospace", color: colors.textSecondary }}>{claim.policyNumber}</Text>
              </div>
            </div>

            {/* Notes */}
            {claim.notes.length > 0 && (
              <div className={styles.section} style={{ marginTop: "16px" }}>
                <div className={styles.sectionHeader}>
                  <NoteRegular style={{ color: colors.primary, fontSize: "16px" }} />
                  <Text weight="semibold" size={300}>Notes ({claim.notes.length})</Text>
                </div>
                <div style={{ padding: "12px 14px", backgroundColor: colors.surface, borderRadius: "10px", border: `1px solid ${colors.borderSubtle}` }}>
                  {claim.notes.map((n, i) => (
                    <Text key={i} size={200} block style={{ color: colors.textSecondary, paddingLeft: "4px", marginBottom: "4px", lineHeight: "1.5" }}>
                      &bull; {n}
                    </Text>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* RIGHT COLUMN — Map */}
          <div>
            <div className={styles.sectionHeader}>
              <LocationRegular style={{ color: colors.primary, fontSize: "16px" }} />
              <Text weight="semibold" size={300}>Property Location</Text>
            </div>
            <FakeMap address={claim.property} colors={colors} style={{ height: "280px" }} />
          </div>
        </div>

        <Divider style={{ margin: "16px 0" }} />
        <Text size={200} style={{ color: colors.textTertiary, fontStyle: "italic" }}>
          To update this claim, create inspections, or manage purchase orders — ask in chat.
        </Text>
      </div>
    );
  }

  /* ═══════════════════════════════════════════════════════════════════
     GRID VIEW — card grid of claims
     ═══════════════════════════════════════════════════════════════════ */
  return (
    <div className={styles.root} style={{ backgroundColor: colors.background, color: colors.text }}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerIcon} style={{
          backgroundColor: colors.primarySubtle,
          color: colors.primary,
          boxShadow: `0 0 0 4px ${colors.primary}12`,
        }}>
          <TaskListLtrRegular style={{ fontSize: "24px" }} />
        </div>
        <div style={{ minWidth: 0, flex: 1 }}>
          <Text size={500} weight="bold" style={{ display: "block", letterSpacing: "-0.01em" }}>Claims Dashboard</Text>
          <Text size={200} style={{ color: colors.textTertiary }}>
            Zava Insurance &middot; {claims.length} claims
          </Text>
        </div>
        <button onClick={toggleFullscreen} title="Fullscreen" style={{
          background: "none", border: `1px solid ${colors.borderSubtle}`,
          cursor: "pointer", color: colors.textSecondary, padding: "8px",
          borderRadius: "10px", display: "flex", alignItems: "center",
        }}>
          <ArrowMaximizeRegular style={{ fontSize: "16px" }} />
        </button>
      </div>

      {/* Sort toolbar */}
      {claims.length > 0 && (
        <div style={{
          display: "flex", alignItems: "center", gap: "10px",
          padding: "12px 24px 0",
        }}>
          <ArrowSortRegular style={{ fontSize: "16px", color: colors.textTertiary }} />
          <Text size={200} style={{ color: colors.textTertiary }}>Sort by</Text>
          <select
            value={localSortBy}
            onChange={(e) => setLocalSortBy(e.target.value as SortField)}
            style={{
              appearance: "none", WebkitAppearance: "none",
              padding: "4px 28px 4px 10px", borderRadius: "8px",
              border: `1px solid ${colors.borderSubtle}`,
              backgroundColor: colors.surface, color: colors.text,
              fontSize: "12px", fontWeight: 500, fontFamily: "inherit",
              cursor: "pointer", outline: "none",
              backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M3 5l3 3 3-3' fill='none' stroke='%23888' stroke-width='1.5'/%3E%3C/svg%3E")`,
              backgroundRepeat: "no-repeat", backgroundPosition: "right 8px center",
            }}
          >
            {SORT_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
          <button
            onClick={() => setLocalSortOrder(o => o === "asc" ? "desc" : "asc")}
            title={localSortOrder === "asc" ? "Ascending" : "Descending"}
            style={{
              display: "inline-flex", alignItems: "center", gap: "4px",
              padding: "4px 10px", borderRadius: "8px",
              border: `1px solid ${colors.borderSubtle}`,
              backgroundColor: colors.surface, color: colors.text,
              fontSize: "12px", fontWeight: 500, cursor: "pointer",
              fontFamily: "inherit",
            }}
          >
            {localSortOrder === "asc" ? "↑ Asc" : "↓ Desc"}
          </button>
        </div>
      )}

      {/* Grid */}
      {claims.length === 0 ? (
        <div style={{ padding: "48px 24px", textAlign: "center" }}>
          <Text size={300} style={{ color: colors.textTertiary }}>No claims to display.</Text>
        </div>
      ) : (
        <div className={styles.grid}>
          {claims.map(claim => (
            <ClaimCard key={claim.id} claim={claim} colors={colors} styles={styles} onClick={() => openDetail(claim)} />
          ))}
        </div>
      )}
    </div>
  );
}

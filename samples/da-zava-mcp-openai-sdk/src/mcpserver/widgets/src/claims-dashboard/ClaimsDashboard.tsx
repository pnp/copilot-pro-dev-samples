import React, { useState, useCallback, useMemo } from "react";
import {
  makeStyles,
  Text,
  Card,
  CardHeader,
  Button,
  Divider,
  Accordion,
  AccordionItem,
  AccordionHeader,
  AccordionPanel,
  Tab,
  TabList,
  tokens,
  Image,
  Select,
  Textarea,
} from "@fluentui/react-components";
import {
  TaskListLtrRegular,
  CheckmarkCircleRegular,
  DismissCircleRegular,
  ClockRegular,
  AlertRegular,
  DocumentRegular,
  ReceiptMoneyRegular,
  ArrowMaximizeRegular,
  ArrowMinimizeRegular,
  ArrowLeftRegular,
  FilterRegular,
  PersonRegular,
  LocationRegular,
  CalendarRegular,
  SearchRegular,
  BoxRegular,
  WrenchRegular,
  ImageRegular,
  EditRegular,
  SaveRegular,
  DismissRegular,
  NoteRegular,
  ShieldCheckmarkRegular,
} from "@fluentui/react-icons";
import { useOpenAiGlobal } from "../hooks/useOpenAiGlobal";
import { useThemeColors } from "../hooks/useThemeColors";
import { FakeMap } from "./FakeMap";
import type {
  ClaimsDashboardData,
  Claim,
  Inspection,
  PurchaseOrder,
} from "../types";

/* ─── Styles ─────────────────────────────────────────────────────────── */
const useStyles = makeStyles({
  root: { fontFamily: tokens.fontFamilyBase, width: "100%", overflow: "auto" },

  /* Grid view — header area */
  header: {
    display: "flex", alignItems: "center", gap: "16px",
    padding: "24px 24px 0",
  },
  headerIcon: {
    display: "flex", alignItems: "center", justifyContent: "center",
    width: "48px", height: "48px", borderRadius: "14px", flexShrink: 0,
  },

  /* Metrics bar */
  metricsBar: {
    display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
    gap: "12px", padding: "16px 24px 0",
  },
  metricCard: {
    display: "flex", flexDirection: "column" as const, gap: "2px",
    padding: "14px 16px", borderRadius: "12px",
  },

  /* Toolbar & Filter */
  toolbar: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    gap: "12px", padding: "16px 24px 4px", flexWrap: "wrap" as const,
  },
  filterRow: { display: "flex", alignItems: "center", gap: "6px" },
  filterChip: {
    padding: "5px 14px", borderRadius: "20px", border: "1px solid",
    fontSize: "12px", fontWeight: 500, cursor: "pointer",
    transition: "all 0.15s ease",
    whiteSpace: "nowrap" as const, fontFamily: tokens.fontFamilyBase,
    letterSpacing: "0.01em",
  },

  /* Claims grid */
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

  /* Detail view */
  detail: { padding: "20px", fontFamily: tokens.fontFamilyBase },
  detailHeader: {
    display: "flex", justifyContent: "space-between", alignItems: "flex-start",
    marginBottom: "20px",
  },
  section: { marginBottom: "16px" },
  sectionHeader: {
    display: "flex", alignItems: "center", gap: "8px",
    marginBottom: "10px",
  },
  overviewLayout: {
    display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px",
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
  poCard: { padding: "14px", borderRadius: "10px", marginBottom: "10px" },
  row: { display: "flex", justifyContent: "space-between", alignItems: "center" },
  lineItemsTable: { width: "100%", borderCollapse: "collapse" as const, marginTop: "10px" },
  photoGrid: { display: "flex", gap: "8px", flexWrap: "wrap" as const, marginTop: "8px" },

  /* Edit areas */
  editBar: {
    display: "flex", gap: "8px", alignItems: "center",
    padding: "14px 16px", borderRadius: "10px", marginBottom: "16px",
  },
  editField: { marginBottom: "12px" },
  fieldLabel: { display: "block", marginBottom: "4px" },
  saveRow: { display: "flex", gap: "8px", marginTop: "8px" },
});

/* ─── Helpers ────────────────────────────────────────────────────────── */
function statusColor(s: string): "success" | "warning" | "danger" | "informative" | "important" {
  const l = s.toLowerCase();
  if (l.includes("approved") || l.includes("completed")) return "success";
  if (l.includes("pending") || l.includes("scheduled")) return "warning";
  if (l.includes("denied") || l.includes("rejected") || l.includes("cancelled")) return "danger";
  if (l.includes("closed")) return "informative";
  return "important";
}

/** Returns { bg, fg } for a status string using theme-aware colors */
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

/** Derive a priority label from claim data (no priority field on Claim type) */
function derivePriority(claim: Claim): string {
  if (claim.estimatedLoss >= 50000) return "high";
  if (claim.estimatedLoss >= 15000) return "medium";
  return "low";
}

/** Reusable pill capsule that never overflows — replaces Badge for status text */
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
      backgroundColor: bg,
      color: fg,
      border: `1px solid ${fg}30`,
      fontSize: isSmall ? "11px" : "12px",
      fontWeight: 600,
      lineHeight: "1.3",
      whiteSpace: "nowrap",
      overflow: "hidden",
      textOverflow: "ellipsis",
      maxWidth: "100%",
      flexShrink: 0,
    }}>
      {icon && <span style={{ display: "inline-flex", fontSize: isSmall ? "12px" : "14px", flexShrink: 0 }}>{icon}</span>}
      {label}
    </span>
  );
}

/* ─── Toast ──────────────────────────────────────────────────────────── */
function Toast({ message, type, onDismiss, colors }: { message: string; type: "success" | "error"; onDismiss: () => void; colors: ReturnType<typeof useThemeColors> }) {
  const bg = type === "success" ? colors.successSubtle : colors.errorSubtle;
  const fg = type === "success" ? colors.success : colors.error;
  return (
    <div style={{
      padding: "12px 16px", borderRadius: "10px", marginBottom: "14px",
      display: "flex", alignItems: "center", gap: "10px",
      backgroundColor: bg, border: `1px solid ${fg}22`, color: fg,
      boxShadow: colors.shadowCard,
    }}>
      {type === "success" ? <CheckmarkCircleRegular /> : <AlertRegular />}
      <Text size={200} style={{ flex: 1, color: fg }}>{message}</Text>
      <button onClick={onDismiss} style={{ background: "none", border: "none", cursor: "pointer", color: fg, padding: "2px" }}>
        <DismissRegular style={{ fontSize: "14px" }} />
      </button>
    </div>
  );
}

/* ─── Constants ──────────────────────────────────────────────────────── */
const CLAIM_STATUSES = [
  "Open - Under Investigation", "Open - Pending Documentation",
  "Pending - Awaiting Inspection", "Pending - Under Review",
  "Approved - In Progress", "Approved - Repair Scheduled", "Approved - Payment Pending",
  "Denied", "Closed - Resolved", "Closed - Withdrawn",
];
const INSPECTION_STATUSES = ["scheduled", "in-progress", "completed", "cancelled"];
const PO_STATUSES = ["draft", "submitted", "approved", "in-progress", "completed", "rejected"];
const STATUS_FILTERS = ["All", "Open", "Pending", "Approved", "Denied", "Closed"] as const;

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
      {/* Priority accent bar */}
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
   MAIN COMPONENT — Client-side master-detail (no callTool navigation)
   ═════════════════════════════════════════════════════════════════════ */
export function ClaimsDashboard() {
  const styles = useStyles();
  const colors = useThemeColors();
  const data = useOpenAiGlobal("toolOutput") as ClaimsDashboardData | null;

  const claims = data?.claims ?? [];
  const allInspections = data?.inspections ?? [];
  const allPurchaseOrders = data?.purchaseOrders ?? [];
  const allContractors = data?.contractors ?? {};
  const allInspectors = data?.inspectors ?? {};

  /* ── View state ────────────────────────────────────────────────────── */
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<string>("All");
  const [nameFilter, setNameFilter] = useState<string>("");

  /* ── Detail tab & edit state ───────────────────────────────────────── */
  const [activeTab, setActiveTab] = useState("overview");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [editingClaim, setEditingClaim] = useState(false);
  const [claimStatus, setClaimStatus] = useState("");
  const [claimNote, setClaimNote] = useState("");
  const [savingClaim, setSavingClaim] = useState(false);
  const [editingInspection, setEditingInspection] = useState<string | null>(null);
  const [inspStatus, setInspStatus] = useState("");
  const [inspFindings, setInspFindings] = useState("");
  const [inspActions, setInspActions] = useState("");
  const [savingInspection, setSavingInspection] = useState(false);
  const [editingPO, setEditingPO] = useState<string | null>(null);
  const [poStatus, setPOStatus] = useState("");
  const [poNote, setPONote] = useState("");
  const [savingPO, setSavingPO] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const showToast = (msg: string, type: "success" | "error") => {
    setToast({ message: msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  /* ── Derived data ──────────────────────────────────────────────────── */
  const filteredClaims = useMemo(() => {
    let result = claims;
    if (activeFilter !== "All") {
      result = result.filter(c => c.status.toLowerCase().includes(activeFilter.toLowerCase()));
    }
    if (nameFilter.trim()) {
      const q = nameFilter.trim().toLowerCase();
      result = result.filter(c => c.policyHolderName.toLowerCase().includes(q));
    }
    return result;
  }, [claims, activeFilter, nameFilter]);

  const metrics = useMemo(() => ({
    total: claims.length,
    totalLoss: claims.reduce((s, c) => s + c.estimatedLoss, 0),
    open: claims.filter(c => c.status.toLowerCase().includes("open")).length,
    approved: claims.filter(c => c.status.toLowerCase().includes("approved")).length,
    pending: claims.filter(c => c.status.toLowerCase().includes("pending")).length,
  }), [claims]);

  const selectedClaim = useMemo(() =>
    claims.find(c => c.id === selectedClaimId) ?? null,
  [claims, selectedClaimId]);

  const claimInspections = useMemo(() =>
    selectedClaimId ? allInspections.filter(i => i.claimId === selectedClaimId) : [],
  [allInspections, selectedClaimId]);

  const claimPOs = useMemo(() =>
    selectedClaimId ? allPurchaseOrders.filter(po => po.claimId === selectedClaimId) : [],
  [allPurchaseOrders, selectedClaimId]);

  /* ── Navigation ────────────────────────────────────────────────────── */
  const openDetail = useCallback((claim: Claim) => {
    setSelectedClaimId(claim.id);
    setActiveTab("overview");
    setEditingClaim(false);
    setEditingInspection(null);
    setEditingPO(null);
  }, []);

  const goBack = useCallback(() => {
    setSelectedClaimId(null);
    setEditingClaim(false);
    setEditingInspection(null);
    setEditingPO(null);
  }, []);

  const toggleFullscreen = useCallback(async () => {
    if (window.openai?.requestDisplayMode) {
      const cur = window.openai.displayMode;
      await window.openai.requestDisplayMode({ mode: cur === "fullscreen" ? "inline" : "fullscreen" });
      setIsFullscreen(p => !p);
      return;
    }
    try {
      if (!document.fullscreenElement) await document.documentElement.requestFullscreen();
      else await document.exitFullscreen();
    } catch {}
    setIsFullscreen(p => !p);
  }, []);

  /* ── Save handlers ─────────────────────────────────────────────────── */
  const handleSaveClaim = useCallback(async () => {
    if (!window.openai?.callTool || !selectedClaim) return;
    setSavingClaim(true);
    try {
      const a: Record<string, unknown> = { claimId: selectedClaim.id, status: claimStatus };
      if (claimNote.trim()) a.note = claimNote.trim();
      await window.openai.callTool("update-claim-status", a);
      showToast(`Claim updated to "${claimStatus}"`, "success");
      setEditingClaim(false);
      setClaimNote("");
    } catch (e) {
      showToast(`Failed: ${e instanceof Error ? e.message : "Unknown error"}`, "error");
    } finally { setSavingClaim(false); }
  }, [selectedClaim, claimStatus, claimNote]);

  const handleSaveInspection = useCallback(async (inspId: string) => {
    if (!window.openai?.callTool) return;
    setSavingInspection(true);
    try {
      const a: Record<string, unknown> = { inspectionId: inspId };
      if (inspStatus) a.status = inspStatus;
      if (inspFindings.trim()) a.findings = inspFindings.trim();
      if (inspActions.trim()) a.recommendedActions = inspActions.split("\n").map(s => s.trim()).filter(Boolean);
      await window.openai.callTool("update-inspection", a);
      showToast(`Inspection ${inspId} updated`, "success");
      setEditingInspection(null);
    } catch (e) {
      showToast(`Failed: ${e instanceof Error ? e.message : "Unknown error"}`, "error");
    } finally { setSavingInspection(false); }
  }, [inspStatus, inspFindings, inspActions]);

  const handleSavePO = useCallback(async (poId: string) => {
    if (!window.openai?.callTool) return;
    setSavingPO(true);
    try {
      const a: Record<string, unknown> = { purchaseOrderId: poId, status: poStatus };
      if (poNote.trim()) a.note = poNote.trim();
      await window.openai.callTool("update-purchase-order", a);
      showToast(`PO updated to "${poStatus}"`, "success");
      setEditingPO(null);
      setPONote("");
    } catch (e) {
      showToast(`Failed: ${e instanceof Error ? e.message : "Unknown error"}`, "error");
    } finally { setSavingPO(false); }
  }, [poStatus, poNote]);

  /* ── Edit-mode launchers ───────────────────────────────────────────── */
  const startEditClaim = useCallback(() => {
    if (!selectedClaim) return;
    setClaimStatus(selectedClaim.status);
    setClaimNote("");
    setEditingClaim(true);
  }, [selectedClaim]);

  const startEditInspection = useCallback((insp: Inspection) => {
    setInspStatus(insp.status);
    setInspFindings(insp.findings || "");
    setInspActions((insp.recommendedActions || []).join("\n"));
    setEditingInspection(insp.id);
  }, []);

  const startEditPO = useCallback((po: PurchaseOrder) => {
    setPOStatus(po.status);
    setPONote("");
    setEditingPO(po.id);
  }, []);

  /* ═══════════════════════════════════════════════════════════════════
     DETAIL VIEW
     ═══════════════════════════════════════════════════════════════════ */
  if (selectedClaim) {
    const claim = selectedClaim;
    const inspections = claimInspections;
    const purchaseOrders = claimPOs;

    return (
      <div className={styles.detail} style={{ backgroundColor: colors.background, color: colors.text }}>
        {toast && <Toast message={toast.message} type={toast.type} onDismiss={() => setToast(null)} colors={colors} />}

        {/* ── Detail header ────────────────────────────────────────── */}
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
          <div style={{ display: "flex", gap: "6px" }}>
            {!editingClaim && (
              <Button icon={<EditRegular />} appearance="subtle" onClick={startEditClaim} title="Edit claim" size="small"
                style={{ borderRadius: "10px" }} />
            )}
            <Button icon={isFullscreen ? <ArrowMinimizeRegular /> : <ArrowMaximizeRegular />} appearance="subtle" onClick={toggleFullscreen}
              style={{ borderRadius: "10px" }} />
          </div>
        </div>

        {/* ── Tabs ─────────────────────────────────────────────────── */}
        <div style={{
          borderBottom: `1px solid ${colors.borderSubtle}`,
          marginBottom: "20px",
        }}>
          <TabList selectedValue={activeTab} onTabSelect={(_, d) => setActiveTab(d.value as string)}>
            <Tab value="overview" icon={<DocumentRegular />}>Overview</Tab>
            <Tab value="inspections" icon={<SearchRegular />}>Inspections ({inspections.length})</Tab>
            <Tab value="purchase-orders" icon={<BoxRegular />}>Purchase Orders ({purchaseOrders.length})</Tab>
          </TabList>
        </div>

        {/* ── Overview ─────────────────────────────────────────────── */}
        {activeTab === "overview" && (
          <>
            {editingClaim && (
              <div className={styles.editBar} style={{ backgroundColor: colors.primarySubtle, border: `1px solid ${colors.primary}30` }}>
                <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "10px" }}>
                  <div>
                    <Text size={200} weight="semibold" className={styles.fieldLabel}>Status</Text>
                    <Select value={claimStatus} onChange={(_, d) => setClaimStatus(d.value)} style={{ width: "100%" }}>
                      {CLAIM_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                    </Select>
                  </div>
                  <div>
                    <Text size={200} weight="semibold" className={styles.fieldLabel}>Add Note (optional)</Text>
                    <Textarea value={claimNote} onChange={(_, d) => setClaimNote(d.value)} placeholder="Add a note…" resize="vertical" style={{ width: "100%" }} />
                  </div>
                  <div className={styles.saveRow}>
                    <Button appearance="primary" icon={<SaveRegular />} onClick={handleSaveClaim} disabled={savingClaim} size="small"
                      style={{ borderRadius: "8px" }}>
                      {savingClaim ? "Saving…" : "Save Changes"}
                    </Button>
                    <Button appearance="subtle" icon={<DismissRegular />} onClick={() => setEditingClaim(false)} size="small"
                      style={{ borderRadius: "8px" }}>Cancel</Button>
                  </div>
                </div>
              </div>
            )}

            <div className={styles.overviewLayout}>
              {/* LEFT COLUMN — info cards */}
              <div>
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

                {/* Quick stats under map */}
                <div style={{
                  display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px",
                  marginTop: "12px",
                }}>
                  <div style={{
                    textAlign: "center", padding: "10px 8px", borderRadius: "10px",
                    backgroundColor: colors.primarySubtle, border: `1px solid ${colors.primary}20`,
                  }}>
                    <Text size={400} weight="bold" block style={{ color: colors.primary }}>{inspections.length}</Text>
                    <Text size={100} style={{ color: colors.textTertiary }}>Inspections</Text>
                  </div>
                  <div style={{
                    textAlign: "center", padding: "10px 8px", borderRadius: "10px",
                    backgroundColor: colors.warningSubtle, border: `1px solid ${colors.warning}20`,
                  }}>
                    <Text size={400} weight="bold" block style={{ color: colors.warning }}>{purchaseOrders.length}</Text>
                    <Text size={100} style={{ color: colors.textTertiary }}>Purchase Orders</Text>
                  </div>
                  <div style={{
                    textAlign: "center", padding: "10px 8px", borderRadius: "10px",
                    backgroundColor: colors.successSubtle, border: `1px solid ${colors.success}20`,
                  }}>
                    <Text size={400} weight="bold" block style={{ color: colors.success }}>{claim.damageTypes.length}</Text>
                    <Text size={100} style={{ color: colors.textTertiary }}>Damage Types</Text>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* ── Inspections ──────────────────────────────────────────── */}
        {activeTab === "inspections" && (
          <div className={styles.section}>
            {inspections.length === 0 ? (
              <Text style={{ color: colors.textSecondary }}>No inspections recorded.</Text>
            ) : (
              <Accordion multiple collapsible>
                {inspections.map(insp => {
                  const inspector = allInspectors[insp.inspectorId];
                  const isEditing = editingInspection === insp.id;
                  return (
                    <AccordionItem key={insp.id} value={insp.id}>
                      <AccordionHeader>
                        <div style={{ display: "flex", gap: "8px", alignItems: "center", width: "100%" }}>
                          {insp.status === "completed"
                            ? <CheckmarkCircleRegular style={{ color: colors.success }} />
                            : <ClockRegular style={{ color: colors.warning }} />}
                          <Text weight="semibold">{insp.id}</Text>
                          <span style={{
                            display: "inline-flex", padding: "2px 8px", borderRadius: "999px",
                            fontSize: "11px", fontWeight: 500, whiteSpace: "nowrap",
                            backgroundColor: colors.surfaceHover, color: colors.textSecondary,
                            border: `1px solid ${colors.borderSubtle}`,
                          }}>{insp.taskType}</span>
                          <span style={{
                            display: "inline-flex", padding: "2px 8px", borderRadius: "999px",
                            fontSize: "11px", fontWeight: 600, whiteSpace: "nowrap",
                            backgroundColor: priorityColor(insp.priority) + "18",
                            color: priorityColor(insp.priority),
                            border: `1px solid ${priorityColor(insp.priority)}40`,
                          }}>{insp.priority}</span>
                          <StatusPill label={insp.status} status={insp.status} size="small" colors={colors} />
                        </div>
                      </AccordionHeader>
                      <AccordionPanel>
                        <div style={{ padding: "8px 0" }}>
                          <Text size={200} style={{ color: colors.textSecondary }} block>
                            Scheduled: {new Date(insp.scheduledDate).toLocaleDateString()}
                            {insp.completedDate && ` · Completed: ${new Date(insp.completedDate).toLocaleDateString()}`}
                          </Text>
                          {inspector && <Text size={200} block style={{ marginTop: "4px" }}>Inspector: {inspector.name} ({inspector.email})</Text>}
                          <Text size={200} block style={{ marginTop: "4px" }}>Property: {insp.property}</Text>

                          {isEditing ? (
                            <div style={{ marginTop: "12px", padding: "12px", backgroundColor: colors.surface, borderRadius: "8px", border: `1px solid ${colors.border}` }}>
                              <div className={styles.editField}>
                                <Text size={200} weight="semibold" className={styles.fieldLabel}>Status</Text>
                                <Select value={inspStatus} onChange={(_, d) => setInspStatus(d.value)} style={{ width: "100%" }}>
                                  {INSPECTION_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                                </Select>
                              </div>
                              <div className={styles.editField}>
                                <Text size={200} weight="semibold" className={styles.fieldLabel}>Findings</Text>
                                <Textarea value={inspFindings} onChange={(_, d) => setInspFindings(d.value)} placeholder="Enter findings…" resize="vertical" style={{ width: "100%" }} />
                              </div>
                              <div className={styles.editField}>
                                <Text size={200} weight="semibold" className={styles.fieldLabel}>Recommended Actions (one per line)</Text>
                                <Textarea value={inspActions} onChange={(_, d) => setInspActions(d.value)} placeholder="One action per line…" resize="vertical" style={{ width: "100%" }} />
                              </div>
                              <div className={styles.saveRow}>
                                <Button appearance="primary" icon={<SaveRegular />} onClick={() => handleSaveInspection(insp.id)} disabled={savingInspection} size="small">
                                  {savingInspection ? "Saving…" : "Save"}
                                </Button>
                                <Button appearance="subtle" icon={<DismissRegular />} onClick={() => setEditingInspection(null)} size="small">Cancel</Button>
                              </div>
                            </div>
                          ) : (
                            <>
                              {insp.findings && (
                                <div style={{ marginTop: "8px", padding: "8px", backgroundColor: colors.surface, borderRadius: "4px" }}>
                                  <Text size={200} weight="semibold" block>Findings</Text>
                                  <Text size={200}>{insp.findings}</Text>
                                </div>
                              )}
                              {insp.recommendedActions.length > 0 && (
                                <div style={{ marginTop: "8px" }}>
                                  <Text size={200} weight="semibold" block>Recommended Actions</Text>
                                  {insp.recommendedActions.map((a, i) => <Text key={i} size={200} block>• {a}</Text>)}
                                </div>
                              )}
                              {insp.flaggedIssues.length > 0 && (
                                <div style={{ marginTop: "8px" }}>
                                  <Text size={200} weight="semibold" block style={{ color: colors.error }}><AlertRegular /> Flagged Issues</Text>
                                  {insp.flaggedIssues.map((issue, i) => <Text key={i} size={200} block style={{ color: colors.error }}>• {issue}</Text>)}
                                </div>
                              )}
                              {insp.photos.length > 0 && (
                                <div style={{ marginTop: "8px" }}>
                                  <Text size={200} weight="semibold" block><ImageRegular /> Photos</Text>
                                  <div className={styles.photoGrid}>
                                    {insp.photos.map((p, i) => (
                                      <Image key={i} src={p} alt={`Photo ${i + 1}`} width={120} height={90} fit="cover" style={{ borderRadius: "4px", border: `1px solid ${colors.border}` }} />
                                    ))}
                                  </div>
                                </div>
                              )}
                              <Button icon={<EditRegular />} appearance="subtle" size="small" onClick={() => startEditInspection(insp)} style={{ marginTop: "8px" }}>
                                Edit Inspection
                              </Button>
                            </>
                          )}
                        </div>
                      </AccordionPanel>
                    </AccordionItem>
                  );
                })}
              </Accordion>
            )}
          </div>
        )}

        {/* ── Purchase Orders ──────────────────────────────────────── */}
        {activeTab === "purchase-orders" && (
          <div className={styles.section}>
            {purchaseOrders.length === 0 ? (
              <Text style={{ color: colors.textSecondary }}>No purchase orders recorded.</Text>
            ) : (
              purchaseOrders.map(po => {
                const contractor = allContractors[po.contractorId];
                const isEditing = editingPO === po.id;
                return (
                  <Card key={po.id} className={styles.poCard} style={{ backgroundColor: colors.surface }}>
                    <CardHeader
                      header={
                        <div className={styles.row} style={{ width: "100%" }}>
                          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                            <BoxRegular style={{ color: colors.primary }} />
                            <Text weight="semibold">{po.poNumber}</Text>
                            <StatusPill label={po.status} status={po.status} size="small" colors={colors} />
                          </div>
                          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <Text weight="bold" style={{ color: colors.primary }}>${po.total.toLocaleString()}</Text>
                            {!isEditing && <Button icon={<EditRegular />} appearance="subtle" size="small" onClick={() => startEditPO(po)} title="Edit PO" />}
                          </div>
                        </div>
                      }
                      description={<Text size={200} style={{ color: colors.textSecondary }}>{po.workDescription}</Text>}
                    />

                    {isEditing && (
                      <div style={{ marginTop: "10px", padding: "12px", borderRadius: "8px", border: `1px solid ${colors.border}`, backgroundColor: colors.background }}>
                        <div className={styles.editField}>
                          <Text size={200} weight="semibold" className={styles.fieldLabel}>Status</Text>
                          <Select value={poStatus} onChange={(_, d) => setPOStatus(d.value)} style={{ width: "100%" }}>
                            {PO_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                          </Select>
                        </div>
                        <div className={styles.editField}>
                          <Text size={200} weight="semibold" className={styles.fieldLabel}>Add Note (optional)</Text>
                          <Textarea value={poNote} onChange={(_, d) => setPONote(d.value)} placeholder="Add a note…" resize="vertical" style={{ width: "100%" }} />
                        </div>
                        <div className={styles.saveRow}>
                          <Button appearance="primary" icon={<SaveRegular />} onClick={() => handleSavePO(po.id)} disabled={savingPO} size="small">
                            {savingPO ? "Saving…" : "Save"}
                          </Button>
                          <Button appearance="subtle" icon={<DismissRegular />} onClick={() => setEditingPO(null)} size="small">Cancel</Button>
                        </div>
                      </div>
                    )}

                    {contractor && (
                      <div style={{ marginTop: "8px", display: "flex", alignItems: "center", gap: "8px" }}>
                        <WrenchRegular style={{ color: colors.primary }} />
                        <Text size={200}>Contractor: <strong>{contractor.name}</strong> — {contractor.businessName}</Text>
                        {contractor.isPreferred && <span style={{
                          display: "inline-flex", padding: "2px 8px", borderRadius: "999px",
                          fontSize: "11px", fontWeight: 600, whiteSpace: "nowrap",
                          backgroundColor: colors.successSubtle, color: colors.success,
                          border: `1px solid ${colors.success}30`,
                        }}>Preferred</span>}
                      </div>
                    )}

                    {Array.isArray(po.lineItems) && po.lineItems.length > 0 && (
                      <table className={styles.lineItemsTable} style={{ marginTop: "8px" }}>
                        <thead>
                          <tr style={{ borderBottom: `1px solid ${colors.border}` }}>
                            <th style={{ textAlign: "left", padding: "4px 8px", fontSize: "12px", color: colors.textSecondary }}>Description</th>
                            <th style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px", color: colors.textSecondary }}>Qty</th>
                            <th style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px", color: colors.textSecondary }}>Unit Price</th>
                            <th style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px", color: colors.textSecondary }}>Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {po.lineItems.map(li => (
                            <tr key={li.id} style={{ borderBottom: `1px solid ${colors.border}` }}>
                              <td style={{ padding: "4px 8px", fontSize: "12px" }}>{li.description}</td>
                              <td style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px" }}>{li.quantity}</td>
                              <td style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px" }}>${li.unitPrice}</td>
                              <td style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px" }}>${li.totalPrice.toLocaleString()}</td>
                            </tr>
                          ))}
                        </tbody>
                        <tfoot>
                          <tr><td colSpan={3} style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px" }}>Subtotal:</td><td style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px", fontWeight: "bold" }}>${po.subtotal.toLocaleString()}</td></tr>
                          <tr><td colSpan={3} style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px" }}>Tax:</td><td style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px" }}>${po.tax.toLocaleString()}</td></tr>
                          <tr><td colSpan={3} style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px", fontWeight: "bold" }}>Total:</td><td style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px", fontWeight: "bold", color: colors.primary }}>${po.total.toLocaleString()}</td></tr>
                        </tfoot>
                      </table>
                    )}

                    {po.notes && po.notes.length > 0 && (
                      <div style={{ marginTop: "8px" }}>
                        <Text size={200} weight="semibold" block>Notes</Text>
                        {po.notes.map((n, i) => <Text key={i} size={200} block style={{ color: colors.textSecondary }}>• {n}</Text>)}
                      </div>
                    )}
                  </Card>
                );
              })
            )}
          </div>
        )}
      </div>
    );
  }

  /* ═══════════════════════════════════════════════════════════════════
     GRID VIEW (default)
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
            Zava Insurance &middot; {claims.length} claims &middot; ${metrics.totalLoss.toLocaleString()} total exposure
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

      {/* Metrics Bar */}
      <div className={styles.metricsBar}>
        {[
          {
            label: "Total Claims", value: metrics.total,
            icon: <TaskListLtrRegular style={{ fontSize: "18px" }} />,
            color: colors.primary, bg: colors.primarySubtle, border: colors.primary,
          },
          {
            label: "Open", value: metrics.open,
            icon: <AlertRegular style={{ fontSize: "18px" }} />,
            color: colors.error, bg: colors.errorSubtle, border: colors.error,
          },
          {
            label: "Pending", value: metrics.pending,
            icon: <ClockRegular style={{ fontSize: "18px" }} />,
            color: colors.warning, bg: colors.warningSubtle, border: colors.warning,
          },
          {
            label: "Approved", value: metrics.approved,
            icon: <CheckmarkCircleRegular style={{ fontSize: "18px" }} />,
            color: colors.success, bg: colors.successSubtle, border: colors.success,
          },
        ].map(m => (
          <div key={m.label} className={styles.metricCard} style={{
            backgroundColor: m.bg,
            border: `1px solid ${m.border}20`,
            borderLeft: `3px solid ${m.color}`,
          }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <Text size={200} style={{ color: colors.textTertiary, fontWeight: 500, textTransform: "uppercase" as const, letterSpacing: "0.05em", fontSize: "10px" }}>{m.label}</Text>
              <span style={{ color: m.color, opacity: 0.6 }}>{m.icon}</span>
            </div>
            <Text size={600} weight="bold" style={{ color: m.color }}>{m.value}</Text>
          </div>
        ))}
      </div>

      {/* Toolbar — Filter */}
      <div className={styles.toolbar}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <Text size={300} weight="semibold" style={{ color: colors.textSecondary }}>
            {filteredClaims.length} {activeFilter === "All" ? "claims" : `"${activeFilter}" claims`}
          </Text>
          <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
            <PersonRegular style={{ position: "absolute", left: "10px", fontSize: "14px", color: colors.textTertiary, pointerEvents: "none" }} />
            <input
              type="text"
              placeholder="Filter by policy holder name…"
              value={nameFilter}
              onChange={e => setNameFilter(e.target.value)}
              style={{
                padding: "6px 10px 6px 30px",
                borderRadius: "20px",
                border: `1px solid ${colors.borderSubtle}`,
                fontSize: "12px",
                fontFamily: tokens.fontFamilyBase,
                backgroundColor: colors.surface,
                color: colors.text,
                outline: "none",
                width: "220px",
                transition: "border-color 0.15s ease",
              }}
              onFocus={e => e.currentTarget.style.borderColor = colors.primary}
              onBlur={e => e.currentTarget.style.borderColor = colors.borderSubtle}
            />
            {nameFilter && (
              <button
                onClick={() => setNameFilter("")}
                style={{
                  position: "absolute", right: "8px",
                  background: "none", border: "none", cursor: "pointer",
                  color: colors.textTertiary, padding: "2px", display: "flex",
                  alignItems: "center",
                }}
                title="Clear filter"
              >
                <DismissRegular style={{ fontSize: "12px" }} />
              </button>
            )}
          </div>
        </div>
        <div className={styles.filterRow}>
          <FilterRegular style={{ fontSize: "14px", color: colors.textTertiary }} />
          {STATUS_FILTERS.map(f => {
            const isActive = activeFilter === f;
            return (
              <button key={f} className={styles.filterChip} style={{
                backgroundColor: isActive ? colors.primary : "transparent",
                color: isActive ? colors.primaryText : colors.textSecondary,
                borderColor: isActive ? colors.primary : colors.borderSubtle,
                boxShadow: isActive ? `0 0 0 2px ${colors.primary}30` : "none",
              }} onClick={() => setActiveFilter(f)}>
                {f}
              </button>
            );
          })}
        </div>
      </div>

      {/* Grid */}
      {filteredClaims.length === 0 ? (
        <div style={{ padding: "48px 24px", textAlign: "center" }}>
          <Text size={300} style={{ color: colors.textTertiary }}>No claims match the &ldquo;{activeFilter}&rdquo; filter.</Text>
        </div>
      ) : (
        <div className={styles.grid}>
          {filteredClaims.map(claim => (
            <ClaimCard key={claim.id} claim={claim} colors={colors} styles={styles} onClick={() => openDetail(claim)} />
          ))}
        </div>
      )}
    </div>
  );
}

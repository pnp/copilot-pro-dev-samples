import React, { useState, useCallback } from "react";
import {
  makeStyles,
  Text,
  Badge,
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
  Input,
  Textarea,
} from "@fluentui/react-components";
import {
  ArrowMaximizeRegular,
  ArrowMinimizeRegular,
  ArrowLeftRegular,
  PersonRegular,
  LocationRegular,
  CalendarRegular,
  ReceiptMoneyRegular,
  DocumentRegular,
  SearchRegular,
  BoxRegular,
  WrenchRegular,
  CheckmarkCircleRegular,
  ClockRegular,
  AlertRegular,
  ImageRegular,
  EditRegular,
  SaveRegular,
  DismissRegular,
  NoteRegular,
  AddRegular,
} from "@fluentui/react-icons";
import { useOpenAiGlobal } from "../hooks/useOpenAiGlobal";
import { useThemeColors } from "../hooks/useThemeColors";
import type { ClaimDetailData, Claim, Inspection, PurchaseOrder } from "../types";

const useStyles = makeStyles({
  container: { padding: "16px", fontFamily: tokens.fontFamilyBase },
  header: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" },
  section: { marginBottom: "16px" },
  infoGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "16px" },
  infoItem: { display: "flex", alignItems: "center", gap: "8px" },
  card: { padding: "12px", borderRadius: "8px", marginBottom: "8px" },
  row: { display: "flex", justifyContent: "space-between", alignItems: "center" },
  tags: { display: "flex", gap: "4px", flexWrap: "wrap" as const, marginTop: "4px" },
  lineItemsTable: { width: "100%", borderCollapse: "collapse" as const, marginTop: "8px" },
  photoGrid: { display: "flex", gap: "8px", flexWrap: "wrap" as const, marginTop: "8px" },
  editBar: {
    display: "flex",
    gap: "8px",
    alignItems: "center",
    padding: "10px 12px",
    borderRadius: "8px",
    marginBottom: "12px",
  },
  editField: { marginBottom: "12px" },
  fieldLabel: { display: "block", marginBottom: "4px" },
  saveRow: { display: "flex", gap: "8px", marginTop: "8px" },
  toast: {
    padding: "10px 16px",
    borderRadius: "8px",
    marginBottom: "12px",
    display: "flex",
    alignItems: "center",
    gap: "8px",
    animation: "fadeIn 0.2s ease-out",
  },
});

/* ── Status Helpers ──────────────────────────────────────────────────── */
const CLAIM_STATUSES = [
  "Open - Under Investigation",
  "Open - Pending Documentation",
  "Pending - Awaiting Inspection",
  "Pending - Under Review",
  "Approved - In Progress",
  "Approved - Repair Scheduled",
  "Approved - Payment Pending",
  "Denied",
  "Closed - Resolved",
  "Closed - Withdrawn",
];

const INSPECTION_STATUSES = ["scheduled", "in-progress", "completed", "cancelled"];

const PO_STATUSES = ["draft", "submitted", "approved", "in-progress", "completed", "rejected"];

function statusBadgeColor(status: string): "success" | "warning" | "danger" | "informative" | "important" {
  const lower = status.toLowerCase();
  if (lower.includes("completed") || lower.includes("approved")) return "success";
  if (lower.includes("pending") || lower.includes("scheduled")) return "warning";
  if (lower.includes("cancelled") || lower.includes("rejected") || lower.includes("denied")) return "danger";
  if (lower.includes("closed")) return "informative";
  return "important";
}

function priorityColor(priority: string): string {
  switch (priority.toLowerCase()) {
    case "high": case "urgent": return "#d13438";
    case "medium": return "#ffb900";
    case "low": return "#107c10";
    default: return "#616161";
  }
}

/* ── Toast component ─────────────────────────────────────────────────── */
function Toast({ message, type, onDismiss }: { message: string; type: "success" | "error"; onDismiss: () => void }) {
  const colors = type === "success"
    ? { bg: "#dff6dd", text: "#107c10", border: "#107c10" }
    : { bg: "#fde7e9", text: "#d13438", border: "#d13438" };

  return (
    <div style={{ padding: "10px 16px", borderRadius: "8px", marginBottom: "12px", display: "flex", alignItems: "center", gap: "8px", backgroundColor: colors.bg, border: `1px solid ${colors.border}`, color: colors.text }}>
      {type === "success" ? <CheckmarkCircleRegular /> : <AlertRegular />}
      <Text size={200} style={{ flex: 1 }}>{message}</Text>
      <button onClick={onDismiss} style={{ background: "none", border: "none", cursor: "pointer", color: colors.text, padding: "2px" }}>
        <DismissRegular style={{ fontSize: "14px" }} />
      </button>
    </div>
  );
}

/* ── Main Component ──────────────────────────────────────────────────── */
export function ClaimDetail() {
  const styles = useStyles();
  const colors = useThemeColors();
  const data = useOpenAiGlobal("toolOutput") as ClaimDetailData | null;

  const [activeTab, setActiveTab] = useState("overview");
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Edit states for claim
  const [editingClaim, setEditingClaim] = useState(false);
  const [claimStatus, setClaimStatus] = useState("");
  const [claimNote, setClaimNote] = useState("");
  const [savingClaim, setSavingClaim] = useState(false);

  // Edit states for inspections
  const [editingInspection, setEditingInspection] = useState<string | null>(null);
  const [inspStatus, setInspStatus] = useState("");
  const [inspFindings, setInspFindings] = useState("");
  const [inspActions, setInspActions] = useState("");
  const [savingInspection, setSavingInspection] = useState(false);

  // Edit states for POs
  const [editingPO, setEditingPO] = useState<string | null>(null);
  const [poStatus, setPOStatus] = useState("");
  const [poNote, setPONote] = useState("");
  const [savingPO, setSavingPO] = useState(false);

  // Toast
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const showToast = (message: string, type: "success" | "error") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleBack = useCallback(async () => {
    if (window.openai?.callTool) {
      await window.openai.callTool("show-claims-dashboard", {});
    }
  }, []);

  const toggleFullscreen = useCallback(async () => {
    if (window.openai?.requestDisplayMode) {
      const current = window.openai.displayMode;
      await window.openai.requestDisplayMode({ mode: current === "fullscreen" ? "inline" : "fullscreen" });
      return;
    }
    try {
      if (!document.fullscreenElement) await document.documentElement.requestFullscreen();
      else await document.exitFullscreen();
    } catch {}
    setIsFullscreen(prev => !prev);
  }, []);

  // ── Save handlers via window.openai.callTool ──────────────────────
  const handleSaveClaim = useCallback(async () => {
    if (!window.openai?.callTool || !data?.claim) return;
    setSavingClaim(true);
    try {
      const args: Record<string, unknown> = { claimId: data.claim.id, status: claimStatus };
      if (claimNote.trim()) args.note = claimNote.trim();
      await window.openai.callTool("update-claim-status", args);
      showToast(`Claim status updated to "${claimStatus}"`, "success");
      setEditingClaim(false);
      setClaimNote("");
    } catch (e) {
      showToast(`Failed to update claim: ${e instanceof Error ? e.message : "Unknown error"}`, "error");
    } finally {
      setSavingClaim(false);
    }
  }, [data?.claim, claimStatus, claimNote]);

  const handleSaveInspection = useCallback(async (inspId: string) => {
    if (!window.openai?.callTool) return;
    setSavingInspection(true);
    try {
      const args: Record<string, unknown> = { inspectionId: inspId };
      if (inspStatus) args.status = inspStatus;
      if (inspFindings.trim()) args.findings = inspFindings.trim();
      if (inspActions.trim()) {
        args.recommendedActions = inspActions.split("\n").map(a => a.trim()).filter(Boolean);
      }
      await window.openai.callTool("update-inspection", args);
      showToast(`Inspection ${inspId} updated`, "success");
      setEditingInspection(null);
    } catch (e) {
      showToast(`Failed to update inspection: ${e instanceof Error ? e.message : "Unknown error"}`, "error");
    } finally {
      setSavingInspection(false);
    }
  }, [inspStatus, inspFindings, inspActions]);

  const handleSavePO = useCallback(async (poId: string) => {
    if (!window.openai?.callTool) return;
    setSavingPO(true);
    try {
      const args: Record<string, unknown> = { purchaseOrderId: poId, status: poStatus };
      if (poNote.trim()) args.note = poNote.trim();
      await window.openai.callTool("update-purchase-order", args);
      showToast(`Purchase order updated to "${poStatus}"`, "success");
      setEditingPO(null);
      setPONote("");
    } catch (e) {
      showToast(`Failed to update PO: ${e instanceof Error ? e.message : "Unknown error"}`, "error");
    } finally {
      setSavingPO(false);
    }
  }, [poStatus, poNote]);

  // ── Enter edit mode helpers ───────────────────────────────────────
  const startEditClaim = useCallback(() => {
    if (!data?.claim) return;
    setClaimStatus(data.claim.status);
    setClaimNote("");
    setEditingClaim(true);
  }, [data?.claim]);

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

  if (!data?.claim) {
    return (
      <div className={styles.container} style={{ backgroundColor: colors.background, color: colors.text }}>
        <Text>No claim data available.</Text>
      </div>
    );
  }

  const { claim, inspections = [], purchaseOrders = [], contractors = {}, inspectors = {} } = data;

  return (
    <div className={styles.container} style={{ backgroundColor: colors.background, color: colors.text }}>
      {/* Toast */}
      {toast && <Toast message={toast.message} type={toast.type} onDismiss={() => setToast(null)} />}

      {/* Header */}
      <div className={styles.header}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <Button
            icon={<ArrowLeftRegular />}
            appearance="subtle"
            onClick={handleBack}
            title="Back to Claims"
            size="small"
            style={{ flexShrink: 0 }}
          />
          <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <Text size={600} weight="bold">{claim.claimNumber}</Text>
            <Badge appearance="filled" color={statusBadgeColor(claim.status)}>
              {claim.status.split(" - ")[0]}
            </Badge>
          </div>
          <Text size={200} style={{ color: colors.textSecondary }}>
            {claim.status}
          </Text>
          </div>
        </div>
        <div style={{ display: "flex", gap: "4px" }}>
          {!editingClaim && (
            <Button
              icon={<EditRegular />}
              appearance="subtle"
              onClick={startEditClaim}
              title="Edit claim"
              size="small"
            />
          )}
          <Button
            icon={isFullscreen ? <ArrowMinimizeRegular /> : <ArrowMaximizeRegular />}
            appearance="subtle"
            onClick={toggleFullscreen}
          />
        </div>
      </div>

      {/* Tabs */}
      <TabList selectedValue={activeTab} onTabSelect={(_, d) => setActiveTab(d.value as string)} style={{ marginBottom: "16px" }}>
        <Tab value="overview" icon={<DocumentRegular />}>Overview</Tab>
        <Tab value="inspections" icon={<SearchRegular />}>Inspections ({inspections.length})</Tab>
        <Tab value="purchase-orders" icon={<BoxRegular />}>Purchase Orders ({purchaseOrders.length})</Tab>
      </TabList>

      {/* ═══════════════════ Overview Tab ═══════════════════ */}
      {activeTab === "overview" && (
        <>
          {/* Edit claim bar */}
          {editingClaim && (
            <div className={styles.editBar} style={{ backgroundColor: colors.surface, border: `1px solid ${colors.border}` }}>
              <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "10px" }}>
                <div>
                  <Text size={200} weight="semibold" className={styles.fieldLabel}>Status</Text>
                  <Select value={claimStatus} onChange={(_, d) => setClaimStatus(d.value)} style={{ width: "100%" }}>
                    {CLAIM_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                  </Select>
                </div>
                <div>
                  <Text size={200} weight="semibold" className={styles.fieldLabel}>Add Note (optional)</Text>
                  <Textarea
                    value={claimNote}
                    onChange={(_, d) => setClaimNote(d.value)}
                    placeholder="Add a note to this claim..."
                    resize="vertical"
                    style={{ width: "100%" }}
                  />
                </div>
                <div className={styles.saveRow}>
                  <Button
                    appearance="primary"
                    icon={<SaveRegular />}
                    onClick={handleSaveClaim}
                    disabled={savingClaim}
                    size="small"
                  >
                    {savingClaim ? "Saving..." : "Save Changes"}
                  </Button>
                  <Button
                    appearance="subtle"
                    icon={<DismissRegular />}
                    onClick={() => setEditingClaim(false)}
                    size="small"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </div>
          )}

          <div className={styles.infoGrid}>
            <div className={styles.infoItem}>
              <PersonRegular style={{ color: colors.primary }} />
              <div>
                <Text size={200} style={{ color: colors.textSecondary }} block>Policy Holder</Text>
                <Text weight="semibold">{claim.policyHolderName}</Text>
                <Text size={200} block style={{ color: colors.textSecondary }}>{claim.policyHolderEmail}</Text>
              </div>
            </div>
            <div className={styles.infoItem}>
              <LocationRegular style={{ color: colors.primary }} />
              <div>
                <Text size={200} style={{ color: colors.textSecondary }} block>Property</Text>
                <Text weight="semibold">{claim.property}</Text>
              </div>
            </div>
            <div className={styles.infoItem}>
              <CalendarRegular style={{ color: colors.primary }} />
              <div>
                <Text size={200} style={{ color: colors.textSecondary }} block>Date of Loss</Text>
                <Text weight="semibold">{new Date(claim.dateOfLoss).toLocaleDateString()}</Text>
              </div>
            </div>
            <div className={styles.infoItem}>
              <ReceiptMoneyRegular style={{ color: colors.primary }} />
              <div>
                <Text size={200} style={{ color: colors.textSecondary }} block>Estimated Loss</Text>
                <Text weight="semibold" style={{ color: colors.error }}>${claim.estimatedLoss.toLocaleString()}</Text>
              </div>
            </div>
          </div>

          <Divider />

          <div className={styles.section} style={{ marginTop: "12px" }}>
            <Text weight="semibold" block style={{ marginBottom: "4px" }}>Description</Text>
            <Text>{claim.description}</Text>
          </div>

          <div className={styles.section}>
            <Text weight="semibold" block style={{ marginBottom: "4px" }}>Damage Types</Text>
            <div className={styles.tags}>
              {claim.damageTypes.map((dt, i) => (
                <Badge key={i} appearance="outline" color="danger">{dt}</Badge>
              ))}
            </div>
          </div>

          <div className={styles.section}>
            <Text weight="semibold" block style={{ marginBottom: "4px" }}>Policy Number</Text>
            <Text>{claim.policyNumber}</Text>
          </div>

          {claim.notes.length > 0 && (
            <div className={styles.section}>
              <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
                <NoteRegular style={{ color: colors.primary }} />
                <Text weight="semibold">Notes ({claim.notes.length})</Text>
              </div>
              {claim.notes.map((n, i) => (
                <Text key={i} size={200} block style={{ color: colors.textSecondary, paddingLeft: "4px", marginBottom: "2px" }}>• {n}</Text>
              ))}
            </div>
          )}
        </>
      )}

      {/* ═══════════════════ Inspections Tab ═══════════════════ */}
      {activeTab === "inspections" && (
        <div className={styles.section}>
          {inspections.length === 0 ? (
            <Text style={{ color: colors.textSecondary }}>No inspections recorded.</Text>
          ) : (
            <Accordion multiple collapsible>
              {inspections.map(insp => {
                const inspector = inspectors[insp.inspectorId];
                const isEditing = editingInspection === insp.id;
                return (
                  <AccordionItem key={insp.id} value={insp.id}>
                    <AccordionHeader>
                      <div style={{ display: "flex", gap: "8px", alignItems: "center", width: "100%" }}>
                        {insp.status === "completed" ? (
                          <CheckmarkCircleRegular style={{ color: colors.success }} />
                        ) : (
                          <ClockRegular style={{ color: colors.warning }} />
                        )}
                        <Text weight="semibold">{insp.id}</Text>
                        <Badge appearance="tint" size="small">{insp.taskType}</Badge>
                        <Badge
                          appearance="filled"
                          size="small"
                          style={{ backgroundColor: priorityColor(insp.priority), color: "#fff" }}
                        >
                          {insp.priority}
                        </Badge>
                        <Badge appearance="outline" size="small" color={statusBadgeColor(insp.status)}>
                          {insp.status}
                        </Badge>
                      </div>
                    </AccordionHeader>
                    <AccordionPanel>
                      <div style={{ padding: "8px 0" }}>
                        <Text size={200} style={{ color: colors.textSecondary }} block>
                          Scheduled: {new Date(insp.scheduledDate).toLocaleDateString()}
                          {insp.completedDate && ` · Completed: ${new Date(insp.completedDate).toLocaleDateString()}`}
                        </Text>
                        {inspector && (
                          <Text size={200} block style={{ marginTop: "4px" }}>
                            Inspector: {inspector.name} ({inspector.email})
                          </Text>
                        )}
                        <Text size={200} block style={{ marginTop: "4px" }}>
                          Property: {insp.property}
                        </Text>

                        {/* Editable inspection form */}
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
                              <Textarea
                                value={inspFindings}
                                onChange={(_, d) => setInspFindings(d.value)}
                                placeholder="Enter inspection findings..."
                                resize="vertical"
                                style={{ width: "100%" }}
                              />
                            </div>
                            <div className={styles.editField}>
                              <Text size={200} weight="semibold" className={styles.fieldLabel}>Recommended Actions (one per line)</Text>
                              <Textarea
                                value={inspActions}
                                onChange={(_, d) => setInspActions(d.value)}
                                placeholder="Enter recommended actions, one per line..."
                                resize="vertical"
                                style={{ width: "100%" }}
                              />
                            </div>
                            <div className={styles.saveRow}>
                              <Button
                                appearance="primary"
                                icon={<SaveRegular />}
                                onClick={() => handleSaveInspection(insp.id)}
                                disabled={savingInspection}
                                size="small"
                              >
                                {savingInspection ? "Saving..." : "Save"}
                              </Button>
                              <Button
                                appearance="subtle"
                                icon={<DismissRegular />}
                                onClick={() => setEditingInspection(null)}
                                size="small"
                              >
                                Cancel
                              </Button>
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
                                {insp.recommendedActions.map((a, i) => (
                                  <Text key={i} size={200} block>• {a}</Text>
                                ))}
                              </div>
                            )}
                            {insp.flaggedIssues.length > 0 && (
                              <div style={{ marginTop: "8px" }}>
                                <Text size={200} weight="semibold" block style={{ color: colors.error }}>
                                  <AlertRegular /> Flagged Issues
                                </Text>
                                {insp.flaggedIssues.map((issue, i) => (
                                  <Text key={i} size={200} block style={{ color: colors.error }}>• {issue}</Text>
                                ))}
                              </div>
                            )}
                            {insp.photos.length > 0 && (
                              <div style={{ marginTop: "8px" }}>
                                <Text size={200} weight="semibold" block><ImageRegular /> Photos</Text>
                                <div className={styles.photoGrid}>
                                  {insp.photos.map((p, i) => (
                                    <Image
                                      key={i}
                                      src={p}
                                      alt={`Inspection photo ${i + 1}`}
                                      width={120}
                                      height={90}
                                      fit="cover"
                                      style={{ borderRadius: "4px", border: `1px solid ${colors.border}` }}
                                    />
                                  ))}
                                </div>
                              </div>
                            )}
                            <Button
                              icon={<EditRegular />}
                              appearance="subtle"
                              size="small"
                              onClick={() => startEditInspection(insp)}
                              style={{ marginTop: "8px" }}
                            >
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

      {/* ═══════════════════ Purchase Orders Tab ═══════════════════ */}
      {activeTab === "purchase-orders" && (
        <div className={styles.section}>
          {purchaseOrders.length === 0 ? (
            <Text style={{ color: colors.textSecondary }}>No purchase orders recorded.</Text>
          ) : (
            purchaseOrders.map(po => {
              const contractor = contractors[po.contractorId];
              const isEditing = editingPO === po.id;
              return (
                <Card key={po.id} className={styles.card} style={{ backgroundColor: colors.surface }}>
                  <CardHeader
                    header={
                      <div className={styles.row} style={{ width: "100%" }}>
                        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                          <BoxRegular style={{ color: colors.primary }} />
                          <Text weight="semibold">{po.poNumber}</Text>
                          <Badge appearance="filled" color={statusBadgeColor(po.status)}>{po.status}</Badge>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <Text weight="bold" style={{ color: colors.primary }}>${po.total.toLocaleString()}</Text>
                          {!isEditing && (
                            <Button
                              icon={<EditRegular />}
                              appearance="subtle"
                              size="small"
                              onClick={() => startEditPO(po)}
                              title="Edit PO"
                            />
                          )}
                        </div>
                      </div>
                    }
                    description={
                      <Text size={200} style={{ color: colors.textSecondary }}>
                        {po.workDescription}
                      </Text>
                    }
                  />

                  {/* Edit PO form */}
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
                        <Textarea
                          value={poNote}
                          onChange={(_, d) => setPONote(d.value)}
                          placeholder="Add a note..."
                          resize="vertical"
                          style={{ width: "100%" }}
                        />
                      </div>
                      <div className={styles.saveRow}>
                        <Button
                          appearance="primary"
                          icon={<SaveRegular />}
                          onClick={() => handleSavePO(po.id)}
                          disabled={savingPO}
                          size="small"
                        >
                          {savingPO ? "Saving..." : "Save"}
                        </Button>
                        <Button
                          appearance="subtle"
                          icon={<DismissRegular />}
                          onClick={() => setEditingPO(null)}
                          size="small"
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}

                  {contractor && (
                    <div style={{ marginTop: "8px", display: "flex", alignItems: "center", gap: "8px" }}>
                      <WrenchRegular style={{ color: colors.primary }} />
                      <Text size={200}>
                        Contractor: <strong>{contractor.name}</strong> — {contractor.businessName}
                      </Text>
                      {contractor.isPreferred && <Badge appearance="tint" size="small" color="success">Preferred</Badge>}
                    </div>
                  )}

                  {/* Line Items */}
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
                        <tr>
                          <td colSpan={3} style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px" }}>Subtotal:</td>
                          <td style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px", fontWeight: "bold" }}>${po.subtotal.toLocaleString()}</td>
                        </tr>
                        <tr>
                          <td colSpan={3} style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px" }}>Tax:</td>
                          <td style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px" }}>${po.tax.toLocaleString()}</td>
                        </tr>
                        <tr>
                          <td colSpan={3} style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px", fontWeight: "bold" }}>Total:</td>
                          <td style={{ textAlign: "right", padding: "4px 8px", fontSize: "12px", fontWeight: "bold", color: colors.primary }}>${po.total.toLocaleString()}</td>
                        </tr>
                      </tfoot>
                    </table>
                  )}

                  {/* PO Notes */}
                  {po.notes && po.notes.length > 0 && (
                    <div style={{ marginTop: "8px" }}>
                      <Text size={200} weight="semibold" block>Notes</Text>
                      {po.notes.map((n, i) => (
                        <Text key={i} size={200} block style={{ color: colors.textSecondary }}>• {n}</Text>
                      ))}
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

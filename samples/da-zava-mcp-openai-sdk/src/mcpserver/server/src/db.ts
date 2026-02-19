import { TableClient } from "@azure/data-tables";

const CONNECTION_STRING =
  process.env.AZURE_STORAGE_CONNECTION_STRING ??
  "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;";

const opts = { allowInsecureConnection: true };

// ── Table Clients ──────────────────────────────────────────────────────
export const claimsTable = TableClient.fromConnectionString(CONNECTION_STRING, "Claims", opts);
export const contractorsTable = TableClient.fromConnectionString(CONNECTION_STRING, "Contractors", opts);
export const inspectionsTable = TableClient.fromConnectionString(CONNECTION_STRING, "Inspections", opts);
export const inspectorsTable = TableClient.fromConnectionString(CONNECTION_STRING, "Inspectors", opts);
export const purchaseOrdersTable = TableClient.fromConnectionString(CONNECTION_STRING, "PurchaseOrders", opts);

export async function ensureTables() {
  const tables = [claimsTable, contractorsTable, inspectionsTable, inspectorsTable, purchaseOrdersTable];
  for (const table of tables) {
    try { await table.createTable(); } catch { /* already exists */ }
  }
}

// ── Entity Interfaces ──────────────────────────────────────────────────
export interface ClaimEntity {
  partitionKey: string;
  rowKey: string;
  claimNumber: string;
  policyNumber: string;
  policyHolderName: string;
  policyHolderEmail: string;
  property: string;
  dateOfLoss: string;
  dateReported: string;
  status: string;
  damageTypes: string;       // JSON array
  description: string;
  estimatedLoss: number;
  adjusterAssigned: string;
  notes: string;             // JSON array
  createdAt: string;
  updatedAt: string;
}

export interface ContractorEntity {
  partitionKey: string;
  rowKey: string;
  name: string;
  businessName: string;
  email: string;
  phone: string;
  address: string;           // JSON object
  licenseNumber: string;
  insuranceCertificate: string;
  specialties: string;       // JSON array
  rating: number;
  isPreferred: boolean;
  isActive: boolean;
}

export interface InspectionEntity {
  partitionKey: string;
  rowKey: string;
  claimId: string;
  claimNumber: string;
  taskType: string;
  priority: string;
  status: string;
  scheduledDate: string;
  inspectorId: string;
  property: string;
  instructions: string;
  photos: string;            // JSON array
  findings: string;
  recommendedActions: string; // JSON array
  flaggedIssues: string;     // JSON array
  createdAt: string;
  updatedAt: string;
  completedDate: string;
}

export interface InspectorEntity {
  partitionKey: string;
  rowKey: string;
  name: string;
  email: string;
  phone: string;
  licenseNumber: string;
  specializations: string;   // JSON array
}

export interface PurchaseOrderEntity {
  partitionKey: string;
  rowKey: string;
  poNumber: string;
  claimId: string;
  claimNumber: string;
  contractorId: string;
  workDescription: string;
  lineItems: string;         // JSON array
  subtotal: number;
  tax: number;
  total: number;
  status: string;
  createdDate: string;
  notes: string;             // JSON array
}

// ── Generic CRUD helpers ───────────────────────────────────────────────
async function listAll<T extends object>(table: TableClient): Promise<T[]> {
  const results: T[] = [];
  for await (const entity of table.listEntities<T>()) {
    results.push(entity);
  }
  return results;
}

async function getById<T extends object>(table: TableClient, partition: string, id: string): Promise<T | null> {
  try {
    return await table.getEntity<T>(partition, id);
  } catch { return null; }
}

async function updateEntity<T extends object>(
  table: TableClient, partition: string, id: string, updates: Record<string, unknown>
): Promise<T | null> {
  const existing = await getById<T>(table, partition, id);
  if (!existing) return null;
  const merged: Record<string, unknown> = { ...(existing as Record<string, unknown>) };
  for (const [key, value] of Object.entries(updates)) {
    merged[key] = Array.isArray(value) || (typeof value === "object" && value !== null)
      ? JSON.stringify(value) : value;
  }
  await table.updateEntity(
    { partitionKey: partition, rowKey: id, ...merged } as any, "Replace"
  );
  return getById<T>(table, partition, id);
}

// ── Claims ─────────────────────────────────────────────────────────────
export const getAllClaims = () => listAll<ClaimEntity>(claimsTable);
export const getClaimById = (id: string) => getById<ClaimEntity>(claimsTable, "claims", id);
export const updateClaim = (id: string, updates: Record<string, unknown>) =>
  updateEntity<ClaimEntity>(claimsTable, "claims", id, updates);

// ── Contractors ────────────────────────────────────────────────────────
export const getAllContractors = () => listAll<ContractorEntity>(contractorsTable);
export const getContractorById = (id: string) => getById<ContractorEntity>(contractorsTable, "contractors", id);
export const updateContractor = (id: string, updates: Record<string, unknown>) =>
  updateEntity<ContractorEntity>(contractorsTable, "contractors", id, updates);

// ── Inspections ────────────────────────────────────────────────────────
export const getAllInspections = () => listAll<InspectionEntity>(inspectionsTable);
export const getInspectionById = (id: string) => getById<InspectionEntity>(inspectionsTable, "inspections", id);
export const getInspectionsByClaimId = async (claimId: string): Promise<InspectionEntity[]> => {
  const all = await getAllInspections();
  return all.filter(i => i.claimId === claimId);
};
export const updateInspection = (id: string, updates: Record<string, unknown>) =>
  updateEntity<InspectionEntity>(inspectionsTable, "inspections", id, updates);

export async function createInspection(fields: Record<string, unknown>): Promise<InspectionEntity> {
  // Auto-generate a unique id
  const all = await getAllInspections();
  const maxNum = all.reduce((max, i) => {
    const m = i.rowKey.match(/^insp-(\d+)$/);
    return m ? Math.max(max, parseInt(m[1], 10)) : max;
  }, 0);
  const newId = `insp-${String(maxNum + 1).padStart(3, "0")}`;
  const now = new Date().toISOString();
  const entity: Record<string, unknown> = {
    partitionKey: "inspections",
    rowKey: newId,
    claimId: fields.claimId ?? "",
    claimNumber: fields.claimNumber ?? "",
    taskType: fields.taskType ?? "initial",
    priority: fields.priority ?? "medium",
    status: fields.status ?? "open",
    scheduledDate: fields.scheduledDate ?? "",
    inspectorId: fields.inspectorId ?? "",
    property: fields.property ?? "",
    instructions: fields.instructions ?? "",
    photos: JSON.stringify(fields.photos ?? []),
    findings: fields.findings ?? "",
    recommendedActions: JSON.stringify(fields.recommendedActions ?? []),
    flaggedIssues: JSON.stringify(fields.flaggedIssues ?? []),
    createdAt: now,
    updatedAt: now,
    completedDate: "",
  };
  await inspectionsTable.createEntity(entity as any);
  return (await getById<InspectionEntity>(inspectionsTable, "inspections", newId))!;
}

// ── Inspectors ─────────────────────────────────────────────────────────
export const getAllInspectors = () => listAll<InspectorEntity>(inspectorsTable);
export const getInspectorById = (id: string) => getById<InspectorEntity>(inspectorsTable, "inspectors", id);

// ── Purchase Orders ────────────────────────────────────────────────────
export const getAllPurchaseOrders = () => listAll<PurchaseOrderEntity>(purchaseOrdersTable);
export const getPurchaseOrderById = (id: string) => getById<PurchaseOrderEntity>(purchaseOrdersTable, "purchaseorders", id);
export const getPurchaseOrdersByClaimId = async (claimId: string): Promise<PurchaseOrderEntity[]> => {
  const all = await getAllPurchaseOrders();
  return all.filter(po => po.claimId === claimId);
};
export const updatePurchaseOrder = (id: string, updates: Record<string, unknown>) =>
  updateEntity<PurchaseOrderEntity>(purchaseOrdersTable, "purchaseorders", id, updates);

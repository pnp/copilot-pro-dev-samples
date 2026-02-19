import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  ensureTables,
  claimsTable,
  contractorsTable,
  inspectionsTable,
  inspectorsTable,
  purchaseOrdersTable,
} from "./db.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_DIR = path.resolve(__dirname, "..", "..", "db");

function loadJson<T>(file: string): T[] {
  const raw = fs.readFileSync(path.join(DB_DIR, file), "utf-8");
  const parsed = JSON.parse(raw);
  // Support both { "rows": [...] } and plain array formats
  return Array.isArray(parsed) ? parsed : parsed.rows;
}

function stringify(value: unknown): string {
  return typeof value === "string" ? value : JSON.stringify(value);
}

async function seed() {
  console.log("🌱 Seeding Zava Insurance database...\n");
  await ensureTables();

  // ── Claims ───────────────────────────────────────────────────────────
  console.log("📋 Seeding Claims...");
  const claims = loadJson<any>("claims.json");
  for (const c of claims) {
    await claimsTable.upsertEntity({
      partitionKey: "claims",
      rowKey: c.id,
      claimNumber: c.claimNumber,
      policyNumber: c.policyNumber,
      policyHolderName: c.policyHolderName,
      policyHolderEmail: c.policyHolderEmail,
      property: c.property,
      dateOfLoss: c.dateOfLoss,
      dateReported: c.dateReported,
      status: c.status,
      damageTypes: stringify(c.damageTypes),
      description: c.description,
      estimatedLoss: c.estimatedLoss,
      adjusterAssigned: c.adjusterAssigned,
      notes: stringify(c.notes),
      createdAt: c.createdAt,
      updatedAt: c.updatedAt,
    }, "Replace");
    console.log(`  ✓ ${c.claimNumber} - ${c.policyHolderName}`);
  }

  // ── Contractors ──────────────────────────────────────────────────────
  console.log("\n🔧 Seeding Contractors...");
  const contractors = loadJson<any>("contractors.json");
  for (const c of contractors) {
    await contractorsTable.upsertEntity({
      partitionKey: "contractors",
      rowKey: c.id,
      name: c.name,
      businessName: c.businessName,
      email: c.email,
      phone: c.phone,
      address: stringify(c.address),
      licenseNumber: c.licenseNumber,
      insuranceCertificate: c.insuranceCertificate,
      specialties: stringify(c.specialties),
      rating: typeof c.rating === "string" ? parseFloat(c.rating) : c.rating,
      isPreferred: c.isPreferred,
      isActive: c.isActive,
    }, "Replace");
    console.log(`  ✓ ${c.name} - ${c.businessName}`);
  }

  // ── Inspections ──────────────────────────────────────────────────────
  console.log("\n🔍 Seeding Inspections...");
  const inspections = loadJson<any>("inspections.json");
  for (const i of inspections) {
    await inspectionsTable.upsertEntity({
      partitionKey: "inspections",
      rowKey: i.id,
      claimId: i.claimId,
      claimNumber: i.claimNumber,
      taskType: i.taskType,
      priority: i.priority,
      status: i.status,
      scheduledDate: i.scheduledDate,
      inspectorId: i.inspectorId,
      property: i.property,
      instructions: i.instructions,
      photos: stringify(i.photos),
      findings: i.findings,
      recommendedActions: stringify(i.recommendedActions),
      flaggedIssues: stringify(i.flaggedIssues),
      createdAt: i.createdAt,
      updatedAt: i.updatedAt,
      completedDate: i.completedDate ?? "",
    }, "Replace");
    console.log(`  ✓ ${i.id} - Claim ${i.claimNumber}`);
  }

  // ── Inspectors ───────────────────────────────────────────────────────
  console.log("\n👷 Seeding Inspectors...");
  const inspectors = loadJson<any>("inspectors.json");
  for (const i of inspectors) {
    await inspectorsTable.upsertEntity({
      partitionKey: "inspectors",
      rowKey: i.id,
      name: i.name,
      email: i.email,
      phone: i.phone,
      licenseNumber: i.licenseNumber,
      specializations: stringify(i.specializations),
    }, "Replace");
    console.log(`  ✓ ${i.name}`);
  }

  // ── Purchase Orders ──────────────────────────────────────────────────
  console.log("\n📦 Seeding Purchase Orders...");
  const pos = loadJson<any>("purchaseOrders.json");
  for (const po of pos) {
    await purchaseOrdersTable.upsertEntity({
      partitionKey: "purchaseorders",
      rowKey: po.id,
      poNumber: po.poNumber,
      claimId: po.claimId,
      claimNumber: po.claimNumber,
      contractorId: po.contractorId,
      workDescription: po.workDescription,
      lineItems: stringify(po.lineItems),
      subtotal: po.subtotal,
      tax: po.tax,
      total: po.total,
      status: po.status,
      createdDate: po.createdDate,
      notes: stringify(po.notes),
    }, "Replace");
    console.log(`  ✓ ${po.poNumber} - Claim ${po.claimNumber}`);
  }

  console.log("\n✅ Seeding complete!");
}

seed().catch(console.error);

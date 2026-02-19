/**
 * Seed Azurite Table Storage from the JSON mock data files.
 * Run: npx tsx src/seed.ts
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  ensureTables,
  consultantsTable,
  projectsTable,
  assignmentsTable,
} from "./db.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_DIR = path.resolve(__dirname, "..", "..", "db");

interface JsonFile<T> { rows: T[] }

function loadJson<T>(file: string): T[] {
  const raw = fs.readFileSync(path.join(DB_DIR, file), "utf-8");
  const parsed: JsonFile<T> = JSON.parse(raw);
  return parsed.rows;
}

async function seed() {
  console.log("Ensuring tables exist…");
  await ensureTables();

  // --- Consultants ---
  const consultants = loadJson<any>("Consultant.json");
  for (const c of consultants) {
    const entity = {
      partitionKey: "consultant",
      rowKey: c.id,
      name: c.name,
      email: c.email,
      phone: c.phone,
      consultantPhotoUrl: c.consultantPhotoUrl,
      location: JSON.stringify(c.location),
      skills: JSON.stringify(c.skills),
      certifications: JSON.stringify(c.certifications),
      roles: JSON.stringify(c.roles),
    };
    try {
      await consultantsTable.upsertEntity(entity, "Replace");
      console.log(`  ✓ Consultant: ${c.name}`);
    } catch (err: any) {
      console.error(`  ✗ Consultant ${c.name}: ${err.message}`);
    }
  }

  // --- Projects ---
  const projects = loadJson<any>("Project.json");
  for (const p of projects) {
    const entity = {
      partitionKey: "project",
      rowKey: p.id,
      name: p.name,
      description: p.description,
      clientName: p.clientName,
      clientContact: p.clientContact,
      clientEmail: p.clientEmail,
      location: JSON.stringify(p.location),
    };
    try {
      await projectsTable.upsertEntity(entity, "Replace");
      console.log(`  ✓ Project: ${p.name}`);
    } catch (err: any) {
      console.error(`  ✗ Project ${p.name}: ${err.message}`);
    }
  }

  // --- Assignments ---
  const assignments = loadJson<any>("Assignment.json");
  for (const a of assignments) {
    const entity = {
      partitionKey: "assignment",
      rowKey: a.id,
      projectId: a.projectId,
      consultantId: a.consultantId,
      role: a.role,
      billable: a.billable,
      rate: a.rate,
      forecast: JSON.stringify(a.forecast),
      delivered: JSON.stringify(a.delivered),
    };
    try {
      await assignmentsTable.upsertEntity(entity, "Replace");
      console.log(`  ✓ Assignment: ${a.id} (${a.role})`);
    } catch (err: any) {
      console.error(`  ✗ Assignment ${a.id}: ${err.message}`);
    }
  }

  console.log("\nSeeding complete ✓");
}

seed().catch((err) => {
  console.error("Seeding failed:", err);
  process.exit(1);
});

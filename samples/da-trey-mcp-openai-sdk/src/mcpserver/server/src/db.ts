import { TableClient, odata } from "@azure/data-tables";

// Azurite default connection string
const CONNECTION_STRING =
  process.env.AZURE_STORAGE_CONNECTION_STRING ??
  "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;";

const tableOptions = { allowInsecureConnection: true };

export const consultantsTable = TableClient.fromConnectionString(CONNECTION_STRING, "Consultants", tableOptions);
export const projectsTable = TableClient.fromConnectionString(CONNECTION_STRING, "Projects", tableOptions);
export const assignmentsTable = TableClient.fromConnectionString(CONNECTION_STRING, "Assignments", tableOptions);

export async function ensureTables(): Promise<void> {
  try { await consultantsTable.createTable(); } catch { /* table may already exist */ }
  try { await projectsTable.createTable(); } catch { /* table may already exist */ }
  try { await assignmentsTable.createTable(); } catch { /* table may already exist */ }
}

// ---------- Consultant helpers ----------

export interface ConsultantEntity {
  partitionKey: string;
  rowKey: string;
  name: string;
  email: string;
  phone: string;
  consultantPhotoUrl: string;
  location: string;     // JSON-stringified
  skills: string;       // JSON-stringified array
  certifications: string;
  roles: string;
}

export async function getAllConsultants(): Promise<ConsultantEntity[]> {
  const results: ConsultantEntity[] = [];
  for await (const entity of consultantsTable.listEntities<ConsultantEntity>()) {
    results.push(entity);
  }
  return results;
}

export async function getConsultantById(id: string): Promise<ConsultantEntity | null> {
  try {
    return await consultantsTable.getEntity<ConsultantEntity>("consultant", id);
  } catch {
    return null;
  }
}

export async function updateConsultant(id: string, updates: Record<string, unknown>): Promise<ConsultantEntity | null> {
  const existing = await getConsultantById(id);
  if (!existing) return null;

  const merged: Record<string, unknown> = { ...existing };
  for (const [key, value] of Object.entries(updates)) {
    if (key === "skills" || key === "certifications" || key === "roles") {
      merged[key] = JSON.stringify(value);
    } else if (key === "location") {
      merged[key] = JSON.stringify(value);
    } else {
      merged[key] = value;
    }
  }
  await consultantsTable.updateEntity(
    { partitionKey: "consultant", rowKey: id, ...merged } as any,
    "Replace"
  );
  return getConsultantById(id);
}

export async function searchConsultantsBySkill(skill: string): Promise<ConsultantEntity[]> {
  const all = await getAllConsultants();
  return all.filter((c) => {
    const skills: string[] = JSON.parse(c.skills || "[]");
    return skills.some((s) => s.toLowerCase().includes(skill.toLowerCase()));
  });
}

// ---------- Project helpers ----------

export interface ProjectEntity {
  partitionKey: string;
  rowKey: string;
  name: string;
  description: string;
  clientName: string;
  clientContact: string;
  clientEmail: string;
  location: string;
}

export async function getAllProjects(): Promise<ProjectEntity[]> {
  const results: ProjectEntity[] = [];
  for await (const entity of projectsTable.listEntities<ProjectEntity>()) {
    results.push(entity);
  }
  return results;
}

export async function getProjectById(id: string): Promise<ProjectEntity | null> {
  try {
    return await projectsTable.getEntity<ProjectEntity>("project", id);
  } catch {
    return null;
  }
}

// ---------- Assignment helpers ----------

export interface AssignmentEntity {
  partitionKey: string;
  rowKey: string;
  projectId: string;
  consultantId: string;
  role: string;
  billable: boolean;
  rate: number;
  forecast: string;   // JSON-stringified
  delivered: string;   // JSON-stringified
}

export async function getAllAssignments(): Promise<AssignmentEntity[]> {
  const results: AssignmentEntity[] = [];
  for await (const entity of assignmentsTable.listEntities<AssignmentEntity>()) {
    results.push(entity);
  }
  return results;
}

export async function getAssignmentsByProject(projectId: string): Promise<AssignmentEntity[]> {
  const all = await getAllAssignments();
  return all.filter((a) => a.projectId === projectId);
}

export async function getAssignmentsByConsultant(consultantId: string): Promise<AssignmentEntity[]> {
  const all = await getAllAssignments();
  return all.filter((a) => a.consultantId === consultantId);
}

export async function createAssignment(data: {
  projectId: string;
  consultantId: string;
  role: string;
  billable?: boolean;
  rate?: number;
  forecast?: Array<{ month: number; year: number; hours: number }>;
}): Promise<AssignmentEntity> {
  const rowKey = `${data.projectId},${data.consultantId}`;
  const entity = {
    partitionKey: "assignment",
    rowKey,
    projectId: data.projectId,
    consultantId: data.consultantId,
    role: data.role,
    billable: data.billable ?? true,
    rate: data.rate ?? 0,
    forecast: JSON.stringify(data.forecast ?? []),
    delivered: JSON.stringify([]),
  };
  await assignmentsTable.upsertEntity(entity as any, "Replace");
  return assignmentsTable.getEntity<AssignmentEntity>("assignment", rowKey);
}

export async function deleteAssignment(projectId: string, consultantId: string): Promise<boolean> {
  const rowKey = `${projectId},${consultantId}`;
  try {
    await assignmentsTable.deleteEntity("assignment", rowKey);
    return true;
  } catch {
    return false;
  }
}

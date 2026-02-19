/**
 * HR Consultant MCP Server factory.
 *
 * Creates a low-level MCP Server with full _meta control for the
 * OpenAI Apps SDK widget protocol (text/html+skybridge resources,
 * openai/outputTemplate, structured content).
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListResourceTemplatesRequestSchema,
  type CallToolRequest,
  type ListToolsRequest,
  type ListResourcesRequest,
  type ReadResourceRequest,
  type ListResourceTemplatesRequest,
  type Resource,
  type ResourceTemplate,
  type Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import * as db from "./db.js";
import { getPublicServerUrl } from "./index.js";

// ─── Widget HTML loader ────────────────────────────────────────────
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ASSETS_DIR = path.resolve(__dirname, "..", "..", "assets");
const MIME_TYPE = "text/html+skybridge";

/**
 * Read a widget's built HTML and inject the public server URL so the
 * widget can call back to this server even when it is loaded through a
 * tunnel or proxy (avoids private-network / mixed-content blocks).
 *
 * Injects a small `<script>` right after `<head>` that sets
 * `window.__SERVER_BASE_URL__`.
 */
function readWidgetHtml(componentName: string): string {
  if (!fs.existsSync(ASSETS_DIR)) {
    throw new Error(
      `Widget assets not found at ${ASSETS_DIR}. Run "npm run build:widgets" first.`
    );
  }
  let html: string | undefined;
  const directPath = path.join(ASSETS_DIR, `${componentName}.html`);
  if (fs.existsSync(directPath)) {
    html = fs.readFileSync(directPath, "utf8");
  } else {
    // Try hashed fallback
    const candidates = fs
      .readdirSync(ASSETS_DIR)
      .filter((f) => f.startsWith(`${componentName}-`) && f.endsWith(".html"))
      .sort();
    const fallback = candidates[candidates.length - 1];
    if (fallback) {
      html = fs.readFileSync(path.join(ASSETS_DIR, fallback), "utf8");
    }
  }
  if (!html) {
    throw new Error(`Widget HTML for "${componentName}" not found in ${ASSETS_DIR}.`);
  }

  // Inject public server URL into the widget
  const serverUrl = getPublicServerUrl();
  const injection = `<script>window.__SERVER_BASE_URL__=${JSON.stringify(serverUrl)};</script>`;
  html = html.replace("<head>", `<head>${injection}`);

  return html;
}

// ─── Widget definitions ────────────────────────────────────────────
interface HRWidget {
  id: string;
  title: string;
  templateUri: string;
  invoking: string;
  invoked: string;
  html: string;
}

let DASHBOARD_WIDGET: HRWidget;
let PROFILE_WIDGET: HRWidget;
let BULK_EDITOR_WIDGET: HRWidget;

function loadWidgets() {
  DASHBOARD_WIDGET = {
    id: "hr-dashboard",
    title: "HR Dashboard",
    templateUri: "ui://widget/hr-dashboard.html",
    invoking: "Loading HR dashboard…",
    invoked: "Dashboard ready",
    html: readWidgetHtml("hr-dashboard"),
  };
  PROFILE_WIDGET = {
    id: "consultant-profile",
    title: "Consultant Profile",
    templateUri: "ui://widget/consultant-profile.html",
    invoking: "Loading consultant profile…",
    invoked: "Profile ready",
    html: readWidgetHtml("consultant-profile"),
  };
  BULK_EDITOR_WIDGET = {
    id: "bulk-editor",
    title: "Bulk Editor",
    templateUri: "ui://widget/bulk-editor.html",
    invoking: "Opening bulk editor…",
    invoked: "Editor ready",
    html: readWidgetHtml("bulk-editor"),
  };
}

function getWidgets(): HRWidget[] {
  return [DASHBOARD_WIDGET, PROFILE_WIDGET, BULK_EDITOR_WIDGET];
}

// ─── Metadata helpers ──────────────────────────────────────────────

/** Meta attached to tool descriptors (list_tools, list_resources) */
function descriptorMeta(widget: HRWidget): Record<string, unknown> {
  return {
    "openai/outputTemplate": widget.templateUri,
    "openai/toolInvocation/invoking": widget.invoking,
    "openai/toolInvocation/invoked": widget.invoked,
    "openai/widgetAccessible": true,
  };
}

/** Meta attached to call_tool responses */
function invocationMeta(widget: HRWidget): Record<string, unknown> {
  return {
    "openai/outputTemplate": widget.templateUri,
    "openai/toolInvocation/invoking": widget.invoking,
    "openai/toolInvocation/invoked": widget.invoked,
    "openai/widgetAccessible": true,
  };
}

// ─── Entity → plain object helpers ─────────────────────────────────

function parseConsultant(c: db.ConsultantEntity) {
  return {
    id: c.rowKey,
    name: c.name,
    email: c.email,
    phone: c.phone,
    photoUrl: c.consultantPhotoUrl,
    location: JSON.parse(c.location || "{}"),
    skills: JSON.parse(c.skills || "[]"),
    certifications: JSON.parse(c.certifications || "[]"),
    roles: JSON.parse(c.roles || "[]"),
  };
}

function parseProject(p: db.ProjectEntity) {
  return {
    id: p.rowKey,
    name: p.name,
    description: p.description,
    clientName: p.clientName,
    clientContact: p.clientContact,
    clientEmail: p.clientEmail,
    location: JSON.parse(p.location || "{}"),
  };
}

function parseAssignment(a: db.AssignmentEntity) {
  return {
    id: a.rowKey,
    projectId: a.projectId,
    consultantId: a.consultantId,
    role: a.role,
    billable: a.billable,
    rate: a.rate,
    forecast: JSON.parse(a.forecast || "[]"),
    delivered: JSON.parse(a.delivered || "[]"),
  };
}

// ─── Tool input schemas ────────────────────────────────────────────

const dashboardInputSchema = {
  type: "object" as const,
  properties: {
    consultantName: {
      type: "string" as const,
      description:
        "Optional consultant name to pre-filter the dashboard (partial match, case-insensitive).",
    },
    projectName: {
      type: "string" as const,
      description:
        "Optional project name to pre-filter the dashboard (partial match, case-insensitive).",
    },
    skill: {
      type: "string" as const,
      description:
        "Optional skill to pre-filter the dashboard — shows only consultants with this skill and their assignments.",
    },
    role: {
      type: "string" as const,
      description:
        "Optional role to pre-filter assignments (e.g. 'Developer', 'Architect').",
    },
    billable: {
      type: "boolean" as const,
      description:
        "Optional — set true to show only billable assignments, false for non-billable.",
    },
  },
  additionalProperties: false,
};

const dashboardParser = z.object({
  consultantName: z.string().optional(),
  projectName: z.string().optional(),
  skill: z.string().optional(),
  role: z.string().optional(),
  billable: z.boolean().optional(),
});

const profileInputSchema = {
  type: "object" as const,
  properties: {
    consultantId: {
      type: "string" as const,
      description: "The ID of the consultant to view.",
    },
  },
  required: ["consultantId"],
  additionalProperties: false,
};

const searchInputSchema = {
  type: "object" as const,
  properties: {
    skill: {
      type: "string" as const,
      description: "Skill to search for (partial match).",
    },
    name: {
      type: "string" as const,
      description: "Name to search for (partial match).",
    },
  },
  additionalProperties: false,
};

const bulkEditorInputSchema = {
  type: "object" as const,
  properties: {
    skill: {
      type: "string" as const,
      description: "Optional skill to filter consultants (partial match, case-insensitive).",
    },
    name: {
      type: "string" as const,
      description: "Optional name to filter consultants (partial match, case-insensitive).",
    },
  },
  additionalProperties: false,
};

const updateConsultantInputSchema = {
  type: "object" as const,
  properties: {
    consultantId: {
      type: "string" as const,
      description: "The ID of the consultant to update.",
    },
    name: { type: "string" as const, description: "Updated name." },
    email: { type: "string" as const, description: "Updated email." },
    phone: { type: "string" as const, description: "Updated phone." },
    skills: {
      type: "array" as const,
      items: { type: "string" as const },
      description: "Updated skills list.",
    },
    roles: {
      type: "array" as const,
      items: { type: "string" as const },
      description: "Updated roles list.",
    },
  },
  required: ["consultantId"],
  additionalProperties: false,
};

const bulkUpdateInputSchema = {
  type: "object" as const,
  properties: {
    consultantIds: {
      type: "array" as const,
      items: { type: "string" as const },
      description: "Array of consultant IDs to update.",
    },
    name: { type: "string" as const, description: "New name for all." },
    email: { type: "string" as const, description: "New email for all." },
    phone: { type: "string" as const, description: "New phone for all." },
    skills: {
      type: "array" as const,
      items: { type: "string" as const },
      description: "New skills list for all.",
    },
    roles: {
      type: "array" as const,
      items: { type: "string" as const },
      description: "New roles list for all.",
    },
  },
  required: ["consultantIds"],
  additionalProperties: false,
};

const projectDetailInputSchema = {
  type: "object" as const,
  properties: {
    projectId: {
      type: "string" as const,
      description: "The project ID.",
    },
  },
  required: ["projectId"],
  additionalProperties: false,
};

const assignConsultantInputSchema = {
  type: "object" as const,
  properties: {
    projectId: {
      type: "string" as const,
      description: "The project ID to assign the consultant to.",
    },
    consultantId: {
      type: "string" as const,
      description: "The consultant ID to assign.",
    },
    role: {
      type: "string" as const,
      description: "The role the consultant will play on the project (e.g. Architect, Developer, Designer, Project lead).",
    },
    billable: {
      type: "boolean" as const,
      description: "Whether the assignment is billable. Defaults to true.",
    },
    rate: {
      type: "number" as const,
      description: "Hourly rate for the consultant on this project. Defaults to 0.",
    },
  },
  required: ["projectId", "consultantId", "role"],
  additionalProperties: false,
};

const bulkAssignInputSchema = {
  type: "object" as const,
  properties: {
    projectId: {
      type: "string" as const,
      description: "The project ID to assign consultants to.",
    },
    consultantIds: {
      type: "array" as const,
      items: { type: "string" as const },
      description: "Array of consultant IDs to assign.",
    },
    role: {
      type: "string" as const,
      description: "The role for all assigned consultants.",
    },
    billable: {
      type: "boolean" as const,
      description: "Whether the assignments are billable. Defaults to true.",
    },
    rate: {
      type: "number" as const,
      description: "Hourly rate for all assigned consultants. Defaults to 0.",
    },
  },
  required: ["projectId", "consultantIds", "role"],
  additionalProperties: false,
};

const removeAssignmentInputSchema = {
  type: "object" as const,
  properties: {
    projectId: {
      type: "string" as const,
      description: "The project ID.",
    },
    consultantId: {
      type: "string" as const,
      description: "The consultant ID to remove from the project.",
    },
  },
  required: ["projectId", "consultantId"],
  additionalProperties: false,
};

// ─── Zod parsers (for runtime validation) ──────────────────────────

const profileParser = z.object({ consultantId: z.string() });
const searchParser = z.object({ skill: z.string().optional(), name: z.string().optional() });
const updateParser = z.object({
  consultantId: z.string(),
  name: z.string().optional(),
  email: z.string().optional(),
  phone: z.string().optional(),
  skills: z.array(z.string()).optional(),
  roles: z.array(z.string()).optional(),
});
const bulkUpdateParser = z.object({
  consultantIds: z.array(z.string()),
  name: z.string().optional(),
  email: z.string().optional(),
  phone: z.string().optional(),
  skills: z.array(z.string()).optional(),
  roles: z.array(z.string()).optional(),
});
const projectDetailParser = z.object({ projectId: z.string() });
const bulkEditorParser = z.object({
  skill: z.string().optional(),
  name: z.string().optional(),
});

const assignConsultantParser = z.object({
  projectId: z.string(),
  consultantId: z.string(),
  role: z.string(),
  billable: z.boolean().optional(),
  rate: z.number().optional(),
});

const bulkAssignParser = z.object({
  projectId: z.string(),
  consultantIds: z.array(z.string()),
  role: z.string(),
  billable: z.boolean().optional(),
  rate: z.number().optional(),
});

const removeAssignmentParser = z.object({
  projectId: z.string(),
  consultantId: z.string(),
});

// ─── Server factory ────────────────────────────────────────────────

export function createHRServer(): Server {
  // Load widget HTML on first call
  if (!DASHBOARD_WIDGET) loadWidgets();

  const server = new Server(
    { name: "trey-hr-consultant", version: "1.0.0" },
    { capabilities: { resources: {}, tools: {} } }
  );

  // ────── List Resources ──────
  const widgetList = getWidgets();
  const widgetsByUri = new Map(widgetList.map((w) => [w.templateUri, w]));

  const resources: Resource[] = widgetList.map((w) => ({
    uri: w.templateUri,
    name: w.title,
    description: `${w.title} widget markup`,
    mimeType: MIME_TYPE,
    _meta: descriptorMeta(w),
  }));

  const resourceTemplates: ResourceTemplate[] = widgetList.map((w) => ({
    uriTemplate: w.templateUri,
    name: w.title,
    description: `${w.title} widget markup`,
    mimeType: MIME_TYPE,
    _meta: descriptorMeta(w),
  }));

  server.setRequestHandler(
    ListResourcesRequestSchema,
    async (_req: ListResourcesRequest) => ({ resources })
  );

  server.setRequestHandler(
    ListResourceTemplatesRequestSchema,
    async (_req: ListResourceTemplatesRequest) => ({ resourceTemplates })
  );

  server.setRequestHandler(
    ReadResourceRequestSchema,
    async (req: ReadResourceRequest) => {
      const widget = widgetsByUri.get(req.params.uri);
      if (!widget) {
        return {
          contents: [],
          _meta: { error: `Unknown resource: ${req.params.uri}` },
        };
      }
      return {
        contents: [
          {
            uri: widget.templateUri,
            mimeType: MIME_TYPE,
            text: widget.html,
            _meta: descriptorMeta(widget),
          },
        ],
      };
    }
  );

  // ────── List Tools ──────
  const tools: Tool[] = [
    {
      name: "show-hr-dashboard",
      title: "Show HR Dashboard",
      description:
        "Display the HR consultant dashboard with KPIs. Accepts optional filters: consultantName, projectName, skill, role, billable — the dashboard auto-applies them so users see a focused view.",
      inputSchema: dashboardInputSchema,
      _meta: descriptorMeta(DASHBOARD_WIDGET),
      annotations: {
        destructiveHint: false,
        openWorldHint: false,
        readOnlyHint: true,
      },
    },
    {
      name: "show-consultant-profile",
      title: "Show Consultant Profile",
      description:
        "Display a detailed profile card for a specific consultant, including contact info, skills, certifications, roles, and current assignments.",
      inputSchema: profileInputSchema,
      _meta: descriptorMeta(PROFILE_WIDGET),
      annotations: {
        destructiveHint: false,
        openWorldHint: false,
        readOnlyHint: true,
      },
    },
    {
      name: "search-consultants",
      title: "Search Consultants",
      description:
        "Search consultants by skill or name. Returns matching consultants in the bulk editor widget for easy viewing and editing.",
      inputSchema: searchInputSchema,
      _meta: descriptorMeta(BULK_EDITOR_WIDGET),
      annotations: {
        destructiveHint: false,
        openWorldHint: false,
        readOnlyHint: true,
      },
    },
    {
      name: "show-bulk-editor",
      title: "Show Bulk Editor",
      description:
        "Open the bulk editor widget to view and edit consultant records. Accepts optional filters: skill, name — to show only matching consultants.",
      inputSchema: bulkEditorInputSchema,
      _meta: descriptorMeta(BULK_EDITOR_WIDGET),
      annotations: {
        destructiveHint: false,
        openWorldHint: false,
        readOnlyHint: false,
      },
    },
    {
      name: "update-consultant",
      title: "Update Consultant",
      description:
        "Update a single consultant's information (name, email, phone, skills, roles).",
      inputSchema: updateConsultantInputSchema,
      annotations: {
        destructiveHint: true,
        openWorldHint: false,
        readOnlyHint: false,
      },
    },
    {
      name: "bulk-update-consultants",
      title: "Bulk Update Consultants",
      description:
        "Batch-update multiple consultant records at once.",
      inputSchema: bulkUpdateInputSchema,
      annotations: {
        destructiveHint: true,
        openWorldHint: false,
        readOnlyHint: false,
      },
    },
    {
      name: "show-project-details",
      title: "Show Project Details",
      description:
        "Display detailed information about a specific project including its assigned consultants and forecasted hours.",
      inputSchema: projectDetailInputSchema,
      _meta: descriptorMeta(DASHBOARD_WIDGET),
      annotations: {
        destructiveHint: false,
        openWorldHint: false,
        readOnlyHint: true,
      },
    },
    {
      name: "assign-consultant-to-project",
      title: "Assign Consultant to Project",
      description:
        "Assign a single consultant to a project with a specified role, optional billing rate, and optional forecast hours.",
      inputSchema: assignConsultantInputSchema,
      annotations: {
        destructiveHint: false,
        openWorldHint: false,
        readOnlyHint: false,
      },
    },
    {
      name: "bulk-assign-consultants",
      title: "Bulk Assign Consultants",
      description:
        "Assign multiple consultants to a project at once. Each assignment includes a role, optional billing rate, and optional forecast.",
      inputSchema: bulkAssignInputSchema,
      annotations: {
        destructiveHint: false,
        openWorldHint: false,
        readOnlyHint: false,
      },
    },
    {
      name: "remove-assignment",
      title: "Remove Assignment",
      description:
        "Remove a consultant's assignment from a project.",
      inputSchema: removeAssignmentInputSchema,
      annotations: {
        destructiveHint: true,
        openWorldHint: false,
        readOnlyHint: false,
      },
    },
  ];

  server.setRequestHandler(
    ListToolsRequestSchema,
    async (_req: ListToolsRequest) => ({ tools })
  );

  // ────── Call Tool ──────
  server.setRequestHandler(
    CallToolRequestSchema,
    async (req: CallToolRequest) => {
      const { name, arguments: rawArgs } = req.params;
      const args = rawArgs ?? {};

      switch (name) {
        // ──── Dashboard ────
        case "show-hr-dashboard": {
          const filters = dashboardParser.parse(args);
          const [consultants, projects, assignments] = await Promise.all([
            db.getAllConsultants(),
            db.getAllProjects(),
            db.getAllAssignments(),
          ]);

          const totalBillableHours = assignments.reduce((sum, a) => {
            if (!a.billable) return sum;
            const forecast: Array<{ hours: number }> = JSON.parse(a.forecast || "[]");
            return sum + forecast.reduce((s, f) => s + f.hours, 0);
          }, 0);

          // Build active filter hints to pass to the widget
          const activeFilters: Record<string, unknown> = {};
          const filterDescParts: string[] = [];

          if (filters.consultantName) {
            activeFilters.consultantName = filters.consultantName;
            filterDescParts.push(`consultant: "${filters.consultantName}"`);
          }
          if (filters.projectName) {
            // Resolve matching project IDs
            const q = filters.projectName.toLowerCase();
            const matchedIds = projects
              .filter((p) => p.name.toLowerCase().includes(q))
              .map((p) => p.rowKey);
            activeFilters.projectIds = matchedIds;
            activeFilters.projectName = filters.projectName;
            filterDescParts.push(`project: "${filters.projectName}"`);
          }
          if (filters.skill) {
            activeFilters.skill = filters.skill;
            filterDescParts.push(`skill: "${filters.skill}"`);
          }
          if (filters.role) {
            activeFilters.role = filters.role;
            filterDescParts.push(`role: "${filters.role}"`);
          }
          if (filters.billable !== undefined) {
            activeFilters.billable = filters.billable;
            filterDescParts.push(filters.billable ? "billable only" : "non-billable only");
          }

          const dashboardData = {
            consultants: consultants.map(parseConsultant),
            projects: projects.map(parseProject),
            assignments: assignments.map((a) => {
              const parsed = parseAssignment(a);
              const proj = projects.find((p) => p.rowKey === a.projectId);
              const cons = consultants.find((c) => c.rowKey === a.consultantId);
              return {
                ...parsed,
                projectName: proj?.name ?? "Unknown",
                clientName: proj?.clientName ?? "Unknown",
                consultantName: cons?.name ?? "Unknown",
              };
            }),
            summary: {
              totalConsultants: consultants.length,
              totalProjects: projects.length,
              totalAssignments: assignments.length,
              totalBillableHours,
            },
            ...(Object.keys(activeFilters).length > 0 ? { filters: activeFilters } : {}),
          };

          const filterDesc = filterDescParts.length > 0
            ? ` (filtered by ${filterDescParts.join(", ")})`
            : "";

          return {
            content: [
              {
                type: "text" as const,
                text: `HR Dashboard: ${consultants.length} consultants, ${projects.length} projects, ${totalBillableHours} billable hours forecasted.${filterDesc}`,
              },
            ],
            structuredContent: dashboardData,
            _meta: invocationMeta(DASHBOARD_WIDGET),
          };
        }

        // ──── Consultant Profile ────
        case "show-consultant-profile": {
          const { consultantId } = profileParser.parse(args);
          const consultant = await db.getConsultantById(consultantId);
          if (!consultant) {
            return {
              content: [{ type: "text" as const, text: `Consultant ${consultantId} not found.` }],
              isError: true,
            };
          }
          const assignments = await db.getAssignmentsByConsultant(consultantId);
          const allProjects = await db.getAllProjects();
          const projectMap = new Map(allProjects.map((p) => [p.rowKey, parseProject(p)]));

          const enrichedAssignments = assignments.map((a) => ({
            ...parseAssignment(a),
            projectName: projectMap.get(a.projectId)?.name ?? "Unknown",
            clientName: projectMap.get(a.projectId)?.clientName ?? "Unknown",
          }));

          const profileData = {
            consultant: parseConsultant(consultant),
            assignments: enrichedAssignments,
          };

          return {
            content: [
              {
                type: "text" as const,
                text: `Profile for ${consultant.name}: ${JSON.parse(consultant.skills || "[]").join(", ")} | ${enrichedAssignments.length} active assignment(s).`,
              },
            ],
            structuredContent: profileData,
            _meta: invocationMeta(PROFILE_WIDGET),
          };
        }

        // ──── Search Consultants ────
        case "search-consultants": {
          const { skill, name: nameFilter } = searchParser.parse(args);
          let results = await db.getAllConsultants();

          if (skill) {
            results = results.filter((c) => {
              const skills: string[] = JSON.parse(c.skills || "[]");
              return skills.some((s) => s.toLowerCase().includes(skill.toLowerCase()));
            });
          }
          if (nameFilter) {
            results = results.filter((c) =>
              c.name.toLowerCase().includes(nameFilter.toLowerCase())
            );
          }

          return {
            content: [
              {
                type: "text" as const,
                text: `Found ${results.length} consultant(s) matching criteria.`,
              },
            ],
            structuredContent: {
              consultants: results.map(parseConsultant),
            },
            _meta: invocationMeta(BULK_EDITOR_WIDGET),
          };
        }

        // ──── Bulk Editor ────
        case "show-bulk-editor": {
          const filters = bulkEditorParser.parse(args);
          let consultants = await db.getAllConsultants();

          if (filters.skill) {
            consultants = consultants.filter((c) => {
              const skills: string[] = JSON.parse(c.skills || "[]");
              return skills.some((s) => s.toLowerCase().includes(filters.skill!.toLowerCase()));
            });
          }
          if (filters.name) {
            consultants = consultants.filter((c) =>
              c.name.toLowerCase().includes(filters.name!.toLowerCase())
            );
          }

          const filterDesc = [filters.skill && `skill: "${filters.skill}"`, filters.name && `name: "${filters.name}"`].filter(Boolean).join(", ");

          return {
            content: [
              {
                type: "text" as const,
                text: `Bulk editor loaded with ${consultants.length} consultant record(s)${filterDesc ? ` (filtered by ${filterDesc})` : ""}.`,
              },
            ],
            structuredContent: {
              consultants: consultants.map(parseConsultant),
            },
            _meta: invocationMeta(BULK_EDITOR_WIDGET),
          };
        }

        // ──── Update Single Consultant ────
        case "update-consultant": {
          const parsed = updateParser.parse(args);
          const { consultantId, ...updates } = parsed;
          const updated = await db.updateConsultant(consultantId, updates);
          if (!updated) {
            return {
              content: [{ type: "text" as const, text: `Consultant ${consultantId} not found.` }],
              isError: true,
            };
          }
          return {
            content: [
              {
                type: "text" as const,
                text: `Updated consultant ${updated.name} (ID: ${consultantId}).`,
              },
            ],
          };
        }

        // ──── Bulk Update ────
        case "bulk-update-consultants": {
          const { consultantIds, ...changes } = bulkUpdateParser.parse(args);
          const results: string[] = [];
          for (const consultantId of consultantIds) {
            const updated = await db.updateConsultant(consultantId, changes);
            results.push(
              updated
                ? `✓ Updated ${updated.name}`
                : `✗ Consultant ${consultantId} not found`
            );
          }
          return {
            content: [
              {
                type: "text" as const,
                text: `Bulk update complete:\n${results.join("\n")}`,
              },
            ],
          };
        }

        // ──── Project Details ────
        case "show-project-details": {
          const { projectId } = projectDetailParser.parse(args);
          const project = await db.getProjectById(projectId);
          if (!project) {
            return {
              content: [{ type: "text" as const, text: `Project ${projectId} not found.` }],
              isError: true,
            };
          }
          const assignments = await db.getAssignmentsByProject(projectId);
          const allConsultants = await db.getAllConsultants();
          const consultantMap = new Map(allConsultants.map((c) => [c.rowKey, parseConsultant(c)]));

          const enrichedAssignments = assignments.map((a) => ({
            ...parseAssignment(a),
            consultantName: consultantMap.get(a.consultantId)?.name ?? "Unknown",
          }));

          const totalBillableHours = enrichedAssignments.reduce((sum, a) => {
            return sum + a.forecast.reduce((s: number, f: any) => s + f.hours, 0);
          }, 0);

          return {
            content: [
              {
                type: "text" as const,
                text: `Project "${project.name}" for ${project.clientName}: ${enrichedAssignments.length} assignment(s).`,
              },
            ],
            structuredContent: {
              projects: [parseProject(project)],
              assignments: enrichedAssignments,
              consultants: allConsultants.map((c) => parseConsultant(c)),
              summary: {
                totalConsultants: allConsultants.length,
                totalProjects: 1,
                totalAssignments: enrichedAssignments.length,
                totalBillableHours,
              },
            },
            _meta: invocationMeta(DASHBOARD_WIDGET),
          };
        }

        // ──── Assign Consultant to Project ────
        case "assign-consultant-to-project": {
          const parsed = assignConsultantParser.parse(args);
          const project = await db.getProjectById(parsed.projectId);
          if (!project) {
            return {
              content: [{ type: "text" as const, text: `Project ${parsed.projectId} not found.` }],
              isError: true,
            };
          }
          const consultant = await db.getConsultantById(parsed.consultantId);
          if (!consultant) {
            return {
              content: [{ type: "text" as const, text: `Consultant ${parsed.consultantId} not found.` }],
              isError: true,
            };
          }
          await db.createAssignment({
            projectId: parsed.projectId,
            consultantId: parsed.consultantId,
            role: parsed.role,
            billable: parsed.billable,
            rate: parsed.rate,
          });
          return {
            content: [
              {
                type: "text" as const,
                text: `Assigned ${consultant.name} to project "${project.name}" as ${parsed.role}${parsed.billable === false ? " (non-billable)" : ""}${parsed.rate ? ` at $${parsed.rate}/hr` : ""}.`,
              },
            ],
          };
        }

        // ──── Bulk Assign Consultants ────
        case "bulk-assign-consultants": {
          const { projectId, consultantIds, role, billable, rate } = bulkAssignParser.parse(args);
          const project = await db.getProjectById(projectId);
          if (!project) {
            return {
              content: [{ type: "text" as const, text: `Project ${projectId} not found.` }],
              isError: true,
            };
          }
          const results: string[] = [];
          for (const consultantId of consultantIds) {
            const consultant = await db.getConsultantById(consultantId);
            if (!consultant) {
              results.push(`✗ Consultant ${consultantId} not found`);
              continue;
            }
            await db.createAssignment({
              projectId,
              consultantId,
              role,
              billable,
              rate,
            });
            results.push(`✓ Assigned ${consultant.name} as ${role}`);
          }
          return {
            content: [
              {
                type: "text" as const,
                text: `Bulk assignment to "${project.name}" complete:\n${results.join("\n")}`,
              },
            ],
          };
        }

        // ──── Remove Assignment ────
        case "remove-assignment": {
          const { projectId, consultantId } = removeAssignmentParser.parse(args);
          const removed = await db.deleteAssignment(projectId, consultantId);
          if (!removed) {
            return {
              content: [{ type: "text" as const, text: `Assignment for consultant ${consultantId} on project ${projectId} not found.` }],
              isError: true,
            };
          }
          return {
            content: [
              {
                type: "text" as const,
                text: `Removed assignment: consultant ${consultantId} from project ${projectId}.`,
              },
            ],
          };
        }

        default:
          return {
            content: [{ type: "text" as const, text: `Unknown tool: ${name}` }],
            isError: true,
          };
      }
    }
  );

  return server;
}

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListResourceTemplatesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as db from "./db.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ASSETS_DIR = path.resolve(__dirname, "..", "..", "assets");

// ── Widget HTML loader ─────────────────────────────────────────────────
function readWidgetHtml(name: string): string {
  const filePath = path.join(ASSETS_DIR, `${name}.html`);
  try {
    return fs.readFileSync(filePath, "utf-8");
  } catch {
    return `<html><body><p>Widget "${name}" not built yet. Run: npm run build:widgets</p></body></html>`;
  }
}

// ── JSON parse helper ──────────────────────────────────────────────────
function safeJsonParse(value: unknown): unknown {
  if (typeof value !== "string") return value;
  try { return JSON.parse(value); } catch { return value; }
}

function parseClaim(entity: db.ClaimEntity) {
  return {
    id: entity.rowKey,
    claimNumber: entity.claimNumber,
    policyNumber: entity.policyNumber,
    policyHolderName: entity.policyHolderName,
    policyHolderEmail: entity.policyHolderEmail,
    property: entity.property,
    dateOfLoss: entity.dateOfLoss,
    dateReported: entity.dateReported,
    status: entity.status,
    damageTypes: safeJsonParse(entity.damageTypes),
    description: entity.description,
    estimatedLoss: entity.estimatedLoss,
    adjusterAssigned: entity.adjusterAssigned,
    notes: safeJsonParse(entity.notes),
    createdAt: entity.createdAt,
    updatedAt: entity.updatedAt,
  };
}

function parseContractor(entity: db.ContractorEntity) {
  return {
    id: entity.rowKey,
    name: entity.name,
    businessName: entity.businessName,
    email: entity.email,
    phone: entity.phone,
    address: safeJsonParse(entity.address),
    licenseNumber: entity.licenseNumber,
    insuranceCertificate: entity.insuranceCertificate,
    specialties: safeJsonParse(entity.specialties),
    rating: entity.rating,
    isPreferred: entity.isPreferred,
    isActive: entity.isActive,
  };
}

function parseInspection(entity: db.InspectionEntity) {
  return {
    id: entity.rowKey,
    claimId: entity.claimId,
    claimNumber: entity.claimNumber,
    taskType: entity.taskType,
    priority: entity.priority,
    status: entity.status,
    scheduledDate: entity.scheduledDate,
    inspectorId: entity.inspectorId,
    property: entity.property,
    instructions: entity.instructions,
    photos: safeJsonParse(entity.photos),
    findings: entity.findings,
    recommendedActions: safeJsonParse(entity.recommendedActions),
    flaggedIssues: safeJsonParse(entity.flaggedIssues),
    createdAt: entity.createdAt,
    updatedAt: entity.updatedAt,
    completedDate: entity.completedDate,
  };
}

function parseInspector(entity: db.InspectorEntity) {
  return {
    id: entity.rowKey,
    name: entity.name,
    email: entity.email,
    phone: entity.phone,
    licenseNumber: entity.licenseNumber,
    specializations: safeJsonParse(entity.specializations),
  };
}

function parsePurchaseOrder(entity: db.PurchaseOrderEntity) {
  return {
    id: entity.rowKey,
    poNumber: entity.poNumber,
    claimId: entity.claimId,
    claimNumber: entity.claimNumber,
    contractorId: entity.contractorId,
    workDescription: entity.workDescription,
    lineItems: safeJsonParse(entity.lineItems),
    subtotal: entity.subtotal,
    tax: entity.tax,
    total: entity.total,
    status: entity.status,
    createdDate: entity.createdDate,
    notes: safeJsonParse(entity.notes),
  };
}

// ── Widget Descriptors ─────────────────────────────────────────────────
const CLAIMS_DASHBOARD = {
  id: "claims-dashboard",
  title: "Claims Dashboard",
  templateUri: "ui://widget/claims-dashboard.html",
  invoking: "Loading claims dashboard…",
  invoked: "Claims dashboard ready",
  html: readWidgetHtml("claims-dashboard"),
};

const CLAIM_DETAIL = {
  id: "claim-detail",
  title: "Claim Detail",
  templateUri: "ui://widget/claim-detail.html",
  invoking: "Loading claim details…",
  invoked: "Claim details ready",
  html: readWidgetHtml("claim-detail"),
};

const CONTRACTORS_LIST = {
  id: "contractors-list",
  title: "Contractors List",
  templateUri: "ui://widget/contractors-list.html",
  invoking: "Loading contractors…",
  invoked: "Contractors ready",
  html: readWidgetHtml("contractors-list"),
};

type WidgetDescriptor = typeof CLAIMS_DASHBOARD;

function descriptorMeta(widget: WidgetDescriptor) {
  return {
    "openai/outputTemplate": widget.templateUri,
    "openai/toolInvocation/invoking": widget.invoking,
    "openai/toolInvocation/invoked": widget.invoked,
    "openai/widgetAccessible": true,
  };
}

function invocationMeta(widget: WidgetDescriptor) {
  return {
    ...descriptorMeta(widget),
  };
}

// ── MCP Server Factory ─────────────────────────────────────────────────
export function createMcpServer(): Server {
  const server = new Server(
    { name: "zava-insurance-mcp", version: "1.0.0" },
    { capabilities: { tools: {}, resources: {} } }
  );

  // ══════════════════════════════════════════════════════════════════════
  //  RESOURCES — Widget HTML (mimeType: text/html+skybridge)
  // ══════════════════════════════════════════════════════════════════════
  const ALL_WIDGETS = [CLAIMS_DASHBOARD, CLAIM_DETAIL, CONTRACTORS_LIST];

  server.setRequestHandler(ListResourcesRequestSchema, async () => ({
    resources: ALL_WIDGETS.map(w => ({
      uri: w.templateUri,
      name: w.title,
      description: `${w.title} widget markup`,
      mimeType: "text/html+skybridge",
      _meta: descriptorMeta(w),
    })),
  }));

  server.setRequestHandler(ListResourceTemplatesRequestSchema, async () => ({
    resourceTemplates: ALL_WIDGETS.map(w => ({
      uriTemplate: w.templateUri,
      name: w.title,
      description: `${w.title} widget markup`,
      mimeType: "text/html+skybridge",
      _meta: descriptorMeta(w),
    })),
  }));

  server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    const uri = request.params.uri;
    const widget = ALL_WIDGETS.find(w => w.templateUri === uri);
    if (!widget) throw new Error(`Resource not found: ${uri}`);
    // Re-read HTML fresh each time so rebuilds are picked up
    const freshHtml = readWidgetHtml(widget.id);
    return {
      contents: [{
        uri: widget.templateUri,
        text: freshHtml,
        mimeType: "text/html+skybridge",
        _meta: descriptorMeta(widget),
      }],
    };
  });

  // ══════════════════════════════════════════════════════════════════════
  //  TOOLS — list_tools with _meta on widget tool definitions
  // ══════════════════════════════════════════════════════════════════════
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: [
      // ── Widget Tools (have _meta) ──────────────────────────────────────
      {
        name: "show-claims-dashboard",
        title: "Show Claims Dashboard",
        description: "Displays the Zava Insurance claims dashboard showing all claims with status overview, filters, and summary metrics. Supports filtering by status and/or policy holder name. When the user mentions a person's name, first name, last name, or partial name, always pass it as the policyHolderName parameter. The name filter is case-insensitive and supports partial matches (e.g. 'kim' will match 'Kimberly King' and 'Kimberly Williams').",
        inputSchema: {
          type: "object" as const,
          properties: {
            status: { type: "string", description: "Filter claims by status keyword (e.g. 'Open', 'Approved', 'Pending', 'Denied', 'Closed')" },
            policyHolderName: { type: "string", description: "Filter claims by policy holder name. Supports partial, case-insensitive matching — pass the first name, last name, or any part of the name (e.g. 'Kimberly', 'king', 'kim'). When the user asks about a specific person's claims, always use this parameter." },
          },
        },
        _meta: descriptorMeta(CLAIMS_DASHBOARD),
        annotations: { readOnlyHint: true },
      },
      {
        name: "show-claim-detail",
        title: "Show Claim Detail",
        description: "Displays detailed information about a specific insurance claim including related inspections, purchase orders, and contractor assignments. Use claim ID (e.g. '1', '2') or claim number (e.g. 'CN202504990').",
        inputSchema: {
          type: "object" as const,
          properties: {
            claimId: { type: "string", description: "The claim ID or claim number to look up" },
          },
          required: ["claimId"],
        },
        _meta: descriptorMeta(CLAIM_DETAIL),
        annotations: { readOnlyHint: true },
      },
      {
        name: "show-contractors",
        title: "Show Contractors",
        description: "Displays the list of contractors available for insurance repair work. Optionally filter by specialty or preferred status.",
        inputSchema: {
          type: "object" as const,
          properties: {
            specialty: { type: "string", description: "Filter by contractor specialty (e.g. 'Roofing', 'Water Damage', 'Fire')" },
            preferredOnly: { type: "boolean", description: "Show only preferred contractors" },
          },
        },
        _meta: descriptorMeta(CONTRACTORS_LIST),
        annotations: { readOnlyHint: true },
      },
      // ── Data Tools (no _meta) ──────────────────────────────────────────
      {
        name: "update-claim-status",
        title: "Update Claim Status",
        description: "Updates the status of an insurance claim. Use claim ID (e.g. '1', '2').",
        inputSchema: {
          type: "object" as const,
          properties: {
            claimId: { type: "string", description: "The claim ID" },
            status: { type: "string", description: "New status (e.g. 'Approved', 'Denied', 'Closed', 'Open - Under Investigation')" },
            note: { type: "string", description: "Optional note to add to the claim" },
          },
          required: ["claimId", "status"],
        },
      },
      {
        name: "update-inspection",
        title: "Update Inspection",
        description: "Updates an inspection record — status, findings, recommended actions, property, or inspector assignment.",
        inputSchema: {
          type: "object" as const,
          properties: {
            inspectionId: { type: "string", description: "The inspection ID (e.g. 'insp-001')" },
            status: { type: "string", description: "New status (e.g. 'completed', 'scheduled', 'in-progress', 'cancelled')" },
            findings: { type: "string", description: "Updated findings text" },
            recommendedActions: { type: "array", items: { type: "string" }, description: "Updated recommended actions" },
            property: { type: "string", description: "Updated property address" },
            inspectorId: { type: "string", description: "Inspector ID to assign (e.g. 'inspector-003')" },
          },
          required: ["inspectionId"],
        },
      },
      {
        name: "update-purchase-order",
        title: "Update Purchase Order",
        description: "Updates a purchase order status (e.g. approve, reject, complete).",
        inputSchema: {
          type: "object" as const,
          properties: {
            purchaseOrderId: { type: "string", description: "The purchase order ID (e.g. 'po-001')" },
            status: { type: "string", description: "New status (e.g. 'approved', 'rejected', 'completed', 'in-progress')" },
            note: { type: "string", description: "Optional note to add" },
          },
          required: ["purchaseOrderId", "status"],
        },
      },
      {
        name: "get-claim-summary",
        title: "Get Claim Summary",
        description: "Returns a text summary for a specific claim with key details. Use claim ID or claim number.",
        inputSchema: {
          type: "object" as const,
          properties: {
            claimId: { type: "string", description: "Claim ID or claim number" },
          },
          required: ["claimId"],
        },
        annotations: { readOnlyHint: true },
      },
      {
        name: "create-inspection",
        title: "Create Inspection",
        description: "Creates a new inspection record. Only claimNumber is required. ID is auto-generated, status defaults to 'open'. claimId is optional.",
        inputSchema: {
          type: "object" as const,
          properties: {
            claimNumber: { type: "string", description: "The claim number (e.g. 'CN202504990')" },
            claimId: { type: "string", description: "Optional claim ID" },
            taskType: { type: "string", description: "Type of inspection: 'initial', 're-inspection', 'final'. Defaults to 'initial'" },
            priority: { type: "string", description: "Priority: 'low', 'medium', 'high'. Defaults to 'medium'" },
            status: { type: "string", description: "Status. Defaults to 'open'" },
            scheduledDate: { type: "string", description: "Scheduled date (ISO string)" },
            inspectorId: { type: "string", description: "Inspector ID to assign" },
            property: { type: "string", description: "Property address" },
            instructions: { type: "string", description: "Inspection instructions" },
          },
          required: ["claimNumber"],
        },
      },
      {
        name: "list-inspectors",
        title: "List Inspectors",
        description: "Lists all available inspectors with their specializations.",
        inputSchema: { type: "object" as const, properties: {} },
        annotations: { readOnlyHint: true },
      },
    ],
  }));

  // ══════════════════════════════════════════════════════════════════════
  //  TOOLS — call_tool handlers with _meta + structuredContent on widgets
  // ══════════════════════════════════════════════════════════════════════
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args = {} } = request.params;

    switch (name) {
      // ── Widget: Claims Dashboard ───────────────────────────────────────
      case "show-claims-dashboard": {
        let claims = (await db.getAllClaims()).map(parseClaim);
        if (args.status) {
          const s = (args.status as string).toLowerCase();
          claims = claims.filter(c => c.status.toLowerCase().includes(s));
        }
        if (args.policyHolderName) {
          const n = (args.policyHolderName as string).toLowerCase();
          claims = claims.filter(c => c.policyHolderName.toLowerCase().includes(n));
        }

        // Enrich: fetch all related data so the widget can do client-side master-detail
        const allInspections = (await db.getAllInspections()).map(parseInspection);
        const allPurchaseOrders = (await db.getAllPurchaseOrders()).map(parsePurchaseOrder);

        const contractorIds = [...new Set(allPurchaseOrders.map(po => po.contractorId))];
        const allContractors: Record<string, any> = {};
        for (const cid of contractorIds) {
          const c = await db.getContractorById(cid);
          if (c) allContractors[cid] = parseContractor(c);
        }

        const inspectorIds = [...new Set(allInspections.map(i => i.inspectorId))];
        const allInspectors: Record<string, any> = {};
        for (const iid of inspectorIds) {
          const i = await db.getInspectorById(iid);
          if (i) allInspectors[iid] = parseInspector(i);
        }

        return {
          content: [{ type: "text" as const, text: `Loaded ${claims.length} claims.` }],
          structuredContent: {
            claims,
            inspections: allInspections,
            purchaseOrders: allPurchaseOrders,
            contractors: allContractors,
            inspectors: allInspectors,
          },
          _meta: invocationMeta(CLAIMS_DASHBOARD),
        };
      }

      // ── Widget: Claim Detail ───────────────────────────────────────────
      case "show-claim-detail": {
        const claimId = args.claimId as string;
        let claim = await db.getClaimById(claimId);
        if (!claim) {
          const all = await db.getAllClaims();
          claim = all.find(c => c.claimNumber === claimId) ?? null;
        }
        if (!claim) {
          return { content: [{ type: "text" as const, text: `Claim "${claimId}" not found.` }] };
        }
        const parsed = parseClaim(claim);
        const inspections = (await db.getInspectionsByClaimId(parsed.id)).map(parseInspection);
        const purchaseOrders = (await db.getPurchaseOrdersByClaimId(parsed.id)).map(parsePurchaseOrder);

        const contractorIds = [...new Set(purchaseOrders.map(po => po.contractorId))];
        const contractors: Record<string, any> = {};
        for (const cid of contractorIds) {
          const c = await db.getContractorById(cid);
          if (c) contractors[cid] = parseContractor(c);
        }

        const inspectorIds = [...new Set(inspections.map(i => i.inspectorId))];
        const inspectors: Record<string, any> = {};
        for (const iid of inspectorIds) {
          const i = await db.getInspectorById(iid);
          if (i) inspectors[iid] = parseInspector(i);
        }

        return {
          content: [{ type: "text" as const, text: `Claim ${parsed.claimNumber} - ${parsed.policyHolderName}` }],
          structuredContent: { claim: parsed, inspections, purchaseOrders, contractors, inspectors },
          _meta: invocationMeta(CLAIM_DETAIL),
        };
      }

      // ── Widget: Contractors List ───────────────────────────────────────
      case "show-contractors": {
        let contractors = (await db.getAllContractors()).map(parseContractor);
        if (args.specialty) {
          const s = (args.specialty as string).toLowerCase();
          contractors = contractors.filter(c => {
            const specs = Array.isArray(c.specialties) ? c.specialties : [];
            return specs.some((sp: string) => sp.toLowerCase().includes(s));
          });
        }
        if (args.preferredOnly) {
          contractors = contractors.filter(c => c.isPreferred);
        }
        return {
          content: [{ type: "text" as const, text: `Loaded ${contractors.length} contractors.` }],
          structuredContent: { contractors },
          _meta: invocationMeta(CONTRACTORS_LIST),
        };
      }

      // ── Data: Update Claim Status ──────────────────────────────────────
      case "update-claim-status": {
        const existing = await db.getClaimById(args.claimId as string);
        if (!existing) {
          return { content: [{ type: "text" as const, text: `Claim "${args.claimId}" not found.` }] };
        }
        const updates: Record<string, unknown> = {
          status: args.status,
          updatedAt: new Date().toISOString(),
        };
        if (args.note) {
          const existingNotes = safeJsonParse(existing.notes);
          const notes = Array.isArray(existingNotes) ? [...existingNotes, args.note] : [args.note];
          updates.notes = notes;
        }
        await db.updateClaim(args.claimId as string, updates);
        return {
          content: [{ type: "text" as const, text: `✅ Claim ${existing.claimNumber} status updated to "${args.status}".` }],
        };
      }

      // ── Data: Update Inspection ────────────────────────────────────────
      case "update-inspection": {
        const existing = await db.getInspectionById(args.inspectionId as string);
        if (!existing) {
          return { content: [{ type: "text" as const, text: `Inspection "${args.inspectionId}" not found.` }] };
        }
        const updates: Record<string, unknown> = { updatedAt: new Date().toISOString() };
        if (args.status) {
          updates.status = args.status;
          if (args.status === "completed") updates.completedDate = new Date().toISOString();
        }
        if (args.findings) updates.findings = args.findings;
        if (args.recommendedActions) updates.recommendedActions = args.recommendedActions;
        if (args.property) updates.property = args.property;
        if (args.inspectorId) updates.inspectorId = args.inspectorId;
        await db.updateInspection(args.inspectionId as string, updates);
        return {
          content: [{ type: "text" as const, text: `✅ Inspection ${args.inspectionId} updated.` }],
        };
      }

      // ── Data: Update Purchase Order ────────────────────────────────────
      case "update-purchase-order": {
        const existing = await db.getPurchaseOrderById(args.purchaseOrderId as string);
        if (!existing) {
          return { content: [{ type: "text" as const, text: `Purchase order "${args.purchaseOrderId}" not found.` }] };
        }
        const updates: Record<string, unknown> = { status: args.status };
        if (args.note) {
          const existingNotes = safeJsonParse(existing.notes);
          const notes = Array.isArray(existingNotes) ? [...existingNotes, args.note] : [args.note];
          updates.notes = notes;
        }
        await db.updatePurchaseOrder(args.purchaseOrderId as string, updates);
        return {
          content: [{ type: "text" as const, text: `✅ Purchase order ${existing.poNumber} status updated to "${args.status}".` }],
        };
      }

      // ── Data: Claim Summary ────────────────────────────────────────────
      case "get-claim-summary": {
        let claim = await db.getClaimById(args.claimId as string);
        if (!claim) {
          const all = await db.getAllClaims();
          claim = all.find(c => c.claimNumber === args.claimId) ?? null;
        }
        if (!claim) {
          return { content: [{ type: "text" as const, text: `Claim "${args.claimId}" not found.` }] };
        }
        const c = parseClaim(claim);
        const inspections = await db.getInspectionsByClaimId(c.id);
        const pos = await db.getPurchaseOrdersByClaimId(c.id);
        const summary = [
          `📋 Claim: ${c.claimNumber}`,
          `👤 Policy Holder: ${c.policyHolderName} (${c.policyHolderEmail})`,
          `📍 Property: ${c.property}`,
          `📅 Date of Loss: ${new Date(c.dateOfLoss).toLocaleDateString()}`,
          `💰 Estimated Loss: $${c.estimatedLoss.toLocaleString()}`,
          `📊 Status: ${c.status}`,
          `🔧 Damage Types: ${(c.damageTypes as string[]).join(", ")}`,
          `🔍 Inspections: ${inspections.length}`,
          `📦 Purchase Orders: ${pos.length}`,
          `📝 Description: ${c.description}`,
        ].join("\n");
        return { content: [{ type: "text" as const, text: summary }] };
      }

      // ── Data: Create Inspection ────────────────────────────────────────
      case "create-inspection": {
        const claimNumber = args.claimNumber as string;
        // Try to resolve claimId and property from the claim if not provided
        let claimId = (args.claimId as string) || "";
        let property = (args.property as string) || "";
        if (!claimId || !property) {
          const allClaims = await db.getAllClaims();
          const matchedClaim = allClaims.find(c => c.claimNumber === claimNumber);
          if (matchedClaim) {
            if (!claimId) claimId = matchedClaim.rowKey;
            if (!property) property = matchedClaim.property;
          }
        }
        const newInspection = await db.createInspection({
          claimNumber,
          claimId,
          property,
          taskType: args.taskType,
          priority: args.priority,
          status: args.status,
          scheduledDate: args.scheduledDate,
          inspectorId: args.inspectorId,
          instructions: args.instructions,
        });
        const parsed = parseInspection(newInspection);
        return {
          content: [{ type: "text" as const, text: `✅ Inspection ${parsed.id} created for claim ${claimNumber}. Status: ${parsed.status}` }],
        };
      }

      // ── Data: List Inspectors ──────────────────────────────────────────
      case "list-inspectors": {
        const inspectors = (await db.getAllInspectors()).map(parseInspector);
        const lines = inspectors.map(i =>
          `• ${i.name} (${i.id}) — ${(i.specializations as string[]).join(", ")} — ${i.email}`
        );
        return {
          content: [{ type: "text" as const, text: `👷 ${inspectors.length} Inspectors:\n${lines.join("\n")}` }],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  });

  return server;
}

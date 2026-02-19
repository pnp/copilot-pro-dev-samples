/**
 * HR Consultant MCP Server – Express + Streamable HTTP transport.
 *
 * Stateless mode: each POST /mcp creates a fresh MCP server + transport.
 * Compatible with ChatGPT, Claude, and other MCP clients.
 */
import express, { type Request, type Response } from "express";
import cors from "cors";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createHRServer } from "./mcp-server.js";
import { ensureTables } from "./db.js";

const PORT = parseInt(process.env.PORT ?? "3001", 10);

const app = express();

// ─── Origin allowlist ────────────────────────────────────────────────
// Exact origins and dot-prefixed wildcard suffixes.
// Dot-prefix (e.g. ".example.com") matches any subdomain.
const STATIC_ALLOWED_ORIGINS: string[] = [
  // Local development
  "http://localhost",
  "http://127.0.0.1",
  "https://localhost",
  "https://127.0.0.1",
  // VS Code webview
  "vscode-webview://",
  // ChatGPT / OpenAI
  ".chatgpt.com",
  ".openai.com",
  // Microsoft 365 Copilot / Office
  ".widgetcopilot.net",
  ".microsoft.com",
  ".cloud.microsoft",
  ".office.com",
  ".office365.com",
  ".sharepoint.com",
  ".live.com",
  ".microsoft365.com",
  ".teams.microsoft.com",
  // Dev tunnels
  ".devtunnels.ms",
  ".ngrok-free.app",
  ".ngrok.io",
  ".loca.lt",
  ".trycloudflare.com",
];

/**
 * Build the full origin set at startup, merging static list with
 * env-driven values: SERVER_BASE_URL and ADDITIONAL_ALLOWED_ORIGINS.
 */
function buildAllowedOrigins(): string[] {
  const origins = [...STATIC_ALLOWED_ORIGINS];

  // SERVER_BASE_URL – the public-facing URL of this server (e.g. a tunnel)
  const serverBase = process.env.SERVER_BASE_URL;
  if (serverBase) {
    try {
      const u = new URL(serverBase);
      origins.push(u.origin);            // exact origin
      origins.push(`.${u.hostname}`);    // also allow subdomains
    } catch { /* ignore malformed URL */ }
  }

  // ADDITIONAL_ALLOWED_ORIGINS – comma-separated extra origins/suffixes
  const extra = process.env.ADDITIONAL_ALLOWED_ORIGINS;
  if (extra) {
    for (const raw of extra.split(",")) {
      const trimmed = raw.trim();
      if (trimmed) origins.push(trimmed);
    }
  }

  return origins;
}

const ALLOWED_ORIGINS = buildAllowedOrigins();

/** Check whether a request origin is permitted. */
function isOriginAllowed(origin: string | undefined): boolean {
  // Sandboxed iframes (ChatGPT, M365 Copilot) send "null" as the origin.
  if (!origin || origin === "null") return true;

  for (const entry of ALLOWED_ORIGINS) {
    // Scheme-prefix match (e.g. "vscode-webview://")
    if (entry.endsWith("://") && origin.startsWith(entry)) return true;

    // Localhost with any port
    if (
      (entry === "http://localhost" || entry === "https://localhost") &&
      origin.startsWith(entry)
    ) return true;
    if (
      (entry === "http://127.0.0.1" || entry === "https://127.0.0.1") &&
      origin.startsWith(entry)
    ) return true;

    // Dot-prefix wildcard subdomain match
    if (entry.startsWith(".")) {
      try {
        const hostname = new URL(origin).hostname;
        if (hostname.endsWith(entry) || hostname === entry.slice(1)) return true;
      } catch { /* not a valid URL */ }
      continue;
    }

    // Exact match
    if (origin === entry) return true;
  }

  return false;
}

/**
 * Return the public-facing base URL of this server.
 * Prefer SERVER_BASE_URL env var (tunnel / proxy URL),
 * otherwise fall back to http://localhost:<PORT>.
 */
export function getPublicServerUrl(): string {
  const base = process.env.SERVER_BASE_URL;
  if (base) return base.replace(/\/+$/, "");
  return `http://localhost:${PORT}`;
}

// ─── CORS middleware ─────────────────────────────────────────────────
const corsOptions: cors.CorsOptions = {
  origin: (origin, callback) => {
    if (isOriginAllowed(origin)) {
      // Reflect the actual origin so the browser accepts the response.
      // For sandboxed iframes that send "null", reflect "null" back.
      callback(null, origin ?? true);
    } else {
      console.warn(`CORS: blocked origin "${origin}"`);
      callback(null, false);
    }
  },
  methods: ["GET", "POST", "DELETE", "OPTIONS"],
  allowedHeaders: [
    "Content-Type",
    "Accept",
    "Mcp-Session-Id",
    "mcp-session-id",
    "Last-Event-ID",
    "Mcp-Protocol-Version",
    "mcp-protocol-version",
  ],
  exposedHeaders: ["Mcp-Session-Id"],
  // credentials: false — avoids the browser requirement that
  // Access-Control-Allow-Origin must not be "*" when credentials are sent.
  // MCP requests don't need cookies or auth headers from the browser.
  credentials: false,
};
app.use(cors(corsOptions));
// Use the same options for preflight on any route
app.options("*", cors(corsOptions));

app.use(express.json());

// ─── Health check ────────────────────────────────────────────────────
app.get("/health", (_req, res) => {
  res.json({ status: "ok", server: "trey-hr-consultant", transport: "streamable-http" });
});

// ─── MCP Streamable HTTP – POST ──────────────────────────────────────
app.post("/mcp", async (req: Request, res: Response) => {
  try {
    // Stateless: fresh server + transport per request
    const server = createHRServer();
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined, // stateless mode
      enableJsonResponse: true,      // return JSON instead of SSE so responses complete immediately
    });

    res.on("close", () => {
      transport.close().catch(console.error);
      server.close().catch(console.error);
    });

    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    console.error("Error handling MCP request:", error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: "2.0",
        error: { code: -32603, message: "Internal server error" },
        id: null,
      });
    }
  }
});

// ─── MCP Streamable HTTP – GET ───────────────────────────────────────
// Clients (e.g. ChatGPT) may send GET to open a server→client SSE stream
// or to probe the endpoint. Delegate to the transport so it responds with
// the correct protocol-level answer instead of a hard 405.
app.get("/mcp", async (req: Request, res: Response) => {
  try {
    const server = createHRServer();
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
      enableJsonResponse: true,
    });

    res.on("close", () => {
      transport.close().catch(console.error);
      server.close().catch(console.error);
    });

    await server.connect(transport);
    await transport.handleRequest(req, res);
  } catch (error) {
    console.error("Error handling MCP GET:", error);
    if (!res.headersSent) {
      res.status(405).json({
        jsonrpc: "2.0",
        error: { code: -32000, message: "Method not allowed." },
        id: null,
      });
    }
  }
});

// ─── MCP Streamable HTTP – DELETE ────────────────────────────────────
app.delete("/mcp", async (req: Request, res: Response) => {
  try {
    const server = createHRServer();
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
      enableJsonResponse: true,
    });

    res.on("close", () => {
      transport.close().catch(console.error);
      server.close().catch(console.error);
    });

    await server.connect(transport);
    await transport.handleRequest(req, res);
  } catch (error) {
    console.error("Error handling MCP DELETE:", error);
    if (!res.headersSent) {
      res.status(405).json({
        jsonrpc: "2.0",
        error: { code: -32000, message: "Method not allowed." },
        id: null,
      });
    }
  }
});

// ─── Start ───────────────────────────────────────────────────────────
async function main() {
  // Ensure Azurite tables exist
  try {
    await ensureTables();
    console.log("Azurite tables ready.");
  } catch (err) {
    console.warn("Could not ensure Azurite tables (is Azurite running?):", err);
  }

  app.listen(PORT, () => {
    const pub = getPublicServerUrl();
    console.log(`\n  HR Consultant MCP Server`);
    console.log(`  Transport: Streamable HTTP (stateless)`);
    console.log(`  Endpoint:  ${pub}/mcp`);
    console.log(`  Health:    ${pub}/health`);
    if (process.env.SERVER_BASE_URL) {
      console.log(`  Public URL: ${pub}  (from SERVER_BASE_URL)`);
    }
    console.log();
  });
}

main().catch(console.error);
